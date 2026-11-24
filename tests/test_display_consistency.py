import importlib.util
import json
import re
import subprocess
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("demo_export", ROOT / "docs/export_data.py")
EXPORT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EXPORT)


class TestDisplayConsistency(unittest.TestCase):
    def test_quote_helpers_remove_only_matching_outer_pairs(self):
        cases = ['“A promise.”', '"A promise."', '““A promise.””', 'A "quoted" word.', '“Unfinished', '', '“A ‘nested’ word.”']
        expected = ['A promise.', 'A promise.', 'A promise.', 'A "quoted" word.', '“Unfinished', '', 'A ‘nested’ word.']
        self.assertEqual([EXPORT.clean_quote_text(x) for x in cases], expected)
        source = (ROOT / 'docs/app.js').read_text()
        helper = source[source.index('  function cleanQuoteText('):source.index('  function escapeHtml(')]
        script = helper + '\nconsole.log(JSON.stringify(' + json.dumps(cases) + '.map(cleanQuoteText)));'
        result = subprocess.run(['node', '-e', script], check=True, capture_output=True, text=True)
        self.assertEqual(json.loads(result.stdout), expected)

    def test_duplicate_role_is_omitted_without_changing_data(self):
        for role in ['Airport', ' airport ', 'AIRPORT', '']:
            row = EXPORT.generate_promise_row_html({'entity': 'Airport', 'role': role})
            self.assertNotIn('table-role-tag', row)
        row = EXPORT.generate_promise_row_html({'entity': 'Airport', 'role': 'City agency'})
        self.assertIn('City agency', row)

    def test_static_quotes_have_one_outer_pair(self):
        html = (ROOT / 'docs/index.html').read_text()
        self.assertNotIn('&ldquo;“', html)
        self.assertNotIn('”&rdquo;', html)

    def test_all_current_verdicts_have_visible_chart_buckets(self):
        source = (ROOT / 'docs/app.js').read_text()
        order = json.loads(re.search(r'const VERDICT_ORDER = (\[[^;]+\]);', source)[1].replace("'", '"'))
        counts = Counter(p['verdict'] for p in json.loads((ROOT / 'docs/data.json').read_text())['promises'])
        self.assertFalse(set(counts) - set(order))
        total = len(json.loads((ROOT / 'docs/data.json').read_text())['promises'])
        self.assertEqual(sum(counts[v] for v in order), total)
        self.assertIn('const verdictColor = VERDICT_COLORS;', source)
        self.assertIn("in_progress: 'var(--verdict-progress)'", source)
        self.assertIn("undecided: 'var(--verdict-undecided)'", source)

    def test_filter_and_legend_counts_match_snapshot(self):
        html = (ROOT / 'docs/index.html').read_text()
        counts = Counter(p['verdict'] for p in json.loads((ROOT / 'docs/data.json').read_text())['promises'])
        for verdict, count in counts.items():
            label = re.search(r'class="btn-seg-verdict[^\"]*" data-verdict="' + verdict + r'"[^>]*>([^<]+)', html)[1]
            self.assertTrue(label.endswith(f'({count})'), label)
            self.assertRegex(html, r'data-verdict="' + verdict + r'" style="width: [^\"]+" title="Filter [^\"]+ \(' + str(count) + r'\)"')


if __name__ == '__main__':
    unittest.main()
