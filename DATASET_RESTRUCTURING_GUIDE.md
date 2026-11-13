# Dataset Restructuring Guide: Standardizing SF Promises for Adaption

This document outlines the standard schema, conversion rules, and consolidation steps for the SF Promises dataset to ensure full compatibility with Adaption and data visualization tools.

---

## 1. Problem Statement & Root Cause

**Issue:** Inconsistent column structures across raw and staged files (e.g., missing `neighborhood`, `confidence` stored as percentages vs. decimals, disparate column names).  
**Solution:** Enforce a strict master schema across all promise records, consolidate into a single validated `sf_promises_master.csv`, and verify identical column headers with zero missing columns.

---

## 2. Master Column Schema (16 Required Columns)

Every row in `sf_promises_master.csv` must include the following 16 columns in this exact order:

| # | Column Name | Type | Description | Example |
|---|---|---|---|---|
| 1 | `promise_id` | string | Unique commitment identifier | `P02`, `SFO-01` |
| 2 | `promise_text` | string | Full verbatim quote or pledge text | `"That's exactly what this 24/7..."` |
| 3 | `entity` | string | Individual or organization who promised | `Daniel Lurie`, `San Francisco International Airport` |
| 4 | `entity_role` | string | Title or operational role | `Mayor`, `Airport Operator` |
| 5 | `entity_type` | string | Sector taxonomy | `government`, `corporate`, `civic` |
| 6 | `category` | string | City policy/civic category | `Public Safety`, `Transit & Infrastructure` |
| 7 | `promise_made_date` | string | Date promise was uttered/published (`YYYY-MM-DD`) | `2024-01-16` |
| 8 | `deadline_date` | string | Due date or deadline (`YYYY-MM-DD` or empty) | `2025-06-30` |
| 9 | `verdict` | string | Rubric outcome (`kept`, `broken`, `in_progress`, `undecided`) | `kept` |
| 10 | `confidence` | float | Arbitrator confidence score (`0.00` to `1.00`) | `0.98` |
| 11 | `evidence_count` | integer | Number of verified evidence ledger entries | `3` |
| 12 | `primary_source_url` | string | URL of origin public record or press release | `https://sf.gov/news/...` |
| 13 | `primary_source_type` | string | Evidence tier (`official_government`, `news`, `reference`) | `official_government` |
| 14 | `neighborhood` | string | SF neighborhood or `Citywide` | `Tenderloin`, `Citywide` |
| 15 | `impact_score` | integer | Civic significance rank/score (`0` to `10`) | `9` |
| 16 | `notes` | string | Plain-English verdict explanation and outcome context | `Opened on schedule April 2025.` |

---

## 3. Data Transformation & Normalization Rules

1. **Dates**: Standardize all dates to ISO 8601 (`YYYY-MM-DD`). Never use `MM/DD/YYYY` or Unix epochs. If unknown or open-ended deadline, use empty string `""`.
2. **Confidence**: Standardize confidence to a `0.00` – `1.00` float scale. If input was percentage (`> 1.0`), divide by 100.
3. **Empty Values**: Use empty string `""` in CSV (never string `"null"`, `"undefined"`, or `"NaN"`).
4. **Column Naming**: Lowercase with underscores (`promise_text`, not `Promise Text`).
5. **No Extra Index Columns**: Always export with `index=False`.

---

## 4. Master Consolidation & Export Code

Run the automated consolidation script:

```bash
python3 scripts/consolidate_master_dataset.py
```

Or via pandas:

```python
import pandas as pd

# Load master database or staging files
df = pd.read_csv('data/sf_promises_master.csv')

# Verify column count and missing headers
master_columns = [
    'promise_id', 'promise_text', 'entity', 'entity_role', 'entity_type',
    'category', 'promise_made_date', 'deadline_date', 'verdict', 'confidence',
    'evidence_count', 'primary_source_url', 'primary_source_type', 
    'neighborhood', 'impact_score', 'notes'
]

assert list(df.columns) == master_columns, "Column schema mismatch!"
assert len(df) == 54, f"Expected 54 records, got {len(df)}"
print("Validation passed: sf_promises_master.csv conforms to master schema.")
```

---

## 5. Verification Checklist

- [x] All 54 verified commitments consolidated into `data/sf_promises_master.csv`.
- [x] Master file has identical 16 columns across all rows in exact order.
- [x] Zero missing columns in any row.
- [x] Dates formatted as ISO `YYYY-MM-DD`.
- [x] Confidence scaled `0.00` - `1.00`.
- [x] No `Unnamed: 0` or pandas index columns.
- [x] Verified column count matches schema exactly (`len(df.columns) == 16`).
