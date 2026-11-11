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
