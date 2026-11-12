# SF Promises: Discovery & Verdict Verification Playbook

This playbook establishes the operational cadence, verification tiers, evidence scoring rubric, and conflict resolution logic for discovering and verifying San Francisco public commitments across autonomous sandbox workers.

---

## PHASE 1: PROMISE DISCOVERY

Find public commitments made by SF entities (politicians, city departments, sports teams, corporations, nonprofits) that are specific, measurable, and time-bound.

### 1.1 Discovery Cadence

- **Monday**:
  - SF Mayor's Office press releases (`sf.gov/news`, `sfgov.org/news`) — last 7 days
  - *SF Chronicle* Politics section (`sfchronicle.com/politics/`) — last 7 days
  - SFMTA News & Updates (`sfmta.com/news`) — last 7 days
- **Wednesday**:
  - Board of Supervisors meeting minutes & Legistar resolutions (`sfgov.org/bos`) — last 7 days
  - *Mission Local* civic reporting (`missionlocal.org`) — last 7 days
- **Friday**:
  - Social media canary feeds (Mayor, city departments) — flagged as *canary only* (0.6–0.7 confidence)
  - SF Open Data (`data.sfgov.org`) new dataset releases and updates
- **Quarterly Deep Dive (Every 3 months)**:
  - News archives sweep: `"SF mayor"`, `"SF city"`, `"commitment"`, `"by 2024/2025/2026"`
  - Review Board resolutions passed in preceding quarter
  - Review City Budget strategic initiatives
  - Community Benefits Agreements (CBAs) from SF Planning
- **Annual Archival (Jan 1)**:
  - Snapshot candidate campaign platforms (Wayback Machine)
  - Snapshot department strategic plans
  - Freeze snapshot of SF Open Data baseline tables

---

## PHASE 2: VERDICT VERIFICATION

Determine if each promise was kept, broken, or remains in progress. Gather evidence and assign a calibrated confidence score.

### 2.1 Verification Sources (Ranked by Confidence)

#### Tier 1: Official Government Records (Confidence: 0.90 – 1.00)
- **City Budget & Spending Data** (`data.sfgov.org/Finance-and-Procurement/`):
  - Check whether allocated/spent funds match the deliverable.
  - Extract budget line item, allocated amount, spent amount, audit dates.
- **Department Performance Reports**:
  - SFMTA (`sfmta.com/about-us/performance-dashboards`): Transit frequencies, line completions, delays.
  - SFPD (`sfgov.org/police/crime-data`): Staffing counts, response times, crime indices.
  - DPH (`sf.gov/departments/department-public-health`): Clinic openings, service capacity metrics.
- **Permit & Construction Records** (SF Planning / DBI `sf-planning.org`):
  - Building permits, conditional use permits, completion certificates.
- **Public Meeting Minutes & Resolutions** (`sfgov.org/bos`):
  - Resolution numbers, roll call votes, enactment milestones.

#### Tier 2: News Reports & Investigative Journalism (Confidence: 0.75 – 0.90)
- **SF Chronicle Investigations**: Fact-checking, progress updates, investigative follow-ups.
- **Mission Local Deep Dives**: Hyperlocal neighborhood tracking, early indicators of stalls.
- **KQED Investigations**: Data-backed public radio reporting and records requests.
- **Nonprofit / Civic Reports**: SF Housing Action Coalition (`sfhousing.org`), SF Bicycle Coalition (`sfbike.org`), SFMTA Riders Union (`sfmtariders.org`).

#### Tier 3: Public Data & Regional Metrics (Confidence: 0.70 – 0.85)
- **SF Open Data Datasets**: Housing units built, homeless shelter capacity, street resurfacing miles.
- **Third-Party Data**: U.S. Census Bureau, HUD homelessness metrics, BART/Caltrain ridership, BAAQMD air quality.

#### Tier 4: Community Reports & Canary Evidence (Confidence: 0.50 – 0.70)
- **Community reports, public comment testimony, social media sentiment**:
  - Must be corroborated with Tier 1 or Tier 2 evidence before establishing a final verdict.
  - Useful for triggering re-investigations of stalled or disputed promises.

---

### 2.2 Verdict Determination Logic

| Verdict | Required Criteria | Confidence Threshold | Typical Evidence Profile |
|---|---|---|---|
| **KEPT** | Objective delivery on or before deadline; verified by primary data or unanimous reporting. | **≥ 0.75** | Operational milestone confirmed by department report + news confirmation. Contradiction count: 0. |
| **BROKEN** | Deadline passed without delivery; or official cancellation, de-funding, or shortfall. | **≥ 0.75** | Target deadline elapsed; audit records or performance data show target unmet. |
| **IN PROGRESS** | Deadline in the future; verifiable work underway with demonstrable pace. | **≥ 0.70** | Budget allocated, permits issued, active construction/hiring. Includes `completion_percentage` and `likelihood_of_completion`. |
| **UNDECIDED** | Conflicting evidence, unmeasurable vague claim, or insufficient primary documentation. | **< 0.70** | Vague metric (e.g., "improve safety"), contradictory claims without primary tie-break. |

---

### 2.3 Evidence Scoring Schema

```json
{
  "evidence_id": "E-P02-001",
  "promise_id": "P02",
  "source_url": "https://sf.gov/news/mayor-breed-announces-opening-crisis-stabilization-center",
  "source_type": "official_government",
  "source_tier": "Tier 1",
  "source_credibility_score": 10,
  "evidence_text": "The 24/7 Crisis Stabilization Center officially opened today at 822 Geary St...",
  "evidence_date": "2025-04-28",
  "supports_verdict": "kept",
  "evidence_strength": 0.95,
  "is_primary_source": true,
  "is_contradicted": false,
  "notes": "Department press release accompanied by facility licensing documentation."
}
```

**Evidence Strength Bands:**
- `0.95 - 1.00`: Official government record (budget line item, certificate of occupancy, enacted resolution).
- `0.85 - 0.94`: Mainstream investigative news with on-the-record department attribution.
- `0.75 - 0.84`: Nonprofit or advocacy research report with data methodology.
- `0.65 - 0.74`: News summary without primary source documentation.
- `0.55 - 0.64`: Community testimony or social canary signal.
- `< 0.45`: Uncorroborated opinion or unsourced assertion.

---

### 2.4 Contradiction Detection & Conflict Resolution

When evidence presents contradictory outcomes (e.g., government announces 1,000 shelter beds opened, while investigative reporting notes only 400 are staffed and operational):
1. **Timestamp Check**: Evaluate publication dates. Newer operational inspections supersede earlier projection announcements.
2. **Definitional Precision**: Distinguish between *allocated funding*, *permitted beds*, and *staffed/operational capacity*.
3. **Hierarchy of Sources**: Official audited data overrides unverified press statements; detailed investigative reporting with on-the-record inspections overrides high-level summaries.
4. **Confidence Degradation**: When unresolvable discrepancies exist, reduce confidence score (e.g. from 0.95 to 0.75 or 0.60) and document both affirming and contradicting advocate positions.

---

### 2.5 Special Cases

1. **Private Corporations** (e.g. Visa Mission Rock, PG&E EV Chargers):
   - Verified via SEC 10-K filings, corporate sustainability audits, CPUC regulatory filings, and news investigations.
2. **Sports Franchises** (e.g. Golden State Warriors, Valkyries, Bay FC):
   - Verified via league official schedules, box office disclosures, venue lease agreements, and venue inspection permits.
3. **Nonprofits & Advocacy Alliances** (e.g. SF Housing Action Coalition):
   - Verified via Form 990 filings, grant compliance deliverables, and HUD data.

---

### 2.6 Archil Parallel Execution Model

Verification tasks execute across disposable **Archil worker sandboxes** forked from the stopped `sf-promises-golden` template:
- Concurrency bounded via an `asyncio.Semaphore` (typically 1 to 3 parallel workers).
- Each worker verifies one candidate lead: downloads raw bytes, validates allowlisted origin, matches SHA-256 digest, checks exact verbatim substring, runs advocate evaluation, and returns a structured decision.
- Workers are stopped and permanently deleted immediately upon task completion, ensuring zero state pollution.
