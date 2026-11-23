"""Entity avatars from the same-origin media manifest (issue #83).

docs/app.js maps entity names to avatars from docs/media/manifest.json when an
exported record has no entity_image_path, so avatars show without regenerating
docs/data.json. The name normalisation and rendering run in node.
"""
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP = (ROOT / "docs" / "app.js").read_text(encoding="utf-8")

HARNESS = r"""
const fs = require('fs');
const src = fs.readFileSync('docs/app.js', 'utf8');
const s = src.indexOf('/* SFPDRAWER_PURE_START */'), e = src.indexOf('/* SFPDRAWER_PURE_END */');
const window = {};
new Function('window', src.slice(s, e) + '\nwindow.SFPDrawer = SFPDrawer;')(window);
const D = window.SFPDrawer;
const manifest = JSON.parse(fs.readFileSync('docs/media/manifest.json', 'utf8'));
const data = JSON.parse(fs.readFileSync('docs/data.json', 'utf8'));
const map = D.entityMediaFromManifest(manifest);
const groupNames = new Set(data.promises.map(p => D.entityNameKey(p.entity_canonical_name || p.entity || 'Unknown')));
const rows = manifest.entities.map(en => {
  const m = D.entityMediaFor(map, en.entity_name);
  return { name: en.entity_name, matched: groupNames.has(D.entityNameKey(en.entity_name)), found: !!m,
    html: m ? D.entityAvatarHtml({ entityImagePath: m.path, entityImageCredit: m.credit, entityImageLicenseUrl: m.licenseUrl, entityImageNote: m.note }) : '',
    license: en.license, logo: !!en.logo, restrictions: en.restrictions || '' };
});
const synthetic = {
  ccby: D.entityAvatarHtml({ entityImagePath: 'media/entities/a.webp', entityImageCredit: 'Jo / CC BY 4.0', entityImageLicenseUrl: 'https://creativecommons.org/licenses/by/4.0/' }),
  badUrl: D.entityAvatarHtml({ entityImagePath: 'media/entities/a.webp', entityImageCredit: 'Jo', entityImageLicenseUrl: 'javascript:alert(1)' }),
  fromManifest: D.entityMediaFromManifest({ entities: [
    { entity_name: '  Ünï  Co ', path: 'entities/x.webp', credit: 'A', license: 'CC BY-SA 4.0', license_url: 'https://creativecommons.org/licenses/by-sa/4.0/' },
    { entity_name: 'PD Co', path: 'entities/y.webp', credit: 'B', license: 'Public domain', license_url: 'https://commons.wikimedia.org/wiki/File:Y.svg' }] }),
};
const look = n => { const m = D.entityMediaFor(synthetic.fromManifest, n); return m && { path: m.path, licenseUrl: m.licenseUrl }; };
console.log(JSON.stringify({ rows, ccby: synthetic.ccby, badUrl: synthetic.badUrl,
  keyed: look('ünï co'), pd: look('pd co'), none: look('Nobody') }));
"""


def _out():
    r = subprocess.run(["node", "-e", HARNESS], capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def test_every_manifest_entity_matches_an_entity_in_data_json_and_gets_an_avatar():
    rows = _out()["rows"]
    assert len(rows) >= 11
    for row in rows:
        assert row["matched"], f"{row['name']} matches no entity in docs/data.json"
        assert row["found"] and 'src="media/entities/' in row["html"], row["name"]


def test_page_makes_no_third_party_request_for_avatars():
    for row in _out()["rows"]:
        srcs = re.findall(r'src="([^"]+)"', row["html"])
        assert srcs and all(not re.match(r"^[a-z][a-z0-9+.-]*:|^//|^/", s, re.I) for s in srcs), row["name"]
        assert "<link" not in row["html"] and "srcset" not in row["html"]
    # The manifest is fetched same-origin and its original_url (Commons) is never used by the page.
    assert "fetch('media/manifest.json')" in APP
    assert "original_url" not in APP and "upload.wikimedia.org" not in APP


def test_name_normalisation_is_case_and_space_insensitive():
    out = _out()
    assert out["keyed"] == {"path": "media/entities/x.webp", "licenseUrl": "https://creativecommons.org/licenses/by-sa/4.0/"}
    assert out["pd"]["licenseUrl"] == "" and out["none"] is None


def test_cc_by_credit_links_the_licence_and_font_is_readable():
    out = _out()
    assert 'href="https://creativecommons.org/licenses/by/4.0/"' in out["ccby"] and 'rel="noopener noreferrer"' in out["ccby"]
    assert "javascript:" not in out["badUrl"] and "<a " not in out["badUrl"]
    css = (ROOT / "docs" / "styles.css").read_text(encoding="utf-8")
    block = css[css.index(".entity-avatar-credit {"):]
    size = re.search(r"font-size:\s*([\d.]+)rem", block.split("}")[0])
    assert size and float(size.group(1)) >= 0.75


def test_logos_and_trademarked_files_show_trademark_note_and_giants_restriction_recorded():
    rows = {r["name"]: r for r in _out()["rows"]}
    for name, r in rows.items():
        if r["logo"] or "trademark" in r["restrictions"].lower():
            assert "Logo is a trademark of its owner" in r["html"], name
        else:
            assert "trademark" not in r["html"], name
    assert rows["San Francisco Giants"]["restrictions"] == "trademarked"
    for name in ("Waymo", "Zoox", "Pacific Gas & Electric (PG&E)", "San Francisco Giants"):
        assert rows[name]["logo"], name
