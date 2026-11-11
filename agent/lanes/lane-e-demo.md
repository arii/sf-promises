# Lane E — Demo Page

## Mission
Build the static demo page from a SQLite export. You are a coding agent: you
build the page, you never run a verdict. Fixture-first: build against a frozen
JSON export matching the schema NOW, swap in the live export later — do not
wait on other lanes.

## Owns / touches
- Writes: demo directory only (new `demo/` folder at repo root).
- Reads: DB exports, `mocks/` fixtures. Must not touch: pipeline code, DB
  writes, checks.

## Page requirements
- Header: promise count + verdict tally + last-checked date, city, method link.
- Filters: entity type, verdict, category (politicians, companies, sports,
  topics). Table with verdict chips, newest promised date first, publishable
  rows only.
- Click-through detail per promise, four parts: promise provenance bundle,
  verdict bundle, both advocate bundles side by side, arbitrator reasoning +
  checks, plus relevance score.
- Quarantine view: quarantined rows with reason, check type, relevance score,
  quarantined_at.
- Live run one: one promise fetch → extract → gate 2.5 → advocates →
  arbitrator → publish, with a per-step timer. Live run two: watchdog catches
  a planted bad example (N01 or N03) — show failing check, reason, quarantine
  entry, row kept out of the main table. Whole demo under 3 minutes.

## Order of work
1. Demo Path 0 first: static page with tally + one promise (checkpoint 6:40).
2. Then full table, filters, detail, quarantine view.
3. Then live runs (fall back to saved runs if live fails — debug nothing
   on stage).

## Validation (check runbook boxes only when this passes)
Page loads with no console errors, every promise links to its stored source
file, at least one promise per verdict in the table, quarantine view shows
the planted catch.

## Cut rule
Live run fails → show the saved run. Never cut the provenance bundle, the
verdict reason, or the hash display.
