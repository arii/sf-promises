# Lane C — Extractor

## Mission
Turn saved source files into 12 `promises_pending` rows (P01–P12) via model
extraction. You are a coding agent: you build the extraction code, you never
run a verdict.

## Already done (do not redo)
- Model call works: Nebius Token Factory, `meta-models/muse-spark-open`,
  returned strict JSON with a verbatim quote on a live sample.

## Owns / touches
- Writes: extraction code, `promises_pending` rows only (through the
  arbitrator path, never directly to `promises`).
- Must not: call the network (read saved files only), write the DB during
  extraction, decide verdicts.

## Rules
- Batch 5 promises per model call, all from the same source file. Strict JSON
  array; each object: `promise_id, promise_text, entity_id, promised_date,
  due_date, page_number` (fields per tech design §5/§11).
- `promise_text` MUST be a substring of the saved source text. If not, flag
  `quote none` and stop that row (it goes to `quarantined`, never `promises`).
- No DB write inside the extraction step; rows land in `promises_pending`.

## Validation (check runbook boxes only when this passes)
Fields present, quotes verbatim, DB unchanged during extraction, then
12 pending rows for P01–P12.

## Cut rule
Model call fails → use the predefined promise text from the validation set.
Fewer than 5 candidates from 10 files → cut to Board minutes PDFs, cut the
prompt to speaker + promise text + date, re-run on the seed set.
