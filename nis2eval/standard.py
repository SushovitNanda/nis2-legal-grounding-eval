from __future__ import annotations

import json
import re
from pathlib import Path

from . import paths

STATUSES = ("verified", "inferred", "to confirm", "proposal")


def load_standard(path: Path = paths.STANDARD) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def questions(std: dict, ids=None, batch=None) -> list[dict]:
    qs = std["questions"]
    if batch:
        qs = [q for q in qs if q.get("batch") == batch]
    if ids:
        qs = [q for q in qs if q["id"] in set(ids)]
    return qs


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def _page_variants(page: str) -> tuple[str, str]:
    """A page of the extracted decree with words split at line ends put back together.

    The PDF breaks words at the end of a line ("disponibili-\\nzação"); the evidence excerpts
    are written without the break. Two variants, because a line can also end on a real hyphen.
    """
    return (_norm(re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", page)),
            _norm(re.sub(r"(\w)-\s*\n\s*(\w)", r"\1-\2", page)))


def check_evidence(std: dict, decree_txt: Path = paths.DECREE_TXT) -> list[str]:
    """Each citation's 'evidence' excerpt must appear on its page of the official text.

    Same test as data/standard/source/check_citations.py (written by the author of the
    standard), run on our own extraction of the PDF. Pages are separated by form feeds.
    """
    pages = [_page_variants(p) for p in Path(decree_txt).read_text(encoding="utf-8").split("\f")]
    problems = []
    for q in std["questions"]:
        for it in q.get("items", []):
            for c in it.get("citations", []):
                ev = c.get("evidence")
                if not ev:
                    continue
                pg = c.get("page") or 0
                if not (1 <= pg <= len(pages)) or not any(_norm(ev) in v for v in pages[pg - 1]):
                    problems.append(f"{q['id']}/{it['id']}: evidence for {c['raw']} not found on p. {pg}")
    return problems


def validate(std: dict, index) -> list[str]:
    """Schema + citation check. Returns a list of problems (empty = OK)."""
    problems = check_evidence(std) if paths.DECREE_TXT.exists() else []
    seen = set()
    for q in std["questions"]:
        qid = q.get("id", "?")
        if qid in seen:
            problems.append(f"{qid}: duplicate id")
        seen.add(qid)
        for f in ("question_en", "question_pt", "items"):
            if not q.get(f):
                problems.append(f"{qid}: missing {f}")
        for it in q.get("items", []):
            tag = f"{qid}/{it.get('id')}"
            if it.get("status") not in STATUSES:
                problems.append(f"{tag}: bad status {it.get('status')!r}")
            if not it.get("text_en"):
                problems.append(f"{tag}: empty text")
            for c in it.get("citations", []):
                for p in (c.get("paragraphs") or [None]):
                    for pt in (c.get("points") or [None]):
                        node, level = index.lookup(c["source"], c["article"], p, pt, c.get("subpoint") if pt else None)
                        want = "subpoint" if (c.get("subpoint") and pt) else "point" if pt else "paragraph" if p else "article"
                        if node is None or level != want:
                            problems.append(f"{tag}: {c['raw']} not found in {c['source']} (reached {level})")
                        elif c.get("page") and not (node["page"] - 1 <= c["page"] <= node.get("page_end", node["page"]) + 1):
                            problems.append(f"{tag}: {c['raw']} page {c['page']} but unit starts on p. {node['page']}")
    return problems
