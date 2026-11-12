# SF Promises v2 Progress Report

This progress report tracks the v2 rebuild according to [PLAN.md](PLAN.md). Tasks are marked `[x]` only after independent verification passes.

---

## Phase 1: Environment & Archil Golden Sandbox Setup
- [x] Clean up stale/unmounted Archil sandboxes (`sf-promises-v2-template`, `sf-promises-clean-a9df37e5`)
- [x] Clean any orphaned disk delegations on `dsk-000000000018f6e1`
- [x] Provision `sf-promises-golden` with `dsk-000000000018f6e1` mounted at `/mnt/archil` and environment variables injected (`ARCHIL_API_KEY`, `KEENABLE_API_KEY`, `OPENROUTER_API_KEY`, `NEBIUS_API_KEY`, `GITHUB_TOKEN`, `PYTHONUNBUFFERED=1`)
- [x] Stop `sf-promises-golden` so it serves as an immutable template for worker forking
- [x] Verify test worker fork inherits mounted disk `/mnt/archil/workspace` and environment variables

## Phase 2: Upgraded Data Model & Deterministic Gates
- [x] Verify `src/schema_v2.sql` (or `src/schema.sql`) implements canonical slugs, `initial_delivery`, `current_survival`, and computed `verdict` enums, plus `evidence_ledger`
- [x] Implement Gate 1: Forward-Looking Claim Check (`check_forward_looking_quote` - reject retrospective >45 days or retrospective phrasing)
- [x] Implement Gate 2: Temporal Arithmetic & Future Deadline Gate (`compute_deterministic_verdict` with cutoff 2026-11-11)
- [x] Implement Gate 3: Strict SF Geography & Sector Dictionary (`check_geography_and_entity`, `VALID_SF_LOCATIONS`)
- [x] Implement Gate 4: Tiered Evidence Rule (TIER3_CANARY requires corroborating TIER1_GOV / TIER2_NEWS)

## Phase 3: Keenable 3-Phase Temporal Search
- [x] Wire Keenable client (`src/v2_keenable.py` / `src/keenable_tools.py`) with 3-phase temporal queries:
  - Phase 1: Origin Query ($T_0$) with `published_before: "{promised_year}-12-31"`
  - Phase 2: Delivery Query ($T_1$) with `published_after: "{date_promised}"` and `published_before: "{deadline_year + 1}-12-31"`
  - Phase 3: Survival Query ($T_{now}$) with `published_after: "{deadline_year}-01-01"` and `published_before: "2026-11-11"`
- [x] Wire content fetch via Keenable extracting clean Markdown for LLM extraction

## Phase 4: LangGraph Swarm & Archil VM Worker Orchestration
- [x] Update `src/v2_sandbox.py` and `src/v2_candidate_sandbox.py` to support and verify the mounted disk `/mnt/archil/workspace`
- [x] Generalize `src/v2_run_live.py` / swarm orchestrator to remove single-seed P36 hardcoding and execute across canonical seeds
- [x] Ensure worker VM executes isolated checks and `pdfplumber` parsing inside the microVM fork
- [x] Ensure verified records commit to `/mnt/archil/workspace/promises_v2.db` with evidence in `evidence_ledger`
- [x] Run swarm audit across canary seeds on Archil VM forks

## Phase 5: Automated Quality Gate Suite
- [x] Implement 5 assertions in `tests/test_checks.py`:
  - `assert_no_future_kept_unverified()`
  - `assert_forward_looking_quotes()`
  - `assert_valid_taxonomy()`
  - `assert_unique_canonical_slugs()`
  - `assert_known_canary_cases()`:
    - Whole Foods Mid-Market (#36) -> `KEPT_THEN_REVERSED`
    - Joe Lacob WNBA Championship (#45) -> `IN_PROGRESS`
    - Ed Lee 2011 No-Run Pledge (#8) -> `BROKEN`
    - Central Subway (#11/#12) -> `DELAYED_OR_PARTIAL`
- [x] Run full pytest suite ensuring all tests pass

## Phase 6: Frontend Badges & Demo Export
- [x] Update `docs/app.js` and `docs/styles.css` to render `KEPT_THEN_REVERSED` ("KEPT → LATER CLOSED / REVERSED") and `DELAYED_OR_PARTIAL` ("DELIVERED LATE / PARTIAL") badges
- [x] Export verified v2 database to `docs/data.json`
- [x] Verify static demo preview renders correctly with v2 records
