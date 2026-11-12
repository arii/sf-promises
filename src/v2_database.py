"""Initialize a new, separate v2 database without modifying an existing file."""

import argparse
from contextlib import closing
import os
from pathlib import Path
import sqlite3
import tempfile

APPLICATION_ID = 0x53465032
SCHEMA_VERSION = 3


def initialize_database(path):
    target = Path(path)
    parent = target.parent.resolve(strict=True)
    target = parent / target.name
    schema = Path(__file__).with_name("schema_v2.sql").read_text(encoding="utf-8")
    descriptor, temporary = tempfile.mkstemp(prefix=".v2-init-", dir=parent)
    os.close(descriptor)
    try:
        with closing(sqlite3.connect(temporary)) as db:
            db.execute("PRAGMA foreign_keys = ON")
            db.executescript("BEGIN;\n" + schema + "\nCOMMIT;")
            db.execute(f"PRAGMA application_id = {APPLICATION_ID}")
            db.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
        os.link(temporary, target)
    finally:
        os.unlink(temporary)
    return target


def main():
    parser = argparse.ArgumentParser(description="Create a new, separate v2 database")
    parser.add_argument("database", type=Path, help="New database path; existing files are never overwritten")
    args = parser.parse_args()
    try:
        path = initialize_database(args.database)
    except FileExistsError:
        parser.exit(2, "Database already exists; refusing to overwrite it.\n")
    print(f"Created separate v2 database: {path}")


if __name__ == "__main__":
    main()
