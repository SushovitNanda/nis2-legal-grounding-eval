#!/usr/bin/env python3
"""Bring the human grader's filled sheet into the shape the agreement code expects.

    python scripts/import_human_grades.py [path/to/filled_sheet.csv]

Default input: results/full/blind/human/Grades_Final_CSV.csv (the file as the grader returned it).
Output:        results/full/blind/grading_sheet.csv (UTF-8), which `nis2eval agreement` reads.

What it changes, and nothing else:
  - reads the file in whatever encoding Excel saved it (Windows-1252 here) and writes UTF-8;
  - drops the empty rows Excel appended;
  - the answer-level marks (n_fabricated_claims, jurisdiction_confusion) belong on the ANSWER row.
    The grader sometimes entered them on the first checklist row of the answer instead. They are
    moved to the ANSWER row; if both places hold a value, the ANSWER row wins and the case is listed.
Every mark, value and note is otherwise copied unchanged; the original file is kept next to it.
"""
from __future__ import annotations

import csv
import sys
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from nis2eval.blind import SHEET_COLS, read_sheet  # noqa: E402

BLIND = ROOT / "results" / "full" / "blind"
DEFAULT_IN = BLIND / "human" / "Grades_Final_CSV.csv"
OUT = BLIND / "grading_sheet.csv"
ANSWER_LEVEL = ("n_fabricated_claims", "jurisdiction_confusion")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_IN
    rows = [r for r in read_sheet(src) if r.get("answer_id")]
    by_answer: "OrderedDict[str, list]" = OrderedDict()
    for r in rows:
        by_answer.setdefault(r["answer_id"].upper(), []).append(r)
    moved, conflicts = [], []
    for aid, rs in by_answer.items():
        ans = next((r for r in rs if r["row"].upper() == "ANSWER"), None)
        if ans is None:
            print(f"!! {aid}: no ANSWER row")
            continue
        for col in ANSWER_LEVEL:
            on_items = [r[col] for r in rs if r["row"].upper() == "ITEM" and r.get(col, "")]
            if ans.get(col, ""):
                if on_items and any(v.lower() != ans[col].lower() for v in on_items):
                    conflicts.append(f"{aid} {col}: ANSWER row {ans[col]!r}, item rows {on_items}")
            elif on_items:
                ans[col] = on_items[0]
                moved.append(f"{aid} {col} = {on_items[0]!r}")
            for r in rs:
                if r["row"].upper() == "ITEM":
                    r[col] = ""
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=SHEET_COLS, extrasaction="ignore")
        w.writeheader()
        for rs in by_answer.values():
            for r in rs:
                w.writerow({c: r.get(c, "") for c in SHEET_COLS})
    n_items = sum(1 for r in rows if r["row"].upper() == "ITEM")
    print(f"{len(by_answer)} answers, {n_items} checklist rows -> {OUT.relative_to(ROOT)}")
    print(f"answer-level marks moved from a checklist row to the ANSWER row: {len(moved)}")
    for m in moved:
        print("   ", m)
    if conflicts:
        print("kept the ANSWER row where the two differed:")
        for c in conflicts:
            print("   ", c)
    missing = [aid for aid, rs in by_answer.items()
               if not next(r for r in rs if r["row"].upper() == "ANSWER").get("jurisdiction_confusion")]
    if missing:
        print("answers with no jurisdiction mark:", missing)
    return 0


if __name__ == "__main__":
    sys.exit(main())
