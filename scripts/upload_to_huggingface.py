#!/usr/bin/env python3
"""
Upload enriched SF Promises dataset, schema, summary, and SQLite database to Hugging Face Hub (onasafari/sf-promises)
"""

import os
import csv
import json
import shutil
import sqlite3
from collections import Counter
from huggingface_hub import HfApi

REPO_ID = "onasafari/sf-promises"
STAGING_DIR = "/tmp/hf_sf_promises_dataset"
os.makedirs(STAGING_DIR, exist_ok=True)

with open("docs/data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

promises = data.get("promises", [])
quarantined = data.get("quarantined", [])
meta = data.get("metadata", {})
db_status = data.get("database_status", {})

# 1. Clean and initialize staging directory
shutil.rmtree(STAGING_DIR, ignore_errors=True)
os.makedirs(STAGING_DIR, exist_ok=True)

with open("docs/data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

promises = data.get("promises", [])
quarantined = data.get("quarantined", [])
meta = data.get("metadata", {})
db_status = data.get("database_status", {})

# 2. Export canonical promises.csv (51 columns)
csv_fields = [
    "promise_id",
    "impact_rank",
    "entity",
    "entity_canonical_name",
    "entity_category",
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
    "latitude",
    "longitude",
    "supervisor_district",
    "is_citywide",
    "promise_text",
    "verbatim_quote",
    "promised_date",
    "promise_made_date",
    "due_date",
    "deadline_date",
    "opened_date",
    "completion_date",
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
    "decided_at"
]

def serialize_row(p):
    row = {}
    for k in csv_fields:
        val = p.get(k)
        if isinstance(val, (list, tuple)):
            row[k] = "; ".join(str(x) for x in val)
        elif val is None:
            row[k] = ""
        else:
            row[k] = str(val)
    return row

csv_path = os.path.join(STAGING_DIR, "promises.csv")
with open(csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=csv_fields)
    writer.writeheader()
    for p in promises:
        writer.writerow(serialize_row(p))

# 3. Export quarantined.csv (10 columns)
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
    "destination"
]

q_csv_path = os.path.join(STAGING_DIR, "quarantined.csv")
with open(q_csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=q_fields)
    writer.writeheader()
    for q in quarantined:
        writer.writerow({k: q.get(k, "") for k in q_fields})

# 4. Export Standardized 16-Column Master Dataset & Canonical JSON
if os.path.exists("data/sf_promises_master.csv"):
    shutil.copy("data/sf_promises_master.csv", os.path.join(STAGING_DIR, "sf_promises_master.csv"))

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
        "max_impact_score": max(impacts) if impacts else 0
    }
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
        "neighborhood_canonical"
    ],
    "properties": {
        "promise_id": {"type": "string", "pattern": "^[A-Z0-9-]+$"},
        "impact_rank": {"type": "integer", "minimum": 1},
        "entity": {"type": "string"},
        "entity_canonical_name": {"type": "string"},
        "entity_category": {
            "type": "string",
            "enum": ["politician", "city_department", "sports_team", "corporation", "nonprofit", "cultural_organization"]
        },
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
        "latitude": {"type": ["number", "null"]},
        "longitude": {"type": ["number", "null"]},
        "supervisor_district": {"type": ["integer", "null"], "minimum": 1, "maximum": 11},
        "is_citywide": {"type": "boolean"},
        "promise_text": {"type": "string"},
        "verbatim_quote": {"type": "string"},
        "promised_date": {"type": ["string", "null"]},
        "promise_made_date": {"type": ["string", "null"]},
        "due_date": {"type": ["string", "null"]},
        "deadline_date": {"type": ["string", "null"]},
        "opened_date": {"type": ["string", "null"]},
        "completion_date": {"type": ["string", "null"]},
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
- config_name: commitments
  data_files:
  - split: train
    path: promises.csv
- config_name: standardized_16col
  data_files:
  - split: train
    path: sf_promises_master.csv
- config_name: quarantined
  data_files:
  - split: train
    path: quarantined.csv
default_config_name: commitments
---

# SF Promises Dataset

## Overview
Civic accountability tracker for public promises made across San Francisco — from City Hall, SF Board of Supervisors, and SFO Airport to Chase Center and neighborhood commercial corridors. Each promise is tracked from announcement through verdict, verified against cryptographically archived primary evidence.

Winner of the **Best Use of Keenable** award at the Archil *"Agents Need Solid Ground"* Hackathon (Nov 10, 2026).

## Available Configurations & Files

This repository provides multiple dataset configurations to prevent schema mixing in Hugging Face's Dataset Viewer:

| Configuration / File | Rows | Columns | Description |
|---|---|---|---|
| `commitments` (`promises.csv`) | 54 | 51 | Primary enriched tabular ledger with full spatial, temporal, source credibility, and verdict features |
| `standardized_16col` (`sf_promises_master.csv`) | 54 | 16 | Standardized master schema for cross-city civic accountability comparisons |
| `quarantined` (`quarantined.csv`) | 13 | 10 | Registry of test cases and rejected claims that failed automated gate checks |
| `promises.sqlite` | 54 + 13 | — | Complete relational SQLite database with `promises`, `quarantined`, and `metadata` tables |
| `SCHEMA.json` | — | — | Formal JSON Schema (draft-07) for schema validation |
| `data_summary.json` | — | — | Precomputed statistical distributions, category counts, and impact percentiles |
| `promises.json` | 54 | — | Canonical JSON records including advocate findings and relevance metrics |

---

## Methodology & Provenance

### 1. Source Discovery & Temporal Grounding
Commitments and outcomes are discovered by querying contemporaneous municipal archives, allowlisted local newsrooms (*SF Chronicle*, *Mission Local*, *San Francisco Standard*, *The Frisc*), agency performance dashboards (*SFMTA*, *SFPD*, *SFO*), and Board of Supervisors legislative records (*Legistar*). All queries are bounded by discovery time horizons to prevent retroactive hindsight bias.

### 2. Verbatim Quoting & Cryptographic Integrity
Every promise statement is linked to an exact verbatim quote and its parent document. The raw document bytes are hashed (SHA-256) upon retrieval. If an investigator agent alters a single word (e.g. mutating "1,500 shelter beds" to "1,500 shelter units"), the verification engine detects the hash discrepancy and diverts the submission to the Quarantine Registry.

### 3. Deterministic Arbitration Engine
A deterministic Python engine (zero model calls at verdict time) evaluates claims across 7 independent checks:
1. `accuracy_quote`: Verbatim quote substring match in hashed source document.
2. `temporal_order`: Promise date must precede the deadline and verification date.
3. `existence_check`: Required entity and source URLs must exist and resolve.
4. `numeric_target`: Quantitative metrics (e.g. bed counts, housing units, officer staffing) must match official records.
5. `source_authority`: Source domain must meet Tier 1 (Official Govt) or Tier 2 (Investigative Press) criteria.
6. `contradiction_balance`: Evaluating affirming versus contradicting evidence bundles.
7. `status_consistency`: Verdict state transitions must follow valid DAG edges.

### 4. Confidence & Impact Metrics
- **Verdict Confidence ($C \in [0.0, 1.0]$)**:
  $$C = W_{\\text{tier}} \\times \\left(1 - \\frac{N_{\\text{contradicting}}}{N_{\\text{total}} + 1}\\right)$$
  where Tier 1 (Official Government) has weight $1.0$, Tier 2 (Press) has $0.85$, and Tier 3 has $0.70$.
- **Impact Score ($I \in [1, 10]$)**:
  Standardized civic priority scale combining scope (citywide vs site-specific), budgetary magnitude ($>\\$10\\text{M}$ capital investments score $\\ge 7$), and population scale directly impacted.

---

## Known Biases & Research Limitations

- **Sample Size ($n=54$)**: This dataset is curated as a high-fidelity civic benchmark and evaluation set (zero-shot and few-shot testing), rather than for training large supervised models from scratch.
- **Jurisdictional Focus**: Exclusively covers San Francisco municipal governance, regional transit (SFO Airport, BART, Muni), and select high-profile civic institutions.
- **Reporting Bias**: High-salience issues (homelessness, public safety, transit infrastructure, downtown revitalization) receive greater media coverage and are more readily documented than routine administrative actions.

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

print(f"Successfully generated files in {STAGING_DIR}:")
for f in os.listdir(STAGING_DIR):
    fsize = os.path.getsize(os.path.join(STAGING_DIR, f))
    print(f"  - {f} ({fsize:,} bytes)")

# 8. Upload to Hugging Face
print(f"\nUploading enriched dataset to Hugging Face repository {REPO_ID}...")
api = HfApi()

# Delete deprecated redundant duplicate files if they exist in the remote repo
for redundant_file in ("data.csv", "data.json"):
    try:
        api.delete_file(path_in_repo=redundant_file, repo_id=REPO_ID, repo_type="dataset")
        print(f"Removed redundant file from remote repo: {redundant_file}")
    except Exception as e:
        pass

api.upload_folder(
    folder_path=STAGING_DIR,
    repo_id=REPO_ID,
    repo_type="dataset",
    commit_message="feat: configure multi-config dataset viewer, add provenance, methodology, and BibTeX citation"
)
print("Upload complete! Dataset is now live at: https://huggingface.co/datasets/" + REPO_ID)
