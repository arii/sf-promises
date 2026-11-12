# SF Promises

## https://arii.github.io/sf-promises/
### 🤗 Hugging Face Dataset & Database: [onasafari/sf-promises](https://huggingface.co/datasets/onasafari/sf-promises)

### 🏆 Hackathon Award Winner: Best Use Of Keenable
**SF Promises** was created during the **Archil "Agents need solid ground" Hackathon** on November 10, 2026. Across **1 night with 33 projects and 46 builders**, SF Promises was awarded **1 of 5 hackathon honors: "Best Use Of Keenable"** for its high-integrity temporal source retrieval and deterministic verification pipeline.

The original submission code created during the hackathon is preserved in the [hackathon-2026-11-10 release](https://github.com/arii/sf-promises/releases/tag/hackathon-2026-11-10) at commit `64972c8`.

SF Promises tracks public commitments across all of San Francisco, not just City Hall, but sports teams, concerts, robotaxis, tech companies, and neighborhood developments.

It starts with a promise made in public, finds the official source, and re-checks the promise against later official evidence. The verdict is kept, in progress, broken, stalled, or undecided. Every promise links to its source, so a reader can verify it.

**How it works:** fetch the official source and save it, extract the promise text from saved files only, check that the promise is real, measurable, and about San Francisco, then let one advocate argue the promise was kept and another argue it was broken, from separate sources. A code-only check runs the rules and decides, with deadlines checked first. No verdict comes from a single model call.

**Verified scope:** 54 tracked promises (25 kept, 10 in progress, 17 broken, 2 undecided) across City Hall, SFO Airport, regional transit, sports, and tech. 13 quarantined items caught by deterministic checks and kept out of public tables. 100% agreement against the 25-promise hand-labeled gold set, and 0.0% false-accept rate across 50 automated adversarial mutations.

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

Database setup is complete: `/mnt/archil/workspace/promises.db` initialized with schema,
filesystem + row round-trip verified.

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

## Archil sandbox example

Install the Python dependencies with `pip install -r requirements.txt`, then
export `ARCHIL_API_KEY` (an account key starting with `key-`, from the
[Archil console](https://console.archil.com)) and `ARCHIL_REGION`. Run:

```bash
python3 src/archil_sandbox_example.py
```

The example creates a separate sandbox, writes a file to its persistent root
filesystem, stops and starts it, reads the file, and stops it again. It does
not modify `sf-promises-golden` or mount the shared project disk. The stopped
sandbox and its root disk remain in Archil and may incur storage charges;
delete the example sandbox in the console when no longer needed. Persistent
sandboxes are available in Archil's public AWS regions, not public GCP regions.

For one-off checks against a mounted disk, Archil's `Disk.exec()` starts a
fresh microVM for one command and then shuts it down. Agent tool adapters can
expose disk reads, writes and execution to models; their permissions and
outputs still require validation. See the [Python SDK](https://docs.archil.com/sdks/python.md)
and [serverless execution](https://docs.archil.com/compute/serverless-execution.md).

## V2 development status

V2 is incomplete and does not publish verdicts. Its offline pieces use a
separate schema, content-addressed sources, preliminary gates, separate
advocate bundles and review-only snapshots. A successful preliminary screen
is not proof of a claim. See `PROGRESS_REPORT.md` for verified increments and
blockers; do not use the incomplete components to replace the live site.

Run the Python tests from the repository root with `python3 -m pytest`. To
regenerate unverified snapshot leads without overwriting an existing file:

```bash
python3 -m src.v2_seeds docs/data.json seeds/leads-review.json
```

The resulting leads are not authoritative records or saved evidence. The
live sandbox pilot requires a valid Archil account key and a verified golden
template; the OpenRouter credential must also work before live extraction.

To create a new, separate v2 database (the parent directory must exist):

```bash
python3 -m src.v2_database /path/to/new-v2.sqlite
```

The command refuses to overwrite an existing file. It does not migrate older
v2 databases; enable SQLite foreign keys on every connection. It marks the
database with a v2 application ID and schema version.

To load a saved extraction response and its archived fetch metadata:

```bash
python3 -m src.v2_load --database /path/to/new-v2.sqlite --sources /path/to/sources \
  --promise-id P01 --slug example --metadata /path/to/metadata.json \
  --metadata-sha256 HASH --response /path/to/extraction.json
```

This writes unverified proposals to pending, not published promises. The
command requires a newly initialized, supported v2 database and rechecks the
saved source and metadata; it never creates a missing database.

For an existing v2 database and source archive, write an export file:

```bash
python3 -m src.v2_export --database /path/to/v2.sqlite --sources /path/to/sources --output docs/data.json
```

Open `docs/index.html` to inspect its tallies, filters, and pipeline visualization.

## Archil checkpoints

After coordinating and quiescing database writers, create an Archil checkpoint
with `sudo archil checkpoints create /mnt/archil <name> --region aws-us-east-1`.
Use a unique name containing the Git commit and timestamp; mark a dirty worktree
explicitly. Record and verify the checkpoint separately: it snapshots the
mounted filesystem, not uncommitted repository files. See `AGENTS.md`.

## Event milestones

The runbook records the event milestones, current checks, and cut rules. Its
target counts are goals, not verified totals.
