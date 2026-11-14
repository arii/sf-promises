"""Verify all 8 data-quality audit fixes in docs/data.json and data/evidence_review_queue.json."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_JSON = ROOT / "docs" / "data.json"
QUEUE_JSON = ROOT / "data" / "evidence_review_queue.json"


def _load_data():
    with DATA_JSON.open("r", encoding="utf-8") as f:
        return json.load(f)


def test_core_dataset_counts():
    data = _load_data()
    promises = data["promises"]
    quarantined = data["quarantined"]
    assert len(promises) == 54
    # 13 quarantined rows: 12 planted test cases plus the DB-derived P68 row.
    assert len(quarantined) == 13


def test_fix1_explicit_date_precision():
    data = _load_data()
    promises = data["promises"]
    valid_prec = {"day", "month", "year"}
    # not_captured: the enricher's marker for a due date a broken/undecided
    # promise should have had but whose precision was never captured
    # (scripts/enrich_dataset.py). The stale pre-3a3017c snapshot never
    # surfaced it; regenerated exports do.
    valid_optional_prec = valid_prec | {"not_applicable", "not_recorded", "not_captured", None}
    by_id = {p["promise_id"]: p for p in promises}

    for p in promises:
        assert p.get("promise_date_precision") in valid_prec
        assert p.get("due_date_precision") in valid_optional_prec
        assert p.get("completion_date_precision") in valid_optional_prec

    for pid in ("P09", "P18", "P62"):
        rec = by_id[pid]
        assert rec["promise_date_precision"] == "year"
        assert "-01-01" not in str(rec.get("promised_date_display", ""))


def test_fix2_evidence_reconciliation():
    data = _load_data()
    promises = data["promises"]
    recon = data["database_status"]["evidence_reconciliation"]

    assert recon["total_database_evidence_records"] == 124
    total_parts = (
        recon["verdict_cited_evidence_records"]
        + recon["background_context_records"]
        + recon["intake_screening_records"]
        + recon["duplicate_or_superseded_records"]
    )
    assert recon["verdict_cited_evidence_records"] == 99
    assert total_parts == 124

    for p in promises:
        assert p["verdict_supporting_evidence_count"] >= 1, (
            f"{p['promise_id']} has zero verdict_supporting_evidence_count"
        )
        assert isinstance(p["affirming_evidence_count"], int)
        assert isinstance(p["refuting_evidence_count"], int)


def test_fix3_verification_exceptions_exposed():
    data = _load_data()
    promises = data["promises"]
    passing = [p for p in promises if p.get("all_checks_passed") is True]
    failing = [p for p in promises if p.get("all_checks_passed") is False]

    # E1b re-export from the live DB: P83's authenticity_domain was resolved
    # by human review, and P17/P37/P58 carry no verification rows in the DB
    # at all (their recorded failures date to an older DB generation not
    # present in the current one).
    assert len(passing) == 51
    assert len(failing) == 3
    assert {p["promise_id"] for p in failing} == {"P82", "P61", "P57"}
    assert sum(p.get("failed_check_count", 0) for p in promises) == 3


def test_fix4_contradictory_evidence_inspectable():
    data = _load_data()
    promises = data["promises"]
    contra = [p for p in promises if p.get("has_contradictory_evidence") is True]
    assert len(contra) == 21
    for p in contra:
        assert p.get("supporting_evidence_summary"), f"{p['promise_id']} missing supporting summary"
        assert p.get("contradicting_evidence_summary"), f"{p['promise_id']} missing contradicting summary"
        assert p.get("arbitration_rule_explanation"), f"{p['promise_id']} missing arbitration explanation"


def test_fix5_canonical_entity_classification():
    data = _load_data()
    promises = data["promises"]
    allowed_cats = {
        "politician",
        "city_department",
        "corporation",
        "sports_team",
        "cultural_organization",
    }
    canonical_entities = set()
    for p in promises:
        canonical_entities.add(p["entity_canonical_name"])
        assert p.get("entity_category_canonical") in allowed_cats
        assert "entity_type_legacy" in p
        cnt = p.get("entity_promise_count")
        assert isinstance(cnt, int) and cnt >= 1
        assert p.get("entity_sample_warning") == (cnt < 3)

    assert len(canonical_entities) == 31


def test_fix6_geographic_scope_and_p64_treasure_island():
    data = _load_data()
    promises = data["promises"]
    allowed_scopes = {"exact_address", "neighborhood", "district", "regional", "citywide"}
    by_id = {p["promise_id"]: p for p in promises}

    exact_count = 0
    centroid_count = 0
    for p in promises:
        scope = p.get("geographic_scope")
        assert scope in allowed_scopes
        assert p.get("is_centroid") == (scope != "exact_address")
        if p["is_centroid"]:
            centroid_count += 1
        else:
            exact_count += 1

    assert exact_count == 12
    assert centroid_count == 42

    p64 = by_id["P64"]
    assert "Treasure Island" in p64["neighborhood_canonical"]
    assert p64["supervisor_district"] == 6


def test_fix7_explicit_missingness_semantics():
    data = _load_data()
    promises = data["promises"]
    allowed_missing = {"present", "not_applicable", "not_yet_known", "not_captured"}
    for p in promises:
        for field in ("due_date_status", "completion_date_status", "address_status", "district_status"):
            assert p.get(field) in allowed_missing, f"{p['promise_id']} invalid {field}={p.get(field)}"


def test_fix8_evidence_review_queue_artifact():
    data = _load_data()
    db_q = data["database_status"]["evidence_review_queue"]
    assert QUEUE_JSON.exists()
    with QUEUE_JSON.open("r", encoding="utf-8") as f:
        disk_q = json.load(f)

    assert db_q["priority_1_evidence_reconciliation_count"] == 7
    # DB-derived queue after the E1b re-export: P83 resolved, P17/P37/P58
    # have no verification rows in the current DB (see test_fix3).
    assert db_q["priority_2_verification_exceptions_count"] == 3
    assert db_q["priority_3_contradictions_and_credibility_count"] == 21
    assert db_q["total_verification_exception_checks"] == 3
    assert disk_q == db_q
