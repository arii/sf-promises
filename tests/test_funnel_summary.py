"""D3: funnel counts and quarantine reason-code sums reconcile with the tables.

Seeds the pipeline schema (src/schema.sql) with a small fixture database and
asserts that the summaries the demo panels render equal direct SQL counts over
the same tables — the panels may only ever show what the tables contain.
"""

import json
import sqlite3
import unittest

from src.funnel import (
    build_funnel_summary,
    funnel_counts_from_db,
    reason_codes_for_item,
    summarize_quarantine_reasons,
    summarize_reason_codes_from_db,
)


def seed_db() -> sqlite3.Connection:
    from pathlib import Path

    schema_path = Path(__file__).resolve().parent.parent / "src" / "schema.sql"
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(schema_path.read_text(encoding="utf-8"))

    # Four candidates: two published, two quarantined.
    for pid in ("C1", "C2", "C3", "C4"):
        conn.execute(
            "INSERT INTO candidates (promise_id, canonical_slug) VALUES (?, ?)",
            (pid, f"slug-{pid}"),
        )
    for pid in ("C1", "C2"):
        conn.execute(
            "INSERT INTO promises (promise_id, entity_name, entity_type, sector, "
            "neighborhood, promise_text, date_promised, date_deadline, created_at) "
            "VALUES (?, 'Entity', 'politicians', 'civic', 'SF', 'text', "
            "'2025-01-01', '2025-12-31', '2025-01-01T00:00:00+00:00')",
            (pid,),
        )
    # Three archived source documents.
    for n, pid in enumerate(("C1", "C1", "C2")):
        conn.execute(
            "INSERT INTO evidence_ledger (promise_id, phase, source_tier, url, "
            "local_source_path, content_sha256, verbatim_quote, quote_verified, "
            "verification_record_json, ingested_at) "
            "VALUES (?, 'ORIGIN', 'TIER1_GOV', ?, ?, ?, 'q', 1, '{}', "
            "'2025-01-01T00:00:00+00:00')",
            (pid, f"https://www.sf.gov/{n}", f"path{n:02d}.md", f"hash{n:02d}"),
        )
    # Three distinct records entered the verification lane.
    for pid in ("C1", "C1", "C2", "C3"):
        conn.execute(
            "INSERT INTO verifications (promise_id, check_type, passed, reason, "
            "checked_at) VALUES (?, 'accuracy_quote', 1, 'ok', "
            "'2025-01-01T00:00:00+00:00')",
            (pid,),
        )
    # Two quarantined rows carrying three reason codes.
    conn.execute(
        "INSERT INTO quarantined (promise_id, stage, reason_codes_json, "
        "candidate_payload_json, created_at) VALUES (?, 'screening', ?, '{}', "
        "'2025-01-01T00:00:00+00:00')",
        ("C3", json.dumps(["NO_VERIFIABLE_ORIGIN"])),
    )
    conn.execute(
        "INSERT INTO quarantined (promise_id, stage, reason_codes_json, "
        "candidate_payload_json, created_at) VALUES (?, 'gate', ?, '{}', "
        "'2025-01-01T00:00:01+00:00')",
        ("C4", json.dumps(["NO_VERIFIABLE_DEADLINE", "LOW_RELEVANCE"])),
    )
    conn.commit()
    return conn


class TestFunnelCountsFromDb(unittest.TestCase):
    def setUp(self):
        self.conn = seed_db()

    def tearDown(self):
        self.conn.close()

    def test_stage_counts_equal_direct_sql_counts(self):
        counts = funnel_counts_from_db(self.conn)
        self.assertEqual(counts, {
            "sources_archived": self.conn.execute("SELECT COUNT(*) FROM evidence_ledger").fetchone()[0],
            "screened": self.conn.execute(
                "SELECT COUNT(DISTINCT promise_id) FROM verifications").fetchone()[0],
            "published": self.conn.execute("SELECT COUNT(*) FROM promises").fetchone()[0],
            "quarantined": self.conn.execute("SELECT COUNT(*) FROM quarantined").fetchone()[0],
        })
        self.assertEqual(counts, {
            "sources_archived": 3, "screened": 3, "published": 2, "quarantined": 2,
        })

    def test_quarantined_stage_equals_reason_summary_total(self):
        counts = funnel_counts_from_db(self.conn)
        reasons = summarize_reason_codes_from_db(self.conn)
        self.assertEqual(reasons["total_quarantined"], counts["quarantined"])

    def test_funnel_summary_with_register_universe(self):
        summary = build_funnel_summary(
            leads_encountered=10,
            sources_archived=3,
            qualified=6,
            screened=3,
            published=2,
            quarantined=2,
        )
        by_stage = {s["stage"]: s for s in summary["stages"]}
        # intake-register universe converts internally
        self.assertEqual(by_stage["qualified"]["conversion_from_previous"], 0.6)
        # database universe converts internally; outcomes convert from screened
        self.assertEqual(by_stage["screened"]["conversion_from_previous"], 1.0)
        self.assertEqual(by_stage["published"]["conversion_from_previous"], 0.667)
        self.assertEqual(by_stage["quarantined"]["conversion_from_previous"], 0.667)
        self.assertEqual(
            summary["stage_counts"],
            {"leads_encountered": 10, "sources_archived": 3, "qualified": 6,
             "screened": 3, "published": 2, "quarantined": 2},
        )

    def test_missing_stages_are_omitted_not_zeroed(self):
        summary = build_funnel_summary(published=54, quarantined=1)
        self.assertEqual(
            [s["stage"] for s in summary["stages"]], ["published", "quarantined"]
        )
        # no screened base -> no conversion rates
        self.assertNotIn("conversion_from_previous", summary["stages"][0])

    def test_outcome_conversion_uses_screened_not_published(self):
        summary = build_funnel_summary(screened=55, published=54, quarantined=1)
        by_stage = {s["stage"]: s for s in summary["stages"]}
        self.assertEqual(by_stage["published"]["conversion_from_previous"], 0.982)
        self.assertEqual(by_stage["quarantined"]["conversion_from_previous"], 0.018)

    def test_negative_counts_are_rejected(self):
        with self.assertRaises(ValueError):
            build_funnel_summary(published=-1)


class TestQuarantineReasonSums(unittest.TestCase):
    def setUp(self):
        self.conn = seed_db()

    def tearDown(self):
        self.conn.close()

    def test_reason_codes_reconcile_with_the_table(self):
        reasons = summarize_reason_codes_from_db(self.conn)
        self.assertEqual(reasons["total_quarantined"], 2)
        self.assertEqual(reasons["total_reason_codes"], 3)
        self.assertEqual(reasons["by_reason"], {
            "LOW_RELEVANCE": 1,
            "NO_VERIFIABLE_DEADLINE": 1,
            "NO_VERIFIABLE_ORIGIN": 1,
        })
        rows = self.conn.execute("SELECT COUNT(*) FROM quarantined").fetchone()[0]
        self.assertEqual(reasons["total_quarantined"], rows)

    def test_malformed_reason_json_counts_as_unknown(self):
        # quarantined rows are unique per (quarantine_id, promise_id), and C4
        # already carries one row, so a second row for C4 is legal.
        self.conn.execute(
            "INSERT INTO quarantined (promise_id, stage, reason_codes_json, "
            "candidate_payload_json, created_at) VALUES (?, 'x', 'not-json', '{}', "
            "'2025-01-02T00:00:00+00:00')",
            ("C4",),
        )
        reasons = summarize_reason_codes_from_db(self.conn)
        self.assertEqual(reasons["total_quarantined"], 3)
        self.assertEqual(reasons["by_reason"].get("unknown"), 1)
        self.assertEqual(
            reasons["total_reason_codes"], sum(reasons["by_reason"].values())
        )

    def test_registry_items_without_codes_are_counted_as_unknown(self):
        items = [{"promise_id": "X1"}, {"promise_id": "X2", "failing_check_code": "accuracy_quote"}]
        summary = summarize_quarantine_reasons(items)
        self.assertEqual(summary["total_quarantined"], 2)
        self.assertEqual(summary["by_reason"], {"accuracy_quote": 1, "unknown": 1})

    def test_non_mapping_items_are_skipped(self):
        summary = summarize_quarantine_reasons([{"failing_check_code": "verdict_rubric"}, "junk", None])
        self.assertEqual(summary["total_quarantined"], 1)

    def test_reason_codes_field_wins_over_fallbacks(self):
        item = {"promise_id": "X", "failing_check_code": "accuracy_quote",
                "reason_codes": ["NO_VERIFIABLE_ORIGIN", "LOW_RELEVANCE"]}
        self.assertEqual(reason_codes_for_item(item), ["NO_VERIFIABLE_ORIGIN", "LOW_RELEVANCE"])


if __name__ == "__main__":
    unittest.main()
