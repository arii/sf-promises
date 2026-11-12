"""Preliminary source checks; passing is not authorization to publish."""

import json
from datetime import datetime, timezone
from urllib.parse import urlsplit

from src.checks import check_domain
from src.sources import is_verbatim_quote, load_archived_metadata, load_archived_text


_GOVERNMENT_ORG_HOSTS = frozenset({
    "sfgov.org", "sfbos.org", "sfmta.com", "sfplanning.org",
    "sfpuc.org", "sfenvironment.org", "cleanpowersf.org",
})

_PRIMARY_HOSTS = frozenset({
    "sfmta.com", "caltrain.com", "waymo.com", "zoox.com", "pge.com",
    "visa.com", "wholefoodsmarket.com", "nba.com", "wnba.com",
    "valkyries.com", "bayfc.com", "att.com", "comcast.com", "sfgiants.com",
    "mlb.com", "nfl.com", "prnewswire.com", "businesswire.com",
})
_NEWS_HOSTS = frozenset({
    "sfchronicle.com", "sfgate.com", "sfstandard.com", "missionlocal.org",
    "kqed.org", "sfexaminer.com", "bisnow.com", "socketsite.com",
    "therealdeal.com", "bizjournals.com", "techcrunch.com", "theverge.com",
    "arstechnica.com", "reuters.com", "apnews.com", "bloomberg.com",
    "cnbc.com", "nytimes.com", "latimes.com", "mercurynews.com",
    "eastbaytimes.com", "nbcbayarea.com", "abc7news.com", "ktvu.com",
    "cbsnews.com", "espn.com", "theathletic.com", "axios.com",
    "politico.com", "calmatters.org",
})
_CANARY_HOSTS = frozenset({
    "reddit.com", "x.com", "twitter.com", "facebook.com", "instagram.com",
    "tiktok.com", "yelp.com", "nextdoor.com", "wikipedia.org", "medium.com",
    "substack.com",
})


def _host_matches(host, domains):
    return any(host == domain or host.endswith("." + domain) for domain in domains)


def is_allowlisted_url(url):
    try:
        parsed = urlsplit(url)
        host = parsed.hostname
        return (
            parsed.scheme == "https"
            and host is not None
            and parsed.username is None
            and parsed.password is None
            and parsed.port in (None, 443)
            and not any(ord(char) <= 32 for char in url)
            and not _host_matches(host, _CANARY_HOSTS)
            and (host.endswith((".gov", ".mil", ".edu"))
                 or _host_matches(host, _PRIMARY_HOSTS | _NEWS_HOSTS)
                 or check_domain(url)[0])
        )
    except (TypeError, ValueError):
        return False


def _government_host(url):
    if not is_allowlisted_url(url):
        return False
    host = urlsplit(url).hostname
    return (host == "static1.squarespace.com"
            and urlsplit(url).path.startswith("/static/66df74757ae89b28c38bb175/")) or host.endswith(".gov") or any(
        host == domain or host.endswith("." + domain)
        for domain in _GOVERNMENT_ORG_HOSTS
    )


def _primary_host(url):
    if not is_allowlisted_url(url):
        return False
    host = urlsplit(url).hostname
    return (_government_host(url) or host.endswith((".mil", ".edu"))
            or _host_matches(host, _PRIMARY_HOSTS))


def screen_saved_source(*, root, promise_id, path, digest, quote, url, source_tier):
    """Return failed checks; source identity, tier, dates and facts need review."""
    failures = []
    if not is_allowlisted_url(url):
        failures.append("source_domain_unlisted")

    if source_tier == "TIER3_CANARY":
        failures.append("canary_not_evidence")
    elif source_tier not in ("TIER1_GOV", "TIER2_NEWS"):
        failures.append("source_tier_unknown")
    elif source_tier == "TIER1_GOV" and not _primary_host(url):
        failures.append("government_source_unverified")

    try:
        text = load_archived_text(root, promise_id, path, digest)
    except ValueError as exc:
        return failures + [str(exc)]
    if not is_verbatim_quote(quote, text):
        failures.append("quote_not_found")
    return failures


def record_preliminary_evidence(conn, *, root, promise_id, source, phase, source_tier, quote):
    """Record mechanical source checks, not independent verification of meaning."""
    if conn.in_transaction or not conn.execute("PRAGMA foreign_keys").fetchone()[0]:
        raise ValueError("A dedicated connection with foreign keys enabled is required")
    if phase not in ("ORIGIN", "DELIVERY", "SURVIVAL"):
        raise ValueError("Invalid evidence phase")
    failures = []
    metadata = None
    try:
        if not isinstance(source, dict):
            raise ValueError
        metadata = load_archived_metadata(
            root, promise_id, source.get("metadata_path"), source.get("metadata_sha256")
        )
        expected = {"path", "sha256", "url", "requested_url", "published_at", "fetched_at"}
        if (set(metadata) != expected or any(source.get(k) != metadata[k] for k in expected)
                or not is_allowlisted_url(metadata["requested_url"])
                or (metadata["published_at"] is not None
                    and not isinstance(metadata["published_at"], str))):
            raise ValueError
        if datetime.fromisoformat(metadata["fetched_at"]).utcoffset() is None:
            raise ValueError
    except (TypeError, ValueError):
        failures.append("source_metadata_invalid")
    if not isinstance(quote, str) or len(quote) > 32000:
        failures.append("quote_invalid")
    elif not failures:
        failures.extend(screen_saved_source(
            root=root, promise_id=promise_id, path=metadata["path"], digest=metadata["sha256"],
            quote=quote, url=metadata["url"], source_tier=source_tier,
        ))

    timestamp = datetime.now(timezone.utc).isoformat()
    conn.execute("BEGIN IMMEDIATE")
    try:
        if not conn.execute("SELECT 1 FROM candidates WHERE promise_id = ?", (promise_id,)).fetchone():
            raise ValueError("Candidate not found")
        if failures:
            conn.executemany(
                "INSERT INTO verifications (promise_id, check_type, passed, reason, checked_at) "
                "VALUES (?, ?, 0, ?, ?)",
                [(promise_id, reason, reason, timestamp) for reason in failures],
            )
            result = {"status": "rejected", "failures": failures}
        else:
            record = json.dumps({
                "metadata_path": source["metadata_path"],
                "metadata_sha256": source["metadata_sha256"],
                "semantics_verified": False,
            }, sort_keys=True)
            parameters = (
                promise_id, phase, source_tier, metadata["url"], metadata["published_at"],
                metadata["path"], metadata["sha256"], quote, record,
            )
            existing = conn.execute(
                "SELECT evidence_id, quote_verified, ingested_at, verification_record_json, "
                "source_tier, published_date, local_source_path FROM evidence_ledger "
                "WHERE promise_id = ? AND phase = ? AND url = ? AND content_sha256 = ? "
                "AND verbatim_quote = ?",
                (promise_id, phase, metadata["url"], metadata["sha256"], quote),
            ).fetchone()
            if existing is None:
                cursor = conn.execute(
                    "INSERT INTO evidence_ledger (promise_id, phase, source_tier, url, "
                    "published_date, local_source_path, content_sha256, verbatim_quote, "
                    "verification_record_json, quote_verified, ingested_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)", (*parameters, timestamp),
                )
                evidence_id = cursor.lastrowid
                conn.execute(
                    "INSERT INTO verifications (promise_id, evidence_id, check_type, passed, reason, checked_at) "
                    "VALUES (?, ?, 'preliminary_source', 1, 'source and quote match; meaning unverified', ?)",
                    (promise_id, evidence_id, timestamp),
                )
            else:
                evidence_id = existing[0]
                if (existing[1] != 1 or existing[4:7] != (
                        source_tier, metadata["published_at"], metadata["path"])
                        or not conn.execute(
                            "SELECT 1 FROM verifications WHERE promise_id = ? AND evidence_id = ? "
                            "AND check_type = 'preliminary_source' AND passed = 1",
                            (promise_id, evidence_id),
                        ).fetchone()):
                    raise ValueError("Existing evidence verification mismatch")
                try:
                    if datetime.fromisoformat(existing[2]).utcoffset() is None:
                        raise ValueError
                    saved_record = json.loads(existing[3])
                    if (set(saved_record) != {"metadata_path", "metadata_sha256", "semantics_verified"}
                            or saved_record["semantics_verified"] is not False):
                        raise ValueError
                    saved = load_archived_metadata(
                        root, promise_id, saved_record["metadata_path"], saved_record["metadata_sha256"]
                    )
                    if (set(saved) != expected
                            or any(saved[key] != metadata[key] for key in ("path", "sha256", "url", "published_at"))
                            or not is_allowlisted_url(saved["requested_url"])
                            or datetime.fromisoformat(saved["fetched_at"]).utcoffset() is None):
                        raise ValueError
                except (TypeError, ValueError, KeyError):
                    raise ValueError("Existing evidence provenance invalid") from None
            result = {"status": "recorded", "evidence_id": evidence_id, "failures": []}
        conn.execute("COMMIT")
    except BaseException:
        if conn.in_transaction:
            conn.execute("ROLLBACK")
        raise
    return result
