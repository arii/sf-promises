"""Story-card media test: featured-story cards surface the export's source media
opt-in only (issue #44).

The story-card media HTML builders live in a marked pure block of docs/app.js
(SFPSTORY_PURE_START .. SFPSTORY_PURE_END). This test executes that block with
node over docs/data.json and asserts:

- the initial card markup is an opt-in button with the export URL/caption in
  escaped data-* attributes: it contains NO src=/srcset= reference, so viewing
  or scrolling the page issues no third-party requests (the pre-existing
  request boundary: remote media loads only after an explicit user action);
- every static story card in docs/index.html whose record carries an image in
  the export gets a button with the byte-identical export URL and an
  aria-label naming the promise;
- the loaded state (built only after the reader taps the button) carries the
  byte-identical src, loading="lazy", a non-empty alt, and the caption only
  when the export records media_caption;
- records without images (or pids that are not exported promises) get '' and
  keep their text-only layout;
- URLs, captions, titles and alt text are HTML-escaped in both builders.
"""
import html
import json
import re
import subprocess
import unittest
from pathlib import Path

APP_JS = Path("docs/app.js")
DATA_JSON = Path("docs/data.json")
INDEX_HTML = Path("docs/index.html")
REPO_ROOT = Path(__file__).resolve().parent.parent
PURE_START = "/* SFPSTORY_PURE_START */"
PURE_END = "/* SFPSTORY_PURE_END */"

NODE_HARNESS = """
const fs = require('fs');
const src = fs.readFileSync('docs/app.js', 'utf8');
const start = src.indexOf('/* SFPSTORY_PURE_START */');
const end = src.indexOf('/* SFPSTORY_PURE_END */');
if (start < 0 || end < 0) {
  console.error('pure story block missing from docs/app.js');
  process.exit(2);
}
const window = {};
new Function('window', src.slice(start, end + '/* SFPSTORY_PURE_END */'.length) + '\\nwindow.SFPStory = SFPStory;')(window);
const data = JSON.parse(fs.readFileSync('docs/data.json', 'utf8'));
const pids = JSON.parse(fs.readFileSync('/tmp/sfpstory_pids.json', 'utf8'));
const byId = {};
for (const p of data.promises) byId[p.promise_id] = p;
const SFPStory = window.SFPStory;
const perCard = pids.map(pid => ({
  pid,
  inExport: !!byId[pid],
  exportUrl: byId[pid] ? (byId[pid].media_image_url || byId[pid].image_url || null) : null,
  exportCaption: byId[pid] ? (byId[pid].media_caption || null) : null,
  exportTitle: byId[pid] ? (byId[pid].title || null) : null,
  html: SFPStory.storyCardMediaHtml(byId[pid]),
  loaded: byId[pid] ? SFPStory.storyCardMediaLoadedHtml(
    byId[pid].media_image_url || byId[pid].image_url || '',
    byId[pid].media_caption || '',
    byId[pid].title || ''
  ) : null
}));
console.log(JSON.stringify({
  perCard,
  noRecord: SFPStory.storyCardMediaHtml(undefined),
  emptyRecord: SFPStory.storyCardMediaHtml({}),
  evil: SFPStory.storyCardMediaHtml({
    promise_id: 'PX',
    title: 'T "x"',
    image_url: 'https://example.com/x.jpg?a=1&b="onerror"',
    media_caption: 'cap"><script>alert(1)</script>'
  }),
  evilLoaded: SFPStory.storyCardMediaLoadedHtml(
    'https://example.com/x.jpg?a=1&b="onerror"', 'cap"><script>alert(1)</script>', 'T "x"'
  ),
  noCaptionLoaded: SFPStory.storyCardMediaLoadedHtml('https://example.com/y.jpg', '', 'T <b>itle</b>')
}));
"""


def static_card_pids():
    html = INDEX_HTML.read_text(encoding="utf-8")
    return re.findall(r'data-story-pid="([^"]+)"', html)


def run_harness(pids):
    Path("/tmp/sfpstory_pids.json").write_text(json.dumps(pids), encoding="utf-8")
    proc = subprocess.run(
        ["node", "-e", NODE_HARNESS], capture_output=True, text=True, timeout=60, cwd=REPO_ROOT
    )
    if proc.returncode != 0:
        raise AssertionError(f"node story harness failed: {proc.stderr.strip()}")
    return json.loads(proc.stdout)


class TestStoryCardMedia(unittest.TestCase):
    def setUp(self):
        self.assertTrue(DATA_JSON.exists(), "docs/data.json must exist")
        self.pids = static_card_pids()
        self.assertGreaterEqual(len(self.pids), 6, "index.html carries the featured story cards")
        self.out = run_harness(self.pids)
        self.by_card = {c["pid"]: c for c in self.out["perCard"]}

    def test_initial_markup_issues_no_third_party_request(self):
        # The opt-in boundary: before any tap, no card markup may reference a
        # remote resource. data-* attributes carry the URL as inert text.
        for card in self.out["perCard"]:
            self.assertNotIn("src=", card["html"], card["pid"])
            self.assertNotIn("srcset", card["html"], card["pid"])
            self.assertNotIn("<img", card["html"], card["pid"])
            self.assertNotIn("url(", card["html"], card["pid"])

    def test_every_exported_image_url_carried_byte_identical(self):
        for card in self.out["perCard"]:
            if card["exportUrl"]:
                self.assertIn(
                    f'data-img-url="{card["exportUrl"]}"', card["html"],
                    f'{card["pid"]}: carried URL must be the export URL, unrewritten',
                )
                self.assertIn(
                    f'src="{card["exportUrl"]}"', card["loaded"],
                    f'{card["pid"]}: loaded src must be the export URL, unrewritten',
                )

    def test_imaged_cards_render_opt_in_button_with_label(self):
        imaged = [c for c in self.out["perCard"] if c["exportUrl"]]
        self.assertGreaterEqual(len(imaged), 1, "at least one story card carries an export image")
        for card in imaged:
            self.assertIn('class="story-card-media"', card["html"])
            self.assertIn('class="btn-story-media"', card["html"], card["pid"])
            self.assertIn('type="button"', card["html"], card["pid"])
            label = re.search(r'aria-label="([^"]*)"', card["html"])
            self.assertIsNotNone(label, card["pid"])
            self.assertIn(html.escape(card["exportTitle"] or "", quote=True), label.group(1), card["pid"])

    def test_loaded_state_lazy_alt_and_caption_rules(self):
        for card in self.out["perCard"]:
            if not card["exportUrl"]:
                continue
            self.assertIn('loading="lazy"', card["loaded"], card["pid"])
            alt = re.search(r'alt="([^"]*)"', card["loaded"])
            self.assertIsNotNone(alt, card["pid"])
            self.assertTrue(alt.group(1).strip(), f'{card["pid"]}: alt must not be empty')
            has_cap = 'story-card-media-caption' in card["loaded"]
            self.assertEqual(bool(card["exportCaption"]), has_cap, card["pid"])
            if has_cap:
                self.assertIn(card["exportCaption"], card["loaded"])

    def test_imageless_and_unknown_cards_keep_text_only_layout(self):
        for card in self.out["perCard"]:
            if not card["exportUrl"]:
                self.assertEqual("", card["html"], f'{card["pid"]}: no export image -> no media block')
        self.assertEqual("", self.out["noRecord"])
        self.assertEqual("", self.out["emptyRecord"])

    def test_data_attributes_and_label_are_html_escaped(self):
        evil = self.out["evil"]
        self.assertNotIn("<script>", evil)
        self.assertNotIn('cap">', evil)
        self.assertIn("&quot;", evil)
        self.assertIn("&lt;script&gt;", evil)
        self.assertIn("https://example.com/x.jpg?a=1&amp;b=&quot;onerror&quot;", evil)

    def test_loaded_state_escapes_and_title_falls_back_into_alt(self):
        loaded = self.out["evilLoaded"]
        self.assertNotIn("<script>", loaded)
        self.assertIn("https://example.com/x.jpg?a=1&amp;b=&quot;onerror&quot;", loaded)
        html = self.out["noCaptionLoaded"]
        self.assertIn('alt="T &lt;b&gt;itle&lt;/b&gt;"', html)
        self.assertNotIn('story-card-media-caption', html)


if __name__ == "__main__":
    unittest.main()
