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


def _foreign_key_violations(conn):
    violations = []
    for table, rowid, parent, key in conn.execute("PRAGMA foreign_key_check"):
        if rowid is None:
            raise ValueError("Cannot baseline foreign key violations without rowids")
        quoted_table = '"' + table.replace('"', '""') + '"'
        columns = [
            row[3] for row in conn.execute(f"PRAGMA foreign_key_list({quoted_table})")
            if row[0] == key
        ]
        quoted_columns = ['"' + column.replace('"', '""') + '"' for column in columns]
        expressions = ", ".join(f"typeof({column}) || ':' || hex({column})" for column in quoted_columns)
        values = conn.execute(
            f"SELECT {expressions} FROM {quoted_table} WHERE rowid = ?", (rowid,),
        ).fetchone()
        violations.append([table, rowid, parent, key, list(values)])
    return sorted(violations, key=lambda row: json.dumps(row))


def _verify(root, *, allow_existing_fk_violations=False, record_baseline=False):
    root = Path(root).resolve(strict=True)
    database = root / "promises.db"
    with sqlite3.connect(database.as_uri() + "?mode=ro", uri=True) as conn:
        if conn.execute("PRAGMA quick_check").fetchall() != [("ok",)]:
            raise ValueError("Database quick_check failed")
        violations = _foreign_key_violations(conn)
        if violations and not allow_existing_fk_violations:
            raise ValueError("Database foreign key check failed")
    files = _sources(root / "sources")
    manifest = root / "backup.json"
    expected = json.loads(manifest.read_text()) if manifest.exists() else None
    baseline = violations if record_baseline and not manifest.exists() else []
    if isinstance(expected, dict):
        expected = dict(expected)
        baseline = expected.pop("foreign_key_violations", [])
    if violations != baseline:
        raise ValueError("Database foreign key baseline mismatch")
    if manifest.exists():
        if isinstance(expected, dict) and expected.get("kind") == "workspace":
            matches = (
                set(expected) == {"kind", "sources"}
                and isinstance(expected["sources"], dict)
                and all(files.get(name) == digest for name, digest in expected["sources"].items())
            )
        else:
            matches = expected == {"database_sha256": _hash(database), "sources": files}
        if not matches:
            raise ValueError("Backup manifest mismatch")
    return files, violations


def verify(root, *, allow_existing_fk_violations=False):
    files, _ = _verify(root, allow_existing_fk_violations=allow_existing_fk_violations)
    return files


def snapshot(source, destination, *, allow_existing_fk_violations=False):
    source = Path(source).resolve(strict=True)
    destination = Path(destination).absolute()
    if destination.exists():
        raise FileExistsError(destination)
    if source == destination or source in destination.parents:
        raise ValueError("Backup must be outside the source workspace")
    files, violations = _verify(
        source, allow_existing_fk_violations=allow_existing_fk_violations,
        record_baseline=allow_existing_fk_violations,
    )
    with tempfile.TemporaryDirectory(prefix=".sf-promises-backup-", dir=destination.parent) as directory:
        temporary = Path(directory) / "workspace"
        temporary.mkdir()
        with sqlite3.connect((source / "promises.db").as_uri() + "?mode=ro", uri=True) as original:
            with sqlite3.connect(temporary / "promises.db") as target:
                original.backup(target)
        shutil.copytree(source / "sources", temporary / "sources", symlinks=True)
        if _sources(temporary / "sources") != files:
            raise ValueError("Source archive changed during backup; quiesce writers")
        manifest = {
            "database_sha256": _hash(temporary / "promises.db"), "sources": files,
        }
        if allow_existing_fk_violations:
            manifest["foreign_key_violations"] = violations
        (temporary / "backup.json").write_text(json.dumps(manifest, indent=2) + "\n")
        verify(temporary, allow_existing_fk_violations=allow_existing_fk_violations)
        temporary.rename(destination)
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["backup", "restore", "verify"])
    parser.add_argument("--workspace", type=Path, default=workspace())
    parser.add_argument("--destination", type=Path)
    parser.add_argument(
        "--allow-existing-fk-violations", action="store_true",
        help="Record legacy FK violations on initial backup; otherwise require an exact recorded baseline",
    )
    args = parser.parse_args()
    if args.action == "verify":
        files = verify(args.workspace, allow_existing_fk_violations=args.allow_existing_fk_violations)
    else:
        if args.destination is None:
            parser.error("--destination is required")
        if args.action == "restore" and not (args.workspace / "backup.json").is_file():
            parser.error("Restore requires a verified backup manifest")
        files = snapshot(
            args.workspace, args.destination,
            allow_existing_fk_violations=args.allow_existing_fk_violations,
        )
        if args.action == "restore":
            manifest_path = args.destination / "backup.json"
            baseline = json.loads(manifest_path.read_text()).get("foreign_key_violations")
            manifest = {
                "kind": "workspace", "sources": files,
            }
            if baseline is not None:
                manifest["foreign_key_violations"] = baseline
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    message = f"{args.action}: quick_check ok; {len(files)} source hashes verified"
    if args.allow_existing_fk_violations:
        root = args.workspace if args.action == "verify" else args.destination
        manifest_path = root / "backup.json"
        manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
        message += f"; {len(manifest.get('foreign_key_violations', []))} baseline foreign key violations accepted"
    print(message)


if __name__ == "__main__":
    main()
