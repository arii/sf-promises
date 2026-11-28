"""Geometry check: on the mobile swipe layout the featured-stories row is as
tall as the active card, not the tallest card. Drives real scrolling and
resizes (mobile, desktop, landscape, round trip) in headless Chrome through the
DevTools protocol. Skipped when Chrome or Node 22+ is not installed."""
import functools
import http.server
import json
import os
import shutil
import subprocess
import threading
import unittest
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CHROME = shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")
NODE = shutil.which("node")

HARNESS = """<!doctype html><body style="margin:0"><iframe id="f" src="index.html" style="border:0;height:900px;width:390px"></iframe>
<script>
const sleep = ms => new Promise(r => setTimeout(r, ms));
// Poll until the row has settled on the active card (or give up after 3 s).
async function settle() {
  for (let n = 0; n < 60; n++) {
    const g = geo(); const i = activeIndex(g);
    if (g.swipe && Math.abs(g.row - (g.cards[i].offsetHeight + g.pad)) <= 2) return;
    await sleep(50);
  }
}
const f = document.getElementById('f');
const out = {errors: [], steps: []};
function geo() {
  const d = f.contentDocument, w = f.contentWindow;
  const c = d.getElementById('featured-stories-container');
  const cards = [...c.querySelectorAll('.story-card')];
  const cs = w.getComputedStyle(c);
  return {c, cards, swipe: cs.display === 'flex', pad: parseFloat(cs.paddingTop) + parseFloat(cs.paddingBottom),
          row: c.offsetHeight, inlineHeight: c.style.height, pager: d.querySelector('.carousel-controls-bar')};
}
function activeIndex(g) {
  let best = 0, diff = 1e9;
  g.cards.forEach((card, i) => { const x = Math.abs(card.offsetLeft - g.c.offsetLeft - g.c.scrollLeft); if (x < diff) { diff = x; best = i; } });
  return best;
}
async function width(px) { f.style.width = px + 'px'; await sleep(300); }
function checkSwipe(label, g) {
  const i = activeIndex(g);
  const want = g.cards[i].offsetHeight + g.pad;
  const gap = g.pager.getBoundingClientRect().top - g.cards[i].getBoundingClientRect().bottom;
  out.steps.push({label, i, row: g.row, want: Math.round(want), gap: Math.round(gap)});
  if (!g.swipe) out.errors.push(label + ': expected swipe layout');
  if (Math.abs(g.row - want) > 2) out.errors.push(label + ': row ' + g.row + ' != active card + padding ' + Math.round(want));
  if (gap > 40) out.errors.push(label + ': blank band ' + Math.round(gap) + 'px under active card');
}
window.runCheck = async () => {
  try {
    await sleep(1200);
    let g = geo();
    for (let i = 0; i < g.cards.length; i++) {          // real scroll, then let the scroll listener settle
      g.c.scrollLeft = g.cards[i].offsetLeft - g.c.offsetLeft; await sleep(100); await settle();
      checkSwipe('swipe ' + (i + 1), geo());
    }
    await width(1100); await sleep(300); g = geo();      // desktop: no inline sizing left behind
    out.steps.push({label: 'desktop', swipe: g.swipe, inlineHeight: g.inlineHeight});
    if (g.swipe || g.inlineHeight !== '') out.errors.push('desktop: inline height or flex layout leaked (' + g.inlineHeight + ')');
    await width(700); await settle(); g = geo(); checkSwipe('landscape 700 (resize from desktop)', g);
    g.c.scrollLeft = g.cards[3].offsetLeft - g.c.offsetLeft; await sleep(100); await settle();
    await width(390); await settle(); checkSwipe('back to 390, slide 4', geo());
    await width(1100); await sleep(300); await width(390); await settle(); checkSwipe('desktop round trip', geo());
  } catch (e) { out.errors.push('exception: ' + e); }
  return out;
};
</script></body>"""


class _Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        if self.path.startswith("/__harness.html"):
            body = HARNESS.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()


@pytest.mark.allow_network  # loopback only: local static server plus the Chrome DevTools socket
class TestCarouselHeight(unittest.TestCase):
    def test_row_follows_active_card_through_scroll_and_resize(self):
        if not (CHROME and NODE):
            message = "headless Chrome and Node 22+ are required"
            if os.environ.get("REQUIRE_BROWSER_TESTS"):
                self.fail(message + " (REQUIRE_BROWSER_TESTS is set, so this check must not be skipped)")
            self.skipTest(message)
        handler = functools.partial(_Handler, directory=str(ROOT / "docs"))
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            url = f"http://127.0.0.1:{server.server_address[1]}/__harness.html"
            proc = subprocess.run(
                [NODE, str(ROOT / "tests/carousel_height_driver.mjs"), CHROME, url],
                capture_output=True, text=True, timeout=120)
        finally:
            server.shutdown()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        result = json.loads(proc.stdout)
        summary = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary:
            rows = "\n".join(
                f"| {s['label']} | {s.get('row', '-')} | {s.get('want', '-')} | {s.get('gap', '-')} |"
                for s in result["steps"])
            with open(summary, "a", encoding="utf-8") as fh:
                fh.write("### Carousel geometry check (ran, not skipped)\n\n"
                         "| step | row px | active card + padding px | gap to pager px |\n"
                         "|---|---|---|---|\n" + rows + "\n")
        self.assertGreaterEqual(len(result["steps"]), 9, result)
        self.assertEqual(result["errors"], [], result)


if __name__ == "__main__":
    unittest.main()
