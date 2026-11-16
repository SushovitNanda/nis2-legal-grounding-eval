#!/usr/bin/env python3
"""Build the submission report (.docx) from the Apart template, the text in report_text.py and the
result tables on disk.

    python scripts/build_report.py

Reads   Report/apart-submission-template.docx   (the Apart Research template; never modified)
        results/full/RESULTS_tables.md, results/full/judge_agreement.md, results/full/fig_main_result_report.png
        results/full/blind/agreement.<judge>.csv   (only if the blind grades are in)
Writes  Report/NIS2-compliance-advice-report.docx

The template's own paragraphs are used as moulds (title, headings, body, lists), so fonts, sizes,
margins and heading styles are the template's. Tables are filled from the generated result files,
so re-running after `python scripts/refresh_results.py` brings the report up to date.
"""
from __future__ import annotations

import copy
import csv
import re
import sys
from pathlib import Path

import docx
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Inches

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import report_text as T  # noqa: E402

TEMPLATE = ROOT / "Report" / "apart-submission-template.docx"
OUT = ROOT / "Report" / "NIS2-compliance-advice-report.docx"
RUN = ROOT / "results" / "full"
FONT = "Old Standard TT"
JUDGE_MAIN, JUDGE_2 = "qwen3.8-27b", "gemma-4-31b-it"


# ---------------------------------------------------------------- reading the generated results
def md_tables(path: Path) -> dict:
    """{section heading: [table, ...]} where a table is a list of rows (lists of cell strings)."""
    out, sec, cur = {}, "", None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            sec, cur = line[3:].strip(), None
        elif line.startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if all(re.fullmatch(r":?-+:?", c) for c in cells):
                continue
            if cur is None:
                cur = []
                out.setdefault(sec, []).append(cur)
            cur.append(cells)
        else:
            cur = None
    return out


def section(tables: dict, prefix: str) -> list:
    for k, v in tables.items():
        if k.startswith(prefix):
            return v
    return []


def human_agreement() -> dict:
    """{judge: {metric: (kappa, raw, n)}} if the blind grades have been scored."""
    out = {}
    for j in (JUDGE_MAIN, JUDGE_2):
        p = RUN / "blind" / f"agreement.{j}.csv"
        if p.exists():
            with p.open(encoding="utf-8") as f:
                out[j] = {r["metric"]: (float(r["kappa"]), float(r["raw_agreement"]), int(r["n"])) for r in csv.DictReader(f)}
    return out


# ---------------------------------------------------------------- building blocks
def rpr(bold=None, italic=None, size=None, sup=False) -> str:
    x = f'<w:rFonts w:ascii="{FONT}" w:cs="{FONT}" w:eastAsia="{FONT}" w:hAnsi="{FONT}"/>'
    if bold:
        x += '<w:b w:val="1"/><w:bCs w:val="1"/>'
    if italic:
        x += '<w:i w:val="1"/><w:iCs w:val="1"/>'
    if size:
        x += f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>'
    if sup:
        x += '<w:vertAlign w:val="superscript"/>'
    return f"<w:rPr>{x}</w:rPr>"


def esc(t: str) -> str:
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def runs_xml(text: str, size=None, bold=False, italic=False) -> str:
    """Inline marks in the text: **bold**, *italic*."""
    out = []
    for part in re.split(r"(\*\*.+?\*\*|\*.+?\*)", text):
        if not part:
            continue
        b, i = bold, italic
        if part.startswith("**") and part.endswith("**") and len(part) > 4:
            part, b = part[2:-2], True
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            part, i = part[1:-1], True
        out.append(f'<w:r>{rpr(b, i, size)}<w:t xml:space="preserve">{esc(part)}</w:t></w:r>')
    return "".join(out)


def para(text: str, size=None, after=90, before=0, align=None, bold=False, italic=False, keep_next=False, ind_left=0):
    ppr = ("<w:keepNext/>" if keep_next else "") + f'<w:spacing w:before="{before}" w:after="{after}"/>'
    if ind_left:
        ppr += f'<w:ind w:left="{ind_left}"/>'
    if align:
        ppr += f'<w:jc w:val="{align}"/>'
    return parse_xml(f'<w:p {nsdecls("w")}><w:pPr>{ppr}</w:pPr>{runs_xml(text, size, bold, italic)}</w:p>')


def from_mould(mould, text: str, size=None):
    """A copy of a template paragraph (its style, numbering, indents) with new text."""
    p = copy.deepcopy(mould)
    first = p.find(qn("w:r"))
    base = copy.deepcopy(first.find(qn("w:rPr"))) if first is not None and first.find(qn("w:rPr")) is not None else None
    for child in list(p):
        if child.tag != qn("w:pPr"):
            p.remove(child)
    is_heading = p.find(qn("w:pPr")) is not None and p.find(qn("w:pPr")).find(qn("w:pStyle")) is not None
    bold = is_heading and base is not None and base.find(qn("w:b")) is not None
    sz = size or (base.find(qn("w:sz")).get(qn("w:val")) if base is not None and base.find(qn("w:sz")) is not None else None)
    for r in parse_xml(f'<w:p {nsdecls("w")}>{runs_xml(text, sz, bold)}</w:p>'):
        p.append(r)
    return p


def table(rows: list, widths: list, size=18, header=True, bold_first_col=False):
    """A plain table: rule above, below and under the header; no vertical lines."""
    total = sum(widths)
    grid = "".join(f'<w:gridCol w:w="{w}"/>' for w in widths)
    trs = []
    for ri, row in enumerate(rows):
        tcs = []
        for ci, cell in enumerate(row):
            borders = '<w:bottom w:val="single" w:sz="6" w:space="0" w:color="000000"/>' if (header and ri == 0) else ""
            b = (header and ri == 0) or (bold_first_col and ci == 0 and ri > 0 and False)
            tcs.append(
                f'<w:tc><w:tcPr><w:tcW w:w="{widths[ci]}" w:type="dxa"/>'
                + (f"<w:tcBorders>{borders}</w:tcBorders>" if borders else "")
                + '<w:tcMar><w:top w:w="30" w:type="dxa"/><w:left w:w="60" w:type="dxa"/><w:bottom w:w="30" w:type="dxa"/>'
                  '<w:right w:w="60" w:type="dxa"/></w:tcMar></w:tcPr>'
                + f'<w:p><w:pPr><w:spacing w:before="0" w:after="0" w:line="240" w:lineRule="auto"/>'
                  f'<w:jc w:val="{"left" if ci == 0 else "center"}"/></w:pPr>{runs_xml(cell, size, bold=b)}</w:p></w:tc>')
        trs.append(f'<w:tr><w:trPr><w:cantSplit/></w:trPr>{"".join(tcs)}</w:tr>')
    xml = (f'<w:tbl {nsdecls("w")}><w:tblPr><w:tblW w:w="{total}" w:type="dxa"/><w:jc w:val="center"/><w:tblBorders>'
           '<w:top w:val="single" w:sz="8" w:space="0" w:color="000000"/><w:bottom w:val="single" w:sz="8" w:space="0" w:color="000000"/>'
           '<w:insideH w:val="single" w:sz="2" w:space="0" w:color="BFBFBF"/></w:tblBorders><w:tblLayout w:type="fixed"/></w:tblPr>'
           f'<w:tblGrid>{grid}</w:tblGrid>{"".join(trs)}</w:tbl>')
    return parse_xml(xml)


def page_break():
    return parse_xml(f'<w:p {nsdecls("w")}><w:r><w:br w:type="page"/></w:r></w:p>')


# ---------------------------------------------------------------- the document
def build() -> Path:
    doc = docx.Document(str(TEMPLATE))
    body = doc.element.body
    blocks = list(body)
    header_tbl = next(b for b in blocks if b.tag == qn("w:tbl"))
    top = [b for b in blocks if b.tag == qn("w:p")]
    text_of = lambda p: "".join(t.text or "" for t in p.iter(qn("w:t")))
    style_of = lambda p: (p.find(qn("w:pPr")).find(qn("w:pStyle")).get(qn("w:val"))
                          if p.find(qn("w:pPr")) is not None and p.find(qn("w:pPr")).find(qn("w:pStyle")) is not None else "")
    numid_of = lambda p: (p.find(qn("w:pPr")).find(qn("w:numPr")).find(qn("w:numId")).get(qn("w:val"))
                          if p.find(qn("w:pPr")) is not None and p.find(qn("w:pPr")).find(qn("w:numPr")) is not None else "")
    m_h2 = copy.deepcopy(next(p for p in top if style_of(p) == "Heading2" and text_of(p).startswith("1. Introduction")))
    m_h3 = copy.deepcopy(next(p for p in top if style_of(p) == "Heading3"))
    m_num = copy.deepcopy(next(p for p in top if numid_of(p) == "5"))           # numbered: contributions
    m_ref = copy.deepcopy(next(p for p in top if numid_of(p) == "1"))           # numbered: references
    m_bul = copy.deepcopy(next(p for p in top if text_of(p).startswith("Code repository")))
    for m in (m_h2, m_h3):
        for bm in list(m.iter(qn("w:bookmarkStart"))) + list(m.iter(qn("w:bookmarkEnd"))):
            bm.getparent().remove(bm)

    # --- title block (inside the template's header table)
    cell_ps = list(header_tbl.iter(qn("w:p")))
    title_p = next(p for p in cell_ps if style_of(p) == "Title")
    for t in title_p.iter(qn("w:t")):
        if t.text and "PROJECT TITLE" in t.text:
            t.text = T.TITLE
    authors = [p for p in cell_ps if text_of(p).startswith("Author name")]
    for p, (name, aff) in zip(authors, T.AUTHORS):
        r = p.find(qn("w:r"))
        ts = r.findall(qn("w:t"))
        ts[0].text = name
        if aff:
            ts[1].text = aff
        else:                                   # no affiliation given: drop the line break and the second line
            for el in list(r):
                if el.tag in (qn("w:br"),) or el is ts[1]:
                    r.remove(el)
    # The authors sit in a nested table of 2 rows x 3 cells. A cell may not be left empty, so unused
    # rows and cells are removed whole (and one grid column per removed cell), keeping the rest centred.
    a_tbl = authors[0].getparent().getparent().getparent()
    rows = a_tbl.findall(qn("w:tr"))
    per_row = len(rows[0].findall(qn("w:tc")))
    n = len(T.AUTHORS)
    need_rows = (n + per_row - 1) // per_row
    for r in rows[need_rows:]:
        a_tbl.remove(r)
    if n < per_row:
        for c in rows[0].findall(qn("w:tc"))[n:]:
            rows[0].remove(c)
        cols = a_tbl.find(qn("w:tblGrid")).findall(qn("w:gridCol"))
        for g in cols[n:per_row]:
            g.getparent().remove(g)
    grid = a_tbl.find(qn("w:tblGrid"))
    for ch in list(grid):
        if ch.tag != qn("w:gridCol"):
            grid.remove(ch)                      # the template's record of an earlier grid
    cell_w = 3800
    used = min(n, per_row)
    for g in grid.findall(qn("w:gridCol")):
        g.set(qn("w:w"), str(cell_w))
    tblw = a_tbl.find(qn("w:tblPr")).find(qn("w:tblW"))
    tblw.set(qn("w:w"), str(cell_w * used))
    for tc in a_tbl.iter(qn("w:tc")):
        tcpr = tc.find(qn("w:tcPr"))
        if tcpr.find(qn("w:tcW")) is None:
            tcpr.insert(0, parse_xml(f'<w:tcW {nsdecls("w")} w:w="{cell_w}" w:type="dxa"/>'))
    abstract_p = next(p for p in cell_ps if text_of(p).startswith("Summarize your project"))
    for child in list(abstract_p):
        if child.tag != qn("w:pPr"):
            abstract_p.remove(child)
    ppr = abstract_p.find(qn("w:pPr"))
    for u in list(ppr.iter(qn("w:u"))):
        u.getparent().remove(u)
    for r in parse_xml(f'<w:p {nsdecls("w")}>{runs_xml(T.ABSTRACT)}</w:p>'):
        abstract_p.append(r)

    # --- remove everything after the header table (guidance box and guidance text), keep page setup
    seen = False
    for b in blocks:
        if b is header_tbl:
            seen = True
            continue
        if seen and b.tag != qn("w:sectPr"):
            body.remove(b)
    sect = body.find(qn("w:sectPr"))
    add = sect.addprevious

    tables = md_tables(RUN / "RESULTS_tables.md")
    done = re.search(r"(\d+) answers graded so far \(target (\d+) per model\)", (RUN / "RESULTS_tables.md").read_text(encoding="utf-8"))
    supp_complete = bool(done) and int(done.group(1)) >= int(done.group(2))
    if not supp_complete:        # leave a half-finished model out of the per-model tables
        for key, tbs in tables.items():
            if key.startswith("5. Per model"):
                for tb in tbs:
                    tb[:] = [r for r in tb if not r[0].startswith(T.SUPPLEMENTARY_MODEL)]
    agree = md_tables(RUN / "judge_agreement.md")
    hpath = RUN / "blind" / "human_results.md"
    htables = md_tables(hpath) if hpath.exists() else {}
    human = human_agreement()

    def h2(t): add(from_mould(m_h2, t))
    def h3(t): add(from_mould(m_h3, t))
    def body_text(paragraphs, size=None):
        for t in paragraphs:
            add(para(t, size=size))

    def caption(t): add(para(t, size=19, after=160, before=60))

    def emit(items):
        for kind, payload in items:
            if kind == "p":
                add(para(payload))
            elif kind == "num":
                for t in payload:
                    add(from_mould(m_num, t))
                add(para("", after=0, size=8))
            elif kind == "bul":
                for t in payload:
                    add(from_mould(m_bul, t))
                add(para("", after=0, size=8))
            elif kind == "h3":
                h3(payload)
            elif kind == "fig":
                p = doc.add_paragraph()
                p.alignment = 1
                p.add_run().add_picture(str(RUN / "fig_main_result_report.png"), width=Inches(6.5))
                p.paragraph_format.space_after = 0
                p.paragraph_format.keep_with_next = True
                add(p._p)
                caption(payload)
            elif kind == "table_main":
                src = section(tables, "1. Main result")[0]
                keep = ["Checklist coverage", "Answers with at least one unsupported claim", "Unsupported claims per answer",
                        "Answers with jurisdiction confusion", "Uncertain items properly flagged",
                        "Says the decree does not settle the point", "Says the text given is not the Portuguese law"]
                rows = [["", "C0: question only", "C1: decree-law", "C2: Directive instead"]]
                for want in keep:
                    r = next(r for r in src[1:] if r[0].startswith(want))
                    rows.append([T.ROW_LABELS.get(want, r[0])] + r[1:])
                add(para(payload, size=19, after=60, before=80, keep_next=True))
                add(table(rows, [3660, 1900, 1900, 1900]))
                add(para("", after=60, size=8))
            elif kind == "table_agreement":
                a = section(agree, "All answers graded by both")[0]
                pick = [("Item coverage (3 levels, linear-weighted)", "Checklist item covered (3 levels, weighted)", "coverage (linear-weighted)"),
                        ("Uncertainty mark", "Uncertainty mark on uncertain items", "uncertainty"),
                        ("Answer has an unsupported claim", "Answer has an unsupported claim", "fab_any"),
                        ("Jurisdiction confusion", "Jurisdiction confusion", "jurisdiction"),
                        ("Says the decree does not settle", "Says the decree does not settle the point", None)]
                head = ["Mark", "Judge vs judge: kappa (agreement), 792 answers"]
                if human:
                    head += [f"{JUDGE_MAIN} vs human", f"{JUDGE_2} vs human"]
                rows = [head]
                for pref, label, hkey in pick:
                    r = next(r for r in a[1:] if r[0].startswith(pref))
                    row = [label, f"{r[1]} ({100 * float(r[2]):.0f}%)"]
                    if human:
                        for j in (JUDGE_MAIN, JUDGE_2):
                            v = human.get(j, {}).get(hkey) if hkey else None
                            row.append(f"{v[0]:.2f} ({100 * v[1]:.0f}%), n={v[2]}" if v and v[0] == v[0] else "n/a")
                    rows.append(row)
                add(para(payload if human else T.TABLE2_CAPTION_NO_HUMAN, size=19, after=60, before=80, keep_next=True))
                add(table(rows, [3360, 2000, 2000, 2000] if human else [4680, 4680]))
                add(para("", after=60, size=8))
            elif kind == "md_table":
                prefix, idx, cap, widths, size = payload
                tb = section(tables, prefix)
                if len(tb) > idx:
                    add(para(cap, size=19, after=60, before=80, keep_next=True))
                    add(table(tb[idx], widths, size=size))
                    add(para("", after=60, size=8))
            elif kind == "hmd_table":
                prefix, idx, cap, widths, size = payload
                tb = section(htables, prefix)
                if len(tb) > idx:
                    add(para(cap, size=19, after=60, before=80, keep_next=True))
                    add(table(tb[idx], widths, size=size))
                    add(para("", after=60, size=8))
            elif kind == "human":
                add(para(T.human_paragraph(human)))
            elif kind == "small":
                add(para(payload, size=20))
            elif kind == "mono":
                for line in payload:
                    add(para(line, size=19, after=40, ind_left=360))

    for title, items in T.SECTIONS:
        h2(title)
        emit(items)

    # --- everything below is outside the 8 pages
    # References start a new page: the break belongs to the heading itself, so a full last page of main
    # text cannot push an empty page in between.
    ref_h = from_mould(m_h2, "References")
    ref_h.find(qn("w:pPr")).find(qn("w:pStyle")).addnext(parse_xml(f'<w:pageBreakBefore {nsdecls("w")}/>'))
    add(ref_h)
    for ref in T.REFERENCES:
        add(from_mould(m_ref, ref, size=20))
    h2("Appendix")
    emit(T.appendix(tables, supp_complete, bool(human) and bool(htables)))
    h2("LLM Usage Statement")
    body_text(T.LLM_USAGE)

    OUT.parent.mkdir(exist_ok=True)
    doc.save(str(OUT))
    return OUT


if __name__ == "__main__":
    print("wrote", build())
