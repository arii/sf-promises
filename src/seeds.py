"""Turn a static snapshot into unverified discovery leads, never evidence."""

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path


def build_leads(snapshot):
    records = snapshot.get("promises")
    if not isinstance(records, list):
        raise ValueError("Snapshot must contain a promises list")
    leads = []
    seen = set()
    texts = defaultdict(list)
    sources = defaultdict(list)
    fields = ("promise_id", "promise_text", "entity", "promised_date",
              "due_date", "source_id", "source_url")
    for row in records:
        if not isinstance(row, dict):
            raise ValueError("Snapshot promise must be an object")
        promise_id = row.get("promise_id")
        if (not isinstance(promise_id, str) or not promise_id.strip()
                or promise_id != promise_id.strip() or promise_id in seen):
            raise ValueError("Snapshot promise IDs must be unique nonempty strings")
        seen.add(promise_id)
        leads.append({key: row.get(key) for key in fields})
        text = row.get("promise_text")
        if isinstance(text, str) and text.strip():
            texts[" ".join(text.split()).casefold()].append(promise_id)
        source_id = row.get("source_id")
        if isinstance(source_id, str) and source_id.strip():
            sources[source_id].append(promise_id)
    return {
        "discovery_only": True,
        "leads": leads,
        "duplicate_text_groups": [group for group in texts.values() if len(group) > 1],
        "shared_source_groups": [group for group in sources.values() if len(group) > 1],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    raw = args.snapshot.read_bytes()
    result = build_leads(json.loads(raw))
    result["snapshot_path"] = str(args.snapshot)
    result["snapshot_sha256"] = hashlib.sha256(raw).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as file:
        json.dump(result, file, ensure_ascii=False, indent=2)
        file.write("\n")


if __name__ == "__main__":
    main()
