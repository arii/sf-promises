# SF Promises contributor instructions

## Commands

Run Python commands from the repository root.

```bash
# Full unit suite
pytest

# One test
pytest tests/test_checks.py::test_domain_pass

# Run the deterministic relevance examples
python3 src/relevance.py
```

The shared SQLite database and archived evidence are mounted outside the
repository at `/mnt/archil/workspace/`. The integration harness operates on
that database:

```bash
python3 tests/lane_f_harness.py
```

The harness records results in the database; it is not an isolated unit test.

There is no configured root build or lint command.

## Architecture and data flow

This repository tracks public San Francisco commitments through a
provenance-first pipeline:

1. **Fetcher:** saves source bytes under `/mnt/archil/workspace/sources/`,
   hashes them, and records `sources` (plus Legistar metadata where relevant).
2. **Extractor:** reads only saved source files, obtains verbatim promise
   candidates, and emits a JSON bundle. The separate `load` command in
   `src/extract.py` writes verified candidates to `promises_pending`.
3. **Verdict:** the deterministic relevance gate, separate kept/broken
   advocate bundles in `staging/`, and `src/arbitrator.py` checks determine
   whether a pending promise is published or quarantined. The arbitrator
   writes the outcome atomically.
4. **Demo export:** the static site must be generated from database records and
   show the latest applicable verdict per promise; it is a snapshot, not a
   live database view.

`src/schema.sql` defines the SQLite contract. `src/checks.py` contains the
reusable evidence checks, while `src/arbitrator.py` applies their ordered
validation and the verdict rubric. `mocks/` provides deterministic P02/P05
fixtures for offline tests; it is not production evidence.

The GitHub Pages site is the static `docs/` application. Its displayed promise
text, tallies, relevance scores, source paths, and latest verdicts must remain
derived from the database export rather than duplicated in client code. The
separate `video/` Remotion project currently expects `../demo/data.json`,
while the static site data is in `docs/data.json`; align that input before
relying on its `npm` scripts.

## Repository-specific rules

- Start with `README.md`, then read only the applicable brief in
  `agent/lanes/`. The lane brief defines the files and database tables an
  agent may modify.
- Only the Verdict lane may write `promises`, `verdicts`, `verifications`, or
  `quarantined`. Publish or quarantine a pending row in the same transaction;
  no failed row may appear in `promises`.
- Preserve the fetch/extract/load separation: fetching saves evidence,
  extraction reads saved material without database writes, and only the load
  phase writes `promises_pending`.
- Every published claim needs an allowlisted source URL, saved file, matching
  SHA-256, and verbatim quote. A snippet is never a source. Missing or failed
  evidence is recorded as verification failure rather than promoted.
- Advocates must remain separate and communicate through
  `staging/kept_<id>.json` and `staging/broken_<id>.json`; the code-only
  arbitrator decides the verdict.
- Keep demo counts and promise text derived from DB/export data. Use the
  latest verdict for each promise and label static or simulated runs honestly.
- Treat blocked validation cases as blocked, never passed. Keep the extended
  CSV and deterministic mocks until their independent expectations have been
  migrated and verified.
- Keep credentials in the ignored `.env`; do not store secrets in SQLite.

## Archil database checkpoints

Before creating an Archil checkpoint, coordinate with database writers and
quiesce them. Use a unique checkpoint name containing the Git commit hash and
UTC timestamp, mark a dirty worktree explicitly, then record and verify the
checkpoint in `WORKING_NOTES.md`. The mounted-disk checkpoint does not include
uncommitted repository changes.
