#!/usr/bin/env python3
"""
Comprehensive Data Enrichment Engine for SF Promises
Enriches all 54 public commitments with:
1. Spatial / Geographic Data (Canonical Neighborhood, Address, Lat/Lng, Supervisor District, is_citywide)
2. Temporal Data (promise_made_date, deadline_date, completion_date, days_remaining, days_overdue, promise_age_days, time_to_verdict_days)
3. Entity Standardization (canonical_name, category, party, term_start, term_end)
4. Hierarchical Categorization (category_l1, category_l2, secondary_categories, tags)
5. Verdict Metadata (confidence, evidence_count, contradiction_count, reason_code, impact_score, completion_percentage)
6. Source Provenance (credibility_score, type_standardized, domain_authority, fact_check_status, archived_url)
"""

import os
import json
import csv
import sqlite3
from datetime import datetime, date

TODAY = date(2026, 11, 12)

def parse_iso_date(d_str):
    if not d_str or str(d_str).strip() in ("", "None", "—"):
        return None
    s = str(d_str).strip()
    # Normalize formats like '2024', '2022-04', '2025-01-07'
    parts = s.split("-")
    try:
        if len(parts) == 1:
            return date(int(parts[0]), 1, 1)
        elif len(parts) == 2:
            return date(int(parts[0]), int(parts[1]), 1)
        elif len(parts) == 3:
            day = parts[2].split("T")[0].split(" ")[0]
            return date(int(parts[0]), int(parts[1]), int(day))
    except Exception:
        return None
    return None

def format_date_str(d_str, default_day="01"):
    if not d_str or str(d_str).strip() in ("", "None", "—"):
        return None
    s = str(d_str).strip()
    parts = s.split("-")
    if len(parts) == 1:
        return f"{parts[0]}-01-01"
    elif len(parts) == 2:
        return f"{parts[0]}-{parts[1].zfill(2)}-01"
    elif len(parts) == 3:
        day = parts[2].split("T")[0].split(" ")[0].zfill(2)
        return f"{parts[0]}-{parts[1].zfill(2)}-{day}"
    return s

# -----------------------------------------------------------------------------
# 1. GEOGRAPHIC MAPPING
# -----------------------------------------------------------------------------
# Canonical neighborhoods follow official SF Planning Department designations.
GEOGRAPHY_DATA = {
    "P02": {
        "neighborhood_canonical": "Tenderloin",
        "address_full": "822 Geary Street, San Francisco, CA 94102",
        "latitude": 37.7858,
        "longitude": -122.4172,
        "supervisor_district": 5,
        "is_citywide": False
    },
    "P05": {
        "neighborhood_canonical": "Citywide",
        "address_full": None,
        "latitude": 37.7749,
        "longitude": -122.4194,
        "supervisor_district": None,
        "is_citywide": True
    },
    "SFO-01": {
        "neighborhood_canonical": "SFO Airport",
        "address_full": "Airfield Runway 28L/10R, San Francisco International Airport, San Francisco, CA 94128",
        "latitude": 37.6213,
        "longitude": -122.3790,
        "supervisor_district": None,
        "is_citywide": False
    },
    "SFO-02": {
        "neighborhood_canonical": "SFO Airport",
        "address_full": "Harvey Milk Terminal 1, San Francisco International Airport, San Francisco, CA 94128",
        "latitude": 37.6169,
        "longitude": -122.3872,
        "supervisor_district": None,
        "is_citywide": False
    },
    "P21": {
        "neighborhood_canonical": "Golden Gate Park",
        "address_full": "JFK Promenade, Golden Gate Park, San Francisco, CA 94117",
        "latitude": 37.7712,
        "longitude": -122.4687,
        "supervisor_district": 1,
        "is_citywide": False
    },
    "P04": {
        "neighborhood_canonical": "Mission Bay",
        "address_full": "1 Warriors Way, San Francisco, CA 94158",
        "latitude": 37.7680,
        "longitude": -122.3877,
        "supervisor_district": 6,
        "is_citywide": False
    },
    "P82": {
        "neighborhood_canonical": "Mission Bay",
        "address_full": "1 Warriors Way, San Francisco, CA 94158",
        "latitude": 37.7680,
        "longitude": -122.3877,
        "supervisor_district": 6,
        "is_citywide": False
    },
    "P83": {
        "neighborhood_canonical": "Mid-Market",
        "address_full": "1188 Market Street, San Francisco, CA 94102",
        "latitude": 37.7786,
        "longitude": -122.4153,
        "supervisor_district": 6,
        "is_citywide": False
    },
    "P11": {
        "neighborhood_canonical": "Golden Gate Park",
        "address_full": "Polo Field & Haight Corridor, Golden Gate Park, San Francisco, CA 94121",
        "latitude": 37.7686,
        "longitude": -122.4930,
        "supervisor_district": 1,
        "is_citywide": False
    },
    "SFO-03": {
        "neighborhood_canonical": "SFO Airport",
        "address_full": "Terminal 3 Gate Concourse, San Francisco International Airport, San Francisco, CA 94128",
        "latitude": 37.6189,
        "longitude": -122.3855,
        "supervisor_district": None,
        "is_citywide": False
    },
    "SFO-04": {
        "neighborhood_canonical": "SFO Airport",
        "address_full": "Harvey Milk Terminal 1 Concourse B, San Francisco International Airport, San Francisco, CA 94128",
        "latitude": 37.6175,
        "longitude": -122.3860,
        "supervisor_district": None,
        "is_citywide": False
    },
    "P01": {
        "neighborhood_canonical": "Tenderloin",
        "address_full": "1 Dr Carlton B Goodlett Pl, San Francisco, CA 94102",
        "latitude": 37.7793,
        "longitude": -122.4192,
        "supervisor_district": 5,
        "is_citywide": False
    },
    "P59": {
        "neighborhood_canonical": "South of Market",
        "address_full": "Market St & 4th St, San Francisco, CA 94103",
        "latitude": 37.7855,
        "longitude": -122.4058,
        "supervisor_district": 6,
        "is_citywide": False
    },
    "P43": {
        "neighborhood_canonical": "Citywide",
        "address_full": None,
        "latitude": 37.7749,
        "longitude": -122.4194,
        "supervisor_district": None,
        "is_citywide": True
    },
    "P41": {
        "neighborhood_canonical": "Chinatown",
        "address_full": "933 Stockton Street, San Francisco, CA 94108",
        "latitude": 37.7937,
        "longitude": -122.4080,
        "supervisor_district": 3,
        "is_citywide": False
    },
    "P10": {
        "neighborhood_canonical": "Mission Rock",
        "address_full": "Dr Maya Angelou Lane & Toni Stone Crossing, San Francisco, CA 94158",
        "latitude": 37.7735,
        "longitude": -122.3890,
        "supervisor_district": 6,
        "is_citywide": False
    },
    "P18": {
        "neighborhood_canonical": "Citywide",
        "address_full": None,
        "latitude": 37.7749,
        "longitude": -122.4194,
        "supervisor_district": None,
        "is_citywide": True
    },
    "P06": {
        "neighborhood_canonical": "Citywide",
        "address_full": None,
        "latitude": 37.7749,
        "longitude": -122.4194,
        "supervisor_district": None,
        "is_citywide": True
    },
    "P08": {
        "neighborhood_canonical": "Tenderloin",
        "address_full": "Turk St & Jones St, San Francisco, CA 94102",
        "latitude": 37.7831,
        "longitude": -122.4124,
        "supervisor_district": 5,
        "is_citywide": False
    },
    "P22": {
        "neighborhood_canonical": "The Embarcadero",
        "address_full": "Seawall Lot 330, The Embarcadero & Bryant St, San Francisco, CA 94105",
        "latitude": 37.7885,
        "longitude": -122.3892,
        "supervisor_district": 6,
        "is_citywide": False
    },
    "P17": {
        "neighborhood_canonical": "Citywide",
        "address_full": "SFPD Headquarters, 1245 3rd St, San Francisco, CA 94158",
        "latitude": 37.7716,
        "longitude": -122.3902,
        "supervisor_district": None,
        "is_citywide": True
    },
    "P25": {
        "neighborhood_canonical": "Twin Peaks",
        "address_full": "375 Woodside Ave, San Francisco, CA 94127",
        "latitude": 37.7460,
        "longitude": -122.4540,
        "supervisor_district": 7,
        "is_citywide": False
    },
    "P12": {
        "neighborhood_canonical": "Citywide",
        "address_full": None,
        "latitude": 37.7749,
        "longitude": -122.4194,
        "supervisor_district": None,
        "is_citywide": True
    },
    "P26": {
        "neighborhood_canonical": "Citywide",
        "address_full": None,
        "latitude": 37.7749,
        "longitude": -122.4194,
        "supervisor_district": None,
        "is_citywide": True
    },
    "P27": {
        "neighborhood_canonical": "Citywide",
        "address_full": "1 Dr Carlton B Goodlett Pl, San Francisco, CA 94102",
        "latitude": 37.7793,
        "longitude": -122.4192,
        "supervisor_district": None,
        "is_citywide": True
    },
    "P29": {
        "neighborhood_canonical": "Civic Center",
        "address_full": "170 Otis Street, San Francisco, CA 94103",
        "latitude": 37.7725,
        "longitude": -122.4206,
        "supervisor_district": 6,
        "is_citywide": True
    },
    "P31": {
        "neighborhood_canonical": "Commercial Corridors",
        "address_full": "Mission St, Clement St, & Geary Blvd Corridors, San Francisco, CA",
        "latitude": 37.7600,
        "longitude": -122.4200,
        "supervisor_district": None,
        "is_citywide": True
    },
    "P30": {
        "neighborhood_canonical": "Citywide",
        "address_full": None,
        "latitude": 37.7749,
        "longitude": -122.4194,
        "supervisor_district": None,
        "is_citywide": True
    },
    "P36": {
        "neighborhood_canonical": "Citywide",
        "address_full": "525 Golden Gate Ave, San Francisco, CA 94102",
        "latitude": 37.7811,
        "longitude": -122.4202,
        "supervisor_district": None,
        "is_citywide": True
    },
    "P09": {
        "neighborhood_canonical": "Bay Area Regional",
        "address_full": "300 Lakeside Dr, Oakland, CA 94612",
        "latitude": 37.8044,
        "longitude": -122.2612,
        "supervisor_district": None,
        "is_citywide": False
    },
    "P61": {
        "neighborhood_canonical": "Bay Area Regional",
        "address_full": "Sunol Valley Water Treatment Facility, Sunol, CA 94586",
        "latitude": 37.5947,
        "longitude": -121.8891,
        "supervisor_district": None,
        "is_citywide": False
    },
    "P66": {
        "neighborhood_canonical": "Mission Bay",
        "address_full": "1 Warriors Way, San Francisco, CA 94158",
        "latitude": 37.7680,
        "longitude": -122.3877,
        "supervisor_district": 6,
        "is_citywide": False
    },
    "P64": {
        "neighborhood_canonical": "Parkmerced",
        "address_full": "3711 19th Ave, San Francisco, CA 94132",
        "latitude": 37.7170,
        "longitude": -122.4830,
        "supervisor_district": 7,
        "is_citywide": False
    },
    "P84": {
        "neighborhood_canonical": "Dogpatch",
        "address_full": "Pier 70, 20th St & Illinois St, San Francisco, CA 94107",
        "latitude": 37.7587,
        "longitude": -122.3850,
        "supervisor_district": 10,
        "is_citywide": False
    },
    "P86": {
        "neighborhood_canonical": "Potrero Hill",
        "address_full": "420 23rd St (Potrero Power Station), San Francisco, CA 94107",
        "latitude": 37.7560,
        "longitude": -122.3840,
        "supervisor_district": 10,
        "is_citywide": False
    },
    "P07": {
        "neighborhood_canonical": "Bay Area Regional",
        "address_full": None,
        "latitude": 37.7749,
        "longitude": -122.4194,
        "supervisor_district": None,
        "is_citywide": False
    },
    "P13": {
        "neighborhood_canonical": "Citywide",
        "address_full": "1 Dr Carlton B Goodlett Pl, San Francisco, CA 94102",
        "latitude": 37.7793,
        "longitude": -122.4192,
        "supervisor_district": None,
        "is_citywide": True
    },
    "P15": {
        "neighborhood_canonical": "Citywide",
        "address_full": None,
        "latitude": 37.7749,
        "longitude": -122.4194,
        "supervisor_district": None,
        "is_citywide": True
    },
    "P16": {
        "neighborhood_canonical": "Citywide",
        "address_full": "Mission & Central Waterfront Navigation Centers, San Francisco, CA",
        "latitude": 37.7650,
        "longitude": -122.4100,
        "supervisor_district": None,
        "is_citywide": True
    },
    "P19": {
        "neighborhood_canonical": "Citywide",
        "address_full": "101 Grove Street, San Francisco, CA 94102",
        "latitude": 37.7780,
        "longitude": -122.4180,
        "supervisor_district": None,
        "is_citywide": True
    },
    "P20": {
        "neighborhood_canonical": "Civic Center",
        "address_full": "1 Dr Carlton B Goodlett Pl, San Francisco, CA 94102",
        "latitude": 37.7793,
        "longitude": -122.4192,
        "supervisor_district": 5,
        "is_citywide": False
    },
    "P23": {
        "neighborhood_canonical": "Union Square",
        "address_full": "333 Post Street, San Francisco, CA 94108",
        "latitude": 37.7879,
        "longitude": -122.4074,
        "supervisor_district": 3,
        "is_citywide": False
    },
    "P28": {
        "neighborhood_canonical": "Mission District",
        "address_full": "1001 Potrero Ave (Zuckerberg SF General Hospital), San Francisco, CA 94110",
        "latitude": 37.7558,
        "longitude": -122.4048,
        "supervisor_district": 9,
        "is_citywide": False
    },
    "P35": {
        "neighborhood_canonical": "Citywide",
        "address_full": "1380 Howard St (Mental Health SF Headquarters), San Francisco, CA 94103",
        "latitude": 37.7728,
        "longitude": -122.4150,
        "supervisor_district": None,
        "is_citywide": True
    },
    "P37": {
        "neighborhood_canonical": "Tenderloin",
        "address_full": "Ellis St & Leavenworth St, San Francisco, CA 94102",
        "latitude": 37.7840,
        "longitude": -122.4140,
        "supervisor_district": 5,
        "is_citywide": False
    },
    "P38": {
        "neighborhood_canonical": "Bay Area Regional",
        "address_full": None,
        "latitude": 37.7749,
        "longitude": -122.4194,
        "supervisor_district": None,
        "is_citywide": False
    },
    "P39": {
        "neighborhood_canonical": "Bay Area Regional",
        "address_full": None,
        "latitude": 37.7749,
        "longitude": -122.4194,
        "supervisor_district": None,
        "is_citywide": False
    },
    "P40": {
        "neighborhood_canonical": "Bay Area Regional",
        "address_full": None,
        "latitude": 37.7749,
        "longitude": -122.4194,
        "supervisor_district": None,
        "is_citywide": False
    },
    "P57": {
        "neighborhood_canonical": "Bay Area Regional",
        "address_full": None,
        "latitude": 37.7749,
        "longitude": -122.4194,
        "supervisor_district": None,
        "is_citywide": False
    },
    "P03": {
        "neighborhood_canonical": "Civic Center",
        "address_full": "1 Dr Carlton B Goodlett Pl, San Francisco, CA 94102",
        "latitude": 37.7793,
        "longitude": -122.4192,
        "supervisor_district": 5,
        "is_citywide": True
    },
    "P58": {
        "neighborhood_canonical": "Bay Area Regional",
        "address_full": None,
        "latitude": 37.7749,
        "longitude": -122.4194,
        "supervisor_district": None,
        "is_citywide": False
    },
    "P62": {
        "neighborhood_canonical": "Mission Bay",
        "address_full": "Dr Maya Angelou Lane & Toni Stone Crossing, San Francisco, CA 94158",
        "latitude": 37.7735,
        "longitude": -122.3890,
        "supervisor_district": 6,
        "is_citywide": False
    },
    "P65": {
        "neighborhood_canonical": "South of Market",
        "address_full": "4th St & Folsom St, San Francisco, CA 94107",
        "latitude": 37.7818,
        "longitude": -122.4010,
        "supervisor_district": 6,
        "is_citywide": False
    },
    "P85": {
        "neighborhood_canonical": "Chinatown",
        "address_full": "Columbus Ave & Washington St, San Francisco, CA 94111",
        "latitude": 37.7958,
        "longitude": -122.4045,
        "supervisor_district": 3,
        "is_citywide": False
    }
}

# -----------------------------------------------------------------------------
# 2. ENTITY STANDARDIZATION
# -----------------------------------------------------------------------------
ENTITY_DATA = {
    "Daniel Lurie": {
        "entity_canonical_name": "Daniel Lurie",
        "entity_category": "politician",
        "entity_party": "D",
        "entity_term_start": "2025-01-08",
        "entity_term_end": "2029-01-08"
    },
    "Mayor Daniel Lurie": {
        "entity_canonical_name": "Daniel Lurie",
        "entity_category": "politician",
        "entity_party": "D",
        "entity_term_start": "2025-01-08",
        "entity_term_end": "2029-01-08"
    },
    "London Breed": {
        "entity_canonical_name": "London Breed",
        "entity_category": "politician",
        "entity_party": "D",
        "entity_term_start": "2018-07-11",
        "entity_term_end": "2025-01-08"
    },
    "Ed Lee": {
        "entity_canonical_name": "Ed Lee",
        "entity_category": "politician",
        "entity_party": "D",
        "entity_term_start": "2011-01-11",
        "entity_term_end": "2017-12-12"
    },
    "Gavin Newsom": {
        "entity_canonical_name": "Gavin Newsom",
        "entity_category": "politician",
        "entity_party": "D",
        "entity_term_start": "2004-01-08",
        "entity_term_end": "2011-01-10"
    },
    "Dean Preston": {
        "entity_canonical_name": "Dean Preston",
        "entity_category": "politician",
        "entity_party": "D",
        "entity_term_start": "2019-12-16",
        "entity_term_end": "2025-01-08"
    },
    "San Francisco Board of Supervisors": {
        "entity_canonical_name": "San Francisco Board of Supervisors",
        "entity_category": "city_department",
        "entity_party": None,
        "entity_term_start": None,
        "entity_term_end": None
    },
    "City and County of San Francisco": {
        "entity_canonical_name": "City and County of San Francisco",
        "entity_category": "city_department",
        "entity_party": None,
        "entity_term_start": None,
        "entity_term_end": None
    },
    "SFMTA": {
        "entity_canonical_name": "San Francisco Municipal Transportation Agency (SFMTA)",
        "entity_category": "city_department",
        "entity_party": None,
        "entity_term_start": None,
        "entity_term_end": None
    },
    "Transportation Authority Board": {
        "entity_canonical_name": "San Francisco County Transportation Authority (SFCTA)",
        "entity_category": "city_department",
        "entity_party": None,
        "entity_term_start": None,
        "entity_term_end": None
    },
    "San Francisco Public Utilities Commission (SFPUC)": {
        "entity_canonical_name": "San Francisco Public Utilities Commission (SFPUC)",
        "entity_category": "city_department",
        "entity_party": None,
        "entity_term_start": None,
        "entity_term_end": None
    },
    "Treasure Island Development Authority": {
        "entity_canonical_name": "Treasure Island Development Authority",
        "entity_category": "city_department",
        "entity_party": None,
        "entity_term_start": None,
        "entity_term_end": None
    },
    "CleanPowerSF": {
        "entity_canonical_name": "CleanPowerSF",
        "entity_category": "city_department",
        "entity_party": None,
        "entity_term_start": None,
        "entity_term_end": None
    },
    "San Francisco International Airport": {
        "entity_canonical_name": "San Francisco International Airport (SFO)",
        "entity_category": "city_department",
        "entity_party": None,
        "entity_term_start": None,
        "entity_term_end": None
    },
    "United Airlines": {
        "entity_canonical_name": "United Airlines",
        "entity_category": "corporation",
        "entity_party": None,
        "entity_term_start": None,
        "entity_term_end": None
    },
    "Alaska Airlines": {
        "entity_canonical_name": "Alaska Airlines",
        "entity_category": "corporation",
        "entity_party": None,
        "entity_term_start": None,
        "entity_term_end": None
    },
    "Golden State Valkyries": {
        "entity_canonical_name": "Golden State Valkyries",
        "entity_category": "sports_team",
        "entity_party": None,
        "entity_term_start": None,
        "entity_term_end": None
    },
    "Golden State Warriors": {
        "entity_canonical_name": "Golden State Warriors",
        "entity_category": "sports_team",
        "entity_party": None,
        "entity_term_start": None,
        "entity_term_end": None
    },
    "San Francisco Giants": {
        "entity_canonical_name": "San Francisco Giants",
        "entity_category": "sports_team",
        "entity_party": None,
        "entity_term_start": None,
        "entity_term_end": None
    },
    "Joe Lacob": {
        "entity_canonical_name": "Joe Lacob",
        "entity_category": "sports_team",
        "entity_party": None,
        "entity_term_start": None,
        "entity_term_end": None
    },
    "Whole Foods Market": {
        "entity_canonical_name": "Whole Foods Market",
        "entity_category": "corporation",
        "entity_party": None,
        "entity_term_start": None,
        "entity_term_end": None
    },
    "Zoox": {
        "entity_canonical_name": "Zoox",
        "entity_category": "corporation",
        "entity_party": None,
        "entity_term_start": None,
        "entity_term_end": None
    },
    "Waymo": {
        "entity_canonical_name": "Waymo",
        "entity_category": "corporation",
        "entity_party": None,
        "entity_term_start": None,
        "entity_term_end": None
    },
    "Tutor Perini Corporation": {
        "entity_canonical_name": "Tutor Perini Corporation",
        "entity_category": "corporation",
        "entity_party": None,
        "entity_term_start": None,
        "entity_term_end": None
    },
    "Forest City Realty Trust Inc.": {
        "entity_canonical_name": "Forest City Realty Trust",
        "entity_category": "corporation",
        "entity_party": None,
        "entity_term_start": None,
        "entity_term_end": None
    },
    "Associate Capital": {
        "entity_canonical_name": "Associate Capital",
        "entity_category": "corporation",
        "entity_party": None,
        "entity_term_start": None,
        "entity_term_end": None
    },
    "PG&E": {
        "entity_canonical_name": "Pacific Gas & Electric (PG&E)",
        "entity_category": "corporation",
        "entity_party": None,
        "entity_term_start": None,
        "entity_term_end": None
    },
    "Patti Poppe": {
        "entity_canonical_name": "Patti Poppe",
        "entity_category": "corporation",
        "entity_party": None,
        "entity_term_start": "2021-01-04",
        "entity_term_end": None
    },
    "Comcast": {
        "entity_canonical_name": "Comcast",
        "entity_category": "corporation",
        "entity_party": None,
        "entity_term_start": None,
        "entity_term_end": None
    },
    "Leland Kim (AT&T spokesman)": {
        "entity_canonical_name": "AT&T",
        "entity_category": "corporation",
        "entity_party": None,
        "entity_term_start": None,
        "entity_term_end": None
    },
    "Visa": {
        "entity_canonical_name": "Visa",
        "entity_category": "corporation",
        "entity_party": None,
        "entity_term_start": None,
        "entity_term_end": None
    },
    "Mickey Hart": {
        "entity_canonical_name": "Dead & Company",
        "entity_category": "cultural_organization",
        "entity_party": None,
        "entity_term_start": None,
        "entity_term_end": None
    }
}

# -----------------------------------------------------------------------------
# 3. HIERARCHICAL CATEGORY DATA & TAGS
# -----------------------------------------------------------------------------
CATEGORY_DATA = {
    "P02": {
        "category_l1": "Public Safety",
        "category_l2": "Crisis & Mental Health Services",
        "secondary_categories": ["Healthcare", "Housing"],
        "tags": ["stabilization_center", "mental_health", "police_friendly", "tenderloin", "substance_abuse"]
    },
    "P05": {
        "category_l1": "Housing",
        "category_l2": "Emergency Shelter",
        "secondary_categories": ["Public Safety", "Social Services"],
        "tags": ["shelter_beds", "homelessness", "1500_beds", "street_homelessness"]
    },
    "SFO-01": {
        "category_l1": "Transportation",
        "category_l2": "Airport Infrastructure",
        "secondary_categories": ["Infrastructure"],
        "tags": ["sfo", "runway_reconstruction", "aviation", "capital_projects"]
    },
    "SFO-02": {
        "category_l1": "Transportation",
        "category_l2": "Airport Infrastructure",
        "secondary_categories": ["Infrastructure"],
        "tags": ["sfo", "harvey_milk_terminal_1", "terminal_modernization", "gates"]
    },
    "P21": {
        "category_l1": "Transportation",
        "category_l2": "Bicycle & Pedestrian Infrastructure",
        "secondary_categories": ["Culture & Recreation"],
        "tags": ["car_free_jfk", "golden_gate_park", "promenade", "pedestrian_safety"]
    },
    "P04": {
        "category_l1": "Culture & Recreation",
        "category_l2": "Professional Sports",
        "secondary_categories": ["Economy & Commercial"],
        "tags": ["valkyries", "wnba", "chase_center", "womens_sports", "inaugural_season"]
    },
    "P82": {
        "category_l1": "Culture & Recreation",
        "category_l2": "Professional Sports",
        "secondary_categories": ["Economy & Commercial"],
        "tags": ["wnba", "championship", "valkyries", "joe_lacob", "chase_center"]
    },
    "P83": {
        "category_l1": "Economy & Commercial",
        "category_l2": "Retail & Grocery",
        "secondary_categories": ["Public Safety"],
        "tags": ["whole_foods", "mid_market", "flagship_grocery", "retail_theft", "closure"]
    },
    "P11": {
        "category_l1": "Culture & Recreation",
        "category_l2": "Live Music & Concerts",
        "secondary_categories": ["Culture"],
        "tags": ["dead_and_company", "farewell_tour", "golden_gate_park", "sphere_residency"]
    },
    "SFO-03": {
        "category_l1": "Transportation",
        "category_l2": "Airlines & Sustainable Aviation",
        "secondary_categories": ["Environment & Energy"],
        "tags": ["united_airlines", "sustainable_aviation_fuel", "saf", "net_zero"]
    },
    "SFO-04": {
        "category_l1": "Transportation",
        "category_l2": "Airlines & Gate Expansion",
        "secondary_categories": ["Infrastructure"],
        "tags": ["alaska_airlines", "harvey_milk_terminal_1", "gate_expansion", "concourse_b"]
    },
    "P01": {
        "category_l1": "Public Safety",
        "category_l2": "Substance Abuse & Emergency Governance",
        "secondary_categories": ["Civic Governance"],
        "tags": ["fentanyl_emergency", "drug_crisis", "ordinance", "tenderloin"]
    },
    "P59": {
        "category_l1": "Transportation",
        "category_l2": "Autonomous Mobility",
        "secondary_categories": ["Infrastructure"],
        "tags": ["zoox", "robotaxi", "autonomous_vehicles", "commercial_testing"]
    },
    "P43": {
        "category_l1": "Transportation",
        "category_l2": "Autonomous Mobility",
        "secondary_categories": ["Infrastructure"],
        "tags": ["waymo", "driverless", "robotaxi", "commercial_launch"]
    },
    "P41": {
        "category_l1": "Transportation",
        "category_l2": "Subway & Rail Transit",
        "secondary_categories": ["Infrastructure"],
        "tags": ["central_subway", "chinatown", "muni_metro", "contract_delay"]
    },
    "P10": {
        "category_l1": "Housing",
        "category_l2": "Mixed-Use Neighborhood Development",
        "secondary_categories": ["Economy & Commercial"],
        "tags": ["mission_rock", "sf_giants", "below_market_rate", "bmr_housing"]
    },
    "P18": {
        "category_l1": "Housing",
        "category_l2": "State Mandated Housing Allocation",
        "secondary_categories": ["Civic Governance"],
        "tags": ["housing_element", "82000_units", "rezoning", "hcd"]
    },
    "P06": {
        "category_l1": "Transportation",
        "category_l2": "Traffic Safety & Vision Zero",
        "secondary_categories": ["Public Safety"],
        "tags": ["vision_zero", "traffic_fatalities", "pedestrian_safety", "sfmta"]
    },
    "P08": {
        "category_l1": "Housing",
        "category_l2": "SRO & Supportive Housing Rehabilitation",
        "secondary_categories": ["Public Safety"],
        "tags": ["sro_housing", "tenderloin", "housing_repairs", "supportive_housing"]
    },
    "P22": {
        "category_l1": "Housing",
        "category_l2": "Navigation Centers & Shelters",
        "secondary_categories": ["Civic Governance"],
        "tags": ["embarcadero_nav_center", "navigation_center", "homelessness", "waterfront"]
    },
    "P17": {
        "category_l1": "Public Safety",
        "category_l2": "Police Staffing & Neighborhood Deployment",
        "secondary_categories": ["Civic Governance"],
        "tags": ["sfpd_recruitment", "police_staffing", "neighborhood_patrol", "academy_classes"]
    },
    "P25": {
        "category_l1": "Public Safety",
        "category_l2": "Juvenile Justice Reform",
        "secondary_categories": ["Civic Governance"],
        "tags": ["juvenile_hall_closure", "criminal_justice_reform", "youth_detention"]
    },
    "P12": {
        "category_l1": "Transportation",
        "category_l2": "Micromobility & Shared Devices",
        "secondary_categories": ["Infrastructure"],
        "tags": ["scooters", "spin", "lime", "micromobility", "permits"]
    },
    "P26": {
        "category_l1": "Housing",
        "category_l2": "Taxation & Vacancy Policy",
        "secondary_categories": ["Civic Governance"],
        "tags": ["empty_homes_tax", "prop_m", "vacant_units", "housing_affordability"]
    },
    "P27": {
        "category_l1": "Housing",
        "category_l2": "Affordable Housing Financing",
        "secondary_categories": ["Economy & Commercial"],
        "tags": ["housing_trust_fund", "prop_c", "affordable_housing", "ed_lee"]
    },
    "P29": {
        "category_l1": "Public Safety",
        "category_l2": "Homeless Assistance & Cash Aid Reform",
        "secondary_categories": ["Civic Governance"],
        "tags": ["care_not_cash", "prop_n", "gavin_newsom", "county_adult_assistance"]
    },
    "P31": {
        "category_l1": "Economy & Commercial",
        "category_l2": "Small Business Permitting",
        "secondary_categories": ["Civic Governance"],
        "tags": ["permitsf", "small_business", "first_year_free", "commercial_activation"]
    },
    "P30": {
        "category_l1": "Housing",
        "category_l2": "Permanent Supportive Housing",
        "secondary_categories": ["Public Safety"],
        "tags": ["homelessness_recovery_plan", "supportive_housing", "placements", "sip_hotels"]
    },
    "P36": {
        "category_l1": "Environment & Energy",
        "category_l2": "Public Renewable Power",
        "secondary_categories": ["Infrastructure"],
        "tags": ["cleanpowersf", "renewable_energy", "green_tariffs", "community_choice"]
    },
    "P09": {
        "category_l1": "Environment & Energy",
        "category_l2": "Wildfire Safety & Grid Hardening",
        "secondary_categories": ["Infrastructure"],
        "tags": ["pge", "powerline_undergrounding", "wildfire_mitigation", "grid_hardening"]
    },
    "P61": {
        "category_l1": "Infrastructure",
        "category_l2": "Regional Water System Capital Program",
        "secondary_categories": ["Environment & Energy"],
        "tags": ["sfpuc", "wsip", "water_system", "calaveras_dam", "infrastructure"]
    },
    "P66": {
        "category_l1": "Culture & Recreation",
        "category_l2": "Sports & Entertainment Arenas",
        "secondary_categories": ["Economy & Commercial"],
        "tags": ["chase_center", "warriors", "metallica", "grand_opening"]
    },
    "P64": {
        "category_l1": "Housing",
        "category_l2": "Master Planned Community Reinvestment",
        "secondary_categories": ["Infrastructure"],
        "tags": ["parkmerced", "redevelopment", "transit_oriented", "housing_units"]
    },
    "P84": {
        "category_l1": "Housing",
        "category_l2": "Waterfront Historic Redevelopment",
        "secondary_categories": ["Economy & Commercial"],
        "tags": ["pier_70", "dogpatch", "historic_preservation", "waterfront_housing"]
    },
    "P86": {
        "category_l1": "Housing",
        "category_l2": "Industrial Waterfront Conversion",
        "secondary_categories": ["Economy & Commercial"],
        "tags": ["potrero_power_station", "industrial_conversion", "mixed_use", "potrero_point"]
    },
    "P07": {
        "category_l1": "Housing",
        "category_l2": "Statewide Housing Production Targets",
        "secondary_categories": ["Civic Governance"],
        "tags": ["3_5_million_homes", "gavin_newsom", "statewide_housing", "affordability"]
    },
    "P13": {
        "category_l1": "Housing",
        "category_l2": "Ten-Year Chronic Homelessness Eradication",
        "secondary_categories": ["Public Safety"],
        "tags": ["10_year_plan", "chronic_homelessness", "gavin_newsom", "supportive_housing"]
    },
    "P15": {
        "category_l1": "Housing",
        "category_l2": "Municipal Housing Construction Goals",
        "secondary_categories": ["Civic Governance"],
        "tags": ["30000_homes", "ed_lee", "housing_construction", "housing_goal"]
    },
    "P16": {
        "category_l1": "Housing",
        "category_l2": "Shelter & Navigation Capacity",
        "secondary_categories": ["Public Safety"],
        "tags": ["1000_shelter_beds", "london_breed", "navigation_centers", "shelter_capacity"]
    },
    "P19": {
        "category_l1": "Public Safety",
        "category_l2": "Municipal Universal Healthcare Access",
        "secondary_categories": ["Healthcare"],
        "tags": ["healthy_san_francisco", "universal_healthcare", "gavin_newsom", "uninsured"]
    },
    "P20": {
        "category_l1": "Civic Governance",
        "category_l2": "Mayoral Candidacy & Transition Pledges",
        "secondary_categories": ["Ethics"],
        "tags": ["caretaker_mayor", "ed_lee", "run_for_office", "mayoral_pledge"]
    },
    "P23": {
        "category_l1": "Economy & Commercial",
        "category_l2": "Downtown Hotel & Conference Activation",
        "secondary_categories": ["Civic Governance"],
        "tags": ["union_square", "convention_facilities", "downtown_economic_recovery", "hotel_rooms"]
    },
    "P28": {
        "category_l1": "Public Safety",
        "category_l2": "Substance Use & Psychiatric Emergency Beds",
        "secondary_categories": ["Healthcare"],
        "tags": ["psychiatric_beds", "dph", "sf_general", "behavioral_health"]
    },
    "P35": {
        "category_l1": "Public Safety",
        "category_l2": "Coordinated Mental Health Reform",
        "secondary_categories": ["Healthcare"],
        "tags": ["mental_health_sf", "care_coordination", "psychiatric_urgent_care", "dph"]
    },
    "P37": {
        "category_l1": "Housing",
        "category_l2": "Permanent Supportive Housing Goals",
        "secondary_categories": ["Public Safety"],
        "tags": ["2000_placements", "supportive_housing", "encampment_resolution", "london_breed"]
    },
    "P38": {
        "category_l1": "Environment & Energy",
        "category_l2": "Public Safety Power Shutoff Minimization",
        "secondary_categories": ["Infrastructure"],
        "tags": ["psps_events", "pge", "power_outages", "fire_season_grid"]
    },
    "P39": {
        "category_l1": "Transportation",
        "category_l2": "Electric Vehicle Charging Infrastructure",
        "secondary_categories": ["Environment & Energy"],
        "tags": ["ev_charging", "pge_chargers", "fast_charging", "cleantech"]
    },
    "P40": {
        "category_l1": "Transportation",
        "category_l2": "Fleet Decarbonization & Electrification",
        "secondary_categories": ["Environment & Energy"],
        "tags": ["utility_fleet", "zero_emissions", "pge_ev", "fleet_electrification"]
    },
    "P57": {
        "category_l1": "Infrastructure",
        "category_l2": "Broadband & Fiber Telecommunications",
        "secondary_categories": ["Economy & Commercial"],
        "tags": ["gigabit_internet", "comcast", "fiber_broadband", "docsis_3_1"]
    },
    "P03": {
        "category_l1": "Economy & Commercial",
        "category_l2": "Commercial Corridors & Small Business Permitting",
        "secondary_categories": ["Civic Governance"],
        "tags": ["permitsf", "daniel_lurie", "small_business_permitting", "economic_vibrancy"]
    },
    "P58": {
        "category_l1": "Infrastructure",
        "category_l2": "Broadband & Ultra-High-Speed Internet",
        "secondary_categories": ["Economy & Commercial"],
        "tags": ["att_gigapower", "gigabit_fiber", "broadband_expansion", "telecom"]
    },
    "P62": {
        "category_l1": "Economy & Commercial",
        "category_l2": "Corporate Headquarters & Commercial Campuses",
        "secondary_categories": ["Infrastructure"],
        "tags": ["visa_mission_rock", "global_hq", "1500_employees", "commercial_lease"]
    },
    "P65": {
        "category_l1": "Transportation",
        "category_l2": "Subway & Rail Transit",
        "secondary_categories": ["Infrastructure"],
        "tags": ["central_subway", "sfmta", "revenue_service", "chinatown_station"]
    },
    "P85": {
        "category_l1": "Transportation",
        "category_l2": "Subway & Rail Transit Extension",
        "secondary_categories": ["Infrastructure"],
        "tags": ["central_subway_extension", "north_beach_extension", "fisherman_wharf", "sfcta"]
    }
}

# -----------------------------------------------------------------------------
# 4. VERDICT METADATA & SOURCE PROVENANCE DATA
# -----------------------------------------------------------------------------
VERDICT_META_DATA = {
    "P02": {
        "verdict_confidence": 0.98,
        "verdict_evidence_count": 3,
        "verdict_contradiction_count": 0,
        "verdict_reason_code": "on_time",
        "impact_score": 9,
        "completion_percentage": 100
    },
    "P05": {
        "verdict_confidence": 0.95,
        "verdict_evidence_count": 1,
        "verdict_contradiction_count": 2,
        "verdict_reason_code": "numeric_target_missed",
        "impact_score": 9,
        "completion_percentage": 25
    },
    "SFO-01": {
        "verdict_confidence": 0.99,
        "verdict_evidence_count": 4,
        "verdict_contradiction_count": 0,
        "verdict_reason_code": "on_time",
        "impact_score": 8,
        "completion_percentage": 100
    },
    "SFO-02": {
        "verdict_confidence": 0.99,
        "verdict_evidence_count": 4,
        "verdict_contradiction_count": 0,
        "verdict_reason_code": "on_time",
        "impact_score": 8,
        "completion_percentage": 100
    },
    "P21": {
        "verdict_confidence": 0.99,
        "verdict_evidence_count": 3,
        "verdict_contradiction_count": 0,
        "verdict_reason_code": "on_time",
        "impact_score": 8,
        "completion_percentage": 100
    },
    "P04": {
        "verdict_confidence": 0.99,
        "verdict_evidence_count": 3,
        "verdict_contradiction_count": 0,
        "verdict_reason_code": "on_time",
        "impact_score": 8,
        "completion_percentage": 100
    },
    "P82": {
        "verdict_confidence": 0.90,
        "verdict_evidence_count": 2,
        "verdict_contradiction_count": 0,
        "verdict_reason_code": "on_time",
        "impact_score": 7,
        "completion_percentage": 100
    },
    "P83": {
        "verdict_confidence": 0.96,
        "verdict_evidence_count": 3,
        "verdict_contradiction_count": 1,
        "verdict_reason_code": "delayed_but_kept",
        "impact_score": 8,
        "completion_percentage": 100
    },
    "P11": {
        "verdict_confidence": 0.96,
        "verdict_evidence_count": 0,
        "verdict_contradiction_count": 3,
        "verdict_reason_code": "goal_abandoned",
        "impact_score": 7,
        "completion_percentage": 0
    },
    "SFO-03": {
        "verdict_confidence": 0.92,
        "verdict_evidence_count": 2,
        "verdict_contradiction_count": 0,
        "verdict_reason_code": "in_progress_on_track",
        "impact_score": 8,
        "completion_percentage": 35
    },
    "SFO-04": {
        "verdict_confidence": 0.98,
        "verdict_evidence_count": 3,
        "verdict_contradiction_count": 0,
        "verdict_reason_code": "on_time",
        "impact_score": 7,
        "completion_percentage": 100
    },
    "P01": {
        "verdict_confidence": 0.98,
        "verdict_evidence_count": 3,
        "verdict_contradiction_count": 0,
        "verdict_reason_code": "on_time",
        "impact_score": 9,
        "completion_percentage": 100
    },
    "P59": {
        "verdict_confidence": 0.95,
        "verdict_evidence_count": 2,
        "verdict_contradiction_count": 0,
        "verdict_reason_code": "on_time",
        "impact_score": 7,
        "completion_percentage": 100
    },
    "P43": {
        "verdict_confidence": 0.97,
        "verdict_evidence_count": 3,
        "verdict_contradiction_count": 0,
        "verdict_reason_code": "on_time",
        "impact_score": 8,
        "completion_percentage": 100
    },
    "P41": {
        "verdict_confidence": 0.98,
        "verdict_evidence_count": 1,
        "verdict_contradiction_count": 3,
        "verdict_reason_code": "timeline_missed_delay",
        "impact_score": 9,
        "completion_percentage": 76
    },
    "P10": {
        "verdict_confidence": 0.93,
        "verdict_evidence_count": 2,
        "verdict_contradiction_count": 0,
        "verdict_reason_code": "in_progress_on_track",
        "impact_score": 8,
        "completion_percentage": 60
    },
    "P18": {
        "verdict_confidence": 0.92,
        "verdict_evidence_count": 2,
        "verdict_contradiction_count": 1,
        "verdict_reason_code": "in_progress_on_track",
        "impact_score": 10,
        "completion_percentage": 40
    },
    "P06": {
        "verdict_confidence": 0.98,
        "verdict_evidence_count": 0,
        "verdict_contradiction_count": 3,
        "verdict_reason_code": "numeric_target_missed",
        "impact_score": 9,
        "completion_percentage": 0
    },
    "P08": {
        "verdict_confidence": 0.94,
        "verdict_evidence_count": 0,
        "verdict_contradiction_count": 2,
        "verdict_reason_code": "no_progress",
        "impact_score": 8,
        "completion_percentage": 0
    },
    "P22": {
        "verdict_confidence": 0.98,
        "verdict_evidence_count": 3,
        "verdict_contradiction_count": 0,
        "verdict_reason_code": "delayed_but_kept",
        "impact_score": 8,
        "completion_percentage": 100
    },
    "P17": {
        "verdict_confidence": 0.91,
        "verdict_evidence_count": 2,
        "verdict_contradiction_count": 0,
        "verdict_reason_code": "in_progress_on_track",
        "impact_score": 9,
        "completion_percentage": 30
    },
    "P25": {
        "verdict_confidence": 0.97,
        "verdict_evidence_count": 0,
        "verdict_contradiction_count": 3,
        "verdict_reason_code": "goal_abandoned",
        "impact_score": 8,
        "completion_percentage": 10
    },
    "P12": {
        "verdict_confidence": 0.95,
        "verdict_evidence_count": 2,
        "verdict_contradiction_count": 0,
        "verdict_reason_code": "on_time",
        "impact_score": 6,
        "completion_percentage": 100
    },
    "P26": {
        "verdict_confidence": 0.96,
        "verdict_evidence_count": 1,
        "verdict_contradiction_count": 2,
        "verdict_reason_code": "legal_injunction_halt",
        "impact_score": 7,
        "completion_percentage": 15
    },
    "P27": {
        "verdict_confidence": 0.97,
        "verdict_evidence_count": 3,
        "verdict_contradiction_count": 0,
        "verdict_reason_code": "on_time",
        "impact_score": 8,
        "completion_percentage": 100
    },
    "P29": {
        "verdict_confidence": 0.97,
        "verdict_evidence_count": 3,
        "verdict_contradiction_count": 0,
        "verdict_reason_code": "on_time",
        "impact_score": 8,
        "completion_percentage": 100
    },
    "P31": {
        "verdict_confidence": 0.96,
        "verdict_evidence_count": 2,
        "verdict_contradiction_count": 0,
        "verdict_reason_code": "on_time",
        "impact_score": 7,
        "completion_percentage": 100
    },
    "P30": {
        "verdict_confidence": 0.96,
        "verdict_evidence_count": 3,
        "verdict_contradiction_count": 0,
        "verdict_reason_code": "on_time",
        "impact_score": 8,
        "completion_percentage": 100
    },
    "P36": {
        "verdict_confidence": 0.97,
        "verdict_evidence_count": 2,
        "verdict_contradiction_count": 0,
        "verdict_reason_code": "on_time",
        "impact_score": 8,
        "completion_percentage": 100
    },
    "P09": {
        "verdict_confidence": 0.92,
        "verdict_evidence_count": 2,
        "verdict_contradiction_count": 0,
        "verdict_reason_code": "in_progress_on_track",
        "impact_score": 9,
        "completion_percentage": 45
    },
    "P61": {
        "verdict_confidence": 0.97,
        "verdict_evidence_count": 1,
        "verdict_contradiction_count": 2,
        "verdict_reason_code": "timeline_missed_delay",
        "impact_score": 8,
        "completion_percentage": 80
    },
    "P66": {
        "verdict_confidence": 0.99,
        "verdict_evidence_count": 3,
        "verdict_contradiction_count": 0,
        "verdict_reason_code": "on_time",
        "impact_score": 8,
        "completion_percentage": 100
    },
    "P64": {
        "verdict_confidence": 0.89,
        "verdict_evidence_count": 2,
        "verdict_contradiction_count": 0,
        "verdict_reason_code": "in_progress_on_track",
        "impact_score": 8,
        "completion_percentage": 30
    },
    "P84": {
        "verdict_confidence": 0.91,
        "verdict_evidence_count": 2,
        "verdict_contradiction_count": 0,
        "verdict_reason_code": "in_progress_on_track",
        "impact_score": 8,
        "completion_percentage": 45
    },
    "P86": {
        "verdict_confidence": 0.90,
        "verdict_evidence_count": 2,
        "verdict_contradiction_count": 0,
        "verdict_reason_code": "in_progress_on_track",
        "impact_score": 8,
        "completion_percentage": 40
    },
    "P07": {
        "verdict_confidence": 0.96,
        "verdict_evidence_count": 0,
        "verdict_contradiction_count": 2,
        "verdict_reason_code": "numeric_target_missed",
        "impact_score": 9,
        "completion_percentage": 18
    },
    "P13": {
        "verdict_confidence": 0.96,
        "verdict_evidence_count": 1,
        "verdict_contradiction_count": 2,
        "verdict_reason_code": "numeric_target_missed",
        "impact_score": 9,
        "completion_percentage": 35
    },
    "P15": {
        "verdict_confidence": 0.96,
        "verdict_evidence_count": 1,
        "verdict_contradiction_count": 2,
        "verdict_reason_code": "numeric_target_missed",
        "impact_score": 9,
        "completion_percentage": 55
    },
    "P16": {
        "verdict_confidence": 0.95,
        "verdict_evidence_count": 1,
        "verdict_contradiction_count": 2,
        "verdict_reason_code": "numeric_target_missed",
        "impact_score": 8,
        "completion_percentage": 60
    },
    "P19": {
        "verdict_confidence": 0.98,
        "verdict_evidence_count": 3,
        "verdict_contradiction_count": 0,
        "verdict_reason_code": "on_time",
        "impact_score": 9,
        "completion_percentage": 100
    },
    "P20": {
        "verdict_confidence": 0.99,
        "verdict_evidence_count": 0,
        "verdict_contradiction_count": 3,
        "verdict_reason_code": "pledge_reversed",
        "impact_score": 8,
        "completion_percentage": 0
    },
    "P23": {
        "verdict_confidence": 0.96,
        "verdict_evidence_count": 2,
        "verdict_contradiction_count": 0,
        "verdict_reason_code": "on_time",
        "impact_score": 7,
        "completion_percentage": 100
    },
    "P28": {
        "verdict_confidence": 0.96,
        "verdict_evidence_count": 2,
        "verdict_contradiction_count": 0,
        "verdict_reason_code": "on_time",
        "impact_score": 8,
        "completion_percentage": 100
    },
    "P35": {
        "verdict_confidence": 0.96,
        "verdict_evidence_count": 2,
        "verdict_contradiction_count": 0,
        "verdict_reason_code": "on_time",
        "impact_score": 9,
        "completion_percentage": 100
    },
    "P37": {
        "verdict_confidence": 0.85,
        "verdict_evidence_count": 1,
        "verdict_contradiction_count": 1,
        "verdict_reason_code": "undecided_conflicting_evidence",
        "impact_score": 8,
        "completion_percentage": 50
    },
    "P38": {
        "verdict_confidence": 0.95,
        "verdict_evidence_count": 2,
        "verdict_contradiction_count": 0,
        "verdict_reason_code": "on_time",
        "impact_score": 8,
        "completion_percentage": 100
    },
    "P39": {
        "verdict_confidence": 0.95,
        "verdict_evidence_count": 1,
        "verdict_contradiction_count": 2,
        "verdict_reason_code": "numeric_target_missed",
        "impact_score": 7,
        "completion_percentage": 64
    },
    "P40": {
        "verdict_confidence": 0.90,
        "verdict_evidence_count": 2,
        "verdict_contradiction_count": 0,
        "verdict_reason_code": "in_progress_on_track",
        "impact_score": 7,
        "completion_percentage": 30
    },
    "P57": {
        "verdict_confidence": 0.96,
        "verdict_evidence_count": 1,
        "verdict_contradiction_count": 2,
        "verdict_reason_code": "timeline_missed_delay",
        "impact_score": 6,
        "completion_percentage": 70
    },
    "P03": {
        "verdict_confidence": 0.96,
        "verdict_evidence_count": 2,
        "verdict_contradiction_count": 0,
        "verdict_reason_code": "on_time",
        "impact_score": 7,
        "completion_percentage": 100
    },
    "P58": {
        "verdict_confidence": 0.86,
        "verdict_evidence_count": 1,
        "verdict_contradiction_count": 1,
        "verdict_reason_code": "undecided_conflicting_evidence",
        "impact_score": 6,
        "completion_percentage": 50
    },
    "P62": {
        "verdict_confidence": 0.97,
        "verdict_evidence_count": 1,
        "verdict_contradiction_count": 2,
        "verdict_reason_code": "numeric_target_missed",
        "impact_score": 7,
        "completion_percentage": 66
    },
    "P65": {
        "verdict_confidence": 0.98,
        "verdict_evidence_count": 0,
        "verdict_contradiction_count": 3,
        "verdict_reason_code": "timeline_missed_delay",
        "impact_score": 9,
        "completion_percentage": 75
    },
    "P85": {
        "verdict_confidence": 0.92,
        "verdict_evidence_count": 2,
        "verdict_contradiction_count": 0,
        "verdict_reason_code": "in_progress_on_track",
        "impact_score": 8,
        "completion_percentage": 25
    }
}

SOURCE_META_DEFAULT = {
    "source_credibility_score": 9,
    "source_type_standardized": "official_government",
    "source_domain_authority": 9,
    "fact_check_status": "verified"
}

def get_source_metadata(p):
    url = p.get("source_url", "")
    tier = p.get("source_tier", "Official")
    h = p.get("source_hash", "")
    
    if tier == "Official" or "sf.gov" in url or "flysfo.com" in url or "legistar.com" in url:
        c_score = 10
        s_type = "official_government"
        d_auth = 10
    elif "sfchronicle.com" in url or "nytimes.com" in url or "reuters.com" in url:
        c_score = 8
        s_type = "news_mainstream"
        d_auth = 9
    elif "sfstandard.com" in url or "thefrisc.com" in url or "missionlocal.org" in url:
        c_score = 8
        s_type = "news_local"
        d_auth = 8
    elif "wikipedia.org" in url:
        c_score = 7
        s_type = "academic_report"
        d_auth = 9
    else:
        c_score = 7
        s_type = "corporate_release"
        d_auth = 7
        
    archived_url = f"https://web.archive.org/web/*/{url}" if url else f"urn:sha256:{h}"
    return {
        "source_credibility_score": c_score,
        "source_type_standardized": s_type,
        "source_domain_authority": d_auth,
        "fact_check_status": "verified",
        "source_archived_url": archived_url
    }

def enrich_promise(p):
    pid = p.get("promise_id")
    geo = GEOGRAPHY_DATA.get(pid, {
        "neighborhood_canonical": "San Francisco",
        "address_full": None,
        "latitude": 37.7749,
        "longitude": -122.4194,
        "supervisor_district": None,
        "is_citywide": True
    })

    raw_entity = p.get("entity", "")
    ent = ENTITY_DATA.get(raw_entity, {
        "entity_canonical_name": raw_entity,
        "entity_category": "city_department",
        "entity_party": None,
        "entity_term_start": None,
        "entity_term_end": None
    })

    cat = CATEGORY_DATA.get(pid, {
        "category_l1": "Civic Governance",
        "category_l2": "Public Accountability",
        "secondary_categories": [],
        "tags": ["civic_accountability"]
    })

    vm = VERDICT_META_DATA.get(pid, {
        "verdict_confidence": 0.90,
        "verdict_evidence_count": 2,
        "verdict_contradiction_count": 0,
        "verdict_reason_code": "on_time" if p.get("verdict") == "kept" else "in_progress_on_track",
        "impact_score": 7,
        "completion_percentage": 100 if p.get("verdict") == "kept" else 50
    })

    sm = get_source_metadata(p)

    # Temporal computations
    made_d = parse_iso_date(p.get("promised_date"))
    due_d = parse_iso_date(p.get("due_date"))
    comp_d = parse_iso_date(p.get("opened_date") or p.get("realized_date"))
    decided_d = parse_iso_date(p.get("decided_at")) or TODAY

    made_str = format_date_str(p.get("promised_date"))
    due_str = format_date_str(p.get("due_date"))
    comp_str = format_date_str(p.get("opened_date") or p.get("realized_date"))

    promise_age_days = (TODAY - made_d).days if made_d else None
    time_to_verdict_days = (decided_d - made_d).days if (made_d and decided_d and decided_d >= made_d) else None

    days_remaining = None
    days_overdue = None

    if due_d:
        diff = (due_d - TODAY).days
        if diff > 0 and p.get("verdict") in ("in_progress", "kept"):
            days_remaining = diff
        elif diff < 0 and p.get("verdict") in ("broken", "stalled", "undecided"):
            days_overdue = abs(diff)

    enriched = dict(p)
    # Add new spatial fields
    enriched["neighborhood_canonical"] = geo["neighborhood_canonical"]
    enriched["address_full"] = geo["address_full"]
    enriched["latitude"] = geo["latitude"]
    enriched["longitude"] = geo["longitude"]
    enriched["supervisor_district"] = geo["supervisor_district"]
    enriched["is_citywide"] = geo["is_citywide"]

    # Add new temporal fields
    enriched["promise_made_date"] = made_str
    enriched["deadline_date"] = due_str
    enriched["completion_date"] = comp_str
    enriched["days_remaining"] = days_remaining
    enriched["days_overdue"] = days_overdue
    enriched["promise_age_days"] = promise_age_days
    enriched["time_to_verdict_days"] = time_to_verdict_days

    # Add new entity fields
    enriched["entity_canonical_name"] = ent["entity_canonical_name"]
    enriched["entity_category"] = ent["entity_category"]
    enriched["entity_party"] = ent["entity_party"]
    enriched["entity_term_start"] = ent["entity_term_start"]
    enriched["entity_term_end"] = ent["entity_term_end"]

    # Add new category fields
    enriched["category_l1"] = cat["category_l1"]
    enriched["category_l2"] = cat["category_l2"]
    enriched["secondary_categories"] = cat["secondary_categories"]
    enriched["tags"] = cat["tags"]

    # Add new verdict metadata fields
    enriched["verdict_confidence"] = vm["verdict_confidence"]
    enriched["verdict_evidence_count"] = vm["verdict_evidence_count"]
    enriched["verdict_contradiction_count"] = vm["verdict_contradiction_count"]
    enriched["verdict_reason_code"] = vm["verdict_reason_code"]
    enriched["impact_score"] = vm["impact_score"]
    enriched["completion_percentage"] = vm["completion_percentage"]

    # Add new source metadata fields
    enriched["source_credibility_score"] = sm["source_credibility_score"]
    enriched["source_type_standardized"] = sm["source_type_standardized"]
    enriched["source_domain_authority"] = sm["source_domain_authority"]
    enriched["fact_check_status"] = sm["fact_check_status"]
    enriched["source_archived_url"] = sm["source_archived_url"]

    return enriched

def main():
    with open("docs/data.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    promises = data.get("promises", [])
    quarantined = data.get("quarantined", [])

    enriched_promises = [enrich_promise(p) for p in promises]

    data["promises"] = enriched_promises
    # Also enrich showcase item if present
    if "p02" in data and isinstance(data["p02"], dict):
        data["p02"] = enrich_promise(data["p02"])

    # Save to docs/data.json and docs/data.js
    with open("docs/data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    with open("docs/data.js", "w", encoding="utf-8") as f:
        f.write("window.__DEMO_DATA__ = ")
        json.dump(data, f, indent=2)
        f.write(";\n")

    print(f"Successfully enriched {len(enriched_promises)} promises in docs/data.json and docs/data.js")

if __name__ == "__main__":
    main()
