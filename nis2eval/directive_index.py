"""Index of Directive (EU) 2022/2555 (NIS 2): article > paragraph > point > sub-point.

Built from the Portuguese text used in condition C2 (data/directive/directive-2022-2555-pt.txt)
and cross-checked against the official English PDF supplied by Bia
(data/directive/Directive-EU-2022-2555-NIS2-en.pdf -> directive-2022-2555-en.txt).

Two uses:
  * the citation check can say whether a provision an answer attributes to the Directive exists
    (an invented directive article is a different error from a real one applied as Portuguese law);
  * `crosscheck()` confirms that the C2 text has the same 46 articles and the same numbered
    paragraphs as the official English version.

The index has the same shape as the decree index, with one section, "diretiva", so DecreeIndex
can read it.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from . import paths
from .decree_index import DecreeIndex, _is_subpoint

ART = {"pt": re.compile(r"^Artigo (\d+)\.º$"), "en": re.compile(r"^Article (\d+)$")}
END = {"pt": re.compile(r"^Feito em Estrasburgo"), "en": re.compile(r"^Done at Strasbourg")}
STRUCT = {"pt": re.compile(r"^CAPÍTULO [IVXLC]+$"), "en": re.compile(r"^CHAPTER [IVXLC]+$")}
PAR_RE = re.compile(r"^(\d{1,2})\.\s+\S")
POINT_RE = {"pt": re.compile(r"^([a-z]{1,2}|[ivx]{1,4})\)(?:\s|$)"), "en": re.compile(r"^\(([a-z]{1,2}|[ivx]{1,4})\)(?:\s|$)")}


def build_directive_index(txt_path: Path | None = None, lang: str = "pt") -> dict:
    txt_path = txt_path or (paths.DIRECTIVE_TXT if lang == "pt" else paths.DIRECTIVE_TXT_EN)
    arts: dict = {}
    art = par = point = sub = None
    want_title = skip_next = False
    prev = ""
    for raw in txt_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        if END[lang].match(line):
            break
        m = ART[lang].match(line)
        if m:
            art = arts.setdefault(m.group(1), {"title": "", "text": "", "paragraphs": {}})
            par = point = sub = None
            want_title = True
            prev = line
            continue
        if STRUCT[lang].match(line):
            art = par = point = sub = None
            skip_next = True  # the chapter title
            continue
        if skip_next:
            skip_next = False
            continue
        if art is None:
            continue
        if want_title:
            art["title"] = line
            want_title = False
            prev = line
            continue
        art["text"] += line + "\n"
        mp = PAR_RE.match(line)
        mpt = POINT_RE[lang].match(line)
        numbered = [int(k) for k in art["paragraphs"] if k != "0"]
        expected = (max(numbered) + 1) if numbered else 1
        if mp and int(mp.group(1)) == expected:
            par = art["paragraphs"].setdefault(mp.group(1), {"text": "", "points": {}})
            point = sub = None
            par["text"] += line + "\n"
        elif mpt:
            tok = mpt.group(1)
            if par is None:
                par = art["paragraphs"].setdefault("0", {"text": "", "points": {}})
            if _is_subpoint(tok, point["_id"] if point else None, sub["_id"] if sub else None, prev):
                sub = point["subpoints"].setdefault(tok, {"text": "", "_id": tok})
                sub["text"] += line + "\n"
                point["text"] += line + "\n"
            else:
                point = par["points"].setdefault(tok, {"text": "", "_id": tok, "subpoints": {}})
                sub = None
                point["text"] += line + "\n"
            par["text"] += line + "\n"
        else:
            if par is None:
                par = art["paragraphs"].setdefault("0", {"text": "", "points": {}})
            par["text"] += line + "\n"
            if sub is not None:
                sub["text"] += line + "\n"
                point["text"] += line + "\n"
            elif point is not None:
                point["text"] += line + "\n"
        prev = line

    def clean(d):
        if isinstance(d, dict):
            d.pop("_id", None)
            for v in d.values():
                clean(v)
            if isinstance(d.get("text"), str):
                d["text"] = d["text"].strip()
    clean(arts)
    return {
        "meta": {"source": "Directive (EU) 2022/2555 (NIS 2), OJ L 333, 27.12.2022, p. 80", "lang": lang,
                 "built_from": txt_path.name},
        "sections": {"diretiva": {"label": "Directive (EU) 2022/2555 (NIS 2)", "articles": arts}},
    }


def shape(index: dict) -> dict:
    """{article: [numbered paragraphs]} - what the two language versions must share."""
    return {a: sorted(int(p) for p in v["paragraphs"] if p != "0")
            for a, v in index["sections"]["diretiva"]["articles"].items()}


def crosscheck(log=print) -> list[str]:
    """Compare the Portuguese C2 text with the official English PDF text. Returns the differences."""
    pt, en = shape(build_directive_index(lang="pt")), shape(build_directive_index(lang="en"))
    diffs = [f"article {a}: only in {'PT' if a in pt else 'EN'}" for a in sorted(set(pt) ^ set(en), key=int)]
    diffs += [f"article {a}: paragraphs PT {pt[a]} vs EN {en[a]}" for a in sorted(set(pt) & set(en), key=int) if pt[a] != en[a]]
    log(f"directive: {len(pt)} articles in the Portuguese text, {len(en)} in the English PDF text; "
        f"{sum(len(v) for v in pt.values())} vs {sum(len(v) for v in en.values())} numbered paragraphs; {len(diffs)} differences")
    for d in diffs:
        log("  " + d)
    return diffs


_cached = None


def load_directive_index() -> DecreeIndex | None:
    """The directive index, or None when the directive text is not in the repository."""
    global _cached
    if _cached is None:
        if paths.DIRECTIVE_INDEX.exists():
            _cached = DecreeIndex(json.loads(paths.DIRECTIVE_INDEX.read_text(encoding="utf-8")))
        elif paths.DIRECTIVE_TXT.exists():
            data = build_directive_index()
            paths.DIRECTIVE_INDEX.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
            _cached = DecreeIndex(data)
        else:
            return None
    return _cached
