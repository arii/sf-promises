"""Run candidate source and temporal checks inside an isolated fork."""

import json
from datetime import date
from pathlib import Path

from src.evidence import screen_saved_source
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
        deadline = date.fromisoformat(origin["deadline"])
        failures.extend(check_origin_dates(promised, published, deadline))
        if promised > published:
            failures.append("promise_after_publication")
    return {"failures": failures}


if __name__ == "__main__":
    root = Path("/tmp/sf-promises-audit/sources")
    request = json.loads(Path("/tmp/sf-promises-audit/request.json").read_text())
    print(json.dumps(check_request(request, root)))
