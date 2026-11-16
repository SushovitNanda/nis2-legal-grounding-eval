"""Index of Decreto-Lei n.º 125/2025: article > paragraph (n.º) > point (alínea) > sub-point.

The decree-law has two bodies that both start at "Artigo 1.º":
  * "decreto"   - the decree-law's own 11 articles (pp. 2-7)
  * "regime"    - the annexed Regime Jurídico da Cibersegurança, arts. 1-87 (pp. 8-60)
plus Annexes I-III (Annex III has its own arts. 1-2: the SME definition).
Keeping them apart matters: "art. 10.º" of the decree and of the regime are different rules.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from . import paths

HEADER_LINES = re.compile(r"^(1\.ª série|N\.º 234|04-12-2025|\d{1,2}/65|Decreto-Lei n\.º 125/2025)$")
ART_RE = re.compile(r"^Artigo (\d+)\.º(-[A-Z])?$")
PAR_RE = re.compile(r"^(\d{1,2}) [—–-] ")
POINT_RE = re.compile(r"^([a-z]{1,2})\) ")
STRUCT_RE = re.compile(r"^(TÍTULO|CAPÍTULO|SECÇÃO|SUBSECÇÃO) [IVXLC]+$")
ROMANS = ["i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x", "xi", "xii"]
SECTION_MARKS = {"ANEXO": "regime", "ANEXO I": "anexo_i", "ANEXO II": "anexo_ii", "ANEXO III": "anexo_iii"}
SECTION_LABELS = {
    "decreto": "Decreto-Lei n.º 125/2025 (articles of the decree-law itself)",
    "regime": "Regime Jurídico da Cibersegurança (annex to DL 125/2025)",
    "anexo_i": "Annex I - sectors of high criticality",
    "anexo_ii": "Annex II - other critical sectors",
    "anexo_iii": "Annex III - SME definition",
}


def _is_subpoint(tok: str, cur_point: str | None, cur_sub: str | None, prev_line: str) -> bool:
    """Decide whether 'i)', 'v)', 'x)' ... opens a sub-point (subalínea) or is an alínea."""
    if tok not in ROMANS or cur_point is None:
        return False
    if cur_sub is not None:  # inside a run of sub-points: is it the next roman numeral?
        nxt = ROMANS.index(cur_sub) + 1
        return nxt < len(ROMANS) and ROMANS[nxt] == tok
    if tok != "i":
        return False
    # 'i)' right after alínea h) is alínea i), unless the previous line opens a list
    if cur_point == "h" and not prev_line.rstrip().endswith(":"):
        return False
    return prev_line.rstrip().endswith(":")


def build_index(txt_path: Path = paths.DECREE_TXT) -> dict:
    pages = txt_path.read_text(encoding="utf-8").split("\f")
    sections: dict = {k: {"label": v, "articles": {}} for k, v in SECTION_LABELS.items()}
    annex_text: dict = {}
    section = None
    art = par = point = sub = None
    skip_title = False
    prev_line = ""
    done = False

    def node(page):
        return {"page": page, "text": ""}

    for pno, page in enumerate(pages, start=1):
        if done:
            break
        for raw in page.splitlines():
            line = raw.strip()
            if not line or HEADER_LINES.match(line):
                continue
            if line in SECTION_MARKS and (SECTION_MARKS[line] != "regime" or section == "decreto"):
                section = SECTION_MARKS[line]
                art = par = point = sub = None
                annex_text.setdefault(section, {"page": pno, "text": ""})
                skip_title = False
                prev_line = line
                continue
            if section in annex_text and section != "regime":
                annex_text[section]["text"] += line + "\n"
            m = ART_RE.match(line)
            if m:
                if section is None:
                    section = "decreto"
                art = sections[section]["articles"].setdefault(
                    m.group(1) + (m.group(2) or ""), {"page": pno, "title": "", "text": "", "paragraphs": {}}
                )
                par = point = sub = None
                skip_title = "title"
                prev_line = line
                continue
            if section is None:
                continue  # preamble
            if skip_title == "title" and art is not None:
                art["title"] = line
                skip_title = False
                prev_line = line
                continue
            if skip_title == "struct":
                skip_title = False
                continue
            if STRUCT_RE.match(line):
                skip_title = "struct"
                art = par = point = sub = None
                continue
            if section == "decreto" and line.startswith("Visto e aprovado em Conselho de Ministros"):
                art = par = point = sub = None
                continue
            if art is None:
                continue
            art["text"] += line + "\n"
            art["page_end"] = pno
            mp = PAR_RE.match(line)
            mpt = POINT_RE.match(line)
            numbered = [int(k) for k in art["paragraphs"] if k != "0"]
            expected = (max(numbered) + 1) if numbered else 1
            if mp and int(mp.group(1)) == expected:  # "2 — ..." only counts if it is the next n.º
                par = art["paragraphs"].setdefault(mp.group(1), {**node(pno), "points": {}})
                point = sub = None
                par["text"] += line + "\n"
            elif mpt:
                tok = mpt.group(1)
                if par is None:
                    par = art["paragraphs"].setdefault("0", {**node(art["page"]), "points": {}})
                if _is_subpoint(tok, point["_id"] if point else None, sub["_id"] if sub else None, prev_line):
                    sub = point["subpoints"].setdefault(tok, {**node(pno), "_id": tok})
                    sub["text"] += line + "\n"
                    point["text"] += line + "\n"
                else:
                    point = par["points"].setdefault(tok, {**node(pno), "_id": tok, "subpoints": {}})
                    sub = None
                    point["text"] += line + "\n"
                par["text"] += line + "\n"
            else:
                if par is None:
                    par = art["paragraphs"].setdefault("0", {**node(pno), "points": {}})
                par["text"] += line + "\n"
                if sub is not None:
                    sub["text"] += line + "\n"
                    point["text"] += line + "\n"
                elif point is not None:
                    point["text"] += line + "\n"
            prev_line = line

    def clean(d):
        if isinstance(d, dict):
            d.pop("_id", None)
            for v in d.values():
                clean(v)
            if "text" in d and isinstance(d["text"], str):
                d["text"] = d["text"].strip()
    clean(sections)
    for a in annex_text.values():
        a["text"] = a["text"].strip()
    return {
        "meta": {
            "source": "Decreto-Lei n.º 125/2025, de 4 de dezembro (Diário da República, 1.ª série, n.º 234)",
            "pages": len(pages),
            "note": "page = page of the official PDF where the unit starts",
        },
        "sections": {k: v for k, v in sections.items() if v["articles"]},
        "annexes": {k: v for k, v in annex_text.items() if k != "regime"},
    }


class DecreeIndex:
    def __init__(self, data: dict):
        self.data = data
        self.sections = data["sections"]

    @classmethod
    def load(cls, path: Path = paths.DECREE_INDEX) -> "DecreeIndex":
        if not path.exists():
            data = build_index()
            path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
            return cls(data)
        return cls(json.loads(path.read_text(encoding="utf-8")))

    def lookup(self, section: str, article, paragraph=None, point=None, subpoint=None):
        """Return (node, level_reached). level_reached is the deepest level that exists:
        None (article missing), 'article', 'paragraph', 'point', 'subpoint'."""
        arts = self.sections.get(section, {}).get("articles", {})
        a = arts.get(str(article))
        if a is None:
            return None, None
        if paragraph is None and point is None:
            return a, "article"
        pars = a["paragraphs"]
        if paragraph is None:  # point cited without paragraph: accept if unique place
            cands = [p for p in pars.values() if str(point) in p["points"]]
            if not cands:
                return a, "article"
            p = cands[0]
        else:
            p = pars.get(str(paragraph))
            if p is None:
                return a, "article"
            if point is None:
                return p, "paragraph"
        pt = p["points"].get(str(point))
        if pt is None:
            return p, "paragraph"
        if subpoint is None:
            return pt, "point"
        sp = pt.get("subpoints", {}).get(str(subpoint))
        if sp is None:
            return pt, "point"
        return sp, "subpoint"

    def text_of(self, section, article, paragraph=None, point=None, subpoint=None, max_chars=1500) -> str | None:
        n, level = self.lookup(section, article, paragraph, point, subpoint)
        if n is None:
            return None
        t = n["text"]
        return t if len(t) <= max_chars else t[:max_chars] + " […]"

    def n_articles(self, section):
        return len(self.sections.get(section, {}).get("articles", {}))
