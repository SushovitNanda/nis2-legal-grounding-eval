#!/usr/bin/env python3
"""Extract a clean, page-separated text of Decreto-Lei n.º 125/2025 from the official PDF.

Why this exists: the official Diário da República PDF maps the glyphs for the
letters "i" and "v" (Roboto Regular) to private-use codepoints U+E034 and
U+E041, so ordinary extractors (pdftotext, copy/paste) silently drop them
("ncdente sgnfcato" for "incidente significativo"). We read the characters
with pdfplumber and map the two codepoints back. Nothing is OCR'd or guessed.

Output: data/decree/DL-125-2025.txt, pages separated by form feed (\f), so
page N of the text is page N of the official PDF (as cited in the standard).

Usage: python scripts/extract_decree_text.py [pdf] [out.txt]
"""
import re
import sys
from pathlib import Path

import pdfplumber

ROOT = Path(__file__).resolve().parents[1]
PUA = {"": "i", "": "v"}


def page_text(page) -> str:
    # drop the rotated margin stamp ("Decreto-Lei n.º 125/2025" printed vertically)
    page = page.filter(lambda o: o.get("object_type") != "char" or o.get("upright", True))
    txt = page.extract_text(x_tolerance=1.5, y_tolerance=3) or ""
    for k, v in PUA.items():
        txt = txt.replace(k, v)
    leftover = sorted({c for c in txt if 0xE000 <= ord(c) <= 0xF8FF})
    if leftover:
        raise SystemExit(f"unmapped private-use glyphs on page {page.page_number}: {leftover!r}")
    lines = [re.sub(r"[ \t]+", " ", ln).rstrip() for ln in txt.splitlines()]
    return "\n".join(lines).strip()


def main():
    pdf_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data/decree/DL-125-2025-NIS2.pdf"
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "data/decree/DL-125-2025.txt"
    with pdfplumber.open(pdf_path) as pdf:
        pages = [page_text(p) for p in pdf.pages]
    out.write_text("\f".join(pages), encoding="utf-8")
    print(f"{len(pages)} pages, {sum(map(len, pages)):,} chars -> {out}")


if __name__ == "__main__":
    main()
