# Lane B — Fetcher

## Mission
Seed 12 validation sources (P01–P12): fetch each URL, save the bytes to the
Archil disk, SHA-256 them, record a `sources` row. You are a sandbox agent:
you run fetches and checks, you never edit code, never extract promises,
never decide verdicts.

## Already done (do not redo)
- Keenable search works (5 results for Lurie 1,500 shelter beds).
- Apr 28, 2026 minutes PDF fetched, saved, hash `88ea935b…0d87d755`
  re-verified on re-fetch.

## Owns / touches
- Writes: `/mnt/archil/workspace/sources/` files, `sources` rows,
  `legistar_matters` rows.
- Must not touch: `promises_pending`, `promises`, checks, demo, tests.

## Inputs
- Seed URLs: `Archil Hackathon Nov 10 - SF Promises Export/05-sources-and-seed-promises.md`
- Legistar: `https://webapi.legistar.com/v1/sfgov/matters?$top=5`
  (expect MatterId, MatterFile, MatterName, MatterStatusName, MatterPassedDate).
  No `contains()`, no `$count`; see tech design §7.

## Rules
- Fetch URL → save file → SHA-256 → `sources` row (URL, fetch time, hash).
  `source_id` = `S` + first 12 hex of hash.
- Web pages: Keenable `GET /v1/fetch` (never pass `prompt`).
  PDFs: raw bytes via `httpx`, save `sources/<hash>.pdf`, extract page-numbered
  text with `pdfplumber` to `<hash>.pages.json`.
- Cache by URL + hash: a second fetch of the same URL reads the saved file,
  no second Keenable call.
- Budgets for the whole demo: at most 20 searches, 30 fetches.

## Validation (check runbook boxes only when this passes)
12 `sources` rows, 12 files on disk, every hash matches a fresh hash of the
saved bytes.

## Cut rule
Source fails? Retry live at most once, then use the saved research file and
move on.
