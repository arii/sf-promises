"""Tests for Hugging Face multi-config staging and dataset viewer split isolation."""

import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "upload_to_huggingface.py"


def test_hf_validate_only_staging_and_splits(tmp_path):
    staging = tmp_path / "hf_stage"
    res = subprocess.run(
        [sys.executable, str(SCRIPT), "--validate-only", "--staging-dir", str(staging)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=True,
    )
    assert "Validate-only mode complete" in res.stdout

    readme_text = (staging / "README.md").read_text(encoding="utf-8")
    for cfg in ("default", "commitments", "standardized_16col", "quarantined", "intake_ledger"):
        assert f"config_name: {cfg}" in readme_text
    assert "path: data/commitments/train.csv" in readme_text
    assert "path: data/standardized_16col/train.csv" in readme_text
    assert "path: data/quarantined/train.csv" in readme_text
    assert "path: data/intake_ledger/train.csv" in readme_text

    expected_splits = {
        "data/commitments/train.csv": (54, 73),
        "data/standardized_16col/train.csv": (54, 16),
        "data/quarantined/train.csv": (13, 10),
        "data/intake_ledger/train.csv": (63, 23),
    }
    for rel, (exp_rows, exp_cols) in expected_splits.items():
        p = staging / rel
        assert p.exists()
        with p.open("r", encoding="utf-8") as f:
            rows = list(csv.reader(f))
        assert len(rows) == exp_rows + 1
        assert len(rows[0]) == exp_cols

    with (staging / "data/commitments/train.csv").open("r", encoding="utf-8") as f:
        header = next(csv.reader(f))
    for col in (
        "record_type",
        "pillar",
        "promise_date_precision",
        "due_date_precision",
        "geographic_scope",
        "is_centroid",
        "all_checks_passed",
        "failed_check_count",
        "entity_category_canonical",
        "entity_sample_warning",
        "verdict_supporting_evidence_count",
        "due_date_status",
    ):
        assert col in header

    schema = json.loads((staging / "SCHEMA.json").read_text(encoding="utf-8"))
    assert "all_checks_passed" in schema["properties"]
    assert "is_centroid" in schema["properties"]
