"""Run candidate source and temporal checks in a local job directory."""

import json
from datetime import date
from pathlib import Path

from src.evidence import screen_saved_source
from src.outcome_rules import origin_date_failures
from src.temporal import check_origin_dates, screen_forward_looking


def check_request(request, root):
    failures = []
    for source in request["sources"]:
        failures.extend(screen_saved_source(
            root=root, promise_id="job",
            path=str(root / "job" / (source["sha256"] + ".md")),
            digest=source["sha256"], quote=source["quote"],
            url=source["url"], source_tier=source["tier"],
        ))
    origin = request.get("origin")
    if origin:
        failures.extend(screen_forward_looking(origin["quote"]))
        promised = date.fromisoformat(origin["promised"])
        published = date.fromisoformat(origin["published"])
        deadline = date.fromisoformat(origin["deadline"]) if origin.get("deadline") else None
        dates = check_origin_dates(promised, published, deadline)
        if origin.get("outcome_rules") is True:
            # Same R1/R2 waivers the audit applied (SF_PROMISES_OUTCOME_RULES):
            # the worker re-derives them from the quote, it does not trust a list.
            dates, _ = origin_date_failures(dates, promised, deadline,
                                            quote=origin["quote"], published=published)
        failures.extend(dates)
        if promised > published:
            failures.append("promise_after_publication")
    return {"failures": failures}


if __name__ == "__main__":
    root = Path("sources").resolve()
    request = json.loads(Path("request.json").read_text())
    print(json.dumps(check_request(request, root)))
