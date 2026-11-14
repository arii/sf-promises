"""UX state tests: data-load banner, zero-match empty state, drawer focus trap.

The banner copy, empty-state markup and focus-cycling math live in a marked
pure block of docs/app.js (SFPUX_PURE_START .. SFPUX_PURE_END) so the node
harness can exercise them without a DOM, mirroring the SFPDrawer pattern of
test_drawer_render.py. DOM wiring (hiding/showing, listeners) is checked as
static wiring in verify_demo.
"""
import json
import subprocess
import unittest
from pathlib import Path

APP_JS = Path("docs/app.js")
REPO_ROOT = Path(__file__).resolve().parent.parent
PURE_START = "/* SFPUX_PURE_START */"
PURE_END = "/* SFPUX_PURE_END */"

NODE_HARNESS = """
const fs = require('fs');
const src = fs.readFileSync('docs/app.js', 'utf8');
const start = src.indexOf('/* SFPUX_PURE_START */');
const end = src.indexOf('/* SFPUX_PURE_END */');
if (start < 0 || end < 0) {
  console.error('SFPUX pure block missing from docs/app.js');
  process.exit(2);
}
const window = {};
new Function('window', src.slice(start, end + '/* SFPUX_PURE_END */'.length) + '\\nwindow.SFPUX = SFPUX;')(window);
const X = window.SFPUX;

// Focus-cycling: 5 focusable nodes, indices 0..4.
const cycle = [];
for (let i = -1; i <= 5; i++) cycle.push(X.nextFocusableIndex(5, i, false));
const cycleBack = [];
for (let i = -1; i <= 5; i++) cycleBack.push(X.nextFocusableIndex(5, i, true));

console.log(JSON.stringify({
  banner: X.dataLoadErrorHtml(),
  noResults: X.noResultsHtml(),
  cycle,
  cycleBack,
  single: [X.nextFocusableIndex(1, 0, false), X.nextFocusableIndex(1, 0, true)],
  zero: X.nextFocusableIndex(0, 3, false)
}));
"""


def run_harness():
    proc = subprocess.run(
        ["node", "-e", NODE_HARNESS], capture_output=True, text=True, timeout=60, cwd=REPO_ROOT
    )
    if proc.returncode != 0:
        raise AssertionError(f"node ux harness failed: {proc.stderr.strip()}")
    return json.loads(proc.stdout)


class TestDataLoadBanner(unittest.TestCase):
    def setUp(self):
        self.out = run_harness()

    def test_banner_names_the_failure_and_what_still_works(self):
        banner = self.out["banner"]
        self.assertIn("could not be loaded", banner)
        # The statically-baked table remains readable; say what is dead.
        self.assertIn("statically published snapshot", banner)
        self.assertIn("refreshing the page", banner)

    def test_banner_is_not_empty_and_not_generic(self):
        self.assertTrue(self.out["banner"].strip())
        self.assertNotIn("Error", self.out["banner"].split(".")[0])


class TestNoResultsEmptyState(unittest.TestCase):
    def setUp(self):
        self.out = run_harness()

    def test_empty_state_states_emptiness_and_offers_clear_filters(self):
        html = self.out["noResults"]
        self.assertIn("No commitments match", html)
        self.assertIn("Clear filters", html)
        self.assertIn("btn-clear-filters-empty", html)

    def test_clear_filters_button_is_a_button_with_type(self):
        self.assertIn('<button type="button"', self.out["noResults"])


class TestDrawerFocusTrap(unittest.TestCase):
    def setUp(self):
        self.out = run_harness()

    def test_tab_wraps_forward_at_both_ends(self):
        cycle = self.out["cycle"]
        # index -1 (focus outside the set) -> first node; 4 (last) -> wraps to 0.
        self.assertEqual(cycle[0], 0)
        self.assertEqual(cycle[1], 1)
        self.assertEqual(cycle[5], 0, "Tab from the last focusable wraps to the first")
        self.assertEqual(cycle[6], 1)

    def test_shift_tab_wraps_backward(self):
        back = self.out["cycleBack"]
        # index -1 -> last node; 0 (first) -> wraps to the last; 4 -> 3.
        self.assertEqual(back[0], 4)
        self.assertEqual(back[1], 4, "Shift+Tab from the first focusable wraps to the last")
        self.assertEqual(back[5], 3)

    def test_degenerate_counts_do_not_throw_or_escape(self):
        # A single focusable keeps focus on itself in both directions; an
        # empty set is a pass-through, never an index error.
        self.assertEqual(self.out["single"], [0, 0])
        self.assertEqual(self.out["zero"], 3)


if __name__ == "__main__":
    unittest.main()
