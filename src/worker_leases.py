"""Durable, fail-closed records of sandbox creation and cleanup."""

import sqlite3
import uuid


class WorkerLeases:
    def __init__(self, connection: sqlite3.Connection):
        if connection.in_transaction:
            raise ValueError("Worker ledger requires a dedicated connection")
        if not connection.execute("PRAGMA database_list").fetchone()[2]:
            raise ValueError("Worker ledger requires a persistent database")
        if connection.execute(
            """SELECT 1 FROM sqlite_master WHERE type = 'table'
               AND name NOT LIKE 'sqlite_%' AND name != 'worker_leases' LIMIT 1"""
        ).fetchone():
            raise ValueError("Worker ledger must use a separate database")
        self.connection = connection
        with connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS worker_leases (
                    run_id TEXT NOT NULL,
                    job_id TEXT NOT NULL,
                    name TEXT NOT NULL UNIQUE,
                    worker_id TEXT UNIQUE,
                    state TEXT NOT NULL CHECK(state IN ('creating', 'created', 'cleaned')),
                    PRIMARY KEY (run_id, job_id)
                )"""
            )

    def claim(self, run_id: str, job_id: str) -> str:
        if not all(isinstance(value, str) and value.strip() for value in (run_id, job_id)):
            raise ValueError("Run and job IDs are required")
        if self.connection.in_transaction:
            raise ValueError("Worker ledger requires a dedicated connection")
        name = f"sf-audit-{uuid.uuid4().hex}"
        try:
            with self.connection:
                self.connection.execute(
                    "INSERT INTO worker_leases (run_id, job_id, name, state) VALUES (?, ?, ?, 'creating')",
                    (run_id, job_id, name),
                )
        except sqlite3.IntegrityError as exc:
            raise ValueError("Worker attempt already recorded; manual review required") from exc
        return name

    def record_worker(self, run_id: str, job_id: str, worker_id: str) -> None:
        if not isinstance(worker_id, str) or not worker_id.strip():
            raise ValueError("Worker ID is required")
        self._transition(run_id, job_id, "creating", "created", worker_id)

    def mark_cleaned(self, run_id: str, job_id: str) -> None:
        self._transition(run_id, job_id, "created", "cleaned")

    def _transition(self, run_id, job_id, previous, state, worker_id=None):
        if self.connection.in_transaction:
            raise ValueError("Worker ledger requires a dedicated connection")
        with self.connection:
            cursor = self.connection.execute(
                """UPDATE worker_leases SET state = ?, worker_id = COALESCE(?, worker_id)
                   WHERE run_id = ? AND job_id = ? AND state = ?""",
                (state, worker_id, run_id, job_id, previous),
            )
            if cursor.rowcount != 1:
                raise ValueError("Invalid worker lease transition")

    def get(self, run_id: str, job_id: str) -> dict:
        row = self.connection.execute(
            "SELECT name, worker_id, state FROM worker_leases WHERE run_id = ? AND job_id = ?",
            (run_id, job_id),
        ).fetchone()
        if row is None:
            raise ValueError("Worker attempt not found")
        return dict(zip(("name", "worker_id", "state"), row))
