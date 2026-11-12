import hashlib
import tempfile
import unittest
from pathlib import Path

from src.sources import archive_source, verify_source


class SourceArchiveTests(unittest.TestCase):
    def test_archive_roundtrip_and_tamper_detection(self):
        with tempfile.TemporaryDirectory() as root:
            data = b"Mayor: We will build a library."
            source = archive_source(Path(root), "P01", data, ".md")
            self.assertEqual(source["sha256"], hashlib.sha256(data).hexdigest())
            self.assertTrue(verify_source(source["path"], source["sha256"],
                                          "We will build a library."))
            Path(source["path"]).write_bytes(b"changed")
            self.assertFalse(verify_source(source["path"], source["sha256"],
                                           "We will build a library."))

    def test_unmatched_quote_and_path_traversal_fail(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(ValueError):
                archive_source(Path(root), "../escape", b"evidence", ".md")
            source = archive_source(Path(root), "P01", b"actual", ".md")
            self.assertFalse(verify_source(source["path"], source["sha256"], "invented"))


if __name__ == "__main__":
    unittest.main()
