# Lane F — Tests

## Mission
Build the validation harness and run it: P01–P12 plus planted bad examples
N01–N12. You are a sandbox agent: you run tests, you never edit pipeline
code to make tests pass.

## Owns / touches
- Writes: test harness code, `test_cases`, `test_runs`, `test_results` rows.
- Must not touch: `src/` pipeline code, demo, fetcher/extractors. A failing
  test is a real contract — report it in `WORKING_NOTES.md`, do not weaken it.

## Inputs
- N01–N12 definitions: `Archil Hackathon Nov 10 - SF Promises Export/03-validation-and-tests.md`
- Extended set: `Archil Hackathon Nov 10 - SF Promises Export/data/promises-P13-P112.csv`
  (100 rows incl. 25 non-SF fillers P88–P112 → 72 cleaned SF rows).
- Existing: `tests/test_checks.py` (11/11 passing — keep green).

## Run order
1. Load P01–P12 into `test_cases` (expected verdict + expected evidence),
   plus P13–P112 extended set.
2. Clean cases first: P21, P22, P23, P43, P66, P67, P83 + P01–P12.
3. Hard cases after: P05, P11, P24, P30, P49, P79, P97.
4. Planted N01–N12, each with its expected check + reason: N01 changed word
   (accuracy_quote), N02 wrong speaker (authenticity_speaker), N03 changed
   byte (authenticity_hash), N04 invented promise (accuracy_evidence), N05
   invented number (accuracy_quote), N06 invented date (accuracy_date), N07
   off-allowlist source (authenticity_domain), N08/N09 news-or-PR-only claimed
   kept (capped at undecided), N10 invented quote / N11 wrong-promise cite
   (evidence row dropped), N12 restated vote (relevance_low).
5. Write one `test_runs` row: total/passed/failed/blocked. Blocked is NOT a pass.

## Pass criteria
A test passes only when: verdict matches expected AND every claim cites a
saved source with matching hash AND the bundle is complete. Clean run =
12 passes + 12 catches. Failed-run rule: see `03-validation-and-tests.md`.

## Cut rule
Cut P08, P10, P12 first (keep P01, P02, P05, P06, P09, P11). Then cut re-check,
then change-log display (keep the table). Never cut: domain allowlist, hash
check, verbatim quote check, undecided outcome.
