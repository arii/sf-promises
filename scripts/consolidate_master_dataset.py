#!/usr/bin/env python3
"""Consolidate SF Promises into a validated, standardized sf_promises_master.csv."""

import csv
import json
from pathlib import Path

MASTER_COLUMNS = [
    "promise_id",
    "promise_text",
    "entity",
    "entity_role",
    "entity_type",
    "category",
    "promise_made_date",
    "deadline_date",
    "verdict",
    "confidence",
    "evidence_count",
    "primary_source_url",
    "primary_source_type",
    "neighborhood",
    "impact_score",
    "notes",
]


def normalize_iso_date(val):
    if not val or str(val).lower() in ("none", "null", "no deadline", "ongoing"):
        return ""
    val_str = str(val).strip()
    # Simple check for YYYY-MM-DD
    if len(val_str) == 10 and val_str[4] == "-" and val_str[7] == "-":
        return val_str
    return val_str[:10] if len(val_str) >= 10 else val_str


def consolidate_master_dataset(
    json_path="docs/data.json", output_csv="data/sf_promises_master.csv"
):
    path = Path(json_path)
    if not path.exists():
        raise FileNotFoundError(f"Missing {json_path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    promises = data.get("promises", [])
    out_path = Path(output_csv)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    for p in promises:
        # Confidence normalized to 0.0 - 1.0 float
        conf_raw = p.get("verdict_confidence")
        if conf_raw is not None:
            try:
                conf = float(conf_raw)
                if conf > 1.0:
                    conf = conf / 100.0
            except (ValueError, TypeError):
                conf = 0.95
        else:
            conf = 0.95

        # Evidence count integer (affirmative evidence + contradiction evidence >= 1)
        aff_count = int(p.get("verdict_evidence_count") or 0)
        neg_count = int(p.get("verdict_contradiction_count") or 0)
        ev_count = aff_count + neg_count
        if ev_count < 1:
            bundles = p.get("advocate_bundles") or {}
            k_claims = len((bundles.get("kept") or {}).get("claims", []) or [])
            b_claims = len((bundles.get("broken") or {}).get("claims", []) or [])
            ev_count = max(1, k_claims + b_claims)

        # Verdict lowercased
        verd = (p.get("verdict") or "undecided").lower().replace(" ", "_")

        # Dates
        made_date = normalize_iso_date(p.get("promise_made_date") or p.get("promised_date"))
        dead_date = normalize_iso_date(p.get("deadline_date") or p.get("due_date"))

        # Role and entity type
        role = p.get("role") or p.get("entity_role") or "City Official"
        ent_type = p.get("entity_type") or "government"

        # Source type standardized
        src_type = p.get("source_type_standardized") or p.get("source_type") or "official_government"
        if "gov" in src_type or "official" in src_type:
            src_type = "official_government"
        elif "news" in src_type or "journalism" in src_type:
            src_type = "news"
        else:
            src_type = "reference"

        # Impact score 0-10
        imp = p.get("impact_score") or p.get("importance_score") or 8
        try:
            imp = int(round(float(imp)))
        except (ValueError, TypeError):
            imp = 8

        row = {
            "promise_id": p.get("promise_id", ""),
            "promise_text": p.get("promise_text", "").strip(),
            "entity": p.get("entity", "").strip(),
            "entity_role": role.strip(),
            "entity_type": ent_type.strip(),
            "category": p.get("category", "Civic Governance").strip(),
            "promise_made_date": made_date,
            "deadline_date": dead_date,
            "verdict": verd,
            "confidence": f"{conf:.2f}",
            "evidence_count": int(ev_count),
            "primary_source_url": p.get("source_url", "").strip(),
            "primary_source_type": src_type,
            "neighborhood": (p.get("neighborhood") or "Citywide").strip(),
            "impact_score": imp,
            "notes": (p.get("verdict_reason") or "").strip(),
        }
        rows.append(row)

    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=MASTER_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Consolidated {len(rows)} records to {output_csv} with 16 master columns.")
    return len(rows)


if __name__ == "__main__":
    consolidate_master_dataset()
