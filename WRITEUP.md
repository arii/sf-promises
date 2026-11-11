# SF Promises — how it works, and four verdicts worth arguing about

How the pipeline turns a public commitment into a sourced verdict, plus four
real cases from `promises.db` where both advocates had something to say —
including the Whole Foods store that opened on time and closed a year later.

## 1. How everything works

One promise moves through six stages. Models draft; only code decides.
Each stage runs in its own sandbox with its own writes (details below).

1. **Fetch (Lane B, `fetcher` sandbox).** A URL is fetched, the bytes are
   saved to `/mnt/archil/workspace/sources/<sha256>.md`, and a `sources`
   row records URL + fetch time + hash. Web search and page fetch run
   through **Keenable** (query mechanics below). Nothing downstream may use
   a source that isn't a saved file with a matching hash. A snippet is
   never a source.
2. **Extract (Lane C, `extractor` sandbox).** A model reads *saved files
   only* (no network, no DB writes) and proposes `promises_pending` rows.
   `promise_text` must be a substring of the saved source, or the row is
   flagged `quote none` and headed for quarantine.
3. **Relevance gate (sandbox D, `src/relevance.py`, code only, zero model
   calls).** Each candidate scores 0–2 on real-promise, measurable,
   SF-relevant, interesting. Publish needs total ≥ 5 AND real-promise ≥ 1;
   anything lower, or a restated vote, goes to `quarantined` with
   `relevance_low`. Scores land in `relevance_checks`; the gate never
   changes a verdict.
4. **Advocates (sandboxes A kept / B broken, run in parallel).** The kept
   advocate finds affirming sources, the broken advocate contradicting
   sources. They can't see each other and hand off only via staging files
   (`staging/kept_<id>.json`, `staging/broken_<id>.json`) — never direct
   DB writes. An advocate that finds nothing records `none found` — no
   second search, no invented claims.
5. **Arbitrator (sandbox C, `src/arbitrator.py`, code only).** Every claim
   runs seven checks in fixed order — domain allowlist → hash re-check →
   verbatim quote → speaker → date consistency → evidence type →
   promise-id match — and *every* check gets a `verifications` row, pass
   or fail. Surviving claims go to the deterministic rubric (§2). One
   transaction then writes the `promises` + `verdicts` + `verifications`
   rows (+ `evidence` rows for passing claims, `change_log` entry) and
   deletes the pending row. Only this lane writes those tables.
6. **Demo export (`demo` sandbox).** The static page renders from a DB
   export (`demo/export_data.py` → `demo/data.js`), tallies counted from
   actual verdict rows, latest verdict per promise. History is
   append-only: re-opened cases get a *new* `verdicts` row; nothing is
   edited in place.

### Where everything lives

`/mnt/archil/workspace/` holds exactly three things (observed Nov 11):

- **`promises.db`** (725 KB) — the SQLite database, 20 tables (§1.1).
- **`sources/`** (122 files, 304 KB) — fetched source documents, one file
  per fetch, named `<sha256>.md`. Every `sources` row points at one file;
  every evidence quote is verified against these bytes.
- **`staging/`** (124 files, 63 KB) — advocate handoff bundles,
  `kept_<id>.json` / `broken_<id>.json`. Raw input to arbitration,
  including claims that were later dropped (e.g. P83's Trinity release)
  and `none found` notes.

### §1.1 The database: 20 tables

`src/schema.sql` defines the schema; row counts verified against the live
DB this session:

- **Reference:** `cities`, `entities` (who promised: politician, company,
  sports_team, artist, official, other).
- **Promise lifecycle:** `promises_pending` (0 rows — intake fully
  resolved) → `promises` (**62** rows) or `quarantined` (**1** row: P68,
  `relevance_low`), with every transition logged in `change_log`.
- **Sources:** `sources` (**122** rows, one per saved file),
  `legistar_matters` (Board of Supervisors matters via Legistar API).
- **Evidence:** `evidence` (**124** rows — only claims that passed all
  seven checks), `outcome_evidence` (external-dataset measures).
- **Verdict:** `verdicts` (**85** rows — includes re-opens as new rows),
  `verifications` (**1,208** rows — one per check per claim),
  `relevance_checks` (gate scores per criterion).
- **Tests:** `test_cases`, `test_runs`, `test_results` (Lane F harness:
  P01–P12 ground truth, N01–N12 planted catches).
- **Telemetry:** `events`, `traces`, `metrics`, `agent_runs` — schema
  exists, but all four tables are **empty (0 rows)**. No per-step timing
  or sandbox audit trail was recorded; the run history lives in
  `WORKING_NOTES.md` / `QUESTIONS.md` prose instead.

Note the FK contract in the write path: the publish branch runs with
`PRAGMA foreign_keys=ON`, the quarantine branch with `OFF` — a
quarantined row must *not* have a `promises` parent, so `ON` would
reject every quarantine write by design.

### §1.2 How Keenable was queried

Two endpoints, two auth modes (both confirmed in artifacts):

- **Search (keyless):** `POST https://api.keenable.ai/v1/search/public`
  via `.agents/skills/keenable-web-search/scripts/search.py` (stdlib
  only, `mode: pro`, `X-Keenable-Title` attribution header, no key).
  Supports natural-language queries plus `site:`, domain exclusions, and
  published/acquired date filters. Real queries from bundle notes:
  `'Dead & Company Sphere residency 2024 Las Vegas concerts announced'`,
  `site:sfchronicle.com 'Dead & Company Golden Gate Park …'`,
  `'Bay FC Oracle Park match August 2025 cancelled postponed moved'`.
- **Fetch (keyed):** `GET https://api.keenable.ai/v1/fetch` with
  `X-API-Key` (`KEENABLE_API_KEY` in `.env`, never committed) — "never
  pass `prompt`". 38 of the 120 saved `.md` sources carry a
  `Fetched: keenable keyed` header; the rest came from direct fetches
  (Legistar API, `httpx` for PDFs, indexed copies such as P06's SFMTA
  fatality report after the origin 403'd).
- **Budgets:** the demo ran under a 30-fetch / 20-search discipline
  (Lane B logged 13–18 fetches, fix batch +2/+2); the cap was lifted for
  the Tier-2 push since the keyed tier allows 100k req/mo. Final
  post-lift totals were never reconciled — an open bookkeeping gap.

Deliberately *not* Keenable: extraction (network forbidden by lane
contract), PDFs (`httpx` + `pdfplumber` with page numbers), Legistar
(direct `webapi.legistar.com` queries), and the verdict itself (zero
network, zero models — `src/arbitrator.py` reads staging files and
the DB only).

### §1.3 Where things were sandboxed

The design (per `08-agent-setup.md` + lane briefs): four verdict
sandboxes — **A** kept advocate, **B** broken advocate, **C** arbitrator
(code only), **D** relevance gate (code only) — plus `fetcher`,
`extractor`, `demo`, and `test` sandboxes, each an Archil Firecracker
microVM mounting the same shared disk, separated by staging-file
ownership (each role writes only its own files) and the single-writer
rule (only C touches `promises`/`verdicts`/`verifications`/
`quarantined`, one transaction per promise).

What actually held at the event: the *separation* held — advocates ran
as separate processes with disjoint staging files, the arbitrator ran as
plain code over staging + DB, and ownership rules were enforced by lane
contract and review. But Firecracker-microVM isolation was **never
verified** (the demo's own label: "separated processes, not
Firecracker"), and the schema's sandbox audit trail (`events`,
`agent_runs`, `traces`, `metrics`, each with a `sandbox` column) is
empty. So: sandboxing was real as a discipline, aspirational as
infrastructure — worth knowing before claiming isolation to anyone.

## 2. The verdict machine in brief

Evidence tiers (`src/arbitrator.py`): vote / ordinance / budget_line /
contract_milestone / regulator_order / filing = **4**; opening / count =
**3**; news_report = **2**; press_release / announcement = **1**.
The rubric, in rule order:

| # | Fires when | Verdict |
|---|-----------|---------|
| 1 | Due date passed, zero passing kept claims | broken |
| 2 | 90+ days, zero passing claims either side, due not passed | stalled |
| 3 | Numeric target + broken claim ≥ tier 2 | broken |
| 4 | Kept ≥ tier 3, zero passing broken claims | kept |
| 5 | Broken ≥ tier 2, kept < tier 3 | broken |
| 6 | Due in future, neither side settles it | in_progress |
| 6b | Genuine partial completion, full scope unresolved | in_progress |
| 7 | Wording ambiguous (records `reading_used`) | undecided |
| 8 | Otherwise | undecided |

Rule order matters more than it looks — see P11 below.

## 3. Four interesting examples

All four were re-run independently for this write-up: every evidence row's
checks re-executed against the saved source files on disk, then the rubric
re-applied (`/tmp/verdict_probe.py`, read-only, not committed). Quotes below
are verbatim from the `evidence` rows.

### P83 — Whole Foods at Trinity Place: kept, then closed (kept-as-worded)

> "Whole Foods Market will open its new 64,737-square-foot San Francisco
> flagship store at Trinity Place (1185 Market Street) in San Francisco's
> Mid-Market neighborhood on Thursday, March 10."
> Speaker: Whole Foods Market · promised 2022-02-17 · due 2022-03-10.

- **Kept case (1 passing claim, tier 3 opening):** "The closure comes just a
  year after the store opened at the Trinity S.F. apartment building at
  Market and Eighth streets in March 2022."
  (`sfchronicle.com`, April 2023 closure article.)
- **Kept's second claim was dropped:** the Trinity opening-day release
  ("Whole Foods Market has opened its new 64,737-square-foot San Francisco
  flagship store … on Thursday, March 10") failed the domain allowlist —
  `trinitysf.com` is unlisted — so it never became an `evidence` row. It
  survives only in `staging/kept_P83.json` and the `verifications` audit
  trail (`VFY-P83-07`, domain fail, everything else pass).
- **Broken case:** empty bundle, with this note: *"none found: broken search
  returned only the April 2023 closure … a post-fulfillment closure does not
  contradict the March 10, 2022 opening. No source disputes the opening
  date."*
- **Rubric:** kept tier 3, zero passing broken claims → Rule 4 → **kept**.
  Re-run agrees.

**My verdict: kept-as-worded, and the caveat is the point.** The promise was
an opening date; the opening happened. But the store closed ~13 months later
over safety concerns, and the pipeline is structurally blind to that: a
later closure *confirms* an opening promise rather than contradicting it, so
even a perfect broken advocate files `none found`. Note the irony the
system produced honestly: the verdict's only evidence is the closure
article, since the actual opening-day primary source was inadmissible on
domain. (The broken bundle gestures at the closure as "a separate promise,
P70 in another partition" — no P70 exists in this database, so the closure
currently falls through the cracks entirely.)

### P05 — 1,500 shelter beds in six months: real progress, still broken

> "…opening 1,500 new shelter beds in his first six months of office…"
> Speaker: Daniel Lurie · promised 2024-11-05 · no due date in DB.

Both sides passed every check (5/5), all from one Frisc retrospective:

- **Kept (2× tier-3 count):** "The administration also says it stood up 500
  new beds." / "…helping nearly 2,000 people enter shelter through the
  reorganized street teams." Real numbers, real progress.
- **Broken (3× tier-2 news):** "The administration abandoned the goal
  altogether in July." / "…1,500 new shelter beds in his first six months of
  office, didn't last long." / "Kunal Modi said the plan to add 1,500 beds
  'was no longer the right approach.'"
- **Rubric:** numeric target + broken ≥ tier 2 → Rule 3 → **broken**.
  Re-run agrees. This is the load-bearing detail: the kept side *out-tiers*
  the broken side (3 > 2), and without the numeric-target flag the case
  falls through Rules 4–6 to undecided. The flag encodes the design
  judgment that number + deadline must *both* hold.

**My verdict: broken.** 500 beds stood up is genuine partial completion, not
fulfillment, and the promisor's own health chief declared the plan
abandoned. This is the pipeline's partial-progress trap working as
designed — the hardest ground truth in the P01–P12 set.

### P11 — "We'll never tour again": the wording case the code can't see

> "We never said we'll never play again, but we'll never tour again."
> Speaker: Mickey Hart / Dead & Company · promised 2022-09-23.

- **Kept (3× tier-2 news, all pass):** the 2023 "Final Tour" happened and
  "concluded on July 16 at Oracle Park in San Francisco." True — and
  structurally the wrong thing to prove: the promise is a *negative*
  ("never tour again"), so showing the farewell tour happened is necessary
  but nowhere near sufficient. One kept quote is just the promise restated.
- **Broken (4× tier-2 news, all pass):** 30-show Sphere leg May–Aug 2024,
  18-show Sphere leg from March 2025, sold-out three-day Golden Gate Park
  run ending Aug 3 2025 ("Tens of thousands of Deadheads once again packed
  the Polo Field").
- **Rubric re-run: broken under every flag combination** — because Rule 5
  (broken ≥ 2, kept < 3) fires *before* Rule 7 (ambiguity). The code can
  never call this case undecided; the DB's first verdict (undecided, with
  `reading_used`: "tour = multi-city concert tour only") was a human
  judgment overriding the rubric, and the re-open (broken, reading:
  "sustained multi-show runs count as touring") brought it back in line
  with what the code said all along.

**My verdict: broken.** 48 Sphere shows plus a three-night sold-out park run
is touring in everything but routing; the multi-city-only reading is too
cute to survive contact with the evidence. But the meta-finding stands:
Rule 7 is unreachable whenever tiers already settle the case, so every
genuine wording dispute is currently decided by a person, then recorded as
if the rubric decided it. If ambiguity should ever win over tiers, Rule 7
has to move up.

### P64 — Treasure Island's 8,000 homes: both sides agree, verdict still hard

> "…the Project is anticipated to include (1) up to 8,000 new residential
> units" · Speaker: Treasure Island Development Authority ·
> promised 2011-06-07 · no deadline (open-ended buildout).

- **Kept (vote tier 4 + count tier 3, both pass):** the Board adopted the
  TI/YBI deal 11–0 in 2011; "nearly 1,000 homes are open or near
  completion" (Sept 2024).
- **Broken (2× tier-3 count, both pass):** "Currently in the first stage of
  redevelopment, there are nearly 1,000 homes now open or near completion"
  after 13 years; the 2025 target is only ~1,208 units, ~15% of the
  promise. Same numbers, opposite framing — there is no factual dispute.
- **Rubric re-run: undecided, with and without the interim-progress flag.**
  Rule 6b's guards (kept < 3, broken < 2) assume "no contradiction," but
  here the tier-3/4 claims *are* the disagreement — over framing, not
  facts. The DB's first verdict (undecided) matches the code exactly; the
  re-open to **in_progress** applied the documented P18 principle (an
  enabling vote proves the plan exists, not the outcome) plus the judgment
  that agreed ~1,000/8,000-open with no deadline is genuine partial
  completion.

**My verdict: in_progress.** ~12% delivered over 13 years with construction
ongoing and no deadline is the literal meaning of the category. The lesson:
the rubric tiers evidence *strength*, not whether the two sides dispute the
facts — agreed-fact cases will keep landing in Rule 8 until framing-vs-fact
is something the code can represent.

## 4. Limitations the examples expose

Yes — P83's blind spot is substantially about how sources are collected:

1. **No durability concept (P83).** Opening promises carry no stay-open
   clause, there is no "kept then lapsed" verdict, and no recheck ran (the
   schema has a `recheck` step; P83 has zero `events` rows). Collection is
   one-shot per advocate bundle: once the verdict is written, later history
   never re-enters unless a person re-opens the case.
2. **Allowlist vs. primary parties (P83).** Retailer/developer domains
   (`trinitysf.com`) are unlisted, so the opening-day primary source was
   dropped and the verdict rests on a news retrospective. The allowlist
   protects against junk sources at the cost of sometimes excluding the
   best source.
3. **Negative promises (P11).** "Never do X again" forces the kept side to
   prove an absence; its affirmative evidence (the farewell tour happened)
   scores tiers without settling anything. The rubric has no absence-of-X
   handling.
4. **Framing disputes (P64).** Tiers measure source strength, not
   factual disagreement. When both sides cite the same agreed numbers,
   high tiers on both sides read as "competing claims" and the case punts
   to Rule 8.
5. **Ambiguity can't win (P11).** Rule 7 sits below Rules 3–5, so wording
   only matters when tiers deadlock or go quiet. Every live wording dispute
   is decided by a human `reading_used`, then stored as a rubric verdict.
6. **Re-opens are principles, not code (P11, P64).** Corrections are
   append-only new rows (good — matches the "corrections, not edits" rule),
   but the reasoning that flips them (P18 outcome-satisfaction, interim
   progress on agreed facts) lives in verdict text and runbook notes, not
   in `decide_verdict`. The rubric and the principles are drifting apart;
   each re-open is a hint about the next rubric revision.

None of these corrupted a verdict in the sample: the re-runs match the
stored verdicts everywhere the code governs (P83, P05, P11-final,
P64-first), and diverge exactly where documented human judgment took over
(P11-first, P64-final). The audit trail (`verifications` rows for every
check, staging bundles for dropped claims) made each case reconstructable
without guessing.

## 5. Status snapshot (Nov 11, 2026 export)

- 62 published promises: 26 kept · 21 broken · 11 in_progress · 4 undecided;
  1 quarantined row (P68, `relevance_low`); the 12 planted N01–N12 cases
  were caught by checks/harness, not written as quarantine rows.
- 85 verdict rows (re-opens included), 124 evidence rows, 20 tables.
- Lane F harness run `F-20261111-045601`: 33 pass / 0 fail / 3
  blocked-extended. `tests/test_checks.py`: 28 passed (observed this
  session).
- 12 promises carry evidence from *both* advocates: P05, P06, P11, P13–P16,
  P24, P26, P62, P64, P81. The rest were decided one-sidedly (usually
  kept-with-no-contradiction or broken-on-empty-kept).
