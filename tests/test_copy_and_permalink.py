"""Frontend copy/IA (#66, #67): renamed labels, hero, legend, permalink."""
from pathlib import Path
import re
import unittest

HTML = Path("docs/index.html").read_text()
JS = Path("docs/app.js").read_text()
CSS = Path("docs/styles.css").read_text()


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

    def test_watch_has_no_intro_or_stage_descriptions(self):
        # #100: Watch is a compact six-stage timeline; no intro paragraph, no per-stage descriptions.
        self.assertNotIn('id="stage-explainers"', HTML)
        self.assertNotIn("Follow a public commitment from its original source", HTML)
        for n, stage in enumerate(("Fetch", "Extract", "Gate", "Argue", "Decide", "Publish"), start=1):
            self.assertIn(f'data-stage="{n}">{stage}</span>', HTML)

    def test_story_cards_have_no_empty_gaps_and_show_full_outcome(self):
        # Featured cards flow in masonry columns (no empty grid cells), photos are a compact crop,
        # and the "what happened" outcome shows up to 4 lines.
        grid = re.search(r"\.featured-stories-grid \{(.*?)\}", CSS, re.S).group(1)
        self.assertIn("columns: 320px 3", grid)
        card = re.search(r"\.story-card \{(.*?)\}", CSS, re.S).group(1)
        self.assertIn("break-inside: avoid", card)
        self.assertNotIn("space-between", card)
        img = re.search(r"\.story-card-media img \{(.*?)\}", CSS, re.S).group(1)
        self.assertIn("aspect-ratio: 5 / 2", img)
        outcome = re.search(r"\.story-outcome-text \{(.*?)\}", CSS, re.S).group(1)
        self.assertIn("-webkit-line-clamp: 4", outcome)

    def test_hash_permalink_opens_drawer(self):
        self.assertIn("#promise-", JS)
        self.assertIn("openPermalinkDrawer", JS)
        self.assertIn("addEventListener('hashchange', openPermalinkDrawer)", JS)


if __name__ == "__main__":
    unittest.main()
