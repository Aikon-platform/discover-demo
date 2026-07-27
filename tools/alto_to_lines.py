#!/usr/bin/env python3
"""
Convert an ALTO dataset (page images + line-by-line XML) to the format expected
by the paleography module: one image crop per line + a homonymous .txt.

Expected source (Metrology4Morphology / Zenodo dataset):
    <src>/images/<page>.jpg
    <src>/annotations/<page>.xml     (ALTO v4)

Produced output:
    <out>/<page>/<page>_l0001.png
    <out>/<page>/<page>_l0001.txt
    ... (one subfolder per page; subfolders allowed per decision #4)
and, optionally, a zip ready to upload.

Usage:
    python alto_to_lines.py --src ~/projects/paleo_data --out ~/projects/paleo_data/lines \
                            --pages 3 --zip dataset_paleo_reel.zip
"""

from __future__ import annotations

import argparse
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from PIL import Image

ALTO_NS = {"alto": "http://www.loc.gov/standards/alto/ns-v4#"}
IMG_EXTS = (".jpg", ".jpeg", ".png", ".tif", ".tiff")


def parse_lines(xml_path: Path) -> list[dict]:
    """Extract lines from an ALTO file: bbox + transcription."""
    root = ET.parse(xml_path).getroot()
    lines = []
    for tl in root.iter():
        if not tl.tag.endswith("}TextLine") and tl.tag != "TextLine":
            continue
        # transcription = concatenation of <String CONTENT="...">
        contents = [
            s.get("CONTENT", "")
            for s in tl.iter()
            if s.tag.endswith("}String") or s.tag == "String"
        ]
        text = " ".join(c for c in contents if c).strip()
        if not text:
            continue  # line without transcription -> skipped
        try:
            box = (
                int(float(tl.get("HPOS"))),
                int(float(tl.get("VPOS"))),
                int(float(tl.get("WIDTH"))),
                int(float(tl.get("HEIGHT"))),
            )
        except (TypeError, ValueError):
            continue  # missing coordinates -> skipped
        lines.append({"id": tl.get("ID", ""), "box": box, "text": text})
    return lines


def crop_page(
    img_path: Path, xml_path: Path, out_dir: Path, *, margin: int = 0
) -> tuple[int, int]:
    """Crop all lines of a page. Returns (n_written, n_skipped)."""
    lines = parse_lines(xml_path)
    if not lines:
        return 0, 0

    page = img_path.stem
    page_dir = out_dir / page
    page_dir.mkdir(parents=True, exist_ok=True)

    written = skipped = 0
    with Image.open(img_path) as im:
        W, H = im.size
        for i, line in enumerate(lines, start=1):
            x, y, w, h = line["box"]
            # margin + clamp to image borders
            x1, y1 = max(0, x - margin), max(0, y - margin)
            x2, y2 = min(W, x + w + margin), min(H, y + h + margin)
            if x2 <= x1 or y2 <= y1:
                skipped += 1
                continue
            crop = im.crop((x1, y1, x2, y2)).convert("RGB")
            stem = f"{page}_l{i:04d}"
            crop.save(page_dir / f"{stem}.png")
            (page_dir / f"{stem}.txt").write_text(
                line["text"] + "\n", encoding="utf-8"
            )
            written += 1
    return written, skipped


def find_image(images_dir: Path, stem: str) -> Path | None:
    for ext in IMG_EXTS:
        p = images_dir / f"{stem}{ext}"
        if p.exists():
            return p
    return None


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", required=True, type=Path, help="folder containing images/ and annotations/")
    ap.add_argument("--out", required=True, type=Path, help="output folder (crops + .txt)")
    ap.add_argument("--pages", type=int, default=0, help="limit to first N pages (0 = all)")
    ap.add_argument("--margin", type=int, default=5, help="margin in pixels around each line")
    ap.add_argument("--zip", type=Path, default=None, help="also create a zip ready to upload")
    args = ap.parse_args()

    images_dir = args.src / "images"
    annots_dir = args.src / "annotations"
    for d in (images_dir, annots_dir):
        if not d.is_dir():
            raise SystemExit(f"Folder not found: {d}")

    xmls = sorted(p for p in annots_dir.glob("*.xml") if not p.name.startswith("."))
    if args.pages:
        xmls = xmls[: args.pages]

    total_w = total_s = pages_ok = pages_ko = 0
    for xml_path in xmls:
        img_path = find_image(images_dir, xml_path.stem)
        if img_path is None:
            print(f"  [skip] no image for {xml_path.name}")
            pages_ko += 1
            continue
        w, s = crop_page(img_path, xml_path, args.out, margin=args.margin)
        total_w += w
        total_s += s
        pages_ok += 1
        print(f"  {xml_path.stem}: {w} lines")

    print(f"\nPages processed: {pages_ok} (skipped: {pages_ko})")
    print(f"Lines written: {total_w} (skipped: {total_s})")
    print(f"Output: {args.out}")

    if args.zip:
        with zipfile.ZipFile(args.zip, "w", zipfile.ZIP_DEFLATED) as zf:
            for p in sorted(args.out.rglob("*")):
                if p.is_file():
                    zf.write(p, p.relative_to(args.out))
        print(f"Zip created: {args.zip}")


if __name__ == "__main__":
    main()
