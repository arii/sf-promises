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
- `/mnt/archil/workspace/` — `promises.db` (20 tables), `sources/`, `staging/`

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

## Archil checkpoints

- Coordinate with database writers and quiesce them before checkpointing so the
  SQLite database and source files represent a consistent state.
- Create a uniquely named checkpoint with
  `sudo archil checkpoints create /mnt/archil <checkpoint-name> --region aws-us-east-1`.
  Include the Git commit hash and a UTC timestamp in the name; explicitly mark
  it `dirty` if the worktree has uncommitted changes. A Git hash does not
  capture those changes, and the checkpoint captures the mounted disk, not the
  repository.
- Record the checkpoint name, Git commit, worktree state, and result in
  `WORKING_NOTES.md`. Verify creation via
  `archil checkpoints list <disk-id> --region aws-us-east-1`; do not claim a
  successful or application-consistent backup without verifying it.
