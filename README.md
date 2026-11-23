# SF Promises

## https://arii.github.io/sf-promises/
### 🤗 Hugging Face Dataset & Database: [onasafari/sf-promises](https://huggingface.co/datasets/onasafari/sf-promises)

### 🏆 Hackathon Award Winner: Best Use Of Keenable
**SF Promises** was created during the **Archil "Agents need solid ground" Hackathon** on November 10, 2026. Across **1 night with 33 projects and 46 builders**, SF Promises was awarded **1 of 5 hackathon honors: "Best Use Of Keenable"** for its high-integrity temporal source retrieval and deterministic verification pipeline.

The original submission code created during the hackathon is preserved in the [hackathon-2026-11-10 release](https://github.com/arii/sf-promises/releases/tag/hackathon-2026-11-10) at commit `64972c8`.

SF Promises tracks public commitments across all of San Francisco, not just City Hall, but sports teams, concerts, robotaxis, tech companies, and neighborhood developments.

It starts with a promise made in public, finds the official source, and re-checks the promise against later official evidence. The verdict is kept, in progress, broken, stalled, or undecided; a kept promise that is later reopened is marked later closed / reversed. Every promise links to its source, so a reader can verify it.

**How it works:** fetch the official source and save it, extract the promise text from saved files only, check that the promise is real, measurable, and about San Francisco, then let one advocate argue the promise was kept and another argue it was broken, from separate sources. A code-only check runs the rules and decides, with deadlines checked first. No verdict comes from a single model call.

**Verified scope (as of November 20, 2026):** 54 tracked promises (24 kept, 10 in progress, 17 broken, 2 undecided, 1 later closed / reversed) across City Hall, SFO Airport, regional transit, sports, and tech. 13 quarantined items caught by deterministic checks and kept out of public tables. 100% agreement against the 25-promise hand-labeled gold set, and 0.0% false-accept rate across 50 automated adversarial mutations.

**Demo:** the 24/7 crisis center at 822 Geary Street, promised by Mayor Daniel Lurie, opened April 28, 2025, verdict kept. And 1,500 shelter beds in six months, verdict broken.

**Built with:** an Archil disk (free tier) for the shared database and saved sources, bounded worker processes, native SQLite, Keenable search and fetch, Nebius and Meta models for extraction only, and a static demo page on GitHub Pages.

Track SF public promises with sourced verdicts: fetch official sources, extract
verbatim promises, run kept/broken advocates plus a deterministic arbitrator,
and present verified outcomes. The working SQLite database and archived sources
live on a shared Archil disk that every machine mounts at `/mnt/archil` (see
[Workspace setup](#workspace-setup)). Work reads and writes the disk directly;
nothing is copied to a machine-local database.

The current product requirements are in [PRD.md](PRD.md). The original
`Archil Hackathon Nov 10 - SF Promises Export/` contains historical plans and
research and the historical runbook; its old counts and budget limits are
not proof of current results.

## For agents: start here

1. Read this README.
2. Open ONLY your lane brief in `agent/lanes/` and follow it.
3. Record current checks and blockers in the collaboration log; the hackathon runbook is historical.
4. Comments/collaboration go in `WORKING_NOTES.md`. Blockers/questions go in
   `QUESTIONS.md`.

### Optional agent skills

The SF Promises-specific `archil-vm-swarm` and `keenable-temporal-audit`
skills ship with this repo. No external skills are required to develop, test,
or deploy SF Promises.

Install generic skills only when needed, directly from their upstream sources.
For example, `npx skills add microsoft/playwright-cli --skill playwright-cli -g`
installs the Playwright skill without adding files to this checkout.

| Skills | Upstream |
| --- | --- |
| General engineering practices | [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) |
| Playwright CLI | [microsoft/playwright-cli](https://github.com/microsoft/playwright-cli) |
| Hugging Face | [huggingface/skills](https://github.com/huggingface/skills) |
| LangGraph | [langchain-ai/langchain-skills](https://github.com/langchain-ai/langchain-skills) |
| Remotion | [remotion-dev/skills](https://github.com/remotion-dev/skills) |
| Impeccable | [pbakaus/impeccable](https://github.com/pbakaus/impeccable) |

Don't commit personal installs or downloaded copies to this public repo.

## Dispatch: tell an agent one line

| Say | Agent reads | Does |
| --- | --- | --- |
| "Work on Discovery" | `agent/lanes/lane-a-discovery.md` | Discover public commitments across official, news, and advocacy sources |
| "Work on Fetcher" | `agent/lanes/lane-b-fetcher.md` | Seed P01–P12 source files + hashes |
| "Work on Extractor" | `agent/lanes/lane-c-extractor.md` | Saved files to `promises_pending` rows |
| "Work on Verdict" | `agent/lanes/lane-d-verdict.md` | Checks, advocates, arbitrator, quarantine |
| "Work on Demo Page" | `agent/lanes/lane-e-demo.md` | Static page from DB export |
| "Work on Tests" | `agent/lanes/lane-f-tests.md` | Harness, P01–P12, planted N01–N12 |

Mount the Archil disk and set `SF_PROMISES_WORKSPACE=/mnt/archil/workspace`
first ([Workspace setup](#workspace-setup)). Initialize a fresh database only
for new work; do not replace the shared archive with an empty database.

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

- Workspace: `SF_PROMISES_WORKSPACE=/mnt/archil/workspace` (the mounted Archil disk)
- DB: `<workspace>/promises.db` (new-work schema: `src/schema.sql`)
- Source files and manifests: `<workspace>/sources/`; staging: `<workspace>/staging/`
- Intake reports: `<workspace>/runs/intake-round/results.json`
- Code: `src/checks.py`, `src/arbitrator.py` — Fixtures: `mocks/`
- Tests: `tests/test_checks.py` (`pytest`)
- Seed data: `Archil Hackathon Nov 10 - SF Promises Export/05-sources-and-seed-promises.md`,
  `.../data/promises-P13-P112.csv`

The extended CSV is currently used by the validation harness; do not remove it
until its inputs and independent test expectations have been migrated and
verified. Keep `mocks/` for deterministic offline tests.

## Workspace setup

**Decision (2026-11-23):** the shared database and saved sources live on the
Archil disk `promises` (`ARCHIL_DISK_ID` in `.env`), on Archil's free plan.
The workspace is about 4 MB against the plan's 10 GB disk limit. Only
Archil storage is used: no Archil sandboxes or serverless execution. Any
machine with `.env` mounts the disk and works on it in place. The public
Hugging Face dataset stays as a published copy (see below); it is not the
working store.

One-time setup per machine (Linux with FUSE; macOS uses macFUSE):

```bash
curl -s https://archil.com/install | sh       # installs the archil client
set -a; source .env; set +a                   # provides ARCHIL_MOUNT_TOKEN, ARCHIL_DISK_ID
sudo mkdir -p /mnt/archil
sudo --preserve-env=ARCHIL_MOUNT_TOKEN archil mount "$ARCHIL_DISK_ID" /mnt/archil \
  --region "$ARCHIL_REGION" --shared
export SF_PROMISES_WORKSPACE=/mnt/archil/workspace
ls "$SF_PROMISES_WORKSPACE"                   # promises.db  sources/  staging/
```

Unmount with `sudo archil unmount /mnt/archil` (not `umount`). Add
`--read-only` when you only need to read. Inside Docker, the container needs
`devices: [/dev/fuse]`, `cap_add: [SYS_ADMIN]` and
`security_opt: [apparmor:unconfined]`.

`--shared` lets several machines mount at once. SQLite still needs **one
writer at a time**: only the Verdict lane writes `promises`/`verdicts`/
`verifications`/`quarantined`, and only one person runs a writing pipeline at
a time. Everyone else reads or mounts `--read-only`.

## Workers and staged exports

Install Python dependencies with `pip install -r requirements.txt`. PDF parsing
also needs `pdfplumber` (included). Commands run from the repository root
with the disk mounted:

```bash
export SF_PROMISES_WORKSPACE=/mnt/archil/workspace
python3 -m src.database "$SF_PROMISES_WORKSPACE/promises.db" # new work only
python3 -m src.run_live --candidate-batch P01
python3 -m src.run_live --durability-cycle --dry-run
python3 scripts/run_intake_round.py
python3 docs/export_data.py --output-dir "$SF_PROMISES_WORKSPACE/staging/exports/review"
```

Intake needs `SECRET_KEENABLE_API_KEY`; discovery needs `KEENABLE_API_KEY`.

### Credentials

Keys live in a git-ignored `.env` at the repository root. `.env.example` lists
every variable with what reads it; copy it and fill in values. Load it without
printing secrets: `set -a; source .env; set +a`. Intake reads the Keenable key
as `SECRET_KEENABLE_API_KEY`, so set both Keenable names to the same value.
`ARCHIL_MOUNT_TOKEN`, `ARCHIL_DISK_ID` and `ARCHIL_REGION` mount the shared
disk; `ARCHIL_API_KEY` is for the `disk` CLI and Archil's API. `HF_TOKEN` is
used only by `scripts/upload_to_huggingface.py`.
Model calls use the agent lane by default; provider credentials remain in the
coordinator only. Candidate and PDF workers receive only public job inputs and
an allowlisted environment, with timeout/output bounds, process-group cleanup
and Linux resource limits. These are local processes, **not VMs**: they do not
provide filesystem or network isolation against malicious same-user code.

Existing explicit `--db`/`--database`, source, and output overrides remain.
Sources and advocate staging for an explicit database default to its parent.
The Pages export refuses missing/invalid databases and stages outside `docs/`.
Legacy databases retain the existing Pages adapter; current-schema databases
produce review-only snapshots using the existing evidence-validating exporter.
There is no schema migration and neither path authorizes automatic publication.
Compare staged IDs, verdict counts, and missing provenance with committed
`docs/data.json` before publishing. Keep that public snapshot live until the
historical database and evidence have been recovered and validated.

## V2 development status

V2 is incomplete and does not publish verdicts. Its offline pieces use a
separate schema, content-addressed sources, preliminary gates, separate
advocate bundles and review-only snapshots. A successful preliminary screen
is not proof of a claim. See `PROGRESS_REPORT.md` for verified increments and
blockers; do not use the incomplete components to replace the live site.

Run the Python tests from the repository root with `python3 -m pytest`. To
regenerate unverified snapshot leads without overwriting an existing file:

```bash
python3 -m src.seeds docs/data.json seeds/leads-review.json
```

The resulting leads are not authoritative records or saved evidence. Live extraction needs a working model lane and discovery credentials, not an Archil template.

To create a new, separate v2 database (the parent directory must exist):

```bash
python3 -m src.database /path/to/new-v2.sqlite
```

The command refuses to overwrite an existing file. It does not migrate older
v2 databases; enable SQLite foreign keys on every connection. It marks the
database with a v2 application ID and schema version.

To load a saved extraction response and its archived fetch metadata:

```bash
python3 -m src.load --database /path/to/new-v2.sqlite --sources /path/to/sources \
  --promise-id P01 --slug example --metadata /path/to/metadata.json \
  --metadata-sha256 HASH --response /path/to/extraction.json
```

This writes unverified proposals to pending, not published promises. The
command requires a newly initialized, supported v2 database and rechecks the
saved source and metadata; it never creates a missing database.

For an existing v2 database and source archive, write an export file:

```bash
python3 -m src.export --database /path/to/v2.sqlite --sources /path/to/sources --output docs/data.json
```

Open `docs/index.html` to inspect its tallies, filters, and pipeline visualization.

## Backup and restore

Quiesce all database and source writers first; SQLite backup alone cannot make
a changing source tree application-consistent. The source is the mounted
workspace; choose new destination paths (another directory on the disk or a
second copy off Archil):

```bash
python3 -m scripts.workspace_backup backup --destination /path/to/backup-UTC-COMMIT
python3 -m scripts.workspace_backup restore --workspace /path/to/backup-UTC-COMMIT --destination /path/to/restore-test
python3 -m scripts.workspace_backup verify --workspace /path/to/restore-test
```

The script uses SQLite's backup API, copies sources/manifests, checks SQLite
`quick_check`/foreign keys, verifies content-addressed filenames and a complete
SHA-256 inventory, and refuses overwrite. Record the Git hash, dirty state,
UTC timestamp, destination and verification output in `WORKING_NOTES.md`.
Keep writers stopped until completion. Source records may contain historical
absolute paths: recovery must reconcile those paths and evidence provenance
before switching a restored archive into production; this script preserves
the database and saved bytes rather than rewriting historical records.

Retain the last known-good Pages files separately. To roll back publication,
restore that reviewed export, not an unvalidated database-generated replacement.

## Event milestones

The runbook records the event milestones, current checks, and cut rules. Its
target counts are goals, not verified totals.
