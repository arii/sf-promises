# Lane D — Verdict

## Mission
Build the four isolated roles that turn pending rows into verdicts: kept
advocate, broken advocate, arbitrator, relevance gate. You are a sandbox
agent: you run checks and verdicts, you never edit code outside this lane's
files. Run one promise at a time, never batched across promises.

## Already done (do not redo)
- `src/checks.py` + `src/arbitrator.py` exist; `tests/test_checks.py` passes
  11/11 (domain, hash, quote, speaker, P02 broken-none logic, planted bad
  quote/speaker/hash catches).
- Still missing: port `relevance.py` from
  `Archil Hackathon Nov 10 - SF Promises Export/src/` to top-level `src/`,
  date + evidence-type + rubric checks, and the verdict-write transaction.

## Owns / touches
- Writes: `src/checks.py`, `src/arbitrator.py`, `src/relevance.py`,
  `staging/kept_<id>.json`, `staging/broken_<id>.json`, and — ONLY this lane —
  `promises`, `verdicts`, `verifications`, `quarantined`, `relevance_checks`.
- Transaction rule: arbitrator moves a row to `promises` or `quarantined` in
  the SAME transaction as its `verdicts` row. No other role writes `promises`.

## The four roles
- Sandbox A, kept advocate: affirming sources only → `staging/kept_<id>.json`.
- Sandbox B, broken advocate: contradicting sources only →
  `staging/broken_<id>.json`. Advocates cannot see each other.
- Sandbox D, relevance gate (step 2.5 ONLY, code only, no model, runs once):
  score `real_promise, measurable, sf_relevant, interesting` 0–2 each
  (rules in tech design §2). Publish only at total ≥ 5 AND `real_promise` ≥ 1;
  else `quarantined` with reason `relevance_low`. Never changes a verdict.
  There is no step 7.5.
- Sandbox C, arbitrator (code only, no model call). Checks in order: domain
  allowlist → hash re-check → quote exact/close (`none` fails) → speaker in
  roll call → date consistency → evidence type allowed. Rubric: official beats
  news, primary beats secondary, dated vote/ordinance/opening/count beats
  intent, later doc beats earlier on the same fact, number + deadline must
  BOTH hold for kept. Verdicts: `kept | in_progress | broken | stalled |
  undecided`, with reason, `reading_used` for wording cases, `decided_at`,
  `decided_by = arbitrator`.

## Evidence requirements
Every evidence row: verbatim quote + allowlisted source + saved file +
matching hash. Claim without verbatim quote is dropped (with a
`verifications` row, `passed = 0`).

## Validation (check runbook boxes only when this passes)
Every evidence row cites a saved source with matching hash, every check has a
`verifications` row, no failed row appears in `promises`, counts across
`promises` + `promises_pending` + `quarantined` add up to the ingest total.
12 `verdicts` rows for P01–P12.

## Cut rule
Advocate finds nothing → record `none found`, no second search for that
advocate. Slow check → run on the saved file only, never a live fetch.
