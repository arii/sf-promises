# SF Promises

SF Promises tracks public commitments across all of San Francisco, not just City Hall, but sports teams, concerts, robotaxis, tech companies, and neighborhood developments.

It starts with a promise made in public, finds the official source, and re-checks the promise against later official evidence. The verdict is kept, in progress, broken, stalled, or undecided. Every promise links to its source, so a reader can verify it.

**How it works:** fetch the official source and save it, extract the promise text from saved files only, check that the promise is real, measurable, and about San Francisco, then let one advocate argue the promise was kept and another argue it was broken, from separate sources. A code-only check runs the rules and decides, with deadlines checked first. No verdict comes from a single model call.

**What was built at the event:** 62 tracked promises, 26 kept, 11 in progress, 21 broken, 4 undecided. 12 planted bad examples, all caught by the watchdog, none leaked to the published list.

**Demo:** the 24/7 crisis center at 822 Geary Street, promised by Mayor Daniel Lurie, opened April 28, 2025, verdict kept. And 1,500 shelter beds in six months, verdict broken.

**Built with:** Archil sandboxes and shared disks, native SQLite, Keenable search and fetch, Nebius and Meta models for extraction only, and a static demo page on GitHub Pages.

Track SF public promises with sourced verdicts: fetch official sources, extract
verbatim promises, run kept/broken advocates plus a deterministic arbitrator,
and present verified outcomes. The working SQLite database and archived sources
live on an Archil-mounted filesystem.

The current product requirements are in [PRD.md](PRD.md). The original
`Archil Hackathon Nov 10 - SF Promises Export/` contains historical plans and
research as well as the active runbook; its old counts and budget limits are
not proof of current results.

## For agents: start here

1. Read this README.
2. Open ONLY your lane brief in `agent/lanes/` and follow it.
3. Status = checkboxes in `Archil Hackathon Nov 10 - SF Promises Export/10-event-runbook.md`.
   Check a box only when its validation passes.
4. Comments/collaboration go in `WORKING_NOTES.md`. Blockers/questions go in
   `QUESTIONS.md`.

## Dispatch: tell an agent one line

| Say | Agent reads | Does |
| --- | --- | --- |
| "Work on Fetcher" | `agent/lanes/lane-b-fetcher.md` | Seed P01–P12 source files + hashes |
| "Work on Extractor" | `agent/lanes/lane-c-extractor.md` | Saved files to `promises_pending` rows |
| "Work on Verdict" | `agent/lanes/lane-d-verdict.md` | Checks, advocates, arbitrator, quarantine |
| "Work on Demo Page" | `agent/lanes/lane-e-demo.md` | Static page from DB export |
| "Work on Tests" | `agent/lanes/lane-f-tests.md` | Harness, P01–P12, planted N01–N12 |

Lane A (Setup) is DONE: `/mnt/archil/workspace/promises.db` has all 20 tables,
FS + row round-trip verified.

## Shared rules (all lanes)

- Only the Verdict lane writes `promises`, `verdicts`, `verifications`,
  `quarantined` — one transaction per verdict. Everyone else writes only their
  own tables/files (see lane brief).
- Advocates hand off via staging files (`staging/kept_<id>.json`,
  `staging/broken_<id>.json`), never direct DB writes.
- Fetch saves sources; extraction reads saved files without DB writes; a separate
  load step writes only `promises_pending`.
- A snippet is never a source. Every claim needs a verbatim quote + allowlisted
  source + saved file + matching SHA-256.
- Derive demo data and tallies from actual DB records, using the latest
  applicable verdict per promise. A static export is a snapshot; label saved
  or simulated runs and do not display fabricated results as live.
- Blocked 15 minutes on your lane? Cut scope per your brief's cut rule and keep
  moving. Never block another lane.
- `.env` holds keys and stays out of version control. No secrets in the DB.
- Specs: `Archil Hackathon Nov 10 - SF Promises Export/02-technical-design.md`
  (schema, enums, pipeline), `.../03-validation-and-tests.md` (N01–N12),
  `.../10-event-runbook.md` (checkpoints, cut rules).

## Key paths

- DB: `/mnt/archil/workspace/promises.db` (schema: `src/schema.sql`)
- Source files: `/mnt/archil/workspace/sources/` — Staging: `/mnt/archil/workspace/staging/`
- Code: `src/checks.py`, `src/arbitrator.py` — Fixtures: `mocks/`
- Tests: `tests/test_checks.py` (`pytest`)
- Seed data: `Archil Hackathon Nov 10 - SF Promises Export/05-sources-and-seed-promises.md`,
  `.../data/promises-P13-P112.csv`

The extended CSV is currently used by the validation harness; do not remove it
until its inputs and independent test expectations have been migrated and
verified. Keep `mocks/` for deterministic offline tests.

## Archil checkpoints

After coordinating and quiescing database writers, create an Archil checkpoint
with `sudo archil checkpoints create /mnt/archil <name> --region aws-us-east-1`.
Use a unique name containing the Git commit and timestamp; mark a dirty worktree
explicitly. Record and verify the checkpoint separately: it snapshots the
mounted filesystem, not uncommitted repository files. See `AGENTS.md`.

## Event milestones

The runbook records the event milestones, current checks, and cut rules. Its
target counts are goals, not verified totals.
