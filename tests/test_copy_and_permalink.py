"""Frontend copy/IA (#66, #67): renamed labels, hero, legend, permalink."""
from pathlib import Path
import re
import unittest

HTML = Path("docs/index.html").read_text()
JS = Path("docs/app.js").read_text()


def visible(html):
    html = re.sub(r"<!--.*?-->", "", html, flags=re.S)
    return re.sub(r"<script.*?</script>", "", html, flags=re.S)


class TestCopy(unittest.TestCase):
    def test_old_labels_absent_from_visible_ui(self):
        text = visible(HTML)
        for old in ("Quality Audit", "Quarantine Registry", "Operational Evidence-Review Queue"):
            self.assertNotIn(old, text)

    def test_new_labels_present(self):
        for new in ("Data Quality", "Rejected &amp; Test Records", "Verification Activity", "Commitment Registry"):
            self.assertIn(new, HTML)

    def test_hero_scope_legend_methodology(self):
        self.assertIn("Did they do what they said they would?", HTML)
        for word in ("officials", "agencies", "businesses", "institutions"):
            self.assertIn(word, HTML)
        self.assertIn('id="hero-scope"', HTML)
        self.assertIn('id="verdict-legend"', HTML)
        for v in ("Kept", "Broken", "In Progress", "Undecided", "Reversed"):
            self.assertIn(f"<dt>{v}</dt>", HTML)
        self.assertIn('id="methodology"', HTML)

    def test_stage_explainers(self):
        block = HTML[HTML.index('id="stage-explainers"'):]
        for stage in ("Fetch", "Extract", "Gate", "Argue", "Decide", "Publish"):
            self.assertIn(f"<dt>{stage}</dt>", block.split("</dl>")[0])

    def test_hash_permalink_opens_drawer(self):
        self.assertIn("#promise-", JS)
        self.assertIn("openPermalinkDrawer", JS)
        self.assertIn("addEventListener('hashchange', openPermalinkDrawer)", JS)


if __name__ == "__main__":
    unittest.main()
