"""OD-20 H3: backfill sweep dedupe — every matching path drops the lead BEFORE audit.

Per the spec's verifying tests: dedupe unit tests per matching path (URL,
sha256, token overlap, ledger origin), and a file-hash assertion that
``data/intake_ledger.csv`` is untouched by the sweep path. Everything here
runs offline: the sweep takes a fake client, the index is built from tmp
fixtures or read-only repo data.
"""

import asyncio
import hashlib
import json
from datetime import date
from types import SimpleNamespace

import pytest

from src.sourcing.backfill import (
    MIN_SWEEP_MONTHS,
    build_sweep_queries,
    run_backfill_sweep,
    sweep_time_window,
)
from src.sourcing.dedupe import (
    DedupeIndex,
    build_dedupe_index,
    dedupe_verdict,
    filter_sweep_leads,
    normalize_tokens,
    normalize_url,
    quarantine_origins_from_db,
    token_overlap,
)

TODAY = date(2026, 11, 14)


def write_repo(tmp_path, *, master=None, register=None, denials=None, ledger=None):
    data = tmp_path / "data"
    data.mkdir(exist_ok=True)
    if master is not None:
        (data / "sf_promises_master.csv").write_text(master, encoding="utf-8")
    if register is not None:
        (data / "intake_candidate_register.json").write_text(
            json.dumps(register), encoding="utf-8"
        )
    if denials is not None:
        (data / "denied_leads.json").write_text(json.dumps(denials), encoding="utf-8")
    if ledger is not None:
        (data / "intake_ledger.csv").write_text(ledger, encoding="utf-8")
    return tmp_path


MASTER_CSV = (
    "promise_id,promise_text,entity,primary_source_url\n"
    'P001,"Will open 200 shelter beds by 2027","SF Department of Homelessness",https://sf.gov/shelter-press-release\n'
    'P002,"Plans to repave Mission Street in 2026","SFMTA",https://sfmta.com/mission-repave\n'
)

REGISTER_JSON = {
    "candidates": [
        {
            "candidate_id": "SEISMIC-01",
            "entity": "SF DBI",
            "statement_preview": "Mandatory seismic retrofits must complete across Tiers 1 through 4.",
            "source_url": "https://sfplanning.org/seismic-tiers",
        },
        {
            "promise_id": "P055",
            "entity": "SFPUC",
            "statement_preview": "CleanPowerSF will add 50 megawatts of local solar.",
            "source_url": "https://sfpuc.org/cleanpowersf-solar",
        },
    ]
}

DENIALS_JSON = [
    {"url": "https://salt-artandculture.com/event-calendar/red-flags", "reason": "domain_not_allowlisted"},
]

# A lead guaranteed novel against the fixtures above (nonce tokens, no overlap).
NOVEL_LEAD = {
    "url": "https://example.com/brand-new-pledge",
    "entity": "Zorbulon Commission",
    "promise_text": "Quibnostic mernelash borfnik xv zzq",
    "snippet": "Trellqwist pandorak vellum quorix",
}


@pytest.fixture
def index_repo(tmp_path):
    return write_repo(
        tmp_path, master=MASTER_CSV, register=REGISTER_JSON, denials=DENIALS_JSON
    )


@pytest.fixture
def index(index_repo):
    return build_dedupe_index(index_repo)


def assert_novel(lead, index):
    assert dedupe_verdict(lead, index) is None


# --- URL matching paths ------------------------------------------------


def test_url_corpus_match_dropped(index):
    match = dedupe_verdict({**NOVEL_LEAD, "url": "https://sf.gov/shelter-press-release"}, index)
    assert match is not None and match.reason == "url_corpus"


def test_url_register_match_dropped(index):
    match = dedupe_verdict({**NOVEL_LEAD, "url": "https://sfplanning.org/seismic-tiers"}, index)
    assert match is not None and match.reason == "url_register"


def test_url_denials_ledger_match_dropped(index):
    match = dedupe_verdict(
        {**NOVEL_LEAD, "url": "https://salt-artandculture.com/event-calendar/red-flags"}, index
    )
    assert match is not None and match.reason == "url_denial"


def test_url_quarantine_origin_match_dropped(index_repo):
    index = build_dedupe_index(
        index_repo, quarantine_urls=("https://sf.gov/quiet-pilot-p113",)
    )
    match = dedupe_verdict({**NOVEL_LEAD, "url": "https://sf.gov/quiet-pilot-p113"}, index)
    assert match is not None and match.reason == "url_quarantine"


def test_url_match_survives_trailing_slash_and_case(index):
    match = dedupe_verdict(
        {**NOVEL_LEAD, "url": "https://SF.Gov/shelter-press-release/"}, index
    )
    assert match is not None and match.reason == "url_corpus"


def test_normalize_url_canonical_form():
    assert normalize_url("HTTPS://SF.gov/Shelter/") == normalize_url("https://sf.gov/Shelter")


# --- sha256 byte-lock path ---------------------------------------------


def test_sha256_archived_match_dropped(tmp_path, index_repo):
    archive_root = tmp_path / "archive" / "P001"
    archive_root.mkdir(parents=True)
    digest = hashlib.sha256(b"archived page bytes").hexdigest()
    (archive_root / f"{digest}.md").write_bytes(b"archived page bytes")

    index = build_dedupe_index(index_repo, archive_root=tmp_path / "archive")
    match = dedupe_verdict(
        {**NOVEL_LEAD, "content_sha256": digest}, index
    )
    assert match is not None and match.reason == "sha256_archived"


def test_sha256_known_digest_supplied_by_caller(index_repo):
    digest = "a" * 64
    index = build_dedupe_index(index_repo, known_sha256=[digest])
    match = dedupe_verdict({**NOVEL_LEAD, "content_sha256": digest}, index)
    assert match is not None and match.reason == "sha256_archived"


def test_non_hex_digest_ignored(index):
    assert_novel({**NOVEL_LEAD, "content_sha256": "not-a-digest"}, index)


# --- token overlap paths ------------------------------------------------


def test_token_overlap_corpus_dropped(index):
    # Same entity + promise_text as corpus row P001, different URL.
    match = dedupe_verdict(
        {
            "url": "https://example.com/other-writeup",
            "entity": "SF Department of Homelessness",
            "promise_text": "Will open 200 shelter beds by 2027",
        },
        index,
    )
    assert match is not None and match.reason == "token_overlap_corpus"


def test_token_overlap_register_preview_dropped(index):
    match = dedupe_verdict(
        {
            "url": "https://example.com/another",
            "entity": "SF DBI",
            "promise_text": "Mandatory seismic retrofits must complete across Tiers 1 through 4.",
        },
        index,
    )
    assert match is not None and match.reason == "token_overlap_register"


def test_below_threshold_overlap_passes(index):
    # A few shared civic words but mostly different content: overlap < 0.8.
    assert_novel(
        {
            "url": "https://example.com/tangential",
            "entity": "SF Department of Public Works",
            "promise_text": "Will open 40 crossing guards at elementary schools",
        },
        index,
    )


def test_token_overlap_math():
    a = normalize_tokens("open two shelter beds")
    b = normalize_tokens("open two shelter beds now")
    # 4 shared tokens over a union of 5.
    assert token_overlap(a, b) == pytest.approx(4 / 5)
    assert token_overlap(a, frozenset()) == 0.0
    assert token_overlap(frozenset(), frozenset()) == 0.0


def test_chinese_token_overlap_uses_characters():
    a = normalize_tokens("將開設兩百個庇護床位")
    b = normalize_tokens("將開設兩百個庇護床位")
    assert a and token_overlap(a, b) == 1.0


# --- identity path ------------------------------------------------------


def test_already_registered_id_dropped(index):
    match = dedupe_verdict({**NOVEL_LEAD, "candidate_id": "SEISMIC-01"}, index)
    assert match is not None and match.reason == "already_registered_id"
    match = dedupe_verdict({**NOVEL_LEAD, "promise_id": "P055"}, index)
    assert match is not None and match.reason == "already_registered_id"


# --- filter + quarantine loader ----------------------------------------


def test_filter_sweep_leads_splits_kept_and_dropped(index):
    dup = {**NOVEL_LEAD, "url": "https://sf.gov/shelter-press-release"}
    kept, dropped = filter_sweep_leads([NOVEL_LEAD, dup], index)
    assert [k["url"] for k in kept] == [NOVEL_LEAD["url"]]
    assert len(dropped) == 1 and dropped[0]["reason"] == "url_corpus"


def test_quarantine_origins_from_db(tmp_path):
    import sqlite3

    conn = sqlite3.connect(tmp_path / "promises.db")
    conn.execute(
        "CREATE TABLE quarantined (quarantine_id INTEGER PRIMARY KEY, candidate_payload_json TEXT)"
    )
    conn.execute(
        "INSERT INTO quarantined (candidate_payload_json) VALUES (?)",
        (json.dumps({"origin": {"url": "https://sf.gov/pilot-p113"}, "notes": "see https://sfmta.com/p113"}),),
    )
    conn.commit()
    conn.close()

    origins = quarantine_origins_from_db(tmp_path / "promises.db")
    assert normalize_url("https://sf.gov/pilot-p113") in origins
    assert normalize_url("https://sfmta.com/p113") in origins


def test_index_reads_real_repo_data():
    """The index loads the actual reviewed files: 54-record corpus, register, denials."""
    from pathlib import Path

    repo_root = Path(__file__).resolve().parent.parent
    index = build_dedupe_index(repo_root)
    assert len(index.corpus_urls) >= 50
    assert len(index.known_ids) >= 50
    assert len(index.denial_urls) >= 30
    # A corpus URL is caught through the real file, not just the fixture.
    master_url = next(iter(index.corpus_urls))
    match = dedupe_verdict({**NOVEL_LEAD, "url": master_url}, index)
    assert match is not None and match.reason == "url_corpus"


# --- sweep window --------------------------------------------------------


def test_sweep_window_minimum_is_twelve_months():
    assert sweep_time_window(12, today=TODAY) == "2025-11-14..2026-11-14"
    assert sweep_time_window(18, today=TODAY) == "2025-05-14..2026-11-14"


def test_sweep_window_rejects_short_and_non_int():
    with pytest.raises(ValueError):
        sweep_time_window(6, today=TODAY)
    with pytest.raises(ValueError):
        sweep_time_window(11, today=TODAY)
    with pytest.raises(ValueError):
        sweep_time_window(True, today=TODAY)
    with pytest.raises(ValueError):
        sweep_time_window("12", today=TODAY)


def test_sweep_window_clamps_month_end():
    # March 31 minus one month is February 28 in a non-leap year.
    window = sweep_time_window(13, today=date(2026, 3, 31))
    assert window == "2025-02-28..2026-03-31"


def test_sweep_queries_carry_operator_window_not_rolling_config():
    queries = build_sweep_queries(time_window="2025-11-14..2026-11-14")
    # 18 stratified (10 pillars x up to 2, civic capped) + 80 diversified variants.
    assert len(queries) == 98
    assert {q.time_window for q in queries} == {"2025-11-14..2026-11-14"}


# --- offline sweep run ---------------------------------------------------


class FakeSearchResponse:
    def __init__(self, results):
        self.results = results


class FakeClient:
    """Offline stand-in for the Keenable client: records calls, returns canned rows."""

    def __init__(self, rows_by_query):
        self.rows_by_query = rows_by_query
        self.calls = []

    async def search(self, query, **kwargs):
        self.calls.append({"query": query, **kwargs})
        return FakeSearchResponse(self.rows_by_query.get(query, []))


def test_sweep_drops_duplicates_before_audit(tmp_path, index_repo):
    corpus_dup = {**NOVEL_LEAD, "url": "https://sf.gov/shelter-press-release"}
    denial_dup = {**NOVEL_LEAD, "url": "https://salt-artandculture.com/event-calendar/red-flags"}
    quarantine_dup = {**NOVEL_LEAD, "url": "https://sf.gov/pilot-p113"}
    novel = {**NOVEL_LEAD, "url": "https://example.com/fresh-scoop"}

    client = FakeClient({
        '"San Francisco" "Richmond" ("will" OR "announced") "exhibition"': [
            SimpleNamespace(url=corpus_dup["url"], title="t", snippet="s"),
            SimpleNamespace(url=denial_dup["url"], title="t", snippet="s"),
            SimpleNamespace(url=quarantine_dup["url"], title="t", snippet="s"),
            SimpleNamespace(url=novel["url"], title="t", snippet="s"),
            # Same URL twice in one sweep: counted, kept once.
            SimpleNamespace(url=novel["url"], title="t", snippet="s"),
        ],
    })

    result = asyncio.run(
        run_backfill_sweep(
            client,
            months=12,
            repo_root=index_repo,
            quarantine_urls=("https://sf.gov/pilot-p113",),
            today=TODAY,
            # One query only keeps this offline and focused.
            planner=_SingleQueryPlanner(),
        )
    )

    assert result["mode"] == "backfill_sweep"
    assert result["window"] == "2025-11-14..2026-11-14"
    assert result["query_count"] == 1
    assert client.calls[0]["published_after"] == "2025-11-14"
    assert client.calls[0]["published_before"] == "2026-11-14"
    assert client.calls[0]["max_results"] == 25
    assert result["in_sweep_duplicate_urls"] == 1
    assert result["dropped_reasons"] == {
        "url_corpus": 1,
        "url_denial": 1,
        "url_quarantine": 1,
    }
    kept_urls = [lead["url"] for lead in result["leads_for_audit"]]
    assert kept_urls == [novel["url"]]
    assert result["deduped_leads_for_audit"] == 1
    assert result["dropped_before_audit"] == 3


def test_sweep_never_writes_the_frozen_ledger(index_repo):
    ledger_path = index_repo / "data" / "intake_ledger.csv"
    ledger_path.write_text("candidate_id\nFROZEN-001\n", encoding="utf-8")
    before = hashlib.sha256(ledger_path.read_bytes()).hexdigest()

    client = FakeClient({
        '"San Francisco" "Richmond" ("will" OR "announced") "exhibition"': [
            SimpleNamespace(url=NOVEL_LEAD["url"], title="t", snippet="s"),
        ],
    })
    asyncio.run(
        run_backfill_sweep(
            client,
            months=12,
            repo_root=index_repo,
            today=TODAY,
            planner=_SingleQueryPlanner(),
        )
    )

    after = hashlib.sha256(ledger_path.read_bytes()).hexdigest()
    assert before == after


def test_real_frozen_ledger_untouched_by_sweep():
    """File-hash guard against the actual repo: a sweep run leaves it byte-identical."""
    from pathlib import Path

    repo_root = Path(__file__).resolve().parent.parent
    ledger_path = repo_root / "data" / "intake_ledger.csv"
    before = hashlib.sha256(ledger_path.read_bytes()).hexdigest()

    client = FakeClient({
        '"San Francisco" "Richmond" ("will" OR "announced") "exhibition"': [
            SimpleNamespace(url="https://example.com/one-off-lead", title="t", snippet="s"),
        ],
    })
    asyncio.run(
        run_backfill_sweep(
            client,
            months=12,
            repo_root=repo_root,
            today=TODAY,
            planner=_SingleQueryPlanner(),
        )
    )

    assert hashlib.sha256(ledger_path.read_bytes()).hexdigest() == before


class _SingleQueryPlanner:
    """Planner stand-in emitting one fixed query — keeps sweep tests offline and tiny."""

    def generate_stratified_queries(self, pillars=None, districts=None, time_window=None, max_per_pillar=2):
        return [
            SimpleNamespace(
                query_id="Q-01-D01-1",
                pillar="Arts, Music & Nightlife",
                supervisor_district=1,
                neighborhood="Richmond",
                time_window=time_window,
                entity_type="cultural_or_business_entity",
                query_text='"San Francisco" "Richmond" ("will" OR "announced") "exhibition"',
                target_domains=[],
                language="en",
            )
        ]

    def generate_diversified_variants(self, pillars=None, districts=None, time_window=None):
        return []


def test_min_sweep_months_constant():
    assert MIN_SWEEP_MONTHS == 12
