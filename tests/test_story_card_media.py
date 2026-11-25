"""Story-card media test: featured-story cards show the export's source media
inline (issue #44; owner decision 2026-11-25 removed the "Show source photo" step).

The story-card media HTML builders live in a marked pure block of docs/app.js
(SFPSTORY_PURE_START .. SFPSTORY_PURE_END). This test executes that block with
node over docs/data.json and asserts:

- a card whose record carries an image renders it inline: one <figure> with an
  <img> whose src is the byte-identical export URL, loading="lazy",
  referrerpolicy="no-referrer", a non-empty alt, the caption only when the
  export records media_caption, and NO button;
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

    def test_imaged_cards_render_photo_inline_without_button(self):
        imaged = [c for c in self.out["perCard"] if c["exportUrl"]]
        self.assertGreaterEqual(len(imaged), 1, "at least one story card carries an export image")
        for card in imaged:
            self.assertTrue(card["html"].startswith('<figure class="story-card-media">'), card["pid"])
            self.assertNotIn("<button", card["html"], card["pid"])
            self.assertNotIn("Show source photo", card["html"], card["pid"])
            self.assertIn(f'src="{card["exportUrl"]}"', card["html"],
                          f'{card["pid"]}: src must be the export URL, unrewritten')
            self.assertEqual(card["html"].count("<img"), 1, card["pid"])

    def test_inline_photo_lazy_alt_referrer_and_caption_rules(self):
        for card in self.out["perCard"]:
            if not card["exportUrl"]:
                continue
            self.assertIn('loading="lazy"', card["html"], card["pid"])
            self.assertIn('referrerpolicy="no-referrer"', card["html"], card["pid"])
            alt = re.search(r'alt="([^"]*)"', card["html"])
            self.assertIsNotNone(alt, card["pid"])
            self.assertTrue(alt.group(1).strip(), f'{card["pid"]}: alt must not be empty')
            has_cap = 'story-card-media-caption' in card["html"]
            self.assertEqual(bool(card["exportCaption"]), has_cap, card["pid"])

    def test_no_button_remains_anywhere(self):
        src = APP_JS.read_text(encoding="utf-8")
        self.assertNotIn("Show source photo", src)
        self.assertNotIn("btn-story-media", src)

    def test_imageless_and_unknown_cards_keep_text_only_layout(self):
        for card in self.out["perCard"]:
            if not card["exportUrl"]:
                self.assertEqual("", card["html"], f'{card["pid"]}: no export image -> no media block')
        self.assertEqual("", self.out["noRecord"])
        self.assertEqual("", self.out["emptyRecord"])

    def test_urls_captions_and_alt_are_html_escaped(self):
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
