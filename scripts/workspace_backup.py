"""Back up or restore a quiesced SQLite workspace and its source archive."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import sqlite3
import tempfile

from src.workspace import workspace


def _hash(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _sources(root):
    files = {}
    if not root.is_dir():
        raise ValueError("Source archive missing")
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError("Source symlinks are not supported")
        if path.is_file():
            digest = _hash(path)
            if re.fullmatch(r"[0-9a-f]{64}", path.stem) and path.stem != digest:
                raise ValueError("Source filename hash mismatch")
            files[path.relative_to(root).as_posix()] = digest
    return files


def verify(root):
    root = Path(root).resolve(strict=True)
    database = root / "promises.db"
    with sqlite3.connect(database.as_uri() + "?mode=ro", uri=True) as conn:
        if conn.execute("PRAGMA quick_check").fetchall() != [("ok",)]:
            raise ValueError("Database quick_check failed")
        if conn.execute("PRAGMA foreign_key_check").fetchone():
            raise ValueError("Database foreign key check failed")
    files = _sources(root / "sources")
    manifest = root / "backup.json"
    if manifest.exists():
        expected = json.loads(manifest.read_text())
        if expected != {"database_sha256": _hash(database), "sources": files}:
            raise ValueError("Backup manifest mismatch")
    return files


def snapshot(source, destination):
    source = Path(source).resolve(strict=True)
    destination = Path(destination).absolute()
    if destination.exists():
        raise FileExistsError(destination)
    if source == destination or source in destination.parents:
        raise ValueError("Backup must be outside the source workspace")
    files = verify(source)
    with tempfile.TemporaryDirectory(prefix=".sf-promises-backup-", dir=destination.parent) as directory:
        temporary = Path(directory) / "workspace"
        temporary.mkdir()
        with sqlite3.connect((source / "promises.db").as_uri() + "?mode=ro", uri=True) as original:
            with sqlite3.connect(temporary / "promises.db") as target:
                original.backup(target)
        shutil.copytree(source / "sources", temporary / "sources", symlinks=True)
        if _sources(temporary / "sources") != files:
            raise ValueError("Source archive changed during backup; quiesce writers")
        (temporary / "backup.json").write_text(json.dumps({
            "database_sha256": _hash(temporary / "promises.db"), "sources": files,
        }, indent=2) + "\n")
        verify(temporary)
        temporary.rename(destination)
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["backup", "restore", "verify"])
    parser.add_argument("--workspace", type=Path, default=workspace())
    parser.add_argument("--destination", type=Path)
    args = parser.parse_args()
    if args.action == "verify":
        files = verify(args.workspace)
    else:
        if args.destination is None:
            parser.error("--destination is required")
        if args.action == "restore" and not (args.workspace / "backup.json").is_file():
            parser.error("Restore requires a verified backup manifest")
        files = snapshot(args.workspace, args.destination)
        if args.action == "restore":
            (args.destination / "backup.json").unlink()
    print(f"{args.action}: quick_check ok; {len(files)} source hashes verified")


if __name__ == "__main__":
    main()
