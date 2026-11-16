#!/usr/bin/env python3
"""What the human grader's blind grades show on their own, and where the judges differ from her.

    python scripts/human_results.py [--run full]

Reads   results/<run>/blind/grading_sheet.csv      (her marks; see scripts/import_human_grades.py)
        results/<run>/blind/KEY_do_not_send.json   (which model and condition each answer came from)
        results/<run>/answers.jsonl, judgments.jsonl
Writes  results/<run>/blind/human_results.md and human_vs_judges.csv

Nothing here re-grades anything. The one table that is not a count of her marks is the legal-basis
table (LEGAL_BASIS below): it is OUR coding of the legal basis she names in her notes for each
answer, written out per answer so that anyone can check it against the sheet.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from nis2eval.blind import read_sheet  # noqa: E402
from nis2eval.runner import latest_ok, read_jsonl  # noqa: E402

JUDGES = ("qwen3.8-27b", "gemma-4-31b-it")
CONDS = ("C0", "C1", "C2")
COV = {"covered": 1.0, "partial": 0.5, "not_covered": 0.0}

# Our coding of the grader's notes: the legal basis each answer actually rests on, as she describes it.
#   directive   = Directive (EU) 2022/2555 applied as the legal basis in Portugal
#   other_law   = a statute named as the NIS 2 transposition or as the law in force that is not it
#                 (either it does not exist or it is about something else)
#   repealed    = Lei n.º 46/2018 (the regime the decree-law repealed) applied as the law in force
#   decree      = Decreto-Lei n.º 125/2025
#   regulation  = a claim about CNCS Regulation n.º 756/2026 (that it is not yet published/approved)
LEGAL_BASIS = {
    "A01": {"decree"}, "A02": {"directive"}, "A03": {"directive"}, "A04": {"other_law"},
    "A05": {"decree"}, "A06": {"other_law"}, "A07": {"decree"}, "A08": {"decree"}, "A09": {"decree"},
    "A10": {"directive"}, "A11": {"decree"}, "A12": {"directive"}, "A13": {"repealed"},
    "A14": {"decree"}, "A15": {"directive"}, "A16": {"decree", "regulation"}, "A17": {"directive"},
    "A18": {"directive"}, "A19": {"other_law"}, "A20": {"repealed", "other_law"},
    "A21": {"directive", "other_law"}, "A22": {"repealed", "other_law"}, "A23": {"decree", "regulation"},
    "A24": {"directive", "other_law"}, "A25": {"repealed", "other_law"},
}


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="full")
    a = ap.parse_args()
    run = ROOT / "results" / a.run
    blind = run / "blind"
    key = json.loads((blind / "KEY_do_not_send.json").read_text(encoding="utf-8"))
    rows = read_sheet(blind / "grading_sheet.csv")
    answers = {x["key"]: x for x in latest_ok(run / "answers.jsonl")}
    sha = {k: hashlib.sha1(x["answer"].encode("utf-8")).hexdigest()[:12] for k, x in answers.items()}
    judg = {}
    for r in read_jsonl(run / "judgments.jsonl"):
        if (r.get("status") == "ok" and r["judge_model"] in JUDGES
                and r.get("answer_sha", sha.get(r["key"])) == sha.get(r["key"])):
            judg[(r["judge_model"], r["key"])] = r["judgment"]

    per = []
    for aid in sorted(key):
        k = key[aid]
        rs = [r for r in rows if r["answer_id"].upper() == aid]
        items = [r for r in rs if r["row"].upper() == "ITEM"]
        ans = next(r for r in rs if r["row"].upper() == "ANSWER")
        fab = int(float(ans["n_fabricated_claims"] or 0))
        rec = {"answer_id": aid, "model": k["model"], "condition": k["condition"], "question": k["qid"],
               "human_coverage": sum(COV.get(r["coverage"].lower(), 0.0) for r in items) / len(items),
               "human_claims": fab, "human_any_claim": int(fab > 0),
               "human_jurisdiction": int(ans["jurisdiction_confusion"].lower().startswith("y")),
               "legal_basis": "+".join(sorted(LEGAL_BASIS.get(aid, set())))}
        for j in JUDGES:
            g = judg[(j, k["key"])]
            short = j.split("-")[0]
            rec[f"{short}_coverage"] = sum({"covered": 1.0, "partial": 0.5}.get(i["coverage"], 0.0) for i in g["items"]) / len(g["items"])
            rec[f"{short}_claims"] = len(g["fabricated_claims"])
            rec[f"{short}_any_claim"] = int(len(g["fabricated_claims"]) > 0)
            rec[f"{short}_jurisdiction"] = int(bool(g["jurisdiction_confusion"]))
        per.append(rec)

    with (blind / "human_vs_judges.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(per[0]))
        w.writeheader()
        w.writerows(per)

    def by(cond, field, fmt):
        v = [r[field] for r in per if r["condition"] == cond]
        return fmt(v)
    pct = lambda v: f"{100 * sum(v) / len(v):.0f}%"
    cnt = lambda v: f"{sum(v)} of {len(v)}"
    md = ["# The blind sample: human grades on their own, and against the two judges", "",
          f"{len(per)} answers, drawn before any grading, stratified over models and conditions "
          f"({', '.join(c + ': ' + str(sum(1 for r in per if r['condition'] == c)) for c in CONDS)}). "
          "Graded by the author of the standard, blind to model, condition and the judges' marks.", "",
          "## 1. By condition: the grader and the two judges on the same answers", "",
          "| Mark | Graded by | C0 | C1 | C2 |", "|---|---|---|---|---|"]
    for label, field, fmt in (("Checklist coverage", "coverage", pct),
                              ("Answers with an unsupported claim", "any_claim", cnt),
                              ("Answers with jurisdiction confusion", "jurisdiction", cnt)):
        for who, name in (("human", "grader"), ("qwen3.8", "qwen3.8-27b"), ("gemma", "gemma-4-31b-it")):
            md.append(f"| {label if who == 'human' else ''} | {name} | " + " | ".join(by(c, f"{who}_{field}", fmt) for c in CONDS) + " |")
    md += ["", "## 2. The legal basis the answers rest on (our coding of the grader's notes)", "",
           "| Legal basis named in the grader's notes | C0 | C1 | C2 |", "|---|---|---|---|"]
    for lab, tag in (("The Directive applied as the law in Portugal", "directive"),
                     ("A statute that is not the transposition, named as the law in force", "other_law"),
                     ("The repealed regime (Lei n.º 46/2018)", "repealed"),
                     ("Any of the three above (wrong legal basis)", "wrong"),
                     ("Decreto-Lei n.º 125/2025", "decree"),
                     ("A claim that CNCS Regulation 756/2026 is not yet published", "regulation")):
        cells = []
        for c in CONDS:
            v = [r for r in per if r["condition"] == c]
            hit = [r for r in v if (tag == "wrong" and set(r["legal_basis"].split("+")) & {"directive", "other_law", "repealed"})
                   or tag in r["legal_basis"].split("+")]
            cells.append(f"{len(hit)} of {len(v)}")
        md.append(f"| {lab} | " + " | ".join(cells) + " |")
    md += ["", "## 3. Where a judge and the grader disagree on an answer-level mark", "",
           "| Answer | Condition | Mark | Grader | qwen3.8-27b | gemma-4-31b-it |", "|---|---|---|---|---|---|"]
    for r in per:
        for field, name in (("any_claim", "unsupported claim"), ("jurisdiction", "jurisdiction confusion")):
            vals = [r[f"human_{field}"], r[f"qwen3.8_{field}"], r[f"gemma_{field}"]]
            if len(set(vals)) > 1:
                yn = lambda x: "yes" if x else "no"
                md.append(f"| {r['answer_id']} | {r['condition']} | {name} | {yn(vals[0])} | {yn(vals[1])} | {yn(vals[2])} |")
    tot = lambda f: sum(r[f] for r in per)
    md += ["", f"Unsupported claims counted over the 25 answers: grader {tot('human_claims')}, qwen3.8-27b "
               f"{tot('qwen3.8_claims')}, gemma-4-31b-it {tot('gemma_claims')}.", ""]
    (blind / "human_results.md").write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md))
    return 0


if __name__ == "__main__":
    sys.exit(main())
