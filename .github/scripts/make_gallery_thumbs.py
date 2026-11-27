#!/usr/bin/env python3
"""Make the small preview copies that the Gallery page shows in its photo tiles.

For every photo in assets/gallery/ this writes two copies, 640 and 1280 pixels wide,
to assets/gallery-thumbs/ (same folders, same names plus -640.jpg / -1280.jpg).
The photo viewer still opens the full photo. A photo without copies still works:
its tile simply loads the full photo, which is slower on phones.

Copies are sRGB JPEGs with no metadata at all (no EXIF, no GPS, no dates, no color
profile). Copies whose photo was deleted are removed.

Run from the top folder of the repository (needs Pillow: pip install pillow):
    python3 .github/scripts/make_gallery_thumbs.py          # only missing copies
    python3 .github/scripts/make_gallery_thumbs.py --force  # remake all copies
"""
import io
import sys
from pathlib import Path

from PIL import Image, ImageCms, ImageOps

SRC = Path("assets/gallery")
OUT = Path("assets/gallery-thumbs")
WIDTHS = (640, 1280)
EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif"}
SRGB = ImageCms.createProfile("sRGB")


def to_srgb(im):
    """Convert to plain sRGB using the photo's own color profile (iPhones use Display P3)."""
    icc = im.info.get("icc_profile")
    if im.mode not in ("RGB", "RGBA"):
        im = im.convert("RGBA" if "transparency" in im.info or im.mode in ("LA", "PA") else "RGB")
    if icc:
        try:
            src = ImageCms.ImageCmsProfile(io.BytesIO(icc))
            im = ImageCms.profileToProfile(im, src, SRGB, outputMode=im.mode)
        except Exception:
            pass  # unreadable profile: keep the pixels as they are
    if im.mode == "RGBA":  # JPEG has no transparency: put it on white
        bg = Image.new("RGB", im.size, (255, 255, 255))
        bg.paste(im, mask=im.split()[3])
        im = bg
    return im


def main(force):
    if not SRC.is_dir():
        sys.exit("Run this from the top folder of the repository.")
    wanted = set()
    made = 0
    for photo in sorted(p for p in SRC.rglob("*") if p.suffix.lower() in EXTS):
        rel = photo.relative_to(SRC)
        with Image.open(photo) as im:
            im = ImageOps.exif_transpose(im)
            width = im.width
            todo = []
            for w in WIDTHS:
                if width <= w:
                    continue  # never enlarge; the page then uses the full photo
                out = OUT / rel.parent / f"{photo.stem}-{w}.jpg"
                wanted.add(out)
                if force or not out.exists():
                    todo.append((w, out))
            if not todo:
                continue
            im = to_srgb(im)
            for w, out in todo:
                h = round(im.height * w / im.width)
                small = im.resize((w, h), Image.LANCZOS)
                out.parent.mkdir(parents=True, exist_ok=True)
                small.save(out, "JPEG", quality=80, optimize=True, progressive=True)
                made += 1
                print("made", out)
    removed = 0
    if OUT.is_dir():
        for old in sorted(OUT.rglob("*.jpg")):
            if old not in wanted:
                old.unlink()
                removed += 1
                print("removed", old)
    print(f"{made} copies made, {removed} old copies removed.")


if __name__ == "__main__":
    main("--force" in sys.argv[1:])
