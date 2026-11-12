import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from src.v2_worker_leases import WorkerLeases


class WorkerLeaseTests(unittest.TestCase):
    def test_existing_application_database_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "application.sqlite"
            with sqlite3.connect(path) as connection:
                connection.execute("CREATE TABLE promises (id TEXT)")
                with self.assertRaises(ValueError):
                    WorkerLeases(connection)
                self.assertIsNone(connection.execute(
                    "SELECT name FROM sqlite_master WHERE name = 'worker_leases'"
                ).fetchone())

    def test_creation_intent_and_known_worker_survive_reopen(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "runner.sqlite"
            with sqlite3.connect(path) as connection:
                leases = WorkerLeases(connection)
                name = leases.claim("run-1", "P1")
                leases.record_worker("run-1", "P1", "worker-id")
            with sqlite3.connect(path) as connection:
                leases = WorkerLeases(connection)
                record = leases.get("run-1", "P1")
                self.assertEqual((record["name"], record["worker_id"], record["state"]),
                                 (name, "worker-id", "created"))
                with self.assertRaises(ValueError):
                    leases.claim("run-1", "P1")
                leases.mark_cleaned("run-1", "P1")
                self.assertEqual(leases.get("run-1", "P1")["state"], "cleaned")

    def test_unresolved_creation_is_not_retried_or_marked_clean(self):
        with tempfile.TemporaryDirectory() as directory:
            with sqlite3.connect(Path(directory) / "runner.sqlite") as connection:
                leases = WorkerLeases(connection)
                leases.claim("run-1", "P1")
                with self.assertRaises(ValueError):
                    leases.claim("run-1", "P1")
                with self.assertRaises(ValueError):
                    leases.mark_cleaned("run-1", "P1")
                self.assertEqual(leases.get("run-1", "P1")["state"], "creating")

    def test_worker_id_survives_abrupt_coordinator_exit(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "runner.sqlite"
            program = """
import os, sqlite3, sys
from src.v2_worker_leases import WorkerLeases
leases = WorkerLeases(sqlite3.connect(sys.argv[1]))
leases.claim("run", "job")
leases.record_worker("run", "job", "worker")
os._exit(0)
"""
            subprocess.run([sys.executable, "-c", program, str(path)], check=True)
            with sqlite3.connect(path) as connection:
                leases = WorkerLeases(connection)
                self.assertEqual(leases.get("run", "job")["worker_id"], "worker")
                with self.assertRaises(ValueError):
                    leases.claim("run", "job")


if __name__ == "__main__":
    unittest.main()
