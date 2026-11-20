from pathlib import Path


def test_hidden_table_state_overrides_mobile_display_mode():
    css = Path('docs/display-consistency.css').read_text()
    assert '#promises-table-container.hidden { display: none !important; }' in css
    html = Path('docs/index.html').read_text()
    assert html.index('styles.css?') < html.index('display-consistency.css?')
