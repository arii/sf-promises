"""Self-hosted street basemap for the Map & Districts view (issue #44).

The street map uses MapLibre GL JS, PMTiles and Protomaps basemaps, all served
from docs/map/. These tests check that the libraries are lazy-loaded (not
referenced by index.html), that every asset app.js names exists on disk, that
app.js names no third-party map, tile or font host, and that docs/map/README.md
documents every vendored file.
"""
import re
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
MAP = DOCS / "map"
APP = (DOCS / "app.js").read_text(encoding="utf-8")
HTML = (DOCS / "index.html").read_text(encoding="utf-8")
README = (MAP / "README.md").read_text(encoding="utf-8")

# Links shown in the attribution control. They are anchors the user may follow,
# never fetched by the page.
ATTRIBUTION_LINKS = {
    "https://www.openstreetmap.org/copyright",
    "https://protomaps.com",
    "https://maplibre.org",
}
MAP_HOST_HINTS = re.compile(
    r"tile|map|font|glyph|sprite|protomaps|openstreetmap|osm|carto|stadia|arcgis|"
    r"unpkg|jsdelivr|cdnjs|googleapis|gstatic|cloudflare|maptiler|thunderforest",
    re.I,
)


def _street_block():
    start = APP.index("const STREET_MAP_ASSETS = {")
    end = APP.index("function renderMapAndDistrictsView(list) {")
    return APP[start:end]


def test_index_html_does_not_load_map_libraries():
    lower = HTML.lower()
    for token in ("maplibre", "pmtiles", "basemaps.js", "map/vendor", "sf-z14"):
        assert token not in lower, token


def test_map_libraries_are_inserted_dynamically():
    block = _street_block()
    assert "document.createElement('script')" in block
    assert "document.createElement('link')" in block
    assert "maplibregl.addProtocol('pmtiles', createStreetMap.protocol.tile)" in block
    assert "new window.pmtiles.Protocol()" in block
    assert "`pmtiles://${tilesUrl}`" in block and "new URL(STREET_MAP_ASSETS.tiles, page)" in block
    assert "cluster: true" in block and "getClusterExpansionZoom" in block
    assert "cooperativeGestures: true" in block and "maxBounds" in block and "maxZoom: 16" in block


def test_every_map_asset_path_in_app_js_exists():
    paths = set(re.findall(r"""['"`](map/[^'"`]*)['"`]""", APP))
    assert {"map/vendor/maplibre-gl.js", "map/vendor/maplibre-gl.css", "map/vendor/pmtiles.js",
            "map/vendor/basemaps.js", "map/sf-z14.pmtiles", "map/sprites/light", "map/fonts/"} <= paths
    for rel in paths:
        target = DOCS / rel
        if rel.endswith("/"):
            assert target.is_dir(), rel
        elif rel == "map/sprites/light":
            for suffix in (".json", ".png", "@2x.json", "@2x.png"):
                assert (DOCS / (rel + suffix)).is_file(), rel + suffix
        else:
            assert target.is_file(), rel


def test_every_font_stack_used_has_glyphs_on_disk():
    fonts = re.search(r"const STREET_MAP_FONTS = \[([^\]]*)\]", APP).group(1)
    stacks = re.findall(r"'([^']+)'", fonts)
    assert stacks == ["Noto Sans Regular", "Noto Sans Medium", "Noto Sans Italic"]
    used = set(re.findall(r"'text-font': \['([^']+)'\]", APP))
    assert used and used <= set(stacks)
    for stack in stacks:
        for rng in ("0-255", "256-511", "8192-8447"):
            assert (MAP / "fonts" / stack / f"{rng}.pbf").is_file(), (stack, rng)


def test_app_js_names_no_third_party_map_tile_or_font_host():
    for url in re.findall(r"https?://[^\s'\"`<>)]+", APP):
        host = urlparse(url).netloc
        if not MAP_HOST_HINTS.search(host + urlparse(url).path):
            continue
        assert url in ATTRIBUTION_LINKS, f"third-party map/tile/font URL in app.js: {url}"
    # Attribution URLs appear only as link targets, not as fetched resources.
    for url in ATTRIBUTION_LINKS:
        for m in re.finditer(re.escape(url), APP):
            assert APP[m.start() - 6:m.start()] == 'href="', url
    assert "//" not in "".join(re.findall(r"STREET_MAP_ASSETS = \{[^}]*\}", APP))


def test_attribution_credits_osm_protomaps_and_maplibre():
    block = _street_block()
    assert 'href="https://www.openstreetmap.org/copyright"' in block
    assert "&copy; OpenStreetMap contributors" in block
    assert ">Protomaps</a>" in block and ">MapLibre</a>" in block
    assert "new maplibregl.AttributionControl({ compact: isMobile" in block


def test_readme_lists_every_vendor_file_and_licenses():
    for f in sorted((MAP / "vendor").iterdir()):
        assert f"`vendor/{f.name}`" in README, f.name
    for needle in ("sf-z14.pmtiles", "ODbL", "OpenStreetMap contributors", "20261123",
                   "5.24.1", "4.5.0", "5.7.2", "BSD-3-Clause", "Open Font License", "sprites/light"):
        assert needle in README, needle
    assert (MAP / "fonts" / "LICENSE-OFL.txt").is_file()


def test_map_assets_stay_within_size_budget():
    total = sum(p.stat().st_size for p in MAP.rglob("*") if p.is_file())
    assert total < 7.8 * 1000 * 1000, total


def test_simple_map_toggle_and_fallback_are_wired():
    for el_id in ('id="btn-map-mode-street"', 'id="btn-map-mode-simple"', 'id="map-mode-note"',
                  'id="street-map"', 'id="sf-svg-map-wrap"'):
        assert el_id in HTML, el_id
    assert "keyboard accessible" in HTML
    block = _street_block()
    assert "localStorage" in block and "webglAvailable()" in block and "streetMapFallback" in block
    assert "getCanvas().setAttribute('aria-label'" in block
