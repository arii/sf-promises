"""Generate data/gold_gate_expectations.json — the frozen evidence-bar gate.

Run from the repo root:

    python3 tests/generate_gold_gate_expectations.py

The file records, over the frozen gold set (data/gold_set.json):

- sha256 of every decision file whose edits are barred by the OD-22 spec
  (src/temporal.py, src/evidence.py, src/screening.py, src/lifecycle_rubric.py)
  and of the gold set itself;
- check_origin_dates outputs for deterministic date scenarios per gold promise;
- screen_saved_source outputs for deterministic archived-source fixtures per
  gold promise;
- parse_extraction golden outputs over a transcript fixture and a budget
  page-range slice (the OD-22 lane fixtures), with recorded model responses.

The committed file is a snapshot of CURRENT behavior. tests/test_evidence_bar_frozen.py
recomputes every recorded output and fails on any difference — byte-for-byte
proof that the bar did not move. Regenerate ONLY when a frozen file's change
was deliberately reviewed: the diff must show gold-set outputs unchanged.
"""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.extract import parse_extraction  # noqa: E402
from src.temporal import check_origin_dates  # noqa: E402
from src.evidence import screen_saved_source  # noqa: E402

FROZEN_FILES = (
    "src/temporal.py",
    "src/evidence.py",
    "src/screening.py",
    "src/lifecycle_rubric.py",
)

GOV_URLS = {
    "bos_transcript": "https://sfgov.legistar.com/View.ashx?M=A&ID=1462992&GUID=9E7FA469",
    "budget": "https://sfcontroller.org/sites/default/files/budget-fy25.pdf",
    "ballot": "https://sfelections.sfgov.org/sites/default/files/Documents/ballot-measure-m.pdf",
}

# Each gold promise walks a deterministic scenario cycle chosen to cover the
# gate's branches. Inputs are recorded, so the test recomputes them exactly.
def origin_dates_cases(gold_promises: list[dict]) -> list[dict]:
    cases = []
    for index, gold in enumerate(gold_promises):
        promised = date(2025, 1, 15) + timedelta(days=index)
        scenarios = [
            ("passing_origin", dict(promised=promised, published=promised - timedelta(days=2),
                                    deadline=promised + timedelta(days=90))),
            ("horizon_short", dict(promised=promised, published=promised - timedelta(days=2),
                                   deadline=promised + timedelta(days=30))),
            ("origin_date_missing", dict(promised=promised, published=None,
                                         deadline=promised + timedelta(days=90))),
            ("promise_date_missing", dict(promised=None, published=promised, deadline=None)),
            ("origin_predates_promise", dict(promised=promised, published=promised - timedelta(days=30),
                                             deadline=promised + timedelta(days=90))),
            ("origin_publication_late", dict(promised=promised, published=promised + timedelta(days=45),
                                             deadline=promised + timedelta(days=90))),
        ]
        name, inputs = scenarios[index % len(scenarios)]
        cases.append({
            "promise_id": gold["promise_id"],
            "scenario": name,
            "inputs": {k: (v.isoformat() if isinstance(v, date) else v)
                       for k, v in inputs.items()},
            "output": check_origin_dates(
                inputs["promised"], inputs["published"], inputs["deadline"]
            ),
        })
    # One historical-official pass: the late-publication branch the screening
    # code may excuse for TIER1_GOV origins, exercised with confirming text.
    gold = gold_promises[0]
    promised = date(2025, 1, 15)
    text = (f"Official proceedings record that the commitment was made on "
            f"{promised.isoformat()}: {gold['rationale']}")
    cases.append({
        "promise_id": gold["promise_id"],
        "scenario": "historical_official_confirmed",
        "inputs": {
            "promised": promised.isoformat(),
            "published": (promised + timedelta(days=45)).isoformat(),
            "deadline": (promised + timedelta(days=90)).isoformat(),
            "historical_official": True,
            "historical_origin_confirmed": True,
            "quote": gold["rationale"],
            "source_text": text,
        },
        "output": check_origin_dates(
            promised, promised + timedelta(days=45), promised + timedelta(days=90),
            historical_official=True, historical_origin_confirmed=True,
            quote=gold["rationale"], source_text=text,
        ),
    })
    return cases


def saved_source_cases(gold_promises: list[dict]) -> list[dict]:
    root = Path(tempfile.mkdtemp())
    cases = []
    lane_cycle = ("bos_transcript", "budget", "ballot")
    for index, gold in enumerate(gold_promises):
        lane = lane_cycle[index % len(lane_cycle)]
        scenario = index % 6
        text = (f"MINUTES OF PROCEEDINGS\n{gold['entity']} stated on the record: "
                f"{gold['rationale']}\nEnd of record.")
        quote = gold["rationale"]
        url, tier = GOV_URLS[lane], "TIER1_GOV"
        if scenario == 3:
            # The quote is genuinely absent from the archived text.
            text = "A record of proceedings about an unrelated matter."
        elif scenario == 4:
            tier = "TIER3_CANARY"
        elif scenario == 5:
            tier = "TIER9_SUSPECT"
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        promise_id = f"G{index:02d}"
        directory = root / promise_id
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{digest}.txt"
        path.write_text(text, encoding="utf-8")
        cases.append({
            "promise_id": promise_id,
            "gold_promise_id": gold["promise_id"],
            "lane": lane,
            "scenario": ("tier1_gov_pass", "tier1_gov_pass", "tier1_gov_pass",
                         "quote_not_found", "canary_not_evidence",
                         "source_tier_unknown")[scenario],
            "inputs": {
                "url": url, "source_tier": tier, "quote": quote,
                "text": text, "digest": digest,
            },
            "output": screen_saved_source(
                root=root, promise_id=promise_id, path=str(path),
                digest=digest, quote=quote, url=url, source_tier=tier,
            ),
        })
    return cases


TRANSCRIPT_TEXT = (
    "BOARD OF SUPERVISORS REGULAR MEETING — VERBATIM TRANSCRIPT\n"
    "Mayor Lurie: We will open the crisis triage center at 822 Geary "
    "by April 28, 2025, and we will fund it in the budget.\n"
    "End of transcript."
)
BUDGET_SLICE_TEXT = (
    "FY2025-26 Mayor's Proposed Budget — Chapter 1: Revenue Overview (pages 1-4)\n"
    "The city shall add 200 shelter beds by December 31, 2026.\n"
    "End of chapter slice."
)


def golden_extraction_cases() -> list[dict]:
    root = Path(tempfile.mkdtemp())
    cases = []
    for name, promise_id, text, response, published in (
        ("transcript_fixture", "harv-gold-transcript", TRANSCRIPT_TEXT,
         json.dumps({"candidates": [{
             "promise_id": "harv-gold-transcript",
             "promise_text": "We will open the crisis triage center at 822 Geary "
                             "by April 28, 2025",
             "speaker": "Mayor Lurie",
             "promised_date": "2025-01-15",
             "deadline": None,
         }]}),
         date(2025, 1, 13)),
        ("budget_slice_fixture", "harv-gold-budget-slice", BUDGET_SLICE_TEXT,
         json.dumps({"candidates": [{
             "promise_id": "harv-gold-budget-slice",
             "promise_text": "The city shall add 200 shelter beds by December 31, 2026",
             "speaker": "Mayor's Proposed Budget",
             "promised_date": "2025-06-01",
             "deadline": "2026-12-31",
         }]}),
         date(2025, 5, 30)),
    ):
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        directory = root / promise_id
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{digest}.txt"
        path.write_text(text, encoding="utf-8")
        candidates = parse_extraction(
            root=root, promise_id=promise_id, path=str(path), digest=digest,
            response=response, published=published,
        )
        cases.append({
            "name": name,
            "promise_id": promise_id,
            "inputs": {
                "source_text": text, "digest": digest, "response": response,
                "published": published.isoformat(),
            },
            "expected": [c.model_dump(mode="json") for c in candidates],
        })
    return cases


def main() -> None:
    gold = json.loads((REPO_ROOT / "data" / "gold_set.json").read_text(encoding="utf-8"))
    gold_promises = gold["gold_promises"]
    payload = {
        "description": (
            "Frozen evidence-bar gate for the OD-22 primary-source intake lane "
            "(spec D3). Generated by tests/generate_gold_gate_expectations.py; "
            "regenerate only after a reviewed, deliberate change to a frozen "
            "file — the regenerated outputs must be identical."
        ),
        "frozen_files": {
            name: hashlib.sha256((REPO_ROOT / name).read_bytes()).hexdigest()
            for name in FROZEN_FILES
        },
        "gold_set_sha256": hashlib.sha256(
            (REPO_ROOT / "data" / "gold_set.json").read_bytes()
        ).hexdigest(),
        "origin_dates": origin_dates_cases(gold_promises),
        "saved_source": saved_source_cases(gold_promises),
        "golden_extraction": golden_extraction_cases(),
    }
    target = REPO_ROOT / "data" / "gold_gate_expectations.json"
    target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {target} with {len(payload['origin_dates'])} origin-date, "
          f"{len(payload['saved_source'])} saved-source and "
          f"{len(payload['golden_extraction'])} extraction cases")


if __name__ == "__main__":
    main()
