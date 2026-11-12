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
