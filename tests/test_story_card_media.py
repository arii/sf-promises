"""Story-card media test: featured-story cards surface exactly the media the export carries (issue #44).

The story-card media HTML builder lives in a marked pure block of docs/app.js
(SFPSTORY_PURE_START .. SFPSTORY_PURE_END). This test executes that block with
node over docs/data.json and asserts:

- every static story card in docs/index.html whose record carries an image in
  the export gets a media block with that exact URL, a non-empty alt, and
  loading="lazy";
- cards whose record carries no image (or whose pid is not an exported
  promise) get '' and keep their text-only layout;
- the caption renders only when the export records media_caption, and both
  caption and alt are HTML-escaped;
- no URL is rewritten: the rendered src is byte-identical to the export value.
"""
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
  html: SFPStory.storyCardMediaHtml(byId[pid])
}));
console.log(JSON.stringify({
  perCard,
  noRecord: SFPStory.storyCardMediaHtml(undefined),
  emptyRecord: SFPStory.storyCardMediaHtml({}),
  evil: SFPStory.storyCardMediaHtml({
    promise_id: 'PX',
    image_url: 'https://example.com/x.jpg?a=1&b="onerror"',
    media_caption: 'cap"><script>alert(1)</script>'
  }),
  noCaption: SFPStory.storyCardMediaHtml({
    promise_id: 'PY',
    title: 'T <b>itle</b>',
    image_url: 'https://example.com/y.jpg'
  })
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

    def test_every_exported_image_url_renders_byte_identical(self):
        for card in self.out["perCard"]:
            if card["exportUrl"]:
                self.assertIn(
                    f'src="{card["exportUrl"]}"', card["html"],
                    f'{card["pid"]}: rendered src must be the export URL, unrewritten',
                )

    def test_imaged_cards_render_media_with_lazy_alt(self):
        imaged = [c for c in self.out["perCard"] if c["exportUrl"]]
        self.assertGreaterEqual(len(imaged), 1, "at least one story card carries an export image")
        for card in imaged:
            self.assertIn('class="story-card-media"', card["html"])
            self.assertIn('loading="lazy"', card["html"], card["pid"])
            alt = re.search(r'alt="([^"]*)"', card["html"])
            self.assertIsNotNone(alt, card["pid"])
            self.assertTrue(alt.group(1).strip(), f'{card["pid"]}: alt must not be empty')

    def test_imageless_and_unknown_cards_keep_text_only_layout(self):
        for card in self.out["perCard"]:
            if not card["exportUrl"]:
                self.assertEqual("", card["html"], f'{card["pid"]}: no export image -> no media block')
        self.assertEqual("", self.out["noRecord"])
        self.assertEqual("", self.out["emptyRecord"])

    def test_caption_only_when_exported(self):
        for card in self.out["perCard"]:
            has_cap = 'story-card-media-caption' in card["html"]
            self.assertEqual(bool(card["exportCaption"] and card["exportUrl"]), has_cap, card["pid"])
            if has_cap:
                self.assertIn(card["exportCaption"], card["html"])

    def test_caption_and_alt_are_html_escaped(self):
        evil = self.out["evil"]
        self.assertNotIn("<script>", evil)
        self.assertNotIn('cap">', evil)
        self.assertIn("&quot;", evil)
        self.assertIn("&lt;script&gt;", evil)
        # URL query is escaped too (ampersands and quotes cannot break the tag).
        self.assertIn("https://example.com/x.jpg?a=1&amp;b=&quot;onerror&quot;", evil)

    def test_title_falls_back_into_alt_escaped(self):
        html = self.out["noCaption"]
        self.assertIn('alt="T &lt;b&gt;itle&lt;/b&gt;"', html)
        self.assertNotIn('story-card-media-caption', html)


if __name__ == "__main__":
    unittest.main()
