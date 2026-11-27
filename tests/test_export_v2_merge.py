import copy
import json
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.database import initialize_database
from src.relevance import record_relevance
from src.site_merge import V2DatabaseError, merge_v2, validate_v2_database
from src.sources import archive_source
from tests.test_export import _load_exporter_module

ROOT = Path(__file__).resolve().parents[1]
URL = "https://www.sf.gov/news/v2-library-announcement"
TEXT = "Mayor Example said: We will build a library on Mission Street by 2025."
PROMISE = "We will build a library on Mission Street by 2025."


DELIVERY_TEXT = "The Mission Street library opened to the public on June 3, 2024."
VERIFIED = {"action": True, "promise_date": True, "deadline": True, "delivery": False,
            "survival": False, "entity_and_location": True, "explanation": "Verified."}


def make_v2(directory, promises, *, source_text=TEXT):
    """Build a tiny v2 database; each spec is a dict overriding the defaults.

    Spec keys: pid, text, quote, url, source_text, verdict, basis (date basis),
    deadline (default 2025-01-01, None for open-ended), extra (list of
    (phase, text, published) evidence rows), verifier (dict of review fields to
    override, or False for no verifier row), verifier_passed, outcome_basis
    (dict or None).
    """
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    db_path = initialize_database(directory / "promises.db")
    sources = directory / "sources"
    db = sqlite3.connect(db_path)
    db.execute("PRAGMA foreign_keys = ON")
    for spec in promises:
        pid = spec["pid"]
        text = spec.get("text", PROMISE)
        quote = spec.get("quote", TEXT)
        url = spec.get("url", URL)
        saved = archive_source(sources, pid, spec.get("source_text", source_text).encode(), ".md")
        db.execute("INSERT INTO candidates VALUES (?, ?)", (pid, f"slug-{pid.lower()}"))
        db.execute(
            "INSERT INTO promises VALUES (?, 'City Library Dept', 'City Agency', "
            "'Parks & Recreation', 'Citywide', ?, '2024-01-01', ?, "
            "'2024-01-02T00:00:00+00:00')",
            (pid, text, spec["deadline"] if "deadline" in spec else "2025-01-01"))
        db.execute(
            "INSERT INTO evidence_ledger (promise_id, phase, source_tier, url, "
            "local_source_path, content_sha256, verbatim_quote, quote_verified, "
            "verification_record_json, published_date, ingested_at) "
            "VALUES (?, 'ORIGIN', 'TIER1_GOV', ?, ?, ?, ?, 1, '{}', '2024-01-02', "
            "'2024-01-02T00:00:00+00:00')", (pid, url, saved["path"], saved["sha256"], quote))
        for number, (phase, extra_text, published) in enumerate(spec.get("extra", [])):
            extra_saved = archive_source(sources, pid, extra_text.encode(), ".md")
            db.execute(
                "INSERT INTO evidence_ledger (promise_id, phase, source_tier, url, "
                "local_source_path, content_sha256, verbatim_quote, quote_verified, "
                "verification_record_json, published_date, ingested_at) "
                "VALUES (?, ?, 'TIER1_GOV', ?, ?, ?, ?, 1, '{}', ?, '2024-06-01T00:00:00+00:00')",
                (pid, phase, f"https://www.sf.gov/news/{pid.lower()}-{phase.lower()}-{number}",
                 extra_saved["path"], extra_saved["sha256"], extra_text, published))
        if spec.get("verifier") is not False:
            review = {**VERIFIED, **spec.get("verifier", {})}
            db.execute(
                "INSERT INTO verifications (promise_id, check_type, passed, reason, checked_at, "
                "model_id) VALUES (?, 'independent_verifier', ?, ?, '2024-06-01T00:00:00+00:00', "
                "'model-x')", (pid, int(spec.get("verifier_passed", True)), json.dumps(review)))
        if spec.get("outcome_basis"):
            db.execute(
                "INSERT INTO verifications (promise_id, check_type, passed, reason, checked_at) "
                "VALUES (?, 'outcome_basis', 1, ?, '2024-06-01T00:00:00+00:00')",
                (pid, json.dumps(spec["outcome_basis"])))
        db.execute(
            "INSERT INTO verdicts (promise_id, verdict, reason, decided_at) VALUES (?, ?, ?, ?)",
            (pid, spec.get("verdict", "IN_PROGRESS"), "construction underway",
             "2024-06-01T00:00:00+00:00"))
        if spec.get("basis"):
            db.execute(
                "INSERT INTO verifications (promise_id, check_type, passed, reason, checked_at) "
                "VALUES (?, 'promise_date_basis', 1, ?, '2024-06-01T00:00:00+00:00')",
                (pid, json.dumps({"basis": spec["basis"], "note": "Dated from the page's byline",
                                  "promised_date": "2024-01-01", "published": "2024-01-02",
                                  "phrase": "today"})))
        db.commit()
        record_relevance(
            db, assessment_id=f"a-{pid}", promise_id=pid, promise_text=text,
            signals={"has_verbatim": True, "has_speaker": True, "has_date": True,
                     "names_sf_or_sf_address_agency_ordinance": True},
            evaluated_at=datetime(2024, 1, 2, tzinfo=timezone.utc))
    db.close()
    return db_path, sources


@pytest.fixture
def base():
    return json.loads((ROOT / "docs" / "data.json").read_text())


def run_merge(base, db_path, sources):
    payload = copy.deepcopy(base)
    return payload, merge_v2(payload, [(db_path, sources)])


def test_v2_record_is_added_with_mapped_fields(base, tmp_path):
    db, src = make_v2(tmp_path / "v2", [{"pid": "P901", "basis": "derived_from_publication"}])
    payload, report = run_merge(base, db, src)
    assert report["added"] == [{"promise_id": "P901", "verdict": "in_progress"}]
    record = payload["promises"][-1]
    assert record["promise_id"] == "P901" and record["pipeline"] == "v2"
    assert record["verdict"] == "in_progress"
    assert record["promise_text"] == PROMISE and record["entity"] == "City Library Dept"
    assert record["category"] == "Parks & Recreation" and record["neighborhood"] == "Citywide"
    assert record["source_url"] == URL and record["verbatim_quote"] == TEXT
    assert len(record["source_hash"]) == 64
    assert record["source_file_path"] == record["source_hash"] + ".md"
    assert record["promised_date"] == "2024-01-01" and record["due_date"] == "2025-01-01"
    assert record["decided_at"] == "2024-06-01T00:00:00+00:00"
    assert record["relevance"]["score"] >= 5
    # derived date reads as derived; verdict basis note rides along
    assert record["promise_date_derived"] is True
    assert record["promised_date_note"] == "Dated from the page's byline"
    assert record["verdict_reason"] == "construction underway"
    assert record["verdict_history"][-1]["verdict"] == "in_progress"
    assert any(v["check"] == "promise_date_basis" for v in record["verification_history"])
    # honest missingness: a citywide record gets the citywide display centroid
    # (is_centroid, never an address), not invented claim geography
    assert (record["latitude"], record["longitude"]) == (37.7749, -122.4194)
    assert record["is_centroid"] is True and record["address_full"] is None
    assert record["address_status"] == "not_applicable"
    assert record["completion_date_status"] == "not_yet_known"
    assert record["advocate_bundles"] == {}


def test_stated_basis_is_not_derived(base, tmp_path):
    db, src = make_v2(tmp_path / "v2", [{"pid": "P901", "basis": "stated"}])
    payload, _ = run_merge(base, db, src)
    assert payload["promises"][-1]["promise_date_derived"] is False


def test_existing_records_unchanged_and_counts_updated(base, tmp_path):
    db, src = make_v2(tmp_path / "v2", [{"pid": "P901"}, {"pid": "P902", "verdict": "KEPT",
        "text": "We will build a clinic on Valencia Street by 2025.",
        "quote": "Mayor Example said: We will build a clinic on Valencia Street by 2025.",
        "url": "https://www.sf.gov/news/v2-clinic", "source_text":
        "Mayor Example said: We will build a clinic on Valencia Street by 2025.",
        "extra": [("DELIVERY", DELIVERY_TEXT, "2024-06-03")],
        "verifier": {"delivery": True}}])
    payload, report = run_merge(base, db, src)
    n = len(base["promises"])
    assert payload["promises"][:n] == base["promises"]
    assert [p["promise_id"] for p in payload["promises"][n:]] == ["P901", "P902"]
    status = payload["database_status"]
    assert status["tracked_count"] == n + 2 and status["v2_promises_added"] == 2
    assert status["counts"]["kept"] == base["database_status"]["counts"]["kept"] + 1
    assert status["counts"]["in_progress"] == base["database_status"]["counts"]["in_progress"] + 1
    assert sum(status["counts"].values()) == sum(base["database_status"]["counts"].values()) + 2
    assert status["v2_merge"]["added_by_verdict"] == {"in_progress": 1, "kept": 1}
    assert f"{n + 2} published (2 from v2 pipeline)" in status["id_reconciliation"]
    assert payload["metadata"]["v2_promises_added"] == 2
    assert payload["promises"][-1]["impact_rank"] == n + 2
    assert report["added_by_verdict"] == {"in_progress": 1, "kept": 1}


def test_colliding_id_gets_prefix(base, tmp_path):
    db, src = make_v2(tmp_path / "v2", [{"pid": "P02"}])
    payload, report = run_merge(base, db, src)
    assert report["added"][0]["promise_id"] == "V2-P02"
    assert sum(p["promise_id"] == "P02" for p in payload["promises"]) == 1
    assert payload["promises"][-1]["v2_promise_id"] == "P02"


def test_tampered_source_is_rejected_and_not_published(base, tmp_path):
    db, src = make_v2(tmp_path / "v2", [{"pid": "P901"}])
    next((src / "P901").glob("*.md")).write_text(TEXT + " (edited)")
    payload, report = run_merge(base, db, src)
    assert report["added"] == []
    assert report["rejected"][0]["promise_id"] == "P901"
    assert "source_hash_mismatch" in report["rejected"][0]["reason"]
    assert payload["promises"] == base["promises"]
    assert payload["database_status"]["v2_promises_added"] == 0


def test_missing_source_and_unfound_quote_are_rejected(base, tmp_path):
    db, src = make_v2(tmp_path / "v2", [
        {"pid": "P901"},
        {"pid": "P902", "quote": "Mayor Example said: We will build a library on Mission Street by 2025. Extra words",
         "source_text": TEXT}])
    next((src / "P901").glob("*.md")).unlink()
    _, report = run_merge(base, db, src)
    reasons = {r["promise_id"]: r["reason"] for r in report["rejected"]}
    assert "source_unavailable" in reasons["P901"]
    assert "quote_not_found" in reasons["P902"]
    assert report["added"] == []


def test_duplicate_of_existing_record_is_skipped(base, tmp_path):
    existing = base["promises"][0]
    db, src = make_v2(tmp_path / "v2", [
        {"pid": "P901", "text": existing["promise_text"],
         "quote": existing["promise_text"], "source_text": existing["promise_text"]},
    ])
    payload, report = run_merge(base, db, src)
    assert report["added"] == []
    assert report["duplicates"][0]["promise_id"] == "P901"
    assert report["duplicates"][0]["reason"] == "same_promise_text"
    assert payload["promises"] == base["promises"]


def test_same_url_with_overlapping_quote_is_skipped(base, tmp_path):
    first, first_src = make_v2(tmp_path / "a", [{"pid": "P901"}])
    payload, report = run_merge(base, first, first_src)
    assert len(report["added"]) == 1
    # A second database publishes a differently worded promise from the same page quote.
    second, second_src = make_v2(tmp_path / "b", [{"pid": "P950", "text": "We will build a library on Mission Street"}])
    report2 = merge_v2(payload, [(second, second_src)])
    assert report2["added"] == []
    assert report2["duplicates"][0]["reason"].startswith("same_source_overlapping_quote:P901")


def test_unsupported_database_is_refused(tmp_path):
    other = tmp_path / "other.db"
    sqlite3.connect(other).close()
    with pytest.raises(V2DatabaseError):
        validate_v2_database(other)
    db, _ = make_v2(tmp_path / "v2", [{"pid": "P901"}])
    with sqlite3.connect(db) as conn:
        conn.execute("PRAGMA user_version = 3")
    with pytest.raises(V2DatabaseError):
        validate_v2_database(db)


def test_v2_database_and_sources_are_not_modified(base, tmp_path):
    db, src = make_v2(tmp_path / "v2", [{"pid": "P901"}])
    before = {p: p.read_bytes() for p in [db, *src.rglob("*.md")]}
    run_merge(base, db, src)
    assert {p: p.read_bytes() for p in before} == before
    assert not Path(str(db) + "-wal").exists()


def test_apply_v2_merge_rewrites_only_the_staged_export(base, tmp_path):
    exporter = _load_exporter_module()
    staging = tmp_path / "staging"
    staging.mkdir()
    shutil.copyfile(ROOT / "docs" / "data.json", staging / "data.json")
    live_before = (ROOT / "docs" / "data.json").read_bytes()
    legacy_text = (staging / "data.json").read_text()
    db, src = make_v2(tmp_path / "v2", [{"pid": "P901"}])
    report = exporter.apply_v2_merge(staging, [(db, src)])
    assert len(report["added"]) == 1
    merged = json.loads((staging / "data.json").read_text())
    assert merged["promises"][-1]["promise_id"] == "P901"
    assert merged["promises"][:-1] == base["promises"]
    assert (staging / "data.js").read_text().startswith("/* SF Promises")
    assert (ROOT / "docs" / "data.json").read_bytes() == live_before
    assert legacy_text != (staging / "data.json").read_text()
    with pytest.raises(ValueError):
        exporter.apply_v2_merge(ROOT / "docs", [(db, src)])


def test_cli_merges_v2_after_legacy_export(tmp_path):
    import subprocess
    import sys
    from tests.test_export import _make_history_fixture_db
    legacy = tmp_path / "legacy"
    legacy.mkdir()
    _make_history_fixture_db(legacy / "promises.db")
    db, _ = make_v2(tmp_path / "v2", [{"pid": "P901"}])
    out = tmp_path / "out"
    result = subprocess.run(
        [sys.executable, "docs/export_data.py", "--db", str(legacy / "promises.db"),
         "--output-dir", str(out), "--v2-db", str(db)],
        capture_output=True, text=True, cwd=ROOT)
    assert result.returncode == 0, result.stderr
    assert "v2 merge: added 1" in result.stdout
    data = json.loads((out / "data.json").read_text())
    assert data["promises"][-1]["pipeline"] == "v2"
    assert data["database_status"]["v2_promises_added"] == 1
    assert "P901" in (out / "data.js").read_text()
    bad = subprocess.run(
        [sys.executable, "docs/export_data.py", "--db", str(legacy / "promises.db"),
         "--output-dir", str(tmp_path / "out2"), "--v2-db", str(legacy / "promises.db")],
        capture_output=True, text=True, cwd=ROOT)
    assert bad.returncode != 0
    assert not (tmp_path / "out2" / "data.json").exists()


# --- verdict must be supported by evidence and verifier rows -----------------

def merged(base, tmp_path, spec):
    db, src = make_v2(tmp_path / "v2", [spec])
    return run_merge(base, db, src)


def rejected_reason(report):
    assert report["added"] == []
    return report["rejected"][0]["reason"]


DELIVERY = ("DELIVERY", DELIVERY_TEXT, "2024-06-03")
SURVIVAL = ("SURVIVAL", "The Mission Street library closed permanently in 2025.", "2025-03-01")


@pytest.mark.parametrize("verdict,extra,reason", [
    ("KEPT", [], "verdict_unsupported:no_delivery_evidence"),
    ("DELAYED_OR_PARTIAL", [], "verdict_unsupported:no_delivery_evidence"),
    ("KEPT_THEN_REVERSED", [], "verdict_unsupported:no_delivery_evidence"),
    ("KEPT_THEN_REVERSED", [DELIVERY], "verdict_unsupported:no_survival_evidence"),
    ("BROKEN", [], "verdict_unsupported:no_contrary_evidence"),
    # An outcome row dated before the promise cannot be delivery evidence.
    ("KEPT", [("DELIVERY", DELIVERY_TEXT, "2023-06-03")], "verdict_unsupported:no_delivery_evidence"),
])
def test_verdict_without_matching_evidence_is_rejected(base, tmp_path, verdict, extra, reason):
    _, report = merged(base, tmp_path, {
        "pid": "P901", "verdict": verdict, "extra": extra,
        "verifier": {"delivery": True, "survival": True}})
    assert rejected_reason(report) == reason


def test_origin_only_in_progress_and_undecided_are_accepted(base, tmp_path):
    for verdict in ("IN_PROGRESS", "UNDECIDED"):
        payload, report = merged(base, tmp_path / verdict, {"pid": "P901", "verdict": verdict})
        record = payload["promises"][-1]
        assert report["added"] and record["verdict"] == verdict.lower()
        assert record["all_checks_passed"] is True and record["failed_check_names"] == []
        assert record["has_contradictory_evidence"] is False


@pytest.mark.parametrize("spec,reason", [
    ({"verifier": False}, "no_passed_independent_verifier"),
    ({"verifier_passed": False}, "no_passed_independent_verifier"),
    ({"verifier": {"action": False}}, "verifier_did_not_confirm"),
    ({"verifier": {"deadline": False}}, "verifier_did_not_confirm"),
    ({"verdict": "KEPT", "extra": [DELIVERY], "verifier": {"delivery": False}},
     "verifier_did_not_confirm"),
])
def test_independent_verifier_must_have_passed_and_confirmed(base, tmp_path, spec, reason):
    _, report = merged(base, tmp_path, {"pid": "P901", **spec})
    assert rejected_reason(report) == f"verdict_unsupported:{reason}"


def test_kept_with_delivery_evidence_computes_checks_from_data(base, tmp_path):
    payload, report = merged(base, tmp_path, {
        "pid": "P901", "verdict": "KEPT", "extra": [DELIVERY], "verifier": {"delivery": True}})
    record = payload["promises"][-1]
    assert report["added"] and record["verdict"] == "kept"
    checks = {c["check"]: c["passed"] for c in record["checks"]}
    assert checks["verdict_evidence"] is True and checks["independent_verifier"] is True
    assert record["all_checks_passed"] is True and record["failed_check_count"] == 0
    assert record["has_contradictory_evidence"] is False
    assert [e["phase"] for e in record["evidence"]] == ["ORIGIN", "DELIVERY"]


def test_broken_and_reversed_records_are_marked_contradictory(base, tmp_path):
    payload, _ = merged(base, tmp_path / "a", {
        "pid": "P901", "verdict": "BROKEN", "extra": [DELIVERY], "verifier": {"delivery": True}})
    assert payload["promises"][-1]["has_contradictory_evidence"] is True
    payload, _ = merged(base, tmp_path / "b", {
        "pid": "P901", "verdict": "KEPT_THEN_REVERSED", "extra": [DELIVERY, SURVIVAL],
        "verifier": {"delivery": True, "survival": True}})
    assert payload["promises"][-1]["has_contradictory_evidence"] is True


# --- open-ended and short-horizon records (R1/R2) -----------------------------

OPEN_ENDED_BASIS = {"rules": ["R1", "R5"], "outcome_rule": "R5", "open_ended": True,
                    "deadline": None, "reason": "no outcome evidence found",
                    "relied_on": [], "verdict": "UNDECIDED"}
ONE_OFF_TEXT = "Mayor Example said: The library will open on January 5, 2024."
ONE_OFF_PROMISE = "The library will open on January 5, 2024."


def one_off(**overrides):
    spec = {"pid": "P901", "text": ONE_OFF_PROMISE, "quote": ONE_OFF_TEXT,
            "source_text": ONE_OFF_TEXT, "deadline": "2024-01-05", "verdict": "IN_PROGRESS",
            "outcome_basis": {**OPEN_ENDED_BASIS, "rules": ["R2", "R3"], "open_ended": False,
                              "outcome_rule": "R3", "deadline": "2024-01-05",
                              "reason": "deadline in the future", "verdict": "IN_PROGRESS"}}
    spec.update(overrides)
    return spec


def test_open_ended_record_reaches_the_site_with_null_deadline(base, tmp_path):
    payload, report = merged(base, tmp_path, {
        "pid": "P901", "deadline": None, "verdict": "UNDECIDED",
        "outcome_basis": OPEN_ENDED_BASIS})
    assert report["added"] == [{"promise_id": "P901", "verdict": "undecided"}]
    record = payload["promises"][-1]
    assert record["due_date"] is None and record["deadline_date"] is None
    assert record["due_date_status"] == "not_applicable"
    assert record["due_date_precision"] == "not_applicable"
    assert record["due_date_display"] == "No fixed deadline"
    assert record["completion_date_status"] == "not_yet_known"


def test_null_deadline_without_a_recorded_basis_is_rejected(base, tmp_path):
    _, report = merged(base, tmp_path, {"pid": "P901", "deadline": None, "verdict": "UNDECIDED"})
    assert rejected_reason(report) == "origin_evidence_missing"
    # A basis that does not name R1 does not waive the missing deadline either.
    _, report = merged(base, tmp_path / "b", {
        "pid": "P901", "deadline": None, "verdict": "UNDECIDED",
        "outcome_basis": {**OPEN_ENDED_BASIS, "rules": ["R5"]}})
    assert rejected_reason(report) == "origin_evidence_missing"


def test_short_horizon_with_deadline_in_the_quote_is_accepted_when_recorded(base, tmp_path):
    payload, report = merged(base, tmp_path, one_off())
    assert report["added"] == [{"promise_id": "P901", "verdict": "in_progress"}]
    assert payload["promises"][-1]["due_date"] == "2024-01-05"


@pytest.mark.parametrize("overrides", [
    # deadline not stated by the quote
    {"text": "The library will open soon.", "quote": "Mayor Example said: The library will open soon.",
     "source_text": "Mayor Example said: The library will open soon."},
    # no outcome basis row in the database
    {"outcome_basis": None},
    # basis row does not name R2
    {"outcome_basis": {**OPEN_ENDED_BASIS, "rules": ["R3"], "open_ended": False,
                       "deadline": "2024-01-05", "verdict": "IN_PROGRESS"}},
])
def test_short_horizon_without_quote_or_record_is_rejected(base, tmp_path, overrides):
    _, report = merged(base, tmp_path, one_off(**overrides))
    assert rejected_reason(report) == "origin_evidence_missing"


def test_invalid_outcome_basis_is_rejected(base, tmp_path):
    db, src = make_v2(tmp_path / "v2", [{"pid": "P901"}])
    with sqlite3.connect(db) as conn:
        conn.execute("INSERT INTO verifications (promise_id, check_type, passed, reason, "
                     "checked_at) VALUES ('P901', 'outcome_basis', 1, 'not json', "
                     "'2024-06-02T00:00:00+00:00')")
    _, report = run_merge(base, db, src)
    assert rejected_reason(report) == "outcome_basis_invalid"


# --- outcome basis reaches the site record -------------------------------------

def test_outcome_basis_is_carried_into_the_record(base, tmp_path):
    basis = {"rules": ["R4"], "outcome_rule": "R4", "open_ended": True, "deadline": None,
             "reason": "current status not checked", "relied_on": ["DELIVERY"], "verdict": "KEPT"}
    payload, report = merged(base, tmp_path, {
        "pid": "P901", "deadline": None, "verdict": "KEPT", "extra": [DELIVERY],
        "verifier": {"delivery": True}, "outcome_basis": {**basis, "rules": ["R1", "R4"]}})
    assert report["added"]
    assert payload["promises"][-1]["outcome_basis"] == {
        "rules": ["R1", "R4"], "outcome_rule": "R4", "open_ended": True,
        "reason": "current status not checked", "relied_on": ["DELIVERY"],
        "status_not_checked": True}


def test_record_without_outcome_basis_has_no_field(base, tmp_path):
    payload, _ = merged(base, tmp_path, {"pid": "P901"})
    assert "outcome_basis" not in payload["promises"][-1]


# Display text widens a fragment quote to its sentence in the same saved bytes.
import pytest as _pytest
from src.site_merge import display_sentence as _display_sentence


@_pytest.mark.parametrize("text, quote, expected", [
    ("officials.\n\nInstallation is expected to be completed around Nov. 21, with the barriers "
     "remaining in place through April 2027.\n\nThe temporary",
     "21, with the barriers remaining in place through April 2027.",
     "Installation is expected to be completed around Nov. 21, with the barriers remaining in "
     "place through April 2027."),
    ("Targets: Shelter\nShelter Beds\nBetween July 2023 and June 2028,\nthe goal is to add 1,075 new\n"
     "shelter beds.\nIn FY 2023-24",
     "the goal is to add 1,075 new",
     "Between July 2023 and June 2028, the goal is to add 1,075 new shelter beds."),
    ("the coast. We anticipate construction to start in \nlate 2027.\n\nOcean Beach",
     "We anticipate construction to start in",
     "We anticipate construction to start in late 2027."),
    ("Mayor said. Construction is slated to begin in early 2027. Every veteran",
     "Construction is slated to begin in early 2027.",
     "Construction is slated to begin in early 2027."),
])
def test_display_sentence_widens_fragments(text, quote, expected):
    assert _display_sentence(text, quote) == expected
    assert quote.split()[0] in expected


def test_display_sentence_missing_or_too_long():
    assert _display_sentence("Nothing here.", "absent quote") is None
    long_text = "word " * 200 + "the quote " + "word " * 200
    assert _display_sentence(long_text, "the quote") is None


def test_centroids_cover_every_neighborhood_label():
    from src.geo_centroids import LOCATION_CENTROIDS
    from src.taxonomy import LOCATIONS
    assert set(LOCATIONS) - set(LOCATION_CENTROIDS) == {"Regional / Northern California", "Not stated"}
    for lat, lon in LOCATION_CENTROIDS.values():
        assert 37.70 <= lat <= 37.83 and -122.52 <= lon <= -122.35


def test_regional_record_gets_no_map_point():
    from src.site_merge import _centroid_fields
    assert _centroid_fields("Regional / Northern California") == {}
    assert _centroid_fields("Mission") == {"latitude": 37.7599, "longitude": -122.4148}


def test_contradictory_v2_record_gets_inspectable_summaries():
    from src.site_merge import _evidence_summaries
    item = {"latest": {"verdict": "BROKEN"},
            "origin": {"verbatim_quote": "The plaza will reopen in 2023."},
            "evidence": [{"phase": "ORIGIN", "verbatim_quote": "The plaza will reopen in 2023."},
                         {"phase": "DELIVERY", "verbatim_quote": "The plaza remains closed in 2025."}],
            "outcome_basis": {"reason": "deadline passed"}}
    out = _evidence_summaries(item, True)
    assert out["supporting_evidence_summary"] == "The plaza remains closed in 2025."
    assert out["contradicting_evidence_summary"].endswith("The plaza will reopen in 2023.")
    assert "deadline passed" in out["arbitration_rule_explanation"]
    assert _evidence_summaries(item, False) == {}


def test_editorial_titles_and_exclusions_are_valid():
    from src.site_merge import load_editorial
    ed = load_editorial()
    assert ed["titles"], "config/v2_editorial.json carries titles"
    assert set(ed["exclude"]) <= set(ed["titles"])
    assert all(0 < len(t) <= 70 for t in ed["titles"].values())


def test_missing_editorial_file_is_empty(tmp_path):
    from src.site_merge import load_editorial
    assert load_editorial(tmp_path / "absent.json") == {"titles": {}, "exclude": {}}
