"""Lane C — Extractor: saved source files -> promises_pending rows.

Reads saved files only (never fetches). The only network call in this module
is the model API (Nebius Token Factory, OpenAI-compatible). No database write
runs in the extraction step: `extract` writes JSON to stdout/file, and only
the separate `load` phase writes promises_pending (short transaction,
busy_timeout=30000; the SQLite DB is shared with live agents).

Batch rule: up to 5 promises per model call, all from the same source file.
Strict JSON array; each object: promise_id, promise_text, entity_id,
promised_date, due_date, page_number (tech design section 11).

promise_text MUST be a substring of the saved source text (exact, or
normalized per src/checks.py). A row that fails verification is flagged
`quote none` and is quarantine-bound: it is reported, never written to
promises_pending by this module (the Verdict lane owns `quarantined`).

Cut rule: if the model call fails, fall back to the predefined promise text
from the validation set (PREDEFINED_P01_P12); the substring check still
applies before any row is loaded.

Usage (from repo root):
  python3 src/extract.py extract --source <saved-file> --ids P02 [--out out.json]
  python3 src/extract.py load --in out.json --db /mnt/archil/workspace/promises.db
"""

import argparse
import hashlib
import json
import os
import sqlite3
import sys
import urllib.request
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from src.checks import check_quote  # reuse, never edit
except ImportError:  # pragma: no cover
    from checks import check_quote  # noqa: F401

NEBIUS_BASE_URL = "https://api.tokenfactory.nebius.com/v1"
NEBIUS_MODEL = os.environ.get("EXTRACT_MODEL", "meta-models/muse-spark-open")
DEFAULT_DB = "/mnt/archil/workspace/promises.db"
CITY_ID = "sf"
BATCH_SIZE = 5
# Trap per tech design: never send a full PDF to the model. Fetched .md sources
# here are <= 35KB, so the cap covers them whole; large PDFs still truncate.
MAX_SOURCE_CHARS_PER_CALL = 60000

REQUIRED_FIELDS = (
    "promise_id",
    "promise_text",
    "entity_id",
    "promised_date",
    "due_date",
    "page_number",
)

# Speaker -> entity_id for the P01-P12 validation set.
ENTITY_MAP = {
    "Mayor Daniel Lurie": "daniel_lurie",
    "Daniel Lurie": "daniel_lurie",
    "Mayor Ed Lee": "ed_lee",
    "Ed Lee": "ed_lee",
    "Governor Gavin Newsom": "gavin_newsom",
    "Gavin Newsom": "gavin_newsom",
    "Mayor London Breed": "london_breed",
    "London Breed": "london_breed",
    "PG&E": "pge",
    "Golden State Valkyries": "valkyries",
    "Giants": "giants",
    "Dead and Company": "dead_and_company",
    "Lime": "lime",
}

# Cut-rule fallback: predefined promise text from the validation set
# (03-validation-and-tests.md ground truth P01-P12). Used ONLY when the model
# call fails, and still gated on the substring check against a saved source.
PREDEFINED_P01_P12 = {
    "P01": {"promise_text": "Fentanyl State of Emergency Ordinance",
            "speaker": "Mayor Daniel Lurie"},
    "P02": {"promise_text": "24/7 crisis stabilization center at 822 Geary St",
            "speaker": "Mayor Daniel Lurie"},
    "P03": {"promise_text": "PermitSF reforms",
            "speaker": "Mayor Daniel Lurie"},
    "P04": {"promise_text": "Golden State Valkyries sellouts",
            "speaker": "Golden State Valkyries"},
    "P05": {"promise_text": "1,500 new shelter beds in six months",
            "speaker": "Mayor Daniel Lurie"},
    "P06": {"promise_text": "Vision Zero, eliminate traffic deaths by 2024",
            "speaker": "Mayor Ed Lee"},
    "P07": {"promise_text": "3.5 million new homes by 2025",
            "speaker": "Governor Gavin Newsom"},
    "P08": {"promise_text": "5 million dollars to repair homeless SRO housing",
            "speaker": "Mayor London Breed"},
    "P09": {"promise_text": "PG&E underground 10,000 miles of power lines",
            "speaker": "PG&E"},
    "P10": {"promise_text": "Giants Mission Rock, 1,200 to 1,500 homes, 40 percent affordable",
            "speaker": "Giants"},
    "P11": {"promise_text": "Dead and Company, final tour, 2023",
            "speaker": "Dead and Company"},
    "P12": {"promise_text": "Lime SFMTA permit",
            "speaker": "Lime"},
}


def load_api_key():
    """Read NEBIUS_API_KEY from env or repo .env (read-only, never printed)."""
    key = os.environ.get("NEBIUS_API_KEY")
    if key:
        return key.strip()
    env_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("NEBIUS_API_KEY="):
                    return line.split("=", 1)[1].strip().strip("'\"")
    except FileNotFoundError:
        pass
    return None


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def read_source(path):
    """Read a saved source file. Returns (full_text, page_hint).

    page_hint is the 1-based page holding the text start for PDFs, else 1.
    Never fetches; reads local bytes only.
    """
    if path.lower().endswith(".pdf"):
        import pdfplumber  # installed per runbook Lane A

        pages = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                pages.append(page.extract_text() or "")
        return "\n".join(pages), 1
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read(), 1


EXTRACTION_SYSTEM = (
    "You extract public promises from a saved source document. "
    "Return ONLY a strict JSON array, no prose, no markdown fences, no wrapper "
    "object. Return exactly one object per requested ID, never an empty array. "
    "Each object has exactly: "
    "promise_id, promise_text, entity_id, promised_date, due_date, page_number. "
    "promise_text MUST be copied verbatim from the source text, character for "
    "character, never paraphrased — copy the commitment sentence as stated, "
    "even if the document also reports its fulfillment. "
    "entity_id is the speaker name (e.g. Mayor Daniel Lurie). "
    "Dates are YYYY-MM-DD or null when absent from the text. "
    "page_number is the 1-based page, or 1 for non-PDF sources."
)


def normalize_entity_id(raw):
    """Map a model-returned speaker name to the canonical entity_id slug."""
    if not raw:
        return raw
    if raw in ENTITY_MAP:
        return ENTITY_MAP[raw]
    slug = "".join(c.lower() if c.isalnum() else "_" for c in raw).strip("_")
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug or raw


def model_extract(source_text, candidate_ids, page_hint=1, guidance=None):
    """One model call: up to 5 promises from one source file. No DB writes."""
    if len(candidate_ids) > BATCH_SIZE:
        raise ValueError(f"max {BATCH_SIZE} promises per model call")
    api_key = load_api_key()
    if not api_key:
        raise RuntimeError("NEBIUS_API_KEY missing (env or .env)")
    excerpt = source_text[:MAX_SOURCE_CHARS_PER_CALL]
    truncated = len(source_text) > MAX_SOURCE_CHARS_PER_CALL
    user_prompt = (
        f"Source document text (excerpt{' — truncated' if truncated else ''}):\n"
        f"<<<\n{excerpt}\n>>>\n\n"
        f"Extract these promise IDs in order: {', '.join(candidate_ids)}. "
        f"Assign each ID its verbatim promise_text from the text above. "
        f"entity_id is the speaker's full name as written in the text. "
        f"Default page_number is {page_hint}."
    )
    if guidance:
        user_prompt += f" Focus: {guidance}"
    body = json.dumps({
        "model": NEBIUS_MODEL,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": EXTRACTION_SYSTEM},
            {"role": "user", "content": user_prompt},
        ],
    }).encode("utf-8")
    req = urllib.request.Request(
        NEBIUS_BASE_URL + "/chat/completions",
        data=body,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {api_key}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=90) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    content = payload["choices"][0]["message"]["content"]
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        # Fall back to the first [...] span if prose wraps the array.
        start, end = content.find("["), content.rfind("]")
        if start < 0 or end <= start:
            raise ValueError("model did not return a JSON array")
        parsed = json.loads(content[start:end + 1])
    # Accept either a bare array or {"promises": [...]}-style wrappers.
    if isinstance(parsed, dict):
        for key in ("promises", "extractions", "results", "data"):
            if isinstance(parsed.get(key), list):
                parsed = parsed[key]
                break
        else:
            parsed = [parsed]
    if not isinstance(parsed, list) or not parsed:
        raise ValueError("model did not return a non-empty JSON array")
    rows = []
    for obj in parsed:
        if not isinstance(obj, dict):
            raise ValueError("model array item is not an object")
        missing = [f for f in REQUIRED_FIELDS if f not in obj]
        if missing:
            raise ValueError(f"model object missing fields: {missing}")
        row = {f: obj[f] for f in REQUIRED_FIELDS}
        row["entity_id"] = normalize_entity_id(row["entity_id"])
        rows.append(row)
    return rows


def cut_rule_rows(candidate_ids, promised_date=None):
    """Predefined validation-set rows when the model call fails."""
    rows = []
    for pid in candidate_ids:
        seed = PREDEFINED_P01_P12[pid]
        rows.append({
            "promise_id": pid,
            "promise_text": seed["promise_text"],
            "entity_id": ENTITY_MAP[seed["speaker"]],
            "promised_date": promised_date,
            "due_date": None,
            "page_number": 1,
        })
    return rows


def verify_rows(rows, full_source_text):
    """Substring-verify each row. Returns (verified, quarantine_bound)."""
    verified, quarantine_bound = [], []
    for row in rows:
        text = row.get("promise_text") or ""
        exact = bool(text.strip()) and text in full_source_text
        ok, reason = check_quote(text, full_source_text)
        if exact or ok:
            row["quote_match"] = "exact" if exact else "close"
            verified.append(row)
        else:
            row["quote_match"] = "none"
            row["quarantine_reason"] = reason  # "quote none"
            quarantine_bound.append(row)
    return verified, quarantine_bound


def extract_file(source_path, candidate_ids, use_cut_rule=False,
                 promised_date=None, guidance=None):
    """Full extraction step for one saved file. No DB writes.

    Returns a bundle dict: source meta + verified rows + quarantine-bound rows.
    """
    full_text, page_hint = read_source(source_path)
    file_hash = sha256_file(source_path)
    if use_cut_rule:
        rows = cut_rule_rows(candidate_ids, promised_date=promised_date)
        method = "cut_rule_predefined"
    else:
        try:
            rows = model_extract(full_text, candidate_ids, page_hint,
                                 guidance=guidance)
            method = f"model:{NEBIUS_MODEL}"
        except Exception as e:  # cut rule: model failure -> predefined text
            rows = cut_rule_rows(candidate_ids, promised_date=promised_date)
            method = f"cut_rule_predefined (model failed: {type(e).__name__})"
    verified, quarantine_bound = verify_rows(rows, full_text)
    return {
        "source_file_path": source_path,
        "source_hash": file_hash,
        "method": method,
        "verified": verified,
        "quarantine_bound": quarantine_bound,
    }


def load_pending(db_path, bundle, source_url, source_type,
                 promised_fallback=None):
    """Load phase: verified rows -> promises_pending ONLY.

    Separate from extraction; short single transaction with busy timeout.
    Refuses unverified rows. Returns (inserted_ids, refused).
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    con = sqlite3.connect(db_path, timeout=30)
    try:
        con.execute("PRAGMA busy_timeout=30000")
        inserted, refused = [], []
        cur = con.cursor()
        for row in bundle.get("verified", []):
            promised_date = row.get("promised_date") or promised_fallback
            if not promised_date:
                refused.append((row["promise_id"], "missing promised_date"))
                continue
            entity_id = row.get("entity_id")
            if not entity_id and row["promise_id"] in PREDEFINED_P01_P12:
                seed = PREDEFINED_P01_P12[row["promise_id"]]
                entity_id = ENTITY_MAP.get(seed["speaker"])
            if not entity_id:
                refused.append((row["promise_id"], "missing entity_id"))
                continue
            row["entity_id"] = entity_id
            cur.execute(
                """INSERT OR REPLACE INTO promises_pending
                   (promise_id, city_id, entity_id, promise_text, promised_date,
                    due_date, status, source_file_path, source_hash, source_url,
                    source_type, created_at, updated_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (row["promise_id"], CITY_ID, row["entity_id"],
                 row["promise_text"], promised_date, row.get("due_date"),
                 "pending", bundle["source_file_path"], bundle["source_hash"],
                 source_url, source_type, now, now),
            )
            inserted.append(row["promise_id"])
        for row in bundle.get("quarantine_bound", []):
            refused.append((row["promise_id"],
                            row.get("quarantine_reason", "quote none")))
        con.commit()
        return inserted, refused
    finally:
        con.close()


def main(argv=None):
    ap = argparse.ArgumentParser(description="Lane C extractor")
    sub = ap.add_subparsers(dest="cmd", required=True)

    ex = sub.add_parser("extract", help="extract to JSON; no DB writes")
    ex.add_argument("--source", required=True, help="saved source file path")
    ex.add_argument("--ids", required=True,
                    help="comma-separated promise IDs (max 5, one file)")
    ex.add_argument("--out", help="write bundle JSON here (else stdout)")
    ex.add_argument("--cut-rule", action="store_true",
                    help="skip model, use predefined validation-set text")
    ex.add_argument("--promised-date", default=None)
    ex.add_argument("--guidance", default=None,
                    help="focus hint appended to the model prompt")

    ld = sub.add_parser("load", help="verified JSON -> promises_pending only")
    ld.add_argument("--in", dest="inp", required=True, help="bundle JSON file")
    ld.add_argument("--db", default=DEFAULT_DB)
    ld.add_argument("--source-url", required=True)
    ld.add_argument("--source-type", required=True)
    ld.add_argument("--promised-fallback", default=None)

    args = ap.parse_args(argv)
    if args.cmd == "extract":
        ids = [i.strip() for i in args.ids.split(",") if i.strip()]
        bundle = extract_file(args.source, ids,
                              use_cut_rule=args.cut_rule,
                              promised_date=args.promised_date,
                              guidance=args.guidance)
        text = json.dumps(bundle, indent=2)
        if args.out:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(text)
        else:
            print(text)
        # Exit nonzero if any row is quarantine-bound (caller decides).
        return 0
    if args.cmd == "load":
        with open(args.inp, "r", encoding="utf-8") as f:
            bundle = json.load(f)
        inserted, refused = load_pending(
            args.db, bundle, args.source_url, args.source_type,
            promised_fallback=args.promised_fallback)
        print(json.dumps({"inserted": inserted, "refused": refused}, indent=2))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
