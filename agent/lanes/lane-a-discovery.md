# Lane A — Discovery

## Mission
Find public commitments made by SF entities (politicians, city departments, sports teams, corporations, nonprofits) that are specific, measurable, and time-bound. Hand off vetted candidates to Lane B (Fetcher) and Lane C (Extractor).

## Scope & Sources

### 1. Primary Sources (Official Commitments — High Confidence)
- **City Hall & Government**:
  - Mayor's Office press releases (`https://sfgov.org/news`, `https://sf.gov/news`): Search for "will", "commit", "pledge", "promise", "goal", "target", "by [date]".
  - Board of Supervisors minutes & resolutions (`https://sfgov.org/bos/meetings-agendas-minutes`, Legistar): Resolutions (File #), Ordinances, Board Reports. Look for "The City commits to...", "By [date], the City will...".
  - City Department announcements: SFMTA (`sfmta.com/news`), SFPD (`sfgov.org/police`), DPH (`sf.gov/departments/department-public-health`), SFPUC (`sfpuc.gov`, `cleanpowersf.org`), SFO (`flysfo.com`).
  - City Budget documents & strategic plans (`sfgov.org/budget`): Look for "By FY [year]", "Within [timeframe]", "Target: [metric]".
- **Political Candidates & Campaign Promises**:
  - Campaign websites & platforms (e.g. 100-day plans, policy platforms).
  - Candidate debates & town halls: Specific policy commitments transcribed from public video archives.
  - Voter guides & questionnaires: SF Chronicle voter guides (`sfchronicle.com/politics/`), League of Women Voters (`lwvba.org`).
  - Election victory speeches: First 100 days commitments, priority lists.

### 2. Secondary Sources (News & Public Records — Verification & Discovery)
- **Local News Archives**:
  - *SF Chronicle* (`sfchronicle.com`)
  - *Mission Local* (`missionlocal.org`)
  - *KQED* (`kqed.org/news`)
  - *The Examiner* (`sfexaminer.com`)
  - *Curbed SF* (`curbed.com`)
  - *The Frisc* (`thefrisc.com`), *SF Standard* (`sfstandard.com`)
- **Official Records & Data Dashboards**:
  - SF Open Data (`data.sfgov.org`)
  - SFPD Crime Data Dashboard (`sfgov.org/police/crime-data`)
  - SFMTA Performance Dashboard (`sfmta.com/about-us/performance-dashboards`)
  - SF Housing Portal (`sf.gov/housing`)
  - Controller's Office & Budget Reports (`sfgov.org/budget`)

### 3. Tertiary Sources (Community & Social — Lower Confidence / Canary)
- **Social Media**: `@LondonBreed`, `@DanielLurieSF`, `@SFMayor`, `@SFBoard`, `@SFMTA` (Twitter/X, Facebook, LinkedIn). Must be flagged as "needs verification from official source" (confidence 0.6–0.7).
- **Community Reports & Advocacy Groups**: SF Housing Action Coalition (`sfhousing.org`), SFMTA Riders Union (`sfmtariders.org`), SF Bicycle Coalition (`sfbike.org`), Community Benefits Agreements (CBAs via SF Planning archives).

---

## Owns / Touches
- **Writes**: `seeds/candidates_discovered.json`, candidate queue in staging.
- **Must Not Touch**: `promises`, `verdicts`, checks, demo page, production database.

---

## Extraction Rules & Required Fields

Each discovered candidate must satisfy the **Relevance & Worthiness Gate (≥ 5/8)**:
1. `subject` (who): Formal entity / speaker name (`entity_canonical_name`).
2. `action` (what): Observable, binary or quantifiable deliverable.
3. `deadline` (when): Explicit ISO 8601 date (`YYYY-MM-DD`) or inferrable timeframe.
4. `verbatim_quote`: Exact character substring from the source document.
5. `source_url`: Allowlisted primary or secondary URL.
6. `source_type`: `official_government`, `news_mainstream`, `news_local`, `corporate_release`, `legal_record`, or `advocacy_canary`.

---

## Archil Sandbox Execution
Where possible, candidate verification, URL screening, and source validation run within **Archil disposable sandboxes** (`run_in_fork` from `sf-promises-golden`), preserving isolation and preventing host pollution.
