#!/usr/bin/env python3
"""One command to bring every result, figure and the report up to date (no model calls).

    python scripts/refresh_results.py

It also rebuilds the report (Report/NIS2-compliance-advice-report.docx) from the template. Run it (a) when the supplementary model has finished, and (b) when Bia's filled grading sheet has
been saved as results/full/blind/grading_sheet.csv. It calls no model: it only rebuilds tables,
figures and agreement tables from the answers and judgments already on disk, so it takes about a
minute and can be run as often as you like, also while the overnight run is still going.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "results" / "full"
SHARE = ROOT / "share_with_bia" / "03-results"
JUDGE_MAIN, JUDGE_2 = "qwen3.8-27b", "gemma-4-31b-it"
CORE = ["qwen3.5-397b", "qwen3.8-27b", "gemma-4-31b-it", "deepseek-v4-flash"]
sys.path.insert(0, str(ROOT))


def run(*args: str) -> int:
    print(">", " ".join(args), flush=True)
    return subprocess.run([sys.executable, *args], cwd=ROOT, env=dict(os.environ, PYTHONIOENCODING="utf-8")).returncode


def sheet_is_filled() -> bool:
    from nis2eval.blind import read_sheet
    sheet = RUN / "blind" / "grading_sheet.csv"
    if not sheet.exists():
        return False
    rows = read_sheet(sheet)
    return sum(1 for r in rows if r.get("coverage") or r.get("n_fabricated_claims")) >= 20


def main() -> int:
    cc = "C0,C1,C2"
    for judge, flag in ((JUDGE_MAIN, []), (JUDGE_2, ["--judge", JUDGE_2])):
        run("-m", "nis2eval", "score", "--run", "full", "--judge", judge, "--tables-only")
        run("-m", "nis2eval", "analyze", "--run", "full", "--conditions", cc, "--models", ",".join(CORE), "--tag", "core4", *flag)
        run("-m", "nis2eval", "analyze", "--run", "full", "--conditions", cc,
            "--models", ",".join(m for m in CORE if m != judge), "--tag", "core-without-judge-model", *flag)
    run("scripts/judge_agreement.py", "--run", "full", "--a", JUDGE_MAIN, "--b", JUDGE_2)
    run("scripts/results_tables.py", "--run", "full")
    run("scripts/report_figure.py", "--run", "full")
    human = sheet_is_filled()
    if human:
        for judge in (JUDGE_MAIN, JUDGE_2):
            run("-m", "nis2eval", "agreement", "--run", "full", "--judge", judge)
        run("scripts/human_results.py", "--run", "full")
    else:
        print("\n(grading sheet not filled in yet: judge-versus-human tables skipped)")

    share_on = SHARE.parent.exists()   # the hand-over folder used during the sprint; absent in a clone
    if share_on:
        SHARE.mkdir(parents=True, exist_ok=True)
    files = [(ROOT / "docs" / "RESULTS_draft.md", "RESULTS_draft.md"),
             (RUN / "RESULTS_tables.md", "RESULTS_tables.md"),
             (RUN / "fig_main_result.png", "fig_main_result.png"),
             (RUN / "fig_main_result.pdf", "fig_main_result.pdf"),
             (RUN / "judge_agreement.md", "judge_agreement.md"),
             (RUN / "analysis-core-without-judge-model" / "summary.md", "per-model-main-judge.md"),
             (RUN / "analysis-core-without-judge-model" / "fig_metrics_by_model_condition.png", "fig_per_model_main_judge.png"),
             (RUN / f"analysis-judge-{JUDGE_2}-core-without-judge-model" / "summary.md", "per-model-second-judge.md")]
    if human:
        files += [(RUN / "blind" / f"agreement.{j}.md", f"judge-vs-human.{j}.md") for j in (JUDGE_MAIN, JUDGE_2)]
        files += [(RUN / "blind" / "human_results.md", "human_results.md")]
    for src, name in files:
        if share_on and src.exists():
            shutil.copyfile(src, SHARE / name)
    if share_on:
        shutil.copyfile(ROOT / "docs" / "METHODS_draft.md", ROOT / "share_with_bia" / "METHODS_draft.md")
    # the report: rebuilt from the template with the tables as they now are
    if run("scripts/build_report.py") == 0 and share_on:
        rep = ROOT / "share_with_bia" / "04-report"
        rep.mkdir(exist_ok=True)
        shutil.copyfile(ROOT / "Report" / "NIS2-compliance-advice-report.docx", rep / "NIS2-compliance-advice-report.docx")
        print("report rebuilt. Check its length:  powershell -ExecutionPolicy Bypass -File scripts\\check_report.ps1")
    print("\nall tables, figures and the report rebuilt" + (f"; hand-over folder refreshed: {SHARE}" if share_on else ""))
    if human:
        for j in (JUDGE_MAIN, JUDGE_2):
            print("\n" + (RUN / "blind" / f"agreement.{j}.md").read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
