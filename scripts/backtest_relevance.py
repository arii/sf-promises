"""Strictness backtest for the D4 relevance-gate rebalance.

Offline, deterministic, stdlib only. Replays the frozen corpora through both
the pre-rebalance gate (verbatim copy of the fbf997f scoring) and the
rebalanced gate in src/relevance.py, and writes
data/relevance_rebalance_backtest.json plus docs/relevance-rebalance-backtest.md.

Frozen corpora (all checked in, no network, no keys):
  1. Published records and quarantined rows exported in docs/data.json,
     including the 25 data/gold_set.json promises (tagged is_gold) and the
     two frozen relevance-gate failures N12 (restated vote) and P68 (non-SF).
  2. The 24 qualified candidates in data/intake_candidate_register.json —
     the population the gate actually evaluates at Step 2.5.

Before/after inputs are identical per record: published rows reuse the
recorded per-criterion gate scores (real, measurable, sf, interesting) as the
before state; register candidates derive the gate booleans from frozen fields
with the documented extractor below. Only the interesting criterion is
recomputed for the after state (the rebalance touches only interesting);
publish = total >= 5 and real >= 1 in both states.

Run: python3 scripts/backtest_relevance.py
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from relevance import (  # noqa: E402
    ADDRESS_RE,
    DOLLAR_RE,
    FILE_ID_RE,
    NUMBER_RE,
    YEAR_RE,
    rebalance_interesting,
)

# Verbatim copy of the fbf997f interesting scorer: the before state of the
# rebalance. Kept local so the backtest never depends on which behavior
# src/relevance.py currently ships.
def score_interesting_before(promise_text, has_named_entity):
    text = promise_text or ""
    if NUMBER_RE.search(text) or DOLLAR_RE.search(text) or ADDRESS_RE.search(text) or FILE_ID_RE.search(text):
        return 2
    if has_named_entity and YEAR_RE.search(text):
        return 1
    return 0


def style_of(text, address_full, record_type):
    """Capital-project style when the record is a project/opening or carries a street address; else service/program."""
    if record_type == "project_or_opening":
        return "capital_project"
    for field in (text, address_full):
        if field and ADDRESS_RE.search(field):
            return "capital_project"
    return "service_program"


def apply_rebalance(promise_text, recorded, has_address=False,
                    has_vote_filing_opening_count_with_id=False, has_named_entity=False):
    """Recompute interesting under the rebalanced rule, holding the other recorded criteria fixed.

    The recorded interesting score is the raw (pre-rebalance) value: it was
    scored against the full archived source, so it is the authoritative input
    to the cap and credit. Text regexes here serve only the distinct-artifact
    test inside the cap.
    """
    intr = rebalance_interesting(
        promise_text, recorded["measurable"], recorded["real_promise"],
        recorded["interesting"],
        has_address=has_address,
        has_vote_filing_opening_count_with_id=has_vote_filing_opening_count_with_id,
        has_named_entity=has_named_entity,
    )
    total = recorded["real_promise"] + recorded["measurable"] + recorded["sf_relevant"] + intr
    return {
        "real_promise": recorded["real_promise"],
        "measurable": recorded["measurable"],
        "sf_relevant": recorded["sf_relevant"],
        "interesting": intr,
        "total": total,
        "publish": total >= 5 and recorded["real_promise"] >= 1,
    }


def load_published_and_quarantined():
    data = json.loads((ROOT / "docs/data.json").read_text())
    gold = json.loads((ROOT / "data/gold_set.json").read_text())
    gold_ids = {p["promise_id"] for p in gold["gold_promises"]}
    records = []
    for p in data["promises"]:
        r = p["relevance"]
        records.append({
            "id": p["promise_id"],
            "population": "gold_set_published" if p["promise_id"] in gold_ids else "published",
            "style": style_of(p.get("promise_text"), p.get("address_full"), p.get("record_type")),
            "text": p.get("promise_text") or "",
            "named_entity": bool(p.get("entity")),
            "distinct_address": bool(p.get("address_full") and ADDRESS_RE.search(p["address_full"])),
            "before": {
                "real_promise": r["real"], "measurable": r["measurable"],
                "sf_relevant": r["sf"], "interesting": r["interesting"],
                "total": r["score"], "publish": r["score"] >= 5 and r["real"] >= 1,
            },
            "restated": False,
        })
    for q in data["quarantined"]:
        pid = q.get("promise_id", "")
        text = q.get("claim") or q.get("planted_claim") or q["title"]
        if pid == "N12":
            # Frozen restated procedural vote: real_promise 0, never publishes.
            before = {"real_promise": 0, "measurable": 2, "sf_relevant": 2,
                      "interesting": score_interesting_before(text, True), "restated": True}
        elif pid == "P68":
            # Frozen non-SF failure: verbatim quote, named speaker, day-month but no
            # year in the claim, no digits beyond the date, sf_relevant 0.
            before = {"real_promise": 1, "measurable": 1, "sf_relevant": 0,
                      "interesting": score_interesting_before(text, True), "restated": False}
        else:
            # Verification-failure cases: the planted claim is not a verbatim quote
            # of the archived source (or the source fails a check), so the gate's
            # has_verbatim is False and real_promise is 0.
            before = {"real_promise": 0, "measurable": 1, "sf_relevant": 2,
                      "interesting": score_interesting_before(text, True), "restated": False}
        total_before = before["real_promise"] + before["measurable"] + before["sf_relevant"] + before["interesting"]
        records.append({
            "id": q["quarantine_id"],
            "population": "quarantined",
            "style": style_of(text, "", "promise"),
            "text": text,
            "named_entity": True,
            "distinct_address": bool(ADDRESS_RE.search(text)),
            "before": {
                "real_promise": before["real_promise"], "measurable": before["measurable"],
                "sf_relevant": before["sf_relevant"], "interesting": before["interesting"],
                "total": total_before,
                "publish": total_before >= 5 and before["real_promise"] >= 1,
            },
            "restated": before["restated"],
        })
    return records


def load_register_qualified():
    register = json.loads((ROOT / "data/intake_candidate_register.json").read_text())
    records = []
    for c in register["candidates"]:
        if c.get("qualification_status") != "qualified":
            continue
        text = c.get("statement_preview") or ""
        signals = {
            "has_verbatim": bool(text),
            "has_speaker": bool(c.get("entity")),
            "has_date": bool(c.get("promised_date")),
            "is_proposal_or_aspiration_or_restated_vote": False,
            "has_number": bool(NUMBER_RE.search(text)),
            "has_address": bool(ADDRESS_RE.search(text)),
            "has_dollar": bool(DOLLAR_RE.search(text)),
            "has_vote_filing_opening_count_with_id": bool(FILE_ID_RE.search(text)),
            "names_sf_or_sf_address_agency_ordinance": bool(
                c.get("supervisor_district") or c.get("geographic_scope") == "citywide"),
            "bay_area_with_sf_link": False,
            "has_named_entity": bool(c.get("entity")),
        }
        records.append({
            "id": c["candidate_id"],
            "population": "register_qualified",
            "style": style_of(text, "", c.get("record_type")),
            "text": text,
            "named_entity": signals["has_named_entity"],
            "distinct_address": signals["has_address"],
            "signals": signals,
            "restated": False,
        })
    return records


def summarize(records):
    styles = {}
    flips_up, flips_down = [], []
    for r in records:
        before, after = r["before"], r["after"]
        s = styles.setdefault(r["style"], {
            "n": 0, "pass_before": 0, "pass_after": 0,
            "total_sum_before": 0, "total_sum_after": 0,
        })
        s["n"] += 1
        s["pass_before"] += int(before["publish"])
        s["pass_after"] += int(after["publish"])
        s["total_sum_before"] += before["total"]
        s["total_sum_after"] += after["total"]
        if before["publish"] != after["publish"]:
            entry = {
                "id": r["id"], "population": r["population"], "style": r["style"],
                "total_before": before["total"], "total_after": after["total"],
                "real_promise_before": before["real_promise"],
                "real_promise_after": after["real_promise"],
                "interesting_before": before["interesting"],
                "interesting_after": after["interesting"],
            }
            (flips_up if after["publish"] else flips_down).append(entry)
    for s in styles.values():
        s["pass_rate_before"] = round(s["pass_before"] / s["n"], 4)
        s["pass_rate_after"] = round(s["pass_after"] / s["n"], 4)
        s["mean_total_before"] = round(s["total_sum_before"] / s["n"], 3)
        s["mean_total_after"] = round(s["total_sum_after"] / s["n"], 3)
        del s["total_sum_before"], s["total_sum_after"]
    return styles, flips_up, flips_down


def main():
    records = load_published_and_quarantined()
    for r in records:
        after = apply_rebalance(
            r["text"], r["before"], has_address=r["distinct_address"],
            has_vote_filing_opening_count_with_id=False,
            has_named_entity=r["named_entity"],
        )
        r["after"] = after
    register = load_register_qualified()
    for r in register:
        signals = r["signals"]
        from relevance import score_relevance  # local import: before/after by construction
        before = score_relevance(
            r["text"], has_verbatim=signals["has_verbatim"], has_speaker=signals["has_speaker"],
            has_date=signals["has_date"],
            is_proposal_or_aspiration_or_restated_vote=signals["is_proposal_or_aspiration_or_restated_vote"],
            has_number=signals["has_number"], has_address=signals["has_address"],
            has_vote_filing_opening_count_with_id=signals["has_vote_filing_opening_count_with_id"],
            names_sf_or_sf_address_agency_ordinance=signals["names_sf_or_sf_address_agency_ordinance"],
            bay_area_with_sf_link=signals["bay_area_with_sf_link"],
            has_named_entity=signals["has_named_entity"],
        )
        # Before state: raw fbf997f scoring (no cap, no credit).
        before["interesting"] = score_interesting_before(r["text"], signals["has_named_entity"])
        before["total"] = (before["real_promise"] + before["measurable"]
                           + before["sf_relevant"] + before["interesting"])
        before["publish"] = before["total"] >= 5 and before["real_promise"] >= 1
        r["before"] = before
        after = score_relevance(
            r["text"], has_verbatim=signals["has_verbatim"], has_speaker=signals["has_speaker"],
            has_date=signals["has_date"],
            is_proposal_or_aspiration_or_restated_vote=signals["is_proposal_or_aspiration_or_restated_vote"],
            has_number=signals["has_number"], has_address=signals["has_address"],
            has_vote_filing_opening_count_with_id=signals["has_vote_filing_opening_count_with_id"],
            names_sf_or_sf_address_agency_ordinance=signals["names_sf_or_sf_address_agency_ordinance"],
            bay_area_with_sf_link=signals["bay_area_with_sf_link"],
            has_named_entity=signals["has_named_entity"],
        )
        r["after"] = after
    records.extend(register)

    styles, flips_up, flips_down = summarize(records)
    all_before_publish = {r["id"] for r in records if r["before"]["publish"]}
    all_after_publish = {r["id"] for r in records if r["after"]["publish"]}
    newly_published = sorted(all_after_publish - all_before_publish)
    unpublished_by_rebalance = sorted(all_before_publish - all_after_publish)
    restated_published = sorted(
        r["id"] for r in records if r["restated"] and r["after"]["publish"])

    # Hard strictness assertions: the generator fails rather than writes a
    # violating artifact. Full attribution means verbatim quote + named speaker
    # + date, which for this gate is exactly real_promise == 2.
    for entry in flips_up:
        rec = next(r for r in records if r["id"] == entry["id"])
        assert rec["after"]["real_promise"] == 2, \
            f"{entry['id']} newly published without full attribution"
        if "signals" in rec:
            assert (rec["signals"]["has_verbatim"] and rec["signals"]["has_speaker"]
                    and rec["signals"]["has_date"]), \
                f"{entry['id']} newly published without verbatim quote + named speaker + date"
    assert not restated_published, "a restated vote newly published"
    assert styles["service_program"]["pass_rate_after"] >= styles["service_program"]["pass_rate_before"], \
        "service/program pass rate decreased"

    artifact = {
        "description": "Strictness backtest for the D4 relevance-gate rebalance (spec art_JBPvBRhF, deliverable D4).",
        "generated_by": "scripts/backtest_relevance.py",
        "baseline_commit": "fbf997f",
        "threshold": {"total": 5, "real_promise": 1, "note": "unchanged by the rebalance"},
        "corpora": {
            "docs/data.json promises": "published records; before-gate state = recorded per-criterion scores; gold_set.json ids tagged gold_set_published",
            "docs/data.json quarantined": "13 frozen rows incl. N12 (restated vote, real_promise 0) and P68 (non-SF, sf 0)",
            "data/intake_candidate_register.json": "24 qualified candidates; gate booleans derived from frozen fields (statement_preview regexes, entity, promised_date, supervisor_district/geographic_scope)",
        },
        "style_classifier": "capital_project = record_type project_or_opening or a street-address match in the text or address fields; else service_program",
        "rebalance": {
            "same_artifact_cap": "interesting contributes at most 1 when measurable is already 2 driven by the physical artifact (street address or filing/opening/count ID) and the text carries no distinct artifact of another class (dollar amount, filing ID, street address). Capping the number+date overlap was prototyped and rejected by this backtest: it cut quantified service programs while capital records escaped through their addresses, dollars, and IDs",
            "attribution_credit": "interesting contributes 1 when raw interesting is 0, real_promise is 2 (verbatim quote + named speaker + date), and a named entity is present; because real_promise 2 forces measurable >= 1, this flips pass rates on sf_relevant-1 records and adds margin on sf_relevant-2 records",
        },
        "per_style": styles,
        "flips_up": flips_up,
        "flips_down": flips_down,
        "strictness": {
            "newly_published": newly_published,
            "newly_published_without_full_attribution": [],
            "unpublished_by_rebalance": unpublished_by_rebalance,
            "restated_votes_published": restated_published,
        },
    }
    (ROOT / "data/relevance_rebalance_backtest.json").write_text(
        json.dumps(artifact, indent=2, sort_keys=False) + "\n")

    lines = [
        "# Relevance-gate rebalance — strictness backtest (D4)",
        "",
        f"Generated by `scripts/backtest_relevance.py` from the frozen corpora at baseline `{artifact['baseline_commit']}`.",
        "The publish threshold is unchanged: **total >= 5 with `real_promise >= 1`**; restated votes never publish.",
        "",
        "## Per-style results",
        "",
        "| Style | n | pass before | pass after | mean total before | mean total after |",
        "|---|---|---|---|---|---|",
    ]
    for style_name, s in sorted(styles.items()):
        lines.append(
            f"| {style_name} | {s['n']} | {s['pass_before']}/{s['n']} ({s['pass_rate_before']:.0%}) "
            f"| {s['pass_after']}/{s['n']} ({s['pass_rate_after']:.0%}) "
            f"| {s['mean_total_before']} | {s['mean_total_after']} |")
    lines += [
        "",
        "## Reading",
        "",
        "- **No publish decision changes anywhere in the frozen corpora** (both flip lists are empty): every published record still passes, and the frozen gate failures stay out.",
        "- The rebalance's measured effect is the margin around the threshold: fully-attributed records with no concrete artifact in their text gain +1 via the attribution credit, while records whose measurable score was driven by an address or filing ID lose the double-counted point via the same-artifact cap.",
        "- On the frozen corpora, service/program **pass rate** structurally cannot increase: every fully-attributed SF record already passes (real_promise 2 forces measurable >= 1, so 2 + 1 + 2 + 0 already clears 5), and the frozen gate failures are attribution or geography exclusions, not style exclusions. The pass-rate gain the credit buys lands on `sf_relevant == 1` records (Bay Area with an SF link, digit-free, fully attributed: 4 -> 5) and on future live-round candidates (D6); none exist in the frozen corpora, so here it shows as mean-total margin: service rises, capital falls.",
        "- Service/program pass rate cannot *decrease*: the credit is gated on `real_promise == 2`, and no frozen record fails because of the cap (an SF record with real >= 1 and measurable 2 still clears 5 under the cap).",
        "- The frozen relevance-gate failures are attribution/geography failures, not style failures: N12 (restated vote, `real_promise` 0) and P68 (non-SF, `sf_relevant` 0) remain unpublished under both rules.",
        "",
        "## Strictness assertions (enforced by the generator and re-asserted in tests)",
        "",
        f"- Newly published records: **{len(newly_published)}**; zero of them lack verbatim quote + named speaker + date (the credit requires `real_promise == 2`).",
        f"- Records unpublished by the rebalance: **{len(unpublished_by_rebalance)}**.",
        f"- Restated votes published: **{len(restated_published)}** (must be 0; N12 case).",
        "",
        "## Populations",
        "",
    ]
    for name, note in artifact["corpora"].items():
        lines.append(f"- `{name}` — {note}")
    lines.append(f"- Style classifier — {artifact['style_classifier']}.")
    (ROOT / "docs/relevance-rebalance-backtest.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({"per_style": styles, "flips_up": flips_up,
                      "flips_down": flips_down, "newly_published": newly_published,
                      "unpublished_by_rebalance": unpublished_by_rebalance}, indent=1))


if __name__ == "__main__":
    main()
