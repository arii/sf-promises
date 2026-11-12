"""Validate and stage separate, untrusted advocate bundles."""

import os
import re
import tempfile
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from src.evidence import screen_saved_source


class AdvocateClaim(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    statement: str
    phase: Literal["ORIGIN", "DELIVERY", "SURVIVAL"]
    url: str
    source_tier: Literal["TIER1_GOV", "TIER2_NEWS", "TIER3_CANARY"]
    path: str
    digest: str
    quote: str


class AdvocateBundle(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    promise_id: str
    role: Literal["kept", "broken"]
    claims: list[AdvocateClaim] = Field(max_length=8)


def check_staging_isolation(
    *,
    role: Literal["kept", "broken", "investigate"],
    target_path: str | Path,
    mode: Literal["read", "write"] = "read"
) -> None:
    """Enforce that an advocate or investigator in a specific role cannot read or write other roles' files or core database."""
    path_str = str(target_path)
    filename = Path(target_path).name

    # Core database protection: no advocate or investigator can touch promises.db
    if "promises.db" in filename or "promises.db" in path_str:
        raise PermissionError(f"Isolation violation: role '{role}' cannot {mode} core database promises.db")

    if mode == "write":
        if role == "kept" and not filename.startswith("kept_"):
            raise PermissionError(f"Isolation violation: kept advocate cannot write to non-kept staging path: {filename}")
        if role == "broken" and not filename.startswith("broken_"):
            raise PermissionError(f"Isolation violation: broken advocate cannot write to non-broken staging path: {filename}")
        if role == "investigate" and not filename.startswith("investigate_"):
            raise PermissionError(f"Isolation violation: investigator cannot write to advocate staging path: {filename}")
        return

    # Read checks
    if role == "kept" and (filename.startswith("broken_") or "/broken_" in path_str):
        raise PermissionError(f"Isolation violation: kept advocate cannot read broken staging file: {filename}")
    if role == "broken" and (filename.startswith("kept_") or "/kept_" in path_str):
        raise PermissionError(f"Isolation violation: broken advocate cannot read kept staging file: {filename}")
    if role == "investigate" and (
        filename.startswith("kept_") or "/kept_" in path_str
        or filename.startswith("broken_") or "/broken_" in path_str
    ):
        raise PermissionError(f"Isolation violation: investigator cannot read advocate staging file: {filename}")


def check_sandbox_network(role: str, target_url: str) -> None:
    """Negative network boundary check: advocate workers are not permitted raw egress."""
    target_lower = target_url.lower()
    if role in ("kept", "broken"):
        # Advocate sandboxes must operate purely on pre-fetched local sources in source_root
        raise ConnectionRefusedError(f"Network egress blocked in advocate sandbox for role '{role}': {target_url}")
    if role == "fetcher":
        # Fetcher can only access approved municipal/news allowlisted domains
        from src.checks import DOMAIN_ALLOWLIST
        import urllib.parse
        host = urllib.parse.urlparse(target_url).hostname or ""
        if not any(host == d or host.endswith("." + d) for d in DOMAIN_ALLOWLIST):
            raise ConnectionRefusedError(f"Network egress blocked: domain '{host}' not on allowlist")


def stage_advocate(*, staging_root, source_root, promise_id, role, response):
    """Stage a bundle, not a verdict; all claim meanings still require review."""
    if (not isinstance(promise_id, str)
            or not re.fullmatch(r"[A-Za-z0-9_-]+", promise_id)
            or role not in ("kept", "broken")
            or not isinstance(response, str) or len(response) > 32000):
        raise ValueError("Invalid advocate input")
    bundle = AdvocateBundle.model_validate_json(response)
    if bundle.promise_id != promise_id or bundle.role != role:
        raise ValueError("Advocate identity mismatch")
    for claim in bundle.claims:
        failures = screen_saved_source(
            root=source_root, promise_id=promise_id, path=claim.path,
            digest=claim.digest, quote=claim.quote, url=claim.url,
            source_tier=claim.source_tier,
        )
        if failures:
            raise ValueError("Advocate source failed preliminary screening")
    directory = Path(staging_root)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{role}_{promise_id}.json"
    data = (bundle.model_dump_json() + "\n").encode("utf-8")
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(dir=directory, delete=False) as file:
            temporary_path = file.name
            file.write(data)
            file.flush()
            os.fsync(file.fileno())
        try:
            os.link(temporary_path, path)
        except FileExistsError:
            if path.read_bytes() != data:
                raise ValueError("An advocate bundle already exists with different contents")
    finally:
        if temporary_path is not None:
            os.unlink(temporary_path)
    return path
