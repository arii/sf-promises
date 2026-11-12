import hashlib

from src.candidate_worker import check_request


def test_worker_checks_source_quote_hash_and_dates(tmp_path):
    directory = tmp_path / "job"
    directory.mkdir()
    text = "San Francisco will build the library by 2022."
    digest = hashlib.sha256(text.encode()).hexdigest()
    source = directory / (digest + ".md")
    source.write_text(text)
    request = {
        "sources": [{"sha256": digest, "quote": text, "url": "https://sf.gov/a",
                     "tier": "TIER1_GOV"}],
        "origin": {"quote": text, "promised": "2020-01-01",
                   "published": "2020-01-01", "deadline": "2022-12-31"},
    }
    assert check_request(request, tmp_path) == {"failures": []}
    request["sources"][0]["quote"] = "fabricated"
    assert "quote_not_found" in check_request(request, tmp_path)["failures"]
    request["sources"][0]["quote"] = text
    request["origin"]["promised"] = "2020-01-02"
    assert "promise_after_publication" in check_request(request, tmp_path)["failures"]
    source.write_text("changed")
    assert "source_hash_mismatch" in check_request(request, tmp_path)["failures"]
