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
from pathlib import Path
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

# Per-window discovery funnel: the stages one discovery window records, in
# flow order. Unlike FUNNEL_STAGES these all measure the same cohort (raw
# search results seen by that window's queries), so conversions run the
# full chain sequentially. Discovery rounds append
# ``{"window", "round_id", "counts"}`` rows to data/window_funnel_rounds.json;
# its absence is an honest gap — no window rows, no panel.
WINDOW_FUNNEL_STAGES: tuple[str, ...] = (
    "raw",
    "allowlisted",
    "archived",
    "leads",
    "gate",
)


def summarize_window_funnel(counts: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Stage rows for one window's funnel.

    Only supplied stages appear. A stage converts from the immediately
    preceding stage in WINDOW_FUNNEL_STAGES when that stage was also
    supplied — a missing middle stage is an honest gap, so the next stage
    gets no conversion rather than one computed across the gap.
    """
    supplied: dict[str, int] = {}
    for stage, count in counts.items():
        if stage not in WINDOW_FUNNEL_STAGES:
            raise ValueError(f"Unknown per-window stage {stage!r}")
        if not isinstance(count, int) or count < 0:
            raise ValueError(f"Stage {stage} requires a non-negative integer count")
        supplied[stage] = count

    stages: list[dict[str, Any]] = []
    previous_count: int | None = None
    for index, stage in enumerate(WINDOW_FUNNEL_STAGES):
        if stage not in supplied:
            continue
        entry: dict[str, Any] = {"stage": stage, "count": supplied[stage]}
        # Convert only from the immediately preceding flow stage; a missing
        # middle stage is an honest gap, not a conversion across it.
        if index > 0 and WINDOW_FUNNEL_STAGES[index - 1] in supplied and previous_count:
            entry["conversion_from_previous"] = round(
                supplied[stage] / previous_count, 3
            )
        stages.append(entry)
        previous_count = supplied[stage]
    return stages


def summarize_window_funnels(rounds: Iterable[Any]) -> dict[str, Any]:
    """Aggregate recorded discovery rounds into per-window funnels.

    Each round row is ``{"window": str, "round_id": str, "counts": {stage:
    count}}``; counts accumulate per window label. Rows that are not
    mappings or carry no window label are skipped (they cannot be
    attributed); attributable rows with malformed counts raise. Windows are
    returned sorted by label so the export is deterministic.
    """
    totals: dict[str, dict[str, int]] = {}
    round_ids: dict[str, list[str]] = {}
    for row in rounds:
        if not isinstance(row, Mapping):
            continue
        window = row.get("window")
        if not isinstance(window, str) or not window.strip():
            continue
        window = window.strip()
        counts = row.get("counts") or {}
        if not isinstance(counts, Mapping):
            counts = {}
        stage_counts = totals.setdefault(window, {})
        for stage in WINDOW_FUNNEL_STAGES:
            if stage not in counts:
                continue
            stage_counts[stage] = stage_counts.get(stage, 0) + counts[stage]
        # Surface unknown stage names here too: a typo'd stage key must not
        # silently drop from the aggregate.
        for stage in counts:
            if stage not in WINDOW_FUNNEL_STAGES:
                raise ValueError(f"Unknown per-window stage {stage!r}")
        rid = row.get("round_id")
        if isinstance(rid, str) and rid.strip():
            round_ids.setdefault(window, []).append(rid.strip())

    windows: list[dict[str, Any]] = []
    for window in sorted(totals):
        stage_counts = totals[window]
        stages = summarize_window_funnel(stage_counts)
        entry: dict[str, Any] = {
            "window": window,
            "round_ids": round_ids.get(window, []),
            "stage_counts": stage_counts,
            "stages": stages,
        }
        windows.append(entry)
    return {
        "stage_order": list(WINDOW_FUNNEL_STAGES),
        "windows": windows,
    }


def window_funnel_rounds_from_file(path: Path) -> list[dict[str, Any]]:
    """Round rows from a ``window_funnel_rounds.json``-shaped file.

    A missing file is an honest gap (no rounds recorded yet) and returns
    an empty list; a malformed or non-list payload raises, because a corrupt
    measurement file should fail the export loudly rather than quietly
    empty the panel.
    """
    if not path.exists():
        return []
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, list):
        raise ValueError(f"{path} must contain a list of round rows")
    return [row for row in loaded if isinstance(row, Mapping)]


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
    window_rounds: Iterable[Any] | None = None,
) -> dict[str, Any]:
    """Assemble stage counts into a conversion summary.

    Only supplied stages appear (an unmounted database is an honest gap, not a
    zero). Conversion rates compare each stage against the last pre-outcome
    stage of the same measuring universe.

    ``window_rounds`` optionally carries recorded discovery-round rows
    (``{"window", "round_id", "counts"}``); when supplied, their aggregate
    is embedded under ``"windows"`` so the audit panels can render each
    window's raw → allowlisted → archived → leads → gate funnel separately
    and a horizon change is measurable round over round.
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

    summary: dict[str, Any] = {
        "stages": stages,
        "stage_counts": {s["stage"]: s["count"] for s in stages},
    }
    if window_rounds is not None:
        summary["windows"] = summarize_window_funnels(window_rounds)["windows"]
    return summary


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
