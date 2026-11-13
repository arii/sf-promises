#!/usr/bin/env python3
"""
Stage, validate, and upload the enriched SF Promises dataset, multi-config splits,
schema, summary, and SQLite database to Hugging Face Hub (onasafari/sf-promises).
"""

import argparse
import csv
import json
import os
import shutil
import sqlite3
from collections import Counter

REPO_ID = "onasafari/sf-promises"
DEFAULT_STAGING_DIR = "/tmp/hf_sf_promises_dataset"

parser = argparse.ArgumentParser(description="Stage, validate, and upload SF Promises HF dataset.")
parser.add_argument(
    "--validate-only",
    action="store_true",
    help="Stage and validate all Hugging Face configs/splits/schemas locally without uploading.",
)
parser.add_argument(
    "--staging-dir",
    default=DEFAULT_STAGING_DIR,
    help="Directory where Hugging Face repository artifacts are staged.",
)
args, _unknown = parser.parse_known_args()

STAGING_DIR = args.staging_dir

# 1. Clean and initialize staging directory
shutil.rmtree(STAGING_DIR, ignore_errors=True)
os.makedirs(STAGING_DIR, exist_ok=True)
os.makedirs(os.path.join(STAGING_DIR, "data", "commitments"), exist_ok=True)
os.makedirs(os.path.join(STAGING_DIR, "data", "standardized_16col"), exist_ok=True)
os.makedirs(os.path.join(STAGING_DIR, "data", "quarantined"), exist_ok=True)
os.makedirs(os.path.join(STAGING_DIR, "data", "intake_ledger"), exist_ok=True)

with open("docs/data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

promises = data.get("promises", [])
quarantined = data.get("quarantined", [])
meta = data.get("metadata", {})
db_status = data.get("database_status", {})

# 2. Export canonical commitments CSV (72 columns including precision, missingness, geo scope, and audit checks)
csv_fields = [
    "promise_id",
    "impact_rank",
    "record_type",
    "pillar",
    "entity",
    "entity_canonical_name",
    "entity_category",
    "entity_category_canonical",
    "entity_type_legacy",
    "entity_promise_count",
    "entity_sample_warning",
    "entity_party",
    "entity_term_start",
    "entity_term_end",
    "role",
    "category",
    "category_l1",
    "category_l2",
    "secondary_categories",
    "tags",
    "neighborhood",
    "neighborhood_canonical",
    "address_full",
    "address_status",
    "latitude",
    "longitude",
    "supervisor_district",
    "district_status",
    "is_citywide",
    "geographic_scope",
    "is_centroid",
    "promise_text",
    "verbatim_quote",
    "promised_date",
    "promise_date_precision",
    "promise_made_date",
    "due_date",
    "due_date_precision",
    "due_date_status",
    "deadline_date",
    "opened_date",
    "completion_date",
    "completion_date_precision",
    "completion_date_status",
    "days_remaining",
    "days_overdue",
    "promise_age_days",
    "time_to_verdict_days",
    "verdict",
    "verdict_reason",
    "verdict_reason_code",
    "verdict_confidence",
    "verdict_evidence_count",
    "verdict_contradiction_count",
    "affirming_evidence_count",
    "refuting_evidence_count",
    "verdict_supporting_evidence_count",
    "verdict_contradicting_evidence_count",
    "has_contradictory_evidence",
    "all_checks_passed",
    "failed_check_count",
    "impact_score",
    "completion_percentage",
    "source_url",
    "source_tier",
    "source_credibility_score",
    "source_type_standardized",
    "source_domain_authority",
    "fact_check_status",
    "source_archived_url",
    "source_hash",
    "relevance_score",
    "decided_at",
]

def serialize_row(p):
    row = {}
    rel = p.get("relevance") or {}
    for k in csv_fields:
        val = p.get(k)
        if k == "relevance_score" and val is None and isinstance(rel, dict):
            val = rel.get("score")
        if k == "verbatim_quote" and not val:
            val = p.get("promise_text")
        if isinstance(val, bool):
            row[k] = "true" if val else "false"
        elif isinstance(val, (list, tuple)):
            row[k] = "; ".join(str(x) for x in val)
        elif val is None:
            row[k] = ""
        else:
            row[k] = str(val)
    return row

commitments_split_path = os.path.join(STAGING_DIR, "data", "commitments", "train.csv")
with open(commitments_split_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=csv_fields)
    writer.writeheader()
    for p in promises:
        writer.writerow(serialize_row(p))
shutil.copy(commitments_split_path, os.path.join(STAGING_DIR, "promises.csv"))

# 3. Export quarantined split CSV (10 columns)
q_fields = [
    "quarantine_id",
    "promise_id",
    "title",
    "planted_claim",
    "check_type",
    "failing_check",
    "reason",
    "agent",
    "quarantined_at",
    "destination",
]

quarantined_split_path = os.path.join(STAGING_DIR, "data", "quarantined", "train.csv")
with open(quarantined_split_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=q_fields)
    writer.writeheader()
    for q in quarantined:
        writer.writerow({k: q.get(k, "") for k in q_fields})
shutil.copy(quarantined_split_path, os.path.join(STAGING_DIR, "quarantined.csv"))

# 4. Export Standardized 16-Column Master Dataset, Intake Ledger Split, & Canonical JSONs
if os.path.exists("data/sf_promises_master.csv"):
    shutil.copy("data/sf_promises_master.csv", os.path.join(STAGING_DIR, "sf_promises_master.csv"))
    shutil.copy("data/sf_promises_master.csv", os.path.join(STAGING_DIR, "data", "standardized_16col", "train.csv"))

intake_rows = []
if os.path.exists("data/intake_ledger.csv"):
    shutil.copy("data/intake_ledger.csv", os.path.join(STAGING_DIR, "intake_ledger.csv"))
    shutil.copy("data/intake_ledger.csv", os.path.join(STAGING_DIR, "data", "intake_ledger", "train.csv"))
    with open("data/intake_ledger.csv", "r", encoding="utf-8") as f:
        intake_rows = list(csv.DictReader(f))

for extra_json in ("data/evidence_review_queue.json", "data/intake_candidate_register.json"):
    if os.path.exists(extra_json):
        shutil.copy(extra_json, os.path.join(STAGING_DIR, os.path.basename(extra_json)))

with open(os.path.join(STAGING_DIR, "promises.json"), "w", encoding="utf-8") as f:
    json.dump(promises, f, indent=2)

# 4. Generate data_summary.json
verdict_counts = Counter(p.get("verdict") for p in promises)
cat_l1_counts = Counter(p.get("category_l1") for p in promises)
neighborhood_counts = Counter(p.get("neighborhood_canonical") for p in promises)
district_counts = Counter(str(p.get("supervisor_district")) for p in promises if p.get("supervisor_district") is not None)
entity_cat_counts = Counter(p.get("entity_category") for p in promises)
reason_code_counts = Counter(p.get("verdict_reason_code") for p in promises)

ages = [p.get("promise_age_days") for p in promises if p.get("promise_age_days") is not None]
ttvs = [p.get("time_to_verdict_days") for p in promises if p.get("time_to_verdict_days") is not None]
impacts = [p.get("impact_score") for p in promises if p.get("impact_score") is not None]

data_summary = {
    "dataset_name": "SF Promises Public Ledger",
    "version": "2.1.0",
    "last_updated": "2026-11-12",
    "total_verified_commitments": len(promises),
    "total_quarantined_records": len(quarantined),
    "verdict_distribution": {
        "kept": verdict_counts.get("kept", 0),
        "in_progress": verdict_counts.get("in_progress", 0),
        "broken": verdict_counts.get("broken", 0),
        "undecided": verdict_counts.get("undecided", 0),
        "kept_percentage": round((verdict_counts.get("kept", 0) / len(promises)) * 100, 1),
        "in_progress_percentage": round((verdict_counts.get("in_progress", 0) / len(promises)) * 100, 1),
        "broken_percentage": round((verdict_counts.get("broken", 0) / len(promises)) * 100, 1),
        "undecided_percentage": round((verdict_counts.get("undecided", 0) / len(promises)) * 100, 1)
    },
    "category_l1_breakdown": dict(cat_l1_counts.most_common()),
    "canonical_neighborhood_breakdown": dict(neighborhood_counts.most_common()),
    "supervisor_district_breakdown": dict(district_counts.most_common()),
    "entity_category_breakdown": dict(entity_cat_counts.most_common()),
    "verdict_reason_code_breakdown": dict(reason_code_counts.most_common()),
    "temporal_summary": {
        "avg_promise_age_days": round(sum(ages) / len(ages), 1) if ages else 0,
        "avg_time_to_verdict_days": round(sum(ttvs) / len(ttvs), 1) if ttvs else 0,
        "overdue_promises_count": sum(1 for p in promises if p.get("days_overdue")),
        "future_deadline_promises_count": sum(1 for p in promises if p.get("days_remaining"))
    },
    "impact_score_stats": {
        "avg_impact_score": round(sum(impacts) / len(impacts), 1) if impacts else 0,
        "min_impact_score": min(impacts) if impacts else 0,
        "max_impact_score": max(impacts) if impacts else 0,
    },
    "verification_exceptions": {
        "all_checks_passed_count": sum(1 for p in promises if p.get("all_checks_passed") is not False),
        "failed_or_incomplete_promises_count": sum(1 for p in promises if p.get("all_checks_passed") is False),
        "total_failed_or_unrecorded_checks": sum(p.get("failed_check_count") or 0 for p in promises),
    },
    "evidence_reconciliation": db_status.get("evidence_reconciliation", {}),
    "sourcing_audit": db_status.get("sourcing_audit", {}),
    "total_intake_candidates": len(intake_rows),
}

with open(os.path.join(STAGING_DIR, "data_summary.json"), "w", encoding="utf-8") as f:
    json.dump(data_summary, f, indent=2)

# 5. Generate SCHEMA.json (Formal JSON Schema for validation)
schema_def = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "SFPromise",
    "description": "Schema for verified San Francisco public promises and commitments",
    "type": "object",
    "required": [
        "promise_id",
        "entity_canonical_name",
        "promise_text",
        "verdict",
        "category_l1",
        "neighborhood_canonical",
        "promise_date_precision",
        "geographic_scope",
        "is_centroid",
        "all_checks_passed",
    ],
    "properties": {
        "promise_id": {"type": "string", "pattern": "^[A-Z0-9-]+$"},
        "impact_rank": {"type": "integer", "minimum": 1},
        "record_type": {"type": "string", "enum": ["commitment", "milestone", "statutory_mandate", "corporate_pledge"]},
        "pillar": {"type": "string"},
        "entity": {"type": "string"},
        "entity_canonical_name": {"type": "string"},
        "entity_category": {"type": "string"},
        "entity_category_canonical": {
            "type": "string",
            "enum": ["politician", "city_department", "corporation", "sports_team", "cultural_organization"],
        },
        "entity_type_legacy": {"type": "string"},
        "entity_promise_count": {"type": "integer", "minimum": 1},
        "entity_sample_warning": {"type": "boolean"},
        "entity_party": {"type": ["string", "null"], "enum": ["D", "R", "I", None]},
        "entity_term_start": {"type": ["string", "null"]},
        "entity_term_end": {"type": ["string", "null"]},
        "role": {"type": ["string", "null"]},
        "category": {"type": "string"},
        "category_l1": {
            "type": "string",
            "enum": ["Public Safety", "Housing", "Transportation", "Infrastructure", "Culture & Recreation", "Economy & Commercial", "Environment & Energy", "Civic Governance"]
        },
        "category_l2": {"type": "string"},
        "secondary_categories": {"type": "array", "items": {"type": "string"}},
        "tags": {"type": "array", "items": {"type": "string"}},
        "neighborhood": {"type": "string"},
        "neighborhood_canonical": {"type": "string"},
        "address_full": {"type": ["string", "null"]},
        "address_status": {"type": "string", "enum": ["present", "not_applicable", "not_yet_known", "not_captured"]},
        "latitude": {"type": ["number", "null"]},
        "longitude": {"type": ["number", "null"]},
        "supervisor_district": {"type": ["integer", "null"], "minimum": 1, "maximum": 11},
        "district_status": {"type": "string", "enum": ["present", "not_applicable", "not_yet_known", "not_captured"]},
        "is_citywide": {"type": "boolean"},
        "geographic_scope": {"type": "string", "enum": ["exact_address", "neighborhood", "district", "regional", "citywide"]},
        "is_centroid": {"type": "boolean"},
        "promise_text": {"type": "string"},
        "verbatim_quote": {"type": "string"},
        "promised_date": {"type": ["string", "null"]},
        "promise_date_precision": {"type": "string", "enum": ["day", "month", "year"]},
        "promise_made_date": {"type": ["string", "null"]},
        "due_date": {"type": ["string", "null"]},
        "due_date_precision": {"type": ["string", "null"], "enum": ["day", "month", "year", "not_applicable", "not_recorded", None]},
        "due_date_status": {"type": "string", "enum": ["present", "not_applicable", "not_yet_known", "not_captured"]},
        "deadline_date": {"type": ["string", "null"]},
        "opened_date": {"type": ["string", "null"]},
        "completion_date": {"type": ["string", "null"]},
        "completion_date_precision": {"type": ["string", "null"], "enum": ["day", "month", "year", "not_applicable", "not_recorded", None]},
        "completion_date_status": {"type": "string", "enum": ["present", "not_applicable", "not_yet_known", "not_captured"]},
        "days_remaining": {"type": ["integer", "null"]},
        "days_overdue": {"type": ["integer", "null"]},
        "promise_age_days": {"type": ["integer", "null"]},
        "time_to_verdict_days": {"type": ["integer", "null"]},
        "verdict": {
            "type": "string",
            "enum": ["kept", "in_progress", "broken", "undecided"]
        },
        "verdict_reason": {"type": "string"},
        "verdict_reason_code": {"type": "string"},
        "verdict_confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        "verdict_evidence_count": {"type": "integer", "minimum": 0},
        "verdict_contradiction_count": {"type": "integer", "minimum": 0},
        "affirming_evidence_count": {"type": "integer", "minimum": 0},
        "refuting_evidence_count": {"type": "integer", "minimum": 0},
        "verdict_supporting_evidence_count": {"type": "integer", "minimum": 1},
        "verdict_contradicting_evidence_count": {"type": "integer", "minimum": 0},
        "has_contradictory_evidence": {"type": "boolean"},
        "all_checks_passed": {"type": "boolean"},
        "failed_check_count": {"type": "integer", "minimum": 0},
        "impact_score": {"type": "integer", "minimum": 1, "maximum": 10},
        "completion_percentage": {"type": "integer", "minimum": 0, "maximum": 100},
        "source_url": {"type": "string"},
        "source_tier": {"type": "string", "enum": ["Official", "News", "Reference"]},
        "source_credibility_score": {"type": "integer", "minimum": 1, "maximum": 10},
        "source_type_standardized": {"type": "string"},
        "source_domain_authority": {"type": "integer", "minimum": 1, "maximum": 10},
        "fact_check_status": {"type": "string", "enum": ["verified", "disputed", "unverified"]},
        "source_archived_url": {"type": "string"},
        "source_hash": {"type": "string"}
    }
}

with open(os.path.join(STAGING_DIR, "SCHEMA.json"), "w", encoding="utf-8") as f:
    json.dump(schema_def, f, indent=2)

# 6. Create enriched SQLite database promises.sqlite
sqlite_path = os.path.join(STAGING_DIR, "promises.sqlite")
if os.path.exists(sqlite_path):
    os.remove(sqlite_path)

con = sqlite3.connect(sqlite_path)
cur = con.cursor()

# Create table promises with all enriched columns
cur.execute("""
CREATE TABLE promises (
    promise_id TEXT PRIMARY KEY,
    impact_rank INTEGER,
    entity TEXT,
    entity_canonical_name TEXT,
    entity_category TEXT,
    entity_party TEXT,
    entity_term_start TEXT,
    entity_term_end TEXT,
    role TEXT,
    category TEXT,
    category_l1 TEXT,
    category_l2 TEXT,
    secondary_categories TEXT,
    tags TEXT,
    neighborhood TEXT,
    neighborhood_canonical TEXT,
    address_full TEXT,
    latitude REAL,
    longitude REAL,
    supervisor_district INTEGER,
    is_citywide INTEGER,
    promise_text TEXT,
    verbatim_quote TEXT,
    promised_date TEXT,
    promise_made_date TEXT,
    due_date TEXT,
    deadline_date TEXT,
    opened_date TEXT,
    completion_date TEXT,
    days_remaining INTEGER,
    days_overdue INTEGER,
    promise_age_days INTEGER,
    time_to_verdict_days INTEGER,
    verdict TEXT,
    verdict_reason TEXT,
    verdict_reason_code TEXT,
    verdict_confidence REAL,
    verdict_evidence_count INTEGER,
    verdict_contradiction_count INTEGER,
    impact_score INTEGER,
    completion_percentage INTEGER,
    source_url TEXT,
    source_tier TEXT,
    source_credibility_score INTEGER,
    source_type_standardized TEXT,
    source_domain_authority INTEGER,
    fact_check_status TEXT,
    source_archived_url TEXT,
    source_hash TEXT,
    relevance_score INTEGER,
    decided_at TEXT
)
""")

for p in promises:
    rel = p.get("relevance") or {}
    rel_score = rel.get("score") if isinstance(rel, dict) else None
    cur.execute("""
    INSERT INTO promises VALUES (
        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
        ?
    )
    """, (
        p.get("promise_id"),
        p.get("impact_rank") or p.get("display_no", 0),
        p.get("entity"),
        p.get("entity_canonical_name"),
        p.get("entity_category"),
        p.get("entity_party"),
        p.get("entity_term_start"),
        p.get("entity_term_end"),
        p.get("role"),
        p.get("category"),
        p.get("category_l1"),
        p.get("category_l2"),
        json.dumps(p.get("secondary_categories", [])),
        json.dumps(p.get("tags", [])),
        p.get("neighborhood"),
        p.get("neighborhood_canonical"),
        p.get("address_full"),
        p.get("latitude"),
        p.get("longitude"),
        p.get("supervisor_district"),
        1 if p.get("is_citywide") else 0,
        p.get("promise_text"),
        p.get("verbatim_quote") or p.get("promise_text"),
        p.get("promised_date"),
        p.get("promise_made_date"),
        p.get("due_date"),
        p.get("deadline_date"),
        p.get("opened_date"),
        p.get("completion_date"),
        p.get("days_remaining"),
        p.get("days_overdue"),
        p.get("promise_age_days"),
        p.get("time_to_verdict_days"),
        p.get("verdict"),
        p.get("verdict_reason"),
        p.get("verdict_reason_code"),
        p.get("verdict_confidence"),
        p.get("verdict_evidence_count"),
        p.get("verdict_contradiction_count"),
        p.get("impact_score"),
        p.get("completion_percentage"),
        p.get("source_url"),
        p.get("source_tier"),
        p.get("source_credibility_score"),
        p.get("source_type_standardized"),
        p.get("source_domain_authority"),
        p.get("fact_check_status"),
        p.get("source_archived_url"),
        p.get("source_hash"),
        rel_score,
        p.get("decided_at")
    ))

# Create quarantined table
cur.execute("""
CREATE TABLE quarantined (
    quarantine_id TEXT PRIMARY KEY,
    promise_id TEXT,
    title TEXT,
    planted_claim TEXT,
    check_type TEXT,
    failing_check TEXT,
    reason TEXT,
    agent TEXT,
    quarantined_at TEXT,
    destination TEXT
)
""")

for q in quarantined:
    cur.execute("""
    INSERT INTO quarantined VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        q.get("quarantine_id", ""),
        q.get("promise_id", ""),
        q.get("title", ""),
        q.get("planted_claim", ""),
        q.get("check_type", ""),
        q.get("failing_check", ""),
        q.get("reason", ""),
        q.get("agent", ""),
        q.get("quarantined_at", ""),
        q.get("destination", "")
    ))

# Create metadata table
cur.execute("""
CREATE TABLE metadata (
    key TEXT PRIMARY KEY,
    value TEXT
)
""")

cur.executemany("INSERT INTO metadata VALUES (?, ?)", [
    ("dataset_name", "SF Promises Public Ledger"),
    ("version", "2.1.0"),
    ("verified_commitments", str(len(promises))),
    ("quarantined_items", str(len(quarantined))),
    ("exported_at", meta.get("exported_at", "")),
    ("git_commit", meta.get("git_commit", "")),
    ("spatial_coverage", "San Francisco (11 Districts & Regional Infrastructure)")
])

con.commit()
con.close()

# 7. Create README.md (Comprehensive Dataset Card & Data Dictionary)
readme_path = os.path.join(STAGING_DIR, "README.md")
with open(readme_path, "w", encoding="utf-8") as f:
    f.write(r"""---
license: mit
task_categories:
- tabular-classification
- text-classification
language:
- en
tags:
- civic-tech
- san-francisco
- public-records
- accountability
- promises
- verdicts
- government
- geography
- spatial-analysis
size_categories:
- n<1K
pretty_name: "SF Promises: Civic Accountability Ledger"
configs:
- config_name: default
  data_files:
  - split: train
    path: data/commitments/train.csv
- config_name: commitments
  data_files:
  - split: train
    path: data/commitments/train.csv
- config_name: standardized_16col
  data_files:
  - split: train
    path: data/standardized_16col/train.csv
- config_name: quarantined
  data_files:
  - split: train
    path: data/quarantined/train.csv
- config_name: intake_ledger
  data_files:
  - split: train
    path: data/intake_ledger/train.csv
---

# SF Promises Dataset

## Overview
Civic accountability tracker for public commitments made across San Francisco — from City Hall, SF Board of Supervisors, and SFO Airport to Chase Center and neighborhood commercial corridors. Each record is linked to its saved source document and SHA-256 hash, evaluated through deterministic code checks, and published with explicit verification exceptions, date precision levels, missingness codes, and geographic scope metadata.

## Available Configurations & Split Files

Every Hugging Face Dataset Viewer configuration reads from an isolated split path under `data/` to prevent mixed-schema auto-loader collisions:

| Config Name | Split Path | Rows | Columns | Description |
|---|---|---|---|---|
| `default` / `commitments` | `data/commitments/train.csv` | 54 | 72 | Primary enriched tabular ledger with precision flags, missingness semantics, geo scope/centroids, evidence counts, and check exception flags |
| `standardized_16col` | `data/standardized_16col/train.csv` | 54 | 16 | Standardized master schema (`sf_promises_master.csv`) for cross-city comparisons |
| `quarantined` | `data/quarantined/train.csv` | 13 | 10 | Registry of planted tests and rejected claims stopped before publishing |
| `intake_ledger` | `data/intake_ledger/train.csv` | 63 | 23 | Outcome-blind stratified sourcing register across 10 pillars and all 11 supervisor districts |

Root convenience files (`promises.csv`, `sf_promises_master.csv`, `quarantined.csv`, `intake_ledger.csv`, `promises.sqlite`, `SCHEMA.json`, `data_summary.json`, `evidence_review_queue.json`, `intake_candidate_register.json`, `promises.json`) are kept alongside the `data/` split directories for direct script access.

---

## Methodology & Provenance

### 1. Outcome-Blind Sourcing & Stratified Discovery
Commitments are discovered via a 3-stage pipeline (`src/sourcing/`):
1. **Stratified Search Planning (`SearchPlanner`)**: Enforces outcome-blind query construction (rejecting outcome terms such as `broken`, `failed`, `kept`, `scandal`, `delayed`) across 10 San Francisco Life & Culture pillars and all 11 supervisor districts.
2. **Retrieval (`DiscoveryHarvester`)**: Stores verbatim source bytes and SHA-256 hashes from municipal portals, allowlisted local journalism, and institutional filings.
3. **Qualification (`QualificationIntakeAgent`)**: Strips any outcome labels before evaluating commitment specificity and date/scope readiness, recording audit status in `intake_ledger`.

### 2. Verbatim Quoting & Cryptographic Integrity
Every statement is checked byte-for-byte against its saved disk snapshot via SHA-256 hash and substring matching. Submissions with altered quotes or unapproved domains are stopped in `quarantined`.

### 3. Deterministic Arbitration & Visible Exceptions
Rather than hiding partial verification failures, every record exposes `all_checks_passed`, `failed_check_count`, and the specific check results:
- **47 of 54** published commitments pass all deterministic checks (`all_checks_passed = true`).
- **7 commitments** (`P82`, `P83`, `P17`, `P61`, `P37`, `P57`, `P58`) remain published with explicit exception flags (`all_checks_passed = false`, totaling **22** failed or unrecorded checks).

### 4. Evidence Reconciliation Model
`promises.db` stores **124** total evidence rows across the project:
- **99** direct verdict-supporting/contradicting claims attached to the 54 published commitments
- **11** background context records
- **8** intake/archival discovery records
- **6** duplicate/superseded claim rows retained for lineage

Every published record (including all **17** broken commitments) carries `verdict_supporting_evidence_count >= 1`, distinguishing affirming vs. refuting direction from whether the evidence supports the final verdict.

### 5. Confidence & Impact Metrics
- **Verdict Confidence ($C \in [0.0, 1.0]$)**:
  $$C = W_{\\text{tier}} \\times \\left(1 - \\frac{N_{\\text{contradicting}}}{N_{\\text{total}} + 1}\\right)$$
  where Tier 1 (Official Government) has weight $1.0$, Tier 2 (Press) has $0.85$, and Tier 3 has $0.70$.
- **Impact Score ($I \in [1, 10]$)**:
  Standardized civic priority scale combining geographic scope, budgetary magnitude ($>\\$10\\text{M}$ capital investments score $\\ge 7$), and affected population.

---

## Known Biases & Research Limitations

- **Sample Size & Single-Record Entities ($n=54$, 31 canonical entities)**: 24 of 31 canonical entities currently have only $n=1$ tracked commitment (flagged via `entity_sample_warning = true`). Aggregate keep/break percentages per entity should not be extrapolated as broad track records.
- **Topic & District Skew**: Published records skew toward Civic Life and Housing/Neighborhoods and omit Districts 2, 4, 8, and 11; the `intake_ledger` split documents ongoing outcome-blind collection closing those gaps.
- **Coordinate Display Centroids**: Only 12 records represent exact street-level pins (`is_centroid = false`). The remaining 42 records carry `is_centroid = true` (citywide, regional, or neighborhood display centroids) and must not be interpreted as physical project locations in spatial joins.
- **Date Precision & Missingness**: Imprecise statements (e.g., `"2024"`) preserve precision in `promise_date_precision` / `due_date_precision` (`year | month | day`). Missing dates/addresses carry explicit reason codes (`not_applicable | not_yet_known | not_captured`).

---

## Citation & BibTeX

If you use this dataset in civic-tech research, public policy analysis, or AI governance evaluation, please cite:

```bibtex
@dataset{sf_promises_2026,
  author = {Anders, Ariel and Contributors},
  title = {SF Promises: A Sourced, Cryptographically Verified Ledger of San Francisco Civic Commitments},
  year = {2026},
  month = {November},
  publisher = {Hugging Face},
  howpublished = {\\url{https://huggingface.co/datasets/onasafari/sf-promises}},
  note = {Version 2.1.0. Winner of Best Use of Keenable, Archil Hackathon}
}
```

---

## Update Cadence & Versioning

- **Ingest Cadence**: Ingest runs periodically with automated source checks.
- **Durability Audits**: Automated checks re-validate source availability, archive URLs, and hash consistency.
- **Version**: `2.1.0` (November 2026).

---

## Fields & Data Dictionary

### Core Promise Data
- `promise_id` *(string)*: Unique identifier (e.g., `P01`, `P02`, `SFO-01`)
- `impact_rank` *(integer)*: Civic impact & public debate rank (#1 to #54)
- `promise_text` *(string)*: Clean promise statement
- `verbatim_quote` *(string)*: Exact quotation from official primary source document
- `entity` *(string)*: Raw entity string
- `entity_canonical_name` *(string)*: Standardized canonical entity name (e.g., `Daniel Lurie`, `Golden State Valkyries`, `SFMTA`)
- `entity_category` *(enum)*: `politician`, `city_department`, `sports_team`, `corporation`, `cultural_organization`
- `entity_party` *(string/null)*: Political party affiliation if politician (`D`, `R`, `I`)
- `entity_term_start` *(string/null)*: Date when entity took office or leadership role
- `entity_term_end` *(string/null)*: Date when entity term ended or ends
- `role` *(string)*: Official title or position at time of commitment

### Temporal Data
- `promise_made_date` *(string)*: Date commitment was first uttered or published (YYYY-MM-DD)
- `deadline_date` *(string/null)*: Target deadline or promised completion date (YYYY-MM-DD)
- `completion_date` *(string/null)*: Date milestone was verified complete or operational
- `days_remaining` *(integer/null)*: Days remaining until deadline (relative to export date, for active commitments)
- `days_overdue` *(integer/null)*: Days overdue past deadline (for broken or stalled commitments)
- `promise_age_days` *(integer)*: Age of promise in days since announcement
- `time_to_verdict_days` *(integer)*: Days elapsed between promise announcement and formal audit verdict

### Geographic & Spatial Data
- `neighborhood_canonical` *(string)*: Standardized neighborhood name aligned with SF Planning Department boundaries (e.g., *Tenderloin*, *Mission Bay*, *Golden Gate Park*, *SFO Airport*, *Citywide*)
- `address_full` *(string/null)*: Full street address or intersection
- `latitude` *(float)*: WGS84 latitude coordinate
- `longitude` *(float)*: WGS84 longitude coordinate
- `supervisor_district` *(integer/null)*: San Francisco Supervisorial District (1 through 11)
- `is_citywide` *(boolean)*: `true` if policy/program affects the entire city; `false` if site-specific

### Categorization
- `category_l1` *(enum)*: Primary broad sector: `Public Safety`, `Housing`, `Transportation`, `Infrastructure`, `Culture & Recreation`, `Economy & Commercial`, `Environment & Energy`, `Civic Governance`
- `category_l2` *(string)*: Specific subcategory (e.g., *Crisis & Mental Health Services*, *Airport Infrastructure*, *Bicycle & Pedestrian Infrastructure*)
- `secondary_categories` *(array)*: Additional related domain classifications
- `tags` *(array)*: Free-form tags for filtering (e.g., *homelessness*, *mental_health*, *stabilization_center*)

### Verdict Metadata
- `verdict` *(enum)*: Outcome status (`kept`, `in_progress`, `broken`, `undecided`)
- `verdict_reason` *(string)*: Plain-English factual rationale from arbitrator checks
- `verdict_reason_code` *(string)*: Structured enum (`on_time`, `delayed_but_kept`, `numeric_target_missed`, `in_progress_on_track`, `goal_abandoned`, etc.)
- `verdict_confidence` *(float)*: Confidence certainty score (0.00 to 1.00)
- `verdict_evidence_count` *(integer)*: Number of supporting evidence claims filed
- `verdict_contradiction_count` *(integer)*: Number of contradicting claims filed
- `impact_score` *(integer)*: Standardized civic importance score (1 to 10)
- `completion_percentage` *(integer)*: Completion milestone percentage (0 to 100)

### Source Provenance
- `source_url` *(string)*: URL of original document
- `source_tier` *(enum)*: `Official`, `News`, `Reference`
- `source_credibility_score` *(integer)*: Credibility rating (1 to 10)
- `source_type_standardized` *(enum)*: `official_government`, `news_mainstream`, `news_local`, `corporate_release`, `legal_record`, `academic_report`
- `source_domain_authority` *(integer)*: Domain authority rating (1 to 10)
- `fact_check_status` *(enum)*: `verified`, `disputed`, `unverified`
- `source_archived_url` *(string)*: Wayback Machine permanent archive URL
- `source_hash` *(string)*: SHA-256 cryptographic digest of saved source bytes

---

## Quickstart

### Python (pandas)

```python
import pandas as pd

# Load primary commitments (51 columns)
df = pd.read_csv("https://huggingface.co/datasets/onasafari/sf-promises/raw/main/promises.csv")
print(f"Loaded {len(df)} commitments")
print(df.groupby('category_l1')['verdict'].value_counts())

# Load standardized master table (16 columns)
df_master = pd.read_csv("https://huggingface.co/datasets/onasafari/sf-promises/raw/main/sf_promises_master.csv")
print(df_master[['promise_id', 'entity', 'verdict', 'confidence']].head())
```

### Python (sqlite3)

```python
import sqlite3
import urllib.request
import pandas as pd

urllib.request.urlretrieve(
    "https://huggingface.co/datasets/onasafari/sf-promises/resolve/main/promises.sqlite",
    "promises.sqlite"
)

con = sqlite3.connect("promises.sqlite")
df = pd.read_sql_query(\"\"\"
    SELECT entity_canonical_name, neighborhood_canonical, verdict, impact_score
    FROM promises
    WHERE category_l1 = 'Public Safety'
    ORDER BY impact_score DESC
\"\"\", con)
print(df)
```

### Hugging Face Datasets

```python
from datasets import load_dataset

# Load commitments configuration
dataset = load_dataset("onasafari/sf-promises", "commitments")
print(dataset['train'][0])

# Load quarantined audit test cases
quarantined = load_dataset("onasafari/sf-promises", "quarantined")
print(f"Quarantined count: {len(quarantined['train'])}")
```

## Project Links

- **Live Web Explorer**: [https://arii.github.io/sf-promises/](https://arii.github.io/sf-promises/)
- **GitHub Repository**: [https://github.com/arii/sf-promises](https://github.com/arii/sf-promises)
""")

# 8. Validate staged splits locally before any Hub upload
expected_splits = {
    "data/commitments/train.csv": (54, len(csv_fields)),
    "data/standardized_16col/train.csv": (54, 16),
    "data/quarantined/train.csv": (13, 10),
    "data/intake_ledger/train.csv": (63, 23),
}
for rel_path, (expected_rows, expected_cols) in expected_splits.items():
    full_path = os.path.join(STAGING_DIR, rel_path)
    assert os.path.exists(full_path), f"Missing split CSV: {rel_path}"
    with open(full_path, "r", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    header = rows[0] if rows else []
    data_rows = rows[1:] if len(rows) > 1 else []
    assert len(header) == expected_cols, f"{rel_path}: expected {expected_cols} cols, got {len(header)}"
    assert len(data_rows) == expected_rows, f"{rel_path}: expected {expected_rows} rows, got {len(data_rows)}"

print(f"Validated all 4 Hugging Face dataset splits cleanly in {STAGING_DIR}:")
for rel_path in expected_splits:
    fsize = os.path.getsize(os.path.join(STAGING_DIR, rel_path))
    print(f"  - {rel_path} ({fsize:,} bytes)")

if args.validate_only:
    print("Validate-only mode complete; skipping Hugging Face Hub upload.")
    raise SystemExit(0)

# 9. Upload to Hugging Face
from huggingface_hub import HfApi

print(f"\nUploading enriched dataset to Hugging Face repository {REPO_ID}...")
api = HfApi(token=os.getenv("HF_TOKEN") or None)

# Delete deprecated redundant duplicate files if they exist in the remote repo
for redundant_file in ("data.csv", "data.json"):
    try:
        api.delete_file(path_in_repo=redundant_file, repo_id=REPO_ID, repo_type="dataset")
        print(f"Removed redundant file from remote repo: {redundant_file}")
    except Exception:
        pass

api.upload_folder(
    folder_path=STAGING_DIR,
    repo_id=REPO_ID,
    repo_type="dataset",
    commit_message="feat: isolate split paths for HF dataset viewer and expose audit schema metadata",
)
print("Upload complete! Dataset is now live at: https://huggingface.co/datasets/" + REPO_ID)
