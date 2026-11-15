"""Lane-lead construction for the OD-22 primary-source intake lanes (spec D3).

Leads built from archived primary documents enter the EXISTING chain —
extraction → deterministic screening → origin review → advocates →
publish/quarantine — unchanged. This module only shapes leads and their
origin rows; it records no decisions and moves no thresholds.

Every lead carries ``intake_channel`` provenance from the fixed lane
vocabulary, and every origin row points at an ARCHIVED primary document
(the harvester's sha256-addressed artifact), never at a news URL. Screening's
``TIER1_GOV`` tier check reads the origin URL through the existing
government group in src/evidence.py, so recording origins needs no new code.

A document harvested in page-range mode yields one lead per range, because
quote verification (``quote in text``, src/evidence.py) must resolve against
one archived document — the range slice is that document.
"""

from __future__ import annotations

from typing import Any, Mapping

# The fixed lane vocabulary: provenance reported per lane in the funnel.
INTAKE_CHANNELS: tuple[str, ...] = (
    "bos_transcript",
    "budget",
    "ballot",
    "campaign_query",
)

# Harvester collection key -> intake channel (src/sourcing/document_harvester.py).
_COLLECTION_CHANNELS: dict[str, str] = {
    "bos_transcripts": "bos_transcript",
    "budget_documents": "budget",
    "ballot_measures": "ballot",
}


def intake_channel_for_collection(collection: str) -> str:
    """The intake channel a harvester collection key belongs to."""
    try:
        return _COLLECTION_CHANNELS[collection]
    except KeyError:
        raise ValueError(f"Unknown harvester collection {collection!r}") from None


def _require_archived(document: Mapping[str, Any], field: str) -> str:
    value = document.get(field)
    if not isinstance(value, str) or not value:
        raise ValueError(
            f"Lane lead requires an archived {field}: a lead whose origin is "
            "not a sha256-addressed artifact must not be built"
        )
    return value


def build_lane_leads(
    document: Mapping[str, Any],
    *,
    entity: str,
    promise_text: str,
    published_at: str | None = None,
) -> list[dict[str, Any]]:
    """Build lane leads from one harvested document's row.

    Document-led intake yields one lead per archived text artifact: the
    whole-document extraction when the document fit the caps, otherwise one
    lead per archived page range. Each lead's origin row points at the
    archived artifact (``path`` + ``sha256``) with the primary document's
    URL — the row shape the audit chain's origin phases already consume.

    Raises on any document without an archived text artifact: an originless
    lead is exactly the NO_VERIFIABLE_ORIGIN failure this lane exists to
    make structurally impossible at intake.
    """
    if not isinstance(document, Mapping):
        raise ValueError("A lane lead is built from a harvested document mapping")
    channel = intake_channel_for_collection(str(document.get("collection", "")))
    url = document.get("url")
    if not isinstance(url, str) or not url:
        raise ValueError("A lane lead's origin row requires the primary document URL")
    digest = _require_archived(document, "sha256")

    leads: list[dict[str, Any]] = []
    ranges = document.get("ranges") or []
    if ranges:
        artifacts = [
            {
                "path": _require_archived(r, "path"),
                "sha256": _require_archived(r, "sha256"),
            }
            for r in ranges
        ]
        suffixes = [f"-p{r['page_from']}-{r['page_to']}" for r in ranges]
    else:
        artifacts = [{
            "path": _require_archived(document, "text_path"),
            "sha256": _require_archived(document, "text_sha256"),
        }]
        suffixes = [""]

    for artifact, suffix in zip(artifacts, suffixes):
        origin: dict[str, Any] = {
            "url": url,
            "path": artifact["path"],
            "sha256": artifact["sha256"],
        }
        if published_at is not None:
            origin["published_at"] = published_at
        leads.append({
            "promise_id": f"harv-{document['collection']}-{digest[:12]}{suffix}",
            "entity": entity,
            "promise_text": promise_text,
            "intake_channel": channel,
            "origins": [origin],
        })
    return leads


def lane_counts(leads: list[Mapping[str, Any]]) -> dict[str, int]:
    """Lead counts per intake channel — the lane dimension funnel rows carry."""
    counts: dict[str, int] = {}
    for lead in leads:
        channel = lead.get("intake_channel")
        if not isinstance(channel, str) or channel not in INTAKE_CHANNELS:
            raise ValueError(f"Lead carries unknown intake_channel {channel!r}")
        counts[channel] = counts.get(channel, 0) + 1
    return dict(sorted(counts.items()))
