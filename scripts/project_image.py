#!/usr/bin/env python3
"""The project image for the submission page: 16:9, readable as a thumbnail.

    python scripts/project_image.py

Writes Report/project-image.png (1600 x 900). Numbers are read from the scored run (main result:
three models, judge qwen3.8-27b), the same as Table 1 of the report.
"""
from __future__ import annotations

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
LABELS = {"C0": "No document", "C1": "With the Portuguese decree-law", "C2": "With the EU Directive instead"}
PANELS = [("coverage", "Checklist coverage"), ("fab_any", "Answers with an unsupported claim"),
          ("juris_confusion", "Applies the wrong law")]


def main() -> int:
    run = ROOT / "results" / "full"
    df = pd.read_csv(run / "scores.csv")
    df = df[df["model"].isin([m for m in CORE if m != JUDGE_MAIN]) & df["condition"].isin(CONDS)]
    plt.rcParams.update({"font.family": "DejaVu Sans"})
    fig = plt.figure(figsize=(16, 9), dpi=100, facecolor=SURFACE)
    fig.text(0.05, 0.90, "Grounded or guessing?", fontsize=40, weight="bold", color=INK)
    fig.text(0.05, 0.835, "What the legal text does to LLM compliance advice on Portugal's NIS 2 law",
             fontsize=21, color=INK2)
    from matplotlib.patches import Patch
    fig.legend(handles=[Patch(facecolor=COND_COLORS[c], label=LABELS[c]) for c in CONDS], loc="upper left",
               bbox_to_anchor=(0.045, 0.79), ncol=3, frameon=False, fontsize=17, handlelength=1.3, handleheight=1.1,
               columnspacing=2.4, labelcolor=INK2)
    axes = [fig.add_axes([0.05 + i * 0.315, 0.17, 0.27, 0.46]) for i in range(3)]
    for ax, (metric, title) in zip(axes, PANELS):
        ax.set_facecolor(SURFACE)
        for i, c in enumerate(CONDS):
            m, lo, hi, _n = pooled(df, metric, c)
            ax.bar(i, 100 * m, width=0.66, color=COND_COLORS[c], zorder=3)
            ax.text(i, 100 * m + 3, f"{100 * m:.0f}%", ha="center", va="bottom", fontsize=24, weight="bold", color=INK)
        ax.set_ylim(0, 112)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.tick_params(length=0, pad=6)
        for side in ("top", "right", "left"):
            ax.spines[side].set_visible(False)
        ax.spines["bottom"].set_color(MUTED)
        ax.grid(False)
        ax.set_title(title, loc="left", fontsize=19, color=INK, pad=14)
    fig.text(0.05, 0.075, "4 models  ·  22 expert-written questions  ·  792 answers  ·  two LLM judges validated "
                          "against a legal professional", fontsize=15, color=INK2)
    fig.text(0.05, 0.035, "Apart Research AI x Epistemics sprint  ·  github.com/SushovitNanda/Legal-grounding-eval",
             fontsize=13, color=MUTED)
    out = ROOT / "Report" / "project-image.png"
    fig.savefig(out, dpi=100, facecolor=SURFACE)
    print("wrote", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
