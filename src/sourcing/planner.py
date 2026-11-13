"""Stage 1: Outcome-blind stratified Search Planner across all 10 SF pillars and 11 districts.

D2 diversification: gap-priority districts (2, 4, 8, 11) additionally get
Spanish and Chinese query variants per pillar, and every pillar carries at
least one non-institutional source (community/ethnic press, neighborhood
paper). Neighborhood proper names are localized where a rendering is
well-attested in SF's Spanish- and Chinese-language press; the canonical
English name is always kept alongside any alias so a query never depends on
the alias alone.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

TEN_CONTENT_PILLARS: Dict[str, Dict[str, object]] = {
    "Arts, Music & Nightlife": {
        "target_share": 0.10,
        "domain_nouns": ["exhibition", "concert", "mural", "festival", "venue", "public art"],
        "sources": ["sfartscommission.org", "sfmoma.org", "sfchronicle.com", "eltecolote.org"],
        "priority": "high_undercovered",
    },
    "Sports & Recreation": {
        "target_share": 0.10,
        "domain_nouns": ["season", "park renovation", "stadium", "championship", "race"],
        "sources": ["valkyries.wnba.com", "bayfc.com", "sfrecpark.org", "singtaousa.com"],
        "priority": "high_undercovered",
    },
    "Food & Local Business": {
        "target_share": 0.10,
        "domain_nouns": ["restaurant opening", "farmers market", "legacy business", "corridor"],
        "sources": ["sf.eater.com", "sfstandard.com", "sf.gov", "elreporterosf.com"],
        "priority": "high_undercovered",
    },
    "Weather & Environment": {
        "target_share": 0.10,
        "domain_nouns": ["climate target", "seawall", "clean power", "urban greening", "heat"],
        "sources": ["sfenvironment.org", "cleanpowersf.org", "sfpuc.org", "sfport.com", "sfbayview.com"],
        "priority": "medium",
    },
    "Transit & Movement": {
        "target_share": 0.10,
        "domain_nouns": ["Muni route", "bike lane", "ferry", "runway", "robotaxi"],
        "sources": ["sfmta.com", "flysfo.com", "sfcta.org", "inglesidelight.com"],
        "priority": "medium",
    },
    "Housing & Neighborhoods": {
        "target_share": 0.10,
        "domain_nouns": ["housing units", "construction start", "zoning", "navigation center"],
        "sources": ["sfplanning.org", "sf.gov", "missionlocal.org", "eltecolote.org"],
        "priority": "capped_overrepresented",
    },
    "People & Demographics": {
        "target_share": 0.10,
        "domain_nouns": ["language access", "youth program", "senior center", "healthcare enrollment"],
        "sources": ["sf.gov", "dcyf.org", "sfpublicpress.org", "singtaousa.com"],
        "priority": "high_undercovered",
    },
    "Work & Opportunity": {
        "target_share": 0.10,
        "domain_nouns": ["workforce training", "apprenticeship", "small business grant", "office lease"],
        "sources": ["oewd.org", "sf.gov", "sfchronicle.com", "elreporterosf.com"],
        "priority": "high_undercovered",
    },
    "Culture & Social Life": {
        "target_share": 0.10,
        "domain_nouns": ["parade", "heritage event", "pedestrian plaza", "community tradition"],
        "sources": ["missionlocal.org", "thefrisc.com", "kqed.org", "noevalleyvoice.com"],
        "priority": "high_undercovered",
    },
    "Civic Life": {
        "target_share": 0.10,
        "domain_nouns": ["city budget", "ordinance", "public safety", "departmental service"],
        "sources": ["sfbos.org", "sfgov.legistar.com", "sf.gov", "inglesidelight.com"],
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

# D2: gap-priority districts get query variants in these languages.
FLAGGED_DISTRICT_LANGUAGES: tuple[str, ...] = ("es", "zh")

# Per-language query scaffolding: localized city name, the "announced" OR-term,
# and committed verbs mirroring COMMITMENT_VERBS. Traditional Chinese is used
# for the zh set, matching the script SF's Chinese-language press publishes in.
LANGUAGE_QUERY_LOCALIZATION: Dict[str, Dict[str, object]] = {
    "es": {
        "city_name": "San Francisco",
        "announced": "anunci\u00f3",
        "commitment_verbs": (
            "promete",
            "anunciar\u00e1",
            "planea",
            "comprometido a",
            "previsto para",
            "abrir\u00e1 en",
            "lanzar\u00e1 en",
            "espera",
        ),
    },
    "zh": {
        "city_name": "\u820a\u91d1\u5c71",
        "announced": "\u5ba3\u4f48",
        "commitment_verbs": (
            "\u5c07",
            "\u8a08\u5283",
            "\u627f\u8afe",
            "\u5b9a\u65bc",
            "\u5c07\u65bc",
            "\u958b\u5e55",
            "\u63a8\u51fa",
            "\u9810\u8a08",
        ),
    },
}

# District label and neighborhood renderings per language. Only well-attested
# renderings from SF's Spanish- and Chinese-language press are listed; a
# neighborhood without an attested alias keeps its canonical English name,
# which every variant query includes regardless.
DISTRICT_LANGUAGE_LOCALIZATION: Dict[int, Dict[str, Dict[str, object]]] = {
    2: {
        "es": {
            "district_label": "Distrito 2",
            "neighborhood_aliases": {},
        },
        "zh": {
            "district_label": "\u7b2c2\u9078\u5340",
            "neighborhood_aliases": {"Pacific Heights": "\u592a\u5e73\u6d0b\u9ad8\u5730"},
        },
    },
    4: {
        "es": {
            "district_label": "Distrito 4",
            "neighborhood_aliases": {"Outer Sunset": "el Sunset"},
        },
        "zh": {
            "district_label": "\u7b2c4\u9078\u5340",
            "neighborhood_aliases": {"Outer Sunset": "\u65e5\u843d\u5340"},
        },
    },
    8: {
        "es": {
            "district_label": "Distrito 8",
            "neighborhood_aliases": {"Castro": "el Castro"},
        },
        "zh": {
            "district_label": "\u7b2c8\u9078\u5340",
            "neighborhood_aliases": {"Castro": "\u5361\u65af\u695a\u5340", "Noe Valley": "\u8afe\u4f0a\u8c37"},
        },
    },
    11: {
        "es": {
            "district_label": "Distrito 11",
            "neighborhood_aliases": {},
        },
        "zh": {
            "district_label": "\u7b2c11\u9078\u5340",
            "neighborhood_aliases": {"Outer Mission": "\u7c73\u614e\u5340"},
        },
    },
}


def flagged_districts() -> List[int]:
    """Districts with gap_priority in SF_SUPERVISOR_DISTRICTS (currently 2, 4, 8, 11)."""
    return sorted(
        d for d, meta in SF_SUPERVISOR_DISTRICTS.items() if meta.get("gap_priority")
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
    language: str = "en"


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

    def generate_diversified_variants(
        self,
        pillars: Optional[Sequence[str]] = None,
        districts: Optional[Sequence[int]] = None,
        time_window: str = "2016-01-01..2026-11-12",
    ) -> List[SearchQuerySpec]:
        """Spanish and Chinese query variants per pillar for gap-priority districts (D2).

        The English stratified queries are untouched; variants are additive.
        Every variant targets only domains already in the pillar's sources
        list, so the planner and the allowlist move together per the spec.
        """
        selected_pillars = list(pillars) if pillars else list(TEN_CONTENT_PILLARS.keys())
        selected_districts = list(districts) if districts else flagged_districts()

        specs: List[SearchQuerySpec] = []
        for p_idx, pillar in enumerate(selected_pillars):
            meta = TEN_CONTENT_PILLARS[pillar]
            nouns: List[str] = list(meta["domain_nouns"])  # type: ignore[arg-type]
            domains: List[str] = list(meta["sources"])  # type: ignore[arg-type]
            entity_type = (
                "city_department"
                if pillar in ("Civic Life", "Transit & Movement", "Weather & Environment")
                else "cultural_or_business_entity"
            )

            for d_idx, district in enumerate(selected_districts):
                d_meta = SF_SUPERVISOR_DISTRICTS[district]
                localization = DISTRICT_LANGUAGE_LOCALIZATION[district]
                neighborhoods: List[str] = list(d_meta["neighborhoods"])  # type: ignore[arg-type]
                neighborhood = neighborhoods[p_idx % len(neighborhoods)]

                for lang_idx, language in enumerate(FLAGGED_DISTRICT_LANGUAGES):
                    lang_meta = LANGUAGE_QUERY_LOCALIZATION[language]
                    verbs: List[str] = list(lang_meta["commitment_verbs"])  # type: ignore[arg-type]
                    verb = verbs[(p_idx + d_idx + lang_idx) % len(verbs)]
                    noun = nouns[(p_idx + d_idx + lang_idx) % len(nouns)]

                    # Canonical neighborhood name always present; the alias is
                    # additive so a query never depends on the alias alone.
                    aliases: Dict[str, str] = dict(localization[language]["neighborhood_aliases"])  # type: ignore[arg-type]
                    alias = aliases.get(neighborhood, "")
                    parts = [
                        str(lang_meta["city_name"]),
                        str(localization[language]["district_label"]),
                        neighborhood,
                    ]
                    if alias and alias != neighborhood:
                        parts.append(alias)
                    q_text = (
                        " ".join(f'"{part}"' for part in parts)
                        + f' ("{verb}" OR "{lang_meta["announced"]}") "{noun}"'
                    )
                    violations = validate_outcome_blind_query(q_text)
                    if violations:
                        raise ValueError(f"Outcome-biased term in planner query: {violations}")
                    specs.append(
                        SearchQuerySpec(
                            query_id=f"Q-{p_idx+1:02d}-D{district:02d}-{language}",
                            pillar=pillar,
                            supervisor_district=district,
                            neighborhood=neighborhood,
                            time_window=time_window,
                            entity_type=entity_type,
                            query_text=q_text,
                            target_domains=domains,
                            language=language,
                        )
                    )

        return specs

