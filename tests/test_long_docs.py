"""Long-document segment selection (SF_PROMISES_LONG_DOCS=1 or SF_PROMISES_OUTCOME_RULES=1).

Without the flags the model sees the sentences of the first 10,000 characters,
so a commitment deeper in a long agenda is never offered. With either flag on,
chunks are chosen by word overlap with the discovery target and entity, up to
the same character budget, and every offered sentence is still an exact
substring of the saved bytes.
"""

import asyncio
import json
from datetime import date

import pytest

from src.extract import (
    LONG_DOCS_FLAG, SEGMENT_WINDOW, _source_segments, extract_with_model, long_docs_enabled,
)
from src.outcome_rules import FLAG as RULES_FLAG
from src.sources import archive_source, load_archived_text

FILLER = "The committee reviewed routine minutes and adopted the consent calendar. "
COMMITMENT = "The Port of San Francisco will open the Pier 70 ferry terminal by December 2027."
TARGET = "Pier 70 ferry terminal opening"


def long_text(position=60000):
    head = "Port Commission agenda, March 1, 2024.\n"
    text = head + FILLER * (position // len(FILLER)) + COMMITMENT + " " + FILLER * 200
    assert len(text) > 4 * SEGMENT_WINDOW and text.index(COMMITMENT) > SEGMENT_WINDOW
    return text


@pytest.fixture(autouse=True)
def flags_off(monkeypatch):
    monkeypatch.delenv(LONG_DOCS_FLAG, raising=False)
    monkeypatch.delenv(RULES_FLAG, raising=False)


def test_flag_reads_either_variable(monkeypatch):
    assert not long_docs_enabled()
    monkeypatch.setenv(LONG_DOCS_FLAG, "1")
    assert long_docs_enabled()
    monkeypatch.delenv(LONG_DOCS_FLAG)
    monkeypatch.setenv(RULES_FLAG, "1")
    assert long_docs_enabled()


def test_flag_off_sees_only_the_first_window():
    segments = _source_segments(long_text(), target=TARGET)
    assert COMMITMENT not in segments
    assert sum(len(s) for s in segments) <= SEGMENT_WINDOW


@pytest.mark.parametrize("flag", [LONG_DOCS_FLAG, RULES_FLAG])
def test_flag_on_selects_the_relevant_chunk_within_budget(monkeypatch, flag):
    monkeypatch.setenv(flag, "1")
    text = long_text()
    segments = _source_segments(text, target=TARGET)
    assert COMMITMENT in segments
    assert segments[0] == "Port Commission agenda, March 1, 2024."  # first chunk kept
    assert sum(len(s) + 1 for s in segments) <= SEGMENT_WINDOW
    assert all(segment in text for segment in segments)
    # Document order is preserved.
    positions = [text.index(segment) for segment in segments[:1]] + [text.index(COMMITMENT)]
    assert positions == sorted(positions)


def test_flag_on_short_text_or_no_target_is_unchanged(monkeypatch):
    monkeypatch.setenv(LONG_DOCS_FLAG, "1")
    short = "Mayor: We will build a library. " * 10
    assert _source_segments(short, target=TARGET) == _source_segments(short)
    text = long_text()
    monkeypatch.delenv(LONG_DOCS_FLAG)
    first_window = _source_segments(text)
    monkeypatch.setenv(LONG_DOCS_FLAG, "1")
    assert _source_segments(text) == first_window
    assert _source_segments(text, target="will the") == first_window  # only stopwords


def test_rank_puts_relevant_sentences_first(monkeypatch):
    monkeypatch.setenv(LONG_DOCS_FLAG, "1")
    ranked = _source_segments(long_text(), target=TARGET, rank=True)
    assert ranked[0] == COMMITMENT


def _extract(tmp_path, text, chosen):
    root = tmp_path / "sources"
    saved = archive_source(root, "P1", text.encode(), ".md")
    seen = {}

    async def complete(messages, **_kwargs):
        lines = messages[1]["content"].split("Numbered source sentences:\n", 1)[1].splitlines()
        seen["lines"] = lines
        index = next((i for i, line in enumerate(lines) if chosen in line), 0)
        return {"choices": [{"message": {"tool_calls": [{"function": {
            "name": "record_promise_evidence", "arguments": json.dumps({"candidates": [{
                "promise_id": "P1", "quote_segment_id": index, "speaker": None,
                "promised_date": "2024-03-01", "deadline": "2027-12-31"}]})}}]}}]}

    candidates = asyncio.run(extract_with_model(
        None, None, [], root=root, promise_id="P1", path=saved["path"], digest=saved["sha256"],
        source_url="https://sf.gov/port-agenda", target=TARGET, completion=complete,
        published=date(2024, 3, 1), entity="Port of San Francisco"))
    return candidates, seen["lines"], load_archived_text(root, "P1", saved["path"], saved["sha256"])


def test_extraction_finds_a_deep_commitment_with_the_flag_on(tmp_path, monkeypatch):
    monkeypatch.setenv(LONG_DOCS_FLAG, "1")
    candidates, lines, saved_text = _extract(tmp_path, long_text(), COMMITMENT)
    assert any(COMMITMENT in line for line in lines)
    assert candidates[0].promise_text == COMMITMENT
    assert candidates[0].promise_text in saved_text  # exact substring of saved bytes


def test_extraction_cannot_see_a_deep_commitment_with_the_flag_off(tmp_path):
    _candidates, lines, _ = _extract(tmp_path, long_text(), COMMITMENT)
    assert not any(COMMITMENT in line for line in lines)
