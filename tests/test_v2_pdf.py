import hashlib
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from src.v2_pdf import extract_archived_pdf
from src.v2_sources import archive_source
from src.v2_worker_leases import WorkerLeases


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
                [sys.executable, "src/v2_pdf_worker.py", str(path)],
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
                    [sys.executable, "src/v2_pdf_worker.py", str(local_pdf)],
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
                [sys.executable, "src/v2_pdf_worker.py", str(path)],
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


if __name__ == "__main__":
    unittest.main()
