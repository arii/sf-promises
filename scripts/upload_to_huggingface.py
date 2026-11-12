#!/usr/bin/env python3
"""
Upload SF Promises database and datasets to Hugging Face Hub (onasafari/sf-promises)
"""

import os
import csv
import json
import sqlite3
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

# 1. Export promises.csv
csv_fields = [
    "promise_id",
    "impact_rank",
    "entity",
    "role",
    "entity_type",
    "category",
    "neighborhood",
    "promise_text",
    "verbatim_quote",
    "promised_date",
    "due_date",
    "opened_date",
    "verdict",
    "verdict_reason",
    "source_url",
    "source_tier",
    "source_hash",
    "relevance_score",
    "decided_at"
]

csv_path = os.path.join(STAGING_DIR, "promises.csv")
with open(csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=csv_fields)
    writer.writeheader()
    for p in promises:
        rel = p.get("relevance") or {}
        rel_score = rel.get("score") if isinstance(rel, dict) else None
        writer.writerow({
            "promise_id": p.get("promise_id", ""),
            "impact_rank": p.get("impact_rank") or p.get("display_no", ""),
            "entity": p.get("entity", ""),
            "role": p.get("role", ""),
            "entity_type": p.get("entity_type", ""),
            "category": p.get("category", ""),
            "neighborhood": p.get("neighborhood", ""),
            "promise_text": p.get("promise_text", ""),
            "verbatim_quote": p.get("verbatim_quote") or p.get("promise_text", ""),
            "promised_date": p.get("promised_date", ""),
            "due_date": p.get("due_date", ""),
            "opened_date": p.get("opened_date") or p.get("realized_date", ""),
            "verdict": p.get("verdict", ""),
            "verdict_reason": p.get("verdict_reason", ""),
            "source_url": p.get("source_url", ""),
            "source_tier": p.get("source_tier", ""),
            "source_hash": p.get("source_hash", ""),
            "relevance_score": rel_score if rel_score is not None else "",
            "decided_at": p.get("decided_at", "")
        })

# 2. Export quarantined.csv
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

# 3. Export JSON files
with open(os.path.join(STAGING_DIR, "promises.json"), "w", encoding="utf-8") as f:
    json.dump(promises, f, indent=2)

with open(os.path.join(STAGING_DIR, "data.json"), "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)

# 4. Create SQLite database promises.sqlite
sqlite_path = os.path.join(STAGING_DIR, "promises.sqlite")
if os.path.exists(sqlite_path):
    os.remove(sqlite_path)

con = sqlite3.connect(sqlite_path)
cur = con.cursor()

# Create promises table
cur.execute("""
CREATE TABLE promises (
    promise_id TEXT PRIMARY KEY,
    impact_rank INTEGER,
    entity TEXT,
    role TEXT,
    entity_type TEXT,
    category TEXT,
    neighborhood TEXT,
    promise_text TEXT,
    verbatim_quote TEXT,
    promised_date TEXT,
    due_date TEXT,
    opened_date TEXT,
    verdict TEXT,
    verdict_reason TEXT,
    source_url TEXT,
    source_tier TEXT,
    source_hash TEXT,
    relevance_score INTEGER,
    decided_at TEXT
)
""")

for p in promises:
    rel = p.get("relevance") or {}
    rel_score = rel.get("score") if isinstance(rel, dict) else None
    cur.execute("""
    INSERT INTO promises VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        p.get("promise_id", ""),
        p.get("impact_rank") or p.get("display_no", 0),
        p.get("entity", ""),
        p.get("role", ""),
        p.get("entity_type", ""),
        p.get("category", ""),
        p.get("neighborhood", ""),
        p.get("promise_text", ""),
        p.get("verbatim_quote") or p.get("promise_text", ""),
        p.get("promised_date", ""),
        p.get("due_date", ""),
        p.get("opened_date") or p.get("realized_date", ""),
        p.get("verdict", ""),
        p.get("verdict_reason", ""),
        p.get("source_url", ""),
        p.get("source_tier", ""),
        p.get("source_hash", ""),
        rel_score,
        p.get("decided_at", "")
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
    ("version", "2.0.0"),
    ("verified_commitments", str(len(promises))),
    ("quarantined_items", str(len(quarantined))),
    ("exported_at", meta.get("exported_at", "")),
    ("git_commit", meta.get("git_commit", ""))
])

con.commit()
con.close()

# 5. Create Dataset Card README.md
readme_path = os.path.join(STAGING_DIR, "README.md")
with open(readme_path, "w", encoding="utf-8") as f:
    f.write("""---
license: mit
task_categories:
- tabular-classification
- table-question-answering
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
size_categories:
- n<1K
pretty_name: SF Promises Public Ledger & Verification Database
configs:
- config_name: default
  data_files:
  - split: train
    path: promises.csv
---

# SF Promises — Public Commitments & Verification Ledger

Public commitments across San Francisco — from City Hall, SF Board of Supervisors, and SFO Airport to Chase Center and neighborhood streets — verified against cryptographically archived primary evidence.

Recipient of the **Best Use of Keenable** award at the Archil *"Agents Need Solid Ground"* Hackathon (Nov 10, 2026).

## Dataset Summary

- **Total Verified Commitments**: 54 tracked public promises across 9 civic domains.
- **Quarantine Registry**: 13 unverified, altered, or duplicate candidate promises caught and quarantined before reaching the public ledger.
- **Outcome Breakdown**: 25 Kept (46%), 10 In Progress (19%), 17 Broken (31%), 2 Undecided (4%).
- **Verification Integrity**: Every quote is pinned to a SHA-256 source hash and verified across dual-advocate sandboxes and deterministic code checks.

## Available Files

| File | Description |
|---|---|
| `promises.csv` | Primary tabular export of all 54 verified commitments |
| `quarantined.csv` | Registry of 13 quarantined items that failed verification checks |
| `promises.sqlite` | Complete SQLite relational database with `promises`, `quarantined`, and `metadata` tables |
| `promises.json` | Detailed structured JSON records including advocate findings and relevance breakdowns |
| `data.json` | Full application state bundle matching the live web explorer |

## Data Fields (`promises.csv`)

- `promise_id` *(string)*: Permanent identifier (e.g., `P02`, `SFO-01`)
- `impact_rank` *(integer)*: Civic impact & public debate rank (#1 to #54)
- `entity` *(string)*: Promising official, agency, airline, or team (e.g., *Mayor Daniel Lurie*, *SFO Airport*, *Golden State Valkyries*)
- `role` *(string)*: Speaker title or role
- `entity_type` *(string)*: `politicians`, `city_government`, `sports`, `companies`, or `culture`
- `category` *(string)*: Civic domain (`Civic Governance`, `Airport & Airlines`, `Transit & Streets`, `Housing & Neighborhoods`, `Sports`, `Culture & Music`, `Environment & Energy`, `Infrastructure & Tech`, `Bay Area & Regional`)
- `neighborhood` *(string)*: Specific SF neighborhood, corridor, or facility (e.g., *Tenderloin (822 Geary St)*, *Mission Bay (Chase Center)*)
- `promise_text` *(string)*: Extracted commitment text
- `verbatim_quote` *(string)*: Unabridged quote from official primary document
- `promised_date` *(string)*: Date promise was uttered or published (YYYY-MM-DD)
- `due_date` *(string)*: Deadline or target completion date (YYYY-MM-DD)
- `opened_date` *(string)*: Milestone realization or opening date if completed
- `verdict` *(string)*: Outcome status (`kept`, `in_progress`, `broken`, `undecided`)
- `verdict_reason` *(string)*: Plain-English factual rationale from arbitrator checks
- `source_url` *(string)*: URL of original document
- `source_tier` *(string)*: Source credibility tier (`Official`, `News`, `Reference`)
- `source_hash` *(string)*: SHA-256 cryptographic digest of saved primary document
- `relevance_score` *(integer)*: 0-8 score from the relevance quality gate

## Quickstart

### Python (pandas)

```python
import pandas as pd

df = pd.read_csv("https://huggingface.co/datasets/onasafari/sf-promises/raw/main/promises.csv")
print(f"Loaded {len(df)} commitments")
print(df['verdict'].value_counts())
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
df = pd.read_sql_query("SELECT entity, verdict, promise_text FROM promises WHERE category = 'Civic Governance'", con)
print(df)
```

### Hugging Face Datasets

```python
from datasets import load_dataset

dataset = load_dataset("onasafari/sf-promises")
print(dataset['train'][0])
```

## Explorer & Project Links

- **Live Explorer**: [https://arii.github.io/sf-promises/](https://arii.github.io/sf-promises/)
- **GitHub Repository**: [https://github.com/arii/sf-promises](https://github.com/arii/sf-promises)
""")

print(f"Successfully generated files in {STAGING_DIR}:")
for f in os.listdir(STAGING_DIR):
    fsize = os.path.getsize(os.path.join(STAGING_DIR, f))
    print(f"  - {f} ({fsize:,} bytes)")

# 6. Upload to Hugging Face
print(f"\nUploading to Hugging Face repository {REPO_ID}...")
api = HfApi()
api.upload_folder(
    folder_path=STAGING_DIR,
    repo_id=REPO_ID,
    repo_type="dataset",
    commit_message="feat: upload SF Promises database, sqlite export, csvs, and dataset card"
)
print("Upload complete! Dataset is now live at: https://huggingface.co/datasets/" + REPO_ID)
