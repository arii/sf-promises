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
- [x] Eliminate all detector anti-patterns using Impeccable engine across desktop and mobile (`390x844`)

---

## Phase 7: Data Integrity, Sandbox Swarm Evidence Investigation, and Legacy Code Retirement

### 7.1 Deterministic Integrity & Reconciliation (Completed)
- [x] **Category sums reconcile to exactly 62**: Merged `Energy & Infrastructure` into `Environment & Energy` across `src/v2_taxonomy.py` and `docs/data.json` (Sports 4 + Culture 2 + Transit 12 + Housing 15 + Civic 18 + Environment 2 + Infrastructure 2 + Bay Area 7 = 62).
- [x] **Verdict casing normalized**: Fixed row #18 (P36) verdict to lowercase `kept`.
- [x] **Mislabeled neighborhoods corrected**:
  - #2 (P29, Care Not Cash): Updated from "Police Commission Oversight (Citywide)" to "Civic Center & Citywide (Human Services)".
  - #25 (P66, Chase Center): Updated from "Citywide Housing Production Corridor" to "Mission Bay (Chase Center)".
  - #26 (P42, Central Subway): Updated from "San Francisco MUNI Transit Fleet" to "Central Subway (SoMa to Chinatown)".
  - #33 (P30, PSH goal): Updated from "Emergency Communications Center (911)" to "Citywide (Supportive Housing Network)".
  - #51 (P67, Valkyries): Updated from "San Francisco Planning Department" to "Mission Bay (Chase Center)".
- [x] **Limitations section references updated**: Replaced raw internal IDs with public display numbers: #36 (Whole Foods), #23 (Dead & Co), #9 (Parkmerced).
- [x] **Export integrity tests added**: Added automated checks in `tests/test_v2_export.py` ensuring category sum equals promise count, all verdicts are lowercase, all rows have source hashes, and export timestamps are not in the future.
- [x] **Watchdog catch prominent on load**: Set pipeline replay default to `N01` ("Altered quote gets caught") so the quarantine catch is visible immediately.
- [x] **Copy cleanups**: Removed trailing "·" after "intake" and clarified technical schema language.

### 7.2 Evidence & Sandbox Investigation (In Progress / Next)
- [ ] **Run investigations in isolated Archil sandboxes**: Fork worker sandboxes using `v2_sandbox.py` for Keenable search/fetch, kept advocate, and broken advocate with partitioned staging files (`staging/investigate_<id>.json`, `staging/kept_<id>.json`, `staging/broken_<id>.json`).
- [ ] **Write sandbox isolation test**: Verify Sandbox A cannot read `staging/broken_*.json` and Sandbox B cannot read `staging/kept_*.json`.
- [ ] **Investigate Row #50 (P05, 1,500 shelter beds)**: Replace journalist paraphrase ("...didn't last long") with Mayor Lurie's verbatim statement from Jan 8, 2025; set due date to Jul 8, 2025.
- [ ] **Investigate Row #52 (P02, 822 Geary St)**: Verify sf.gov primary source for 822 Geary 16-bed opening on Apr 28, 2025; confirm domain allowlist and record full SHA-256 and 8/8 gate score.
- [ ] **Audit non-forward-looking rows**:
  - Past facts / outcomes (#3, #25, #36, #43, #56, #57): Run `check_forward_looking_quote` and quarantine if not a prospective commitment.
  - Forecasts (#9, #19, #32): Reclassify or quarantine if merely economic forecasts.
  - Questionable "broken" announcements (#39, #44): Review primary evidence.
  - Table fragment (#7, P61): Replace fragment with the full source sentence.
- [ ] **Date audits**: Address date oddities for #56, #37, #60, and label duration-derived dates (#46).

### 7.3 Legacy Code Retirement & Archiving (Planned)
- [ ] **Tag Hackathon baseline commit**: `git tag -a hackathon-2026-11-10 64972c8 -m "Archil hackathon submission"` and push tag upon user confirmation.
- [ ] **Audit importers**: Verify imports of legacy modules (`src/extract.py`, `checks.py`, `arbitrator.py`, `relevance.py`, `schema.sql`, `swarm_runner.py`).
- [ ] **Clean legacy files & folders**: Remove `cleanup.md` and unused legacy modules.
- [ ] **Rename v2 modules to standard names**: Rename `src/v2_*.py` to clean standard module names without collisions.
- [ ] **Verify green test suite**: Keep 188/188 pytest suite green throughout.
