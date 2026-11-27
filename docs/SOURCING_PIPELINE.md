# SF Promises & Signals: Sourcing Pipeline Specification & Agent Instructions

## 1. Editorial Vision & Scope
SF Promises is an open, verifiable life-and-culture tracker for San Francisco. While civic and political accountability is vital, the platform tracks commitments and future-facing milestones across the full breadth of San Francisco life:
- **Promises**: Forward-looking commitments whose fulfillment can be empirically evaluated.
- **Projects & Openings**: Venues, transit services, housing developments, parks, restaurants, public art, and major events with announced dates or targets.
- **Claims & Forecasts**: Measurable statements about attendance, weather/climate targets, population, ridership, jobs, or budgets.
- **SF Signals**: Recurring indicators and observations that describe how the city is changing, without forcing a binary kept/broken verdict.

---

## 2. Content Pillars & Coverage Targets

Every search and intake cycle must distribute encounters across all 10 pillars:

| Pillar | Example Commitments & Subjects | Primary Sourcing Targets |
| :--- | :--- | :--- |
| **1. Arts, Music & Nightlife** | Exhibitions, festivals, concerts, murals, venue openings, public art | Museum announcements, venue permits, SF Arts Commission, festival organizers |
| **2. Sports & Recreation** | Team facilities, games, races, park renovations, leagues, public recreation | Golden State Warriors/Valkyries, SF Giants, Bay FC, Rec & Parks Department |
| **3. Food & Local Business** | Restaurant openings, farmers markets, commercial corridors, legacy businesses | SF Eater, SF Business Times, neighborhood merchant associations, liquor license filings |
| **4. Weather & Environment** | Climate targets, sea-level rise programs, shoreline work, urban greening, clean power | CleanPowerSF, SF Environment, BAAQMD reports, Port of SF resilience projects |
| **5. Transit & Movement** | Muni service routes, BART extensions, bike lanes, pedestrian zones, ferries, SFO airport | SFMTA Board, Caltrain, SFCTA, SFO Airport Commission, Bay Ferry |
| **6. Housing & Neighborhoods** | Construction starts, affordable housing quotas, public plazas, navigation centers | Planning Commission, MOHCD, neighborhood community benefit districts (CBDs) |
| **7. People & Demographics** | Community programs, language access, demographic services, senior/youth initiatives | Department of Children, Youth & Their Families (DCYF), Human Rights Commission |
| **8. Work & Opportunity** | Job training, apprenticeships, tech/creative workforce initiatives, small biz grants | Office of Economic and Workforce Development (OEWD), city workforce partners |
| **9. Culture & Social Life** | Civic traditions, parades, community cultural events, shared public norms | Heritage organizations, cultural district boards, community event permits |
| **10. Civic Life** | Official city services, elections, department budgets, legislative enactments | Board of Supervisors, Mayor's Office, SF Controller, agency directors |

---

## 3. Separation of Responsibilities

To prevent bias and preserve evidence purity, the sourcing pipeline runs prior to and strictly isolated from the verification pipeline.

```
[Search Planner Agent]
       │ (generates stratified, outcome-blind query batches)
       ▼
[Discovery & Harvesting Agent]
       │ (retrieves sources, verifies domains, records SHA-256 digests)
       ▼
[Qualification & Intake Agent]
       │ (applies eligibility criteria, assigns date precision & geographic scope)
       ▼
[Intake Candidate Ledger / Review Queue]
       │ (unbiased pool ready for downstream adjudication)
       ▼
[Verification Pipeline: Pro-True, Pro-False & Arbitrator]
```

### Agent A: Search Planner
**Role**: Generates systematic, reproducible search queries without knowing or screening for outcomes.
- **Strict Anti-Outcome Mandate**: Never include outcome terms such as `"failed"`, `"broken"`, `"delayed"`, `"completed"`, `"delivered"`, `"scandal"`, or `"kept"`.
- **Query Structure**: Each query must specify:
  1. Content Pillar (1 of 10)
  2. Geographic scope / neighborhood
  3. Time window (announcement era)
  4. Entity type (artist, company, transit operator, official, non-profit)
  5. Commitment language: `"will"`, `"plans to"`, `"committed to"`, `"scheduled to"`, `"set to"`, `"aims to"`, `"expects to"`, `"opening in"`, `"launching in"`.

### Agent B: Discovery & Harvesting Agent
**Role**: Submits queries via the Keenable Temporal API, ingests contemporaneous documents, locks document bytes, and extracts verbatim quotes.
- **Source Hierarchy**:
  1. *Primary Records* (official statements, press releases, meeting minutes, contracts, verified social posts, permit filings).
  2. *Contemporaneous Reporting* (local news directly quoting the entity and publishing at the time the promise was made).
  3. *Discovery-Only Sources* (snippets, aggregators, newsletters — permitted as leads only; must be upgraded to primary records).
- **Cryptographic Grounding**: Calculates `SHA-256` of saved document bytes immediately upon receipt.

### Agent C: Qualification & Intake Agent
**Role**: Evaluates the statement against the qualification rubric and populates standardized metadata fields:
1. **Attribution**: Identifiable person, team, business, or agency.
2. **Forward-looking Commitment**: Action, opening, delivery, or measurable metric occurring in the future relative to the source date.
3. **Date Precision**:
   - `day`: Exact day specified (e.g., `2024-06-21` &rarr; `June 21, 2024`).
   - `month`: Month and year specified (e.g., `2025-04` &rarr; `April 2025`).
   - `year`: Year only (e.g., `2024` &rarr; `2024`).
   - *Never synthesize artificial `-01` or `-01-01` dates into user-facing text.*
4. **Geographic Scope**:
   - `exact_address`: Physical building/location (e.g., `822 Geary St`).
   - `neighborhood`: Specific neighborhood (e.g., `Mission`, `Tenderloin`, `Chinatown`).
   - `district`: Specific supervisorial district (`District 1` through `District 11`).
   - `regional`: Multi-county Bay Area (e.g., BART, SFO, Bay Ferry).
   - `citywide_centroid`: Citywide policy; coordinates are strictly display centroids, not physical claim addresses.
5. **Missingness Semantics**:
   - `not_applicable`: Field does not apply to this commitment type (e.g., open-ended ongoing program has no due date).
   - `not_yet_known`: Event is scheduled or in progress; date/metric has not yet occurred.
   - `not_captured`: Information exists in principle but has not yet been extracted or verified.

---

## 4. Evidence Model & Reconciliation Standard

The database distinguishes between the total evidence ledger and promise-level verdict citations:
- **Total Evidence Records (124 items)**:
  - *Verdict Evidence (99 citations)*: Primary documents cited directly by affirming and contradicting advocates during arbitration.
  - *Context & Discovery Records (25 items)*: Contemporaneous background reports, initial seed candidate discovery URLs, and superseded citations retained for audit provenance.
- **Contradiction Transparency**: For any promise with competing claims (e.g., 21 commitments with both affirmative and contradicting evidence), the user interface must render both sides side-by-side with the arbitration rule explaining the resolution.
- **Audit Queue Prioritization**:
  1. Promises with 0 linked evidence records (requires primary source harvest).
  2. Promises with 1+ failed checks or warnings.
  3. Promises with unresolved contradictory evidence.

## Keenable 0.3 search and fetch options

Searches ask for 25 results (`search_max_results` in `config/discovery.json`) and send a per-phase `objective` (origin, delivery, survival) so ranking favors the right kind of page. Hosts listed in `config/exclude_domains.json` (social and aggregator sites) are left out. `disable_cards=True` is always set, because card URLs are temporary and would break provenance.
Fetches ask for `max_chars` 400000 (`fetch_max_chars`) so long agendas and PDFs are not rejected as truncated. A page that is still truncated is not archived. A per-page `error` in a fetch response counts as a blocked URL, like a 404, except statuses 429, 500, 502, 503 and 504: those are transient, so `fetch_and_archive` raises `PageTransientError` (a `KeenableConnectionError`) and the URL is recorded as `fetch_connection_error`. `run_live --candidate-batch` then blocks the seed as `SOURCE_FETCH_TRANSIENT_FAILURE`, which is retryable, instead of auditing it.

Each phase makes at most `fetch_attempts_per_phase` fetch attempts per candidate (default 8, in `config/discovery.json`). Blocked attempts count, so a list of dead links cannot cost 25 fetches per phase. A phase that hit the cap records `"fetch_budget_exhausted": true`. The 3-source cap per phase still applies.

Archive size: a full 400,000-character page is saved byte for byte. With 3 sources in each of 3 phases, one candidate can store about 3.6 MB of text, against 7.6 MB for all 21 promise directories in `data/sources` today. The larger cap buys completeness of the archive. The model does not read the whole page. Extraction and outcome material read a 10,000-character window chosen in `src/extract.py` (`_source_segments`, `SEGMENT_WINDOW`). With the flags off, that window is the first 10,000 characters, so a commitment deeper in a long agenda is never offered to the model. With `SF_PROMISES_LONG_DOCS=1` or `SF_PROMISES_OUTCOME_RULES=1`, a page longer than the window is split into chunks of about 1,200 characters. The first chunk (title and dateline) is kept, and the rest are chosen by word overlap with the discovery target and entity, up to the same 10,000-character budget, in document order. Every sentence offered is still an exact substring of the saved bytes, and quotes are re-checked against the saved bytes as before.
Each archived manifest also records `acquired_at` (when Keenable indexed the page, from the search result, or null) and `retrieval` (`indexed`, or `live` if `max_age_hours=0` was used). The SDK's own retries are off (`max_retries=0`); `src/keenable.py` keeps the only retry policy.

## Discovery round 3: verbatim sentence mining

`scripts/discovery_round.py` finds many new commitments as exact sentences from saved, allowlisted pages. It makes no model calls. Leads whose `promise_text` is an exact sentence of a saved source pass the audit far more often than paraphrased ones.

1. **Plan.** `config/discovery_round_3.json` lists SF actors (aliases, official domains, relevant topics) and topics. Queries are actor x topic x commitment template ("expected to be completed by", "will ... by {year}", "plans to ..."). Two windows: recent (2025-01-01 to today) and historical (2016-01-01 to 2023-12-31, for promises whose deadlines have passed). The first 6 combos per actor also get one `site=` query per official domain. `--max-queries` (default 200) caps all searches; the plan interleaves actors and windows so a small cap still touches every actor. 200 is thin (about 1.4 combos per actor per window); use 600 or more for real coverage.
2. **Fetch.** Search results are deduplicated and kept only if `is_allowlisted_url`. Official hosts are fetched first, sequentially, with a per-host delay (`--domain-delay`, default 1 s), up to `--max-fetches` (default 400). Each page is archived with `fetch_and_archive` under its own lead id `R3-<first 10 of sha256(url)>` in `WORKSPACE/sources/`. The record lists the most common non-allowlisted hosts, as input for allowlist proposals.
3. **Mine.** A sentence qualifies when it has a commitment verb, a deadline signal (year 2016-2040, "by end of", fiscal year, "within N years/months"), passes `screen_forward_looking`, names SF or an SF actor (or the page title/lede does), is 40-420 characters, and does not carry only deadlines earlier than the page's publication year. Sentences are scored; the top 3 per page are kept. Each is an exact substring of the saved bytes and passes `screen_saved_source`. Candidates are deduplicated against `docs/data.json`, the seed queues, earlier rounds, and each other. A page whose URL is already a source in the dataset is skipped.
4. **Review.** The round record goes to `data/discovery_round_3_<date>.json` (commit it). The review file goes to `WORKSPACE/staging/discovery_round_3_review_<date>.json` (not committed): each candidate has the sentence and one sentence of context either side. Set `decision` to `accept` or `reject`.
5. **Queue.** `--build-queue REVIEWED.json` writes `seeds/discovery_round_3_targets.json` from accepted candidates. `promised_date` is the page's published date (day precision; candidates without one are skipped), `due_date` is `deadline_from_quote` or null, and ids that collide with existing ones are skipped.

```bash
python -m scripts.discovery_round --dry-run                       # print the plan, no network
KEENABLE_API_KEY=... python -m scripts.discovery_round --workspace DIR --max-queries 600 --max-fetches 400
python -m scripts.discovery_round --build-queue DIR/staging/discovery_round_3_review_<date>.json
python -m src.run_live --queue seeds/discovery_round_3_targets.json --candidate-batch ...
```

The script reads `KEENABLE_API_KEY` from the environment only. It prints the count of searches and fetches, and stops at both budgets (and after 3 consecutive rate-limit errors).
