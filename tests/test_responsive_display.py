import unittest
import subprocess
import re
import json
from pathlib import Path


class TestResponsiveDisplay(unittest.TestCase):
    def test_mobile_header_has_its_own_verdict_row(self):
        css = Path('docs/display-consistency.css').read_text()
        self.assertIn('grid-template-areas: "speaker" "verdict" "quote" "timeline"', css)
        self.assertIn('grid-template-columns: minmax(0, 1fr)', css)

    def test_desktop_dates_can_wrap(self):
        css = Path('docs/display-consistency.css').read_text()
        self.assertIn('.timeline-val { white-space: normal; overflow-wrap: anywhere; }', css)

    def test_mobile_chart_uses_mobile_coordinate_system(self):
        js = Path('docs/app.js').read_text()
        self.assertIn("window.matchMedia('(max-width: 600px)').matches", js)
        self.assertIn('const W = compact ? 360 : 760;', js)

    def test_mobile_tab_label_does_not_wrap_and_axis_ticks_legible(self):
        css = Path('docs/styles.css').read_text()
        block = css[css.index('.tab-nav-btn {'):css.index('.tab-nav-btn.active')]
        self.assertIn('white-space: nowrap', block)
        js = Path('docs/app.js').read_text()
        self.assertIn('font-size="${compact ? 11 : 9}" fill="var(--muted)" font-family="monospace">${t}</text>', js)

    def test_exact_address_does_not_repeat_scope(self):
        js = Path('docs/app.js').read_text()
        self.assertIn('scopeRaw.toLowerCase() === geoType.toLowerCase() ? geoType', js)

    def test_rendered_mobile_timeline_ticks_do_not_collide(self):
        source = Path('docs/app.js').read_text()
        pure = source[source.index('/* SFPVIZ_PURE_START */'):source.index('/* SFPVIZ_PURE_END */')]
        chart = source[source.index('  function renderTimelineChart('):source.index('  function renderVisualizations(')]
        script = "const fs = require('fs'); const wrap = {}; const window = {matchMedia:()=>({matches:true})}; const document = {getElementById:()=>wrap}; const VERDICT_COLORS = {}; const formatVerdictLabel = x=>x;" + pure + chart + "renderTimelineChart(JSON.parse(fs.readFileSync('docs/data.json')).promises);console.log(wrap.innerHTML);"
        html = subprocess.run(['node', '-e', script], check=True, capture_output=True, text=True).stdout
        self.assertIn('viewBox="0 0 360 280"', html)
        ticks = re.findall(r'<text x="([0-9.]+)" y="272"[^>]*>([0-9]{4})</text>', html)
        self.assertGreaterEqual(len(ticks), 3)
        self.assertEqual(ticks[0][1], '2002')
        self.assertEqual(ticks[-1][1], '2026')
        for left, right in zip(ticks, ticks[1:]):
            self.assertGreaterEqual(float(right[0]) - float(left[0]), 39.9)

    def test_drawer_pin_label_keeps_distinct_scope_only(self):
        source = Path('docs/app.js').read_text()
        start = source.index('    const scopeRaw =')
        end = source.index('    if (subtitleEl)', start)
        helper = source[start:end]
        cases = [{'geographic_scope': 'exact_address', 'is_centroid': False}, {'geographic_scope': 'citywide', 'is_centroid': True}]
        script = 'const cases = ' + json.dumps(cases) + ';console.log(JSON.stringify(cases.map(p=>{' + helper + ';return geoPinLabel;})));'
        labels = json.loads(subprocess.run(['node', '-e', script], check=True, capture_output=True, text=True).stdout)
        self.assertEqual(labels, ['Exact address', 'Display centroid (citywide)'])
