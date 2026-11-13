"""D1: allowlist-as-data representation tests.

The config file must carry the same domains, categories, provenance, and
canary flags the code used to hardcode, and the consumers must behave
identically to the pre-migration behavior.
"""

import pytest

from src.allowlist import (
    DEFAULT_ALLOWLIST_PATH,
    canary_domains,
    domains_in_group,
    entry_for_host,
    load_allowlist,
)
from src.checks import DOMAIN_ALLOWLIST, check_domain
from src.evidence import (
    _CANARY_HOSTS,
    _GOVERNMENT_ORG_HOSTS,
    _NEWS_HOSTS,
    _PRIMARY_HOSTS,
    is_allowlisted_url,
)

# Group sizes pinned at migration; any change to the allowlist must be a
# reviewed config edit, so these counts act as tripwires.
# D2 deliberately grew checks_allowlist 34→40 and news 31→37 by adding six
# community/ethnic-press query targets (elreporterosf.com, eltecolote.org,
# inglesidelight.com, noevalleyvoice.com, sfbayview.com, singtaousa.com).
EXPECTED_GROUP_SIZES = {
    "checks_allowlist": 40,
    "government": 7,
    "primary": 24,
    "news": 37,
}
EXPECTED_CANARY_COUNT = 11


def test_config_exists_with_valid_schema():
    entries = load_allowlist()
    assert len(entries) >= 1
    for entry in entries:
        assert entry.domain == entry.domain.strip().lower()
        assert entry.source_type
        assert entry.added_reason
        assert entry.added_by
        assert entry.added_at
        assert entry.review_status in {"approved", "pending", "denied"}
        assert isinstance(entry.canary, bool)


def test_no_duplicate_domains():
    entries = load_allowlist()
    domains = [entry.domain for entry in entries]
    assert len(domains) == len(set(domains))


def test_groups_match_the_migrated_sets():
    assert len(domains_in_group("checks_allowlist")) == EXPECTED_GROUP_SIZES["checks_allowlist"]
    assert len(domains_in_group("government")) == EXPECTED_GROUP_SIZES["government"]
    assert len(domains_in_group("primary")) == EXPECTED_GROUP_SIZES["primary"]
    assert len(domains_in_group("news")) == EXPECTED_GROUP_SIZES["news"]
    assert len(canary_domains()) == EXPECTED_CANARY_COUNT


def test_representative_domains_carry_provenance():
    entries = {entry.domain: entry for entry in load_allowlist()}
    assert entries["sf.gov"].groups == ("checks_allowlist",)
    assert entries["sfenvironment.org"].source_type == "official_government"
    assert entries["sfenvironment.org"].added_reason.startswith("Parent decision")
    assert entries["sfmta.com"].groups == ("checks_allowlist", "government", "primary")
    assert entries["sfgate.com"].source_type == "news"
    assert entries["wikipedia.org"].source_type == "canary_social"
    assert entries["wikipedia.org"].canary is True


def test_loader_rejects_missing_required_field(tmp_path):
    path = tmp_path / "allowlist.json"
    path.write_text(
        '[{"domain": "example.com", "source_type": "news", "added_by": "x",'
        ' "added_at": "2026-01-01", "review_status": "approved", "canary": false}]',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="added_reason"):
        load_allowlist(str(path))


def test_loader_rejects_duplicate_domains(tmp_path):
    path = tmp_path / "allowlist.json"
    entry = (
        '{"domain": "example.com", "source_type": "news", "added_reason": "r",'
        ' "added_by": "x", "added_at": "2026-01-01", "review_status": "approved",'
        ' "canary": false}'
    )
    path.write_text(f"[{entry}, {entry}]", encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate"):
        load_allowlist(str(path))


def test_loader_rejects_missing_file():
    with pytest.raises(ValueError, match="not found"):
        load_allowlist("/nonexistent/allowlist.json")


def test_consumers_are_backed_by_the_config_file():
    assert DOMAIN_ALLOWLIST == domains_in_group("checks_allowlist")
    assert _GOVERNMENT_ORG_HOSTS == domains_in_group("government")
    assert _PRIMARY_HOSTS == domains_in_group("primary")
    assert _NEWS_HOSTS == domains_in_group("news")
    assert _CANARY_HOSTS == canary_domains()
    assert DEFAULT_ALLOWLIST_PATH.name == "allowlist.json"


@pytest.mark.parametrize(
    "url,expected",
    [
        # allowlisted: gov, subdomain, exact-host-only, https, port 443
        ("https://sf.gov/news", True),
        ("https://www.sf.gov/news", True),
        ("https://sfbos.org/", True),
        ("https://www.sfpuc.org/projects", True),
        ("https://edition.pagesuite.com/tribune/article_popover.aspx?guid=x", True),
        ("https://sf.gov:443/news", True),
        # exact hosts only: parents of seeded hosts must still fail
        ("https://www.pagesuite.com/x", False),
        ("https://www.wikipedia.org/wiki/x", False),
        ("https://www.senate.ca.gov/x", False),
        ("https://www.pgecorp.com/x", False),
        # unlisted hosts fail
        ("https://example.com/news", False),
        ("https://random-sf-blog.example.com/post", False),
        # canaries stay hard-blocked
        ("https://www.reddit.com/r/sanfrancisco", False),
        ("https://x.com/someone/status/1", False),
        # pre-migration quirk preserved: check_domain sees the exact seeded host,
        # while is_allowlisted_url blocks it as a canary subdomain (probe below)
        ("https://en.wikipedia.org/wiki/x", True),
    ],
)
def test_check_domain_probe_set(url, expected):
    passed, _ = check_domain(url)
    assert passed is expected


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://sf.gov/news", True),
        ("https://www.sfstandard.com/articles/x", True),
        ("http://sf.gov/news", False),  # https-only
        ("https://sf.gov:8080/news", False),
        ("https://user:pass@sf.gov/news", False),
        ("https://www.reddit.com/r/sanfrancisco", False),
        ("https://en.wikipedia.org/wiki/x", False),  # canary subdomain
        ("not a url", False),
    ],
)
def test_is_allowlisted_url_probe_set(url, expected):
    assert is_allowlisted_url(url) is expected


def test_entry_for_host_prefers_the_closest_listed_ancestor():
    entries = load_allowlist()
    assert entry_for_host("www.sf.gov", entries=entries).domain == "sf.gov"
    assert entry_for_host("en.wikipedia.org", entries=entries).domain == "en.wikipedia.org"
    assert entry_for_host("random-sf-blog.example.com", entries=entries) is None
    assert entry_for_host("", entries=entries) is None


def test_pending_entries_do_not_match():
    entry = entry_for_host("sf.gov")
    assert entry is not None and entry.review_status == "approved"
    suspended = (
        type(entry)(
            domain="sf.gov",
            source_type=entry.source_type,
            added_reason=entry.added_reason,
            added_by=entry.added_by,
            added_at=entry.added_at,
            review_status="pending",
            canary=entry.canary,
            groups=entry.groups,
        ),
    )
    assert entry_for_host("sf.gov", entries=suspended) is None
