# Collaboration Log & Working Notes

## 2026-11-12: Full UX Redesign, Hardening & Rubric Gaps Resolution

### 1. Website UX Overhaul (Guide 1)
- **Mobile Layout (390px)**:
  - Eliminated conflicting CSS blocks in `docs/styles.css` and transformed table rows into CSS Grid cards with `grid-template-columns: 1fr auto;`.
  - Positioned verdict chips squarely in header cell `(2, 1)` inside card padding with 0 margin/overlap overflow.
  - Enforced `white-space: nowrap !important;` on date and deadline strings, placing `Due: <date>` on its own clean line.
  - Collapsed topbar GitHub link to compact icon button on screens under 640px; shortened hackathon badge to "Best Use of Keenable".
  - Verified with zero horizontal overflow (`scrollWidth = 390 == innerWidth = 390`).
- **Desktop Table & Pagination**:
  - Added right padding (`padding-right: 24px;`) to `.data-table th:last-child` and `td:last-child`.
  - Implemented client-side pagination displaying 15 promises initially (`currentPageSize = 15`) with "Show 15 More Commitments" and "Show All 54" controls, reducing initial page scroll height by over 70%.
- **Hero & Story**:
  - Softened hero claim from "independently verified against cryptographically archived primary evidence" to "sourced to saved, hashed documents".
  - Added proportional outcome stacked bar chart (Kept 46.3%, In Progress 18.5%, Broken 31.5%, Undecided 3.7%) with 2x2 legend grid.
  - Added mission intro section featuring a 2-sentence civic problem statement and 3-pillar verification architecture breakdown (Keenable, Adversarial Advocates, Arbitrator & Archil).
- **Pipeline Replay State**:
  - Pipeline initialized directly in verified completed state for `P02` (Stage 6: 7/7 checks pass, KEPT stamp, evidence receipts) instead of showing empty 0/8 bars. Play button updated to "Replay Walkthrough".
- **Source Tiers & Permalinks**:
  - Implemented `get_source_tier` classifying sources into Official (`sf.gov`, `flysfo.com`, `legistar.com`), News, and Reference (`wikipedia.org`).
  - Added permanent stable IDs (`P02`, `SFO-01`) alongside impact ranks and enabled URL hash routing (`#promise-P02`) with inspect modal linkage.
  - Labeled `P05` 1,500 beds quote with `[Reported by The Frisc]`.

### 2. Sandbox Hardening & Rubric Resolution (Guide 2)
- **Proof of Isolation**:
  - Stamped `database_status` and `metadata` in `docs/export_data.py` with git commit SHA.
  - Labeled isolation strictly as "separated processes, not Firecracker".
  - Enhanced `check_staging_isolation` to enforce write-mode restrictions (advocates cannot write outside their role file or touch `promises.db`).
  - Added `check_sandbox_network` enforcing raw network egress blocks in advocate sandboxes.
- **Threat Model in `PRD.md`**:
  - Added comprehensive Threat Model detailing process boundary guarantees (disjoint memory, role file scoping, 0 LLM arbitrator calls) and explicit non-guarantees (shared kernel, shared host disk, uncontrolled egress).
  - Formalized FK contract: core tables enforce strict foreign keys; staging and quarantine operate as decoupled pre-publication buffers.
  - Defined verified benchmark scope at 54 promises with 38 pending seeds queued.
- **Rubric Gaps Closed**:
  - Added scheduled re-check calculation (`compute_next_check_at`) with +90 days for kept promises (preventing Whole Foods closure regressions) and +30 days for in-progress.
  - Added absence rule handling for negative promises ("never again" / "will not X").
  - Added `needs_human_review` state for competing primary claims with divergent framing.
  - Added `reopen_promise_verdict` turning the corrections principle into an append-only audit trail in `verdicts` and `change_log`.
- **Autonomous Investigations**:
  - Created structured `investigations/<pid>.md` records for all 54 published commitments documenting queries tried, 5-round cap, what was found vs what could not be found, and deterministic check outcomes.
- **Accuracy Benchmarks**:
  - Created `data/gold_set.json` with 25 hand-labeled consensus commitments; verified 100% agreement (`tests/test_gold_agreement.py`).
  - Created `tests/test_adversarial_mutations.py` testing 50 automated adversarial mutations with a 0.0% false-accept rate.
  - Setup `.github/workflows/ci.yml` running pytest and JavaScript syntax validation on every push.
  - Full test suite: **198/198 tests passing green**.
