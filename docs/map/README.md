# Street basemap assets (issue #44)

Everything the Map & Districts street map needs is served from this directory.
The page makes no request to a third-party map, tile, font or CDN host.
`docs/app.js` loads these files only when the Map & Districts view is first
opened. The page itself does not reference them.

PMTiles is read with HTTP Range requests. GitHub Pages supports them, but
`python3 -m http.server` does not. To preview locally, use a server that
supports Range.

## Map data

| File | Size (bytes) | Content | License |
| --- | ---: | --- | --- |
| `sf-z14.pmtiles` | 5,407,797 | Protomaps vector tiles for San Francisco including SFO, zoom 0–14, bounds -122.53,37.60,-122.35,37.84. Extracted from the Protomaps daily planet build `20261123` (https://build.protomaps.com/20261123.pmtiles) with `pmtiles extract`. | © OpenStreetMap contributors, Open Database License (ODbL) 1.0: https://www.openstreetmap.org/copyright |

The tiles are © OpenStreetMap contributors and are available under the ODbL.
The map shows this credit with a link to https://www.openstreetmap.org/copyright
in MapLibre's attribution control, next to the "Protomaps" and "MapLibre" credits.

## Libraries (`vendor/`)

Versions are also listed in `vendor/VERSIONS.txt`.

| File | Size (bytes) | Package and version | License | Source |
| --- | ---: | --- | --- | --- |
| `vendor/maplibre-gl.js` | 1,058,059 | maplibre-gl 5.24.1 (`dist/maplibre-gl.js`) | BSD-3-Clause, `vendor/LICENSE-maplibre.txt` | https://github.com/maplibre/maplibre-gl-js (npm `maplibre-gl@5.24.1`) |
| `vendor/maplibre-gl.css` | 70,024 | maplibre-gl 5.24.1 (`dist/maplibre-gl.css`) | BSD-3-Clause, `vendor/LICENSE-maplibre.txt` | https://github.com/maplibre/maplibre-gl-js (npm `maplibre-gl@5.24.1`) |
| `vendor/pmtiles.js` | 20,229 | pmtiles 4.5.0 (`dist/pmtiles.js`, global `pmtiles`) | BSD-3-Clause, `vendor/LICENSE-pmtiles.txt` | https://github.com/protomaps/PMTiles (npm `pmtiles@4.5.0`) |
| `vendor/basemaps.js` | 38,680 | @protomaps/basemaps 5.7.2 (`dist/basemaps.js`, global `basemaps`) | BSD-3-Clause (code); style design CC0; some icons MIT (Mapzen); see `vendor/LICENSE-basemaps.txt` | https://github.com/protomaps/basemaps (npm `@protomaps/basemaps@5.7.2`) |
| `vendor/LICENSE-maplibre.txt` | 5,984 | MapLibre GL JS license text | — | maplibre-gl-js repository |
| `vendor/LICENSE-pmtiles.txt` | 1,713 | PMTiles license text | — | PMTiles repository |
| `vendor/LICENSE-basemaps.txt` | 3,289 | Protomaps basemaps license and attribution text | — | basemaps repository |
| `vendor/VERSIONS.txt` | 59 | Pinned versions of the three packages | — | — |

## Sprites and glyphs

| Path | Size (bytes) | Content | License | Source |
| --- | ---: | --- | --- | --- |
| `sprites/light.json`, `sprites/light.png`, `sprites/light@2x.json`, `sprites/light@2x.png` | 52,154 | Protomaps "light" sprite sheet (POI and shield icons) | Protomaps basemaps assets: CC0 design, some icons derived from Mapzen icons under MIT (see `vendor/LICENSE-basemaps.txt`) | https://github.com/protomaps/basemaps-assets (`sprites/`) |
| `fonts/{Noto Sans Regular,Noto Sans Medium,Noto Sans Italic}/{0-255,256-511,8192-8447}.pbf` | 805,565 (9 files) | Signed-distance-field glyph ranges generated from Noto Sans: Basic Latin, Latin-1, Latin Extended-A/B and General Punctuation | SIL Open Font License 1.1, `fonts/LICENSE-OFL.txt` | https://github.com/protomaps/basemaps-assets (`fonts/`) |
| `fonts/LICENSE-OFL.txt` | 4,477 | OFL 1.1 text for Noto Sans | — | — |

The app limits every label to these three font stacks. Labels in other scripts
(for example Cyrillic) would need glyph ranges that are not shipped here.
MapLibre draws CJK characters with the browser's local font, so they make no
glyph request.

## Size

7,471,993 bytes (about 7.5 MB, 7.1 MiB) in total, measured with `du -sb docs/map`. Adding zoom levels, a larger extent
or more glyph ranges raises that, so check the size in review first.
