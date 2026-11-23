"""Build a run_live lead queue from qualified intake candidates.

Reads data/intake_candidate_register.json and writes a queue file in the
seeds/canonical_targets.json shape ({"leads": [...]}) for
`python -m src.run_live --queue <file> --candidate-batch ...`.

Only qualified candidates with a day-precision promised date are queued; the
rest are listed under "skipped" with a reason. Where a discovery round
recorded a quote checked against saved bytes, that quote is the
promise_text; otherwise the register statement preview is used and the audit
re-checks it against freshly archived bytes. A lead is not evidence.

Usage: python3 scripts/build_discovery_queue.py [--output seeds/discovery_targets.json]
"""

import argparse
import hashlib
import json
import re
from urllib.parse import unquote
from pathlib import Path

REGISTER = Path("data/intake_candidate_register.json")
ROUNDS = (Path("data/discovery_round_20261122.json"), Path("data/discovery_round_2_20261122.json"))
ISO_DAY = re.compile(r"\d{4}-\d{2}-\d{2}")
STOP = {
    "the", "and", "for", "with", "from", "that", "this", "will", "more", "than",
    "news", "press", "release", "releases", "about", "into", "over", "under",
    "mayor", "celebrates", "announces", "launches", "new", "san", "francisco",
    "html", "aspx", "php", "pdf", "index", "www", "https", "http", "page", "default",
    "sites", "files", "documents", "document", "article", "articles", "blog", "blogs",
}


def search_keywords(url, entity, text, limit=6):
    """Search terms from the source URL slug, falling back to the quote.

    discover_and_archive otherwise uses the first long words of the quote,
    which for short quotes ("Construction is slated to begin...") retrieves
    unrelated pages from other cities.
    """
    path = unquote(re.sub(r"^https?://[^/]+", "", url or ""))
    words = [w for w in re.split(r"[^A-Za-z0-9]+", path) if len(w) > 2 and not w.isdigit()]
    words = [w for w in words if w.lower() not in STOP]
    if len(words) < 3:
        words += [w for w in re.findall(r"[A-Za-z][A-Za-z0-9'-]{3,}", text) if w.lower() not in STOP]
    seen, picked = set(), []
    for word in words:
        if word.lower() not in seen:
            seen.add(word.lower())
            picked.append(word)
    return " ".join(["San Francisco", *picked[:limit]])


def build(register=REGISTER, rounds=ROUNDS):
    raw = register.read_bytes()
    quotes = {}
    for path in rounds:
        if path.exists():
            for item in json.loads(path.read_text(encoding="utf-8"))["candidates"]:
                if item.get("quote_verbatim") and item.get("verbatim_quote"):
                    quotes[item["candidate_id"]] = (item["verbatim_quote"], item.get("url"))
    leads, skipped = [], []
    for item in json.loads(raw)["candidates"]:
        cid = item["candidate_id"]
        if item["qualification_status"] != "qualified":
            continue
        if not ISO_DAY.fullmatch(item.get("promised_date") or ""):
            skipped.append({"promise_id": cid, "reason": "promised_date not day-precision"})
            continue
        quote, url = quotes.get(cid, (item["statement_preview"], item["source_url"]))
        leads.append({
            "promise_id": cid,
            "promise_text": quote,
            "entity": item["entity"],
            "promised_date": item["promised_date"],
            "due_date": item["due_date"] or None,
            "source_id": None,
            "source_url": url or item["source_url"],
            "keywords": search_keywords(url or item["source_url"], item["entity"],
                                        item["statement_preview"]),
        })
    if len({lead["promise_id"] for lead in leads}) != len(leads):
        raise ValueError("Duplicate candidate_id in register")
    return {
        "generated_from": str(register),
        "register_sha256": hashlib.sha256(raw).hexdigest(),
        "leads": leads,
        "skipped": skipped,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--output", type=Path, default=Path("seeds/discovery_targets.json"))
    args = parser.parse_args()
    queue = build()
    args.output.write_text(json.dumps(queue, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{args.output}: {len(queue['leads'])} leads, {len(queue['skipped'])} skipped")


if __name__ == "__main__":
    main()
