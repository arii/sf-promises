import json
import sqlite3
import subprocess
import sys

import pytest

from scripts.workspace_backup import snapshot, verify


@pytest.fixture
def legacy_workspace(tmp_path):
    root = tmp_path / "legacy"
    root.mkdir()
    (root / "sources").mkdir()
    (root / "sources" / "legacy.txt").write_bytes(b"historical evidence")
    with sqlite3.connect(root / "promises.db") as db:
        db.executescript("""
            CREATE TABLE promises (id TEXT PRIMARY KEY);
            CREATE TABLE sources (id INTEGER PRIMARY KEY, promise_id TEXT REFERENCES promises(id));
            INSERT INTO sources VALUES (1, 'missing');
        """)
    return root


def test_legacy_baseline_requires_explicit_opt_in(legacy_workspace, tmp_path):
    root = legacy_workspace
    original = (root / "promises.db").read_bytes()
    with pytest.raises(ValueError, match="foreign key check failed"):
        snapshot(root, tmp_path / "strict")
    with pytest.raises(ValueError, match="baseline mismatch"):
        verify(root, allow_existing_fk_violations=True)
    backup = tmp_path / "backup"
    files = snapshot(root, backup, allow_existing_fk_violations=True)
    assert verify(backup, allow_existing_fk_violations=True) == files
    assert json.loads((backup / "backup.json").read_text())["foreign_key_violations"]
    with pytest.raises(ValueError, match="foreign key check failed"):
        verify(backup)
    with pytest.raises(ValueError, match="foreign key check failed"):
        snapshot(backup, tmp_path / "strict-copy")
    assert (root / "promises.db").read_bytes() == original
    assert not (root / "backup.json").exists()
    assert not (tmp_path / "strict").exists()


@pytest.mark.parametrize("change", ["new", "different", "resolved"])
def test_restored_legacy_baseline_rejects_any_change(legacy_workspace, tmp_path, change):
    backup, restored = tmp_path / "backup", tmp_path / "restored"
    files = snapshot(legacy_workspace, backup, allow_existing_fk_violations=True)
    command = [sys.executable, "-m", "scripts.workspace_backup"]
    strict = subprocess.run(command + [
        "restore", "--workspace", str(backup), "--destination", str(restored),
    ], capture_output=True, text=True)
    assert strict.returncode != 0
    assert "foreign key check failed" in strict.stderr
    result = subprocess.run(command + [
        "restore", "--workspace", str(backup), "--destination", str(restored),
        "--allow-existing-fk-violations",
    ], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "1 baseline foreign key violations accepted" in result.stdout
    assert verify(restored, allow_existing_fk_violations=True) == files
    (restored / "sources" / "new.txt").write_bytes(b"new evidence")
    snapshot(restored, tmp_path / "next-backup", allow_existing_fk_violations=True)
    with sqlite3.connect(restored / "promises.db") as db:
        if change == "new":
            db.execute("INSERT INTO sources VALUES (2, 'another-missing')")
        elif change == "different":
            db.execute("UPDATE sources SET promise_id = 'different-missing'")
        else:
            db.execute("INSERT INTO promises VALUES ('missing')")
    with pytest.raises(ValueError, match="baseline mismatch"):
        verify(restored, allow_existing_fk_violations=True)
    with pytest.raises(ValueError, match="baseline mismatch"):
        snapshot(restored, tmp_path / "bad-backup", allow_existing_fk_violations=True)
    assert not (tmp_path / "bad-backup").exists()
    assert verify(backup, allow_existing_fk_violations=True) == files


def test_empty_legacy_baseline_and_cli(legacy_workspace, tmp_path):
    with sqlite3.connect(legacy_workspace / "promises.db") as db:
        db.execute("INSERT INTO promises VALUES ('missing')")
    backup = tmp_path / "backup"
    command = [sys.executable, "-m", "scripts.workspace_backup"]
    result = subprocess.run(command + [
        "backup", "--workspace", str(legacy_workspace), "--destination", str(backup),
        "--allow-existing-fk-violations",
    ], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    result = subprocess.run(command + [
        "verify", "--workspace", str(backup), "--allow-existing-fk-violations",
    ], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "0 baseline foreign key violations accepted" in result.stdout
    assert verify(backup)
    with sqlite3.connect(backup / "promises.db") as db:
        db.execute("INSERT INTO sources VALUES (2, 'new-missing')")
    with pytest.raises(ValueError, match="baseline mismatch"):
        verify(backup, allow_existing_fk_violations=True)
