# SF Promises Tracker: Product Requirements

## Purpose and scope

Give San Francisco residents, journalists, and researchers a traceable record
of public commitments and what happened. Start with SF-relevant promises by
officials and other entities; expand only when a source establishes a real,
attributable commitment. A project announcement, forecast, or search snippet
alone is not automatically a promise.

The event target is a working sourced demo, evaluated across a verified scope
of 54 public commitments (12 primary seeds plus 42 civic and regional candidates).
These 54 commitments represent the current complete benchmark scope; 38 additional
seeds remain banked for subsequent intake rounds. See the [event runbook](Archil%20Hackathon%20Nov%2010%20-%20SF%20Promises%20Export/10-event-runbook.md)
for lane progress and acceptance checks.

## Evidence and verdicts

- Save source documents on the Archil filesystem with their URL, retrieval
  information, and SHA-256 hash. Published claims must cite saved, allowlisted
  sources and verifiable quotations; a search result snippet is not a source.
- Extract the commitment verbatim, attributing its speaker and date from the
  source. Record a deadline or page number when supported; do not invent them.
  Dates inferred from explicit durations must be identified as derived.
  Date resolution is off unless `SF_PROMISES_DATE_RESOLUTION=1`. When on and
  the model returns no commitment date, the date is taken in this order:
  stated (an explicit full date near the quote or in a dateline), then relative
  ("today", "yesterday", "on Tuesday", "last Tuesday", resolved against the
  source publication date), then the publication date itself. It is never
  later than the publication date. Relative and publication dates are labelled
  derived (`promise_date_basis`) and must not be shown as explicitly stated.
  The verbatim quote and both verifiers are still required.
- Outcome rules are off unless `SF_PROMISES_OUTCOME_RULES=1`; with the flag off
  the audit is unchanged. When on, a candidate still needs a verified verbatim
  origin quote, the relevance gate, the taxonomy check, and a stated promise
  date. Then:
  - R1: a verified origin with no deadline is open-ended, not quarantined; the
    deadline is stored as null.
  - R2: `promise_horizon_short` is ignored only when the origin quote itself
    states the deadline: an explicit date in the quote (a month and day without
    a year is the next such day on or after publication), or a weekday or
    relative day term ("Friday", "next Tuesday", "tomorrow", "today") resolved
    by `src/date_resolution.py` against the source publication date, equal to
    the deadline. Any other short horizon ("within 30 days", an unstated date)
    still fails, and so does a deadline before the promised date.
  - R3: a deadline after the as-of date with no contrary evidence is
    `in_progress`, with no delivery or survival sentence required. Contrary
    evidence is a selected sentence establishing not delivered or
    revoked/halted, and follows the existing rubric.
  - R4: a selected delivery sentence with survival unknown gives `kept` for
    on-time delivery, and `delayed_or_partial` for late or partial delivery,
    with the note "current status not checked". Shuttered or revoked need their
    own selected survival sentence.
  - R5: deadline passed or none, and no selected delivery or contrary
    sentence: `undecided` (published), not quarantined.
  - R6: the semantic verifier only has to confirm fields the verdict relies on.
    `in_progress` and `undecided` need action, promise date, entity and
    location, and the deadline if there is one. `kept` and `delayed_or_partial`
    also need a verified delivery sentence; `broken` needs a verified
    contrary sentence and a passed deadline.
  - `broken` also needs the contrary source to be published on or after the
    deadline. A source published before the deadline (or undated) cannot show
    the deadline was missed, so its sentence is set aside and the other rules
    decide: `undecided` for a passed deadline, with the reason noting the early
    source.
  - R7: every published verdict writes an `outcome_basis` verification row with
    the rules used, whether the commitment is open-ended, and the reason
    ("no outcome evidence found", "deadline in the future").
  - Exports read the rule set from the database, not the environment: the
    candidate snapshot (`src/export.py`) and the site merge
    (`src/site_merge.py`) waive the R1/R2 origin date failures only when the
    promise's `outcome_basis` row names that rule. A flagged database exports
    with the flag unset; a database without `outcome_basis` rows (flag off)
    still rejects open-ended and short-horizon records.
  - Schema: `src/schema.sql` allows a NULL `promises.date_deadline` and an
    `UNDECIDED` verdict so flagged runs can publish. With the flag off,
    `src/candidate.py` enforces the old constraints in code at the publish
    step (`require_flag_off_strictness`): a NULL deadline or an `UNDECIDED`
    verdict raises before anything is written. With the flag on, the audit and
    `run_live --candidate-batch` first check `sqlite_master` and stop with a
    clear message if the database was created with the older schema
    (`NOT NULL` deadline, no `UNDECIDED`); create a new database for flagged
    runs.
  - Gold gate rebaseline: `data/gold_gate_expectations.json` records the
    SHA-256 of `src/lifecycle_rubric.py`. On this branch it moved from
    `e2c3b525…e118` to `b5da20fd…2696`. The only change behind it is the
    `decide_verdict` None-deadline handling: the signature allows
    `deadline: date | None`; `future` is false and a new `no_deadline` flag is
    true when the deadline is None; with no deadline, `NOT_DELIVERED` is never
    `broken`, `DELIVERED_LATE` is never `delayed_or_partial` or
    `kept_then_reversed`; and the docstring explains this. Every branch with a
    non-None deadline is unchanged (`tests/test_outcome_rules.py`
    `test_decide_verdict_with_deadline_is_unchanged` and
    `test_exhaustive_safety_of_rubric`). Any other edit to the file must
    rebaseline the hash with its own review.
- The site merge (`docs/export_data.py --v2-db`) publishes a v2 record only
  when its evidence supports the verdict: a verified DELIVERY row dated after
  the promise for `kept` and `delayed_or_partial`, DELIVERY and SURVIVAL rows
  for `kept_then_reversed`, a contrary DELIVERY row for `broken`, and a passed
  `independent_verifier` row confirming action, promise date, entity and
  location, the deadline when there is one, and each phase the verdict needs.
  `all_checks_passed`, `failed_check_names` and `has_contradictory_evidence`
  are computed from those rows. Open-ended records show "No fixed deadline"
  (`due_date` null, `due_date_status` `not_applicable`), and the record carries
  `outcome_basis` (rules, open-ended, reason, relied-on phases, and whether
  current status was not checked), shown as one line in the record drawer.
- Apply the deterministic relevance gate once: a candidate needs a total score
  of at least 5/8 **and** `real_promise >= 1`. Quarantine failures; do not
  count them as published promises.
- Kept and broken advocates supply separate evidence; the arbitrator applies
  deterministic checks and records its reason and evidence. Verdicts are
  `kept`, `broken`, `in_progress`, `stalled`, or `undecided`. A genuine but
  weak news-only or press-release-only claim does not establish a kept verdict
  (N08/N09: `undecided`). An unsupported candidate is not a verified promise.
- Preserve provenance, verification results, and changes to verdicts. Multiple
  verdict records may exist for a promise; presentation must use the latest
  applicable verdict, not count every historical verdict as a separate promise.

## Storage and execution

- The working database and archived sources live on the shared Archil disk
  (free plan), mounted at `/mnt/archil` on every machine that works on the
  data; the workspace is `/mnt/archil/workspace`. Setup steps are in the
  README ("Workspace setup"). Fetching saves sources; extraction reads saved material without
  database writes; a separate load step writes `promises_pending`. Only the
  Verdict lane publishes to `promises`, `verdicts`, `verifications`, and
  `quarantined`.
- Advocate outputs are staged separately. The isolation model relies on
  separated processes (not Firecracker microVMs) and is verified via automated
  negative boundary tests.
- Checkpoint the mounted disk after coordinating and quiescing writers. Name
  checkpoints with a Git commit and timestamp; mark a dirty worktree explicitly.
  An Archil checkpoint does not capture uncommitted repository files. Verify
  checkpoint creation and restore consistency separately.
- Foreign-key architecture contract: Core relational tables (`promises`,
  `verdicts`, `verifications`, and `evidence`) strictly enforce SQLite foreign
  keys (`PRAGMA foreign_keys = ON;`). In contrast, staging directories (`staging/`)
  and the `quarantined` table operate as decoupled pre-publication quarantine buffers.
  Quarantined rows do not reference `promises.promise_id` because rejected claims
  are never admitted into the public registry. This architectural boundary resolves
  the pre-verdict FK question without dangling references in core tables.

## Threat Model: Process Separation & Storage Boundaries

The verification pipeline runs adversarial advocate models and deterministic
arbitrator code across separated OS processes ("separated processes, not Firecracker").

### What Separated Processes Protect
1. **File isolation across roles**: Advocate A (`kept`) cannot read or write
   Advocate B's staging files (`broken_*.json`), and neither advocate can write
   to `promises.db` or the arbitrator verification log.
2. **Disjoint runtime memory**: Separate worker address spaces prevent in-memory
   prompt leakage or adversarial manipulation between the affirming and contradicting
   evaluators.
3. **Execution containment**: Arbitrator checks execute independently with zero model
   calls (`0 LLM calls in arbitrator`), ensuring deterministic verdict computation.

### What Separated Processes Do NOT Protect Against
1. **Shared host kernel vulnerabilities**: Because workers share the Linux kernel,
   kernel exploits could break process isolation.
2. **Shared host filesystem mount**: Workers execute on the same mounted disk
   (`/mnt/archil`). Path boundaries are enforced at the application and OS permission
   level, not through hypervisor memory virtualization.
3. **Uncontrolled external egress**: External HTTP network calls must be explicitly
   restricted in advocate workers to prevent data exfiltration.

All published isolation claims must explicitly read "separated processes, not Firecracker".

## Demo

The demo must display actual published promises, latest verdicts, counts,
source links, hashes, and available checks from the Archil-backed database and
stored evidence. Counts must not be hardcoded or derived from expected test
verdicts. Show missing or unavailable data honestly. Source URLs are
browser-accessible links; filesystem paths on `/mnt/archil` are not.

A static export is a point-in-time snapshot, not a live database connection.
Generate it for deployment rather than treating hardcoded demo data as the
source of truth. A live view requires a server with access to the Archil mount.
Label saved or simulated runs clearly; do not claim a live pipeline ran when
it did not. Keep credentials server-side in the ignored `.env`.

## Validation and release

The validation lane checks P01–P12 and the planted N01–N12 cases, including
source, hash, quotation, relevance, and verdict checks. A blocked test is not
a pass. Keep small deterministic mocks for offline and regression tests;
production data must not depend on them. The extended CSV is a research/test
input for now, not a source of published verdicts; retire it only after its
needed data and independent expectations have been migrated and verified.

Acceptance requires a verified end-to-end run, evidence and source integrity,
accurate demo output, and a negative-test run with no failed examples published.
See the runbook for outstanding checks; do not infer acceptance from a lane's
status label or from raw database row counts.

## Documentation

This PRD records current product decisions; the original event export contains
historical plans, research, specifications, and the active runbook. Older
counts, budgets, or completion claims in that pack are not current status.
