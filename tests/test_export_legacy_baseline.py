import json
import sqlite3
import subprocess
import sys

import pytest

from scripts.workspace_backup import snapshot
from tests.test_export import _load_exporter_module, _make_history_fixture_db


@pytest.fixture
def legacy_workspace(tmp_path):
    root = tmp_path / "original"
    root.mkdir()
    _make_history_fixture_db(root / "promises.db")
    (root / "sources").mkdir()
    (root / "sources" / "saved.txt").write_text("historical evidence")
    with sqlite3.connect(root / "promises.db") as db:
        db.executescript("""
            CREATE TABLE legacy_refs (id INTEGER PRIMARY KEY, promise_id TEXT REFERENCES promises(promise_id));
            INSERT INTO legacy_refs VALUES (1, 'missing');
        """)
    backup, restored = tmp_path / "backup", tmp_path / "restored"
    snapshot(root, backup, allow_existing_fk_violations=True)
    result = subprocess.run([
        sys.executable, "-m", "scripts.workspace_backup", "restore",
        "--workspace", str(backup), "--destination", str(restored),
        "--allow-existing-fk-violations",
    ], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    return restored


def test_export_accepts_recorded_baseline_only_with_opt_in(legacy_workspace, tmp_path):
    root = legacy_workspace
    database = root / "promises.db"
    before = database.read_bytes()
    output = tmp_path / "export"
    command = [sys.executable, "docs/export_data.py", "--db", str(database), "--output-dir", str(output)]
    strict = subprocess.run(command, capture_output=True, text=True)
    assert strict.returncode != 0
    assert "foreign key check failed" in strict.stderr
    assert not output.exists()
    result = subprocess.run(command + ["--allow-existing-fk-violations"], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "P83" in {row["promise_id"] for row in json.loads((output / "data.json").read_text())["promises"]}
    assert database.read_bytes() == before


@pytest.mark.parametrize("fault", ["new", "different", "no_baseline", "no_manifest", "lost_source", "wrong_database"])
def test_export_baseline_opt_in_fails_closed(legacy_workspace, tmp_path, fault):
    root = legacy_workspace
    database = root / "promises.db"
    if fault in ("new", "different"):
        with sqlite3.connect(database) as db:
            if fault == "new":
                db.execute("INSERT INTO legacy_refs VALUES (2, 'another-missing')")
            else:
                db.execute("UPDATE legacy_refs SET promise_id = 'different-missing'")
    elif fault == "no_baseline":
        manifest = json.loads((root / "backup.json").read_text())
        del manifest["foreign_key_violations"]
        (root / "backup.json").write_text(json.dumps(manifest))
    elif fault == "no_manifest":
        (root / "backup.json").unlink()
    elif fault == "lost_source":
        (root / "sources" / "saved.txt").unlink()
    else:
        database = root / "other.db"
        database.write_bytes((root / "promises.db").read_bytes())
    output = tmp_path / "export"
    result = subprocess.run([
        sys.executable, "docs/export_data.py", "--db", str(database),
        "--output-dir", str(output), "--allow-existing-fk-violations",
    ], capture_output=True, text=True)
    assert result.returncode != 0
    expected = "baseline mismatch"
    if fault == "lost_source":
        expected = "manifest mismatch"
    elif fault == "wrong_database":
        expected = "requires a workspace database named promises.db"
    assert expected in result.stderr
    assert not output.exists()


def test_export_opt_in_allows_zero_violations(tmp_path):
    database = tmp_path / "promises.db"
    _make_history_fixture_db(database)
    (tmp_path / "sources").mkdir()
    assert _load_exporter_module().validate_database(database, allow_existing_fk_violations=True) == "legacy"
