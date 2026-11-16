#!/usr/bin/env python3
"""Get the official Portuguese text of Directive (EU) 2022/2555 (NIS 2) for condition C2.

  python scripts/fetch_directive.py                    # download from EUR-Lex
  python scripts/fetch_directive.py --from-html f.html # convert a page you saved from the browser
  python scripts/fetch_directive.py --keep-recitals    # default drops the recitals, which roughly halves the length

Writes data/directive/directive-2022-2555-pt.txt. If EUR-Lex refuses the script (it sometimes
answers 202/403 to non-browser clients), open the URL in a browser, "Save page as... HTML only",
and use --from-html. Source: OJ L 333, 27.12.2022, p. 80; CELEX 32022L2555.
"""
import argparse
import html
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

URL = "https://eur-lex.europa.eu/legal-content/PT/TXT/HTML/?uri=CELEX:32022L2555"
CELLAR_URL = "http://publications.europa.eu/resource/celex/32022L2555"
OUT = Path(__file__).resolve().parents[1] / "data/directive/directive-2022-2555-pt.txt"
BLOCK = {"p", "div", "tr", "table", "br", "h1", "h2", "h3", "h4", "li", "hr"}


class _Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts, self.skip = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "head"):
            self.skip += 1
        if tag in BLOCK:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style", "head"):
            self.skip = max(0, self.skip - 1)
        if tag in BLOCK:
            self.parts.append("\n")
        if tag == "td":
            self.parts.append(" ")

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


_ORDINAL = re.compile(r'\.\s*<(?:span class="(?:oj-)?super"|sup)[^>]*>\s*([oa])\s*</(?:span|sup)>', re.I)


def html_to_text(src: str) -> str:
    # The Official Journal writes ordinals as "1.<span class="oj-super">o</span>"; make them "1.º" / "1.ª"
    src = _ORDINAL.sub(lambda m: ".º" if m.group(1).lower() == "o" else ".ª", src)
    p = _Text()
    p.feed(src)
    t = html.unescape("".join(p.parts)).replace("\xa0", " ")
    lines = [re.sub(r"[ \t]+", " ", l).strip() for l in t.splitlines()]
    out, blank = [], False
    for l in lines:
        if l:
            out.append(l); blank = False
        elif not blank:
            out.append(""); blank = True
    return "\n".join(out).strip()


def drop_recitals(text: str) -> str:
    m = re.search(r"ADOTARAM A PRESENTE DIRETIVA", text)
    if not m:
        return text
    head_end = re.search(r"Considerando o seguinte", text)
    head = text[: head_end.start()].strip() if head_end else ""
    return (head + "\n\n[Considerandos omitidos]\n\n" + text[m.start():]).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-html")
    ap.add_argument("--keep-recitals", action="store_true")
    a = ap.parse_args()
    if a.from_html:
        src = Path(a.from_html).read_text(encoding="utf-8", errors="replace")
    else:
        import requests
        src = None
        # EUR-Lex often serves a placeholder page to scripts; the Publications Office (Cellar) serves the same official text.
        for url, headers in ((URL, {"User-Agent": "Mozilla/5.0", "Accept-Language": "pt-PT,pt;q=0.9"}),
                             (CELLAR_URL, {"User-Agent": "Mozilla/5.0", "Accept": "text/html, application/xhtml+xml", "Accept-Language": "por"})):
            try:
                r = requests.get(url, timeout=150, headers=headers)
            except requests.RequestException as e:
                print(f"{url}: {e}")
                continue
            r.encoding = "utf-8"
            if r.status_code == 200 and "ADOTARAM A PRESENTE DIRETIVA" in r.text:
                src = r.text
                print(f"downloaded from {url}")
                break
            print(f"{url}: HTTP {r.status_code} without the directive text")
        if src is None:
            sys.exit(f"Could not download the text. Save the page from a browser and use --from-html.\n{URL}")
    text = html_to_text(src)
    if not a.keep_recitals:
        text = drop_recitals(text)
    n_art = len(set(re.findall(r"^Artigo (\d+)\.º", text, flags=re.M)))
    if n_art < 40:
        sys.exit(f"only {n_art} article headings found - this does not look like the full directive (46 articles). Not saved.")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    print(f"{len(text):,} chars, {n_art} articles, recitals {'kept' if a.keep_recitals else 'dropped'} -> {OUT}")


if __name__ == "__main__":
    main()
