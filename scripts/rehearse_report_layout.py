#!/usr/bin/env python3
"""Layout rehearsal: does the report still fit in 8 pages once the judge-versus-human columns exist?

    python scripts/rehearse_report_layout.py <output.docx>

Builds the report into the given scratch file with PLACEHOLDER agreement numbers. Nothing in the
project is written and the placeholder numbers never reach the real report. Check the result with
    powershell -ExecutionPolicy Bypass -File scripts\\check_report.ps1 -Docx <output.docx>
and delete it afterwards.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_report as B  # noqa: E402

if len(sys.argv) != 2 or Path(sys.argv[1]).resolve() == B.OUT.resolve():
    sys.exit("usage: python scripts/rehearse_report_layout.py <a scratch .docx, not the real report>")
placeholder = {m: {"coverage (linear-weighted)": (0.77, 0.84, 85), "uncertainty": (0.55, 0.80, 85),
                   "fab_any": (0.83, 0.92, 25), "jurisdiction": (0.75, 0.88, 25)} for m in (B.JUDGE_MAIN, B.JUDGE_2)}
B.human_agreement = lambda: placeholder
B.OUT = Path(sys.argv[1])
print("layout rehearsal written to", B.build(), "(placeholder numbers: do not submit)")
