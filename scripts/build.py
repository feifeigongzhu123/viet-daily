"""Build static assets for the VietDaily PWA.

Reads data/words.json, validates it, writes data/words.js (so the app also
works when opened directly from the filesystem), and renders the app icons.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "words.json"
OUT_JS = ROOT / "data" / "words.js"
PHONETICS_FILE = ROOT / "data" / "phonetics.json"
PHONETICS_JS = ROOT / "data" / "phonetics.js"
ICON_DIR = ROOT / "icons"

REQUIRED = {
    "id", "word", "pos", "ipa", "homophone", "meaning",
    "example", "exampleZh", "lesson", "topic", "source",
}


def load_words() -> list[dict]:
    words = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    seen: set[str] = set()
    for index, item in enumerate(words, start=1):
        missing = REQUIRED - item.keys()
        if missing:
            raise ValueError(f"Entry #{index} ({item.get('id')}) missing: {sorted(missing)}")
        if item["id"] in seen:
            raise ValueError(f"Duplicate id: {item['id']}")
        seen.add(item["id"])
    return words


def write_words_js(words: list[dict]) -> None:
    payload = json.dumps(words, ensure_ascii=False, indent=2)
    OUT_JS.write_text(
        "/* Generated from words.json by scripts/build.py. */\n"
        f"window.VOCAB = {payload};\n",
        encoding="utf-8",
    )


def load_phonetics() -> dict:
    data = json.loads(PHONETICS_FILE.read_text(encoding="utf-8"))
    ids = set()
    for section in ("vowels", "consonants", "tones"):
        if not isinstance(data.get(section), list):
            raise ValueError(f"phonetics.json missing list: {section}")
        for item in data[section]:
            if not item.get("id") or item["id"] in ids:
                raise ValueError(f"Duplicate/missing phonetics id in {section}: {item.get('id')}")
            ids.add(item["id"])
            if not item.get("example"):
                raise ValueError(f"Phonetics {item['id']} missing example")
    return data


def write_phonetics_js(data: dict) -> None:
    payload = json.dumps(data, ensure_ascii=False, indent=2)
    PHONETICS_JS.write_text(
        "/* Generated from phonetics.json by scripts/build.py. */\n"
        f"window.PHONETICS = {payload};\n",
        encoding="utf-8",
    )


def star_points(cx: float, cy: float, outer: float, inner: float, points: int = 5) -> list[tuple[float, float]]:
    result = []
    for i in range(points * 2):
        radius = outer if i % 2 == 0 else inner
        angle = -math.pi / 2 + i * math.pi / points
        result.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
    return result


def rounded_mask(size: int, radius: int) -> Image.Image:
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size - 1, size - 1), radius=radius, fill=255)
    return mask


def make_icon(size: int, *, maskable: bool = False) -> Image.Image:
    scale = 4
    canvas = size * scale
    image = Image.new("RGB", (canvas, canvas), "#9E0D26")
    draw = ImageDraw.Draw(image)

    # Vertical deep-red gradient.
    for y in range(canvas):
        t = y / max(canvas - 1, 1)
        r = round(176 + (116 - 176) * t)
        g = round(18 + (7 - 18) * t)
        b = round(45 + (29 - 45) * t)
        draw.line([(0, y), (canvas, y)], fill=(r, g, b))

    # Soft cream glow in the upper-left.
    glow = Image.new("RGBA", (canvas, canvas), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse(
        (-canvas * 0.25, -canvas * 0.35, canvas * 0.65, canvas * 0.55),
        fill=(247, 225, 185, 30),
    )
    image = Image.alpha_composite(image.convert("RGBA"), glow).convert("RGB")
    draw = ImageDraw.Draw(image)

    # Thin double ring.
    inset = canvas * (0.105 if maskable else 0.09)
    ring_width = max(2, round(canvas * 0.008))
    draw.ellipse(
        (inset, inset, canvas - inset, canvas - inset),
        outline=(240, 205, 132),
        width=ring_width,
    )
    inner = inset + canvas * 0.028
    draw.ellipse(
        (inner, inner, canvas - inner, canvas - inner),
        outline=(240, 205, 132, 110),
        width=max(1, ring_width // 2),
    )

    # Gold star, Vietnam-flag inspired.
    star_outer = canvas * (0.075 if maskable else 0.085)
    sx, sy = canvas * 0.755, canvas * 0.245
    draw.polygon(star_points(sx, sy, star_outer, star_outer * 0.42), fill=(242, 198, 92))

    # Big cream V.
    font_size = round(canvas * (0.47 if maskable else 0.52))
    font = None
    for candidate in (
        Path(r"C:\Windows\Fonts\arialbd.ttf"),
        Path(r"C:\Windows\Fonts\segoeuib.ttf"),
        Path(r"C:\Windows\Fonts\calibrib.ttf"),
    ):
        if candidate.exists():
            font = ImageFont.truetype(str(candidate), font_size)
            break
    if font is None:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), "V", font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = (canvas - tw) / 2 - bbox[0]
    ty = canvas * (0.535 if maskable else 0.55) - th / 2 - bbox[1]
    draw.text((tx, ty), "V", font=font, fill=(251, 244, 229))

    # Small gold underline under the V.
    line_w = canvas * 0.17
    line_y = canvas * 0.765
    draw.rounded_rectangle(
        (canvas / 2 - line_w / 2, line_y, canvas / 2 + line_w / 2, line_y + canvas * 0.012),
        radius=canvas * 0.006,
        fill=(242, 198, 92),
    )

    icon = image.resize((size, size), Image.Resampling.LANCZOS)
    if not maskable:
        icon = icon.convert("RGBA")
        icon.putalpha(rounded_mask(size, round(size * 0.22)))
    else:
        icon = icon.convert("RGBA")
    return icon


def write_icons() -> None:
    ICON_DIR.mkdir(exist_ok=True)
    make_icon(192).save(ICON_DIR / "icon-192.png", optimize=True)
    make_icon(512).save(ICON_DIR / "icon-512.png", optimize=True)
    make_icon(512, maskable=True).save(ICON_DIR / "icon-maskable-512.png", optimize=True)
    make_icon(180).save(ICON_DIR / "apple-touch-icon.png", optimize=True)
    make_icon(32).save(ICON_DIR / "favicon-32.png", optimize=True)


def main() -> None:
    words = load_words()
    write_words_js(words)
    phonetics = load_phonetics()
    write_phonetics_js(phonetics)
    write_icons()
    lessons = sorted({item["lesson"] for item in words})
    topics = sorted({item["topic"] for item in words})
    print(f"OK: {len(words)} words, lessons={lessons}, topics={topics}")
    print(
        f"OK: phonetics vowels={len(phonetics['vowels'])}, "
        f"consonants={len(phonetics['consonants'])}, tones={len(phonetics['tones'])}"
    )
    print(f"Wrote {OUT_JS.relative_to(ROOT)}, {PHONETICS_JS.relative_to(ROOT)} and {ICON_DIR.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
