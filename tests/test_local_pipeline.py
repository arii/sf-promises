import asyncio
import functools
import hashlib
import json
from pathlib import Path
import runpy
import sqlite3
import subprocess
import sys

import httpx
import pytest

from scripts.workspace_backup import snapshot, verify
from src.database import initialize_database
from src.local_worker import WorkerError, run_worker
from src.pdf import extract_archived_pdf, inspect_archived_pdf
from src.sources import archive_source
from src.sourcing.document_harvester import (
    CollectionSpec, RawByteFetcher, harvest_collections, parse_legistar_documents, parse_pdf_documents,
)
from src.workspace import database_path, workspace
from tests.offline_pipeline import reconcile, run
from tests.test_pdf import small_pdf
from tests.test_export import _load_exporter_module, _make_history_fixture_db


def test_workspace_defaults_and_override(monkeypatch, tmp_path):
    monkeypatch.delenv("SF_PROMISES_WORKSPACE", raising=False)
    assert workspace() == Path("/mnt/archil/workspace")
    monkeypatch.setenv("SF_PROMISES_WORKSPACE", str(tmp_path))
    assert database_path() == tmp_path / "promises.db"


def test_worker_environment_and_cleanup(monkeypatch):
    monkeypatch.setenv("KEENABLE_API_KEY", "not-a-real-key")
    monkeypatch.setenv("SECRET_ARCHIL_API_KEY", "not-a-real-key")
    result = asyncio.run(run_worker("tests.worker_probe", files={}, arguments=["environment"]))
    assert not any("KEY" in name or "SECRET" in name for name in result["environment"])
    assert not Path(result["cwd"]).exists()


def test_intake_workspace_and_explicit_output_override(monkeypatch, tmp_path):
    monkeypatch.setenv("SF_PROMISES_WORKSPACE", str(tmp_path))
    monkeypatch.delenv("ROUND_ROOT", raising=False)
    settings = runpy.run_path("scripts/run_intake_round.py")
    assert settings["ROUND_ROOT"] == tmp_path / "runs" / "intake-round"
    assert settings["ARCHIVE_ROOT"] == tmp_path / "sources"
    monkeypatch.setenv("ROUND_ROOT", str(tmp_path / "reports"))
    settings = runpy.run_path("scripts/run_intake_round.py")
    assert settings["ROUND_ROOT"] == tmp_path / "reports"
    assert settings["ARCHIVE_ROOT"] == tmp_path / "sources"


@pytest.mark.parametrize("mode,match", [("overflow", "output exceeds"), ("invalid", "JSON"),
                                       ("empty", "JSON"), ("failure", "unsuccessfully")])
def test_worker_failure_modes(mode, match):
    with pytest.raises(WorkerError, match=match):
        asyncio.run(run_worker("tests.worker_probe", files={}, arguments=[mode], output_cap=1024))


def test_worker_timeout_kills_group_and_cleans_directory(tmp_path):
    record = tmp_path / "worker.json"
    with pytest.raises(WorkerError, match="timed out"):
        asyncio.run(run_worker("tests.worker_probe", files={},
                               arguments=["timeout", str(record)], timeout=1))
    result = json.loads(record.read_text())
    assert not Path(result["cwd"]).exists()
    stat = Path(f"/proc/{result['child']}/stat")
    assert not stat.exists() or stat.read_text().split()[2] == "Z"


def test_worker_accepts_inputs_under_symlinked_temp_directory(tmp_path, monkeypatch):
    directory = tmp_path / "real"
    directory.mkdir()
    link = tmp_path / "linked"
    link.symlink_to(directory, target_is_directory=True)
    monkeypatch.setattr("tempfile.tempdir", str(link))
    result = asyncio.run(run_worker("src.candidate_worker", files={
        "request.json": json.dumps({"sources": [], "origin": None}).encode(),
    }))
    assert result == {"failures": []}
    assert list(directory.iterdir()) == []


@pytest.mark.parametrize("name", ["../escape", "/absolute/escape"])
def test_worker_rejects_input_paths_outside_job_directory(name):
    with pytest.raises(WorkerError, match="Invalid worker input path"):
        asyncio.run(run_worker("src.candidate_worker", files={name: b"input"}))


@pytest.mark.skipif(sys.platform != "linux", reason="Linux resource limits")
def test_worker_resource_limits():
    limits = asyncio.run(run_worker("tests.worker_probe", files={}, arguments=["limits"]))
    assert limits["RLIMIT_CPU"] == [60, 60]
    assert limits["RLIMIT_AS"] == [1024 ** 3] * 2
    assert limits["RLIMIT_CORE"] == [0, 0]
    assert limits["RLIMIT_NOFILE"] == [64, 64]


@pytest.mark.parametrize("lane,host,parser", [
    ("bos_transcripts", "sfgov.legistar.com", parse_legistar_documents),
    ("budget_documents", "sfcontroller.org", parse_pdf_documents),
    ("ballot_measures", "sfelections.sfgov.org", parse_pdf_documents),
])
def test_pdf_intake_uses_real_local_worker(tmp_path, lane, host, parser):
    async def check():
        listing, document = f"https://{host}/index", f"https://{host}/source.pdf"
        if lane == "bos_transcripts":
            document = f"https://{host}/View.ashx?M=A&ID=1"
        data = small_pdf()

        def handler(request):
            body = f'<a href="{document}">Source</a>'.encode() if str(request.url) == listing else data
            return httpx.Response(200, content=body)

        async def sleep(_):
            pass

        root = tmp_path / "sources"
        async with RawByteFetcher(transport=httpx.MockTransport(handler)) as fetcher:
            result = await harvest_collections(
                specs=(CollectionSpec(lane, lane, (listing,), parser),),
                archive_root=root, repo_root=tmp_path,
                fetcher=fetcher,
                extract_pdf=functools.partial(extract_archived_pdf, root=root),
                inspect_pdf=functools.partial(inspect_archived_pdf, root=root), sleep=sleep,
                max_documents=1,
            )
        assert len(result["documents"]) == 1
        saved = result["documents"][0]
        assert saved["sha256"] == hashlib.sha256(data).hexdigest()
        assert "We will build a library." in Path(saved["text_path"]).read_text()
        assert hashlib.sha256(Path(saved["text_path"]).read_bytes()).hexdigest() == saved["text_sha256"]
    asyncio.run(check())


def test_candidate_batch_publish_quarantine_resume_and_staged_export(tmp_path, monkeypatch):
    monkeypatch.setenv("SF_PROMISES_WORKSPACE", str(tmp_path))
    database = database_path()
    results = asyncio.run(run(database))
    assert [row["status"] for row in results] == ["published", "quarantined"]
    again = asyncio.run(run(database))
    assert [row["status"] for row in again] == ["published", "quarantined"]
    with sqlite3.connect(database) as conn:
        assert conn.execute("SELECT count(*) FROM verdicts").fetchone()[0] == 1
        assert conn.execute("SELECT count(*) FROM quarantined").fetchone()[0] == 1
    output = tmp_path / "export"
    baseline = Path("docs/data.json").read_bytes()
    result = subprocess.run([sys.executable, "docs/export_data.py", "--output-dir", str(output)],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    document = json.loads((output / "data.json").read_text())
    assert document["snapshot_kind"] == "candidate_not_published"
    assert document["tallies"] == {"KEPT": 1}
    diff = reconcile(document, json.loads(baseline))
    assert diff["staged_count"] == 1 and diff["baseline_count"] == 54
    assert diff["added_ids"] == []
    assert len(diff["missing_ids"]) == 53
    assert Path("docs/data.json").read_bytes() == baseline


def test_tampered_candidate_source_is_blocked_without_publication(tmp_path):
    results = asyncio.run(run(tmp_path / "promises.db", reject=True))
    assert results[0]["status"] == "blocked"
    assert results[0]["reason"] == "WORKER_CHECK_FAILED"
    with sqlite3.connect(tmp_path / "promises.db") as conn:
        assert conn.execute("SELECT count(*) FROM verdicts").fetchone()[0] == 0


@pytest.mark.parametrize("kind", ["missing", "empty", "invalid"])
def test_export_fails_closed(tmp_path, kind):
    database = tmp_path / "promises.db"
    if kind == "empty":
        sqlite3.connect(database).close()
    elif kind == "invalid":
        database.write_bytes(b"not sqlite")
    output = tmp_path / "export"
    result = subprocess.run([sys.executable, "docs/export_data.py", "--db", str(database),
                             "--output-dir", str(output)], capture_output=True, text=True)
    assert result.returncode != 0
    assert not output.exists()


def test_legacy_export_stages_without_changing_live_files(tmp_path, monkeypatch):
    database = tmp_path / "legacy.db"
    _make_history_fixture_db(database)
    staging = tmp_path / "advocates"
    staging.mkdir()
    bundle = {"claims": [], "fixture_staging_override": True}
    (staging / "kept_P83.json").write_text(json.dumps(bundle))
    monkeypatch.setenv("STAGING_DIR", str(staging))
    output = tmp_path / "export"
    names = ("docs/data.json", "docs/data.js", "docs/index.html", "data/evidence_review_queue.json")
    before = {name: Path(name).read_bytes() for name in names}
    result = subprocess.run([sys.executable, "docs/export_data.py", "--db", str(database),
                             "--output-dir", str(output)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    payload = json.loads((output / "data.json").read_text())
    assert "P83" in {p["promise_id"] for p in payload["promises"]}
    assert next(p for p in payload["promises"] if p["promise_id"] == "P83")["advocate_bundles"]["kept"] == bundle
    assert payload["database_status"]["total_db_promises"] == 2
    assert (output / "index.html").is_file()
    assert {name: Path(name).read_bytes() for name in names} == before


def test_backup_restore_verifies_database_and_all_source_hashes(tmp_path):
    root = tmp_path / "original"
    root.mkdir()
    initialize_database(root / "promises.db")
    saved = archive_source(root / "sources", "P1", b"saved evidence", ".txt")
    backup, restored = tmp_path / "backup", tmp_path / "restored"
    expected = snapshot(root, backup)
    assert snapshot(backup, restored) == expected
    assert verify(restored) == expected
    with pytest.raises(FileExistsError):
        snapshot(backup, restored)
    archived = restored / "sources" / "P1" / Path(saved["path"]).name
    archived.write_bytes(b"tampered")
    with pytest.raises(ValueError, match="hash mismatch"):
        verify(restored)


@pytest.mark.parametrize("stale_output", [False, True])
def test_staged_legacy_export_preserves_committed_pending_ids(tmp_path, stale_output):
    database = tmp_path / "legacy.db"
    _make_history_fixture_db(database)
    script = Path("docs/export_data.py").resolve()
    baseline = json.loads(script.with_name("data.json").read_text())
    expected = baseline["database_status"]["pending_intake_ids"]
    assert expected
    output = tmp_path / "export"
    if stale_output:
        output.mkdir()
        (output / "data.json").write_text(json.dumps({
            "database_status": {"pending_intake_ids": ["STALE-PENDING"]},
        }))
    result = subprocess.run([
        sys.executable, str(script), "--db", str(database), "--output-dir", str(output),
    ], cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    payload = json.loads((output / "data.json").read_text())
    assert payload["database_status"]["pending_intake_ids"] == expected


def test_backup_manifest_detects_missing_sources(tmp_path):
    root = tmp_path / "original"
    root.mkdir()
    initialize_database(root / "promises.db")
    saved = archive_source(root / "sources", "P1", b"evidence", ".txt")
    backup = tmp_path / "backup"
    snapshot(root, backup)
    (backup / "sources" / "P1" / Path(saved["path"]).name).unlink()
    with pytest.raises(ValueError, match="manifest mismatch"):
        verify(backup)


def test_fallback_pending_ids_exclude_published_and_quarantined(tmp_path, monkeypatch):
    exporter = _load_exporter_module()
    previous = json.loads(Path(exporter.__file__).with_name("data.json").read_text())
    pending = previous["database_status"]["pending_intake_ids"]
    published_id, quarantined_id = pending[:2]
    database = tmp_path / "legacy.db"
    _make_history_fixture_db(database)
    with sqlite3.connect(database) as conn:
        conn.execute(
            """INSERT INTO promises
               SELECT ?, entity_id, promise_text, promised_date, due_date, source_url,
                      source_file_path, source_hash, source_type, status
               FROM promises WHERE promise_id = 'P06'""", (published_id,),
        )
        conn.execute("INSERT INTO quarantined VALUES (?, ?, ?, ?, NULL, NULL)",
                     ("Q1", quarantined_id, "relevance_low", "2026-01-01T00:00:00Z"))
    monkeypatch.chdir(tmp_path)
    result = exporter._load_from_db(str(database))
    assert published_id in {row["promise_id"] for row in result[0]}
    assert quarantined_id in {row["promise_id"] for row in result[-2]}
    assert result[-1] == sorted(set(pending) - {published_id, quarantined_id})


def test_restored_workspace_can_be_updated_and_backed_up(tmp_path):
    original, backup = tmp_path / "original", tmp_path / "backup"
    restored, next_backup = tmp_path / "restored", tmp_path / "next-backup"
    original.mkdir()
    initialize_database(original / "promises.db")
    archive_source(original / "sources", "P1", b"original evidence", ".txt")
    original_files = snapshot(original, backup)
    result = subprocess.run([
        sys.executable, "-m", "scripts.workspace_backup", "restore",
        "--workspace", str(backup), "--destination", str(restored),
    ], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    with sqlite3.connect(restored / "promises.db") as conn:
        conn.execute("CREATE TABLE new_activity (value TEXT)")
    archive_source(restored / "sources", "P2", b"new evidence", ".txt")
    files = snapshot(restored, next_backup)
    assert len(files) == len(original_files) + 1
    assert verify(next_backup) == files
    assert verify(backup) == original_files


@pytest.mark.parametrize("fault", ["missing", "changed"])
def test_restored_workspace_retains_source_completeness(tmp_path, fault):
    original, backup, restored = (tmp_path / name for name in ("original", "backup", "restored"))
    original.mkdir()
    initialize_database(original / "promises.db")
    (original / "sources").mkdir()
    (original / "sources" / "legacy.txt").write_bytes(b"original evidence")
    expected = snapshot(original, backup)
    result = subprocess.run([
        sys.executable, "-m", "scripts.workspace_backup", "restore",
        "--workspace", str(backup), "--destination", str(restored),
    ], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    archive_source(restored / "sources", "P2", b"new evidence", ".txt")
    archived = restored / "sources" / "legacy.txt"
    if fault == "missing":
        archived.unlink()
    else:
        archived.write_bytes(b"changed evidence")
    with pytest.raises(ValueError, match="manifest mismatch"):
        verify(restored)
    with pytest.raises(ValueError, match="manifest mismatch"):
        snapshot(restored, tmp_path / "next-backup")
    assert not (tmp_path / "next-backup").exists()
    assert verify(backup) == expected
