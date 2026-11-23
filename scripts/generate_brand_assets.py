#!/usr/bin/env python3
"""
Generate custom SF Promises favicon suite, Apple touch icon, Open Graph social preview card,
and web app manifest into docs/ without external assets.
"""

from __future__ import annotations

import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"

BG_DARK = (15, 26, 38)
BG_CARD = (20, 34, 49)
EMERALD = (16, 185, 129)
AMBER = (245, 158, 11)
RED = (239, 68, 68)
SLATE = (148, 163, 184)
CYAN = (56, 189, 248)
WHITE = (248, 250, 252)
MUTED = (163, 179, 198)
BORDER = (43, 62, 85)


def _find_font(size: int, bold: bool = True, mono: bool = False):
    candidates = []
    if mono:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        ]
    else:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def draw_sf_emblem(size: int) -> Image.Image:
    """Render a crisp dark-slate rounded-square SF monogram icon at any square resolution."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    pad = max(1, round(size * 0.04))
    radius = max(4, round(size * 0.22))
    stroke = max(1, round(size * 0.06))

    draw.rounded_rectangle(
        [pad, pad, size - pad - 1, size - pad - 1],
        radius=radius,
        fill=BG_DARK,
        outline=EMERALD,
        width=stroke,
    )

    # Bottom status accent strip (kept/progress/broken triad)
    bar_y0 = round(size * 0.80)
    bar_y1 = round(size * 0.86)
    x_left = round(size * 0.18)
    x_right = round(size * 0.82)
    span = x_right - x_left
    draw.rectangle([x_left, bar_y0, x_left + round(span * 0.48), bar_y1], fill=EMERALD)
    draw.rectangle([x_left + round(span * 0.50), bar_y0, x_left + round(span * 0.70), bar_y1], fill=AMBER)
    draw.rectangle([x_left + round(span * 0.72), bar_y0, x_right, bar_y1], fill=RED)

    # Centered bold "SF" monogram
    font = _find_font(round(size * 0.46), bold=True)
    bbox = draw.textbbox((0, 0), "SF", font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = (size - tw) / 2 - bbox[0]
    ty = (size * 0.45) - (th / 2) - bbox[1]
    draw.text((tx, ty), "SF", font=font, fill=WHITE)

    return img


def write_favicon_svg():
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" role="img" aria-label="SF Promises">
  <defs>
    <linearGradient id="sf-ring" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#10b981"/>
      <stop offset="100%" stop-color="#38bdf8"/>
    </linearGradient>
  </defs>
  <rect x="6" y="6" width="116" height="116" rx="26" fill="#0f1a26" stroke="url(#sf-ring)" stroke-width="6"/>
  <text x="64" y="75" text-anchor="middle" font-family="ui-sans-serif, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-weight="800" font-size="60" letter-spacing="-2" fill="#f8fafc">SF</text>
  <rect x="24" y="96" width="38" height="8" rx="4" fill="#10b981"/>
  <rect x="65" y="96" width="17" height="8" rx="4" fill="#f59e0b"/>
  <rect x="85" y="96" width="19" height="8" rx="4" fill="#ef4444"/>
</svg>
"""
    (DOCS / "favicon.svg").write_text(svg, encoding="utf-8")


def write_og_image():
    w, h = 1200, 630
    img = Image.new("RGB", (w, h), BG_DARK)
    draw = ImageDraw.Draw(img)

    # Outer civic frame
    draw.rounded_rectangle([28, 28, w - 28, h - 28], radius=24, fill=BG_CARD, outline=BORDER, width=2)

    # Paste high-res SF emblem top-left
    emblem = draw_sf_emblem(112)
    img.paste(emblem, (72, 72), emblem)

    font_tag = _find_font(22, bold=True, mono=True)
    font_h1 = _find_font(54, bold=True)
    font_sub = _find_font(28, bold=False)
    font_stat = _find_font(24, bold=True, mono=True)
    font_foot = _find_font(21, bold=False, mono=True)

    draw.text((208, 86), "SAN FRANCISCO CIVIC ACCOUNTABILITY", font=font_tag, fill=CYAN)
    draw.text((208, 122), "SF Promises", font=font_h1, fill=WHITE)

    draw.text((72, 224), "A sourced record of what San Francisco's", font=font_h1, fill=WHITE)
    draw.text((72, 290), "leaders promised, and what happened.", font=font_h1, fill=EMERALD)

    draw.text(
        (72, 376),
        "Tracking 54 commitments across City Hall, SFO Airport, transit, & sports",
        font=font_sub,
        fill=MUTED,
    )

    # Proportional Outcome Distribution Bar (matches 25 / 10 / 17 / 2)
    bx0, by0, bx1, by1 = 72, 444, w - 72, 474
    span = bx1 - bx0
    s1 = round(span * 0.463)
    s2 = round(span * 0.185)
    s3 = round(span * 0.315)
    draw.rectangle([bx0, by0, bx0 + s1, by1], fill=EMERALD)
    draw.rectangle([bx0 + s1, by0, bx0 + s1 + s2, by1], fill=AMBER)
    draw.rectangle([bx0 + s1 + s2, by0, bx0 + s1 + s2 + s3, by1], fill=RED)
    draw.rectangle([bx0 + s1 + s2 + s3, by0, bx1, by1], fill=SLATE)

    draw.text(
        (72, 492),
        "25 KEPT (46%)   ·   10 IN PROGRESS (19%)   ·   17 BROKEN (31%)   ·   2 UNDECIDED (4%)",
        font=font_stat,
        fill=WHITE,
    )

    draw.line([(72, 546), (w - 72, 546)], fill=BORDER, width=2)
    draw.text(
        (72, 562),
        "Sourced to saved, SHA-256 hashed primary records  |  arii.github.io/sf-promises",
        font=font_foot,
        fill=MUTED,
    )

    img.save(DOCS / "og-image.png", format="PNG", optimize=True)

    og_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 630" role="img" aria-label="SF Promises Social Card">
  <rect width="1200" height="630" fill="#0f1a26"/>
  <rect x="28" y="28" width="1144" height="574" rx="24" fill="#142231" stroke="#2b3e55" stroke-width="2"/>
  <rect x="72" y="72" width="112" height="112" rx="24" fill="#0f1a26" stroke="#10b981" stroke-width="6"/>
  <text x="128" y="138" text-anchor="middle" font-family="ui-sans-serif, system-ui, sans-serif" font-weight="800" font-size="52" fill="#f8fafc">SF</text>
  <text x="208" y="106" font-family="ui-monospace, monospace" font-weight="700" font-size="20" fill="#38bdf8">SAN FRANCISCO CIVIC ACCOUNTABILITY</text>
  <text x="208" y="166" font-family="ui-sans-serif, system-ui, sans-serif" font-weight="800" font-size="52" fill="#f8fafc">SF Promises</text>
  <text x="72" y="268" font-family="ui-sans-serif, system-ui, sans-serif" font-weight="800" font-size="52" fill="#f8fafc">A sourced record of what San Francisco's</text>
  <text x="72" y="332" font-family="ui-sans-serif, system-ui, sans-serif" font-weight="800" font-size="52" fill="#10b981">leaders promised, and what happened.</text>
  <text x="72" y="398" font-family="ui-sans-serif, system-ui, sans-serif" font-size="26" fill="#a3b3c6">Tracking 54 commitments across City Hall, SFO Airport, transit, &amp; sports</text>
  <rect x="72" y="444" width="489" height="28" fill="#10b981"/>
  <rect x="561" y="444" width="195" height="28" fill="#f59e0b"/>
  <rect x="756" y="444" width="333" height="28" fill="#ef4444"/>
  <rect x="1089" y="444" width="39" height="28" fill="#94a3b8"/>
  <text x="72" y="512" font-family="ui-monospace, monospace" font-weight="700" font-size="22" fill="#f8fafc">25 KEPT (46%)  ·  10 IN PROGRESS (19%)  ·  17 BROKEN (31%)  ·  2 UNDECIDED (4%)</text>
  <text x="72" y="576" font-family="ui-monospace, monospace" font-size="20" fill="#a3b3c6">Sourced to saved, SHA-256 hashed primary records  |  arii.github.io/sf-promises</text>
</svg>
"""
    (DOCS / "og-image.svg").write_text(og_svg, encoding="utf-8")


def write_webmanifest():
    manifest = {
        "name": "SF Promises — San Francisco Public Commitments",
        "short_name": "SF Promises",
        "description": "A sourced civic accountability record of 54 public commitments across San Francisco City Hall, SFO Airport, transit, housing, and sports.",
        "start_url": "/sf-promises/",
        "scope": "/sf-promises/",
        "display": "standalone",
        "theme_color": "#0f1a26",
        "background_color": "#0f1a26",
        "icons": [
            {"src": "favicon.svg", "sizes": "any", "type": "image/svg+xml"},
            {"src": "favicon-32x32.png", "sizes": "32x32", "type": "image/png"},
            {"src": "apple-touch-icon.png", "sizes": "180x180", "type": "image/png"},
        ],
    }
    (DOCS / "site.webmanifest").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def main():
    DOCS.mkdir(parents=True, exist_ok=True)
    write_favicon_svg()

    icon_180 = draw_sf_emblem(180)
    icon_180.save(DOCS / "apple-touch-icon.png", format="PNG", optimize=True)

    icon_32 = draw_sf_emblem(32)
    icon_32.save(DOCS / "favicon-32x32.png", format="PNG", optimize=True)

    icon_48 = draw_sf_emblem(48)
    icon_48.save(
        DOCS / "favicon.ico",
        format="ICO",
        sizes=[(16, 16), (32, 32), (48, 48)],
    )

    write_og_image()
    write_webmanifest()
    print("Generated favicon.svg, favicon-32x32.png, apple-touch-icon.png, favicon.ico, og-image.png, og-image.svg, and site.webmanifest in docs/")


if __name__ == "__main__":
    main()
