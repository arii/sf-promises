"""Discovery-funnel and quarantine-reason summaries (D3 measurement).

Pure aggregation over counts and rows supplied by callers: the sourcing
pipeline's intake register, the SQLite tables, and the exported snapshot.
Nothing here gates anything — these summaries only make the existing hardest
filters visible.

Funnel stages, in flow order. Each stage is tagged with the universe that can
count it, so conversion rates are only computed between stages drawn from the
same cohort (mixing the intake register's candidate cohort with the database's
record cohort would produce nonsense ratios):

- ``leads_encountered`` (intake register): candidate rows the intake ledger saw.
- ``sources_archived`` (database): archived source documents.
- ``qualified`` (intake register): candidates that passed intake qualification.
- ``screened`` (database): distinct records that entered the verification lane.
- ``published`` (database): rows in the promises table.
- ``quarantined`` (database): rows in the quarantined table.
"""

from __future__ import annotations

import json
import sqlite3
from collections import Counter
from collections.abc import Iterable, Mapping
from typing import Any

# Canonical stage order; every stage with the universe that measures it.
FUNNEL_STAGES: tuple[tuple[str, str], ...] = (
    ("leads_encountered", "intake_register"),
    ("sources_archived", "database"),
    ("qualified", "intake_register"),
    ("screened", "database"),
    ("published", "database"),
    ("quarantined", "database"),
)

STAGE_ORDER = tuple(stage for stage, _ in FUNNEL_STAGES)

# published and quarantined are sibling outcomes of the verification lane, not
# sequential steps: each converts from the last pre-outcome stage (screened).
OUTCOME_STAGES = ("published", "quarantined")


def build_funnel_summary(
    *,
    leads_encountered: int | None = None,
    sources_archived: int | None = None,
    qualified: int | None = None,
    screened: int | None = None,
    published: int | None = None,
    quarantined: int | None = None,
) -> dict[str, Any]:
    """Assemble stage counts into a conversion summary.

    Only supplied stages appear (an unmounted database is an honest gap, not a
    zero). Conversion rates compare each stage against the last pre-outcome
    stage of the same measuring universe.
    """
    supplied = {
        "leads_encountered": leads_encountered,
        "sources_archived": sources_archived,
        "qualified": qualified,
        "screened": screened,
        "published": published,
        "quarantined": quarantined,
    }
    for stage, count in supplied.items():
        if count is not None and (not isinstance(count, int) or count < 0):
            raise ValueError(f"Stage {stage} requires a non-negative integer count")

    universes = dict(FUNNEL_STAGES)
    stages: list[dict[str, Any]] = []
    # Last same-universe pre-outcome stage: the base each stage converts from.
    # Outcomes (published/quarantined) are siblings, so they don't rebase.
    flow_base: dict[str, dict[str, Any]] = {}
    for stage in STAGE_ORDER:
        count = supplied[stage]
        if count is None:
            continue
        universe = universes[stage]
        base = flow_base.get(universe)
        conversion = None
        if base and base["count"]:
            conversion = round(count / base["count"], 3)
        entry: dict[str, Any] = {
            "stage": stage,
            "count": count,
            "universe": universe,
        }
        if conversion is not None:
            entry["conversion_from_previous"] = conversion
        stages.append(entry)
        if stage not in OUTCOME_STAGES:
            flow_base[universe] = entry

    return {
        "stages": stages,
        "stage_counts": {s["stage"]: s["count"] for s in stages},
    }


def funnel_counts_from_db(conn: sqlite3.Connection) -> dict[str, int]:
    """Stage counts read directly from the SQLite tables.

    ``leads_encountered`` and ``qualified`` live in the intake register, not the
    database, and stay the caller's supply; this returns the database-universe
    stages only. Archived sources are ``evidence_ledger`` rows in the
    pipeline schema; the Archil export database calls the same concept
    ``sources``.
    """
    has_ledger = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='evidence_ledger'"
    ).fetchone()
    sources_query = "SELECT COUNT(*) FROM evidence_ledger" if has_ledger else "SELECT COUNT(*) FROM sources"
    return {
        "sources_archived": conn.execute(sources_query).fetchone()[0],
        "screened": conn.execute(
            "SELECT COUNT(DISTINCT promise_id) FROM verifications"
        ).fetchone()[0],
        "published": conn.execute("SELECT COUNT(*) FROM promises").fetchone()[0],
        "quarantined": conn.execute("SELECT COUNT(*) FROM quarantined").fetchone()[0],
    }


def _normalize_reason_code(value: Any) -> str:
    code = str(value or "").strip()
    return code or "unknown"


def reason_codes_for_item(item: Mapping[str, Any]) -> list[str]:
    """The reason codes attributable to one quarantined item.

    Database-shaped rows carry ``reason_codes`` (already parsed from
    ``reason_codes_json``); exported registry items carry a single
    ``failing_check_code`` or ``check_type``. An item without any code is
    counted as ``unknown`` rather than dropped, so sums always reconcile.
    """
    codes = item.get("reason_codes")
    if isinstance(codes, list) and codes:
        return [_normalize_reason_code(code) for code in codes]
    for field in ("failing_check_code", "check_type"):
        code = item.get(field)
        if isinstance(code, str) and code.strip():
            return [_normalize_reason_code(code)]
    return ["unknown"]


def summarize_quarantine_reasons(items: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Reason-code distribution over quarantined items.

    Every item is attributed exactly once per code it carries, so
    ``sum(by_reason.values())`` equals the total code count and the item total
    equals ``len(items)`` — the reconciliation the audit panels assert.
    """
    by_reason: Counter[str] = Counter()
    total = 0
    for item in items:
        if not isinstance(item, Mapping):
            continue
        codes = reason_codes_for_item(item)
        total += 1
        for code in codes:
            by_reason[code] += 1
    return {
        "total_quarantined": total,
        "total_reason_codes": sum(by_reason.values()),
        "by_reason": dict(sorted(by_reason.items())),
    }


def summarize_reason_codes_from_db(conn: sqlite3.Connection) -> dict[str, Any]:
    """Quarantine reason-code sums read from the ``quarantined`` table.

    Each row's ``reason_codes_json`` is a list of codes; every code in the list
    is counted, so the code total can exceed the row count when a row carries
    several reasons.
    """
    by_reason: Counter[str] = Counter()
    rows = conn.execute("SELECT reason_codes_json FROM quarantined").fetchall()
    for (reason_codes_json,) in rows:
        try:
            codes = json.loads(reason_codes_json)
        except (TypeError, ValueError):
            codes = None
        if not isinstance(codes, list) or not codes:
            by_reason["unknown"] += 1
            continue
        for code in codes:
            by_reason[_normalize_reason_code(code)] += 1
    return {
        "total_quarantined": len(rows),
        "total_reason_codes": sum(by_reason.values()),
        "by_reason": dict(sorted(by_reason.items())),
    }
