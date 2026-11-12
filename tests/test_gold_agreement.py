"""Test arbitrator agreement against hand-labeled consensus gold benchmark."""

import json
from pathlib import Path


def test_gold_set_agreement():
    repo_root = Path(__file__).resolve().parent.parent
    gold_file = repo_root / "data" / "gold_set.json"
    data_file = repo_root / "docs" / "data.json"

    assert gold_file.exists(), "gold_set.json must exist"
    assert data_file.exists(), "docs/data.json must exist"

    with open(gold_file) as f:
        gold_data = json.load(f)

    with open(data_file) as f:
        export_data = json.load(f)

    gold_promises = gold_data.get("gold_promises", [])
    assert len(gold_promises) >= 20, "Gold set must contain at least 20 promises"

    export_map = {p["promise_id"]: p for p in export_data.get("promises", [])}

    agreements = 0
    total = len(gold_promises)
    disagreements = []

    for gp in gold_promises:
        pid = gp["promise_id"]
        consensus = gp["consensus_verdict"]
        p = export_map.get(pid)
        assert p is not None, f"Gold promise {pid} must be in published export"

        verdict = p.get("verdict")
        if verdict == consensus:
            agreements += 1
        else:
            disagreements.append(f"{pid} ({gp['entity']}): expected {consensus}, got {verdict}")

    agreement_rate = agreements / total
    print(f"\nGold set agreement: {agreements}/{total} ({agreement_rate * 100:.1f}%)")
    if disagreements:
        print("Disagreements:\n" + "\n".join(disagreements))

    # Bar: at least 90% agreement
    assert agreement_rate >= 0.90, f"Agreement rate {agreement_rate:.2f} is below 0.90 threshold"
