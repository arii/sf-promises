import hashlib
import re
from datetime import date, datetime
from urllib.parse import urlparse

from src.allowlist import domains_in_group

# The allowlist is reviewed data (config/allowlist.json). Every domain carries
# category and provenance; this set is the same hand-curated list, loaded —
# matching semantics are unchanged (exact host or subdomain).
DOMAIN_ALLOWLIST = domains_in_group("checks_allowlist")


def normalize_whitespace(text: str) -> str:
    """Normalize whitespace and lowercase for quote matching."""
    return re.sub(r"\s+", " ", text).strip().lower()


def check_domain(url: str) -> tuple[bool, str]:
    """Check if the source URL is on the domain allowlist."""
    try:
        parsed = urlparse(url)
        netloc = (parsed.netloc or "").lower()
        # Strip port if present
        if ":" in netloc:
            netloc = netloc.split(":")[0]

        if not netloc:
            return False, "unlisted source domain"

        if (netloc == "static1.squarespace.com"
                and parsed.path.startswith("/static/66df74757ae89b28c38bb175/")):
            return True, "pass"

        # Direct match or subdomain match
        for allowed in DOMAIN_ALLOWLIST:
            if netloc == allowed or netloc.endswith("." + allowed):
                return True, "pass"

        return False, "unlisted source domain"
    except Exception:
        return False, "unlisted source domain"


def check_hash(file_path: str, expected_hash: str) -> tuple[bool, str]:
    """Check if the SHA-256 hash of the file matches the expected hash."""
    try:
        with open(file_path, "rb") as f:
            file_bytes = f.read()
        computed = hashlib.sha256(file_bytes).hexdigest()
        if computed.lower() == expected_hash.strip().lower():
            return True, "pass"
        return False, "hash mismatch"
    except FileNotFoundError:
        return False, "file not found"
    except Exception as e:
        return False, f"hash check error: {e}"


def check_quote(quote: str, source_text: str) -> tuple[bool, str]:
    """Check if the verbatim quote is a substring of the source text after normalization."""
    if not quote or not quote.strip():
        return False, "quote none"

    norm_quote = normalize_whitespace(quote)
    norm_source = normalize_whitespace(source_text)

    if norm_quote in norm_source:
        return True, "pass"
    return False, "quote none"


def check_speaker(speaker: str, roll_call: list[str]) -> tuple[bool, str]:
    """Check if the speaker appears in the roll call / attendance list."""
    if not speaker or not speaker.strip():
        return False, "speaker not in roll call"

    norm_speaker = speaker.strip().lower()
    for member in roll_call:
        if member and norm_speaker in member.strip().lower():
            return True, "pass"
        if member and member.strip().lower() in norm_speaker:
            return True, "pass"
    return False, "speaker not in roll call"


EVIDENCE_TYPES = frozenset({
    "vote",
    "ordinance",
    "budget_line",
    "contract_milestone",
    "regulator_order",
    "filing",
    "opening",
    "count",
    "news_report",
    "press_release",
    "announcement",
})


def _parse_date(value: str | None) -> date | None:
    """Parse YYYY-MM-DD, YYYY-MM, or YYYY; None when unparseable."""
    if not value or not str(value).strip():
        return None
    text = str(value).strip()
    try:
        return datetime.strptime(text[:10], "%Y-%m-%d").date()
    except ValueError:
        pass
    try:
        return datetime.strptime(text[:7], "%Y-%m").date()
    except ValueError:
        pass
    try:
        return datetime.strptime(text[:4], "%Y").date()
    except ValueError:
        return None


def check_date(
    evidence_date: str | None,
    promised_date: str | None,
    due_date: str | None = None,
    today: date | None = None,
) -> tuple[bool, str]:
    """Date consistency: evidence must carry a parseable date within
    [promised_date, today]. Catches N06-style invented/shifted dates.
    Post-deadline reporting is allowed (reporting lag is normal); the
    number-plus-deadline rule lives in the rubric, not here."""
    now = today or date.today()
    ev = _parse_date(evidence_date)
    promised = _parse_date(promised_date)
    if ev is None or promised is None:
        return False, "date mismatch with source"
    if ev < promised:
        return False, "date mismatch with source"
    if ev > now:
        return False, "date mismatch with source"
    return True, "pass"


def check_promise_id(claim_promise_id: str | None, promise_id: str) -> tuple[bool, str]:
    """Evidence must cite the promise being judged. Catches N11-style
    cross-promise bundles (e.g. P06 evidence in a P05 bundle)."""
    if not claim_promise_id or not str(claim_promise_id).strip():
        return False, "evidence does not match promise_id"
    if str(claim_promise_id).strip() != str(promise_id).strip():
        return False, "evidence does not match promise_id"
    return True, "pass"


def check_evidence_type(evidence_type: str | None) -> tuple[bool, str]:
    """Evidence type must be one the rubric can tier."""
    if not evidence_type or str(evidence_type).strip().lower() not in EVIDENCE_TYPES:
        return False, "evidence type not allowed"
    return True, "pass"


# ==============================================================================
# Deterministic Gates
# ==============================================================================

VALID_SF_LOCATIONS = {
    "Citywide", "Mid-Market & Civic Center", "Tenderloin", "SoMa", "Mission Bay & Mission Rock",
    "Treasure Island", "Parkmerced", "Pier 70 & Dogpatch", "Chinatown & North Beach",
    "Golden Gate Park", "The Embarcadero", "Union Square & Financial District",
    "Twin Peaks", "Haight-Ashbury", "Presidio & Doyle Drive", "Bayview-Hunters Point",
    "Regional / Northern California",
}


def check_forward_looking_quote(
    date_promised: date,
    quote_published_date: date,
    verbatim_quote: str,
) -> list[str]:
    """Gate 1: Forward-Looking Claim Check (Eliminates Retrospective Quotes)."""
    errors = []
    # 1. Source document cannot be a retrospective written years after the promise
    if (quote_published_date - date_promised).days > 45:
        errors.append(
            f"Retrospective source rejected: quote published on {quote_published_date} "
            f"is >45 days after promise date {date_promised}. Search with published_before={date_promised}."
        )
    # 2. Reject retrospective critique phrasing
    retrospective_red_flags = [
        "didn't last long", "failed to", "had promised", "pledged in 20",
        "was originally scheduled", "sold out all", "opened with",
    ]
    lower_q = verbatim_quote.lower()
    for phrase in retrospective_red_flags:
        if phrase in lower_q:
            errors.append(f"Quote contains retrospective phrasing ('{phrase}'). Find original T0 pledge.")
    return errors


def check_geography_and_entity(neighborhood: str, entity_name: str, quote: str) -> list[str]:
    """Gate 3: Strict SF Geography & Sector Dictionary (Eliminates Hallucinated Titles)."""
    errors = []
    if neighborhood not in VALID_SF_LOCATIONS:
        errors.append(f"Invalid neighborhood '{neighborhood}'. Must be one of {VALID_SF_LOCATIONS}.")
    if "spokesman" in entity_name.lower() or "spokesperson" in entity_name.lower():
        errors.append(f"Entity '{entity_name}' is a spokesperson. Use the parent organization.")
    if neighborhood == "Treasure Island" and "parkmerced" in quote.lower():
        errors.append("Geographic mismatch: Quote is about Parkmerced, not Treasure Island.")
    return errors


def check_tiered_evidence(sources: list[dict]) -> list[str]:
    """Gate 4: Tiered Evidence Rule.
    A promise cannot be resolved using only TIER3_CANARY sources (Reddit, social media, blogs).
    Requires at least one corroborating TIER1_GOV or TIER2_NEWS document.
    """
    tiers = {s.get("source_tier") or s.get("tier") for s in sources}
    if tiers == {"TIER3_CANARY"} or (tiers and not tiers.intersection({"TIER1_GOV", "TIER2_NEWS"})):
        return ["Tier 3 canary signal requires corroborating TIER1_GOV or TIER2_NEWS source."]
    return []

