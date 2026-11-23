"""Presentation-only media pipeline (issues #82, #83).

Images are never evidence: nothing here reads or writes `promises`,
`verdicts`, `verifications` or `quarantined`. The only outputs are
`staging/media_candidates.json` (review file), files under `docs/media/` and
`docs/media/manifest.json`.

Network access follows the Fetcher lane rules: allowlisted hosts only, a size
cap and timeout per fetch, saved bytes plus SHA-256. Callers pass the httpx
client so tests can inject a mock transport (the test suite blocks sockets).
"""

from __future__ import annotations

import hashlib
import io
import json
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit

from src.allowlist import entry_for_host

REPO_ROOT = Path(__file__).resolve().parent.parent
MEDIA_DIR = REPO_ROOT / "docs" / "media"
MANIFEST_PATH = MEDIA_DIR / "manifest.json"
ENTITY_DIR = MEDIA_DIR / "entities"
MAX_MEDIA_BYTES = 2 * 1024 * 1024 - 1
MAX_FETCH_BYTES = 8 * 1024 * 1024
FETCH_TIMEOUT = 20.0

# Commons is reviewed for this job only; config/allowlist.json is not edited.
EXTRA_FETCH_HOSTS = frozenset({"commons.wikimedia.org", "upload.wikimedia.org", "thumb.wikimedia.org"})
GOV_HOSTS = frozenset({"sf.gov", "flysfo.com", "sfmta.com", "sfrecpark.org"})
# Issue #82: these keep the opt-in hotlink and are never rehosted.
NEVER_REHOST_IDS = frozenset({"P05", "P04", "P10", "P06", "P07", "P83"})
NEVER_REHOST_HOSTS = (
    "sfstandard.com", "abcotvs.com", "sfexaminer.com", "townnews.com",
    "latimes.com", "brightspotcdn.com", "gettyimages.com", "hdnux.com",
    "sfchronicle.com",
)
# Public domain, CC0, CC BY and CC BY-SA only. NC/ND variants do not match.
OPEN_LICENSE = re.compile(r"^(public domain|pd([ -]|$)|cc0|cc[ -]by(-sa)?[ -]\d)", re.I)
USER_AGENT = "sf-promises-media/1.0 (https://github.com/arii/sf-promises; accountability tracker, contact via repo issues)"
ENTITY_CONFIG = REPO_ROOT / "config" / "media_entities.json"


class MediaError(Exception):
    pass


def _host(url: str) -> str:
    return (urlsplit(url).hostname or "").lower()


def _under(host: str, domain: str) -> bool:
    return host == domain or host.endswith("." + domain)


def host_allowed(url: str) -> bool:
    if urlsplit(url).scheme != "https":
        return False
    host = _host(url)
    return host in EXTRA_FETCH_HOSTS or entry_for_host(host) is not None


def is_never_rehost(promise_id: str | None, url: str) -> bool:
    host = _host(url)
    return promise_id in NEVER_REHOST_IDS or any(_under(host, d) for d in NEVER_REHOST_HOSTS)


def guess_license(url: str) -> str:
    host = _host(url)
    if any(_under(host, d) for d in GOV_HOSTS):
        return "gov"
    if _under(host, "wikimedia.org"):
        return "CC"
    return "unknown"


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def fetch_bytes(client, url: str) -> bytes:
    """Bounded fetch of an allowlisted https URL; returns the response bytes."""
    if not host_allowed(url):
        raise MediaError(f"host not allowlisted: {url}")
    response = client.get(url, timeout=FETCH_TIMEOUT, follow_redirects=False)
    if response.status_code != 200:
        raise MediaError(f"fetch failed ({response.status_code}): {url}")
    data = response.content
    if len(data) > MAX_FETCH_BYTES:
        raise MediaError(f"response too large: {url}")
    return data


class _MetaParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images: list[tuple[str, str]] = []

    def handle_starttag(self, tag, attrs):
        if tag != "meta":
            return
        a = {k.lower(): (v or "") for k, v in attrs}
        key = (a.get("property") or a.get("name") or "").lower()
        if key in ("og:image", "og:image:url", "og:image:secure_url", "twitter:image", "twitter:image:src") and a.get("content"):
            self.images.append((key, a["content"].strip()))


def extract_image_urls(html_text: str, base_url: str) -> list[str]:
    """og:image / twitter:image URLs from saved page text, absolute and de-duplicated."""
    parser = _MetaParser()
    parser.feed(html_text)
    seen: list[str] = []
    for _, raw in parser.images:
        url = urljoin(base_url, raw)
        if url not in seen:
            seen.append(url)
    return seen


def load_candidates(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _cand_key(c: dict):
    return (c.get("kind"), c.get("promise_id") or c.get("entity_name"), c.get("image_url"))


def write_candidates(path: Path, candidates: list[dict]) -> None:
    """Write the review file, keeping reviewer decisions on entries already present."""
    existing = {_cand_key(c): c for c in load_candidates(path)}
    merged = []
    for c in candidates:
        old = existing.get(_cand_key(c))
        if old:
            c = {**c, **{k: old[k] for k in ("status", "license", "license_url", "credit", "reviewer_note") if k in old}}
        merged.append(c)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(merged, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def stage_promise_candidates(promises, sources_dir: Path, client, save_dir: Path | None = None) -> list[dict]:
    """One pending candidate per saved source page that declares an og/twitter image.

    Reads the saved source file, fetches each image once (allowlisted hosts only),
    saves the bytes and records the SHA-256. Never auto-approves.
    """
    out = []
    for p in promises:
        pid, rel = p.get("promise_id"), p.get("source_file_path")
        if not pid or not rel or pid in NEVER_REHOST_IDS:
            continue
        path = Path(sources_dir) / rel
        if not path.is_file():
            continue
        page = p.get("source_url") or ""
        for url in extract_image_urls(path.read_text(encoding="utf-8", errors="replace"), page)[:1]:
            if is_never_rehost(pid, url) or not host_allowed(url):
                continue
            try:
                data = fetch_bytes(client, url)
            except MediaError:
                continue
            digest = sha256_hex(data)
            if save_dir is not None:
                save_dir.mkdir(parents=True, exist_ok=True)
                (save_dir / digest).write_bytes(data)
            out.append({
                "kind": "promise", "promise_id": pid, "image_url": url,
                "source_page": page, "sha256": digest,
                "license_guess": guess_license(url), "status": "pending",
                "fetched_at": now_iso(),
            })
    return out


COMMONS_API = "https://commons.wikimedia.org/w/api.php"


def _strip_tags(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s or "")).strip()


def commons_lookup(client, entity_name: str) -> dict | None:
    """Best Commons image for an entity whose license is open; None if none qualifies."""
    params = {
        "action": "query", "format": "json", "generator": "search",
        "gsrsearch": f"{entity_name} filetype:bitmap", "gsrnamespace": "6", "gsrlimit": "5",
        "prop": "imageinfo", "iiprop": "url|extmetadata|mime", "iiurlwidth": "160",
    }
    response = client.get(COMMONS_API, params=params, timeout=FETCH_TIMEOUT)
    if response.status_code != 200:
        raise MediaError(f"commons lookup failed ({response.status_code})")
    pages = (response.json().get("query") or {}).get("pages") or {}
    for page in sorted(pages.values(), key=lambda x: x.get("index", 0)):
        info = (page.get("imageinfo") or [{}])[0]
        meta = info.get("extmetadata") or {}
        license_name = _strip_tags((meta.get("LicenseShortName") or {}).get("value", ""))
        url = info.get("thumburl") or info.get("url")
        if not url or not OPEN_LICENSE.match(license_name) or not host_allowed(url):
            continue
        return {
            "image_url": url, "source_page": info.get("descriptionurl", ""),
            "credit": _strip_tags((meta.get("Artist") or {}).get("value", "")) or "Unknown author",
            "license": license_name,
            "license_url": _strip_tags((meta.get("LicenseUrl") or {}).get("value", "")),
        }
    return None


def _no_query(url: str) -> str:
    """Drop the utm_* tracking query Commons appends to upload URLs."""
    return url.split("?", 1)[0]


def commons_file_info(client, title: str) -> dict | None:
    """Commons imageinfo for one exact file title; None unless its license is open.

    Uses prop=imageinfo with iiprop=url|extmetadata|sha1. `thumb_url` is a 320px
    render (needed for SVG, which Pillow cannot read).
    """
    params = {
        "action": "query", "format": "json", "titles": title, "prop": "imageinfo",
        "iiprop": "url|extmetadata|sha1|mime|size", "iiurlwidth": "320",
    }
    response = client.get(COMMONS_API, params=params, timeout=FETCH_TIMEOUT)
    if response.status_code != 200:
        raise MediaError(f"commons lookup failed ({response.status_code})")
    for page in ((response.json().get("query") or {}).get("pages") or {}).values():
        info = (page.get("imageinfo") or [None])[0]
        if not info:
            continue
        meta = info.get("extmetadata") or {}
        license_name = _strip_tags((meta.get("LicenseShortName") or {}).get("value", ""))
        url = _no_query(info.get("url") or "")
        if not url or not OPEN_LICENSE.match(license_name) or not host_allowed(url):
            return None
        return {
            "original_url": url, "thumb_url": _no_query(info.get("thumburl") or ""),
            "sha1": info.get("sha1") or "", "mime": info.get("mime") or "",
            "size": info.get("size") or 0,
            "source_page": info.get("descriptionurl", ""),
            "credit": _strip_tags((meta.get("Artist") or {}).get("value", "")) or "Unknown author",
            "license": license_name,
            "license_url": _strip_tags((meta.get("LicenseUrl") or {}).get("value", "")),
        }
    return None


def load_entity_config(path: Path = ENTITY_CONFIG) -> dict:
    """entity_canonical_name -> {"title": "File:...", "fit": "cover"|"contain"}; curated, exact titles."""
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def stage_curated_entity_candidates(config: dict, client, names=None) -> list[dict]:
    """Pending candidates for curated Commons file titles (no fuzzy search).

    Downloads the original once and checks it against the Commons sha1, then
    records the SHA-256 of that original. SVG and other non-raster originals are
    rendered from the 320px Commons thumbnail (`image_url`); `original_url`
    always names the Commons original. Never auto-approves.
    """
    out = []
    for name, spec in sorted(config.items()):
        if names is not None and name not in names:
            continue
        try:
            hit = commons_file_info(client, spec["title"])
            if not hit or not (0 < hit["size"] <= MAX_FETCH_BYTES):
                continue
            data = fetch_bytes(client, hit["original_url"])
        except MediaError:
            continue
        if hit["sha1"] and hashlib.sha1(data).hexdigest() != hit["sha1"]:
            continue
        raster = hit["mime"] in ("image/jpeg", "image/png", "image/webp")
        render_url = hit["original_url"] if raster else hit["thumb_url"]
        if not render_url:
            continue
        out.append({
            "kind": "entity", "entity_name": name, "image_url": render_url,
            "original_url": hit["original_url"], "source_page": hit["source_page"],
            "sha256": sha256_hex(data), "commons_sha1": hit["sha1"],
            "fit": spec.get("fit", "cover"), "license_guess": "CC",
            "suggested_license": hit["license"], "suggested_license_url": hit["license_url"],
            "suggested_credit": hit["credit"], "status": "pending", "fetched_at": now_iso(),
        })
    return out


def stage_entity_candidates(entity_names, client) -> list[dict]:
    out = []
    for name in entity_names:
        try:
            hit = commons_lookup(client, name)
        except MediaError:
            continue
        if not hit:
            continue
        data = fetch_bytes(client, hit["image_url"])
        out.append({
            "kind": "entity", "entity_name": name, "image_url": hit["image_url"],
            "source_page": hit["source_page"], "sha256": sha256_hex(data),
            "license_guess": "CC", "suggested_license": hit["license"],
            "suggested_license_url": hit["license_url"], "suggested_credit": hit["credit"],
            "status": "pending", "fetched_at": now_iso(),
        })
    return out


def check_approved(c: dict) -> None:
    """Licensing gate: raise MediaError unless the candidate may enter docs/media."""
    ident = c.get("promise_id") or c.get("entity_name")
    if c.get("status") != "approved":
        raise MediaError(f"{ident}: candidate is not approved")
    for field in ("license", "license_url", "credit", "image_url"):
        if not str(c.get(field) or "").strip():
            raise MediaError(f"{ident}: approved candidate has empty {field}")
    if c.get("kind") == "promise" and is_never_rehost(c.get("promise_id"), c["image_url"]):
        raise MediaError(f"{ident}: source must not be rehosted")
    if c.get("kind") == "entity" and not OPEN_LICENSE.match(c["license"]):
        raise MediaError(f"{ident}: entity license is not open: {c['license']}")


def resize_webp(data: bytes, width: int) -> bytes:
    from PIL import Image

    img = Image.open(io.BytesIO(data))
    img = img.convert("RGBA" if img.mode in ("RGBA", "LA", "P") else "RGB")
    if img.width > width:
        img = img.resize((width, max(1, round(img.height * width / img.width))), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, "WEBP", quality=80, method=6)
    return buf.getvalue()


def square_webp(data: bytes, size: int = 160, fit: str = "cover") -> bytes:
    """Square avatar. cover: crop from the top (portraits). contain: logo on white with margin."""
    from PIL import Image

    img = Image.open(io.BytesIO(data)).convert("RGBA")
    if fit == "contain":
        inner = round(size * 0.84)
        img.thumbnail((inner, inner), Image.LANCZOS)
        canvas = Image.new("RGBA", (size, size), (255, 255, 255, 255))
        canvas.alpha_composite(img, ((size - img.width) // 2, (size - img.height) // 2))
        img = canvas
    else:
        side = min(img.width, img.height)
        left = (img.width - side) // 2
        img = img.crop((left, 0, left + side, side)).resize((size, size), Image.LANCZOS)
    buf = io.BytesIO()
    img.convert("RGB").save(buf, "WEBP", quality=80, method=6)
    return buf.getvalue()


def load_manifest(path: Path = MANIFEST_PATH) -> dict:
    if not path.exists():
        return {"images": [], "entities": []}
    m = json.loads(path.read_text(encoding="utf-8"))
    m.setdefault("images", [])
    m.setdefault("entities", [])
    return m


def media_dir_bytes(root: Path = MEDIA_DIR) -> int:
    return sum(f.stat().st_size for f in root.rglob("*") if f.is_file())


def apply_candidates(candidates, client, media_dir: Path = MEDIA_DIR) -> list[str]:
    """Download approved candidates, resize, hash, and update the manifest.

    Unapproved entries are skipped silently; approved entries that fail the
    gate raise. The downloaded bytes must match the staged SHA-256.
    """
    manifest_path = media_dir / "manifest.json"
    manifest = load_manifest(manifest_path)
    written: list[str] = []
    for c in candidates:
        if c.get("status") != "approved":
            continue
        check_approved(c)
        data = fetch_bytes(client, c["image_url"])
        digest = sha256_hex(data)
        original = c.get("original_url") or c["image_url"]
        if original != c["image_url"]:
            # Rendered from a thumbnail (e.g. SVG): the recorded hash is the original's.
            if not host_allowed(original):
                raise MediaError(f"{c.get('entity_name')}: original host not allowlisted")
            digest = sha256_hex(fetch_bytes(client, original))
        if c.get("sha256") and c["sha256"] != digest:
            raise MediaError(f"{c.get('promise_id') or c.get('entity_name')}: sha256 changed since staging")
        if c["kind"] == "promise":
            pid = c["promise_id"]
            files = {f"{pid}-800.webp": resize_webp(data, 800), f"{pid}-320.webp": resize_webp(data, 320)}
            for name, blob in files.items():
                (media_dir).mkdir(parents=True, exist_ok=True)
                (media_dir / name).write_bytes(blob)
            manifest["images"] = [e for e in manifest["images"] if e["promise_id"] != pid]
            manifest["images"].append({
                "promise_id": pid, "original_url": c["image_url"], "sha256": digest,
                "credit": c["credit"], "license": c["license"], "license_url": c["license_url"],
                "fetched_at": c.get("fetched_at") or now_iso(),
            })
            written += list(files)
        else:
            name = c["entity_name"]
            slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
            rel = f"entities/{slug}-160.webp"
            (media_dir / "entities").mkdir(parents=True, exist_ok=True)
            (media_dir / rel).write_bytes(square_webp(data, 160, c.get("fit", "cover")))
            manifest["entities"] = [e for e in manifest["entities"] if e["entity_name"] != name]
            manifest["entities"].append({
                "entity_name": name, "path": rel, "original_url": original, "sha256": digest,
                "credit": c["credit"], "license": c["license"], "license_url": c["license_url"],
                "fetched_at": c.get("fetched_at") or now_iso(),
            })
            written.append(rel)
    manifest["images"].sort(key=lambda e: e["promise_id"])
    manifest["entities"].sort(key=lambda e: e["entity_name"])
    if media_dir_bytes(media_dir) > MAX_MEDIA_BYTES + 1:
        raise MediaError("docs/media would exceed 2 MB")
    media_dir.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return written


def apply_manifest_fields(promises, manifest: dict | None = None) -> None:
    """Add media_* / entity_image_* export fields from the manifest (no manifest entry, no field)."""
    manifest = manifest if manifest is not None else load_manifest()
    by_pid = {e["promise_id"]: e for e in manifest["images"]}
    by_entity = {e["entity_name"]: e for e in manifest["entities"]}
    for p in promises:
        e = by_pid.get(p.get("promise_id"))
        if e:
            pid = e["promise_id"]
            p["media_path"] = f"media/{pid}-800.webp"
            p["media_thumb_path"] = f"media/{pid}-320.webp"
            p["media_credit"] = e["credit"]
            p["media_license"] = e["license"]
        ent = by_entity.get(p.get("entity_canonical_name"))
        if ent:
            p["entity_image_path"] = f"media/{ent['path']}"
            p["entity_image_credit"] = f"{ent['credit']} / {ent['license']}"
