"""Loader for the reviewed domain allowlist (config/allowlist.json).

The allowlist is versioned data, not code: every domain carries its category,
the mechanical groups it belongs to, and review provenance. Matching semantics
live with the consumers (src/checks.py, src/evidence.py); this module only
loads, validates, and answers membership questions.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ALLOWLIST_PATH = REPO_ROOT / "config" / "allowlist.json"

REQUIRED_FIELDS = (
    "domain",
    "source_type",
    "added_reason",
    "added_by",
    "added_at",
    "review_status",
    "canary",
)

VALID_REVIEW_STATUSES = frozenset({"approved", "pending", "denied"})


@dataclass(frozen=True)
class AllowlistEntry:
    domain: str
    source_type: str
    added_reason: str
    added_by: str
    added_at: str
    review_status: str
    canary: bool
    groups: tuple[str, ...] = ()


def _validate_entry(raw: object, index: int, path: Path) -> AllowlistEntry:
    where = f"{path} entry {index}"
    if not isinstance(raw, dict):
        raise ValueError(f"{where}: expected an object")
    missing = [field for field in REQUIRED_FIELDS if field not in raw]
    if missing:
        raise ValueError(f"{where}: missing required fields {missing}")
    for field in ("domain", "source_type", "added_reason", "added_by", "added_at", "review_status"):
        if not isinstance(raw[field], str) or not raw[field].strip():
            raise ValueError(f"{where}: field '{field}' must be a non-empty string")
    if not isinstance(raw["canary"], bool):
        raise ValueError(f"{where}: field 'canary' must be a boolean")
    if raw["review_status"] not in VALID_REVIEW_STATUSES:
        raise ValueError(f"{where}: unknown review_status {raw['review_status']!r}")
    groups = raw.get("groups", [])
    if not isinstance(groups, list) or any(not isinstance(g, str) for g in groups):
        raise ValueError(f"{where}: field 'groups' must be a list of strings")
    return AllowlistEntry(
        domain=raw["domain"],
        source_type=raw["source_type"],
        added_reason=raw["added_reason"],
        added_by=raw["added_by"],
        added_at=raw["added_at"],
        review_status=raw["review_status"],
        canary=raw["canary"],
        groups=tuple(groups),
    )


@lru_cache(maxsize=8)
def load_allowlist(path: str = "") -> tuple[AllowlistEntry, ...]:
    """Load and validate the allowlist file. Raises ValueError on any bad entry."""
    allowlist_path = Path(path) if path else DEFAULT_ALLOWLIST_PATH
    try:
        raw = json.loads(allowlist_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"allowlist file not found: {allowlist_path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"allowlist file is not valid JSON: {allowlist_path}: {exc}") from exc
    if not isinstance(raw, list):
        raise ValueError(f"allowlist file must contain a JSON array: {allowlist_path}")
    entries = tuple(_validate_entry(item, i, allowlist_path) for i, item in enumerate(raw))
    domains = [entry.domain for entry in entries]
    duplicates = sorted({d for d in domains if domains.count(d) > 1})
    if duplicates:
        raise ValueError(f"allowlist file has duplicate domains: {duplicates}")
    return entries


def domains_in_group(group: str, path: str = "") -> frozenset[str]:
    """Domains that belong to a mechanical group (canary flag is not consulted)."""
    return frozenset(
        entry.domain
        for entry in load_allowlist(path)
        if group in entry.groups
    )


def canary_domains(path: str = "") -> frozenset[str]:
    """Domains flagged canary — hard-blocked, never matched by allowlist consumers."""
    return frozenset(entry.domain for entry in load_allowlist(path) if entry.canary)


def entry_for_host(
    host: str,
    entries: tuple[AllowlistEntry, ...] | None = None,
    path: str = "",
) -> AllowlistEntry | None:
    """The allowlist entry governing a host, following exact-then-subdomain rules.

    Returns None when the host is not listed (or its closest listed ancestor is
    not approved). Only 'approved' entries match, mirroring review semantics.
    """
    if entries is None:
        entries = load_allowlist(path)
    host = (host or "").lower()
    if not host:
        return None
    best: AllowlistEntry | None = None
    best_labels = -1
    for entry in entries:
        if entry.review_status != "approved":
            continue
        if host == entry.domain or host.endswith("." + entry.domain):
            labels = entry.domain.count(".") + 1
            if labels > best_labels:
                best, best_labels = entry, labels
    return best
