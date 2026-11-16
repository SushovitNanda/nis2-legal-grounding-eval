#!/usr/bin/env python3
"""Figure 1 of the report: the main result, pooled over models, by condition.

    python scripts/report_figure.py [--run full]

Writes results/<run>/fig_main_result.png (and .pdf). Four panels, one bar per condition; the same
numbers are in RESULTS_tables.md, table 1. Colours follow the condition, in the fixed order used by
every other figure of the project (nis2eval/analysis.py).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from nis2eval.analysis import COND_COLORS, GRID, INK, INK2, MUTED, SURFACE  # noqa: E402
from results_tables import CONDS, CORE, JUDGE_MAIN, pooled  # noqa: E402

NL = chr(10)
PANELS = [("coverage", "Checklist coverage" + NL),
          ("fab_any", "Answers with an" + NL + "unsupported claim"),
          ("juris_confusion", "Answers that confuse directive" + NL + "and national law"),
          ("admits_gap", "Says the decree does not settle it" + NL + "(the 3 questions it does not answer)")]
SHORT = {"C0": "No text", "C1": "Decree-law", "C2": "Directive" + NL + "instead"}


def draw(df, models, run, compact: bool) -> Path:
    """compact=True: drawn at the width of the report page (6.5 in), so its text is read at true size."""
    nl = NL
    if compact:
        panels = [("coverage", "Checklist" + nl + "coverage"), ("fab_any", "Answers with an" + nl + "unsupported claim"),
                  ("juris_confusion", "Answers with" + nl + "jurisdiction confusion"),
                  ("admits_gap", "Says the decree" + nl + "does not settle it")]
        short = {"C0": "", "C1": "", "C2": ""}       # the legend names the bars; three labels do not fit under a panel
        size, fs_title, fs_tick, fs_val, fs_y = (6.5, 2.6), 8, 7.5, 8, 6.5
    else:
        panels, short, size, fs_title, fs_tick, fs_val, fs_y = PANELS, SHORT, (13, 4.1), 10, 9, 10.5, 8.5
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": fs_tick})
    fig, axes = plt.subplots(1, 4, figsize=size, facecolor=SURFACE)
    for ax, (metric, title) in zip(axes, panels):
        ax.set_facecolor(SURFACE)
        for i, c in enumerate(CONDS):
            m, lo, hi, _n = pooled(df, metric, c)
            ax.bar(i, 100 * m, width=0.62, color=COND_COLORS[c], zorder=3)
            if lo == lo and hi > lo:   # interval exists and is not degenerate
                ax.plot([i, i], [100 * lo, 100 * hi], color=INK2, lw=1.0 if compact else 1.2, zorder=4)
            ax.text(i, 100 * (hi if hi == hi else m) + 3, f"{100 * m:.0f}%", ha="center", va="bottom", color=INK, fontsize=fs_val, zorder=5)
        ax.set_xticks(range(len(CONDS)))
        ax.set_xticklabels([short[c] for c in CONDS], color=INK2, fontsize=fs_tick)
        ax.set_ylim(0, 122 if compact else 118)
        ax.set_yticks([0, 25, 50, 75, 100])
        ax.set_yticklabels(["0", "25", "50", "75", "100%"], color=MUTED, fontsize=fs_y)
        ax.grid(axis="y", color=GRID, lw=0.8, zorder=0)
        ax.tick_params(length=0, pad=2)
        for side in ("top", "right", "left"):
            ax.spines[side].set_visible(False)
        ax.spines["bottom"].set_color(MUTED)
        ax.set_title(title, loc="left", color=INK, fontsize=fs_title, pad=6 if compact else 8)
    if compact:
        from matplotlib.patches import Patch
        names = {"C0": "C0: question only", "C1": "C1: with the decree-law", "C2": "C2: with the Directive instead"}
        fig.legend(handles=[Patch(facecolor=COND_COLORS[c], label=names[c]) for c in CONDS], loc="upper center", ncol=3,
                   frameon=False, fontsize=8, handlelength=1.2, handleheight=0.9, columnspacing=2.0, labelcolor=INK2)
        fig.tight_layout(rect=(0, 0, 1, 0.90), w_pad=1.4)
        out = run / "fig_main_result_report.png"
        fig.savefig(out, dpi=300, facecolor=SURFACE)
    else:
        fig.text(0.008, 0.012,
                 f"Mean over 22 questions (3 on the right), {len(models)} models and 3 repetitions averaged within a question first. "
                 f"Lines: 95% bootstrap interval over questions. Judge: {JUDGE_MAIN}; its own answers are left out.",
                 color=MUTED, fontsize=8)
        fig.tight_layout(rect=(0, 0.045, 1, 1), w_pad=2.2)
        out = run / "fig_main_result.png"
        for ext in ("png", "pdf"):
            fig.savefig(run / f"fig_main_result.{ext}", dpi=200, facecolor=SURFACE)
    plt.close(fig)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="full")
    a = ap.parse_args()
    run = ROOT / "results" / a.run
    df = pd.read_csv(run / "scores.csv")
    models = [m for m in CORE if m != JUDGE_MAIN]
    df = df[df["model"].isin(models) & df["condition"].isin(CONDS)]
    for compact in (False, True):
        print("wrote", draw(df, models, run, compact))
    return 0


if __name__ == "__main__":
    sys.exit(main())
