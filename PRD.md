# SF Promises Tracker: Product Requirements

## Purpose and scope

Give San Francisco residents, journalists, and researchers a traceable record
of public commitments and what happened. Start with SF-relevant promises by
officials and other entities; expand only when a source establishes a real,
attributable commitment. A project announcement, forecast, or search snippet
alone is not automatically a promise.

The event target is a working sourced demo, then a larger set of up to 100
SF-relevant promises. These are targets, not claims about how many promises
have been verified. See the [event runbook](Archil%20Hackathon%20Nov%2010%20-%20SF%20Promises%20Export/10-event-runbook.md)
for current lane progress and acceptance checks.

## Evidence and verdicts

- Save source documents on the Archil filesystem with their URL, retrieval
  information, and SHA-256 hash. Published claims must cite saved, allowlisted
  sources and verifiable quotations; a search result snippet is not a source.
- Extract the commitment verbatim, attributing its speaker and date from the
  source. Record a deadline or page number when supported; do not invent them.
  Dates inferred from explicit durations must be identified as derived.
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

- The working database and archived sources live on an Archil-mounted
  filesystem. Fetching saves sources; extraction reads saved material without
  database writes; a separate load step writes `promises_pending`. Only the
  Verdict lane publishes to `promises`, `verdicts`, `verifications`, and
  `quarantined`.
- Advocate outputs are staged separately. The intended sandbox isolation and
  end-to-end execution must be verified, not inferred from code or fixtures.
- Checkpoint the mounted disk after coordinating and quiescing writers. Name
  checkpoints with a Git commit and timestamp; mark a dirty worktree explicitly.
  An Archil checkpoint does not capture uncommitted repository files. Verify
  checkpoint creation and restore consistency separately.
- The staging and quarantine foreign-key model remains an integration issue:
  staged references can precede published promises, and quarantine currently
  requires a different FK handling path. Do not describe the whole database as
  FK-clean until the contract and checks are resolved.

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
