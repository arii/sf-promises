#!/usr/bin/env python3
"""Round 3 discovery: mine verbatim commitment sentences from saved, allowlisted pages.

No model calls. Keenable searches (actor x topic, commitment phrasing) produce page
leads, allowlisted pages are fetched and archived byte for byte, and sentences that
look like forward-looking commitments with a deadline are mined from the saved
text. A candidate's sentence is always an exact substring of the saved bytes, so
it can pass the audit's verbatim check. A candidate is a lead, not evidence.

Run (needs KEENABLE_API_KEY in the environment; the script never reads .env):
    python -m scripts.discovery_round --dry-run
    python -m scripts.discovery_round --workspace DIR --max-queries 200 --max-fetches 400
Then review the staging file and build the audit queue:
    python -m scripts.discovery_round --build-queue REVIEWED.json
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import re
import sys
import time
from collections import Counter
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from keenable import KeenableAPIError, KeenableConnectionError, KeenableRateLimitError  # noqa: E402

from scripts.build_discovery_queue import search_keywords  # noqa: E402
from src.discovery import fetch_and_archive  # noqa: E402
from src.discovery_config import search_options  # noqa: E402
from src.evidence import _primary_host, is_allowlisted_url, screen_saved_source  # noqa: E402
from src.sentences import (  # noqa: E402
    SENTENCE_CAP, _BULLETS, _is_line_break_boundary, _is_paragraph_break, _is_sentence_end,
)
from src.temporal import deadline_from_quote, screen_forward_looking  # noqa: E402
from src.workspace import workspace as default_workspace  # noqa: E402

CONFIG_PATH = REPO_ROOT / "config" / "discovery_round_3.json"
ID_PREFIX = "R3"
MIN_SENTENCE, MAX_SENTENCE = 40, SENTENCE_CAP
MAX_PER_PAGE = 3
RATE_LIMIT_STOP = 3  # consecutive 429s after the client's own retries
SEED_FILES = ("seeds/discovery_targets.json", "seeds/recovery_targets.json",
              "seeds/canonical_targets.json", "seeds/discovery_round_3_targets.json")
ROUND_GLOB = "data/discovery_round*.json"


# --------------------------------------------------------------------------- config

def load_config(path: Path = CONFIG_PATH) -> dict:
    cfg = json.loads(Path(path).read_text(encoding="utf-8"))
    topics = {t["id"] for t in cfg["topics"]}
    for actor in cfg["actors"]:
        unknown = set(actor["topics"]) - topics
        if unknown:
            raise ValueError(f"actor {actor['id']}: unknown topics {sorted(unknown)}")
    if len({a["id"] for a in cfg["actors"]}) != len(cfg["actors"]):
        raise ValueError("duplicate actor id")
    return cfg


# --------------------------------------------------------------------------- query plan

def make_windows(cfg: dict, *, as_of: date, recent_start=None, recent_end=None,
                 historical_start=None, historical_end=None) -> dict:
    w = cfg["windows"]
    return {
        "recent": {"after": recent_start or w["recent"]["default_start"],
                   "before": recent_end or as_of.isoformat(),
                   "years": [as_of.year + n for n in w["recent"]["years_ahead"]]},
        "historical": {"after": historical_start or w["historical"]["default_start"],
                       "before": historical_end or w["historical"]["default_end"],
                       "years": list(w["historical"]["years"])},
    }


def _actor_combos(actor: dict, templates: list, topics: dict, years: list, site_combos: int):
    """(topic, template) pairs for one actor, topic coverage first, expanded to queries."""
    ids = actor["topics"]
    combos = [(ids[i], (i + r) % len(templates)) for r in range(len(templates))
              for i in range(len(ids))]
    queries = []
    for n, (topic_id, tidx) in enumerate(combos):
        topic = topics[topic_id]
        text = templates[tidx].format(actor=actor["name"], noun=topic["noun"],
                                      verb=topic["verb"], year=years[n % len(years)])
        base = {"actor_id": actor["id"], "topic_id": topic_id, "template": tidx, "text": text}
        queries.append({**base, "site": None})
        if n < site_combos:
            queries.extend({**base, "site": domain} for domain in actor.get("domains", []))
    return queries


def build_query_plan(cfg: dict, windows: dict, max_queries: int) -> list:
    """Deterministic plan: actors interleaved, the two windows alternating, capped."""
    topics = {t["id"]: t for t in cfg["topics"]}
    per_window = {}
    for name, window in windows.items():
        lists = [_actor_combos(a, cfg["templates"], topics, window["years"],
                               cfg.get("site_combos_per_actor", 6)) for a in cfg["actors"]]
        merged = []
        for position in range(max((len(q) for q in lists), default=0)):
            merged.extend(q[position] for q in lists if position < len(q))
        per_window[name] = [{**q, "window": name, "after": window["after"],
                             "before": window["before"]} for q in merged]
    plan = []
    names = list(per_window)
    for position in range(max((len(v) for v in per_window.values()), default=0)):
        for name in names:
            if position < len(per_window[name]):
                plan.append(per_window[name][position])
    return plan[:max(0, max_queries)]


# --------------------------------------------------------------------------- sentences

_COMMIT_CASED = re.compile(r"\b(?:will|shall)\b")
_COMMIT = re.compile(
    r"\b(?:plans?\s+to|planned\s+to|expected\s+to|(?:scheduled|slated|set)\s+to|"
    r"aims?\s+to|commits?\s+to|committed\s+to|pledged|pledges|goals?\s+of|targets?\s+of|"
    r"anticipated\s+to)\b", re.IGNORECASE)
_YEAR = re.compile(r"\b20(?:1[6-9]|2\d|3\d|40)\b")
_NUMBER_WORDS = r"(?:\d{1,3}|one|two|three|four|five|six|seven|eight|nine|ten|twelve)"
_DEADLINE_OTHER = re.compile(
    rf"\bby\s+(?:the\s+)?end\s+of\b|\bfiscal\s+year\b|\bFY\s?\d{{2}}\b|"
    rf"\bwithin\s+{_NUMBER_WORDS}\s+(?:years?|months?)\b", re.IGNORECASE)
_SF = re.compile(r"\bSan Francisco\b|\bSF\b|\bSFO\b|\bSFMTA\b|\bSFPUC\b|\bSFUSD\b|\bSFPD\b")


def split_sentences(text: str) -> list:
    """(start, end) spans; text[start:end] is an exact substring, bullets/space trimmed."""
    spans, start, i, n = [], 0, 0, len(text)
    trim = _BULLETS + "#>"

    def close(a, b):
        while a < b and (text[a].isspace() or text[a] in trim):
            a += 1
        while b > a and text[b - 1].isspace():
            b -= 1
        if a < b:
            spans.append((a, b))

    while i < n:
        ch = text[i]
        if ch == "\n" and text[i:i + 2] == "\n\n" and _is_paragraph_break(text, i):
            close(start, i)
            start = i = i + 2
            continue
        if ch in ".!?" and _is_sentence_end(text, i):
            close(start, i + 1)
            start = i = i + 1
            continue
        if ch == "\n" and _is_line_break_boundary(text, i):
            close(start, i)
            start = i = i + 1
            continue
        i += 1
    close(start, n)
    return spans


def _alias_pattern(aliases) -> re.Pattern | None:
    names = sorted({a for a in aliases if a}, key=len, reverse=True)
    if not names:
        return None
    return re.compile(r"(?<![A-Za-z0-9])(?:" + "|".join(re.escape(a) for a in names) + r")(?![A-Za-z0-9])")


def actor_matcher(cfg: dict):
    """Returns find(text) -> actor or None, matching the longest alias first."""
    pairs = sorted(((alias, actor) for actor in cfg["actors"]
                    for alias in [*actor.get("aliases", []), actor["name"]]),
                   key=lambda p: len(p[0]), reverse=True)
    by_alias = {}
    for alias, actor in pairs:
        by_alias.setdefault(alias, actor)
    pattern = _alias_pattern(by_alias)

    def find(text: str):
        match = pattern.search(text) if pattern else None
        return by_alias[match.group(0)] if match else None
    return find


def published_date(value) -> date | None:
    match = re.match(r"(\d{4})-(\d{2})-(\d{2})", value or "")
    if not match:
        return None
    try:
        return date(*map(int, match.groups()))
    except ValueError:
        return None


def reject_reason(sentence: str, *, published: date | None) -> str | None:
    """Why a sentence is not a forward-looking dated commitment, or None if it passes."""
    if not MIN_SENTENCE <= len(sentence) <= MAX_SENTENCE:
        return "length"
    if sentence.endswith("?"):
        return "question"
    if not (_COMMIT_CASED.search(sentence) or _COMMIT.search(sentence)):
        return "no_commitment_verb"
    years = [int(y) for y in _YEAR.findall(sentence)]
    if not (years or _DEADLINE_OTHER.search(sentence)):
        return "no_deadline_signal"
    if screen_forward_looking(sentence):
        return "retrospective_wording"
    if published and years and max(years) < published.year:
        return "deadline_before_publication"
    return None


def mine_page(text: str, *, title: str = "", published: str | None = None, tier: str = "TIER2_NEWS",
              find_actor=lambda _t: None, query_actor: dict | None = None) -> list:
    """Scored candidate sentences for one saved page, best first. Each one is asserted
    to be an exact substring of ``text``."""
    pub = published_date(published)
    lede = f"{title}\n{text[:600]}"
    page_names_sf = bool(_SF.search(lede) or find_actor(lede))
    spans = split_sentences(text)
    found = []
    for idx, (a, b) in enumerate(spans):
        sentence = text[a:b]
        if reject_reason(sentence, published=pub):
            continue
        sentence_actor = find_actor(sentence)
        if not (_SF.search(sentence) or sentence_actor or page_names_sf):
            continue
        assert text[a:b] == sentence and sentence in text  # verbatim by construction
        deadline = deadline_from_quote(sentence, published=pub, promised=pub)
        score = (1 * bool(re.search(r"\d", sentence)) + 2 * bool(deadline)
                 + 1 * bool(re.search(r"\bby\b[^.]{0,40}\b20\d\d\b", sentence))
                 + 2 * bool(sentence_actor or _SF.search(sentence))
                 + 2 * (tier == "TIER1_GOV"))
        actor = sentence_actor or query_actor
        found.append({
            "sentence": sentence, "span": [a, b], "score": score,
            "deadline_guess": deadline.isoformat() if deadline else None,
            "actor_id": actor["id"] if actor else None,
            "actor": (actor.get("entity") or actor["name"]) if actor else None,
            "actor_in_sentence": bool(sentence_actor or _SF.search(sentence)),
            "context_before": text[spans[idx - 1][0]:spans[idx - 1][1]] if idx else "",
            "context_after": text[spans[idx + 1][0]:spans[idx + 1][1]] if idx + 1 < len(spans) else "",
        })
    found.sort(key=lambda c: (-c["score"], c["span"][0]))
    return found


# --------------------------------------------------------------------------- dedupe

def normalize(text: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).split())


def canonical_url(url: str) -> str:
    parts = urlsplit(url or "")
    host = (parts.hostname or "").lower().removeprefix("www.")
    return f"{host}{parts.path.rstrip('/')}" + (f"?{parts.query}" if parts.query else "")


def _overlaps(a: str, b: str) -> bool:
    if not a or not b:
        return False
    if a == b:
        return True
    short, long_ = sorted((a, b), key=len)
    return len(short) >= 60 and short in long_


def _jaccard(a: str, b: str) -> float:
    sa, sb = set(a.split()), set(b.split())
    return len(sa & sb) / len(sa | sb) if sa | sb else 0.0


def load_existing(root: Path = REPO_ROOT) -> dict:
    """Texts, URLs and ids already in the dataset, seeds and earlier rounds."""
    texts, urls, ids = [], set(), set()
    data = root / "docs" / "data.json"
    if data.exists():
        for p in json.loads(data.read_text(encoding="utf-8")).get("promises", []):
            texts += [p.get("promise_text"), p.get("verbatim_quote")]
            if p.get("source_url"):
                urls.add(canonical_url(p["source_url"]))
            ids.add(p.get("promise_id"))
    for name in SEED_FILES:
        path = root / name
        if path.exists():
            for lead in json.loads(path.read_text(encoding="utf-8")).get("leads", []):
                texts.append(lead.get("promise_text"))
                if lead.get("source_url"):
                    urls.add(canonical_url(lead["source_url"]))
                ids.add(lead.get("promise_id"))
    for path in sorted(root.glob(ROUND_GLOB)):
        try:
            candidates = json.loads(path.read_text(encoding="utf-8")).get("candidates", [])
        except (OSError, ValueError, AttributeError):
            continue
        for item in candidates:
            if isinstance(item, dict):
                texts.append(item.get("verbatim_quote"))
                ids.add(item.get("candidate_id"))
    return {"texts": [t for t in map(normalize, texts) if t], "urls": urls,
            "ids": {i for i in ids if i}}


class Deduper:
    """Rejects a candidate that repeats the dataset, an earlier candidate, or its URL."""

    def __init__(self, existing: dict):
        self.existing_texts = existing["texts"]
        self.existing_urls = existing["urls"]
        self.kept = []  # (norm, canonical_url)
        self.reasons = Counter()

    def url_known(self, url: str) -> bool:
        return canonical_url(url) in self.existing_urls

    def admit(self, sentence: str, url: str) -> str | None:
        """None and the candidate is recorded, or the rejection reason."""
        norm, curl = normalize(sentence), canonical_url(url)
        reason = None
        if curl in self.existing_urls:
            reason = "existing_url"
        elif any(_overlaps(norm, t) for t in self.existing_texts):
            reason = "existing_text"
        else:
            for other, other_url in self.kept:
                if _overlaps(norm, other):
                    reason = "duplicate_text"
                    break
                if other_url == curl and _jaccard(norm, other) >= 0.5:
                    reason = "duplicate_same_url"
                    break
        if reason:
            self.reasons[reason] += 1
            return reason
        self.kept.append((norm, curl))
        return None


# --------------------------------------------------------------------------- run

def page_lead_id(url: str) -> str:
    return f"{ID_PREFIX}-{hashlib.sha256(url.encode('utf-8')).hexdigest()[:10]}"


def _tier(url: str) -> str:
    return "TIER1_GOV" if _primary_host(url) else "TIER2_NEWS"


async def run_search(client, plan, cfg, counts, *, options=None):
    """Execute the plan; returns {url: lead}. Stops after repeated rate limits."""
    options = options or search_options("origin", max_results=cfg.get("max_results", 50))
    leads, consecutive = {}, 0
    for q in plan:
        kwargs = {**options, "published_after": q["after"], "published_before": q["before"]}
        if q["site"]:
            kwargs["site"] = q["site"]
        counts["searches"] += 1
        try:
            response = await client.search(q["text"], **kwargs)
            consecutive = 0
        except KeenableRateLimitError:
            counts["search_errors"] += 1
            consecutive += 1
            if consecutive >= RATE_LIMIT_STOP:
                counts["stopped_rate_limited"] = True
                break
            continue
        except (KeenableAPIError, KeenableConnectionError):
            counts["search_errors"] += 1
            continue
        for result in getattr(response, "results", None) or []:
            url = getattr(result, "url", None)
            if not isinstance(url, str) or not url:
                continue
            counts["results"] += 1
            leads.setdefault(url, {
                "url": url, "title": getattr(result, "title", "") or "",
                "published_at": getattr(result, "published_at", None),
                "acquired_at": getattr(result, "acquired_at", None),
                "actor_id": q["actor_id"], "topic_id": q["topic_id"],
                "window": q["window"], "query": q["text"],
            })
    return leads


def filter_leads(leads: dict, counts: dict) -> list:
    """Allowlisted leads only, official hosts first, otherwise in discovery order."""
    kept, hosts = [], Counter()
    for url, lead in leads.items():
        if is_allowlisted_url(url):
            kept.append(lead)
        else:
            hosts[urlsplit(url).hostname or "?"] += 1
    counts["urls_unique"] = len(leads)
    counts["urls_allowlisted"] = len(kept)
    counts["urls_not_allowlisted"] = len(leads) - len(kept)
    kept.sort(key=lambda lead: 0 if _primary_host(lead["url"]) else 1)  # stable
    return kept, dict(hosts.most_common(25))


async def run_fetch(client, leads, root: Path, counts, *, max_fetches, domain_delay=1.0,
                    sleep=asyncio.sleep, clock=time.monotonic):
    """Fetch and archive sequentially, politely per host, up to the budget."""
    pages, last, consecutive = [], {}, 0
    for lead in leads:
        if counts["fetches"] >= max_fetches:
            counts["fetch_budget_exhausted"] = True
            break
        host = urlsplit(lead["url"]).hostname or ""
        wait = domain_delay - (clock() - last[host]) if host in last else 0
        if wait > 0:
            await sleep(wait)
        last[host] = clock()
        counts["fetches"] += 1
        lead_id = page_lead_id(lead["url"])
        try:
            saved = await fetch_and_archive(client, lead["url"], root, lead_id,
                                            acquired_at=lead.get("acquired_at"))
            consecutive = 0
        except KeenableRateLimitError:
            counts["fetch_blocked"] += 1
            consecutive += 1
            if consecutive >= RATE_LIMIT_STOP:
                counts["stopped_rate_limited"] = True
                break
            continue
        except (KeenableAPIError, KeenableConnectionError, ValueError) as exc:
            counts["fetch_blocked"] += 1
            counts["fetch_block_reasons"][str(exc)[:60] or type(exc).__name__] += 1
            continue
        counts["fetch_ok"] += 1
        pages.append({"lead": lead, "lead_id": lead_id, "saved": saved})
    return pages


def mine_pages(pages, cfg, root: Path, existing: dict, *, per_page=MAX_PER_PAGE) -> tuple:
    find_actor = actor_matcher(cfg)
    actors = {a["id"]: a for a in cfg["actors"]}
    topics = {t["id"]: t for t in cfg["topics"]}
    deduper = Deduper(existing)
    candidates, stats = [], Counter()
    for page in pages:
        saved, lead = page["saved"], page["lead"]
        text = Path(saved["path"]).read_text(encoding="utf-8")
        tier = _tier(saved["url"])
        if deduper.url_known(saved["url"]):
            stats["pages_existing_url"] += 1
            continue
        mined = mine_page(text, title=lead.get("title", ""), published=saved.get("published_at"),
                          tier=tier, find_actor=find_actor,
                          query_actor=actors.get(lead["actor_id"]))
        stats["sentences_mined"] += len(mined)
        taken = 0
        for item in mined:
            if taken >= per_page:
                break
            if deduper.admit(item["sentence"], saved["url"]):
                continue
            failures = screen_saved_source(
                root=root, promise_id=page["lead_id"], path=saved["path"], digest=saved["sha256"],
                quote=item["sentence"], url=saved["url"], source_tier=tier)
            if failures:
                stats["gate_failed"] += 1
                deduper.kept.pop()
                continue
            taken += 1
            candidates.append({
                "candidate_id": f"{page['lead_id']}-{taken}",
                "lead_id": page["lead_id"],
                "url": saved["url"], "requested_url": saved["requested_url"],
                "published_at": saved.get("published_at"), "fetched_at": saved["fetched_at"],
                "sha256": saved["sha256"],
                "saved_path": os.path.relpath(saved["path"], root.parent)
                if root.parent in Path(saved["path"]).parents else saved["path"],
                "source_tier": tier,
                "verbatim_quote": item["sentence"], "quote_verbatim": True, "gate_failures": [],
                "actor": item["actor"], "actor_in_sentence": item["actor_in_sentence"],
                "topic": topics[lead["topic_id"]]["id"], "window": lead["window"],
                "query": lead["query"], "page_title": lead.get("title", ""),
                "deadline_guess": item["deadline_guess"], "score": item["score"],
                "sentence_span": item["span"],
                "context_before": item["context_before"], "context_after": item["context_after"],
            })
    stats.update({f"dedupe_{k}": v for k, v in deduper.reasons.items()})
    candidates.sort(key=lambda c: (-c["score"], c["candidate_id"]))
    return candidates, dict(stats)


def new_counts() -> dict:
    return {"searches": 0, "search_errors": 0, "results": 0, "fetches": 0, "fetch_ok": 0,
            "fetch_blocked": 0, "fetch_block_reasons": Counter()}


async def run_round(client, cfg, *, windows, root: Path, max_queries=200, max_fetches=400,
                    domain_delay=1.0, as_of: date, existing=None, sleep=asyncio.sleep,
                    clock=time.monotonic):
    plan = build_query_plan(cfg, windows, max_queries)
    counts = new_counts()
    leads = await run_search(client, plan, cfg, counts)
    fetchable, hosts = filter_leads(leads, counts)
    pages = await run_fetch(client, fetchable, root, counts, max_fetches=max_fetches,
                            domain_delay=domain_delay, sleep=sleep, clock=clock)
    existing = existing if existing is not None else load_existing()
    candidates, stats = mine_pages(pages, cfg, root, existing)
    counts["fetch_block_reasons"] = dict(counts["fetch_block_reasons"])
    stamp = as_of.strftime("%Y%m%d")
    queries = {}
    for q in plan:
        queries.setdefault(q["window"], []).append(
            q["text"] + (f"  [site={q['site']}]" if q["site"] else ""))
    record = {
        "round_id": f"discovery-round-3-{stamp}",
        "as_of": as_of.isoformat(),
        "builds_on": "discovery-round-2-20261122 (data/discovery_round_2_20261122.json)",
        "method": ("scripts/discovery_round.py. Keenable search (src.keenable.RetryingKeenable, "
                   "search_options('origin'), max_results 50) over config/discovery_round_3.json "
                   "actor x topic commitment queries in two published-date windows produced page "
                   "leads only. Allowlisted pages were archived with src.discovery.fetch_and_archive "
                   "under per-URL lead ids. Sentences were mined deterministically (no model): "
                   "commitment verb + deadline signal + forward-looking screen + SF/actor named + "
                   "40-420 chars, top 3 per page, deduped against the dataset and seeds. Every "
                   "verbatim_quote is an exact substring of the saved bytes and passed "
                   "src.evidence.screen_saved_source. Saved bytes live in the workspace, not the repo."),
        "windows": windows,
        "keenable_counts": {k: v for k, v in counts.items()},
        "keenable_queries": queries,
        "non_allowlisted_hosts_top": hosts,
        "mining": stats,
        "candidates": [{k: v for k, v in c.items() if k not in ("context_before", "context_after")}
                       for c in candidates],
        "pipeline_notes": ["Candidates are leads; the v2 audit re-fetches and verifies each one.",
                           "promised_date for the queue is the page published date (day precision)."],
    }
    return record, candidates, counts


def review_document(record: dict, candidates: list) -> dict:
    return {
        "round_id": record["round_id"],
        "instructions": ("Set decision to 'accept' or 'reject' on each candidate (leave null to "
                         "skip). Accept only a sentence that states a real, future-facing San "
                         "Francisco commitment with a checkable outcome. Then run "
                         "python -m scripts.discovery_round --build-queue THIS_FILE."),
        "candidates": [{
            "candidate_id": c["candidate_id"], "decision": None, "note": "",
            "url": c["url"], "published_at": c["published_at"], "sha256": c["sha256"],
            "saved_path": c["saved_path"], "source_tier": c["source_tier"],
            "actor": c["actor"], "topic": c["topic"], "window": c["window"],
            "score": c["score"], "deadline_guess": c["deadline_guess"],
            "verbatim_quote": c["verbatim_quote"],
            "context_before": c["context_before"], "context_after": c["context_after"],
        } for c in candidates],
    }


# --------------------------------------------------------------------------- queue

ISO_DAY = re.compile(r"\d{4}-\d{2}-\d{2}")


def build_queue(reviewed: dict, existing: dict, *, sources_root: Path | None = None) -> dict:
    """Accepted candidates -> run_live queue (seeds/canonical_targets.json shape)."""
    leads, skipped, seen_ids = [], [], set()
    deduper = Deduper({"texts": existing["texts"], "urls": set(), "ids": existing["ids"]})
    for item in reviewed.get("candidates", []):
        cid = item.get("candidate_id")
        if item.get("decision") != "accept":
            continue

        def skip(reason):
            skipped.append({"promise_id": cid, "reason": reason})

        quote, url = item.get("verbatim_quote"), item.get("url")
        if not cid or not quote or not url:
            skip("missing_fields")
            continue
        if cid in existing["ids"] or cid in seen_ids:
            skip("id_collision")
            continue
        promised = (item.get("published_at") or "")[:10]
        if not ISO_DAY.fullmatch(promised) or published_date(promised) is None:
            skip("published_date_missing")
            continue
        due = item.get("deadline_guess") or None
        if due is not None and (not ISO_DAY.fullmatch(due) or due < promised):
            skip("deadline_before_promised_date")
            continue
        if sources_root is not None and item.get("saved_path"):
            saved = Path(sources_root).parent / item["saved_path"]
            if saved.exists() and quote not in saved.read_text(encoding="utf-8"):
                skip("quote_not_in_saved_bytes")
                continue
        reason = deduper.admit(quote, url)
        if reason:
            skip(reason)
            continue
        seen_ids.add(cid)
        entity = item.get("actor") or "San Francisco"
        keywords = search_keywords(url, entity, quote)
        if entity.lower() not in keywords.lower():
            keywords = f"{keywords} {entity}"
        leads.append({
            "promise_id": cid, "promise_text": quote, "entity": entity,
            "promised_date": promised, "due_date": due, "source_id": None,
            "source_url": url, "keywords": keywords,
        })
    return {"generated_from": reviewed.get("round_id", "discovery-round-3"),
            "leads": leads, "skipped": skipped}


# --------------------------------------------------------------------------- cli

def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--config", type=Path, default=CONFIG_PATH)
    p.add_argument("--workspace", type=Path, default=None,
                   help="defaults to SF_PROMISES_WORKSPACE (sources go in WORKSPACE/sources)")
    p.add_argument("--max-queries", type=int, default=200)
    p.add_argument("--max-fetches", type=int, default=400)
    p.add_argument("--recent-start")
    p.add_argument("--recent-end")
    p.add_argument("--historical-start")
    p.add_argument("--historical-end")
    p.add_argument("--domain-delay", type=float, default=1.0, help="seconds between fetches per host")
    p.add_argument("--as-of", type=date.fromisoformat, default=None)
    p.add_argument("--output", type=Path, default=None, help="round record (default data/discovery_round_3_<date>.json)")
    p.add_argument("--review-output", type=Path, default=None,
                   help="review file (default WORKSPACE/staging/discovery_round_3_review_<date>.json)")
    p.add_argument("--dry-run", action="store_true", help="print the query plan; no network")
    p.add_argument("--build-queue", type=Path, metavar="REVIEWED.json")
    p.add_argument("--queue-output", type=Path, default=Path("seeds/discovery_round_3_targets.json"))
    return p.parse_args(argv)


def _write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main(argv=None, *, client_factory=None) -> int:
    args = parse_args(argv)
    if args.max_queries < 0 or args.max_fetches < 0:
        print("budgets must be non-negative", file=sys.stderr)
        return 2
    if args.build_queue:
        reviewed = json.loads(args.build_queue.read_text(encoding="utf-8"))
        workspace = args.workspace or default_workspace()
        queue = build_queue(reviewed, load_existing(), sources_root=workspace / "sources")
        _write_json(args.queue_output, queue)
        print(f"{args.queue_output}: {len(queue['leads'])} leads, {len(queue['skipped'])} skipped")
        return 0

    cfg = load_config(args.config)
    as_of = args.as_of or date.today()
    windows = make_windows(cfg, as_of=as_of, recent_start=args.recent_start, recent_end=args.recent_end,
                           historical_start=args.historical_start, historical_end=args.historical_end)
    if args.dry_run:
        plan = build_query_plan(cfg, windows, args.max_queries)
        by_window = Counter(q["window"] for q in plan)
        for q in plan[:20]:
            print(f"[{q['window']}] {q['text']}" + (f"  site={q['site']}" if q["site"] else ""))
        print(f"planned searches: {len(plan)} {dict(by_window)} (fetch budget {args.max_fetches})")
        return 0

    workspace = (args.workspace or default_workspace())
    root = workspace / "sources"
    stamp = as_of.strftime("%Y%m%d")
    output = args.output or REPO_ROOT / "data" / f"discovery_round_3_{stamp}.json"
    review_output = args.review_output or workspace / "staging" / f"discovery_round_3_review_{stamp}.json"

    async def go():
        if client_factory is not None:
            client = client_factory()
        else:
            from src.keenable import RetryingKeenable
            key = os.environ.get("KEENABLE_API_KEY")
            if not key:
                raise SystemExit("KEENABLE_API_KEY is not set in the environment")
            client = RetryingKeenable(api_key=key)
        async with client:
            return await run_round(client, cfg, windows=windows, root=root,
                                   max_queries=args.max_queries, max_fetches=args.max_fetches,
                                   domain_delay=args.domain_delay, as_of=as_of)

    record, candidates, counts = asyncio.run(go())
    _write_json(output, record)
    _write_json(review_output, review_document(record, candidates))
    print(f"keenable searches: {counts['searches']} (errors {counts['search_errors']}); "
          f"fetches: {counts['fetches']} (ok {counts['fetch_ok']}, blocked {counts['fetch_blocked']})")
    print(f"urls: {counts['urls_unique']} unique, {counts['urls_allowlisted']} allowlisted; "
          f"candidates: {len(candidates)}")
    print(f"record: {output}\nreview: {review_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
