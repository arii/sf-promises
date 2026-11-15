import hashlib
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from src.pdf import extract_archived_pdf
from src.sources import archive_source
from src.worker_leases import WorkerLeases


def small_pdf():
    stream = b"BT /F1 12 Tf 72 720 Td (We will build a library.) Tj ET"
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources "
        b"<< /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n"
        + stream + b"\nendstream",
    ]
    data = b"%PDF-1.4\n"
    offsets = []
    for index, obj in enumerate(objects, 1):
        offsets.append(len(data))
        data += str(index).encode() + b" 0 obj\n" + obj + b"\nendobj\n"
    xref = len(data)
    data += b"xref\n0 6\n0000000000 65535 f \n"
    data += b"".join(f"{offset:010d} 00000 n \n".encode() for offset in offsets)
    return data + b"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n" + str(xref).encode() + b"\n%%EOF\n"


class AsyncMethod:
    def __init__(self, func):
        self.aio = func


class PDFTests(unittest.IsolatedAsyncioTestCase):
    def fake_client(self, directory, upload, execute):
        async def delete():
            pass

        async def stop():
            return worker

        worker = SimpleNamespace(
            id="worker", status="running", mounts=[],
            files=SimpleNamespace(upload_file=AsyncMethod(upload)),
            exec=AsyncMethod(execute), stop=AsyncMethod(stop), delete=AsyncMethod(delete),
        )

        async def fork(*, name):
            worker.name = name
            return worker

        async def get(_):
            return SimpleNamespace(status="stopped", mounts=[], fork=AsyncMethod(fork))

        connection = sqlite3.connect(Path(directory) / "worker-ledger.sqlite")
        self.addCleanup(connection.close)
        return (SimpleNamespace(sandboxes=SimpleNamespace(get=AsyncMethod(get))),
                WorkerLeases(connection))

    async def test_real_pdf_is_parsed_by_worker_script(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.pdf"
            path.write_bytes(small_pdf())
            result = subprocess.run(
                [sys.executable, "src/pdf_worker.py", str(path)],
                capture_output=True, check=True, text=True,
            )
            data = json.loads(result.stdout)
            self.assertEqual(data["sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
            self.assertEqual(data["pages"], [{"page": 1, "text": "We will build a library."}])

    async def test_transfer_validates_result_and_saved_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            saved = archive_source(root, "P1", small_pdf(), ".pdf")
            uploads = []

            async def upload(local, remote):
                uploads.append((Path(local).read_bytes(), remote))

            async def execute(command):
                self.assertEqual(command, "python3 /tmp/sf-promises-pdf-worker.py /tmp/sf-promises-source.pdf")
                local_pdf = root / "uploaded.pdf"
                local_pdf.write_bytes(uploads[0][0])
                output = subprocess.run(
                    [sys.executable, "src/pdf_worker.py", str(local_pdf)],
                    capture_output=True, check=True, text=True,
                )
                return SimpleNamespace(exit_code=0, stdout=output.stdout)

            client, ledger = self.fake_client(directory, upload, execute)
            result = await extract_archived_pdf(
                client, "golden", ledger=ledger, run_id="run", job_id="P1", template_reviewed=True,
                network_reviewed=True,
                root=root, promise_id="P1", path=saved["path"], digest=saved["sha256"]
            )
            self.assertEqual(result["pages"][0]["text"], "We will build a library.")
            self.assertEqual(uploads[0][0], small_pdf())
            Path(saved["path"]).write_bytes(b"tampered")
            with self.assertRaises(ValueError):
                await extract_archived_pdf(
                    client, "golden", ledger=ledger, run_id="run", job_id="P2", template_reviewed=True,
                    network_reviewed=True,
                    root=root, promise_id="P1", path=saved["path"], digest=saved["sha256"]
                )
            self.assertEqual(len(uploads), 2)

    async def test_mismatched_hash_fails_closed_and_cleans_worker(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            saved = archive_source(root, "P1", small_pdf(), ".pdf")

            async def upload(local, remote):
                pass

            async def execute(command):
                return SimpleNamespace(exit_code=0, stdout=json.dumps({
                    "sha256": "0" * 64, "pages": [{"page": 1, "text": "Quoted text"}]
                }))

            client, ledger = self.fake_client(directory, upload, execute)
            with self.assertRaises(ValueError):
                await extract_archived_pdf(
                    client, "golden", ledger=ledger, run_id="run", job_id="P1", template_reviewed=True,
                    network_reviewed=True,
                    root=root, promise_id="P1", path=saved["path"], digest=saved["sha256"]
                )
            self.assertEqual(ledger.get("run", "P1")["state"], "cleaned")

    async def test_no_extractable_text_is_not_reported_as_success(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "blank.pdf"
            original = b"We will build a library."
            path.write_bytes(small_pdf().replace(original, b" " * len(original)))
            result = subprocess.run(
                [sys.executable, "src/pdf_worker.py", str(path)],
                capture_output=True, text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(result.stdout)

    async def test_worker_failure_cleans_fork_without_returning_text(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            saved = archive_source(root, "P1", small_pdf(), ".pdf")

            async def upload(local, remote):
                pass

            async def execute(command):
                return SimpleNamespace(exit_code=1, stdout="worker failed")

            client, ledger = self.fake_client(directory, upload, execute)
            with self.assertRaises(ValueError):
                await extract_archived_pdf(
                    client, "golden", ledger=ledger, run_id="run", job_id="P1",
                    template_reviewed=True, network_reviewed=True, root=root,
                    promise_id="P1", path=saved["path"], digest=saved["sha256"]
                )
            self.assertEqual(ledger.get("run", "P1")["state"], "cleaned")


def multi_page_pdf(texts):
    """A valid multi-page PDF whose page i shows texts[i] as its text."""
    count = len(texts)
    page_objects = [4 + 2 * index for index in range(count)]
    kids = " ".join(f"{obj} 0 R" for obj in page_objects)
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        f"<< /Type /Pages /Kids [{kids}] /Count {count} >>".encode(),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    for text in texts:
        stream = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode()
        page_number = len(objects) + 1
        objects.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources "
            f"<< /Font << /F1 3 0 R >> >> /Contents {page_number + 1} 0 R >>".encode()
        )
        objects.append(
            b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n"
            + stream + b"\nendstream"
        )
    data = b"%PDF-1.4\n"
    offsets = []
    for index, obj in enumerate(objects, 1):
        offsets.append(len(data))
        data += str(index).encode() + b" 0 obj\n" + obj + b"\nendobj\n"
    xref = len(data)
    data += f"xref\n0 {len(objects) + 1}\n".encode() + b"0000000000 65535 f \n"
    data += b"".join(f"{offset:010d} 00000 n \n".encode() for offset in offsets)
    return data + (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n".encode()
        + str(xref).encode() + b"\n%%EOF\n"
    )


def run_worker(pdf_bytes, *arguments):
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "fixture.pdf"
        path.write_bytes(pdf_bytes)
        return subprocess.run(
            [sys.executable, "src/pdf_worker.py", str(path), *arguments],
            capture_output=True, text=True,
        )


class PDFRangeModeTests(unittest.TestCase):
    def test_full_extraction_rejects_a_document_over_the_page_cap(self):
        pdf = multi_page_pdf([f"Page {n} of the oversized fixture." for n in range(1, 121)])
        result = run_worker(pdf)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(result.stdout)

    def test_range_extracts_are_within_caps_and_independently_hashed(self):
        pdf = multi_page_pdf([f"Page {n} of the oversized fixture." for n in range(1, 121)])
        digest = hashlib.sha256(pdf).hexdigest()
        first = json.loads(run_worker(pdf, "--from", "1", "--to", "100").stdout)
        second = json.loads(run_worker(pdf, "--from", "101", "--to", "120").stdout)
        for page_from, page_to, extracted in ((1, 100, first), (101, 120, second)):
            self.assertEqual(extracted["sha256"], digest)
            self.assertEqual(extracted["page_from"], page_from)
            self.assertEqual(extracted["page_to"], page_to)
            self.assertEqual(len(extracted["pages"]), page_to - page_from + 1)
            self.assertLessEqual(sum(len(p["text"]) for p in extracted["pages"]), 500_000)
        self.assertEqual(first["pages"][0], {"page": 1, "text": "Page 1 of the oversized fixture."})
        self.assertEqual(second["pages"][-1], {"page": 120, "text": "Page 120 of the oversized fixture."})

    def test_range_over_the_page_cap_is_rejected(self):
        pdf = multi_page_pdf([f"Page {n}." for n in range(1, 121)])
        result = run_worker(pdf, "--from", "1", "--to", "120")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(result.stdout)

    def test_inspect_emits_char_counts_and_first_lines_without_text(self):
        pdf = multi_page_pdf([f"Chapter {n} - Section" for n in range(1, 4)])
        result = run_worker(pdf, "--inspect")
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["sha256"], hashlib.sha256(pdf).hexdigest())
        self.assertEqual([page["page"] for page in data["pages"]], [1, 2, 3])
        self.assertTrue(all(page["chars"] > 0 for page in data["pages"]))
        self.assertEqual([page["first_line"] for page in data["pages"]],
                         ["Chapter 1 - Section", "Chapter 2 - Section", "Chapter 3 - Section"])
        self.assertNotIn("text", data["pages"][0])

    def test_inspect_rejects_a_document_over_the_inspect_page_limit(self):
        pdf = multi_page_pdf([f"Page {n}." for n in range(1, 120)])
        # 120 pages is under the 5000-page inspect limit but over the extract cap.
        result = run_worker(pdf, "--inspect")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(json.loads(result.stdout)["pages"]), 119)


if __name__ == "__main__":
    unittest.main()
