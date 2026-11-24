"""Add v2-published promises to a staged site export.

Read-only on every v2 database and source tree. Nothing here writes a file;
the caller owns the staging directory. A v2 record reaches the site only after
its cited source bytes are re-hashed and every quote is re-found in the saved
text at merge time, so a stale or edited source can never be published.
"""

from collections import Counter
from contextlib import closing
from datetime import date, datetime, timezone
import json
from pathlib import Path
import re
import sqlite3

from src.database import APPLICATION_ID, SCHEMA_VERSION
from src.evidence import screen_saved_source
from src.outcome_rules import (
    NOT_CHECKED_NOTE, recorded_origin_date_failures, recorded_outcome_rules,
)
from src.relevance import evaluate_relevance
from src.sources import is_verbatim_quote
from src.taxonomy import screen_taxonomy
from src.temporal import check_origin_dates, screen_forward_looking

# Evidence phases (beyond ORIGIN) a verdict needs: a delivery sentence for the kept
# family, a delivery plus a survival sentence for a reversal, and the contrary
# (not delivered) delivery sentence for broken. IN_PROGRESS and UNDECIDED need none.
REQUIRED_PHASES = {
    "KEPT": ("DELIVERY",), "DELAYED_OR_PARTIAL": ("DELIVERY",),
    "KEPT_THEN_REVERSED": ("DELIVERY", "SURVIVAL"), "BROKEN": ("DELIVERY",),
}
VERIFIER_FIELDS = ("action", "promise_date", "entity_and_location")

VERDICT_MAP = {
    "KEPT": "kept",
    "IN_PROGRESS": "in_progress",
    "BROKEN": "broken",
    "UNDECIDED": "undecided",
    "STALLED": "stalled",
    "KEPT_THEN_REVERSED": "kept_then_reversed",
    "DELAYED_OR_PARTIAL": "delayed_or_partial",
}

ENTITY_CATEGORY = {
    "Mayor / Executive": "politician",
    "Board of Supervisors": "politician",
    "City Agency": "city_department",
    "State Regulator": "city_department",
    "Private Corporation": "corporation",
    "Developer": "corporation",
    "Sports Franchise": "sports_team",
}

# Site pillars (docs/app.js pillarNames) for each v2 sector.
SECTOR_PILLAR = {
    "Housing & Land Use": "Housing & Neighborhoods",
    "Transit & Streets": "Transit & Movement",
    "Homelessness & Behavioral Health": "Civic Life",
    "Public Safety & Justice": "Civic Life",
    "Energy & Infrastructure": "Weather & Environment",
    "Environment & Energy": "Weather & Environment",
    "Autonomous Vehicles": "Transit & Movement",
    "Parks & Recreation": "Sports & Recreation",
    "Sports, Culture & Retail": "Culture & Social Life",
    "Governance & Finance": "Civic Life",
    "Education & Youth": "Civic Life",
}

# The site's category buckets (docs/export_data.py SF_CATEGORY_MAP). A v2 sector
# that the legacy export already renders under another name is folded into that
# bucket; sectors without a legacy equivalent keep their own name.
SECTOR_CATEGORY = {
    "Energy & Infrastructure": "Environment & Energy",
    "Governance & Finance": "Civic Governance",
    "Homelessness & Behavioral Health": "Civic Governance",
    "Housing & Land Use": "Housing & Neighborhoods",
    "Education & Youth": "Civic Governance",
}

TIER_SOURCE_TYPE = {"TIER1_GOV": "official_record", "TIER2_NEWS": "news_report"}


class V2DatabaseError(ValueError):
    """The database as a whole cannot be trusted; nothing is merged from it."""


def _rows(conn, query, parameters=()):
    cursor = conn.execute(query, parameters)
    names = [column[0] for column in cursor.description]
    return [dict(zip(names, row)) for row in cursor.fetchall()]


def _timestamp(value):
    parsed = datetime.fromisoformat(value)
    if parsed.utcoffset() is None:
        raise ValueError("naive timestamp")
    return parsed.astimezone(timezone.utc)


def _date(value):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        try:
            return datetime.fromisoformat(value).date()
        except (TypeError, ValueError):
            return None


def open_v2_database(path):
    """Open read-only and validate identity and integrity, or raise."""
    try:
        resolved = Path(path).resolve(strict=True)
    except OSError as exc:
        raise V2DatabaseError(f"v2 database not found: {path}") from exc
    conn = sqlite3.connect(resolved.as_uri() + "?mode=ro", uri=True)
    try:
        conn.execute("PRAGMA query_only = ON")
        if conn.execute("PRAGMA application_id").fetchone()[0] != APPLICATION_ID:
            raise V2DatabaseError("Unsupported v2 database application ID")
        if conn.execute("PRAGMA user_version").fetchone()[0] != SCHEMA_VERSION:
            raise V2DatabaseError("Unsupported v2 database schema version")
        if conn.execute("PRAGMA quick_check").fetchall() != [("ok",)]:
            raise V2DatabaseError("v2 database quick_check failed")
        if conn.execute("PRAGMA foreign_key_check").fetchone():
            raise V2DatabaseError("v2 database foreign key check failed")
    except sqlite3.Error as exc:
        conn.close()
        raise V2DatabaseError(f"v2 database unreadable: {exc}") from exc
    except BaseException:
        conn.close()
        raise
    return conn


def validate_v2_database(path):
    with closing(open_v2_database(path)):
        pass


def _load_promise(conn, promise, source_root, today):
    """Return (loaded, None) or (None, rejection reason). Never raises on bad data."""
    pid = promise["promise_id"]
    if screen_taxonomy(
        entity_name=promise["entity_name"], entity_type=promise["entity_type"],
        sector=promise["sector"], neighborhood=promise["neighborhood"],
        quote=promise["promise_text"],
    ):
        return None, "taxonomy_unverified"

    verdicts = _rows(conn, "SELECT * FROM verdicts WHERE promise_id = ?", (pid,))
    if not verdicts:
        return None, "no_verdict"
    try:
        ordered = sorted(verdicts, key=lambda v: (_timestamp(v["decided_at"]), v["verdict_id"]))
    except ValueError:
        return None, "verdict_timestamp_invalid"
    latest = ordered[-1]
    if latest["verdict"] not in VERDICT_MAP:
        return None, "verdict_unmapped"

    assessments = _rows(
        conn, "SELECT rowid AS seq, * FROM relevance_assessments WHERE promise_id = ?", (pid,))
    try:
        assessment = max(assessments, key=lambda a: (_timestamp(a["evaluated_at"]), a["seq"]))
        inputs = json.loads(assessment["input_json"])
        relevance = evaluate_relevance(inputs["promise_text"], inputs["signals"])
        if (inputs["promise_text"] != promise["promise_text"] or not relevance["publish"]
                or assessment["passed"] != 1
                or any(assessment[k] != relevance[k] for k in
                       ("real_promise", "measurable", "sf_relevant", "interesting", "total"))):
            raise ValueError
    except (ValueError, KeyError, TypeError):
        return None, "relevance_invalid"

    promised = _date(promise["date_promised"])
    deadline = _date(promise["date_deadline"])
    if promise["date_deadline"] is not None and deadline is None:
        return None, "promise_date_invalid"
    if promised is None or promised > today:
        return None, "promise_date_invalid"

    verifications = _rows(
        conn, "SELECT * FROM verifications WHERE promise_id = ? ORDER BY verification_id", (pid,))
    try:
        recorded = recorded_outcome_rules(
            [v for v in verifications if v["check_type"] == "outcome_basis"])
        outcome_basis = next((json.loads(v["reason"]) for v in reversed(verifications)
                              if v["check_type"] == "outcome_basis"), None)
    except (ValueError, KeyError, TypeError):
        return None, "outcome_basis_invalid"

    evidence = _rows(
        conn, "SELECT * FROM evidence_ledger WHERE promise_id = ? ORDER BY evidence_id", (pid,))
    if not evidence:
        return None, "no_evidence"
    rebased = []
    for item in evidence:
        digest = item["content_sha256"]
        # Never trust the stored directory (it may be a historical absolute
        # path): the file must be <sources>/<promise_id>/<sha256>.<ext>.
        path = Path(source_root) / pid / Path(item["local_source_path"]).name
        failures = screen_saved_source(
            root=source_root, promise_id=pid, path=str(path), digest=digest,
            quote=item["verbatim_quote"], url=item["url"], source_tier=item["source_tier"],
        )
        if item["quote_verified"] != 1:
            failures = failures + ["quote_not_verified_in_database"]
        if failures:
            return None, "evidence_unverified:" + ",".join(failures)
        published = _date(item["published_date"])
        if published is None or published > today:
            return None, "evidence_date_invalid"
        rebased.append({**item, "_file": path.name, "_published": published,
                        "_saved_path": str(path)})

    origin = next((
        item for item in rebased
        if item["phase"] == "ORIGIN"
        and is_verbatim_quote(promise["promise_text"], item["verbatim_quote"])
        and not screen_forward_looking(promise["promise_text"])
        and not recorded_origin_date_failures(
            check_origin_dates(promised, item["_published"], deadline), promised, deadline,
            quote=promise["promise_text"], published=item["_published"], recorded=recorded)
    ), None)
    if origin is None:
        return None, "origin_evidence_missing"

    basis = None
    basis_rows = _rows(
        conn, "SELECT * FROM verifications WHERE promise_id = ? "
        "AND check_type = 'promise_date_basis' ORDER BY verification_id", (pid,))
    if basis_rows:
        try:
            detail = json.loads(basis_rows[-1]["reason"])
            basis = {"basis": str(detail["basis"]), "note": str(detail["note"])}
        except (ValueError, KeyError, TypeError):
            return None, "promise_date_basis_invalid"

    problem = _verdict_support_problem(latest["verdict"], rebased, verifications, promised, deadline)
    if problem:
        return None, problem
    return {
        "promise": promise, "verdicts": ordered, "latest": latest, "relevance": relevance,
        "evidence": rebased, "origin": origin, "basis": basis,
        "verifications": verifications, "promised": promised, "deadline": deadline,
        "outcome_basis": outcome_basis,
    }, None


def _verdict_support_problem(verdict, evidence, verifications, promised, deadline):
    """Return a rejection reason unless the evidence and verifier rows support the verdict."""
    phases = {e["phase"] for e in evidence
              if e["phase"] != "ORIGIN" and e["_published"] > promised}
    for phase in REQUIRED_PHASES.get(verdict, ()):
        if phase not in phases:
            return ("verdict_unsupported:no_contrary_evidence" if verdict == "BROKEN"
                    else f"verdict_unsupported:no_{phase.lower()}_evidence")
    verifier = next((v for v in reversed(verifications)
                     if v["check_type"] == "independent_verifier"), None)
    if verifier is None or verifier["passed"] != 1:
        return "verdict_unsupported:no_passed_independent_verifier"
    try:
        review = json.loads(verifier["reason"])
    except (TypeError, ValueError):
        return "verdict_unsupported:verifier_unreadable"
    needed = list(VERIFIER_FIELDS)
    if deadline is not None:
        needed.append("deadline")
    needed += [phase.lower() for phase in REQUIRED_PHASES.get(verdict, ())]
    if not isinstance(review, dict) or any(review.get(name) is not True for name in needed):
        return "verdict_unsupported:verifier_did_not_confirm"
    return None


def load_v2_promises(db_path, source_root, *, today=None):
    """Return (loaded promises, rejections) for one v2 database."""
    today = today or datetime.now(timezone.utc).date()
    loaded, rejected = [], []
    with closing(open_v2_database(db_path)) as conn:
        conn.execute("BEGIN")
        try:
            promises = _rows(conn, "SELECT * FROM promises ORDER BY date_promised DESC, promise_id")
            for promise in promises:
                item, reason = _load_promise(conn, promise, Path(source_root), today)
                if item is None:
                    rejected.append({"promise_id": promise["promise_id"], "reason": reason})
                else:
                    loaded.append(item)
        finally:
            conn.execute("ROLLBACK")
    return loaded, rejected


def _text_key(text):
    text = str(text or "").translate(str.maketrans({
        "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"'}))
    return " ".join(re.sub(r"[^0-9a-z]+", " ", text.casefold()).split())


def _url_key(url):
    match = re.match(r"(?i)^https?://(?:www\.)?([^/?#]+)([^?#]*)(\?[^#]*)?", str(url or "").strip())
    if not match:
        return str(url or "").strip().casefold()
    return (match[1].casefold() + match[2].rstrip("/") + (match[3] or "")).casefold()


def _quotes_overlap(a, b):
    a, b = _text_key(a), _text_key(b)
    short, long_ = sorted((a, b), key=len)
    return len(short) >= 20 and short in long_


def _existing_index(records):
    by_url, texts = {}, set()
    for record in records:
        quotes = [record.get("promise_text"), record.get("verbatim_quote")]
        urls = [record.get("source_url")]
        for bundle in (record.get("advocate_bundles") or {}).values():
            for claim in (bundle or {}).get("claims") or []:
                quotes.append(claim.get("quote"))
                urls.append(claim.get("source_url"))
        for url in urls:
            if url:
                by_url.setdefault(_url_key(url), []).append((record["promise_id"], quotes))
        if record.get("promise_text"):
            texts.add(_text_key(record["promise_text"]))
    return by_url, texts


def _find_duplicate(item, by_url, texts):
    if _text_key(item["promise"]["promise_text"]) in texts:
        return "same_promise_text"
    for evidence in item["evidence"]:
        for other_id, quotes in by_url.get(_url_key(evidence["url"]), []):
            if any(_quotes_overlap(evidence["verbatim_quote"], quote) for quote in quotes if quote):
                return f"same_source_overlapping_quote:{other_id}"
    return None


def _format_date(value):
    from scripts.enrich_dataset import _format_human_date
    return _format_human_date(value, "day")


def _source_tier_label(url):
    url = (url or "").lower()
    if any(h in url for h in ["sf.gov", "flysfo.com", "sfgov.org", "sfmta.com",
                              "legistar.com", "granicus.com", "sfpublicworks"]):
        return "Official"
    if "wikipedia.org" in url:
        return "Reference"
    return "News"


def _reason_text(reason, verdict):
    reason = (reason or "").strip()
    if not reason:
        return "Not recorded."
    return reason[0].upper() + reason[1:]


def _outcome_basis_field(detail, open_ended):
    """Site-facing outcome basis, or None for a record the flag-off audit published."""
    if not isinstance(detail, dict):
        return None
    reason = detail.get("reason")
    return {
        "rules": list(detail.get("rules") or []),
        "outcome_rule": detail.get("outcome_rule"),
        "open_ended": bool(detail.get("open_ended", open_ended)),
        "reason": reason,
        "relied_on": list(detail.get("relied_on") or []),
        "status_not_checked": reason == NOT_CHECKED_NOTE,
    }


_RULE_EXPLANATIONS = {
    "BROKEN": ("The deadline passed and a source published on or after the deadline "
               "reports the commitment was not delivered."),
    "KEPT_THEN_REVERSED": ("A source shows the commitment was delivered, and a later "
                           "source shows it was closed, halted or revoked."),
}


def _evidence_summaries(item, contradictory):
    """Inspectable summaries for a record whose outcome evidence contradicts the
    promise (the site requires them on every has_contradictory_evidence record).
    Quotes come from the verified evidence rows; nothing is paraphrased."""
    if not contradictory:
        return {}
    verdict = item["latest"]["verdict"]
    outcome = [e for e in item["evidence"] if e["phase"] in ("DELIVERY", "SURVIVAL")]
    supporting = " ".join(" ".join(e["verbatim_quote"].split()) for e in outcome)
    origin = " ".join(item["origin"]["verbatim_quote"].split())
    reason = (item.get("outcome_basis") or {}).get("reason") if isinstance(
        item.get("outcome_basis"), dict) else None
    explanation = _RULE_EXPLANATIONS.get(verdict, "")
    if reason:
        explanation = f"{explanation} {reason}".strip()
    return {
        "supporting_evidence_summary": supporting or None,
        "contradicting_evidence_summary": f"The original commitment: {origin}",
        "arbitration_rule_explanation": explanation or None,
    }


_ABBREVIATIONS = frozenset({
    "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "sept", "oct", "nov", "dec",
    "st", "ave", "blvd", "dr", "mr", "mrs", "ms", "no", "inc", "co", "corp", "jr", "sr",
    "u.s", "e.g", "i.e", "vs", "approx",
})
_SENTENCE_CAP = 420


def _is_sentence_end(text, i):
    """True when text[i] ends a sentence: .!? followed by whitespace or end,
    and not an abbreviation or a single initial."""
    if text[i] not in ".!?":
        return False
    if i + 1 < len(text) and not text[i + 1].isspace():
        return False
    if text[i] == ".":
        j = i
        while j > 0 and (text[j - 1].isalpha() or text[j - 1] == "."):
            j -= 1
        word = text[j:i].lower()
        if word in _ABBREVIATIONS or len(word) == 1:
            return False
    return True


def _is_line_break_boundary(text, i):
    """A single newline at i starts a new unit (heading or list line ending,
    next line capitalized) rather than wrapping a sentence."""
    if text[i] != "\n":
        return False
    nxt = text[i + 1:i + 2]
    prev = text[:i].rstrip(" \t")[-1:]
    return bool(nxt) and nxt.isupper() and prev not in (",", ";", ":", "-", "")


def display_sentence(text, quote):
    """The complete sentence(s) of saved ``text`` that contain ``quote``,
    whitespace-collapsed, for display. Returns None if the quote is not found
    or the sentence would exceed the cap. The evidence quote is unchanged;
    this only widens the displayed text to sentence boundaries in the same
    saved bytes (PDF line wrapping often cuts a segment mid-sentence)."""
    start = text.find(quote)
    if start < 0:
        return None
    end = start + len(quote)
    left = start
    while left > 0:
        if text[left - 2:left] == "\n\n" or _is_sentence_end(text, left - 1) \
                or _is_line_break_boundary(text, left - 1):
            break
        left -= 1
    right = end
    if not (quote.rstrip()[-1:] in ".!?" and _is_sentence_end(text, start + len(quote.rstrip()) - 1)):
        while right < len(text):
            if text[right:right + 2] == "\n\n":
                break
            if _is_sentence_end(text, right):
                right += 1
                break
            right += 1
    span = " ".join(text[left:right].split()).lstrip("-*•· ").strip()
    if not span or len(span) > _SENTENCE_CAP:
        return None
    return span


def _display_text(item):
    origin = item["origin"]
    quote = origin["verbatim_quote"]
    try:
        text = Path(origin["_saved_path"]).read_text(encoding="utf-8")
    except (KeyError, OSError, UnicodeDecodeError):
        return item["promise"]["promise_text"], False
    sentence = display_sentence(text, quote)
    if not sentence or sentence == " ".join(quote.split()):
        return item["promise"]["promise_text"], False
    return sentence, True


def _centroid_fields(neighborhood):
    """Display centroid for a neighborhood-level record (never a claim site).
    Regional and unknown locations get no point, so the map does not plot them."""
    from src.geo_centroids import LOCATION_CENTROIDS
    point = LOCATION_CENTROIDS.get(neighborhood)
    return {"latitude": point[0], "longitude": point[1]} if point else {}


def build_record(item, *, promise_id, rank, entity_count):
    promise, origin = item["promise"], item["origin"]
    display_text, expanded = _display_text(item)
    verdict = VERDICT_MAP[item["latest"]["verdict"]]
    canonical = ENTITY_CATEGORY[promise["entity_type"]]
    category = SECTOR_CATEGORY.get(promise["sector"], promise["sector"])
    neighborhood = promise["neighborhood"]
    scope = ("citywide" if neighborhood == "Citywide"
             else "regional" if neighborhood.startswith("Regional") else "neighborhood")
    promised, deadline = promise["date_promised"], promise["date_deadline"]
    basis = item["basis"]
    # Missing deadline follows the legacy export's convention: null date, status
    # and precision "not_applicable", display "No fixed deadline".
    open_ended = deadline is None
    outcome_basis = _outcome_basis_field(item["outcome_basis"], open_ended)

    history = [{"verdict": VERDICT_MAP[v["verdict"]], "decided_at": v["decided_at"],
                "reason": v["reason"]} for v in item["verdicts"]]
    newest = {}
    for row in item["verifications"]:
        newest[row["check_type"]] = row
    verification_history = []
    for row in sorted(newest.values(), key=lambda r: (r["checked_at"], r["verification_id"])):
        entry = {"check": row["check_type"], "passed": bool(row["passed"]),
                 "checked_at": row["checked_at"]}
        if row["model_id"]:
            entry["model_id"] = row["model_id"]
        verification_history.append(entry)

    phases = {e["phase"] for e in item["evidence"]}
    verifier = next((r for r in reversed(item["verifications"])
                     if r["check_type"] == "independent_verifier"), None)
    required = REQUIRED_PHASES.get(item["latest"]["verdict"], ())
    contradictory = bool(
        item["latest"]["verdict"] in ("BROKEN", "KEPT_THEN_REVERSED")
        and phases & {"DELIVERY", "SURVIVAL"})
    # The origin source always supports the promise; cited outcome evidence
    # counts for the verdict unless the verdict is a contradiction.
    refuting = (sum(e["phase"] in ("DELIVERY", "SURVIVAL") for e in item["evidence"])
                if contradictory else 0)
    supporting = 1 + len(item["evidence"]) - refuting
    # Results of the checks this merge itself just ran against the saved bytes
    # and the database's own rows.
    checks = [
        {"check": "authenticity_domain", "passed": True,
         "reason": "Source domain and tier re-screened at export."},
        {"check": "authenticity_hash", "passed": True,
         "reason": "SHA-256 of every cited saved source re-computed at export and matched."},
        {"check": "accuracy_quote", "passed": True,
         "reason": "Every cited quote found verbatim in the saved source text at export."},
        {"check": "accuracy_date", "passed": True,
         "reason": "Origin publication date is consistent with the promise date and deadline."},
        {"check": "verdict_evidence",
         "passed": all(phase in phases for phase in required),
         "reason": ("Evidence phases required by the verdict are present: "
                    + (", ".join(required) if required else "none beyond the origin") + ".")},
        {"check": "independent_verifier",
         "passed": bool(verifier is not None and verifier["passed"] == 1),
         "reason": "A passed independent verifier row is recorded for this promise."},
    ]
    failed = [c["check"] for c in checks if not c["passed"]]

    record = {
        "promise_id": promise_id,
        "pipeline": "v2",
        "v2_promise_id": promise["promise_id"],
        "promise_text": display_text,
        "promise_text_expanded": expanded,
        "entity": promise["entity_name"],
        "role": None,
        "entity_type": canonical,
        "entity_type_legacy": promise["entity_type"],
        "sector": promise["sector"],
        "category": category,
        "category_l1": category,
        "pillar": SECTOR_PILLAR[promise["sector"]],
        "neighborhood": neighborhood,
        "neighborhood_canonical": neighborhood,
        "geographic_scope": scope,
        "is_citywide": neighborhood == "Citywide",
        "is_centroid": scope != "exact_address",
        **_centroid_fields(neighborhood),
        "promised_date": promised,
        "due_date": deadline,
        "promise_made_date": promised,
        "deadline_date": deadline,
        "completion_date": None,
        "promise_date_precision": "day",
        "due_date_precision": "not_applicable" if open_ended else "day",
        "completion_date_precision": "not_recorded",
        "promised_date_display": _format_date(promised) or "Not recorded",
        "due_date_display": ("No fixed deadline" if open_ended
                             else _format_date(deadline) or "Not recorded"),
        "due_date_status": "not_applicable" if open_ended else "present",
        "completion_date_status": (
            "not_yet_known" if verdict in ("in_progress", "undecided")
            else "not_applicable" if verdict == "broken" else "not_captured"),
        "address_full": None,
        "address_status": "not_applicable" if scope in ("citywide", "regional") else "not_captured",
        "supervisor_district": None,
        "district_status": "not_applicable" if scope in ("citywide", "regional") else "not_captured",
        "page_number": None,
        "verdict": verdict,
        "verdict_reason": item["latest"]["reason"],
        "decided_at": item["latest"]["decided_at"],
        "factual_outcome": _reason_text(item["latest"]["reason"], verdict),
        "source_id": "S" + origin["content_sha256"][:12],
        "source_url": origin["url"],
        "source_file_path": origin["_file"],
        "source_hash": origin["content_sha256"],
        "source_type": TIER_SOURCE_TYPE[origin["source_tier"]],
        "source_tier": _source_tier_label(origin["url"]),
        "fetched_at": None,
        "verbatim_quote": origin["verbatim_quote"],
        "title": f"{promise['entity_name']} Commitment",
        "document_title": f"{promise['entity_name']} Commitment",
        "relevance": {
            "score": item["relevance"]["total"], "real": item["relevance"]["real_promise"],
            "measurable": item["relevance"]["measurable"], "sf": item["relevance"]["sf_relevant"],
            "interesting": item["relevance"]["interesting"],
        },
        "advocate_bundles": {},
        "checks": checks,
        "all_checks_passed": not failed,
        "failed_check_count": len(failed),
        "failed_check_names": failed,
        "verdict_history": history,
        "verification_history": verification_history,
        "evidence": [{
            "phase": e["phase"], "source_tier": e["source_tier"], "url": e["url"],
            "published_date": e["published_date"], "source_hash": e["content_sha256"],
            "source_file_path": e["_file"], "quote": e["verbatim_quote"],
        } for e in item["evidence"]],
        "has_contradictory_evidence": contradictory,
        **_evidence_summaries(item, contradictory),
        "verdict_supporting_evidence_count": supporting,
        "verdict_contradicting_evidence_count": refuting,
        "affirming_evidence_count": supporting,
        "refuting_evidence_count": refuting,
        "record_type": "promise",
        "impact_rank": rank,
        "display_no": rank,
        "entity_canonical_name": promise["entity_name"],
        "entity_category": canonical,
        "entity_category_canonical": canonical,
        "entity_promise_count": entity_count,
        "entity_sample_warning": entity_count < 3,
    }
    if outcome_basis is not None:
        record["outcome_basis"] = outcome_basis
    if basis is not None:
        record["promise_date_basis"] = basis["basis"]
        record["promise_date_derived"] = basis["basis"] != "stated"
        record["promised_date_note"] = basis["note"]
    return record


def merge_v2(payload, sources):
    """Merge v2-published promises into ``payload`` in place.

    ``sources`` is a list of ``(database_path, sources_root)``. Existing
    records are never modified. Returns a report dict.
    """
    promises = payload["promises"]
    existing_before = len(promises)
    used_ids = {p["promise_id"] for p in promises}
    by_url, texts = _existing_index(promises)
    entity_counts = Counter(p.get("entity_canonical_name") or p.get("entity") for p in promises)
    report = {"added": [], "duplicates": [], "rejected": [], "databases": len(sources)}

    for number, (db_path, source_root) in enumerate(sources, start=1):
        loaded, rejected = load_v2_promises(db_path, source_root)
        report["rejected"] += [{**r, "database": number} for r in rejected]
        for item in loaded:
            reason = _find_duplicate(item, by_url, texts)
            v2_id = item["promise"]["promise_id"]
            if reason:
                report["duplicates"].append(
                    {"promise_id": v2_id, "reason": reason, "database": number})
                continue
            promise_id = v2_id
            if promise_id in used_ids:
                promise_id = f"V2-{v2_id}"
            if promise_id in used_ids:
                promise_id = f"V2-{number}-{v2_id}"
            if promise_id in used_ids:
                report["rejected"].append(
                    {"promise_id": v2_id, "reason": "id_collision", "database": number})
                continue
            entity = item["promise"]["entity_name"]
            entity_counts[entity] += 1
            record = build_record(
                item, promise_id=promise_id, rank=len(promises) + 1,
                entity_count=entity_counts[entity])
            used_ids.add(promise_id)
            promises.append(record)
            quotes = [record["promise_text"], record["verbatim_quote"]]
            for evidence in record["evidence"]:
                by_url.setdefault(_url_key(evidence["url"]), []).append((promise_id, quotes))
            texts.add(_text_key(record["promise_text"]))
            report["added"].append({"promise_id": promise_id, "verdict": record["verdict"]})

    added = len(report["added"])
    by_verdict = dict(sorted(Counter(a["verdict"] for a in report["added"]).items()))
    report["added_by_verdict"] = by_verdict
    status = payload["database_status"]
    counts = Counter(status.get("counts") or {})
    counts.update(by_verdict)
    status["counts"] = dict(counts)
    status["tracked_count"] = len(promises)
    status["v2_promises_added"] = added
    status["v2_merge"] = {
        "databases": len(sources), "added": added, "added_by_verdict": by_verdict,
        "skipped_duplicates": len(report["duplicates"]), "rejected": len(report["rejected"]),
        "legacy_promises": existing_before,
        "funnel_scope": "Funnel and DB totals count the legacy database only.",
    }
    quarantined = status.get("quarantine_registry_count", 0)
    pending = status.get("pending_intake_count", 0)
    status["id_reconciliation"] = (
        f"{len(promises)} published ({added} from v2 pipeline) · {quarantined} in quarantine "
        f"registry · {pending} seeds awaiting intake")
    status.setdefault("discrepancies", []).append(
        f"{added} of {len(promises)} published records come from the v2 pipeline; their sources "
        "were re-hashed and every quote re-found in saved text at export. Funnel and DB totals "
        "count the legacy database only.")
    payload["metadata"]["v2_promises_added"] = added
    payload["metadata"]["legacy_promises"] = existing_before
    return report


def format_report(report):
    lines = [f"v2 merge: added {len(report['added'])}"
             + (f" {report['added_by_verdict']}" if report["added"] else "")
             + f", skipped duplicates {len(report['duplicates'])}"
             + f", rejected {len(report['rejected'])}"]
    for dup in report["duplicates"]:
        lines.append(f"  duplicate {dup['promise_id']} (db {dup['database']}): {dup['reason']}")
    for rej in report["rejected"]:
        lines.append(f"  rejected {rej['promise_id']} (db {rej['database']}): {rej['reason']}")
    return "\n".join(lines)
