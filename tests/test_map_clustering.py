"""Map marker clustering, touch targets and interaction (issue #44).

Runs the pure block of docs/app.js (SFPMAP_PURE_START .. SFPMAP_PURE_END) in node,
with a minimal fake DOM for the interaction functions. No new npm dependencies.
The map stays the self-hosted SVG (no third-party tiles, per issue #82).
"""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP = (ROOT / "docs" / "app.js").read_text(encoding="utf-8")

PRELUDE = r"""
const fs = require('fs');
const src = fs.readFileSync('docs/app.js', 'utf8');
const pa = src.indexOf('/* SFPMAP_PURE_START */'), pb = src.indexOf('/* SFPMAP_PURE_END */');
if (pa < 0 || pb < 0) { console.error('pure map block missing'); process.exit(2); }
const M = new Function(src.slice(pa, pb) + '\nreturn { clusterPins, mapHitDiameterPx, mapSvgOpenTag, bindMapMarkers, findMapMarker, openMapCluster, closeMapCluster };')();
const input = JSON.parse(fs.readFileSync(0, 'utf8') || 'null');

// Minimal fake DOM: nodes with attributes, listeners, classList, focus tracking.
let focused = null;
function node(attrs, cls) {
  const l = {};
  const n = {
    attrs: attrs || {}, listeners: l, cls: new Set(cls || []), innerHTML: '', children: [],
    getAttribute(k) { return k in this.attrs ? this.attrs[k] : null; },
    addEventListener(t, f) { (l[t] = l[t] || []).push(f); },
    focus() { focused = this; },
    classList: { add: c => n.cls.add(c), remove: c => n.cls.delete(c), contains: c => n.cls.has(c) },
    fire(t, e) { (l[t] || []).forEach(f => f(e || {})); },
  };
  return n;
}
function root(nodes) {
  return { querySelectorAll(sel) {
    const keys = sel.split(',').map(s => s.trim().slice(1, -1));
    const out = nodes.filter(n => keys.some(k => k in n.attrs));
    out.forEach = out.forEach.bind(out);
    return out;
  } };
}
"""


def node_run(body, payload=None):
    out = subprocess.run(["node", "-e", PRELUDE + body], input=json.dumps(payload),
                         capture_output=True, text=True, cwd=ROOT)
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout)


def cluster(pins, min_dist):
    return node_run(
        "console.log(JSON.stringify(M.clusterPins(input.pins, input.minDist).map("
        "c => ({ids: c.items.map(i => i.p.promise_id), x: c.x, y: c.y, inSFO: c.inSFO}))));",
        {"pins": pins, "minDist": min_dist})


def pin(pid, x, y, sfo=False):
    return {"p": {"promise_id": pid}, "x": x, "y": y, "inSFO": sfo}


def test_close_pins_merge_and_far_pins_stay_single():
    r = cluster([pin("P1", 100, 100), pin("P2", 110, 105), pin("P3", 400, 250)], 40)
    assert sorted(sorted(c["ids"]) for c in r) == [["P1", "P2"], ["P3"]]
    merged = next(c for c in r if len(c["ids"]) == 2)
    assert (merged["x"], merged["y"]) == (105, 102.5)


def test_chain_merge_converges():
    # Merging P1+P2 moves the centroid within reach of P3; a single greedy pass would leave them apart.
    r = cluster([pin("P1", 0, 0), pin("P2", 25, 0), pin("P3", 45, 0)], 40)
    assert len(r) == 1 and r[0]["ids"] == ["P1", "P2", "P3"]


def test_sfo_inset_pins_never_merge_with_city_pins():
    assert len(cluster([pin("P1", 430, 340), pin("P2", 432, 341, sfo=True)], 60)) == 2


def _real_pins():
    """Pins from docs/data.json, projected with the projection code taken from app.js itself."""
    data = json.loads((ROOT / "docs" / "data.json").read_text())["promises"]
    return node_run(r"""
const a = src.indexOf('const minLat'), b = src.indexOf('const verdictColor');
const proj = src.slice(a, b);
const c0 = src.indexOf('const inSFO ='), c1 = src.indexOf('if (!inSF && !inSFO)');
const classify = src.slice(c0, c1);
const f = new Function('lat', 'lon', proj + classify + `
  if (!inSF && !inSFO) return null;
  const pt = inSFO ? projectSFO(lat, lon) : projectSF(lat, lon);
  return { x: pt.x, y: pt.y, inSFO, W };`);
const pins = [];
input.forEach(p => {
  const lat = Number(p.latitude), lon = Number(p.longitude);
  if (!Number.isFinite(lat) || !Number.isFinite(lon)) return;
  const r = f(lat, lon);
  if (r) pins.push({ p: { promise_id: p.promise_id }, x: r.x, y: r.y, inSFO: r.inSFO, W: r.W });
});
console.log(JSON.stringify(pins));
""", data)


def test_real_export_clusters_never_overlap_at_mobile_and_desktop_sizes():
    pins = _real_pins()
    assert len(pins) > 20
    w = pins[0]["W"]
    sizes = {"phone-360": (360, True), "phone-390": (390, True), "tablet-coarse-820": (820, True),
             "desktop-560": (560, False), "desktop-1100": (1100, False)}
    for label, (width, mobile) in sizes.items():
        diameter = node_run("console.log(JSON.stringify(M.mapHitDiameterPx(input)));", mobile)
        min_dist = diameter / (width / w)
        r = cluster([{k: v for k, v in p.items() if k != "W"} for p in pins], min_dist)
        assert sum(len(c["ids"]) for c in r) == len(pins), label
        for i, c1 in enumerate(r):
            for c2 in r[i + 1:]:
                if c1["inSFO"] != c2["inSFO"]:
                    continue
                d = ((c1["x"] - c2["x"]) ** 2 + (c1["y"] - c2["y"]) ** 2) ** 0.5
                assert d >= min_dist - 1e-9, (label, c1["ids"], c2["ids"], d, min_dist)
        # Hit circles of different coordinate spaces (city vs SFO inset) may not overlap either.
        for i, c1 in enumerate(r):
            for c2 in r[i + 1:]:
                d = ((c1["x"] - c2["x"]) ** 2 + (c1["y"] - c2["y"]) ** 2) ** 0.5
                assert d >= min_dist - 1e-9, ("cross-space", label, c1["ids"], c2["ids"])


def test_touch_target_sizes():
    r = node_run("console.log(JSON.stringify([M.mapHitDiameterPx(true), M.mapHitDiameterPx(false)]));")
    assert r[0] >= 44 and r[1] >= 24


def test_svg_is_a_group_so_marker_buttons_stay_exposed():
    tag = node_run("console.log(JSON.stringify(M.mapSvgOpenTag(560, 430)));")
    assert 'role="group"' in tag and 'aria-label="' in tag and 'role="img"' not in tag
    assert 'role="img"' not in APP[APP.index("function renderMapAndDistrictsView"):APP.index("function renderEntityProfilesView")]


def test_single_marker_click_enter_space_open_record_only():
    r = node_run(r"""
const m = node({ 'data-promise-id': 'P7' });
const calls = [];
M.bindMapMarkers(root([m]), { openPromise: (id, n) => calls.push(['promise', id, n === m]), openCluster: () => calls.push(['cluster']) });
let prevented = 0;
m.fire('click');
m.fire('keydown', { key: 'Enter', preventDefault() { prevented++; } });
m.fire('keydown', { key: ' ', preventDefault() { prevented++; } });
m.fire('keydown', { key: 'Tab', preventDefault() { prevented++; } });
console.log(JSON.stringify({ calls, prevented }));
""")
    assert r["calls"] == [["promise", "P7", True]] * 3 and r["prevented"] == 2


def test_cluster_activation_passes_ids_and_focus_moves_into_list_then_back():
    r = node_run(r"""
const marker = node({ 'data-cluster-ids': 'P1,P2,P3' });
const single = node({ 'data-promise-id': 'P9' });
const rt = root([marker, single]);
const got = [];
M.bindMapMarkers(rt, { openPromise() {}, openCluster: (ids, n) => got.push([ids, n === marker]) });
marker.fire('keydown', { key: 'Enter', preventDefault() {} });

const card = node({}, ['hidden']);
const firstItem = node({});
card.querySelector = sel => sel === '.btn-map-cluster-item' ? firstItem : null;
const opened = M.openMapCluster(card, '<ul>list</ul>');
const afterOpen = { hidden: card.cls.has('hidden'), html: card.innerHTML, focusIsList: focused === firstItem };

const closed = M.closeMapCluster(card, rt, ['P2', 'P3']);
const afterClose = { hidden: card.cls.has('hidden'), focusIsMarker: focused === marker };
const noMarker = M.closeMapCluster(card, rt, ['NOPE']);
console.log(JSON.stringify({ got, opened, afterOpen, closed, afterClose, noMarker }));
""")
    assert r["got"] == [[["P1", "P2", "P3"], True]]
    assert r["opened"] and r["afterOpen"] == {"hidden": False, "html": "<ul>list</ul>", "focusIsList": True}
    assert r["closed"] and r["afterClose"] == {"hidden": True, "focusIsMarker": True}
    assert r["noMarker"] is False


def test_find_marker_after_rerender_maps_member_to_new_cluster():
    r = node_run(r"""
const n1 = node({ 'data-cluster-ids': 'P1,P2' }), n2 = node({ 'data-promise-id': 'P3' });
const rt = root([n1, n2]);
console.log(JSON.stringify([M.findMapMarker(rt, 'P2') === n1, M.findMapMarker(rt, 'P3') === n2, M.findMapMarker(rt, 'P4')]));
""")
    assert r == [True, True, None]


def test_dead_state_removed_and_single_tap_does_not_fill_card():
    assert "lastMapMobile" not in APP
    region = APP[APP.index("bindMapMarkers(mapWrap, {"):]
    single = region[:region.index("openCluster:")]
    assert "openInspectDrawer(pid)" in single and "selectedCard.innerHTML" not in single


def test_map_stays_self_hosted_no_third_party_tiles():
    html = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
    for token in ("maplibre", "openstreetmap", "tile.", "leaflet", "mapbox"):
        assert token not in (APP + html).lower(), token
