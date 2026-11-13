"""Unit and pipeline tests for the 3-stage outcome-blind sourcing pipeline (src/sourcing/)."""

import csv
import json
from pathlib import Path

import pytest

from src.sourcing.harvester import DiscoveryHarvester, classify_discovery_tier
from src.sourcing.planner import (
    SF_SUPERVISOR_DISTRICTS,
    TEN_CONTENT_PILLARS,
    SearchPlanner,
    validate_outcome_blind_query,
)
from src.sourcing.qualification import QualificationIntakeAgent, strip_outcome_fields

ROOT = Path(__file__).resolve().parent.parent


def test_search_planner_stratified_and_outcome_blind():
    planner = SearchPlanner(max_civic_share=0.25)
    specs = planner.generate_stratified_queries(max_per_pillar=2)

    assert len(specs) == 18
    covered_pillars = {s.pillar for s in specs}
    assert covered_pillars == set(TEN_CONTENT_PILLARS.keys())

    covered_districts = {s.supervisor_district for s in specs}
    assert covered_districts == set(SF_SUPERVISOR_DISTRICTS.keys())

    # Gap districts (2, 4, 8, 11) must be prioritized in early slots
    assert {s.supervisor_district for s in specs[:4]} == {2, 4, 8, 11}

    civic_housing = sum(1 for s in specs if s.pillar in ("Civic Life", "Housing & Neighborhoods"))
    assert civic_housing / len(specs) <= 0.25

    for spec in specs:
        assert validate_outcome_blind_query(spec.query_text) == []


@pytest.mark.parametrize("banned_word", ["broken", "failed", "kept", "scandal", "delayed"])
def test_planner_rejects_banned_outcome_terms(banned_word):
    violations = validate_outcome_blind_query(f'"San Francisco" "Sunset" {banned_word} project')
    assert banned_word in violations


def test_harvester_sha256_and_tier_classification(tmp_path):
    harvester = DiscoveryHarvester(archive_root=tmp_path)
    raw = b"# City Announcement\nThe SFMTA will open the new Sunset bikeway next fall.\n"
    excerpt = "The SFMTA will open the new Sunset bikeway next fall."

    doc = harvester.ingest_raw_document(
        candidate_id="CAND-TEST-01",
        url="https://www.sfmta.com/projects/sunset-bikeway",
        raw_bytes=raw,
        excerpt=excerpt,
        published_at="2025-03-10",
    )
    assert len(doc.content_sha256) == 64
    assert doc.source_tier == "TIER1_PRIMARY"
    assert doc.allowlisted is True
    assert (tmp_path / "CAND-TEST-01" / f"{doc.content_sha256}.md").exists()

    with pytest.raises(ValueError, match="Verbatim excerpt"):
        harvester.ingest_raw_document(
            candidate_id="CAND-TEST-02",
            url="https://www.sfmta.com/projects/sunset-bikeway",
            raw_bytes=raw,
            excerpt="Non-existent fabricated sentence",
        )

    assert classify_discovery_tier("https://missionlocal.org/2025/05/example/") == "TIER2_CONTEMPORANEOUS_NEWS"
    assert classify_discovery_tier("https://random-blog.example.com/post") == "TIER3_DISCOVERY_ONLY"


def test_qualification_strips_outcome_fields_and_evaluates():
    raw_candidate = {
        "candidate_id": "CAND-QUAL-01",
        "entity": "SFMTA",
        "promise_text": "SFMTA will construct 4 miles of protected bikeway along Sunset Boulevard by December 2026.",
        "source_url": "https://www.sfmta.com/projects/sunset-corridor",
        "source_tier": "TIER1_PRIMARY",
        "promised_date": "2025-02-15",
        "due_date": "2026-12-31",
        "supervisor_district": 4,
        "neighborhood": "Outer Sunset",
        # Outcome fields that MUST be stripped before evaluation
        "verdict": "broken",
        "verdict_reason": "Missed target",
        "factual_outcome": "Never built",
        "completion_date": "2026-11-01",
    }
    stripped = strip_outcome_fields(raw_candidate)
    for leak in ("verdict", "verdict_reason", "factual_outcome", "completion_date"):
        assert leak not in stripped

    agent = QualificationIntakeAgent()
    res = agent.evaluate_candidate(
        raw_candidate,
        source_batch="unit_test",
        discovery_channel="stratified_planner",
    )
    assert res.qualification_status == "qualified"
    assert res.outcome_blind_verified is True
    assert res.pillar == "Transit & Movement"
    assert res.supervisor_district == 4
    assert res.due_date_status == "present"


def test_intake_candidate_register_and_ledger_counts():
    reg_path = ROOT / "data" / "intake_candidate_register.json"
    csv_path = ROOT / "data" / "intake_ledger.csv"
    assert reg_path.exists()
    assert csv_path.exists()

    with reg_path.open("r", encoding="utf-8") as f:
        reg = json.load(f)
    summary = reg["summary"]
    assert summary["encountered_count"] == 63
    assert summary["qualified_count"] == 24
    assert summary["needs_review_count"] == 38
    assert summary["rejected_count"] == 1

    with csv_path.open("r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 63
