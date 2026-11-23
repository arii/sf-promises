"""Stage and apply presentation-only media (issues #82, #83).

    python3 -m scripts.fetch_media stage-promises   # og:image/twitter:image from saved sources
    python3 -m scripts.fetch_media stage-entities   # curated Wikimedia Commons files per entity
    python3 -m scripts.fetch_media apply            # approved candidates -> docs/media + manifest

`stage-*` only write `<workspace>/staging/media_candidates.json` (status
"pending"). A person approves an entry by setting status "approved" and filling
license, license_url and credit. `apply` refuses anything unapproved, with an
empty license, or from a never-rehost source. Nothing here touches the database.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import httpx

from src import media
from src.workspace import workspace

EXPORT = Path(__file__).resolve().parent.parent / "docs" / "data.json"


def _candidates_path() -> Path:
    return workspace() / "staging" / "media_candidates.json"


def _client():
    return httpx.Client(headers={"User-Agent": media.USER_AGENT})


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["stage-promises", "stage-entities", "apply"])
    args = ap.parse_args(argv)
    path = _candidates_path()
    exported = json.loads(EXPORT.read_text(encoding="utf-8"))["promises"]
    try:
        with _client() as client:
            if args.command == "stage-promises":
                found = media.stage_promise_candidates(exported, workspace() / "sources", client, workspace() / "sources" / "media")
                keep = [c for c in media.load_candidates(path) if c.get("kind") != "promise"]
                media.write_candidates(path, keep + found)
                print(f"staged {len(found)} promise image candidates -> {path}")
            elif args.command == "stage-entities":
                # Curated exact Commons titles (config/media_entities.json); no fuzzy search.
                names = {p["entity_canonical_name"] for p in exported if p.get("entity_canonical_name")}
                found = media.stage_curated_entity_candidates(media.load_entity_config(), client, names)
                keep = [c for c in media.load_candidates(path) if c.get("kind") != "entity"]
                media.write_candidates(path, keep + found)
                print(f"staged {len(found)} entity image candidates -> {path}")
            else:
                written = media.apply_candidates(media.load_candidates(path), client)
                print(f"wrote {len(written)} files; re-run docs/export_data.py to refresh docs/data.json")
    except media.MediaError as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
