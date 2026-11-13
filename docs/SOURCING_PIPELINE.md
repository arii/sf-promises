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
