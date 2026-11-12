"""
Unit and integration tests for the SF Promises Discovery & Verification Playbook Engine.
"""

import asyncio
from datetime import date
import pytest

from src.playbook_verifier import (
    TIER_1_GOV,
    TIER_2_NEWS,
    TIER_3_DATA,
    TIER_4_COMMUNITY,
    classify_source_tier,
    check_is_vague_promise,
    build_evidence_item,
    synthesize_verdict,
    run_parallel_verification,
)


def test_classify_source_tiers():
    tier, s_type, cred, strength = classify_source_tier("https://sf.gov/news/crisis-center")
    assert tier == TIER_1_GOV
    assert s_type == "official_government"
    assert cred == 10
    assert strength >= 0.95

    tier, s_type, cred, strength = classify_source_tier("https://data.sfgov.org/Housing/dataset")
    assert tier == TIER_3_DATA
    assert s_type == "public_dataset"

    tier, s_type, cred, strength = classify_source_tier("https://missionlocal.org/2024/05/housing-stall/")
    assert tier == TIER_2_NEWS
    assert s_type == "news_investigative"
    assert strength >= 0.80

    tier, s_type, cred, strength = classify_source_tier("https://twitter.com/random_user/status/123")
    assert tier == TIER_4_COMMUNITY
    assert strength <= 0.70


def test_vague_promise_detection():
    vague_text = "Improve public safety and support community in the Tenderloin"
    assert check_is_vague_promise(vague_text) is True

    specific_text = "Hire 200 new sworn police officers and reduce response times to 5 minutes by 2026"
    assert check_is_vague_promise(specific_text) is False

    res = synthesize_verdict("TEST-VAGUE", vague_text, "2026-12-31", [])
    assert res.is_vague is True
    assert res.verdict == "undecided"
    assert res.confidence == 0.45


def test_kept_verdict_high_confidence():
    ev1 = build_evidence_item(
        "P02", 1, "https://sf.gov/news/crisis-center-open",
        "The 24/7 Crisis Stabilization Center officially opened today at 822 Geary St",
        "2025-04-28", "kept"
    )
    ev2 = build_evidence_item(
        "P02", 2, "https://sfchronicle.com/health/crisis-center",
        "San Francisco's new psychiatric emergency center opens its doors",
        "2025-04-29", "kept"
    )

    res = synthesize_verdict("P02", "Open 24/7 Crisis Center at 822 Geary St", "2025-05-01", [ev1, ev2])
    assert res.verdict == "kept"
    assert res.confidence >= 0.90
    assert res.contradiction_count == 0
    assert len(res.evidence_chain) == 2


def test_broken_verdict():
    ev = build_evidence_item(
        "P06", 1, "https://data.sfgov.org/Transportation/fatalities",
        "San Francisco traffic fatalities in 2024 totaled 32 deaths, failing Vision Zero zero-death target",
        "2025-01-05", "broken"
    )

    res = synthesize_verdict("P06", "Zero traffic deaths by 2024", "2024-12-31", [ev], as_of=date(2025, 1, 15))
    assert res.verdict == "broken"
    assert res.confidence >= 0.85
    assert res.contradiction_count == 0


def test_contradiction_detection_and_resolution():
    ev_gov = build_evidence_item(
        "P16", 1, "https://sf.gov/news/shelter-progress",
        "City opens 1,000 shelter spaces",
        "2020-01-10", "kept"
    )
    ev_investigation = build_evidence_item(
        "P16", 2, "https://sfchronicle.com/news/shelter-audit",
        "Investigation reveals only 400 shelter beds are operational and staffed; 600 beds never opened",
        "2020-02-15", "broken"
    )

    res = synthesize_verdict("P16", "Open 1,000 shelter beds", "2020-01-01", [ev_gov, ev_investigation])
    assert res.contradiction_count == 2
    assert ev_gov.is_contradicted is True
    assert ev_investigation.is_contradicted is True
    # Per Playbook 3.1: Primary government source wins, but confidence is degraded to 0.75
    assert res.verdict == "kept"
    assert res.confidence == 0.75


@pytest.mark.anyio
async def test_parallel_verification_execution():
    candidates = [
        {
            "promise_id": "CAND-01",
            "promise_text": "Open Chase Center on time with 18,064 seats",
            "url": "https://sf.gov/news/chase-center-ribbon-cutting",
            "snippet": "Chase Center officially opens today with full 18,064 capacity.",
            "inferred_verdict": "kept"
        },
        {
            "promise_id": "CAND-02",
            "promise_text": "Improve neighborhood street ambiance",
            "url": "https://sf.gov/news/neighborhood",
            "snippet": "City pledges to support street beauty.",
            "inferred_verdict": "in_progress"
        },
        {
            "promise_id": "CAND-03",
            "promise_text": "Deliver 1,500 Visa employees at Mission Rock in 2024",
            "url": "https://sfchronicle.com/business/visa-downsizes",
            "snippet": "Visa downsizes Mission Rock footprint to fewer than 500 staff.",
            "inferred_verdict": "broken"
        }
    ]

    results = await run_parallel_verification(candidates, max_concurrency=2)
    assert len(results) == 3
    r_map = {r.promise_id: r for r in results}

    assert r_map["CAND-01"].verdict == "kept"
    assert r_map["CAND-02"].is_vague is True
    assert r_map["CAND-02"].verdict == "undecided"
    assert r_map["CAND-03"].verdict == "broken"
