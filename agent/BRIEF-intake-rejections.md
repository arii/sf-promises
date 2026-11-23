# Brief: the v2 candidate audit rejects almost everything

Status: open research. Written 2026-11-23. Tracking issue: see `gh issue list`
("v2 audit rejects nearly every candidate").

## Problem

The site has published 54 promises since the Nov 10 hackathon. Those records
came through the legacy pipeline. The v2 candidate audit (`src/candidate.py`,
run through `python -m src.run_live --candidate-batch`) is the only path that
adds new records. On its first real run (2026-11-23) it published **0 of 12**
candidates:

| Reason | Count | Candidates |
| --- | --- | --- |
| `NO_VERIFIABLE_ORIGIN` | 9 | SEISMIC-02, CLIMATE-01, CLIMATE-02, LEADER-01, LEADER-02, LEADER-03, RETAIL-01, BIKE-01, BIKE-02 |
| `INSUFFICIENT_OUTCOME_EVIDENCE` | 2 | ARTS-01, DISC-20261122-013 |
| `AMBIGUOUS_EVIDENCE` | 1 | SEISMIC-01 |

Every candidate had saved sources: 6 to 10 archived files each, in
`/mnt/archil/workspace/v2/sources/<id>/`. The failures happened after retrieval,
in extraction and verification.

We want the audit to publish real, well-sourced promises at a useful rate
**without** publishing unsupported claims. The 0% false-accept rate on 50
adversarial mutations and the gold-set agreement must not get worse.

## Where the rejections come from (`src/candidate.py`, `audit_candidate`)

1. **Origin.** For each archived origin source, the model is asked to pick the
   sentence that states the discovery target (`record_promise_evidence`,
   prompt in `src/extract.py`). It must also return an explicit
   `promised_date` and a `deadline`.
   - No sentence returned leads to `NO_VERIFIABLE_ORIGIN`.
   - A missing promise date leads to `INVALID_PROMISE_DATE_LATER_THAN_SOURCE`
     (also used for "date not stated").
   - A missing deadline, or a horizon that is too short
     (`screen_pending_origin`), leads to `NO_VERIFIABLE_DEADLINE`.
2. **Origin review.** An independent `verify_origin` call must answer true for
   action, promise_date and deadline, with "false for any ambiguity". A
   failure leads to `AMBIGUOUS_EVIDENCE`, `NO_VERIFIABLE_DEADLINE` or the
   promise-date reason.
3. **Outcome.** The kept and broken advocates (`assess_outcome`) must agree
   on delivery and survival status (otherwise `ADVOCATE_DISAGREEMENT`).
   **Both** a delivery segment and a survival segment must be selected
   (otherwise `INSUFFICIENT_OUTCOME_EVIDENCE`, lines ~247 and ~281).
4. **Semantic review.** `verify_evidence` must answer true for all six of
   action, promise date, deadline, delivery, survival, and entity and
   location. Then taxonomy (`INVALID_TAXONOMY`) and relevance (`RELEVANCE_LOW`).

Any one failure quarantines the candidate. There is no partial or
"in progress" outcome.

## What we observed (from the lane worker reports)

- **Paraphrased targets.** The 15 "outside the box" register entries
  (`SEISMIC-*`, `CLIMATE-*`, `LEADER-*`, `RETAIL-*`, `BIKE-*`, `ARTS-*`,
  `TECH-*`) have `statement_preview` text that we wrote, not a quote. Example:
  LEADER-01's target was "$100M in annual $10M+ grants". The source described
  a one-time $7M donation, so no sentence matched.
- **Missing commitment dates.** Matching sentences were often found, but the
  origin had no explicit date the rules accept. Examples: news pages saying
  "on Tuesday" or "next year" (CLIMATE-01, RETAIL-01, BIKE-01, BIKE-02), and
  an ordinance whose only date is an "AMENDED IN BOARD 11/10/2020" header.
  The rule "never infer the promise date from the publication date" rejects
  these even when the page is dated.
- **Future deadlines can never pass.** A promise whose deadline is after
  today has no delivery evidence yet, so step 3 always fails. ARTS-01 and
  DISC-20261122-013 had a verified origin and failed only here. 24 of the 45
  queued candidates have future deadlines.
- **Segmenting problems.** Some sentences are split across segments (an
  ordinance sentence split at [286]/[287], strikethrough text merged into
  "JanuaryJune 1, 2021"). Outcome segments can be bare fragments ("4,648 (
  94%)", or a heading such as "Soft Story Program"), which a skeptical
  `verify_evidence` reader then rejects (SEISMIC-01).
- **Deadline normalization.** "Seven years" from 2013 gives 2020-12-31 under
  the rules, while the register said 2021-09-15. "Early 2027" has no rule. The
  worker used December 31, which the origin reviewer accepted.
- **Search noise.** Before the keyword fix, discovery pulled pages from other
  cities (DC, Jersey Village, TX) for short quotes. This is fixed by
  URL-slug keywords, but retrieval quality is still unmeasured.

## Result of experiment 1: recall baseline (2026-11-23)

**H1 is confirmed.** The v2 audit rejected **all 48** runnable canonical leads,
which are promises the site already publishes. It ran in 4 shards under
`/mnt/archil/workspace/v2-baseline/shard-{0..3}/`. The other 14 of the 62 leads
(P13–P41 etc.) have no day-precision `promised_date`, so discovery cannot run
them at all.

| Final reason | Count |
| --- | --- |
| `INVALID_PROMISE_DATE_LATER_THAN_SOURCE` | 26 |
| `NO_VERIFIABLE_ORIGIN` | 9 |
| `NO_VERIFIABLE_DEADLINE` | 6 |
| `INVALID_SOURCE_PUBLICATION_DATE` | 5 |
| `INSUFFICIENT_OUTCOME_EVIDENCE` | 1 |
| `INVALID_ORIGIN_EVIDENCE` | 1 |

According to the lane workers' per-promise notes, the dominant cause is the
promise date. The matching sentence was found, but the source states the
date only relatively ("on Tuesday", "today", "last year") or not at all. The
rules forbid using the source's publication date, so every retry returns
null. Many `NO_VERIFIABLE_ORIGIN` and `INVALID_SOURCE_PUBLICATION_DATE`
results end the same way after the retry.

Secondary causes:
- Commitments with no deadline (S1, S2, P81) fail `NO_VERIFIABLE_DEADLINE`.
- Future deadlines fail at outcome (P40).
- Off-topic origin sources are retrieved (KQED, civil-rights slide decks).
- Fragment segments.
- Some leads restate past events rather than commitments (P04, P29).

**Fix order:** H4 first (date resolution), then H3 (in progress for future
deadlines), then target quality for leads.

## Result of experiment 4a: date resolution on (2026-11-23)

The same 48 leads were rerun with `SF_PROMISES_DATE_RESOLUTION=1` in
`/mnt/archil/workspace/v2-baseline-dates/shard-{0..3}/`. Still **0 published**,
but the date failures fell from 26 to 3. The candidates now pass origin
and fail at the next gates:

| Final reason | Flag off | Flag on |
| --- | --- | --- |
| `INVALID_PROMISE_DATE_LATER_THAN_SOURCE` | 26 | 3 |
| `NO_VERIFIABLE_DEADLINE` | 6 | **24** |
| `INSUFFICIENT_OUTCOME_EVIDENCE` | 1 | **10** |
| `NO_VERIFIABLE_ORIGIN` | 9 | 5 |
| `INVALID_SOURCE_PUBLICATION_DATE` | 5 | 5 |
| `INVALID_ORIGIN_EVIDENCE` | 1 | 1 |

Next blockers:
1. **Deadline.** Many published records are commitments with no stated
   deadline, or a dated one-off event (an opening day, a sell-out, a pledge,
   "starting today"). v2 requires a deadline before it looks at outcomes.
2. **Outcome evidence.** Outcome sources are often unrelated (another city,
   another program). Both a delivery and a survival sentence are required.
   This is a retrieval problem as much as a rule problem. The Keenable
   features in the next section apply here.

## Hypotheses to test

- **H1. The audit is stricter than the standard that produced the published
  54.** If we run the v2 audit on the 62 existing leads in
  `seeds/canonical_targets.json` (the published promises), most will also be
  rejected. If so, the problem is the gates, not the candidates.
- **H2. Most `NO_VERIFIABLE_ORIGIN` results come from paraphrased targets.**
  Candidates whose `promise_text` is a verified verbatim quote (the
  `DISC-20261122-*` set from the discovery rounds) pass origin far more often.
- **H3. Requiring delivery and survival evidence blocks every future-deadline
  promise.** An `in_progress` path (verified origin, deadline in the future,
  no contrary evidence) would publish most of them safely.
- **H4. A dated source page is enough for the promise date** when the
  commitment sentence is in the page's own body, such as a press release or
  news article with a dateline or a `published_at`. The current rule
  rejects this.

  **Date resolution (flag).** Implemented in `src/date_resolution.py`, off by
  default; set `SF_PROMISES_DATE_RESOLUTION=1` to enable. When the model
  returns a null `promised_date` and the source has a valid publication date,
  the date is filled in this order: **stated** (an explicit full date in the
  quote sentence, the two sentences before it, or a dateline in the first five
  sentences), then **relative** ("today", "yesterday", "on Tuesday", "last
  Tuesday", resolved against the publication date), then **publication** (the
  publication date itself, an upper bound). A date is never later than the
  publication date. Vague phrases such as "last year" or "recently" are not
  resolved to a day. Derived dates are labelled to the verifiers and in the
  export (`promise_date_basis`). The quote must still be verbatim and both
  verifiers must still accept the date. The basis is stored as a
  `promise_date_basis` row in `verifications`. Not yet measured: rerun
  experiment 1 with the flag on.
- **H5. Better segmenting** (keep whole sentences; drop headings and
  fragments as outcome candidates) removes most `AMBIGUOUS_EVIDENCE` and
  `INSUFFICIENT_OUTCOME_EVIDENCE` results that are caused by fragments.

## Experiments (in order)

1. **Recall baseline (H1).** Run `--candidate-batch` on the canonical
   queue against a fresh v2 database, for example
   `/mnt/archil/workspace/v2-baseline/promises.db`, and record the reason for
   each rejection. Compare with the published verdicts in `docs/data.json`.
   This gives the **false-reject rate on known-good promises**, which nothing
   measures today. The cost is Keenable calls (billed) plus agent-lane
   answers, about 5 to 20 per seed.
2. **Rejection-reason ledger.** Make the quarantine row record which gate
   failed, the origin source, and the worker's explanation, not just the last
   reason code. Today `reason_codes_json` keeps one code and the detail is lost.
3. **Target quality (H2).** Re-run the `DISC-20261122-*` candidates, which
   have verbatim quotes, and compare pass rates with the paraphrased set.
   For paraphrased entries, try passing the verbatim quote found in the
   source as the target, or drop them from the queue.
4. **Rule changes behind flags, scored on three measures.** Run each change
   on (a) the canonical recall set, (b) the gold set
   `data/gold_set.json` with `data/gold_gate_expectations.json`, and (c) the
   adversarial mutations. Record recall, gold agreement and false-accept
   rate. Candidate changes:
   - an `in_progress` verdict for verified origins with future deadlines (H3);
   - the publication date as the promise date for first-party dated pages (H4);
   - deadline normalization for "early/mid/late YEAR" and "N years from"
     (document the rule);
   - sentence-preserving segmentation, with fragments excluded as outcome
     selections (H5);
   - letting the outcome stage accept delivery **or** survival when the other
     is not yet applicable.
5. **Decide.** Adopt only the changes that raise recall without raising
   false accepts or lowering gold agreement. Record the decision in `PRD.md`.

## Success criteria

- A measured false-reject rate on the canonical set, before and after.
- At least half of the 45 queued candidates end in a published verdict
  (kept, broken, in progress or undecided) or in a quarantine with a specific,
  correct reason.
- False-accept rate stays 0.0% on the 50 adversarial mutations, and gold-set
  agreement does not drop.
- Every rule change is documented in `PRD.md` and covered by a test.

## Constraints

- Only the Verdict lane writes `promises`, `verdicts`, `verifications` and
  `quarantined`. Use one writer per database, and take Archil delegations
  before writing (README, "Workspace setup").
- Do not touch the legacy `/mnt/archil/workspace/promises.db` or the
  published `docs/data.json` during experiments. Use separate v2 databases.
- A snippet is never a source. Quotes must still match saved bytes exactly.

## Useful pointers

- Gates: `src/candidate.py` (`audit_candidate`), `src/extract.py` (extraction
  prompt and segmenting), `src/screening.py` (`screen_pending_origin`),
  `src/lifecycle_rubric.py` (`decide_verdict`), `src/relevance.py`.
- Queue: `seeds/discovery_targets.json` (built by
  `scripts/build_discovery_queue.py`) and `seeds/canonical_targets.json`.
- Run log: `WORKING_NOTES.md`, 2026-11-23, "First v2 audit of qualified
  discovery candidates".
- The v2 database from the first run: `/mnt/archil/workspace/v2/promises.db`
  (12 candidates, 14 quarantine rows, 4 `promises_pending`).
