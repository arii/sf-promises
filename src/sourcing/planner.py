"""Stage 1: Outcome-blind stratified Search Planner across all 10 SF pillars and 11 districts."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

TEN_CONTENT_PILLARS: Dict[str, Dict[str, object]] = {
    "Arts, Music & Nightlife": {
        "target_share": 0.10,
        "domain_nouns": ["exhibition", "concert", "mural", "festival", "venue", "public art"],
        "sources": ["sfartscommission.org", "sfmoma.org", "sfchronicle.com"],
        "priority": "high_undercovered",
    },
    "Sports & Recreation": {
        "target_share": 0.10,
        "domain_nouns": ["season", "park renovation", "stadium", "championship", "race"],
        "sources": ["valkyries.wnba.com", "bayfc.com", "sfrecpark.org"],
        "priority": "high_undercovered",
    },
    "Food & Local Business": {
        "target_share": 0.10,
        "domain_nouns": ["restaurant opening", "farmers market", "legacy business", "corridor"],
        "sources": ["sf.eater.com", "sfstandard.com", "sf.gov"],
        "priority": "high_undercovered",
    },
    "Weather & Environment": {
        "target_share": 0.10,
        "domain_nouns": ["climate target", "seawall", "clean power", "urban greening", "heat"],
        "sources": ["sfenvironment.org", "cleanpowersf.org", "sfpuc.org", "sfport.com"],
        "priority": "medium",
    },
    "Transit & Movement": {
        "target_share": 0.10,
        "domain_nouns": ["Muni route", "bike lane", "ferry", "runway", "robotaxi"],
        "sources": ["sfmta.com", "flysfo.com", "sfcta.org"],
        "priority": "medium",
    },
    "Housing & Neighborhoods": {
        "target_share": 0.10,
        "domain_nouns": ["housing units", "construction start", "zoning", "navigation center"],
        "sources": ["sfplanning.org", "sf.gov", "missionlocal.org"],
        "priority": "capped_overrepresented",
    },
    "People & Demographics": {
        "target_share": 0.10,
        "domain_nouns": ["language access", "youth program", "senior center", "healthcare enrollment"],
        "sources": ["sf.gov", "dcyf.org", "sfpublicpress.org"],
        "priority": "high_undercovered",
    },
    "Work & Opportunity": {
        "target_share": 0.10,
        "domain_nouns": ["workforce training", "apprenticeship", "small business grant", "office lease"],
        "sources": ["oewd.org", "sf.gov", "sfchronicle.com"],
        "priority": "high_undercovered",
    },
    "Culture & Social Life": {
        "target_share": 0.10,
        "domain_nouns": ["parade", "heritage event", "pedestrian plaza", "community tradition"],
        "sources": ["missionlocal.org", "thefrisc.com", "kqed.org"],
        "priority": "high_undercovered",
    },
    "Civic Life": {
        "target_share": 0.10,
        "domain_nouns": ["city budget", "ordinance", "public safety", "departmental service"],
        "sources": ["sfbos.org", "sfgov.legistar.com", "sf.gov"],
        "priority": "capped_overrepresented",
    },
}

SF_SUPERVISOR_DISTRICTS: Dict[int, Dict[str, object]] = {
    1: {"label": "District 1", "neighborhoods": ["Richmond", "Golden Gate Park"]},
    2: {"label": "District 2", "neighborhoods": ["Marina", "Pacific Heights", "Presidio"], "gap_priority": True},
    3: {"label": "District 3", "neighborhoods": ["North Beach", "Chinatown", "Union Square", "Financial District"]},
    4: {"label": "District 4", "neighborhoods": ["Outer Sunset", "Parkside", "Ocean Beach"], "gap_priority": True},
    5: {"label": "District 5", "neighborhoods": ["Haight-Ashbury", "Western Addition", "Tenderloin"]},
    6: {"label": "District 6", "neighborhoods": ["SoMa", "Mission Bay", "Mid-Market", "Treasure Island"]},
    7: {"label": "District 7", "neighborhoods": ["West Portal", "Twin Peaks", "Parkmerced", "Stern Grove"]},
    8: {"label": "District 8", "neighborhoods": ["Castro", "Noe Valley", "Glen Park"], "gap_priority": True},
    9: {"label": "District 9", "neighborhoods": ["Mission", "Bernal Heights", "Portola"]},
    10: {"label": "District 10", "neighborhoods": ["Bayview-Hunters Point", "Dogpatch", "Potrero Hill", "Visitacion Valley"]},
    11: {"label": "District 11", "neighborhoods": ["Excelsior", "Ingleside", "Outer Mission"], "gap_priority": True},
}

COMMITMENT_VERBS = (
    "will",
    "plans to",
    "committed to",
    "scheduled to",
    "set to",
    "opening in",
    "launching in",
    "expects to",
)

BANNED_OUTCOME_TERMS = frozenset({
    "failed",
    "fail",
    "failure",
    "broken",
    "delayed",
    "delay",
    "completed",
    "delivered",
    "kept",
    "scandal",
    "abandoned",
    "lawsuit",
    "controversy",
    "shuttered",
    "defaulted",
})

_BANNED_REGEX = re.compile(
    r"\b(" + "|".join(re.escape(term) for term in sorted(BANNED_OUTCOME_TERMS)) + r")\b",
    re.IGNORECASE,
)


def validate_outcome_blind_query(query: str) -> List[str]:
    """Return any banned outcome-biasing terms found in a planner query."""
    if not query or not query.strip():
        return ["empty_query"]
    matches = _BANNED_REGEX.findall(query)
    return sorted({m.lower() for m in matches})


@dataclass(frozen=True)
class SearchQuerySpec:
    query_id: str
    pillar: str
    supervisor_district: int
    neighborhood: str
    time_window: str
    entity_type: str
    query_text: str
    target_domains: List[str] = field(default_factory=list)


class SearchPlanner:
    """Generates outcome-blind search batches balanced across all 10 pillars and 11 districts."""

    def __init__(self, max_civic_share: float = 0.25):
        self.max_civic_share = max_civic_share

    def generate_stratified_queries(
        self,
        pillars: Optional[Sequence[str]] = None,
        districts: Optional[Sequence[int]] = None,
        time_window: str = "2016-01-01..2026-11-12",
        max_per_pillar: int = 2,
    ) -> List[SearchQuerySpec]:
        selected_pillars = list(pillars) if pillars else list(TEN_CONTENT_PILLARS.keys())
        selected_districts = list(districts) if districts else list(SF_SUPERVISOR_DISTRICTS.keys())

        # Prioritize undercovered districts (2, 4, 8, 11) first when rotating
        ordered_districts = sorted(
            selected_districts,
            key=lambda d: (0 if SF_SUPERVISOR_DISTRICTS[d].get("gap_priority") else 1, d),
        )

        specs: List[SearchQuerySpec] = []
        dist_idx = 0
        for p_idx, pillar in enumerate(selected_pillars):
            meta = TEN_CONTENT_PILLARS[pillar]
            nouns: List[str] = list(meta["domain_nouns"])  # type: ignore[arg-type]
            domains: List[str] = list(meta["sources"])  # type: ignore[arg-type]

            # Enforce civic/political cap on batch count
            count_for_pillar = 1 if (pillar in ("Civic Life", "Housing & Neighborhoods") and max_per_pillar > 1) else max_per_pillar

            for slot in range(count_for_pillar):
                district = ordered_districts[dist_idx % len(ordered_districts)]
                dist_idx += 1
                d_meta = SF_SUPERVISOR_DISTRICTS[district]
                neighborhoods: List[str] = list(d_meta["neighborhoods"])  # type: ignore[arg-type]
                neighborhood = neighborhoods[slot % len(neighborhoods)]
                verb = COMMITMENT_VERBS[(p_idx + slot) % len(COMMITMENT_VERBS)]
                noun = nouns[slot % len(nouns)]
                entity_type = (
                    "city_department"
                    if pillar in ("Civic Life", "Transit & Movement", "Weather & Environment")
                    else "cultural_or_business_entity"
                )
                q_text = f'"San Francisco" "{neighborhood}" ("{verb}" OR "announced") "{noun}"'
                violations = validate_outcome_blind_query(q_text)
                if violations:
                    raise ValueError(f"Outcome-biased term in planner query: {violations}")
                specs.append(
                    SearchQuerySpec(
                        query_id=f"Q-{p_idx+1:02d}-D{district:02d}-{slot+1}",
                        pillar=pillar,
                        supervisor_district=district,
                        neighborhood=neighborhood,
                        time_window=time_window,
                        entity_type=entity_type,
                        query_text=q_text,
                        target_domains=domains,
                    )
                )

        # Verify Civic + Housing share respects stratification balance when all 10 pillars queried
        if len(selected_pillars) >= 5 and specs:
            civic_count = sum(1 for s in specs if s.pillar in ("Civic Life", "Housing & Neighborhoods"))
            if civic_count / len(specs) > self.max_civic_share + 0.05:
                raise ValueError("Civic/Housing share exceeded stratified cap")

        return specs
