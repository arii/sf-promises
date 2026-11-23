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

### 3. Progressive Disclosure & Library-Driven UX (Guide 1 & Feedback Follow-up)
- **Library Vendoring (`docs/list.min.js`)**:
  - Integrated `list.js` (19KB, zero runtime dependencies) directly into GitHub Pages static distribution for client-side multi-facet search, sorting, and filtering.
- **In-Line Accordion Rows (`tr.promise-accordion-row`)**:
  - Main table rows now clamp long verbatim quotes to 2 lines (`-webkit-line-clamp: 2`).
  - Clicking any row or expand chevron smoothly expands an inline accordion drawer displaying the full unabridged quote, primary source link with source tier badge, SHA-256 hash with 1-click clipboard copy, advocate findings (Sandbox A vs Sandbox B), and deep inspect modal launcher.
- **Sticky Table Headers & Directional Sorting**:
  - Set `position: sticky; top: 0; background: #0f172a;` on `thead`.
  - Added interactive sort headers with visual directional arrows (`▲`/`▼`) on `# Rank`, `Entity & Area`, `Verbatim Commitment`, `Timeline`, and `Verdict`.
- **Removable Filter Chips Tray**:
  - Added `#active-chips-tray` with individual removable chips (`×`) for entity, verdict, category, and search query, plus a `"Clear all ×"` button.
- **Row Density Toggle**:
  - Added segmented switch (`Comfortable` vs `Compact`) toggling row padding and quote line-clamping (2 lines vs 1 line).
- **Modal Plain-English Summary & Collapsible Technical Provenance**:
  - Added "WHAT WAS PROMISED" plain-English summary card at the very top of the inspect modal showing verbatim quote, speaker/role, target dates, and plain-language outcome explanation.
  - Collapsed technical audit logs (SHA-256 hashes, file paths, run ID, sandbox worker UUIDs) into an expandable `<details class="tech-audit-drawer">`.
  - Prevented truncated modal headers by allowing wrapping and formatting clean titles (`#51 (P04) · Golden State Valkyries: Chase Center`).
- **Data & Category Harmonization**:
  - Unified counts across hero tally, Outcome Distribution box, table status, and pagination (`54 VERIFIED`).
  - Formatted all verdict enums into human-readable strings (`In Progress`, `Kept`, `Broken`, `Undecided`, eliminating raw `IN_PROGRESS`).
  - Harmonized category naming to `"Civic Governance"` across pill bar, dropdown, and data payloads; hid empty category pills with `(0)` items.
  - Cleaned up advocate output notes, replacing raw agent search/cut-rule notes with user-facing copy.
- **Responsive & Design Verification**:
  - Mobile card fallback (<768px) smoothly incorporates accordion drawers without horizontal scroll (`scrollWidth=390, innerWidth=390`).
  - Impeccable tool detector exited with code 0 (0 warnings/errors).
  - Pytest: **198/198 passed green**.

### 4. Phase 1 Discovery Integration, Archil Sandbox Verification & Hugging Face
- **Discovery Lane Brief (`agent/lanes/lane-a-discovery.md`)**:
  - Formalized discovery workflow for public commitments across SF entities.
  - Sourced primary (Mayor, BOS, City departments, budget, candidate platforms/debates), secondary (Chronicle, Mission Local, KQED, Examiner, Curbed, SF Open Data), and tertiary (civic advocacy, social media canaries) sources.
  - Linked `Lane A — Discovery` to root `README.md` dispatch table.
- **Codebase Review & Discovery Fixes**:
  - Fixed missing `import re` in `src/discovery.py` caught during static review.
  - Expanded allowlists in `src/evidence.py` to include `curbed.com`, `sfhousing.org`, `sfmtariders.org`, `sfbike.org`, and `lwvba.org`.
  - Cleaned unused variables and imports in `src/advocates.py`, `src/candidate.py`, and `src/run_live.py`.
  - Static analysis: `pyflakes src/` cleanly returns 0 errors.
- **Live Archil Sandbox Execution**:
  - Tested live microVM sandbox forking via `src/sandbox.py:run_in_fork` with `archil.Archil` client against golden template `01a1cd7a-6b6d-7bbd-a49d-cfad0054435e` (`sf-promises-golden`).
  - Successfully spawned disposable worker `01a1d1b2-8390-7c85-907d-8a0290f70c36`, executed isolated checks (`Linux 6.18.39`), cleanly stopped and deleted the worker microVM, and reconciled status in `WorkerLeases`.
- **Hugging Face Hub Dataset**:
  - Published 51-column enriched dataset at `https://huggingface.co/datasets/onasafari/sf-promises` including `promises.csv`, `promises.sqlite`, `quarantined.csv`, `SCHEMA.json`, `data_summary.json`, and dataset card.
- **Test Suite**:
  - **198/198 tests green**.

### 5. Durability Engine, Playbook Verification & Outside-the-Box Expansion
- **Durability Cron Engine (`src/durability_cron.py` & `tests/test_durability.py`)**:
  - Implemented `find_due_rechecks` using `compute_next_check_at` (+90 days for kept, +30 days for in-progress, +60 days for undecided).
  - Implemented `run_durability_cycle` executing append-only transitions via `reopen_promise_verdict` without erasing historical provenance.
  - Added full test suite in `tests/test_durability.py`.
- **Media & Image Tracking**:
  - Added `image_url` and `media_caption` support to data schemas and UI modal (`modal-media-container`, `modal-media-img`, `modal-media-caption`).
- **Playbook Verification Engine (`src/playbook_verifier.py`)**:
  - Implemented 4-tier source scoring, contradiction detection, and vague promise screening.
  - Supported semaphore-bounded parallel execution across Archil sandboxes.
- **Outside-the-Box 10-Year Trends & Prominent SF Leaders**:
  - Cataloged 15 deduplicated promises across soft-story seismic retrofits, seawall bonds, all-electric gas bans, coastal retreat, Marc Benioff, Kyle Vogt (Cruise), Jack Dorsey (Square), Westfield default, SF Bicycle Coalition, Another Planet Entertainment, and Castro Theatre.
- **Full Test Suite**:
  - **213/213 tests passing green**.

### 6. Data-Quality Audit Fixes, Outcome-Blind Sourcing, Multi-View Explorer & HF Dataset Viewer Fix
- **8 Data-Quality Audit Fixes (`scripts/enrich_dataset.py`, `docs/export_data.py`)**:
  - Preserved explicit date precision (`promise_date_precision`, `due_date_precision`, `completion_date_precision`) and display formatting so year/month records do not fabricate `-01-01`.
  - Reconciled all `124` SQLite evidence rows against the `99` verdict-cited claims (`11` background context, `8` intake screening, `6` duplicate/superseded cross-references) and ensured `verdict_supporting_evidence_count >= 1` across all 54 commitments.
  - Exposed verification exceptions (`all_checks_passed`: `47` pass, `7` flagged on `P82, P83, P17, P61, P37, P57, P58`, totaling `22` flagged/unrecorded checks).
  - Exposed contradictory evidence summaries and arbitration explanations across all `21` affected commitments (`has_contradictory_evidence`).
  - Consolidated canonical entity taxonomy across `31` canonical entities with explicit `entity_sample_warning` (`n=1` / `< 3` caution).
  - Distinguished `exact_address` (`12`) from `is_centroid` display centroids (`42`) and corrected `P64` to Treasure Island / `D6`.
  - Added explicit missingness semantics (`present | not_applicable | not_yet_known | not_captured`) across date, address, and district fields.
  - Exported the prioritized operational queue to `data/evidence_review_queue.json`.
- **3-Stage Outcome-Blind Sourcing Pipeline (`src/sourcing/`, `docs/SOURCING_PIPELINE.md`)**:
  - Built `SearchPlanner`, `DiscoveryHarvester`, and `QualificationIntakeAgent` spanning all 10 SF content pillars and all 11 supervisor districts (prioritizing gap districts D2, D4, D8, D11).
  - Audited `63` encountered candidates into `data/intake_candidate_register.json` and `data/intake_ledger.csv` (`24` qualified, `38` needs_review, `1` rejected).
- **Interactive Multi-View Explorer (`docs/index.html`, `docs/app.js`, `docs/styles.css`)**:
  - Added Explore view switcher across **Table**, **Map & Districts** (inline SF + SFO inset SVG map + D1–D11 coverage bars), **Entity Profiles** (`n<3` caution badges), and **Quality Audit** (KPI cards, 10-pillar matrix, clickable review queue), maintaining `0px` CLS and `6,303px` mobile `scrollHeight` (< `6,500px`).
- **Hugging Face Dataset Viewer (`scripts/upload_to_huggingface.py`)**:
  - Isolated split files into `data/{commitments,standardized_16col,quarantined,intake_ledger}/train.csv` with explicit YAML `configs` and `--validate-only` CLI check.
  - Verified live on `onasafari/sf-promises`: `datasets-server` `is-valid` returns `{"preview":true,"viewer":true,"search":true,"filter":true,"statistics":true}` with all 5 configs (`default`, `commitments`, `intake_ledger`, `quarantined`, `standardized_16col`) and `failed: []`.
- **Verification**:
  - `.venv/bin/pyflakes src/` cleanly returns 0 warnings/errors.
  - **236/236 tests passing green** in `.venv/bin/pytest tests/`.

## 2026-11-23: Archil workspace mounted; shared promises.db cleanup

- Mounted the Archil disk at `/mnt/archil` on host s5 with
  `scripts/mount_archil.sh` (`--shared`). Git `961dc2f`, clean tree.
- Pre-change backup: `/mnt/archil/backups/backup-20261123T113801Z-961dc2f`
  (`quick_check` ok, 126 source hashes verified, 52 baseline FK violations).
- Deleted leftover `promises.db.pre-e1b.bak` (older legacy copy, 62 promises
  / 85 verdicts) and `promises_v2.db` (+`-shm`, empty `-wal`; v2 schema,
  2 pending rows). Copies with SHA-256 sums:
  `/home/ari/backups/sf-promises-leftovers-20261123/` on s5.
- `promises.db` FK cleanup (approved by the owner): deleted 13 rows whose
  `promise_id` has no `promises` row: 7 `sources` (P97 x2, P68, S4 x4),
  4 `relevance_checks` (P68), 1 `change_log` (P68), 1 `quarantined` (P68).
  Kept 39 `test_cases` rows for unpublished promises (P32–P34, P45–P56,
  P68–P79, P97, S4–S14) because 12 `test_results` rows reference them; they
  are the recorded legacy baseline. Script: `/home/ari/backups/fk_cleanup_20261123.py`.
- First commit attempt failed with "disk I/O error" and left a hot journal:
  on a `--shared` mount SQLite needs a delegation on the workspace
  directory to delete its journal. Rolled back automatically on reopen
  (verified on a copy first). Before writing `promises.db`, run
  `archil checkout /mnt/archil/workspace` and
  `archil checkout /mnt/archil/workspace/promises.db`.
- Post-change backup: `/mnt/archil/backups/backup-20261123T114325Z-961dc2f-post-fk`
  (`quick_check` ok, 126 source hashes, 39 baseline FK violations).
- Live counts after cleanup: promises 62, verdicts 87, quarantined 0,
  sources 115, test_cases 113, test_results 144.

## 2026-11-23: First v2 audit of qualified discovery candidates

- New v2 database on the Archil disk: `/mnt/archil/workspace/v2/promises.db`
  (sources in `v2/sources/`, agent lane in `v2/agent-lane/`). The legacy
  `promises.db` and the published `docs/data.json` are unchanged.
- Queue: `seeds/discovery_targets.json` (45 qualified register candidates with
  day-precision dates; built by `scripts/build_discovery_queue.py`). Ran
  `python -m src.run_live --db /mnt/archil/workspace/v2/promises.db --queue
  seeds/discovery_targets.json --candidate-batch ...` on 11 of the 15
  candidates whose deadlines have passed, plus one future-deadline pilot
  (DISC-20261122-013): 12 candidates in total. Lane
  requests were answered by coding agents (extraction, advocates, and a
  skeptical second reader for verify_origin / verify_evidence).
- Result: 0 published, 12 quarantined (9 NO_VERIFIABLE_ORIGIN,
  2 INSUFFICIENT_OUTCOME_EVIDENCE, 1 AMBIGUOUS_EVIDENCE). Not yet run (33):
  the past-deadline ARTS-02, ARTS-03, TECH-01 and DISC-20261122-002, 23 more
  future-deadline candidates, and 6 with no deadline (45 = 12 + 33).
- Why so few pass: (1) the "outside the box" register entries are
  paraphrases; archived sources rarely contain a sentence with the same
  deliverable and an explicit commitment date; (2) news pages often lack a
  dateline the verifier accepts ("on Tuesday"); (3) promises with future
  deadlines cannot be published by v2 because it requires delivery and
  survival evidence; (4) segmenting splits some sentences (ordinance text,
  strikethrough artifacts), and outcome segments can be bare fragments.
- Robustness fixes made during the run: Keenable 502/503/504 and connection
  errors retry (30 s, 3 tries). A URL still unreachable after that is
  recorded as blocked and the seed ends `blocked`
  (SOURCE_FETCH_TRANSIENT_FAILURE, retryable) instead of being audited, so an
  outage is never recorded as a quarantine. A 422 "different page" fetch is a
  permanent per-URL block like 404/410;
  `SF_PROMISES_LANE_TIMEOUT` raises the lane wait for agent-answered runs.

## 2026-11-23 · Issues #44 / #83 / #82 (branch feat/issues-44-83)

- **#83 entity images:** 11 entities have a self-hosted 160px avatar in
  `docs/media/entities/` (Commons only, exact titles in `config/media_entities.json`,
  licenses from `extmetadata`: PD/CC0/CC BY/CC BY-SA only, sha1 checked against the
  Commons API, sha256 of the original recorded in `docs/media/manifest.json`).
  Skipped for lack of a clearly correct official portrait or logo: SFMTA (Commons has only
  the Muni worm and old Muni logos, not the SFMTA mark), Port of San Francisco and Golden State
  Valkyries (game/venue photos only), Ed Lee (no official portrait), Joe Lacob (tiny image).
  Commons tags the logos public domain (simple shapes/text), but they remain trademarks.
- **Not done: `docs/data.json` refresh.** `entity_image_path` and `entity_image_credit` come from
  `docs/export_data.py`, which needs the database. data.json was not hand-edited, so avatars
  appear on the page only after the next reviewed export.
- **#44 map:** kept the self-hosted SVG (no third-party tiles, per #82). Added marker
  clustering, tap-to-open drawer and 44px touch targets on mobile. Not done: MapLibre or any
  real basemap, story-card images, the hero pipeline teaser, inline timelines.
- **#82 not done on purpose:** licenses of sf.gov, flysfo.com, sfmta.com and sfrecpark.org images
  are unconfirmed, so P02, SFO-01, SFO-02, P21 and P41 keep the opt-in hotlink. Press images
  (P04-P07, P10, P83) are never rehosted.

## 2026-11-23: review fixes for #44 / #83 (feat/issues-44-83)

- Map: SVG is `role="group"` (static layers `aria-hidden`); clustering merges closest pair until stable (no overlapping hit circles, checked on real data at 5 widths); cluster open focuses the list, Escape or "Close list" returns focus to the marker; single tap opens the drawer only; resize re-render restores focus. `lastMapMobile` removed.
- Avatars: `docs/app.js` loads same-origin `media/manifest.json` and maps entity names, so avatars show without regenerating `docs/data.json` (no database touched). Credit links the licence for CC BY / CC BY-SA, 0.75rem.
- Manifest/media: `logo` flag and `restrictions` recorded (Giants: `trademarked`, from the review's Commons check; the other logos carry `logo: true` and were not re-queried). Logo credit shows "Logo is a trademark of its owner". `check_approved` rejects a license that differs from `suggested_license`.
- Open: re-run `scripts/fetch_media.py stage-entities` when network is allowed to fill `restrictions` for all entries; regenerate `docs/data.json` with the export when the production database may be used.

## 2026-11-23 · #44 street basemap (branch feat/basemap-44)

- **Map & Districts street map:** self-hosted MapLibre GL JS 5.24.1 + pmtiles 4.5.0 +
  @protomaps/basemaps 5.7.2 ("light" flavor) reading `docs/map/sf-z14.pmtiles` (Protomaps build
  20261123, SF + SFO, z0–14, © OpenStreetMap contributors, ODbL). Assets and licenses are listed in
  `docs/map/README.md` (7.47 MB in total). `index.html` does not reference them: `app.js` inserts the
  `<script>`/`<link>` tags the first time the Map view opens.
- Records are a clustered GeoJSON source coloured with `VERDICT_COLORS`. Display centroids get a ring,
  as on the SVG map. A tap opens the record drawer. A cluster zooms in, or lists its records when they
  share one coordinate (14 records sit at 37.7749,-122.4194). Hit box 44px on phones. Cooperative
  gestures, max zoom 16, padded max bounds. Labels use only the three shipped Noto Sans stacks.
- "Street map" / "Simple map" toggle, remembered in `localStorage` (`sfp-map-mode`). The SVG map stays
  the keyboard-accessible option and is used automatically without WebGL or if MapLibre fails to load.
- PMTiles needs HTTP Range: GitHub Pages serves it, `python3 -m http.server` does not (use a
  Range-capable server for local previews).
- Checked in headless Chrome at 390 and 1280 px: zero third-party requests, zero 4xx/5xx, zero JS
  errors. Touch: one finger scrolls the page, two fingers pan, pinch zooms. Fallbacks checked by blocking
  maplibre-gl.js and by stubbing WebGL.
- Also: the "Watch one promise get checked" walkthrough now starts its timer on load (it showed
  "Pause" but never advanced). Pagination and back-to-top labels are vertically centred, and the
  "Technical & Audit Specifications" accordion is styled like the limits accordion.
- Not done (other #44 items, out of scope): story-card images, hero pipeline teaser, inline timelines.
