#!/usr/bin/env python3
"""
CLI tool for searching civic commitments and primary sources using Keenable.
Provides time-bounded searching, allowlist verification, and relevance scoring.

Usage:
    python -m src.cli_search --topic "SFO runway" --limit 5
    python -m src.cli_search --query "SFO Runway 28L reopen" --after 2024-01-01 --before 2024-07-01
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

from src.evidence import is_allowlisted_url
from src.keenable import RetryingKeenable


def _load_env_if_needed():
    if not os.environ.get("KEENABLE_API_KEY") and Path(".env").exists():
        for line in Path(".env").read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


async def search_keenable(query: str, after: str = None, before: str = None, limit: int = 5):
    _load_env_if_needed()
    api_key = os.environ.get("KEENABLE_API_KEY")
    if not api_key:
        print("Error: KEENABLE_API_KEY environment variable is required.", file=sys.stderr)
        return []

    client = RetryingKeenable(api_key=api_key)
    kwargs = {"max_results": limit}
    if after:
        kwargs["published_after"] = after
    if before:
        kwargs["published_before"] = before

    print(f"Searching Keenable for: {query!r} (after={after}, before={before}, limit={limit})...")
    try:
        response = await client.search(query, **kwargs)
        results = getattr(response, "results", []) or []
        leads = []
        for r in results:
            url = getattr(r, "url", "")
            title = getattr(r, "title", "")
            pub = getattr(r, "published_at", None)
            snippet = getattr(r, "snippet", "") or getattr(r, "content", "")[:200]
            leads.append({
                "title": title,
                "url": url,
                "published_at": pub,
                "allowlisted": is_allowlisted_url(url),
                "snippet": snippet
            })
        return leads
    except Exception as e:
        print(f"Keenable search error: {e}", file=sys.stderr)
        return []
    finally:
        await client._http.aclose()


def main():
    parser = argparse.ArgumentParser(description="Search civic promises on Keenable.")
    parser.add_argument("--query", "-q", type=str, help="Search query string")
    parser.add_argument("--topic", "-t", type=str, help="Search topic (e.g. 'SFO runway construction')")
    parser.add_argument("--after", type=str, default=None, help="Published after date (YYYY-MM-DD)")
    parser.add_argument("--before", type=str, default=None, help="Published before date (YYYY-MM-DD)")
    parser.add_argument("--limit", "-n", type=int, default=5, help="Maximum number of leads (default: 5)")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")

    args = parser.parse_args()
    q = args.query or args.topic
    if not q:
        parser.print_help()
        sys.exit(1)

    leads = asyncio.run(search_keenable(q, after=args.after, before=args.before, limit=args.limit))

    if args.json:
        print(json.dumps(leads, indent=2))
        return

    print(f"\nFound {len(leads)} leads:")
    for idx, lead in enumerate(leads, 1):
        status = "ALLOWLISTED" if lead["allowlisted"] else "UNLISTED"
        print(f"\n[{idx}] {lead['title']}")
        print(f"    URL: [{status}] {lead['url']}")
        print(f"    Date: {lead['published_at'] or 'Unknown'}")
        if lead["snippet"]:
            print(f"    Snippet: {lead['snippet'][:150]}...")


if __name__ == "__main__":
    main()
