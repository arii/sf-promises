"""Stage 3: Outcome-blind Qualification & Intake Agent and Auditable Candidate Register."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.sourcing.planner import TEN_CONTENT_PILLARS

QUALIFICATION_STATUSES = ("qualified", "needs_review", "rejected")

REJECTION_REASONS = (
    "no_responsible_actor",
    "vague_aspiration",
    "already_completed",
    "unattributed_rumor",
    "outside_sf",
    "pending_hydration",
)

# Fields that expose downstream outcome and MUST be hidden from qualification
_OUTCOME_LEAK_FIELDS = frozenset({
    "verdict",
    "verdict_reason",
    "verdict_reason_code",
    "verdict_confidence",
    "factual_outcome",
    "completion_date",
    "opened_date",
    "realized_date",
    "completion_percentage",
    "advocate_bundles",
})

_FORWARD_ACTION_RE = re.compile(
    r"\b(will|commit|commits|committed|pledge|pledges|pledged|plan|plans|planned|scheduled|"
    r"set to|aims|target|goal|must complete|prohibiting|begin|opening|launching|construct|"
    r"add \d+|hire|fund|invest|maintain|evaluate|by \d{4})\b",
    re.IGNORECASE,
)

_SF_CONTEXT_RE = re.compile(
    r"\b(San Francisco|SF|SFMTA|SFPUC|SFPD|SFO|SFUSD|BART|Muni|CleanPowerSF|"
    r"Tenderloin|Mission|SoMa|Sunset|Marina|Castro|Excelsior|Chinatown|Union Square|"
    r"Embarcadero|Market Street|Chase Center|Oracle Park|Golden Gate Park|Stern Grove|"
    r"Valencias?|Potrero|Dogpatch|Parkmerced|Treasure Island|City Hall|Bay Area)\b",
    re.IGNORECASE,
)


def strip_outcome_fields(raw_candidate: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure QualificationIntakeAgent sees only origin/announcement attributes."""
    return {k: v for k, v in raw_candidate.items() if k not in _OUTCOME_LEAK_FIELDS}


def _kw_match(text: str, terms: tuple[str, ...]) -> bool:
    for term in terms:
        if re.search(r"\b" + re.escape(term) + r"\b", text):
            return True
    return False


def infer_pillar(text: str, category: str = "", tags: Optional[List[str]] = None) -> str:
    combined = " ".join([text or "", category or "", " ".join(tags or [])]).lower()
    if _kw_match(combined, ("climate", "seawall", "earthquake", "seismic", "natural gas", "all-electric", "cleanpower", "cleanpowersf", "renewable", "wildfire", "ocean beach", "coastal", "flood")):
        return "Weather & Environment"
    if _kw_match(combined, ("shelter", "homeless", "homelessness", "housing", "soft-story", "supportive housing", "zoning", "navigation center", "pier 70", "potrero", "treasure island")):
        return "Housing & Neighborhoods"
    if _kw_match(combined, ("wifi", "wi-fi", "fiber", "broadband", "gigabit", "permitting", "small business", "local hiring", "headquarters", "grants", "stem", "sfusd", "computer science", "mid-market")):
        return "Work & Opportunity"
    if _kw_match(combined, ("concert", "concerts", "theatre", "theater", "music", "festival", "art", "arts", "mural", "museum", "stern grove", "cinema")):
        return "Arts, Music & Nightlife"
    if _kw_match(combined, ("bike lane", "bikeway", "sfmta", "muni", "transit", "robotaxi", "autonomous", "cruise", "waymo", "zoox", "subway", "sfo", "runway", "ferry", "vision zero", "scooters")):
        return "Transit & Movement"
    if _kw_match(combined, ("sport", "sports", "wnba", "valkyries", "warriors", "giants", "bay fc", "stadium", "chase center", "recreation", "promenade")):
        return "Sports & Recreation"
    if _kw_match(combined, ("restaurant", "dining", "grocery", "mall", "westfield", "retail", "union square", "winter walk", "hospitality")):
        return "Food & Local Business"
    if _kw_match(combined, ("healthcare", "mental health", "behavioral health", "youth", "senior", "student", "language access")):
        return "People & Demographics"
    if _kw_match(combined, ("culture", "tradition", "heritage", "community plaza", "parade")):
        return "Culture & Social Life"
    return "Civic Life"


def infer_record_type(text: str, pillar: str = "") -> str:
    low = (text or "").lower()
    if any(w in low for w in ("open", "reopen", "construct", "build", "install", "facility", "terminal", "runway", "theatre", "mall", "center", "metro", "wifi", "wi-fi")):
        return "project_or_opening"
    if any(w in low for w in ("%", "percent", "million homes", "reduce", "fatalities", "attendance", "forecast", "target of")):
        return "claim_or_forecast"
    if pillar in ("Weather & Environment", "People & Demographics", "Culture & Social Life") and "report" in low:
        return "sf_signal"
    return "promise"


def infer_geographic_metadata(raw: Dict[str, Any]) -> Dict[str, Any]:
    scope = raw.get("geographic_scope")
    is_citywide = bool(raw.get("is_citywide"))
    district = raw.get("supervisor_district")
    neighborhood = raw.get("neighborhood_canonical") or raw.get("neighborhood") or "San Francisco"
    addr = raw.get("address_full")

    if not scope:
        if addr:
            scope = "exact_address"
        elif is_citywide or "citywide" in neighborhood.lower():
            scope = "citywide"
        elif "regional" in neighborhood.lower() or "northern california" in neighborhood.lower():
            scope = "regional"
        elif district is not None:
            scope = "district"
        else:
            scope = "neighborhood"
    elif scope == "citywide_centroid":
        scope = "citywide"

    is_centroid = (scope != "exact_address")
    addr_status = "present" if addr else ("not_applicable" if scope in ("citywide", "regional") else "not_captured")
    dist_status = "present" if district is not None else ("not_applicable" if scope in ("citywide", "regional") else "not_captured")

    return {
        "geographic_scope": scope,
        "is_centroid": is_centroid,
        "supervisor_district": district,
        "neighborhood": neighborhood,
        "address_status": addr_status,
        "district_status": dist_status,
    }


def _date_precision(d_val: Optional[str]) -> str:
    if not d_val or str(d_val).strip() in ("", "None", "null", "not recorded"):
        return "not_recorded"
    s = str(d_val).strip()
    if len(s) == 4 and s.isdigit():
        return "year"
    if len(s) == 7 and s[4] == "-":
        return "month"
    return "day"


@dataclass
class AuditableCandidate:
    candidate_id: str
    source_batch: str
    discovery_channel: str
    encounter_date: str
    entity: str
    pillar: str
    record_type: str
    statement_preview: str
    promised_date: Optional[str]
    promise_date_precision: str
    due_date: Optional[str]
    due_date_status: str
    geographic_scope: str
    is_centroid: bool
    supervisor_district: Optional[int]
    neighborhood: str
    address_status: str
    district_status: str
    source_url: Optional[str]
    source_tier: str
    media_image_url: Optional[str]
    media_caption: Optional[str]
    qualification_status: str
    rejection_reason: Optional[str]
    dual_review_sample: bool = False
    dual_review_agreed: Optional[bool] = None
    outcome_blind_verified: bool = True
    missingness_note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class QualificationIntakeAgent:
    """Screens encountered candidates blind to outcomes and populates the Auditable Candidate Register."""

    def evaluate_candidate(
        self,
        raw_candidate: Dict[str, Any],
        *,
        source_batch: str,
        discovery_channel: str,
        encounter_date: Optional[str] = None,
        dual_sample: bool = False,
    ) -> AuditableCandidate:
        blind = strip_outcome_fields(raw_candidate)
        cid = str(blind.get("promise_id") or blind.get("candidate_id") or "").strip()
        text = str(blind.get("promise_text") or blind.get("verbatim_quote") or blind.get("snippet") or "").strip()
        entity = str(blind.get("entity") or "").strip()
        url = blind.get("source_url") or blind.get("url")
        tier = str(blind.get("source_tier") or blind.get("tier") or "TIER3_DISCOVERY_ONLY")
        promised_date = blind.get("promised_date") or (
            str(blind.get("published_at"))[:10] if blind.get("published_at") else None
        )
        due_date = blind.get("due_date")

        geo = infer_geographic_metadata(blind)
        pillar = blind.get("pillar") or infer_pillar(
            text, category=str(blind.get("category") or ""), tags=blind.get("tags")
        )
        if pillar not in TEN_CONTENT_PILLARS:
            pillar = "Civic Life"

        rec_type = blind.get("record_type") or infer_record_type(text, pillar=pillar)

        p_prec = _date_precision(promised_date)
        due_status = "present" if due_date else "not_applicable"

        # Handle unhydrated pending IDs transparently without fabricating text
        if blind.get("pending_hydration"):
            return AuditableCandidate(
                candidate_id=cid,
                source_batch=source_batch,
                discovery_channel=discovery_channel,
                encounter_date=encounter_date or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                entity=entity or "Pending Seed Record",
                pillar=pillar,
                record_type="promise",
                statement_preview="",
                promised_date=None,
                promise_date_precision="not_recorded",
                due_date=None,
                due_date_status="not_captured",
                geographic_scope="citywide",
                is_centroid=True,
                supervisor_district=None,
                neighborhood="San Francisco",
                address_status="not_captured",
                district_status="not_captured",
                source_url=None,
                source_tier="TIER3_DISCOVERY_ONLY",
                media_image_url=None,
                media_caption=None,
                qualification_status="needs_review",
                rejection_reason="pending_hydration",
                dual_review_sample=False,
                dual_review_agreed=None,
                outcome_blind_verified=True,
                missingness_note="Awaiting source CSV/Archil DB mount to hydrate seed text for intake triage.",
            )

        # Reviewer A (Rule check) & Reviewer B (Taxonomy/Attribution strict check)
        has_actor = bool(entity) and "spokesman" not in entity.lower() and entity.lower() not in ("unknown", "none")
        has_forward = bool(_FORWARD_ACTION_RE.search(text))
        has_sf = bool(_SF_CONTEXT_RE.search(text + " " + geo["neighborhood"] + " " + entity))

        rej_reason: Optional[str] = None
        if not has_actor:
            rej_reason = "no_responsible_actor"
        elif not has_sf:
            rej_reason = "outside_sf"
        elif not has_forward:
            rej_reason = "vague_aspiration"

        rev_a_qualified = (rej_reason is None)
        rev_b_qualified = rev_a_qualified and len(text) >= 35 and bool(url)

        if rej_reason is not None:
            q_status = "rejected"
        elif rev_a_qualified and rev_b_qualified:
            q_status = "qualified"
        else:
            q_status = "needs_review"

        agreed: Optional[bool] = None
        if dual_sample:
            agreed = (rev_a_qualified == rev_b_qualified)
            if not agreed and q_status == "qualified":
                q_status = "needs_review"

        return AuditableCandidate(
            candidate_id=cid,
            source_batch=source_batch,
            discovery_channel=discovery_channel,
            encounter_date=encounter_date or str(promised_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")),
            entity=entity,
            pillar=pillar,
            record_type=rec_type,
            statement_preview=text[:240],
            promised_date=promised_date,
            promise_date_precision=p_prec,
            due_date=due_date,
            due_date_status=due_status,
            geographic_scope=geo["geographic_scope"],
            is_centroid=geo["is_centroid"],
            supervisor_district=geo["supervisor_district"],
            neighborhood=geo["neighborhood"],
            address_status=geo["address_status"],
            district_status=geo["district_status"],
            source_url=url,
            source_tier=tier,
            media_image_url=blind.get("image_url") or blind.get("media_image_url"),
            media_caption=blind.get("media_caption"),
            qualification_status=q_status,
            rejection_reason=rej_reason,
            dual_review_sample=dual_sample,
            dual_review_agreed=agreed,
            outcome_blind_verified=True,
            missingness_note="Screened strictly without outcome fields.",
        )

    @staticmethod
    def should_dual_sample(candidate_id: str, rate: float = 0.20) -> bool:
        """Deterministic 20% dual-review sampling based on SHA-256 of candidate_id."""
        bucket = int(hashlib.sha256(candidate_id.encode("utf-8")).hexdigest()[:4], 16) % 100
        return bucket < int(rate * 100)
