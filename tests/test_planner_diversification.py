"""D2: diversified discovery query tests.

Variant generation for the flagged districts (2, 4, 8, 11) in Spanish and
Chinese, community/ethnic-press targets present in the D1 allowlist, and
intact social/canary blocks. English query texts and English qualification
behavior are pinned byte-identical to the release base (7e9e090).
"""

from collections import Counter

from src.allowlist import canary_domains, entry_for_host, load_allowlist
from src.evidence import is_allowlisted_url
from src.sourcing.pipeline import REPO_ROOT, _load_existing_candidate_pools
from src.sourcing.planner import (
    DISTRICT_LANGUAGE_LOCALIZATION,
    FLAGGED_DISTRICT_LANGUAGES,
    SF_SUPERVISOR_DISTRICTS,
    TEN_CONTENT_PILLARS,
    SearchPlanner,
    flagged_districts,
    validate_outcome_blind_query,
)
from src.sourcing.qualification import QualificationIntakeAgent

NON_INSTITUTIONAL_TARGETS = {
    "elreporterosf.com",
    "eltecolote.org",
    "inglesidelight.com",
    "noevalleyvoice.com",
    "sfbayview.com",
    "singtaousa.com",
}

# Frozen at the release base (7e9e090): the English stratified batch must
# never change shape or text. target_domains intentionally excluded — D2
# appends the non-institutional source per pillar by design.
FROZEN_ENGLISH_QUERIES = (
    '"San Francisco" "Marina" ("will" OR "announced") "exhibition"',
    '"San Francisco" "Parkside" ("plans to" OR "announced") "concert"',
    '"San Francisco" "Castro" ("plans to" OR "announced") "season"',
    '"San Francisco" "Ingleside" ("committed to" OR "announced") "park renovation"',
    '"San Francisco" "Richmond" ("committed to" OR "announced") "restaurant opening"',
    '"San Francisco" "Chinatown" ("scheduled to" OR "announced") "farmers market"',
    '"San Francisco" "Haight-Ashbury" ("scheduled to" OR "announced") "climate target"',
    '"San Francisco" "Mission Bay" ("set to" OR "announced") "seawall"',
    '"San Francisco" "West Portal" ("set to" OR "announced") "Muni route"',
    '"San Francisco" "Bernal Heights" ("opening in" OR "announced") "bike lane"',
    '"San Francisco" "Bayview-Hunters Point" ("opening in" OR "announced") "housing units"',
    '"San Francisco" "Marina" ("launching in" OR "announced") "language access"',
    '"San Francisco" "Parkside" ("expects to" OR "announced") "youth program"',
    '"San Francisco" "Castro" ("expects to" OR "announced") "workforce training"',
    '"San Francisco" "Ingleside" ("will" OR "announced") "apprenticeship"',
    '"San Francisco" "Richmond" ("will" OR "announced") "parade"',
    '"San Francisco" "Chinatown" ("plans to" OR "announced") "heritage event"',
    '"San Francisco" "Haight-Ashbury" ("plans to" OR "announced") "city budget"',
)


def test_flagged_districts_are_the_gap_priority_set():
    assert flagged_districts() == [2, 4, 8, 11]
    for district in flagged_districts():
        assert SF_SUPERVISOR_DISTRICTS[district].get("gap_priority") is True
        # Every flagged district has localization data for both languages
        assert set(DISTRICT_LANGUAGE_LOCALIZATION[district].keys()) == set(FLAGGED_DISTRICT_LANGUAGES)


def test_variants_cover_every_flagged_district_and_pillar_in_both_languages():
    specs = SearchPlanner().generate_diversified_variants()
    by_key = {(s.pillar, s.supervisor_district, s.language) for s in specs}
    for pillar in TEN_CONTENT_PILLARS:
        for district in flagged_districts():
            for language in FLAGGED_DISTRICT_LANGUAGES:
                assert (pillar, district, language) in by_key
    assert len(specs) == len(by_key)  # no duplicate keys


def test_variants_carry_localized_district_labels_and_language_field():
    specs = SearchPlanner().generate_diversified_variants()
    for spec in specs:
        assert spec.language in FLAGGED_DISTRICT_LANGUAGES
        expected_label = DISTRICT_LANGUAGE_LOCALIZATION[spec.supervisor_district][spec.language]["district_label"]
        assert expected_label in spec.query_text
        assert spec.query_id.endswith(f"-{spec.language}")
        assert validate_outcome_blind_query(spec.query_text) == []


def test_spanish_and_chinese_variants_use_localized_verbs():
    specs = SearchPlanner().generate_diversified_variants()
    es_texts = [s.query_text for s in specs if s.language == "es"]
    zh_texts = [s.query_text for s in specs if s.language == "zh"]
    assert any("promete" in t or "anunciará" in t for t in es_texts)
    assert any("anunció" in t for t in es_texts)
    assert any("將" in t or "計劃" in t for t in zh_texts)
    assert any("舊金山" in t for t in zh_texts)
    # No Spanish/Chinese verb leaked into the English batch
    english = SearchPlanner().generate_stratified_queries(max_per_pillar=2)
    for spec in english:
        assert spec.language == "en"
        assert "promete" not in spec.query_text and "舊金山" not in spec.query_text


def test_every_new_query_target_is_allowlisted():
    entries = load_allowlist()
    for domain in NON_INSTITUTIONAL_TARGETS:
        entry = entry_for_host(domain, entries=entries)
        assert entry is not None, domain
        assert entry.review_status == "approved"
        assert entry.added_reason.strip()
        assert "checks_allowlist" in entry.groups


def test_every_pillar_has_at_least_one_non_institutional_source():
    for pillar, meta in TEN_CONTENT_PILLARS.items():
        sources = list(meta["sources"])  # type: ignore[arg-type]
        overlap = [d for d in sources if d in NON_INSTITUTIONAL_TARGETS]
        assert overlap, f"pillar {pillar!r} lacks a community/ethnic-press source"
        # Targets must not name hosts outside the allowlist that we added for D2
        assert all(is_allowlisted_url(f"https://{d}/") for d in overlap)


def test_social_hosts_stay_hard_blocked():
    canaries = canary_domains()
    for meta in TEN_CONTENT_PILLARS.values():
        for domain in meta["sources"]:  # type: ignore[union-attr]
            assert domain not in canaries
    for url, expected in [
        ("https://www.facebook.com/SFGovernment", False),
        ("https://x.com/SFGov", False),
        ("https://www.reddit.com/r/sanfrancisco", False),
        ("https://www.instagram.com/sfgov", False),
        # The new community-press targets must pass, not block
        ("https://eltecolote.org/content/en/", True),
        ("https://www.sfbayview.com/2026/09/example", True),
        ("https://www.singtaousa.com/sf/example", True),
    ]:
        assert is_allowlisted_url(url) is expected


def test_english_stratified_queries_byte_identical_to_release_base():
    specs = SearchPlanner().generate_stratified_queries(max_per_pillar=2)
    assert len(specs) == 18
    assert tuple(s.query_text for s in specs) == FROZEN_ENGLISH_QUERIES


def test_english_qualification_reproduces_the_frozen_register():
    """Re-evaluating the frozen intake pool must reproduce the committed
    register counts exactly (24 qualified / 38 needs_review / 1 rejected)."""
    pool = _load_existing_candidate_pools(REPO_ROOT)
    qualifier = QualificationIntakeAgent()
    statuses = Counter()
    for raw in pool:
        cid = str(raw.get("promise_id") or raw.get("candidate_id") or "")
        dual = False if raw.get("pending_hydration") else qualifier.should_dual_sample(cid, rate=0.20)
        result = qualifier.evaluate_candidate(
            raw,
            source_batch=raw.get("_source_batch", "manual"),
            discovery_channel=raw.get("_discovery_channel", "direct_seed"),
            dual_sample=dual,
        )
        statuses[result.qualification_status] += 1
    assert statuses == Counter({"needs_review": 38, "qualified": 24, "rejected": 1})


def test_spanish_forward_statement_qualifies():
    raw = {
        "candidate_id": "CAND-ES-01",
        "entity": "Alcaldesa de San Francisco",
        "promise_text": "La alcaldesa prometió construir 200 viviendas asequibles en el Distrito 11 para 2028.",
        "source_url": "https://eltecolote.org/content/en/2026/05/housing-pledge/",
        "source_tier": "TIER2_CONTEMPORANEOUS_NEWS",
        "promised_date": "2026-05-01",
        "supervisor_district": 11,
        "neighborhood": "Excelsior",
        "tags": ["housing"],
    }
    result = QualificationIntakeAgent().evaluate_candidate(
        raw, source_batch="d2_test", discovery_channel="diversified_planner_es"
    )
    assert result.qualification_status == "qualified"
    assert result.rejection_reason is None
    assert result.pillar == "Housing & Neighborhoods"


def test_chinese_forward_statement_qualifies():
    raw = {
        "candidate_id": "CAND-ZH-01",
        "entity": "舊金山市長",
        "promise_text": "市長宣布將在日落區興建新的圖書館分館，並承諾在2028年之前完工開幕，為華埠及日落區居民提供更多社區服務與閱讀空間。",
        "source_url": "https://www.singtaousa.com/sf/2026/06/library-branch/",
        "source_tier": "TIER2_CONTEMPORANEOUS_NEWS",
        "promised_date": "2026-06-01",
        "supervisor_district": 4,
        "neighborhood": "Outer Sunset",
    }
    result = QualificationIntakeAgent().evaluate_candidate(
        raw, source_batch="d2_test", discovery_channel="diversified_planner_zh"
    )
    assert result.qualification_status == "qualified"
    assert result.rejection_reason is None
    assert result.pillar in TEN_CONTENT_PILLARS


def test_statement_without_any_forward_action_still_rejects():
    # Neither English, Spanish, nor Chinese forward-action terms present
    raw = {
        "candidate_id": "CAND-ES-02",
        "entity": "La Junta de Supervisores",
        "promise_text": "La Junta debatió sobre la vivienda en el Distrito 11 durante la reunión de anoche.",
        "source_url": "https://elreporterosf.com/2026/05/debate/",
        "source_tier": "TIER2_CONTEMPORANEOUS_NEWS",
        "promised_date": "2026-05-20",
        "supervisor_district": 11,
        "neighborhood": "Excelsior",
    }
    result = QualificationIntakeAgent().evaluate_candidate(
        raw, source_batch="d2_test", discovery_channel="diversified_planner_es"
    )
    assert result.qualification_status == "rejected"
    assert result.rejection_reason == "vague_aspiration"
