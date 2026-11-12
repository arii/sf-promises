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
