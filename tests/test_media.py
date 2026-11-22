"""Media pipeline tests (issues #82, #83). Offline: httpx.MockTransport, no sockets."""
import io
import json
from pathlib import Path

import httpx
import pytest
from PIL import Image

from src import media

ROOT = Path(__file__).resolve().parent.parent


def _png(color=(200, 30, 30), size=(1000, 600)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, "PNG")
    return buf.getvalue()


IMG = _png()
PAGE = '<html><head><meta property="og:image" content="/img/a.png"><meta name="twitter:image" content="https://www.sf.gov/img/a.png"></head></html>'


def _client():
    def handler(request: httpx.Request):
        if request.url.host == "commons.wikimedia.org":
            return httpx.Response(200, json={"query": {"pages": {
                "1": {"index": 1, "imageinfo": [{
                    "thumburl": "https://upload.wikimedia.org/x/160px-a.png",
                    "descriptionurl": "https://commons.wikimedia.org/wiki/File:A.png",
                    "extmetadata": {"LicenseShortName": {"value": "CC BY-SA 4.0"},
                                    "Artist": {"value": "<a>Jane Doe</a>"},
                                    "LicenseUrl": {"value": "https://creativecommons.org/licenses/by-sa/4.0"}}}]},
                "2": {"index": 2, "imageinfo": [{"thumburl": "https://upload.wikimedia.org/x/b.png",
                      "extmetadata": {"LicenseShortName": {"value": "Fair use"}}}]}}}})
        return httpx.Response(200, content=IMG)
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_extract_image_urls_absolute_and_deduped():
    urls = media.extract_image_urls(PAGE, "https://www.sf.gov/news/x")
    assert urls == ["https://www.sf.gov/img/a.png"]


def test_stage_promise_candidates_pending_only(tmp_path):
    (tmp_path / "s.md").write_text(PAGE)
    promises = [
        {"promise_id": "P02", "source_file_path": "s.md", "source_url": "https://www.sf.gov/news/x"},
        {"promise_id": "P05", "source_file_path": "s.md", "source_url": "https://www.sf.gov/news/x"},
        {"promise_id": "PXX", "source_file_path": "missing.md", "source_url": "https://www.sf.gov/"},
    ]
    out = media.stage_promise_candidates(promises, tmp_path, _client(), tmp_path / "saved")
    assert [c["promise_id"] for c in out] == ["P02"]
    c = out[0]
    assert c["status"] == "pending" and c["license_guess"] == "gov"
    assert c["sha256"] == media.sha256_hex(IMG)
    assert (tmp_path / "saved" / c["sha256"]).read_bytes() == IMG


def test_non_allowlisted_host_refused():
    with pytest.raises(media.MediaError):
        media.fetch_bytes(_client(), "https://evil.example.com/a.png")
    with pytest.raises(media.MediaError):
        media.fetch_bytes(_client(), "http://www.sf.gov/a.png")


def test_write_candidates_preserves_review(tmp_path):
    path = tmp_path / "staging" / "media_candidates.json"
    base = {"kind": "promise", "promise_id": "P02", "image_url": "https://www.sf.gov/a.png", "status": "pending"}
    media.write_candidates(path, [base])
    reviewed = json.loads(path.read_text())
    reviewed[0].update(status="approved", license="Public domain")
    path.write_text(json.dumps(reviewed))
    media.write_candidates(path, [base])
    assert json.loads(path.read_text())[0]["status"] == "approved"


def _approved(**kw):
    c = {"kind": "promise", "promise_id": "P02", "image_url": "https://www.sf.gov/a.png",
         "sha256": media.sha256_hex(IMG), "status": "approved", "license": "Public domain (US city government work)",
         "license_url": "https://www.sf.gov/terms", "credit": "SF.gov"}
    c.update(kw)
    return c


def test_apply_writes_files_and_manifest(tmp_path):
    written = media.apply_candidates([_approved()], _client(), tmp_path)
    assert sorted(written) == ["P02-320.webp", "P02-800.webp"]
    m = json.loads((tmp_path / "manifest.json").read_text())
    e = m["images"][0]
    assert e["sha256"] == media.sha256_hex(IMG) and e["license"] and e["original_url"]
    assert Image.open(tmp_path / "P02-320.webp").width == 320


@pytest.mark.parametrize("change", [
    {"license": ""},
    {"license_url": " "},
    {"credit": ""},
    {"promise_id": "P05"},
    {"image_url": "https://assets.sfstandard.com/a.png"},
    {"sha256": "0" * 64},
])
def test_apply_refuses_ungated(tmp_path, change):
    with pytest.raises(media.MediaError):
        media.apply_candidates([_approved(**change)], _client(), tmp_path)
    assert not list(tmp_path.glob("*.webp")) and not (tmp_path / "manifest.json").exists()


def test_unapproved_never_enters_media(tmp_path):
    assert media.apply_candidates([_approved(status="pending")], _client(), tmp_path) == []
    assert not list(tmp_path.glob("*.webp"))


def test_entity_lookup_requires_open_license_and_stays_pending():
    out = media.stage_entity_candidates(["Daniel Lurie"], _client())
    assert len(out) == 1
    c = out[0]
    assert c["status"] == "pending" and c["suggested_license"] == "CC BY-SA 4.0"
    assert c["suggested_credit"] == "Jane Doe"
    assert media.guess_license("https://upload.wikimedia.org/a.png") == "CC"


def test_entity_apply_and_export_fields(tmp_path):
    cand = {"kind": "entity", "entity_name": "Daniel Lurie", "image_url": "https://upload.wikimedia.org/x/a.png",
            "status": "approved", "license": "CC BY-SA 4.0", "license_url": "https://creativecommons.org/licenses/by-sa/4.0",
            "credit": "Jane Doe"}
    media.apply_candidates([cand], _client(), tmp_path)
    manifest = media.load_manifest(tmp_path / "manifest.json")
    assert (tmp_path / "entities" / "daniel-lurie-160.webp").exists()
    promises = [{"promise_id": "P01", "entity_canonical_name": "Daniel Lurie"}, {"promise_id": "P02", "entity_canonical_name": "X"}]
    media.apply_manifest_fields(promises, manifest)
    assert promises[0]["entity_image_path"] == "media/entities/daniel-lurie-160.webp"
    assert promises[0]["entity_image_credit"] == "Jane Doe / CC BY-SA 4.0"
    assert "entity_image_path" not in promises[1] and "media_path" not in promises[1]


def test_export_media_paths_exist_and_in_manifest():
    data = json.loads((ROOT / "docs" / "data.json").read_text())["promises"]
    manifest = media.load_manifest(ROOT / "docs" / "media" / "manifest.json")
    ids = {e["promise_id"] for e in manifest["images"]}
    for e in manifest["images"]:
        assert e["license"].strip() and e["sha256"] and e["credit"].strip()
    for p in data:
        if p.get("media_path"):
            assert (ROOT / "docs" / p["media_path"]).is_file()
            assert (ROOT / "docs" / p["media_thumb_path"]).is_file()
            assert p["promise_id"] in ids and p["media_license"]
            assert p["promise_id"] not in media.NEVER_REHOST_IDS
        if p.get("entity_image_path"):
            assert (ROOT / "docs" / p["entity_image_path"]).is_file()
    assert media.media_dir_bytes(ROOT / "docs" / "media") < 2 * 1024 * 1024 if (ROOT / "docs" / "media").exists() else True


def test_media_module_never_touches_verdict_tables():
    src = (ROOT / "src" / "media.py").read_text() + (ROOT / "scripts" / "fetch_media.py").read_text()
    for token in ("sqlite3", "INSERT", "UPDATE ", "DELETE ", "src.database"):
        assert token not in src
