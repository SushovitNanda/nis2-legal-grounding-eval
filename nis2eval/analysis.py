"""Analysis: per model x condition means with question-level bootstrap intervals,
paired condition contrasts, repetition variance, tables and figures.

Unit of analysis = the QUESTION. Repetitions of the same question are averaged first
(they are not independent), then questions are resampled with replacement."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .scorer import METRICS

LABELS = {
    "coverage": "Coverage of the checklist (0-1)",
    "fab_claims": "Fabricated claims per answer (judge)",
    "fab_any": "Answers with at least one fabricated claim",
    "cit_invalid_rate": "Cited provisions that do not exist (share)",
    "overconf_rate": "Uncertain items stated as certain (share)",
    "flag_rate": "Uncertain items properly flagged (share)",
    "hedge_rate": "Verified items hedged without reason (share)",
    "juris_confusion": "Answers with jurisdiction confusion (share)",
    "admits_gap": "Says the decree is silent (3 silent questions)",
    "flags_mismatch": "Notes that the text given is not the law in force",
}
CONTRASTS = [("C1", "C0"), ("C2", "C1"), ("C2", "C0"), ("C4", "C1"), ("C3", "C1"), ("C0p", "C0"), ("C1p", "C1")]
# categorical palette (fixed order, colour follows the condition) - validated, see README "Figures"
COND_COLORS = {"C0": "#2a78d6", "C1": "#eb6834", "C2": "#1baf7a", "C3": "#eda100", "C4": "#e87ba4",
               "C0p": "#86b6ef", "C1p": "#f3a98a"}
COND_NAMES = {"C0": "C0 question only", "C1": "C1 with the decree-law", "C2": "C2 with the directive instead",
              "C3": "C3 with the artifact", "C4": "C4 decree-law + legal-categories scheme",
              "C0p": "C0 after pushback", "C1p": "C1 after pushback"}
SURFACE, INK, INK2, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e6e5e0"


def boot_ci(values: np.ndarray, n_boot=5000, seed=7, alpha=0.05):
    """Mean and percentile bootstrap CI over questions (NaNs dropped)."""
    v = np.asarray(values, dtype=float)
    v = v[~np.isnan(v)]
    if len(v) == 0:
        return np.nan, np.nan, np.nan, 0
    if len(v) == 1:
        return float(v[0]), np.nan, np.nan, 1
    rng = np.random.default_rng(seed)
    means = v[rng.integers(0, len(v), size=(n_boot, len(v)))].mean(axis=1)
    lo, hi = np.quantile(means, [alpha / 2, 1 - alpha / 2])
    return float(v.mean()), float(lo), float(hi), len(v)


def analyse(run_dir: Path, n_boot=5000, seed=7, log=print, models=None, tag="subset", judge=None,
            conditions=None) -> dict:
    """judge: read the tables of another judge (scores.<judge>.csv); conditions: keep only these."""
    suffix = f".{judge}" if judge else ""
    df = pd.read_csv(run_dir / f"scores{suffix}.csv")
    name = "analysis" + (f"-judge-{judge}" if judge else "")
    if conditions:
        df = df[df["condition"].isin(conditions)]
    if models:  # e.g. leave out the model that is also the judge
        df = df[df["model"].isin(models)]
    if models or conditions:
        name += f"-{tag}"
    out = run_dir / name
    out.mkdir(exist_ok=True)
    metrics = [m for m in METRICS if m in df.columns]
    # 1) average repetitions within question
    q = df.groupby(["model", "condition", "qid"], as_index=False)[metrics].mean()
    rep_sd = df.groupby(["model", "condition", "qid"])[metrics].std(ddof=1).groupby(["model", "condition"]).mean()

    # 2) model x condition summary
    rows = []
    for (model, cond), g in q.groupby(["model", "condition"]):
        for m in metrics:
            mean, lo, hi, n = boot_ci(g[m].to_numpy(), n_boot, seed)
            rows.append({"model": model, "condition": cond, "metric": m, "mean": mean, "ci_lo": lo, "ci_hi": hi,
                         "n_questions": n,
                         "rep_sd": rep_sd.loc[(model, cond), m] if (model, cond) in rep_sd.index else np.nan})
    summary = pd.DataFrame(rows)
    summary.to_csv(out / "summary_by_model_condition.csv", index=False)

    # 3) paired contrasts over questions (per model and pooled over models)
    crow = []
    conds = set(q["condition"])
    for a, b in CONTRASTS:
        if a not in conds or b not in conds:
            continue
        for m in metrics:
            wide = q[q["condition"].isin([a, b])].pivot_table(index=["model", "qid"], columns="condition", values=m)
            if a not in wide or b not in wide:
                continue
            d = (wide[a] - wide[b]).dropna()
            for model, dm in d.groupby(level="model"):
                mean, lo, hi, n = boot_ci(dm.to_numpy(), n_boot, seed)
                crow.append({"contrast": f"{a} - {b}", "model": model, "metric": m, "diff": mean, "ci_lo": lo,
                             "ci_hi": hi, "n_questions": n})
            pooled = d.groupby(level="qid").mean()
            mean, lo, hi, n = boot_ci(pooled.to_numpy(), n_boot, seed)
            crow.append({"contrast": f"{a} - {b}", "model": "ALL (mean over models)", "metric": m, "diff": mean,
                         "ci_lo": lo, "ci_hi": hi, "n_questions": n})
    contrasts = pd.DataFrame(crow)
    contrasts.to_csv(out / "paired_contrasts.csv", index=False)

    # 4) per-question table (which questions drive the result)
    q.to_csv(out / "by_question.csv", index=False)

    # 5) uncertainty by item status, from item marks
    ipath = run_dir / f"item_scores{suffix}.csv"
    if ipath.exists():
        it = pd.read_csv(ipath)
        if conditions:
            it = it[it["condition"].isin(conditions)]
        if models:
            it = it[it["model"].isin(models)]
        tab = (it.groupby(["model", "condition", "status", "uncertainty"]).size().rename("n").reset_index())
        tab["share"] = tab["n"] / tab.groupby(["model", "condition", "status"])["n"].transform("sum")
        tab.to_csv(out / "uncertainty_by_status.csv", index=False)

    figs = make_figures(summary, out)
    write_summary_md(df, summary, contrasts, out)
    log(f"analysis written to {out} ({len(figs)} figures)")
    return {"summary_rows": len(summary), "contrast_rows": len(contrasts), "figures": figs}


def _fmt(mean, lo, hi):
    if np.isnan(mean):
        return "n/a"
    if np.isnan(lo):
        return f"{mean:.2f}"
    return f"{mean:.2f} [{lo:.2f}, {hi:.2f}]"


def write_summary_md(df, summary, contrasts, out: Path):
    lines = ["# Results summary", "",
             f"{len(df)} scored answers; {df['qid'].nunique()} questions; models: {', '.join(sorted(df['model'].unique()))}; "
             f"conditions: {', '.join(sorted(df['condition'].unique()))}; repetitions per cell: up to {int(df['rep'].max()) + 1}.",
             "", "Means over questions (repetitions averaged first), with 95% bootstrap intervals over questions.", ""]
    for m in summary["metric"].unique():
        s = summary[summary["metric"] == m]
        if s["mean"].isna().all():
            continue
        conds = sorted(s["condition"].unique())
        lines += [f"## {LABELS.get(m, m)}", "", "| Model | " + " | ".join(conds) + " |", "|---|" + "---|" * len(conds)]
        for model, g in s.groupby("model"):
            cells = []
            for c in conds:
                r = g[g["condition"] == c]
                cells.append(_fmt(r["mean"].iloc[0], r["ci_lo"].iloc[0], r["ci_hi"].iloc[0]) if len(r) else "-")
            lines.append(f"| {model} | " + " | ".join(cells) + " |")
        lines.append("")
    if len(contrasts):
        lines += ["## Paired contrasts (difference per question, pooled over models)", "",
                  "| Contrast | Metric | Difference [95% CI] | Questions |", "|---|---|---|---|"]
        for _, r in contrasts[contrasts["model"].str.startswith("ALL")].iterrows():
            if not np.isnan(r["diff"]):
                lines.append(f"| {r['contrast']} | {LABELS.get(r['metric'], r['metric'])} | "
                             f"{r['diff']:+.2f} [{r['ci_lo']:+.2f}, {r['ci_hi']:+.2f}] | {int(r['n_questions'])} |")
        lines.append("")
    (out / "summary.md").write_text("\n".join(lines), encoding="utf-8")


def make_figures(summary: pd.DataFrame, out: Path) -> list[str]:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": MUTED,
                         "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2, "text.color": INK})
    panels = [["coverage", "fab_claims", "cit_invalid_rate"], ["overconf_rate", "juris_confusion", "admits_gap"]]
    models = sorted(summary["model"].unique())
    conds = [c for c in COND_COLORS if c in set(summary["condition"])]
    files = []
    fig, axes = plt.subplots(2, 3, figsize=(13, 7.2), facecolor=SURFACE)
    width = 0.8 / max(len(conds), 1)
    for ax, m in zip(axes.ravel(), [m for row in panels for m in row]):
        ax.set_facecolor(SURFACE)
        s = summary[summary["metric"] == m]
        for ci, c in enumerate(conds):
            xs, ys, los, his = [], [], [], []
            for mi, model in enumerate(models):
                r = s[(s["model"] == model) & (s["condition"] == c)]
                if len(r) and not np.isnan(r["mean"].iloc[0]):
                    y = r["mean"].iloc[0]
                    xs.append(mi - 0.4 + width * (ci + 0.5))
                    ys.append(y)
                    los.append(0 if np.isnan(r["ci_lo"].iloc[0]) else y - r["ci_lo"].iloc[0])
                    his.append(0 if np.isnan(r["ci_hi"].iloc[0]) else r["ci_hi"].iloc[0] - y)
            ax.bar(xs, ys, width=width * 0.86, color=COND_COLORS[c], label=COND_NAMES[c], linewidth=0, zorder=3)
            ax.errorbar(xs, ys, yerr=[los, his], fmt="none", ecolor=INK2, elinewidth=1, capsize=2, zorder=4)
        ax.set_title(LABELS.get(m, m), loc="left", fontsize=10, color=INK, pad=8)
        ax.set_xticks(range(len(models)))
        ax.set_xticklabels(models, rotation=0 if len(models) <= 3 else 12)
        ax.yaxis.grid(True, color=GRID, linewidth=0.8, zorder=0)
        ax.set_axisbelow(True)
        for sp in ("top", "right", "left"):
            ax.spines[sp].set_visible(False)
        ax.tick_params(length=0)
        if m != "fab_claims":
            ax.set_ylim(0, 1.05)
        else:
            ax.set_ylim(bottom=0)
    h, l = axes[0, 0].get_legend_handles_labels()
    fig.legend(h, l, loc="upper center", ncol=min(len(conds), 4), frameon=False, bbox_to_anchor=(0.5, 0.995))
    fig.text(0.01, 0.005, "Bars: mean over questions (repetitions averaged first). Whiskers: 95% bootstrap interval over questions.",
             fontsize=8, color=MUTED)
    fig.tight_layout(rect=(0, 0.02, 1, 0.94))
    f = out / "fig_metrics_by_model_condition.png"
    fig.savefig(f, dpi=200, facecolor=SURFACE)
    plt.close(fig)
    files.append(str(f))
    return files
