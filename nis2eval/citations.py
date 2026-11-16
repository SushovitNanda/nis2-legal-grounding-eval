"""Parse legal citations out of free text (Portuguese and English forms) and check them
against the decree index.

Handles, among others:
  art. 42.º, n.º 1            artigo 61.º, n.º 1, al. j)        arts. 40.º a 44.º
  art. 32.º, n.os 3 e 4       art. 41.º, n.º 1, als. a) a c)    art. 61.º, n.º 2, al. b) i)
  alínea b) do n.º 1 do artigo 6.º      n.os 1 e 2 do artigo 27.º
  art. 10.º, n.º 2, do decreto          artigo 23.º da Diretiva (UE) 2022/2555
  Article 42(1)               Article 6(1)(e)                   Articles 41 to 44

Source attribution of each citation:
  'decreto'  - explicitly the decree-law's own articles ("do decreto", "of the decree itself")
  'regime'   - explicitly the annexed regime ("do regime", "RJC", "do anexo")
  'dl'       - DL 125/2025 with no further indication (regime first, then decree)
  'diretiva' - Directive (EU) 2022/2555 (NIS 2) -> counted for jurisdiction confusion
  'other'    - any other instrument (CNCS regulation, repealed law, GDPR, DORA...) -> not checked
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict

ORD = r"(?:\s*\.?\s*[º°]|\.o\b)"
ANUM = rf"(\d{{1,3}}){ORD}?(?:-[A-Z]\b)?"
ART_KW = r"(?:artigos?|articles?|arts?\.?)"
ART_RE = re.compile(
    rf"(?<![\w.])(?P<kw>{ART_KW})\s*(?P<first>\d{{1,3}})(?P<ord>{ORD})?(?:-[A-Z]\b)?"
    rf"(?P<rest>(?:\s*(?:,|e|a|ao|to|and|through|until|-|–|—)\s*\d{{1,3}}{ORD}?(?:-[A-Z]\b)?(?!\s*\)))*)",
    re.IGNORECASE,
)
REST_TOK = re.compile(rf"\s*(,|e|a|ao|to|and|through|until|-|–|—)\s*(\d{{1,3}})({ORD})?", re.IGNORECASE)

NLIST = r"\d{1,2}(?:\s*(?:,|e|a|to|and|-|–)\s*(?:n\s*\.?\s*[º°o]\s*)?\d{1,2}(?!\s*(?:\.?\s*[º°]|horas|dias|meses|hours|days|months|%)))*"
PAR_KW = r"(?:n\s*\.?\s*[º°o]\s*s?\.?|n\.?\s*os\.?|números?|nos?\.|paragraphs?|paras?\.?|§)"
PAR_TRAIL = re.compile(rf"\s*,?\s*{PAR_KW}\s*(?P<p>{NLIST})", re.IGNORECASE)
PAR_PAREN = re.compile(r"\s*\((?P<p>\d{1,2})\)(?:\s*\((?P<pt>[a-z]{1,2})\))?(?:\s*\((?P<sub>i{1,3}|iv|v|vi{1,3}|ix|x)\))?")
PLIST = r"\(?[a-z]{1,2}\)(?:\s*(?:,|e|a|to|and|-|–)\s*\(?[a-z]{1,2}\))*"
ROMAN = r"(?:i{1,3}|iv|v|vi{1,3}|ix|x)"
PT_KW = r"(?:als?\.|alíneas?|alineas?|points?|pts?\.|letras?|lit\.)"
PT_TRAIL = re.compile(
    rf"\s*,?\s*(?:e\s+)?{PT_KW}\s*(?P<pts>{PLIST})(?:\s*,?\s*(?:subalíneas?\s*|subpoints?\s*)?(?P<sub>\(?{ROMAN}\)))?",
    re.IGNORECASE,
)
LEAD_RE = re.compile(
    rf"(?:(?:{PT_KW}|subalíneas?)\s*(?P<pts>{PLIST})\s*,?\s*(?:d[oa]s?|of(?:\s+the)?)\s+)?"
    rf"(?:{PAR_KW}\s*(?P<p>{NLIST})\s*,?\s*(?:d[oa]s?|of(?:\s+the)?)\s+)?(?:the\s+)?$",
    re.IGNORECASE,
)

ATTR_AFTER = [
    ("diretiva", re.compile(r"^[\s,]*(?:d[ao]|of(?:\s+the)?|in(?:\s+the)?)?\s*(?:referida\s+|mesma\s+)?(?:(?:Diretiva|Directiva|Directive)\b|(?:Diretiva\s+)?(?:NIS\s*-?\s*2|SRI\s*2)\b)", re.I)),
    ("other", re.compile(r"^[\s,]*(?:d[ao]|of(?:\s+the)?|in(?:\s+the)?)?\s*(?:Regulamento|Regulation|Reg\.|RGPD|GDPR|DORA|CPA|Código|Code\b|Lei\s+n|Law\s+(?:no|n)|Constituição|Recomendação|Recommendation|Instrução|IT\s+n|Portaria|Decreto-Lei\s+n\.?\s*[º°o]?\s*(?!125/2025)\d|Decree-Law\s+(?:no\.?|n\.?[º°o]?)\s*(?!125/2025)\d)", re.I)),
    ("decreto", re.compile(r"^[\s,]*(?:d[oa]|of\s+the)\s+(?:decreto(?!-lei)\b|decreto-lei\s+(?:preambular|de aprovação|em si)|corpo\s+do\s+(?:decreto-lei|diploma)|próprio\s+decreto-lei|articulado\s+do\s+decreto-lei|body\s+of\s+the\s+decree|diploma\s+preambular|parte\s+preambular|decree\s+itself|decree(?!-law)\b|approving\s+decree|preambular)", re.I)),
    ("regime", re.compile(r"^[\s,]*(?:d[oa]|of\s+the|in\s+the)?\s*(?:regime\b|RJC\b|anexo\b|annex(?:ed)?\b|Regime\s+Jurídico)", re.I)),
    ("dl", re.compile(r"^[\s,]*(?:d[oa]|of(?:\s+the)?)?\s*(?:Decreto-Lei|Decree-Law|DL)\s*(?:n\.?\s*[º°o]?\.?|no\.?)?\s*125/2025", re.I)),
]
ATTR_BEFORE = re.compile(r"(?:Diretiva|Directiva|Directive|NIS\s*-?\s*2|SRI\s*2)[^.;:\n]{0,18}$", re.I)
REPEALED_RE = re.compile(r"Lei\s+n\.?\s*[º°o]?\s*46/2018|Law\s+(?:no\.?\s*)?46/2018|Decreto-Lei\s+n\.?\s*[º°o]?\s*65/2021|Decree-Law\s+(?:no\.?\s*)?65/2021", re.I)
NAMES_DL_RE = re.compile(r"125\s*/\s*2025|Regime\s+Jurídico\s+da\s+Cibersegurança|\bRJC\b", re.I)
OTHER_STATUTE_RE = re.compile(r"(?:Decreto-Lei|Decree-Law|\bDL|\bLei|\bLaw)\s*(?:n\.?\s*[º°o]?\.?|no\.?)?\s*(?!125\s*/\s*2025)\d{1,3}(?:-[A-Z])?\s*/\s*\d{4}", re.I)
NAMES_DIRECTIVE_RE = re.compile(r"(?:Diretiva|Directiva|Directive)\s*\(UE\)\s*2022/2555|(?:Diretiva|Directiva|Directive)\s*\(EU\)\s*2022/2555|2022/2555|(?:Diretiva|Directiva)\s+(?:NIS\s*-?\s*2|SRI\s*2)|NIS\s*-?\s*2\s+Directive", re.I)

LETTERS = "abcdefghijklmnopqrstuvwxyz"


def _expand_nums(s: str) -> list[int]:
    toks = re.findall(r"\d{1,3}|,|\be\b|\ba\b|\bto\b|\band\b|-|–", s, flags=re.I)
    out: list[int] = []
    rng = False
    for t in toks:
        if t.isdigit():
            n = int(t)
            if rng and out and n > out[-1] and n - out[-1] < 60:
                out.extend(range(out[-1] + 1, n + 1))
            else:
                out.append(n)
            rng = False
        else:
            rng = t.lower() in ("a", "to", "-", "–")
    return out


def _expand_points(s: str) -> list[str]:
    toks = re.findall(r"\(?([a-z]{1,2})\)|(,|\be\b|\ba\b|\bto\b|\band\b|-|–)", s, flags=re.I)
    out: list[str] = []
    rng = False
    for pt, conn in toks:
        if pt:
            pt = pt.lower()
            if rng and out and len(pt) == 1 and len(out[-1]) == 1 and pt > out[-1]:
                out.extend(LETTERS[LETTERS.index(out[-1]) + 1: LETTERS.index(pt) + 1])
            else:
                out.append(pt)
            rng = False
        else:
            rng = conn.lower() in ("a", "to", "-", "–")
    return out


@dataclass
class Citation:
    raw: str
    start: int
    end: int
    source: str                      # decreto | regime | dl | diretiva | other
    articles: list[int]
    paragraphs: list[int] = field(default_factory=list)
    points: list[str] = field(default_factory=list)
    subpoint: str | None = None

    def refs(self):
        """Flatten to (article, paragraph, point, subpoint) tuples."""
        if len(self.articles) != 1:
            return [(a, None, None, None) for a in self.articles]
        a = self.articles[0]
        pars = self.paragraphs or [None]
        pts = self.points or [None]
        return [(a, p, pt, self.subpoint if pt else None) for p in pars for pt in pts]

    def to_dict(self):
        return asdict(self)


def parse_citations(text: str) -> list[Citation]:
    out: list[Citation] = []
    for m in ART_RE.finditer(text):
        has_ord = bool(m.group("ord"))
        arts = [int(m.group("first"))]
        end = m.end("first") + len(m.group("ord") or "")
        mm = re.match(r"-[A-Z]\b", text[end:])
        if mm:
            end += mm.end()
        pos = 0
        rest = m.group("rest") or ""
        rng_next = False
        while True:
            t = REST_TOK.match(rest, pos)
            if not t:
                break
            conn, num, o = t.group(1).lower(), int(t.group(2)), t.group(3)
            # in Portuguese text, a following number is only an article if it carries the ordinal mark
            if has_ord and not o:
                break
            if not has_ord and conn in (",", "e", "a", "ao") and m.group("kw").lower().startswith("art") and not re.match(r"articles?", m.group("kw"), re.I):
                break
            is_rng = conn in ("a", "ao", "to", "through", "until", "-", "–", "—")
            if is_rng and num > arts[-1] and num - arts[-1] < 60:
                arts.extend(range(arts[-1] + 1, num + 1))
            else:
                arts.append(num)
            pos = t.end()
            end = m.end("first") + len(m.group("ord") or "") + pos if not mm else end + 0
            end = m.start("rest") + pos
        pars: list[int] = []
        pts: list[str] = []
        sub = None
        if len(arts) == 1:
            tail = text[end:]
            t = PAR_PAREN.match(tail)
            if t:
                pars = [int(t.group("p"))]
                if t.group("pt"):
                    pts = [t.group("pt").lower()]
                sub = t.group("sub")
                end += t.end()
                tail = text[end:]
            else:
                t = PAR_TRAIL.match(tail)
                if t:
                    pars = _expand_nums(t.group("p"))
                    end += t.end()
                    tail = text[end:]
            t = PT_TRAIL.match(tail)
            if t and not pts:
                pts = _expand_points(t.group("pts"))
                if t.group("sub"):
                    sub = t.group("sub").strip("()").lower()
                end += t.end()
            start = m.start()
            if not pars and not pts:
                lead = LEAD_RE.search(text[max(0, m.start() - 140): m.start()])
                if lead and (lead.group("p") or lead.group("pts")):
                    if lead.group("p"):
                        pars = _expand_nums(lead.group("p"))
                    if lead.group("pts"):
                        pts = _expand_points(lead.group("pts"))
                    start = max(0, m.start() - 140) + lead.start()
        else:
            start = m.start()
        source = "dl"
        after = text[end: end + 110]
        for name, rx in ATTR_AFTER:
            if rx.match(after):
                source = name
                break
        else:
            if ATTR_BEFORE.search(text[max(0, start - 45): start]):
                source = "diretiva"
        out.append(Citation(text[start:end].strip(" ,"), start, end, source, arts, pars, pts, sub))
    # An answer that never names DL 125/2025 and builds on another national statute (seen in the dry run:
    # "Decreto-Lei n.º 157/2024 ... Artigo 24.º, n.º 2") is not citing our decree: its bare article
    # references belong to that statute. Do not check them against the index, where they can exist by chance.
    # The same holds for an answer built on the Directive (condition C2: the model was given the Directive
    # and cites "artigo 23.º, n.º 4" throughout): those are directive citations, checked against the
    # directive index. The nearest instrument named before the citation decides.
    if not NAMES_DL_RE.search(text):
        marks = sorted([(m.start(), "other") for m in OTHER_STATUTE_RE.finditer(text)]
                       + [(m.start(), "diretiva") for m in NAMES_DIRECTIVE_RE.finditer(text)])
        for c in out:
            if c.source == "dl":
                before = [src for pos, src in marks if pos < c.start]
                if before:
                    c.source = before[-1]
    return out


def check_citation(c: Citation, index, directive=None) -> list[dict]:
    """Check every reference of a citation against the decree index.

    verdict: valid | no_article | no_paragraph | no_point | not_checked
    'ambiguous' is set when the article number exists in both bodies (1-11) and the
    text does not say which one is meant.
    Citations attributed to the Directive stay 'not_checked' for the decree metrics; when a
    directive index is given they also get 'directive_verdict' (does the provision exist in
    Directive (EU) 2022/2555 at all?).
    """
    res = []
    for art, par, pt, sub in c.refs():
        r = {"article": art, "paragraph": par, "point": pt, "subpoint": sub, "source": c.source,
             "raw": c.raw, "resolved": None, "ambiguous": False, "page": None}
        if c.source in ("diretiva", "other"):
            r["verdict"] = "not_checked"
            if c.source == "diretiva" and directive is not None:
                _, level = directive.lookup("diretiva", art, par, pt, None)
                r["directive_verdict"] = ("no_article" if level is None else
                                          "no_paragraph" if par is not None and level == "article" else
                                          "no_point" if pt is not None and level != "point" else "valid")
            res.append(r)
            continue
        order = {"decreto": ["decreto"], "regime": ["regime"], "dl": ["regime", "decreto"]}[c.source]
        best = (-1, None, None, None)
        want = 3 if sub else 2 if pt else 1 if par else 0
        rank = {None: -1, "article": 0, "paragraph": 1, "point": 2, "subpoint": 3}
        for sec in order:
            node, level = index.lookup(sec, art, par, pt, sub)
            got = rank[level]
            if par is None and pt is not None and level == "point":
                got = 2
            if got > best[0]:
                best = (got, sec, node, level)
        got, sec, node, level = best
        if got < 0:
            r["verdict"] = "no_article"
        elif got >= want:
            r["verdict"] = "valid"
        elif got == 0:
            r["verdict"] = "no_paragraph" if par is not None else "no_point"
        else:
            r["verdict"] = "no_point"
        if got >= 0:
            r["resolved"] = sec
            r["page"] = node.get("page")
            if c.source == "dl" and art <= index.n_articles("decreto"):
                r["ambiguous"] = True
        res.append(r)
    return res


def citation_summary(text: str, index, directive="auto") -> dict:
    if directive == "auto":
        from .directive_index import load_directive_index
        directive = load_directive_index()
    cits = parse_citations(text)
    checks = [chk for c in cits for chk in check_citation(c, index, directive)]
    checked = [c for c in checks if c["verdict"] != "not_checked"]
    invalid = [c for c in checked if c["verdict"] != "valid"]
    return {
        "n_citations": len(checks),
        "n_checked": len(checked),
        "n_invalid": len(invalid),
        "n_directive": sum(1 for c in checks if c["source"] == "diretiva"),
        "n_directive_invalid": sum(1 for c in checks if c.get("directive_verdict") not in (None, "valid")),
        "n_other": sum(1 for c in checks if c["source"] == "other"),
        "n_ambiguous": sum(1 for c in checked if c["ambiguous"]),
        "mentions_repealed": bool(REPEALED_RE.search(text)),
        "invalid": invalid,
        "checks": checks,
    }
