"""Loader for the discovery horizon config (config/discovery.json).

Following the allowlist-as-data pattern (PR #6): the rolling horizon is
reviewed data, not code. The config carries only relative days plus review
provenance; concrete window dates are computed at run time so no hardcoded
endpoint can go stale.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DISCOVERY_CONFIG_PATH = REPO_ROOT / "config" / "discovery.json"

REQUIRED_FIELDS = ("rolling_days", "added_reason", "added_by", "added_at")


@dataclass(frozen=True)
class DiscoveryConfig:
    rolling_days: int
    added_reason: str
    added_by: str
    added_at: str
    search_max_results: int = 25
    fetch_max_chars: int = 400000
    fetch_attempts_per_phase: int = 8
    objectives: tuple = ()  # ((phase, objective), ...)

    def objective(self, phase: str | None) -> str | None:
        return dict(self.objectives).get(phase)


@lru_cache(maxsize=8)
def load_discovery_config(path: str = "") -> DiscoveryConfig:
    """Load and validate the discovery config. Raises ValueError on bad data."""
    config_path = Path(path) if path else DEFAULT_DISCOVERY_CONFIG_PATH
    try:
        raw = json.loads(config_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"discovery config file not found: {config_path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"discovery config file is not valid JSON: {config_path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise ValueError(f"discovery config file must contain a JSON object: {config_path}")
    missing = [field for field in REQUIRED_FIELDS if field not in raw]
    if missing:
        raise ValueError(f"discovery config {config_path}: missing required fields {missing}")
    rolling_days = raw["rolling_days"]
    if isinstance(rolling_days, bool) or not isinstance(rolling_days, int) or rolling_days <= 0:
        raise ValueError("discovery config: field 'rolling_days' must be a positive integer")
    for field in ("added_reason", "added_by", "added_at"):
        if not isinstance(raw[field], str) or not raw[field].strip():
            raise ValueError(f"discovery config: field '{field}' must be a non-empty string")
    defaults = DiscoveryConfig(rolling_days, "", "", "")
    for field in ("search_max_results", "fetch_max_chars", "fetch_attempts_per_phase"):
        value = raw.get(field, getattr(defaults, field))
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError(f"discovery config: field '{field}' must be a positive integer")
    if raw.get("search_max_results", 25) > 50:
        raise ValueError("discovery config: field 'search_max_results' must be at most 50")
    objectives = raw.get("objectives", {})
    if not isinstance(objectives, dict) or any(
            not isinstance(k, str) or not isinstance(v, str) or not v.strip()
            for k, v in objectives.items()):
        raise ValueError("discovery config: field 'objectives' must map phase to a non-empty string")
    return DiscoveryConfig(
        search_max_results=raw.get("search_max_results", 25),
        fetch_max_chars=raw.get("fetch_max_chars", 400000),
        fetch_attempts_per_phase=raw.get("fetch_attempts_per_phase", 8),
        objectives=tuple(sorted(objectives.items())),
        rolling_days=rolling_days,
        added_reason=raw["added_reason"],
        added_by=raw["added_by"],
        added_at=raw["added_at"],
    )


DEFAULT_EXCLUDE_DOMAINS_PATH = REPO_ROOT / "config" / "exclude_domains.json"


@lru_cache(maxsize=8)
def load_exclude_domains(path: str = "") -> tuple:
    """Reviewed hosts to leave out of Keenable searches (config/exclude_domains.json)."""
    config_path = Path(path) if path else DEFAULT_EXCLUDE_DOMAINS_PATH
    try:
        raw = json.loads(config_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"exclude domains file not found: {config_path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"exclude domains file is not valid JSON: {config_path}: {exc}") from exc
    domains = raw.get("domains") if isinstance(raw, dict) else None
    if (not isinstance(domains, list)
            or any(not isinstance(d, str) or not d.strip() or "/" in d or d != d.lower()
                   for d in domains)):
        raise ValueError(f"exclude domains {config_path}: 'domains' must be a list of lowercase hostnames")
    return tuple(domains)


def search_options(phase: str | None = None, *, max_results: int | None = None,
                   path: str = "", exclude_path: str = "") -> dict:
    """Keenable search kwargs shared by every caller: cap, objective, cards off, excluded hosts."""
    config = load_discovery_config(path)
    options = {
        "max_results": max_results if max_results is not None else config.search_max_results,
        "disable_cards": True,  # card URLs are temporary and break provenance
    }
    excluded = load_exclude_domains(exclude_path)
    if excluded:
        options["exclude_domains"] = list(excluded)
    objective = config.objective(phase)
    if objective:
        options["objective"] = objective
    return options


def rolling_window_start(rolling_days: int, today: date | None = None) -> str:
    """The window's start date: rolling_days back from the run date."""
    return ((today or date.today()) - timedelta(days=rolling_days)).isoformat()


def rolling_window_end(today: date | None = None) -> str:
    """The window's end date: the run date itself, never a pinned endpoint."""
    return (today or date.today()).isoformat()


def rolling_time_window(today: date | None = None, path: str = "") -> str:
    """Keenable-style 'start..end' window sourced from the discovery config."""
    config = load_discovery_config(path)
    return f"{rolling_window_start(config.rolling_days, today)}..{rolling_window_end(today)}"
