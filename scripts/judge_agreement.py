#!/usr/bin/env python3
"""Agreement between two LLM judges on the answers both have graded.

    python scripts/judge_agreement.py [--run full] [--a qwen3.8-27b] [--b gemma-4-31b-it]

Writes results/<run>/judge_agreement.md. Cohen's kappa per mark, over all answers and separately
leaving out each judge's own answers (a judge that is also a test model grades itself there).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from nis2eval.blind import COV, UNC, cohen_kappa  # noqa: E402
from nis2eval.judge import JUDGE_PROMPT_VERSION  # noqa: E402
from nis2eval.runner import read_jsonl  # noqa: E402


def load(run_dir: Path, judge: str) -> dict:
    out = {}
    for r in read_jsonl(run_dir / "judgments.jsonl"):
        if r.get("status") == "ok" and r.get("judge_model") == judge and r.get("judge_prompt") == JUDGE_PROMPT_VERSION:
            out[(r["key"], r.get("answer_sha"), r.get("standard_sha"))] = r
    return out


def table(pairs: list, title: str) -> list[str]:
    cov = ([], []); unc = ([], []); fab = ([], []); jur = ([], []); gap = ([], [])
    for ra, rb in pairs:
        ja, jb = ra["judgment"], rb["judgment"]
        ib = {i["id"]: i for i in jb["items"]}
        for i in ja["items"]:
            o = ib.get(i["id"])
            if not o:
                continue
            cov[0].append(i["coverage"]); cov[1].append(o["coverage"])
            if i["status"] != "verified":
                unc[0].append(i["uncertainty"]); unc[1].append(o["uncertainty"])
        yn = lambda v: "yes" if v else "no"
        fab[0].append(yn(ja["fabricated_claims"])); fab[1].append(yn(jb["fabricated_claims"]))
        jur[0].append(yn(ja["jurisdiction_confusion"])); jur[1].append(yn(jb["jurisdiction_confusion"]))
        if "says_decree_does_not_answer" in ja and "says_decree_does_not_answer" in jb:
            gap[0].append(yn(ja["says_decree_does_not_answer"])); gap[1].append(yn(jb["says_decree_does_not_answer"]))
    rows = [("Item coverage (3 levels, linear-weighted)", cov, COV, True),
            ("Item coverage (3 levels, exact)", cov, COV, False),
            ("Uncertainty mark on inferred / to-confirm items", unc, UNC, False),
            ("Answer has an unsupported claim", fab, ["yes", "no"], False),
            ("Jurisdiction confusion", jur, ["yes", "no"], False),
            ("Says the decree does not settle the point", gap, ["yes", "no"], False)]
    md = [f"## {title} ({len(pairs)} answers)", "", "| Mark | Cohen's kappa | Raw agreement | n |", "|---|---|---|---|"]
    for name, (a, b), labels, weighted in rows:
        k, raw, n = cohen_kappa(a, b, labels, weighted)
        md.append(f"| {name} | {k:.2f} | {raw:.2f} | {n} |")
    return md + [""]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="full")
    ap.add_argument("--a", default="qwen3.8-27b")
    ap.add_argument("--b", default="gemma-4-31b-it")
    ap.add_argument("--conditions", default="C0,C1,C2")
    ap.add_argument("--models", default="qwen3.5-397b,qwen3.8-27b,gemma-4-31b-it,deepseek-v4-flash",
                    help="answers of these models only (default: the four core models)")
    a = ap.parse_args()
    run_dir = ROOT / "results" / a.run
    A, B = load(run_dir, a.a), load(run_dir, a.b)
    conds = set(a.conditions.split(","))
    models = set(a.models.split(","))
    pairs = [(A[k], B[k]) for k in A if k in B and A[k]["condition"] in conds and A[k]["model"] in models]
    md = [f"# Agreement between the two judges: {a.a} and {a.b}", "",
          f"Conditions {a.conditions}; models {a.models}. Both judges saw the same prompt, rubric and full decree text.", ""]
    md += table(pairs, "All answers graded by both")
    md += table([p for p in pairs if p[0]["model"] not in (a.a, a.b)], "Without the two judges' own answers")
    for c in sorted(conds):
        md += table([p for p in pairs if p[0]["condition"] == c], f"Condition {c}")
    (run_dir / "judge_agreement.md").write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md))
    return 0


if __name__ == "__main__":
    sys.exit(main())
