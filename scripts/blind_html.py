#!/usr/bin/env python3
"""A readable version of the blind sample: one HTML page that opens in any browser.

    python scripts/blind_html.py [--run full]

Reads results/<run>/blind/blind_answers.md and grading_sheet.csv (never the key file) and writes
blind_answers.html next to them: each answer as the model formatted it, followed by the checklist
items to grade for it. The marks still go in grading_sheet.csv; this page is only for reading.
"""
from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from nis2eval.blind import read_sheet  # noqa: E402


def inline(t: str) -> str:
    t = html.escape(t, quote=False)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*\*(.+?)\*\*\*", r"<strong><em>\1</em></strong>", t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", t)
    return t


def md_to_html(md: str) -> str:
    """Enough Markdown for model answers: headings, lists, tables, quotes, rules, paragraphs."""
    out, para, lst = [], [], None
    lines = md.replace("\r\n", "\n").split("\n")

    def flush():
        nonlocal para, lst
        if para:
            out.append("<p>" + "<br>".join(inline(x) for x in para) + "</p>")
            para = []
        if lst:
            out.append(f"</{lst}>")
            lst = None

    i = 0
    while i < len(lines):
        line = lines[i]
        s = line.strip()
        if not s:
            flush()
        elif re.fullmatch(r"(-{3,}|\*{3,}|_{3,})", s):
            flush(); out.append("<hr>")
        elif m := re.match(r"(#{1,6})\s+(.*)", s):
            flush()
            n = min(6, len(m.group(1)) + 2)          # answers' own headings sit below the page's headings
            out.append(f"<h{n}>{inline(m.group(2).strip('# '))}</h{n}>")
        elif s.startswith("|") and i + 1 < len(lines) and re.fullmatch(r"\|?[\s:|-]+\|?", lines[i + 1].strip()) and "-" in lines[i + 1]:
            flush()
            cells = lambda r: [c.strip() for c in r.strip().strip("|").split("|")]
            out.append("<table><thead><tr>" + "".join(f"<th>{inline(c)}</th>" for c in cells(s)) + "</tr></thead><tbody>")
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                out.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in cells(lines[i])) + "</tr>")
                i += 1
            out.append("</tbody></table>")
            continue
        elif m := re.match(r"(?:[-*+•])\s+(.*)", s):
            if para:
                flush()
            if lst != "ul":
                flush(); out.append("<ul>"); lst = "ul"
            out.append(f"<li>{inline(m.group(1))}</li>")
        elif m := re.match(r"\d+[.)]\s+(.*)", s):
            if para:
                flush()
            if lst != "ol":
                flush(); out.append("<ol>"); lst = "ol"
            out.append(f"<li>{inline(m.group(1))}</li>")
        elif s.startswith(">"):
            flush(); out.append(f"<blockquote>{inline(s.lstrip('> '))}</blockquote>")
        else:
            if lst:
                flush()
            para.append(s)
        i += 1
    flush()
    return "\n".join(out)


CSS = """
:root { --ink:#16181d; --ink2:#4a4f5a; --line:#d9dce3; --bg:#ffffff; --panel:#f5f6f8; --accent:#1f5fbf; }
* { box-sizing: border-box; }
body { margin:0; background:var(--bg); color:var(--ink); font:16px/1.55 Georgia, 'Times New Roman', serif; }
main { max-width: 860px; margin: 0 auto; padding: 24px 16px 80px; }
h1 { font: 600 26px/1.2 system-ui, 'Segoe UI', sans-serif; margin: 8px 0 12px; }
h2 { font: 600 20px/1.25 system-ui, 'Segoe UI', sans-serif; margin: 56px 0 8px; padding-top: 18px; border-top: 3px solid var(--ink); }
h3, h4, h5, h6 { font: 600 16px/1.3 system-ui, 'Segoe UI', sans-serif; margin: 18px 0 6px; }
.how, .items { font: 14px/1.5 system-ui, 'Segoe UI', sans-serif; }
.how { background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 12px 16px; }
.how code, .items code { background:#e9ebf0; padding: 1px 5px; border-radius: 4px; font-size: 13px; }
.q { font: 15px/1.5 system-ui, 'Segoe UI', sans-serif; margin: 6px 0 2px; }
.q em { color: var(--ink2); }
.label { font: 600 12px/1 system-ui, 'Segoe UI', sans-serif; letter-spacing: .06em; text-transform: uppercase; color: var(--ink2); margin: 18px 0 6px; }
.answer { border-left: 4px solid var(--accent); padding: 2px 0 2px 16px; overflow-wrap: anywhere; }
table { border-collapse: collapse; width: 100%; margin: 10px 0; font-size: 14px; display: block; overflow-x: auto; }
th, td { border: 1px solid var(--line); padding: 6px 8px; text-align: left; vertical-align: top; }
th { background: var(--panel); font-family: system-ui, 'Segoe UI', sans-serif; }
.items table { display: table; }
.items td:first-child { white-space: nowrap; font-weight: 600; }
nav { font: 14px/1.9 system-ui, 'Segoe UI', sans-serif; margin: 14px 0 0; }
nav a { color: var(--accent); text-decoration: none; margin-right: 10px; white-space: nowrap; }
blockquote { margin: 8px 0; padding: 4px 12px; border-left: 3px solid var(--line); color: var(--ink2); }
@media print { h2 { page-break-before: always; } nav { display: none; } }
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="full")
    a = ap.parse_args()
    blind = ROOT / "results" / a.run / "blind"
    md = (blind / "blind_answers.md").read_text(encoding="utf-8")
    rows = read_sheet(blind / "grading_sheet.csv")
    items: dict = {}
    for r in rows:
        if r["row"].upper() == "ITEM":
            items.setdefault(r["answer_id"].upper(), []).append(r)
    parts = re.split(r"^## (A\d+) - question (\S+)\s*$", md, flags=re.M)
    body, nav = [], []
    for k in range(1, len(parts), 3):
        aid, qid, block = parts[k], parts[k + 1], parts[k + 2]
        m = re.search(r"\*\*Question:\*\*\s*(.*?)\n\s*\n\*\((.*?)\)\*\s*\n\s*\n\*\*Answer:\*\*\s*\n(.*)", block, flags=re.S)
        q_pt, q_en, ans = (m.group(1).strip(), m.group(2).strip(), m.group(3)) if m else ("", "", block)
        ans = re.sub(r"\n---\s*$", "", ans.strip())
        nav.append(f'<a href="#{aid}">{aid}</a>')
        rows_html = "".join(f"<tr><td>{html.escape(aid)} &middot; {html.escape(r['item'])}</td><td>{html.escape(r['status'])}</td>"
                            f"<td>{html.escape(r['checklist_item_or_instruction'])}</td></tr>" for r in items.get(aid, []))
        body.append(
            f'<h2 id="{aid}">{aid} &middot; question {html.escape(qid)}</h2>'
            f'<p class="q"><strong>{html.escape(q_pt)}</strong><br><em>{html.escape(q_en)}</em></p>'
            f'<div class="label">Answer</div><div class="answer">{md_to_html(ans)}</div>'
            f'<div class="label">What to mark in the sheet for {aid}</div><div class="items">'
            f'<table><thead><tr><th>Row</th><th>Status</th><th>Checklist item</th></tr></thead><tbody>{rows_html}'
            f'<tr><td>{aid} &middot; ANSWER</td><td></td><td>Whole answer: number of fabricated claims (one underlying error counts '
            f'once); jurisdiction confusion yes / no</td></tr></tbody></table></div>')
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Blind grading sample</title><style>{CSS}</style></head><body><main>
<h1>Blind grading sample: {len(nav)} answers</h1>
<div class="how">
<p><strong>Two files work together.</strong> This page is for reading: each answer, then the checklist items to grade for it.
Your marks go in <code>grading_sheet.csv</code> (open it in Excel). The code at the start of each row here
(<code>A01 &middot; a</code>) is the same as columns <code>answer_id</code> and <code>item</code> in the sheet.</p>
<p><strong>For each checklist item</strong>, fill two columns:<br>
<code>coverage</code>: <code>covered</code> / <code>partial</code> / <code>not_covered</code><br>
<code>uncertainty</code>: <code>stated_as_certain</code> / <code>flagged</code> / <code>hedged_without_reason</code> / <code>not_addressed</code></p>
<p><strong>For each answer</strong> (the row marked ANSWER), fill two columns:<br>
<code>n_fabricated_claims</code>: a number; one underlying error counts once, however often it is repeated<br>
<code>jurisdiction_confusion</code>: <code>yes</code> / <code>no</code></p>
<p>Grade with <code>rubric.md</code>. The answers come from different models and conditions, in random order; which is which is
not shown. Save the sheet as CSV when you are done.</p>
</div>
<nav>{' '.join(nav)}</nav>
{''.join(body)}
</main></body></html>"""
    (blind / "blind_answers.html").write_text(page, encoding="utf-8")
    print(f"wrote {blind / 'blind_answers.html'}: {len(nav)} answers, {sum(len(v) for v in items.values())} checklist rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
