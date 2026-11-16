#!/usr/bin/env python3
"""Check every citation in a standard JSON against the decree text.

Usage: python3 check_citations.py standard-draft-en-2026-11-14.json DL-125-2025-NIS2-texto.txt

Each citation has pdf_page and evidence (a literal excerpt of the decree, in Portuguese).
The decree text file has one page per form feed (\\f), matching the pages of the official PDF.
A citation passes when the evidence appears on that page (whitespace normalised).
Exit code 0 = all pass, 1 = at least one miss.
"""
import json, re, sys
std, dl = sys.argv[1], sys.argv[2]
pages = open(dl, encoding="utf-8").read().split("\f")
norm = lambda s: re.sub(r"\s+", " ", s).strip()
d = json.load(open(std, encoding="utf-8"))
n = miss = 0
for q in d["questions"]:
    if not q.get("question_pt"):
        print("NO PORTUGUESE QUESTION", q["id"])
    for it in q["checklist"]:
        for c in it["citations"]:
            n += 1
            ok = 1 <= c["pdf_page"] <= len(pages) and norm(c["evidence"]) in norm(pages[c["pdf_page"] - 1])
            if not ok:
                miss += 1
                print("MISS", it["id"], f"art. {c['article']}", c.get("paragraph"), c.get("point"), f"p. {c['pdf_page']}", c["part"])
print(f"{len(d['questions'])} questions, {sum(len(q['checklist']) for q in d['questions'])} items, {n} citations, {miss} misses")
sys.exit(1 if miss else 0)
