"""Copy the facts the video needs from demo/data.json (DB export) into src/data.json."""
import json, re
d = json.load(open("../demo/data.json"))
clean = lambda s: re.sub(r"\*\*", "", re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s or ""))
ids = ["P82", "P11", "P10", "P05", "P02", "P21"]
by = {p["promise_id"]: p for p in d["promises"]}
out = {
    "counts": d["database_status"]["counts"],
    "total": len(d["promises"]),
    "planted": len(d["quarantined"]),
    "cards": [{"id": i, "entity": by[i]["entity"], "verdict": by[i]["verdict"],
               "quote": clean(by[i]["promise_text"])[:150],
               "domain": re.sub(r"^https?://(www\.)?","",by[i]["source_url"]).split("/")[0], "made": by[i]["promised_date"], "reason": clean(by[i]["verdict_reason"]).split(" [")[0][:130], "hash": by[i]["source_hash"][:12], "file": by[i]["source_file_path"].split("/")[-1]}
              for i in ids],
    "planted_example": d["quarantined"][0],
}
json.dump(out, open("src/data.json", "w"), indent=1)
