import hashlib
import json
import os
import tempfile
import pytest

from src.checks import (
    check_date,
    check_domain,
    check_evidence_type,
    check_hash,
    check_promise_id,
    check_quote,
    check_speaker,
)
from src.arbitrator import decide_verdict


def test_domain_pass():
    passed, reason = check_domain("https://www.sf.gov/news")
    assert passed is True
    assert reason == "pass"


def test_domain_fail():
    passed, reason = check_domain("https://example.com/news")
    assert passed is False
    assert reason == "unlisted source domain"


def test_domain_seed_hosts_pass():
    for url in (
        "https://edition.pagesuite.com/tribune/article_popover.aspx?guid=x",
        "https://src.senate.ca.gov/governor-gavin-newsoms-top-15-worst-flip-flops-and-fails",
        "https://investor.pgecorp.com/news-events/press-releases/press-release-details/2023/x",
        "https://en.wikipedia.org/wiki/Dead_%26_Company_Summer_Tour_2023",
    ):
        passed, reason = check_domain(url)
        assert passed is True, url
        assert reason == "pass"


def test_domain_n07_blog_still_fails():
    passed, reason = check_domain("https://random-sf-blog.example.com/post")
    assert passed is False
    assert reason == "unlisted source domain"


def test_domain_parent_hosts_not_allowlisted():
    for url in (
        "https://www.pagesuite.com/x",
        "https://www.wikipedia.org/wiki/x",
        "https://www.senate.ca.gov/x",
        "https://www.pgecorp.com/x",
    ):
        passed, reason = check_domain(url)
        assert passed is False, url
        assert reason == "unlisted source domain"


def test_hash_pass():
    with open("mocks/source_P05.md", "rb") as f:
        real_hash = hashlib.sha256(f.read()).hexdigest()
    passed, reason = check_hash("mocks/source_P05.md", real_hash)
    assert passed is True
    assert reason == "pass"


def test_hash_fail():
    with tempfile.NamedTemporaryFile("wb", delete=False) as tmp:
        tmp.write(b"original content")
        tmp_path = tmp.name

    try:
        real_hash = hashlib.sha256(b"original content").hexdigest()
        # Change one byte
        with open(tmp_path, "wb") as f:
            f.write(b"modified content")
        passed, reason = check_hash(tmp_path, real_hash)
        assert passed is False
        assert reason == "hash mismatch"
    finally:
        os.remove(tmp_path)


def test_quote_pass():
    with open("mocks/source_P05.md", "r") as f:
        source_text = f.read()
    quote = "1,500 new shelter beds within six months"
    passed, reason = check_quote(quote, source_text)
    assert passed is True
    assert reason == "pass"


def test_quote_fail():
    with open("mocks/source_P05.md", "r") as f:
        source_text = f.read()
    quote = "2,000 new shelter beds within six months"
    passed, reason = check_quote(quote, source_text)
    assert passed is False
    assert reason == "quote none"


def test_hash_pass_p02():
    with open("mocks/source_P02.md", "rb") as f:
        real_hash = hashlib.sha256(f.read()).hexdigest()
    passed, reason = check_hash("mocks/source_P02.md", real_hash)
    assert passed is True
    assert reason == "pass"


def test_quote_pass_p02():
    with open("mocks/source_P02.md", "r") as f:
        source_text = f.read()
    quote = "24/7 police-friendly stabilization center at 822 Geary Street"
    passed, reason = check_quote(quote, source_text)
    assert passed is True
    assert reason == "pass"


def test_broken_none_p02():
    with open("mocks/kept_P02.json") as f:
        kept_data = json.load(f)
    with open("mocks/broken_P02.json") as f:
        broken_data = json.load(f)

    assert len(broken_data["claims"]) == 0
    assert len(kept_data["claims"]) > 0

    verdict, reason = decide_verdict(
        kept_claims=kept_data["claims"],
        broken_claims=broken_data["claims"],
    )
    assert verdict == "kept"


def test_speaker_pass():
    passed, reason = check_speaker("Daniel Lurie", ["Daniel Lurie", "Rafael Mandelman"])
    assert passed is True
    assert reason == "pass"


def test_speaker_fail():
    passed, reason = check_speaker("Jane Doe", ["Daniel Lurie", "Rafael Mandelman"])
    assert passed is False
    assert reason == "speaker not in roll call"


def test_interim_progress_in_progress():
    verdict, _ = decide_verdict(
        kept_claims=[{"evidence_type": "news_report"}],
        broken_claims=[],
        interim_progress=True,
    )
    assert verdict == "in_progress"


def test_interim_progress_yields_to_broken():
    verdict, _ = decide_verdict(
        kept_claims=[{"evidence_type": "news_report"}],
        broken_claims=[{"evidence_type": "count"}],
        interim_progress=True,
    )
    assert verdict == "broken"


def test_interim_progress_yields_to_kept():
    verdict, _ = decide_verdict(
        kept_claims=[{"evidence_type": "count"}],
        broken_claims=[],
        interim_progress=True,
    )
    assert verdict == "kept"


def test_date_pass():
    passed, reason = check_date("2025-04-28", "2025-01-07")
    assert passed is True
    assert reason == "pass"


def test_date_pass_month_precision():
    passed, reason = check_date("2025-04", "2025-01-07")
    assert passed is True
    assert reason == "pass"


def test_date_pass_year_precision():
    passed, reason = check_date("2026", "2018-11-06")
    assert passed is True
    assert reason == "pass"


def test_date_fail_predates_promise():
    passed, reason = check_date("2024-06-01", "2025-01-07")
    assert passed is False
    assert reason == "date mismatch with source"


def test_date_fail_unparseable():
    passed, reason = check_date("sometime last spring", "2025-01-07")
    assert passed is False
    assert reason == "date mismatch with source"


def test_date_fail_future():
    passed, reason = check_date("2099-01-01", "2025-01-07")
    assert passed is False
    assert reason == "date mismatch with source"


def test_promise_id_pass():
    passed, reason = check_promise_id("P05", "P05")
    assert passed is True
    assert reason == "pass"


def test_promise_id_fail_cross_promise():
    passed, reason = check_promise_id("P06", "P05")
    assert passed is False
    assert reason == "evidence does not match promise_id"


def test_promise_id_fail_missing():
    passed, reason = check_promise_id("", "P05")
    assert passed is False
    assert reason == "evidence does not match promise_id"


def test_evidence_type_pass():
    passed, reason = check_evidence_type("opening")
    assert passed is True
    assert reason == "pass"


def test_evidence_type_fail():
    passed, reason = check_evidence_type("rumor")
    assert passed is False
    assert reason == "evidence type not allowed"
