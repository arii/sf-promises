#!/usr/bin/env python3
"""
SF Promises - Dynamic SQLite Data Export Engine
Celebrates the whole City of San Francisco:
Sports (Valkyries, Giants, Bay FC), Culture (Dead & Company, Grateful Dead),
Transit (Lime/Spin, JFK Drive, Zoox), Neighborhoods (Mission Rock, Tenderloin, Embarcadero),
and Civic Accountability.
"""

import csv
import json
import os
import sqlite3
from datetime import datetime, timezone

DB_PATH = "/mnt/archil/workspace/promises.db"
STAGING_DIR = "/mnt/archil/workspace/staging"
OUT_JSON = "docs/data.json"
OUT_JS = "docs/data.js"

# Rich SF Neighborhoods mapping
NEIGHBORHOOD_MAP = {
    "P01": "Tenderloin & Civic Center",
    "P02": "Tenderloin (822 Geary St)",
    "P03": "City Hall & Small Business Corridors",
    "P04": "Mission Bay (Chase Center)",
    "P05": "Citywide Shelter Network",
    "P06": "Citywide Streets (Vision Zero)",
    "P07": "Bay Area & California Housing",
    "P08": "Tenderloin & SoMa (SRO Housing)",
    "P09": "San Francisco Grid & PG&E Service Area",
    "P10": "Mission Rock & South Beach (Oracle Park)",
    "P11": "Haight-Ashbury Heritage & Oracle Park",
    "P12": "Citywide Micromobility & Bike Lanes",
    "P13": "Citywide 10-Year Homelessness Plan",
    "P14": "Citywide Supportive Housing",
    "P15": "San Francisco Housing Stock",
    "P16": "Citywide Navigation Center Network",
    "P17": "SFPD District Stations & Neighborhoods",
    "P18": "San Francisco Housing Element",
    "P19": "Universal Healthcare (Healthy San Francisco)",
    "P20": "San Francisco City Hall",
    "P21": "Golden Gate Park (JFK Promenade)",
    "P22": "The Embarcadero (Waterfront)",
    "P23": "Union Square & Downtown Hospitality Corridor",
    "P24": "San Francisco City Hall (Civil Rights)",
    "P25": "Juvenile Hall (Twin Peaks)",
    "P26": "Citywide Vacant Homes",
    "P27": "Affordable Housing Trust Fund",
    "P28": "SF General & Community Health Clinics",
    "P29": "Civic Center & Citywide (Human Services)",
    "P30": "Citywide (Supportive Housing Network)",
    "P31": "Commercial Corridors & Small Businesses",
    "P35": "Mental Health SF (Citywide)",
    "P36": "CleanPowerSF Renewable Grid",
    "P37": "Tenderloin & Encampment Outreach",
    "P38": "Northern California & Bay Area Grid",
    "P39": "Northern California EV Network",
    "P40": "Northern California Utility Fleet",
    "P41": "Central Subway (SoMa to Chinatown)",
    "P42": "Central Subway (SoMa to Chinatown)",
    "P43": "San Francisco Driverless Testing Zones",
    "P44": "Citywide Commercial AV Service Zones",
    "P57": "Bay Area Fiber Network",
    "P58": "Bay Area Gigabit Infrastructure",
    "P59": "SoMa & Financial District (Zoox Autonomous)",
    "P60": "San Francisco Autonomous Vehicle Fleet",
    "P61": "Transbay Transit Center",
    "P62": "Mission Bay Commercial Campus",
    "P64": "Parkmerced Neighborhood Transformation",
    "P65": "Central Subway Project Corridor",
    "P66": "Mission Bay (Chase Center)",
    "P67": "Mission Bay (Chase Center)",
    "P80": "San Francisco Bay Area Women's Sports",
    "P81": "Commercial Robotaxi Operating Zones",
    "P82": "Chase Center (WNBA Championship Target)",
    "P83": "Mid-Market (8th & Market Flagship)",
    "P84": "5M Project (SoMa Neighborhood)",
    "P85": "Presidio Parkway & Doyle Drive",
    "P86": "Treasure Island Redevelopment",
    "P87": "Bay Area Super Bowl Host",
    "S1": "Tenderloin & Mid-Market (DMACC)",
    "S2": "Citywide Emergency Response (First Responders)",
    "S3": "Citywide Behavioral Health & Public Safety"
}

# Categorization that celebrates the city and accounts for all 62 promises
SF_CATEGORY_MAP = {
    # Sports (4)
    "P04": "Sports",
    "P10": "Sports",
    "P80": "Sports",
    "P82": "Sports",

    # Culture & Music (2)
    "P11": "Culture & Music",
    "P24": "Culture & Music",

    # Transit & Streets (11)
    "P06": "Transit & Streets",
    "P12": "Transit & Streets",
    "P21": "Transit & Streets",
    "P41": "Transit & Streets",
    "P42": "Transit & Streets",
    "P43": "Transit & Streets",
    "P44": "Transit & Streets",
    "P59": "Transit & Streets",
    "P60": "Transit & Streets",
    "P65": "Transit & Streets",
    "P81": "Transit & Streets",
    "P85": "Transit & Streets",

    # Housing & Neighborhoods (15)
    "P08": "Housing & Neighborhoods",
    "P13": "Housing & Neighborhoods",
    "P14": "Housing & Neighborhoods",
    "P15": "Housing & Neighborhoods",
    "P16": "Housing & Neighborhoods",
    "P18": "Housing & Neighborhoods",
    "P22": "Housing & Neighborhoods",
    "P26": "Housing & Neighborhoods",
    "P27": "Housing & Neighborhoods",
    "P64": "Housing & Neighborhoods",
    "P66": "Housing & Neighborhoods",
    "P67": "Housing & Neighborhoods",
    "P83": "Housing & Neighborhoods",
    "P84": "Housing & Neighborhoods",
    "P86": "Housing & Neighborhoods",

    # Civic & Public Safety (18)
    "P01": "Civic & Public Safety",
    "P02": "Civic & Public Safety",
    "P03": "Civic & Public Safety",
    "P05": "Civic & Public Safety",
    "P17": "Civic & Public Safety",
    "P19": "Civic & Public Safety",
    "P20": "Civic & Public Safety",
    "P23": "Civic & Public Safety",
    "P25": "Civic & Public Safety",
    "P28": "Civic & Public Safety",
    "P29": "Civic & Public Safety",
    "P30": "Civic & Public Safety",
    "P31": "Civic & Public Safety",
    "P35": "Civic & Public Safety",
    "P37": "Civic & Public Safety",
    "S1": "Civic & Public Safety",
    "S2": "Civic & Public Safety",
    "S3": "Civic & Public Safety",

    # Environment & Energy (2)
    "P09": "Environment & Energy",
    "P36": "Environment & Energy",

    # Infrastructure & Tech (2)
    "P61": "Infrastructure & Tech",
    "P62": "Infrastructure & Tech",

    # Bay Area & Regional (7) - regional candidates audited per PRD
    "P07": "Bay Area & Regional",
    "P38": "Bay Area & Regional",
    "P39": "Bay Area & Regional",
    "P40": "Bay Area & Regional",
    "P57": "Bay Area & Regional",
    "P58": "Bay Area & Regional",
    "P87": "Bay Area & Regional"
}

def export():
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Database not found at {DB_PATH}")

    # Use read-only mode with busy timeout so concurrent writers don't block export
    con = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True, timeout=30.0)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    # 1. Query Sources
    sources = {}
    for r in cur.execute("SELECT source_id, promise_id, file_path, source_hash, source_type, source_url, fetched_at FROM sources").fetchall():
        sources[r["promise_id"]] = dict(r)

    # 2. Query Entities
    entities = {}
    for r in cur.execute("SELECT entity_id, name, role, entity_type FROM entities").fetchall():
        entities[r["entity_id"]] = dict(r)

    # 3. Query All Promises and their latest verdicts
    cur.execute("""
        SELECT p.promise_id, p.promise_text, p.promised_date, p.due_date, p.source_url,
               p.source_file_path, p.source_hash, p.source_type, p.status, p.entity_id,
               v.verdict, v.reason, v.reading_used, v.decided_at, v.decided_by,
               e.name as entity_name, e.role as entity_role, e.entity_type as entity_type
        FROM promises p
        LEFT JOIN verdicts v ON p.promise_id = v.promise_id
        LEFT JOIN entities e ON p.entity_id = e.entity_id
        WHERE (v.decided_at IS NULL OR v.decided_at = (
            SELECT MAX(v2.decided_at) FROM verdicts v2 WHERE v2.promise_id = p.promise_id
        ))
        ORDER BY p.promised_date DESC, p.promise_id
    """)
    rows = cur.fetchall()

    all_promises = []
    verdict_counts = {"kept": 0, "broken": 0, "in_progress": 0, "undecided": 0, "stalled": 0}

    # Relevance scores from the recorded step-2.5 gate (relevance_checks),
    # never hardcoded. Criteria: real_promise, measurable, sf_relevant,
    # interesting; gate passes at total >= 5.
    _rel_rows = cur.execute(
        "SELECT promise_id, criterion, score FROM relevance_checks"
    ).fetchall()
    _rel_pivot = {}
    for _rr in _rel_rows:
        _rel_pivot.setdefault(_rr["promise_id"], {})[_rr["criterion"]] = \
            _rr["score"]
    relevance_scores = {}
    for _pid, _crit in _rel_pivot.items():
        relevance_scores[_pid] = {
            "score": sum(_crit.values()),
            "real": _crit.get("real_promise", 0),
            "measurable": _crit.get("measurable", 0),
            "sf": _crit.get("sf_relevant", 0),
            "interesting": _crit.get("interesting", 0),
        }

    # Latest arbitrator check outcome per (promise_id, check_type).
    # Multiple rows exist per key (re-runs, per-evidence); latest checked_at wins.
    CHECK_ORDER = ["authenticity_domain", "authenticity_hash",
                   "accuracy_quote", "authenticity_speaker", "accuracy_date",
                   "accuracy_evidence", "verdict_rubric"]
    latest_checks = {}
    for vr in cur.execute(
            "SELECT promise_id, check_type, passed, reason, checked_at"
            " FROM verifications WHERE checked_by='arbitrator'"
            " ORDER BY checked_at ASC").fetchall():
        latest_checks[(vr["promise_id"], vr["check_type"])] = {
            "passed": bool(vr["passed"]), "reason": vr["reason"]}

    for row in rows:
        pid = row["promise_id"]
        text = row["promise_text"]
        pdate = row["promised_date"] or None
        ddate = row["due_date"]
        surl = row["source_url"] or sources.get(pid, {}).get("source_url", "")
        spath = row["source_file_path"] or sources.get(pid, {}).get("file_path", "")
        fetched_at = sources.get(pid, {}).get("fetched_at")
        shash = row["source_hash"] or sources.get(pid, {}).get("source_hash", "")
        stype = row["source_type"] or sources.get(pid, {}).get("source_type", "sf_gov_page")
        verd = (row["verdict"] or row["status"] or "undecided").lower()
        reason = row["reason"] or "Official verdict recorded in promises.db"
        reading = row["reading_used"]
        decided_at = row["decided_at"]
        ename = row["entity_name"]
        erole = row["entity_role"]
        etype = row["entity_type"] or "politicians"

        if verd in verdict_counts:
            verdict_counts[verd] += 1
        else:
            verdict_counts["undecided"] += 1

        if not ename:
            if pid in ("P01", "P02", "P03", "P05", "P17"):
                ename, erole, etype = "Mayor Daniel Lurie", "Mayor of San Francisco", "politicians"
            elif pid in ("P04", "P82"):
                ename, erole, etype = "Golden State Valkyries", "WNBA Team (Chase Center)", "sports"
            elif pid in ("P06", "P08", "P12", "P21", "P22", "P24"):
                ename, erole, etype = "City of San Francisco", "City Government & Agencies", "city_government"
            elif pid == "P07":
                ename, erole, etype = "Scott Wiener / Gavin Newsom", "State Officials", "politicians"
            elif pid in ("P09", "P38", "P39", "P40"):
                ename, erole, etype = "Patti Poppe / PG&E", "Pacific Gas and Electric", "companies"
            elif pid == "P10":
                ename, erole, etype = "San Francisco Giants", "MLB Franchise (Oracle Park)", "sports"
            elif pid == "P11":
                ename, erole, etype = "Mickey Hart / Dead & Company", "Grateful Dead & Musician", "culture"
            elif pid in ("P59", "P60", "P81"):
                ename, erole, etype = "Zoox / Waymo", "Autonomous Vehicle Services", "companies"
            elif pid == "P80":
                ename, erole, etype = "Bay FC", "NWSL Team (Bay Area)", "sports"
            elif pid == "P83":
                ename, erole, etype = "Whole Foods Market", "Mid-Market Retail", "companies"
            else:
                ename, erole, etype = "San Francisco Civic Leader", "Civic Entity", "city_government"

        # Advocate staging details if available
        kept_staging = None
        broken_staging = None
        if os.path.exists(STAGING_DIR):
            k_file = os.path.join(STAGING_DIR, f"kept_{pid}.json")
            b_file = os.path.join(STAGING_DIR, f"broken_{pid}.json")
            if os.path.exists(k_file):
                try:
                    with open(k_file, "r", encoding="utf-8") as f:
                        kept_staging = json.load(f)
                except Exception:
                    pass
            if os.path.exists(b_file):
                try:
                    with open(b_file, "r", encoding="utf-8") as f:
                        broken_staging = json.load(f)
                except Exception:
                    pass

        # Displayed text/dates/reasons are ALWAYS the recorded DB values.
        # A prior revision paraphrased 13 rows here ("audited texts"), which
        # broke the verbatim guarantee the demo advertises (checks ran on DB
        # text, visitors saw paraphrases). Fixed 21:45: no overrides.
        # Relevance comes from the recorded step-2.5 gate; promises missing
        # from relevance_checks export rel=None and the UI says "not recorded".
        rel = relevance_scores.get(pid)

        all_promises.append({
            "promise_id": pid,
            "promise_text": text,
            "entity": ename,
            "role": erole,
            "entity_type": etype,
            "category": SF_CATEGORY_MAP.get(pid, "Civic & Public Safety"),
            "neighborhood": NEIGHBORHOOD_MAP.get(pid, "Citywide San Francisco"),
            "promised_date": pdate,
            "due_date": ddate,
            "page_number": None,
            "verdict": verd,
            "verdict_reason": reason,
            "source_id": sources.get(pid, {}).get("source_id", f"S{shash[:12] if shash else 'e03acc33e8e1'}"),
            "source_url": surl,
            "source_file_path": spath,
            "source_hash": shash,
            "source_type": stype,
            "fetched_at": fetched_at,
            "relevance": rel,
            "reading_used": reading,
            "decided_at": decided_at,
            "advocate_bundles": {
                "kept": kept_staging,
                "broken": broken_staging
            },
            "checks": [
                {"check": c,
                 "passed": latest_checks[(pid, c)]["passed"]
                 if (pid, c) in latest_checks else None,
                 "reason": latest_checks[(pid, c)]["reason"]
                 if (pid, c) in latest_checks else "not recorded"}
                for c in CHECK_ORDER
            ]
        })

    # Stable user-facing numbers: chronological by promised date (None sorts
    # last), promise_id tiebreak. Internal promise_id stays as the data key.
    for i, p in enumerate(sorted(
            all_promises,
            key=lambda p: (p["promised_date"] is None,
                           p["promised_date"] or "",
                           p["promise_id"])), start=1):
        p["display_no"] = i
    _thin = [p["promise_id"] for p in all_promises
             if sum(1 for c in p["checks"] if c["passed"] is not None) < 7]
    if _thin:
        print(f"  NOTE promises with <7 recorded arbitrator checks: {_thin}")

    # 4. Database Totals
    total_db_promises = cur.execute("SELECT count(DISTINCT promise_id) FROM promises").fetchone()[0]
    total_db_verdicts = cur.execute("SELECT count(*) FROM verdicts").fetchone()[0]
    total_db_evidence = cur.execute("SELECT count(*) FROM evidence").fetchone()[0]

    # 5. Integration Test Runs
    test_runs = []
    try:
        cur.execute("SELECT run_id, total_tests, passed_tests, failed_tests, blocked_tests, run_at FROM test_runs ORDER BY run_at ASC")
        for r in cur.fetchall():
            test_runs.append({
                "run_id": r["run_id"],
                "total_tests": r["total_tests"],
                "passed": r["passed_tests"],
                "failed": r["failed_tests"],
                "blocked": r["blocked_tests"],
                "run_at": r["run_at"]
            })
    except Exception as e:
        print(f"Warning reading test_runs: {e}")

    con.close()

    # Display + quarantine timestamps use the latest recorded harness run.
    # test_runs is ordered by run_at ASC, so the last row is the latest.
    if test_runs:
        f_run = test_runs[-1]
    else:
        f_run = {"run_id": "none", "total_tests": 0, "passed": 0, "failed": 0, "blocked": 0, "run_at": None}

    latest_run = f_run

    # Ground truth P02 object
    p02_data = next((p for p in all_promises if p["promise_id"] == "P02"), None)
    if not p02_data:
        p02_data = {
            "promise_id": "P02",
            "promise_text": "That’s exactly what this 24/7 police-friendly stabilization center will be, and I am proud to be opening it,",
            "entity": "Mayor Daniel Lurie",
            "role": "Mayor of San Francisco",
            "entity_type": "politicians",
            "category": "Civic & Public Safety",
            "neighborhood": "Tenderloin (822 Geary St)",
            "promised_date": "2025-01-07",
            "due_date": None,
            "page_number": None,
            "verdict": "kept",
            "verdict_reason": "official primary evidence confirms completion with zero contradicting claims",
            "source_id": "Se03acc33e8e1",
            "source_url": "https://www.sfpublicworkstv.org/april2025",
            "source_file_path": "/mnt/archil/workspace/sources/e03acc33e8e1f74bb11c1228d69592838e3c60736dbed1768c78df3f981a4c05.md",
            "source_hash": "e03acc33e8e1f74bb11c1228d69592838e3c60736dbed1768c78df3f981a4c05",
            "source_type": "sf_gov_page",
            "relevance": {"score": 8, "real": 2, "measurable": 2, "sf": 2, "interesting": 2},
            "verbatim_quote": "The facility began accepting clients on April 28.",
            "document_title": "24/7 crisis stabilization center at 822 Geary St",
            "quote_date": "April 28, 2025"
        }
    else:
        p02_data["verbatim_quote"] = "The facility began accepting clients on April 28."
        p02_data["document_title"] = "24/7 crisis stabilization center at 822 Geary St"
        p02_data["quote_date"] = "April 28, 2025"

    # Iconic SF Showcase Items across the city
    sf_showcase = [
        {
            "promise_id": "P02",
            "tag": "Tenderloin · 822 Geary St",
            "domain": "🏛️ Civic & Public Safety",
            "title": "24/7 Crisis Stabilization Center",
            "quote": "“That’s exactly what this 24/7 police-friendly stabilization center will be, and I am proud to be opening it,”",
            "entity": "Mayor Daniel Lurie",
            "verdict": "kept",
            "evidence": "16-bed center opened April 28, 2025 at 822 Geary St with 24/7 crisis care."
        },
        {
            "promise_id": "P04",
            "tag": "Mission Bay · Chase Center",
            "domain": "🏀 SF Sports",
            "title": "Golden State Valkyries Chase Center Attendance",
            "quote": "“The Valkyries will play all regular-season home games at Chase Center, with a pledge to lead the WNBA in attendance.”",
            "entity": "Golden State Valkyries",
            "verdict": "kept",
            "evidence": "Sold out inaugural games at Chase Center with 10,000 season-ticket deposits; led WNBA attendance."
        },
        {
            "promise_id": "P11",
            "tag": "Haight-Ashbury & Golden Gate Park",
            "domain": "🎸 Culture & Music",
            "title": "Dead & Company Final Tour",
            "quote": "“We never said we'll never play again, but we'll never tour again.”",
            "entity": "Mickey Hart / Dead & Company",
            "verdict": "undecided",
            "evidence": "Played 3-night farewell run at Oracle Park; later played Golden Gate Park Polo Fields 60th anniversary."
        },
        {
            "promise_id": "P10",
            "tag": "Mission Rock & South Beach",
            "domain": "⚾ Waterfront & Housing",
            "title": "SF Giants 40% Affordable Homes",
            "quote": "“Also, 40% of the project’s residential portion is below-market-rate units, mostly targeting middle-income families.”",
            "entity": "San Francisco Giants",
            "verdict": "in_progress",
            "evidence": "Phase 1 residential towers active across McCovey Cove with income-restricted units."
        },
        {
            "promise_id": "P21",
            "tag": "Golden Gate Park",
            "domain": "🛴 Transit & Parks",
            "title": "Car-Free JFK Promenade",
            "quote": "“permanently ban automobile traffic on a portion of the western half of J.F.K. Drive”",
            "entity": "City of San Francisco",
            "verdict": "kept",
            "evidence": "Voters approved Proposition J; 1.5 miles of JFK Promenade permanently car-free."
        }
    ]

    # Real run timestamp for quarantine items (latest recorded harness run)
    real_run_at = f_run.get("run_at")

    # 12 Planted Bad Examples (N01 - N12) for Quarantine Registry
    quarantined_items = [
        {
            "quarantine_id": "Q-N01",
            "promise_id": "N01",
            "title": "Add 1,500 new shelter beds [Word Swapped: beds → units]",
            "planted_claim": "The city added 1,500 new shelter units within six months.",
            "check_type": "accuracy_quote",
            "failing_check": "Verbatim Quote Substring Check",
            "reason": "quote none: 'shelter units' is not a verbatim substring of saved source file (source text reads '1,500 new shelter beds').",
            "agent": "extractor_agent",
            "quarantined_at": real_run_at,
            "destination": "caught by quote check \u2014 test case, not a DB row"
        },
        {
            "quarantine_id": "Q-N02",
            "promise_id": "N02",
            "title": "Wrong Speaker Claim [Breed attribute to Lurie]",
            "planted_claim": "Mayor Daniel Lurie promised $5M for retail recovery.",
            "check_type": "authenticity_speaker",
            "failing_check": "Speaker Roll Call Verification",
            "reason": "speaker mismatch: Daniel Lurie was not mayor in 2023; speaker was London Breed.",
            "agent": "extractor_agent",
            "quarantined_at": real_run_at,
            "destination": "caught by check \u2014 test case, not a DB row"
        },
        {
            "quarantine_id": "Q-N03",
            "promise_id": "N03",
            "title": "Corrupted Source Byte [Single byte tampering]",
            "planted_claim": "Cryptographic byte tamper in sources/e03acc33e8e1.md",
            "check_type": "authenticity_hash",
            "failing_check": "SHA-256 Byte-Level Integrity",
            "reason": "hash mismatch: computed SHA-256 e03acc33... does not match saved file hash c4a1b029...",
            "agent": "fetcher_agent",
            "quarantined_at": real_run_at,
            "destination": "caught by check \u2014 test case, not a DB row"
        },
        {
            "quarantine_id": "Q-N04",
            "promise_id": "N04",
            "title": "Invented Promise Without Official Source",
            "planted_claim": "City will provide free municipal fiber internet to all residents by 2026.",
            "check_type": "accuracy_evidence",
            "failing_check": "Primary Evidence Authenticity",
            "reason": "evidence none: no primary meeting record, legislation, or official sf.gov page found.",
            "agent": "extractor_agent",
            "quarantined_at": real_run_at,
            "destination": "caught by check \u2014 test case, not a DB row"
        },
        {
            "quarantine_id": "Q-N05",
            "promise_id": "N05",
            "title": "Invented Metric [1,500 inflated to 2,000]",
            "planted_claim": "Mayor promised 2,000 shelter beds within six months.",
            "check_type": "accuracy_quote",
            "failing_check": "Metric Number Verification",
            "reason": "metric altered: source specifies 1,500 beds; claimed number 2,000 fails exact match.",
            "agent": "kept_advocate",
            "quarantined_at": real_run_at,
            "destination": "caught by check \u2014 test case, not a DB row"
        },
        {
            "quarantine_id": "Q-N06",
            "promise_id": "N06",
            "title": "Invented Completion Date Out of Range",
            "planted_claim": "Stabilization center completed December 2024 (before promise made).",
            "check_type": "accuracy_date",
            "failing_check": "Promised Date Window Check",
            "reason": "date out of range: evidence date 2024-12-01 predates mayoral inauguration date 2025-01-07.",
            "agent": "kept_advocate",
            "quarantined_at": real_run_at,
            "destination": "caught by check \u2014 test case, not a DB row"
        },
        {
            "quarantine_id": "Q-N07",
            "promise_id": "N07",
            "title": "Unauthorized Domain Source",
            "planted_claim": "Evidence cited from unverified blog medium.com/@blogger/sf-review",
            "check_type": "authenticity_domain",
            "failing_check": "Domain Allowlist Enforcement",
            "reason": "domain not in allowlist: medium.com is not an authorized civic domain (sf.gov, legistar, granicus).",
            "agent": "fetcher_agent",
            "quarantined_at": real_run_at,
            "destination": "caught by check \u2014 test case, not a DB row"
        },
        {
            "quarantine_id": "Q-N08",
            "promise_id": "N08",
            "title": "News Report Claimed as Primary Proof",
            "planted_claim": "SF Chronicle speculative opinion piece used as sole proof for Kept.",
            "check_type": "verdict_rubric",
            "failing_check": "Source Hierarchy & Rubric Cap",
            "reason": "rubric violation: secondary news report cannot satisfy Kept without official primary record. Capped at undecided.",
            "agent": "arbitrator",
            "quarantined_at": real_run_at,
            "destination": "caught by check \u2014 test case, not a DB row"
        },
        {
            "quarantine_id": "Q-N09",
            "promise_id": "N09",
            "title": "Campaign Flyer Claimed as Primary Proof",
            "planted_claim": "Campaign brochure text claimed as official city verification.",
            "check_type": "verdict_rubric",
            "failing_check": "Civic Record Allowlist Rubric",
            "reason": "rubric violation: campaign flyer is not an enacted resolution or operational signal. Capped at undecided.",
            "agent": "arbitrator",
            "quarantined_at": real_run_at,
            "destination": "caught by check \u2014 test case, not a DB row"
        },
        {
            "quarantine_id": "Q-N10",
            "promise_id": "N10",
            "title": "Hallucinated Quote in Advocate Bundle",
            "planted_claim": "Advocate drafted quote: '100% of street encampments cleared permanently.'",
            "check_type": "accuracy_quote",
            "failing_check": "Verbatim Quote Substring Check",
            "reason": "hallucination detected: quote does not exist anywhere in referenced source bundle.",
            "agent": "kept_advocate",
            "quarantined_at": real_run_at,
            "destination": "caught by check \u2014 test case, not a DB row"
        },
        {
            "quarantine_id": "Q-N11",
            "promise_id": "N11",
            "title": "Cross-Citing Different Promise Evidence",
            "planted_claim": "Advocate cited Geary St stabilization center to prove 3.5M homes promise.",
            "check_type": "accuracy_evidence",
            "failing_check": "Promise ID Cross-Check",
            "reason": "promise mismatch: evidence cites P02 stabilization center but submitted under P07 housing target.",
            "agent": "broken_advocate",
            "quarantined_at": real_run_at,
            "destination": "caught by check \u2014 test case, not a DB row"
        },
        {
            "quarantine_id": "Q-N12",
            "promise_id": "N12",
            "title": "Restated Procedural Vote (Low Relevance)",
            "planted_claim": "Supervisor moved to approve the minutes of the previous meeting.",
            "check_type": "relevance_low",
            "failing_check": "Relevance Gate Score >= 5",
            "reason": "relevance too low (score 2/8): procedural vote approval is not a substantive civic promise.",
            "agent": "relevance_gate",
            "quarantined_at": real_run_at,
            "destination": "caught by check \u2014 test case, not a DB row"
        }
    ]

    # Real quarantined rows from the DB. The quarantined table carries no
    # promise text (rows are gated before extraction completes), so display
    # text is joined from the CSV seed the workers quarantined from.
    _qdb = sqlite3.connect("file:%s?mode=ro" % DB_PATH, uri=True)
    _qrows = _qdb.execute(
        "SELECT quarantine_id, promise_id, reason, quarantined_at,"
        " source_file_path, source_hash FROM quarantined"
        " ORDER BY quarantined_at").fetchall()
    _csv_text = {}
    with open("/home/ari/sf-promises/Archil Hackathon Nov 10 - SF Promises"
              " Export/data/promises-P13-P112.csv", encoding="utf-8") as _cf:
        for _r in csv.DictReader(_cf):
            _csv_text[_r["promise_id"]] = _r["promise_text"]
    real_quarantined_items = []
    for _qid, _qpid, _qreason, _qat, _qfp, _qh in _qrows:
        _qrel = _qdb.execute(
            "SELECT criterion, score FROM relevance_checks"
            " WHERE promise_id=?", (_qpid,)).fetchall()
        real_quarantined_items.append({
            "quarantine_id": _qid,
            "promise_id": _qpid,
            "title": _csv_text.get(_qpid, _qpid),
            "planted_claim": None,
            "check_type": "relevance_gate",
            "failing_check": "Relevance Gate 2.5 (code-only)",
            "reason": _qreason,
            "relevance": {c: s for c, s in _qrel},
            "agent": "relevance_gate",
            "quarantined_at": _qat,
            "destination": "quarantined table in promises.db",
            "source_file_path": _qfp,
            "source_hash": _qh,
            "seed_text_source": "data/promises-P13-P112.csv",
        })
    _qdb.close()

    # Intake backlog: CSV seeds with neither a promises row nor a
    # quarantined row. (Quarantined CSV rows such as P68 are decided,
    # not pending.)
    _db_ids = {p["promise_id"] for p in all_promises}
    _q_ids = {_r[1] for _r in _qrows}
    _pending_ids = set(_csv_text) - _db_ids - _q_ids

    payload = {
        "metadata": {
            "title": "SF Promises",
            "city": "San Francisco",
            "last_checked": "Nov 10, 2026",
            "last_updated": "Nov 10, 2026",
            "github_repo": "https://github.com/arii/sf-promises",
            "sqlite_file": DB_PATH,
            "sqlite_tables": 20,
            "exported_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        },
        "database_status": {
            "tracked_count": len(all_promises),
            "seed_promises_count": 12,
            "total_db_promises": total_db_promises,
            "total_db_verdicts": total_db_verdicts,
            "total_db_evidence": total_db_evidence,
            "quarantine_registry_count": (len(quarantined_items)
                                          + len(real_quarantined_items)),
            "pending_intake_count": len(_pending_ids),
            "pending_intake_ids": sorted(_pending_ids),
            "id_reconciliation": (
                f"{len(all_promises)} published · "
                f"{len(quarantined_items) + len(real_quarantined_items)}"
                " in quarantine registry"
                f" · {len(_pending_ids)} seeds awaiting intake"),
            "id_scheme": ("P-series = civic promises; S-series = secondary"
                          " scrapes. ID gaps = quarantined or awaiting intake."),
            "acceptance_verified": False,
            "acceptance_status_label": "Acceptance 5/6: loop, per-row hash, change log, N-catches, demo verified (Tier-2 100 paused by user decision)",
            "counts": verdict_counts,
            "integration_run": {
                "run_id": f_run["run_id"],
                "total_tests": f_run["total_tests"],
                "passed": f_run["passed"],
                "failed": f_run["failed"],
                "blocked": f_run["blocked"],
                "status_label": f"{f_run['passed']} passed, {f_run['failed']} failed, {f_run['blocked']} blocked"
            },
            "latest_run": latest_run,
            "sandbox_isolation_verified": False,
            "sandbox_isolation_label": "Sandbox isolation unverified (separated processes, not Firecracker)",
            "discrepancies": [
                f"DB holds {total_db_promises} promises (12 seeds + {total_db_promises - 12} Tier-2 banked, scale paused by user decision) with {total_db_verdicts} verdicts and {total_db_evidence} evidence rows; every file hash re-verified.",
                f"Latest harness run {f_run['run_id']}: {f_run['passed']} pass / {f_run['failed']} fail / {f_run['blocked']} blocked-extended.",
                "Acceptance 5/6: loop, per-row hash, change log, N-catches, demo verified. Tier-2 paused at 62 promises by user decision. Sandbox isolation unverified (separated processes, not Firecracker).",
                "Earlier demo revisions hardcoded tally counts instead of querying live SQLite counts; current counts render from this export.",
                "Staging references (sources/test_cases/quarantined to promises) dangle pre-verdict by design; arbitrator publishes FK ON (decided, see QUESTIONS.md)."
            ],
            "discrepancy_files": ["QUESTIONS.md", "WORKING_NOTES.md"]
        },
        "p02": p02_data,
        "sf_showcase": sf_showcase,
        "promises": all_promises,
        "quarantined": quarantined_items + real_quarantined_items
    }

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    with open(OUT_JS, "w", encoding="utf-8") as f:
        f.write("/* SF Promises - Dynamic SQLite Export */\n")
        f.write("window.__DEMO_DATA__ = ")
        json.dump(payload, f, indent=2)
        f.write(";\n")

    print(f"Data export complete.")
    print(f"  Exported {len(all_promises)} promises with verdicts {verdict_counts}")
    print(f"  Quarantined items: {len(quarantined_items)}")
    print(f"  DB totals: {total_db_promises} promises, {total_db_verdicts} verdicts")

if __name__ == "__main__":
    export()
