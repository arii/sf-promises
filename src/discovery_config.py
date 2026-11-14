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
    return DiscoveryConfig(
        rolling_days=rolling_days,
        added_reason=raw["added_reason"],
        added_by=raw["added_by"],
        added_at=raw["added_at"],
    )


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
