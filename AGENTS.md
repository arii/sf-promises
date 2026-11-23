# AGENTS.md

## Start here

Read `README.md`, then your lane brief in `agent/lanes/`. Dispatch needs only:
"read README, work on Verdict" (or Fetcher, Extractor, Demo Page, Tests).

## Code Map

- `README.md` — dispatch surface: lane table, shared rules, checkpoints
- `agent/lanes/lane-b-fetcher.md` … `lane-f-tests.md` — self-contained lane briefs
- `Archil Hackathon Nov 10 - SF Promises Export` — specs (`02-technical-design.md`,
  `03-validation-and-tests.md`, `05-sources-and-seed-promises.md`,
  `10-event-runbook.md` = status checkboxes, `data/`, `src/` reference code)
- `src/` — `schema.sql`, `checks.py`, `arbitrator.py` (Verdict lane owns)
- `tests/test_checks.py` — 11/11 passing, keep green (`pytest`)
- `mocks/` — P02/P05 fixtures for advocates and demo
- `WORKING_NOTES.md` — collaboration log · `QUESTIONS.md` — blockers/questions
- `SF_PROMISES_WORKSPACE` (default `/mnt/archil/workspace`, the shared Archil disk; mount it per README "Workspace setup") — `promises.db`, `sources/`, `staging/`

## Rules

- Only Verdict writes `promises`/`verdicts`/`verifications`/`quarantined`.
- Lane briefs define owns/touches — stay in your lane's files and tables.
- `.env` out of version control; no secrets in the DB.

## Nebius Token Factory model catalog

Load local credentials without printing them:

```bash
set -a
source .env
set +a
```

List available models:

```bash
curl https://api.tokenfactory.nebius.com/v1/models \
  -H "Authorization: Bearer $NEBIUS_API_KEY"
```

Add `?verbose=true` to include pricing, context length, and request limits.
The `pricing` values are strings and may include `prompt`, `completion`,
`input_cache_read`, `image`, `price_per_video_second`, `request`, and
`price_per_minute`.

```bash
curl -s 'https://api.tokenfactory.nebius.com/v1/models?verbose=true' \
  -H "Authorization: Bearer $NEBIUS_API_KEY" \
  | jq '.data[] | {id, pricing}'
```

Pass `ai_project_id` when the catalog should be scoped to a specific project.
The OpenAI SDK can also list models with
`client.models.list()` and
`base_url="https://api.tokenfactory.nebius.com/v1/"`. Check the live catalog
before selecting a model or estimating fallback cost.

For the November 2026 coordinator preference order, try these Nebius fallback
models only when present in the verbose catalog:

1. `Qwen/Qwen3-30B-A3B-Instruct-2507`
2. `nvidia/Nemotron-3.5-Lightning` or `nvidia/Nemotron-3_5-Lightning`
3. `MiniMaxAI/MiniMax-M3`
4. `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B`

If using the Nemotron Nano model, allow `max_tokens=4096` so reasoning tokens
do not consume the response budget.

OpenRouter is the primary provider. Verify and rotate only through currently
listed, zero-priced `:free` models:

```bash
curl -s https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  | jq '.data[] | {id, pricing}'
```

Preferred IDs, in order: `cohere/north-mini-code:free`,
`nvidia/nemotron-3.5-lightning:free`,
`nvidia/nemotron-3-super-120b-a12b:free`, `qwen/qwen3.8-27b:free`, and
`nvidia/nemotron-3-ultra-550b-a55b:free`. Use Nebius only after OpenRouter
rate limits; the coordinator's persistent spend ledger is capped at $5.

For extraction, pass the Pydantic bundle schema as a function tool named
`record_promise_evidence`, force that tool with `tool_choice`, and set
`temperature=0` and `max_tokens=4096`. Parse
`message.tool_calls[0].function.arguments`; if there is no tool call, accept
`message.content` only after removing `<think>...</think>` and then validate
it against the same Pydantic schema. Source quotes must still match saved
bytes exactly.

## Backup and restore

Quiesce all database and source writers first; SQLite backup alone cannot make
a changing source tree application-consistent. Choose new destination paths:

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

## Manual utility scripts

These `scripts/` entries are referenced by no CI job, doc, or other code; each
is a manual entry point retained for the purpose below. Run from the
repository root.

- `scripts/autonomous_investigator.py` — manual discovery/investigation
  utility. Queries Keenable (network access and `KEENABLE_API_KEY` required,
  billed usage) and extracts/verifies candidates inside a bounded local
  process. Try a bounded dry run first:
  `python3 -m scripts.autonomous_investigator --entity "SFMTA" --dry-run`.
- `scripts/update-permissions.sh` — local agent-environment helper that merges
  agent-tool permission rules into the Antigravity CLI settings
  (`$SETTINGS_FILE`/`$CONFIG_FILE`, defaulting to `~/.gemini/...`). Modifies
  no repository files; run only when configuring a local agent environment.
- `scripts/rebuild_index_html.py` — one-shot migration (2026-11-12) that
  rewrote `docs/index.html` into the 7-section page flow. Historical: the
  markup markers it extracts no longer exist in `docs/index.html`, so running
  it against the current page fails its own assertions. Retained for
  provenance of that redesign; do not run it.
- `scripts/fill_investigations.py` — one-shot backfill (2026-11-12) that
  created missing `investigations/<promise_id>.md` records from
  `docs/data.json`; skips records that already exist. Retained for provenance
  of the investigation records.
- `scripts/build_outside_the_box_promises.py` — one-shot generator
  (2026-11-12) of the tracked `seeds/outside_the_box_candidates.json`
  (hand-curated outside-the-box promise set with media fields). Retained as
  that seed file's generator of record.
