#!/usr/bin/env python3
"""Extract the English text of Directive (EU) 2022/2555 from the official OJ PDF supplied by Bia.

  python scripts/extract_directive_en.py                  # articles and annexes, recitals dropped
  python scripts/extract_directive_en.py --keep-recitals

Reads  data/directive/Directive-EU-2022-2555-NIS2-en.pdf   (OJ L 333, 27.12.2022, pp. 80-152)
Writes data/directive/directive-2022-2555-en.txt

The English text is used (a) to cross-check the Portuguese text given to the models in C2
(`python -m nis2eval directive`) and (b) as the C2 document when a run is made with --lang en.
"""
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "data/directive/Directive-EU-2022-2555-NIS2-en.pdf"
OUT = ROOT / "data/directive/directive-2022-2555-en.txt"
HEADER = re.compile(r"^(L 333/\d+\s+EN\s+Official Journal of the European Union\s+27\.12\.2022"
                    r"|27\.12\.2022\s+EN\s+Official Journal of the European Union\s+L 333/\d+)$")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep-recitals", action="store_true")
    a = ap.parse_args()
    import pdfplumber
    lines = []
    with pdfplumber.open(PDF) as pdf:
        n_pages = len(pdf.pages)
        for page in pdf.pages:
            for line in (page.extract_text() or "").splitlines():
                line = line.strip()
                if line and not HEADER.match(line):
                    lines.append(line)
    text = "\n".join(lines)
    if not a.keep_recitals:
        start, end = text.find("Whereas:"), text.find("HAVE ADOPTED THIS DIRECTIVE")
        if start < 0 or end < 0:
            sys.exit("could not find the recitals - is this the English OJ text?")
        text = text[:start].strip() + "\n\n[Recitals omitted]\n\n" + text[end:]
    n_art = len(set(re.findall(r"^Article (\d+)$", text, flags=re.M)))
    if n_art < 46:
        sys.exit(f"only {n_art} article headings found (46 expected). Not saved.")
    OUT.write_text(text, encoding="utf-8")
    print(f"{n_pages} pages, {len(text):,} chars, {n_art} articles, recitals {'kept' if a.keep_recitals else 'dropped'} -> {OUT}")


if __name__ == "__main__":
    main()
