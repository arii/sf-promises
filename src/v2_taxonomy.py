"""Screen taxonomy labels; valid labels do not establish factual accuracy."""

ENTITY_TYPES = frozenset({
    "Mayor / Executive", "City Agency", "Board of Supervisors", "State Regulator",
    "Private Corporation", "Sports Franchise", "Developer",
})
SECTORS = frozenset({
    "Housing & Land Use", "Transit & Streets", "Homelessness & Behavioral Health",
    "Public Safety & Justice", "Energy & Infrastructure", "Environment & Energy", "Autonomous Vehicles",
    "Parks & Recreation", "Sports, Culture & Retail", "Governance & Finance",
})
LOCATIONS = frozenset({
    "Citywide", "Mid-Market & Civic Center", "Tenderloin", "SoMa",
    "Mission Bay & Mission Rock", "Treasure Island", "Parkmerced",
    "Pier 70 & Dogpatch", "Chinatown & North Beach", "Golden Gate Park",
    "The Embarcadero", "Union Square & Financial District", "Twin Peaks",
    "Haight-Ashbury", "Presidio & Doyle Drive", "Bayview-Hunters Point",
    "Regional / Northern California",
})


def screen_taxonomy(*, entity_name, entity_type, sector, neighborhood, quote,
                    has_verified_sf_link=False):
    """Return failed checks; entity and location still require source review."""
    failures = []
    if not isinstance(entity_name, str) or not entity_name.strip():
        failures.append("entity_missing")
    elif any(term in entity_name.casefold() for term in ("spokesman", "spokesperson")):
        failures.append("spokesperson_not_entity")
    if not isinstance(entity_type, str) or entity_type not in ENTITY_TYPES:
        failures.append("entity_type_invalid")
    if not isinstance(sector, str) or sector not in SECTORS:
        failures.append("sector_invalid")
    if not isinstance(neighborhood, str) or neighborhood not in LOCATIONS:
        failures.append("neighborhood_invalid")
    elif neighborhood == "Regional / Northern California" and has_verified_sf_link is not True:
        failures.append("regional_sf_link_unverified")
    if (neighborhood == "Treasure Island" and isinstance(quote, str)
            and "parkmerced" in quote.casefold()):
        failures.append("geography_conflict")
    return failures
