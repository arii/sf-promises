"""Stage 2: Discovery & Harvesting Agent with 3-tier source hierarchy and byte SHA-256 locking."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional
from urllib.parse import urlparse

from src.evidence import _government_host, _primary_host, is_allowlisted_url
from src.sandbox import run_in_fork

SOURCE_HIERARCHY_TIERS = (
    "TIER1_PRIMARY",
    "TIER2_CONTEMPORANEOUS_NEWS",
    "TIER3_DISCOVERY_ONLY",
)


def classify_discovery_tier(url: str, source_type: str = "") -> str:
    """Classify source into primary, contemporaneous news, or discovery-only lead."""
    u = (url or "").lower()
    st = (source_type or "").lower()
    if _primary_host(url) or _government_host(url) or any(
        d in u for d in ("sf.gov", "sfgov.org", "sfmta.com", "flysfo.com", "sfpuc.org", "sfport.com", "sfplanning.org", "sfcta.org", "legistar.com")
    ):
        return "TIER1_PRIMARY"
    if "official" in st or "press-releases" in u or "valkyries.wnba.com" in u or "bayfc.com" in u:
        return "TIER1_PRIMARY"
    if is_allowlisted_url(url) or any(
        d in u for d in ("sfchronicle.com", "missionlocal.org", "kqed.org", "sfstandard.com", "thefrisc.com", "sfexaminer.com", "sf.eater.com")
    ):
        return "TIER2_CONTEMPORANEOUS_NEWS"
    return "TIER3_DISCOVERY_ONLY"


def extract_media_from_markdown_or_html(text: str) -> Dict[str, Optional[str]]:
    """Extract first candidate image URL and alt/caption from retrieved document text."""
    if not text:
        return {"media_image_url": None, "media_caption": None}
    md_img = re.search(r"!\[([^\]]*)\]\((https?://[^)\s]+)\)", text)
    if md_img:
        return {
            "media_caption": md_img.group(1).strip() or None,
            "media_image_url": md_img.group(2).strip(),
        }
    og_img = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\'](https?://[^"\']+)["\']', text, re.I)
    if og_img:
        return {"media_image_url": og_img.group(1).strip(), "media_caption": None}
    return {"media_image_url": None, "media_caption": None}


@dataclass
class HarvestedDocument:
    candidate_id: str
    url: str
    domain: str
    source_tier: str
    allowlisted: bool
    published_at: Optional[str]
    content_sha256: str
    verbatim_excerpt: str
    media_image_url: Optional[str] = None
    media_caption: Optional[str] = None
    needs_primary_upgrade: bool = False
    harvested_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class DiscoveryHarvester:
    """Executes bounded document retrieval, SHA-256 locking, and tier classification."""

    def __init__(self, archive_root: Optional[Path] = None):
        self.archive_root = archive_root

    def ingest_raw_document(
        self,
        *,
        candidate_id: str,
        url: str,
        raw_bytes: bytes,
        excerpt: str,
        published_at: Optional[str] = None,
        source_type: str = "",
        media_image_url: Optional[str] = None,
        media_caption: Optional[str] = None,
    ) -> HarvestedDocument:
        if not raw_bytes:
            raise ValueError("Cannot ingest empty document bytes")
        digest = hashlib.sha256(raw_bytes).hexdigest()
        text = raw_bytes.decode("utf-8", errors="replace")
        if excerpt and excerpt not in text:
            raise ValueError("Verbatim excerpt does not match saved document bytes")

        tier = classify_discovery_tier(url, source_type=source_type)
        allowed = is_allowlisted_url(url)
        domain = urlparse(url).hostname or ""

        extracted_media = extract_media_from_markdown_or_html(text)
        img_url = media_image_url or extracted_media["media_image_url"]
        img_caption = media_caption or extracted_media["media_caption"]

        if self.archive_root is not None:
            cand_dir = self.archive_root / candidate_id
            cand_dir.mkdir(parents=True, exist_ok=True)
            (cand_dir / f"{digest}.md").write_bytes(raw_bytes)

        return HarvestedDocument(
            candidate_id=candidate_id,
            url=url,
            domain=domain,
            source_tier=tier,
            allowlisted=allowed,
            published_at=published_at,
            content_sha256=digest,
            verbatim_excerpt=excerpt or text[:320].strip(),
            media_image_url=img_url,
            media_caption=img_caption,
            needs_primary_upgrade=(tier == "TIER3_DISCOVERY_ONLY"),
        )

    async def harvest_in_archil_sandbox(
        self,
        archil_client,
        golden_id: str,
        ledger,
        run_id: str,
        job_id: str,
        operation,
    ):
        """Dispatch live Keenable discovery inside an isolated Archil fork with policy gates."""
        return await run_in_fork(
            archil_client,
            golden_id,
            operation,
            ledger=ledger,
            run_id=run_id,
            job_id=job_id,
            template_reviewed=True,
            network_reviewed=True,
        )
