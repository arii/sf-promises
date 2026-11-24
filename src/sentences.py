"""Sentence boundaries in saved source text, shared by the site export and the audit.

`sentence_span` returns the raw span of the complete sentence(s) containing a
quote, so `text[start:end]` is an exact substring of the saved text and still
passes the verbatim-quote check. `display_sentence` is the same span with
whitespace collapsed, for display.
"""

_ABBREVIATIONS = frozenset({
    "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "sept", "oct", "nov", "dec",
    "st", "ave", "blvd", "dr", "mr", "mrs", "ms", "no", "inc", "co", "corp", "jr", "sr",
    "u.s", "e.g", "i.e", "vs", "approx",
})
SENTENCE_CAP = 420
_BULLETS = "-*•· "


def _is_sentence_end(text, i):
    """True when text[i] ends a sentence: .!? followed by whitespace or end,
    and not an abbreviation or a single initial."""
    if text[i] not in ".!?":
        return False
    if i + 1 < len(text) and not text[i + 1].isspace():
        return False
    if text[i] == ".":
        j = i
        while j > 0 and (text[j - 1].isalpha() or text[j - 1] == "."):
            j -= 1
        word = text[j:i].lower()
        if word in _ABBREVIATIONS or len(word) == 1:
            return False
    return True


def _is_line_break_boundary(text, i):
    """A single newline at i starts a new unit (heading or list line ending,
    next line capitalized) rather than wrapping a sentence."""
    if text[i] != "\n":
        return False
    nxt = text[i + 1:i + 2]
    prev = text[:i].rstrip(" \t")[-1:]
    return bool(nxt) and nxt.isupper() and prev not in (",", ";", ":", "-", "")


def sentence_span(text, quote):
    """(start, end) of the complete sentence(s) of ``text`` containing ``quote``.

    ``text[start:end]`` is raw (not whitespace-collapsed) with leading bullets
    and surrounding whitespace trimmed. Returns None if the quote is not found
    or the sentence, whitespace-collapsed, would exceed the cap."""
    if not isinstance(text, str) or not isinstance(quote, str) or not quote:
        return None
    start = text.find(quote)
    if start < 0:
        return None
    end = start + len(quote)
    left = start
    while left > 0:
        if text[left - 2:left] == "\n\n" or _is_sentence_end(text, left - 1) \
                or _is_line_break_boundary(text, left - 1):
            break
        left -= 1
    right = end
    if not (quote.rstrip()[-1:] in ".!?" and _is_sentence_end(text, start + len(quote.rstrip()) - 1)):
        while right < len(text):
            if text[right:right + 2] == "\n\n":
                break
            if _is_sentence_end(text, right):
                right += 1
                break
            right += 1
    while left < right and (text[left].isspace() or text[left] in _BULLETS):
        left += 1
    while right > left and text[right - 1].isspace():
        right -= 1
    if left >= right or len(" ".join(text[left:right].split())) > SENTENCE_CAP:
        return None
    return left, right


def display_sentence(text, quote):
    """The complete sentence(s) of saved ``text`` that contain ``quote``,
    whitespace-collapsed, for display. Returns None if the quote is not found
    or the sentence would exceed the cap. The evidence quote is unchanged;
    this only widens the displayed text to sentence boundaries in the same
    saved bytes (PDF line wrapping often cuts a segment mid-sentence)."""
    span = sentence_span(text, quote)
    if span is None:
        return None
    return " ".join(text[span[0]:span[1]].split())
