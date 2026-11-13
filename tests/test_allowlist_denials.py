"""D1: per-domain denial histogram over recorded blocked-lead deny rows."""

from src.allowlist import load_allowlist
from src.denials import host_of, source_type_for_host, summarize_denials

# Deny rows in the shape discovery records for blocked leads
# ({"url", "reason"} — the phases[p]["blocked"] entries).
SYNTHETIC_DENY_ROWS = [
    {"url": "https://www.reddit.com/r/sanfrancisco/comments/abc/post", "reason": "unlisted source domain"},
    {"url": "https://old.reddit.com/r/BayArea/comments/def/other", "reason": "unlisted source domain"},
    {"url": "https://x.com/someone/status/123", "reason": "unlisted source domain"},
    {"url": "https://example.com/not-archived", "reason": "fetch returned 404"},
    {"url": "https://example.com/also-gone", "reason": "unlisted source domain"},
    {"url": "https://medium.com/@someone/a-post", "reason": "canary host blocked"},
]


def test_host_of_normalizes_case_port_and_scheme():
    assert host_of("https://WWW.Example.com:8443/a") == "www.example.com"
    assert host_of("http://reddit.com") == "reddit.com"
    assert host_of("not a url") == ""


def test_histogram_reconciles_with_recorded_deny_rows():
    summary = summarize_denials(SYNTHETIC_DENY_ROWS)

    assert summary["total_denials"] == len(SYNTHETIC_DENY_ROWS)
    # reddit (www + old are separate hosts), x.com, example.com, medium.com = 5
    assert summary["distinct_domains"] == 5
    assert summary["by_domain"]["www.reddit.com"]["count"] == 1
    assert summary["by_domain"]["old.reddit.com"]["count"] == 1
    assert summary["by_domain"]["x.com"]["count"] == 1
    assert summary["by_domain"]["example.com"]["count"] == 2
    assert summary["by_domain"]["medium.com"]["count"] == 1
    # every row is attributed exactly once
    assert sum(d["count"] for d in summary["by_domain"].values()) == summary["total_denials"]


def test_reason_breakdown_per_domain():
    summary = summarize_denials(SYNTHETIC_DENY_ROWS)
    assert summary["by_domain"]["example.com"]["reasons"] == {
        "fetch returned 404": 1,
        "unlisted source domain": 1,
    }


def test_source_types_come_from_the_reviewed_allowlist():
    summary = summarize_denials(SYNTHETIC_DENY_ROWS)
    # canaries attribute to their reviewed category
    assert summary["by_domain"]["www.reddit.com"]["source_types"] == {"canary_social": 1}
    assert summary["by_domain"]["medium.com"]["source_types"] == {"canary_social": 1}
    # hosts absent from the allowlist are honest about being unlisted
    assert summary["by_domain"]["example.com"]["source_types"] == {"unlisted": 2}


def test_source_type_for_host_follows_subdomain_rules():
    entries = load_allowlist()
    assert source_type_for_host("www.sfstandard.com", entries=entries) == "news"
    assert source_type_for_host("sfmta.com", entries=entries) == "official_government"
    assert source_type_for_host("random-sf-blog.example.com", entries=entries) == "unlisted"
    assert source_type_for_host("", entries=entries) == "unlisted"


def test_malformed_rows_are_skipped_not_crashed():
    summary = summarize_denials(
        [
            {"url": "https://reddit.com/x", "reason": "unlisted source domain"},
            {"reason": "no url"},
            {"url": None, "reason": "no url"},
            "not a mapping",
            {"url": "https://substack.com/@w", "reason": None},
        ]
    )
    assert summary["total_denials"] == 2
    assert summary["by_domain"]["substack.com"]["reasons"] == {"unknown": 1}


def test_empty_input_yields_empty_histogram():
    summary = summarize_denials([])
    assert summary == {"total_denials": 0, "distinct_domains": 0, "by_domain": {}}
