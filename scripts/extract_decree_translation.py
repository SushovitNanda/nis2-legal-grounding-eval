#!/usr/bin/env python3
"""Pull the English column out of the bilingual table of Decreto-Lei n.º 125/2025 (unofficial translation).

  python scripts/extract_decree_translation.py

Reads  data/decree/translation/DL-125-2025-pt-en-proposed-translation.pdf
       (91 pages; columns: source page | Portuguese as published | proposed English translation)
Writes data/decree/translation/DL-125-2025-en-proposed.txt

The translation is UNOFFICIAL: produced with AI, segment by segment, not reviewed by a translator
or a lawyer. It is a reading aid (for readers of the report who do not read Portuguese, and for
reading judge outputs). It is not given to any model in the core conditions and the judge never
sees it: the reference text is the official Portuguese one in data/decree/DL-125-2025.txt.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "data/decree/translation/DL-125-2025-pt-en-proposed-translation.pdf"
OUT = ROOT / "data/decree/translation/DL-125-2025-en-proposed.txt"
BANNER = ("UNOFFICIAL ENGLISH TRANSLATION of Decreto-Lei n.º 125/2025, de 4 de dezembro. Produced with AI, not reviewed "
          "by a translator or a lawyer. Only the Portuguese text published in the Diário da República is official.")


def main():
    import pdfplumber
    out = []
    with pdfplumber.open(PDF) as pdf:
        n = len(pdf.pages)
        for i, page in enumerate(pdf.pages, 1):
            head = [w for w in page.extract_words() if w["text"] == "English" and w["top"] < 400]
            if not head:
                sys.exit(f"page {i}: no 'English' column header found")
            x0, top = head[0]["x0"] - 2, head[0]["bottom"] + 1
            text = page.crop((x0, top, page.width, page.height)).extract_text() or ""
            lines = [l.strip() for l in text.splitlines() if l.strip() and not re.fullmatch(r"\d+ / \d+", l.strip())]
            out.append("\n".join(lines))
    text = BANNER + "\n\n" + "\n".join(out)
    n_art = len(re.findall(r"^Article \d+$", text, flags=re.M))
    OUT.write_text(text, encoding="utf-8")
    print(f"{n} pages, {len(text):,} chars, {n_art} article headings (100 expected: 11 + 87 + 2) -> {OUT}")


if __name__ == "__main__":
    main()
