"""Read-only verifier for the demo_overhaul.md punchlist.

Run: python3 tests/verify_demo.py
Prints PASS/FAIL per item and exits nonzero if any item fails. Never writes to the DB.
"""
import csv
import json
import os
import re
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEMO = os.path.join(ROOT, "demo")
DB = os.environ.get("PROMISES_DB", "/mnt/archil/workspace/promises.db")
results = []


def read(name):
    with open(os.path.join(DEMO, name), encoding="utf-8") as f:
        return f.read()


def check(name, ok, detail=""):
    results.append((name, ok, detail))


def main():
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True, timeout=30)
    q = lambda s, a=(): con.execute(s, a).fetchall()
    code = {n: read(n) for n in ("app.js", "index.html", "export_data.py", "styles.css")}
    data = json.load(open(os.path.join(DEMO, "data.json"), encoding="utf-8"))

    n_db = q("select count(*) from promises")[0][0]
    check("export matches DB promise count", len(data["promises"]) == n_db,
          f"export {len(data['promises'])} vs DB {n_db}")

    latest = dict(q("""select verdict, count(*) from verdicts v
        where decided_at=(select max(decided_at) from verdicts where promise_id=v.promise_id)
        group by verdict"""))
    exp = {}
    for p in data["promises"]:
        exp[p["verdict"]] = exp.get(p["verdict"], 0) + 1
    check("export verdict counts match latest-per-promise DB counts",
          {k: v for k, v in latest.items() if v} == exp, f"db {latest} vs export {exp}")

    check("no invented 2025-05-01 due date in demo code",
          "2025-05-01" not in code["app.js"] + code["export_data.py"])
    check("no hardcoded 'All of SF (N)' count in index.html",
          not re.search(r"All of SF \(\d+\)", code["index.html"]))
    check("no 'of 100 target' / '98 verified' copy",
          not re.search(r"of 100 target|98 verified", code["index.html"] + code["app.js"] + code["export_data.py"]))
    check("no unhedged MicroVM isolation claim",
          not re.search(r"MicroVM", code["index.html"] + code["app.js"]),
          "hedge as 'designed to run in isolated sandboxes' until isolation is tested")
    wrong = {"P61": "Transbay Transit Center", "P64": "Parkmerced", "P84": "5M Project",
             "P85": "Presidio Parkway", "P86": "Treasure Island Redevelopment"}
    still = [k for k, v in wrong.items() if re.search(rf'"{k}":\s*"{v}', code["export_data.py"])]
    check("known-wrong neighborhood labels removed (P61, P64, P84, P85, P86)", not still, ",".join(still))
    check("no '3 sandboxes' copy", "3 sandboxes" not in code["index.html"].lower())
    check("prefers-reduced-motion supported", "prefers-reduced-motion" in code["styles.css"])
    check("reference mockup files removed from demo/",
          not [f for f in os.listdir(DEMO) if f.startswith("reference_")])

    # Displayed form mirrors the client's cleanQuoteText: links collapse to
    # their text, bold/italic markers are stripped. Raw JSON keeps DB truth.
    def displayed(text):
        t = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text or "")
        t = re.sub(r"\*\*([^*]+)\*\*", r"\1", t)
        t = re.sub(r"\*([^*]+)\*", r"\1", t)
        t = re.sub(r"__([^_]+)__", r"\1", t)
        return t

    bad_md = [p["promise_id"] for p in data["promises"]
              if re.search(r"\]\(http|\*\*", displayed(p.get("promise_text", "")))]
    check("no raw markdown in displayed promise text", not bad_md, ",".join(bad_md))
    db_text = {r[0]: (r[1] or "") for r in
               q("select promise_id, promise_text from promises")}
    paraphrased = [p["promise_id"] for p in data["promises"]
                   if (p.get("promise_text") or "") != db_text.get(p["promise_id"], "")]
    check("exported text equals DB text (no paraphrase)", not paraphrased,
          ",".join(paraphrased))
    db_rel = {}
    for r in q("select promise_id, criterion, score from relevance_checks"):
        db_rel.setdefault(r[0], {})[r[1]] = r[2]
    _cmap = {"real_promise": "real", "measurable": "measurable",
             "sf_relevant": "sf", "interesting": "interesting"}
    rel_bad = [p["promise_id"] for p in data["promises"]
               if not p.get("relevance") or
               any(p["relevance"].get(v) != db_rel.get(p["promise_id"], {}).get(k)
                   for k, v in _cmap.items())]
    check("exported relevance equals recorded gate", not rel_bad, ",".join(rel_bad))

    missing = [p["promise_id"] for p in data["promises"]
               if not p.get("source_file_path") or not os.path.exists(p["source_file_path"])]
    check("every exported promise resolves to a saved source file", not missing, ",".join(missing))

    # P62 regression: inspect modal must render per-promise staging files and
    # check outcomes from data, never hardcoded P02 content.
    modal = code["index.html"]
    check("modal has no hardcoded staging filenames",
          "staging/kept_P02.json" not in modal and "staging/broken_P02.json" not in modal)
    check("modal has no hardcoded claim counts",
          not re.search(r"\d+ affirming claims, \d+ contradicting", modal))
    hooks = ("modal-kept-file", "modal-broken-file", "modal-checks-list")
    check("modal markup exposes file/check hooks",
          all(h in modal for h in hooks),
          ",".join(h for h in hooks if h not in modal))
    check("openInspectModal writes file/check hooks from data",
          all(h in code["app.js"] for h in hooks),
          ",".join(h for h in hooks if h not in code["app.js"]))

    # ux_feedback: reconciliation strip + fetch timestamp must be data-driven.
    static_nums = re.search(r"26 pending intake|12 quarantined|Target: up to 100",
                            code["index.html"] + code["export_data.py"])
    check("no hardcoded reconciliation numbers", not static_nums)
    check("no hardcoded fetch timestamp",
          "19:07:00" not in code["index.html"] + code["app.js"])
    dbs = data["database_status"]
    src_pids = {r[0] for r in q("select promise_id from sources")}
    no_fetch = [p["promise_id"] for p in data["promises"]
                if p["promise_id"] in src_pids and not p.get("fetched_at")]
    check("export carries recorded fetch time per promise", not no_fetch,
          ",".join(no_fetch))
    q_csv = {r[0] for r in
             q("select promise_id from quarantined where promise_id like 'P%'")}
    csv_ids = set()
    with open(os.path.join(ROOT, "Archil Hackathon Nov 10 - SF Promises Export",
                           "data", "promises-P13-P112.csv"),
              encoding="utf-8") as _f:
        for _r in csv.DictReader(_f):
            csv_ids.add(_r["promise_id"])
    pub_csv = len([p for p in data["promises"] if p["promise_id"] in csv_ids])
    recon_ok = (pub_csv + len(q_csv & csv_ids) + dbs.get("pending_intake_count", -1)
                == len(csv_ids))
    check("intake backlog reconciles with CSV universe", recon_ok,
          f"pub_csv {pub_csv} + q {len(q_csv & csv_ids)} + pending "
          f"{dbs.get('pending_intake_count')} vs csv {len(csv_ids)}")

    # WRITEUP.md: N01-N12 were caught by checks/harness, not written as
    # quarantine rows. Only real rows (P68) may claim the quarantined table.
    lying = [q.get("quarantine_id") for q in data["quarantined"]
             if (q.get("quarantine_id") or "").startswith("Q-N")
             and "quarantined table" in (q.get("destination") or "")]
    check("planted tests do not claim quarantined-table rows", not lying,
          ",".join(lying))
    copy = code["index.html"] + code["app.js"]
    check("no unhedged isolation-infra claim",
          not re.search(r"isolated (MicroVM|sandbox)", copy),
          "writeup: separated processes; Firecracker never verified")
    check("limitations section present with all six writeup items",
          all(s in code["index.html"] for s in
              ('id="limitations"', "No durability", "Allowlist trade-off",
               "Negative promises", "Framing disputes", "Ambiguity can",
               "Re-opens are principles")))
    check("sponsor division stated (infra-only + provenance labels)",
          "Infrastructure only" in code["index.html"]
          and "provenance labels" in code["index.html"])

    ids = {r[0] for r in q("select promise_id from promises")}
    check("P13/P14 deduped (only one published)", not {"P13", "P14"} <= ids)
    check("P41/P42/P65 consolidated or distinguished (not all three published)",
          not {"P41", "P42", "P65"} <= ids)
    check("P17/S1/S2 consolidated or distinguished (not all three published)",
          not {"P17", "S1", "S2"} <= ids)
    past = sorted({"P24", "P28", "P44", "P61"} & ids)
    check("past-event / fragment rows not published (P24, P28, P44, P61)", not past, ",".join(past))
    s_ids = sorted(i for i in ids if i.startswith("S"))
    check("S-prefixed ids renamed or explained", not s_ids, ",".join(s_ids))

    for name, ok, detail in results:
        print(("PASS " if ok else "FAIL ") + name + (f"  [{detail}]" if detail and not ok else ""))
    failed = sum(1 for _, ok, _ in results if not ok)
    print(f"\n{len(results) - failed}/{len(results)} checks pass")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
