from pathlib import Path


def test_entity_progress_and_static_map_legend_share_progress_token():
    app = Path('docs/app.js').read_text()
    css = Path('docs/display-consistency.css').read_text()
    assert 'width:${progPct}%;background:var(--verdict-progress);' in app
    assert 'width:${progPct}%;background:#F59E0B;' not in app
    assert '.pin-dot.in_progress { background: var(--verdict-progress); }' in css
