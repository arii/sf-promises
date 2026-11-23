"""Map marker clustering and touch targets (issue #44).

Runs the pure block of docs/app.js (SFPMAP_PURE_START .. SFPMAP_PURE_END) in node.
The map stays the self-hosted SVG (no third-party tiles, per issue #82).
"""
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
APP = (ROOT / "docs" / "app.js").read_text(encoding="utf-8")

HARNESS = r"""
const fs = require('fs');
const src = fs.readFileSync('docs/app.js', 'utf8');
const a = src.indexOf('/* SFPMAP_PURE_START */'), b = src.indexOf('/* SFPMAP_PURE_END */');
if (a < 0 || b < 0) { console.error('pure map block missing'); process.exit(2); }
const f = new Function(src.slice(a, b) + '\nreturn { clusterPins, mapHitDiameterPx };')();
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
console.log(JSON.stringify({
  clusters: f.clusterPins(input.pins, input.minDist).map(c => ({ ids: c.items.map(i => i.p.promise_id), x: c.x, y: c.y, inSFO: c.inSFO })),
  mobile: f.mapHitDiameterPx(true), desktop: f.mapHitDiameterPx(false),
}));
"""


def run(pins, min_dist):
    out = subprocess.run(["node", "-e", HARNESS], input=json.dumps({"pins": pins, "minDist": min_dist}),
                         capture_output=True, text=True, cwd=ROOT, check=True)
    return json.loads(out.stdout)


def pin(pid, x, y, sfo=False):
    return {"p": {"promise_id": pid}, "x": x, "y": y, "inSFO": sfo}


def test_close_pins_merge_and_far_pins_stay_single():
    r = run([pin("P1", 100, 100), pin("P2", 110, 105), pin("P3", 400, 250)], 40)
    assert sorted(sorted(c["ids"]) for c in r["clusters"]) == [["P1", "P2"], ["P3"]]
    merged = next(c for c in r["clusters"] if len(c["ids"]) == 2)
    assert (merged["x"], merged["y"]) == (105, 102.5)


def test_sfo_inset_pins_never_merge_with_city_pins():
    r = run([pin("P1", 430, 340), pin("P2", 432, 341, sfo=True)], 60)
    assert len(r["clusters"]) == 2


def test_clusters_account_for_every_pin_on_real_export():
    data = json.loads((ROOT / "docs" / "data.json").read_text())["promises"]
    pins = []
    for p in data:
        lat, lon = p.get("latitude"), p.get("longitude")
        if isinstance(lat, (int, float)) and isinstance(lon, (int, float)) and 37.704 <= lat <= 37.836 and -122.516 <= lon <= -122.354:
            x = (lon + 122.516) / 0.162 * 500 + 30
            y = (37.836 - lat) / 0.132 * 360 + 28
            pins.append(pin(p["promise_id"], x, y))
    r = run(pins, 69)  # 44px on a 0.64-scale phone map
    cs = r["clusters"]
    assert sum(len(c["ids"]) for c in cs) == len(pins)
    assert len(cs) <= len(pins)
    assert r["mobile"] >= 44 and r["desktop"] >= 24


def test_markers_have_44px_hit_area_and_open_drawer():
    assert 'class="map-pin-hit"' in APP and "mapHitDiameterPx(isMobile)" in APP
    assert "return isMobile ? 44 : 28;" in APP
    handler = APP[APP.index("const pid = node.getAttribute('data-promise-id')"):]
    assert "openInspectDrawer(p.promise_id);" in handler.split("data-cluster-ids")[0]


def test_map_stays_self_hosted_no_third_party_tiles():
    html = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
    for token in ("maplibre", "openstreetmap", "tile.", "leaflet", "mapbox"):
        assert token not in (APP + html).lower(), token
