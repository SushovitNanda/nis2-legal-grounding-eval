"""Blind sample for the human grader, and judge-vs-human agreement (Cohen's kappa)."""
from __future__ import annotations

import csv
import json
import random
from collections import defaultdict
from pathlib import Path

from .runner import latest_ok, read_jsonl

COV = ["covered", "partial", "not_covered"]
UNC = ["stated_as_certain", "flagged", "hedged_without_reason", "not_addressed"]
SHEET_COLS = ["answer_id", "row", "question_id", "item", "status", "checklist_item_or_instruction",
              "coverage", "uncertainty", "n_fabricated_claims", "jurisdiction_confusion", "notes"]


def export_sample(run_dir: Path, standard: dict, n=25, seed=2026, conditions=("C0", "C1", "C2"), log=print,
                  force=False) -> Path:
    out = run_dir / "blind"
    if (out / "KEY_do_not_send.json").exists() and not force:
        # the sample may already be with the grader: a new draw would not match the sheet that comes back
        log(f"blind sample already drawn in {out}; left as it is (pass --force to draw a new one)")
        return out
    qmap = {q["id"]: q for q in standard["questions"]}
    answers = [a for a in latest_ok(run_dir / "answers.jsonl") if a["condition"] in conditions and a["qid"] in qmap]
    rng = random.Random(seed)
    cells = defaultdict(list)
    for a in answers:
        cells[(a["model"], a["condition"])].append(a)
    for v in cells.values():
        rng.shuffle(v)
    order = sorted(cells)
    rng.shuffle(order)
    picked, used_q = [], defaultdict(int)
    while len(picked) < n and any(cells.values()):
        for cell in order:  # round-robin over model x condition; prefer questions not yet over-used
            if len(picked) >= n or not cells[cell]:
                continue
            cells[cell].sort(key=lambda a: used_q[a["qid"]])
            a = cells[cell].pop(0)
            picked.append(a)
            used_q[a["qid"]] += 1
    rng.shuffle(picked)
    out.mkdir(exist_ok=True)
    key = {}
    md = ["# Blind grading sample", "",
          "Grade each answer with the rubric (data/standard/rubric.md). Fill the sheet `grading_sheet.csv`:",
          "- one row per checklist item: `coverage` = covered / partial / not_covered; "
          "`uncertainty` = stated_as_certain / flagged / hedged_without_reason / not_addressed",
          "- one ANSWER row per answer: `n_fabricated_claims` (a number) and `jurisdiction_confusion` (yes / no)", ""]
    rows = []
    for i, a in enumerate(picked, 1):
        aid = f"A{i:02d}"
        key[aid] = {"key": a["key"], "model": a["model"], "condition": a["condition"], "qid": a["qid"], "rep": a["rep"]}
        q = qmap[a["qid"]]
        md += [f"## {aid} - question {q['id']}", "", f"**Question:** {q['question_pt']}", "",
               f"*({q['question_en']})*", "", "**Answer:**", "", a["answer"].strip(), "", "---", ""]
        for it in q["items"]:
            rows.append([aid, "ITEM", q["id"], it["id"], it["status"], it["text_en"], "", "", "", "", ""])
        rows.append([aid, "ANSWER", q["id"], "", "", "Whole answer: count fabricated claims; jurisdiction confusion yes/no",
                     "", "", "", "", ""])
    with (out / "grading_sheet.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(SHEET_COLS)
        w.writerows(rows)
    (out / "blind_answers.md").write_text("\n".join(md), encoding="utf-8")
    (out / "KEY_do_not_send.json").write_text(json.dumps(key, indent=1), encoding="utf-8")
    log(f"{len(picked)} answers -> {out}/blind_answers.md and grading_sheet.csv (send these two; keep KEY_do_not_send.json)")
    return out


def cohen_kappa(a: list, b: list, labels: list, weighted=False):
    """Cohen's kappa (optionally linear-weighted for ordered labels). Returns (kappa, raw agreement, n)."""
    n = len(a)
    if n == 0:
        return float("nan"), float("nan"), 0
    k = len(labels)
    idx = {l: i for i, l in enumerate(labels)}
    obs = [[0.0] * k for _ in range(k)]
    for x, y in zip(a, b):
        obs[idx[x]][idx[y]] += 1 / n
    pa = [sum(obs[i]) for i in range(k)]
    pb = [sum(obs[i][j] for i in range(k)) for j in range(k)]
    w = lambda i, j: (abs(i - j) / (k - 1) if weighted and k > 1 else float(i != j))
    do = sum(w(i, j) * obs[i][j] for i in range(k) for j in range(k))
    de = sum(w(i, j) * pa[i] * pb[j] for i in range(k) for j in range(k))
    raw = sum(obs[i][i] for i in range(k))
    return (1 - do / de if de > 0 else float("nan")), raw, n


def _norm(v: str, labels):
    v = (v or "").strip().lower().replace(" ", "_").replace("-", "_")
    alias = {"yes": "yes", "y": "yes", "sim": "yes", "true": "yes", "1": "yes", "no": "no", "n": "no", "não": "no",
             "nao": "no", "false": "no", "0": "no", "not covered": "not_covered", "certain": "stated_as_certain",
             "hedged": "hedged_without_reason", "n/a": "not_addressed", "na": "not_addressed", "": None,
             "coberto": "covered", "parcial": "partial", "nao_coberto": "not_covered", "não_coberto": "not_covered",
             "notcovered": "not_covered", "stated_certain": "stated_as_certain", "flag": "flagged"}
    v = alias.get(v, v)
    return v if v in labels else None


def read_sheet(sheet: Path) -> list[dict]:
    """The grading sheet as it comes back from a spreadsheet program: any of the usual encodings,
    comma or semicolon as separator (Excel in a Portuguese locale writes semicolons), stray spaces
    and capitals in the header."""
    raw = sheet.read_bytes()
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):      # "Unicode text" from Excel
        text = raw.decode("utf-16")
    else:
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeError:                         # "CSV (semicolon delimited)" from Excel on Windows
            text = raw.decode("cp1252")
    first = text.splitlines()[0] if text.strip() else ""
    delim = max(",;\t", key=first.count)
    rows = []
    for row in csv.DictReader(text.splitlines(), delimiter=delim):
        rows.append({(k or "").strip().lower(): (v or "").strip() for k, v in row.items()})
    return rows


def agreement(run_dir: Path, sheet: Path | None = None, judge_model=None, log=print) -> dict:
    out = run_dir / "blind"
    sheet = sheet or out / "grading_sheet.csv"
    key = json.loads((out / "KEY_do_not_send.json").read_text(encoding="utf-8"))
    # the judgment of the answer that was shown to the grader: same key and, where recorded, same text
    import hashlib
    shown = {a["key"]: hashlib.sha1(a["answer"].encode("utf-8")).hexdigest()[:12] for a in latest_ok(run_dir / "answers.jsonl")}
    judg = {}
    for r in read_jsonl(run_dir / "judgments.jsonl"):
        if (r.get("status") == "ok" and (judge_model is None or r["judge_model"] == judge_model)
                and r.get("answer_sha", shown.get(r["key"])) == shown.get(r["key"])):
            judg[r["key"]] = r["judgment"]
    pairs = {"coverage": ([], []), "uncertainty": ([], []), "fab_any": ([], []), "jurisdiction": ([], [])}
    fab_counts = []
    skipped = 0
    if True:
        for row in read_sheet(sheet):
            k = key.get(row["answer_id"].upper())
            j = judg.get(k["key"]) if k else None
            if j is None:
                skipped += 1
                continue
            if row["row"].upper() == "ITEM":
                ji = next((i for i in j["items"] if i["id"] == row["item"].lower()), None)
                hc, hu = _norm(row["coverage"], COV), _norm(row["uncertainty"], UNC)
                if ji and hc:
                    pairs["coverage"][0].append(hc); pairs["coverage"][1].append(ji["coverage"])
                if ji and hu:
                    pairs["uncertainty"][0].append(hu); pairs["uncertainty"][1].append(ji["uncertainty"])
            else:
                hj = _norm(row["jurisdiction_confusion"], ["yes", "no"])
                if hj:
                    pairs["jurisdiction"][0].append(hj); pairs["jurisdiction"][1].append("yes" if j["jurisdiction_confusion"] else "no")
                try:
                    hf = int(float(row["n_fabricated_claims"]))
                except (TypeError, ValueError):
                    continue
                jf = len(j["fabricated_claims"])
                fab_counts.append((hf, jf))
                pairs["fab_any"][0].append("yes" if hf else "no"); pairs["fab_any"][1].append("yes" if jf else "no")
    res = []
    specs = [("coverage", COV, True), ("coverage", COV, False), ("uncertainty", UNC, False),
             ("fab_any", ["yes", "no"], False), ("jurisdiction", ["yes", "no"], False)]
    for name, labels, weighted in specs:
        kappa, raw, n = cohen_kappa(pairs[name][0], pairs[name][1], labels, weighted)
        res.append({"metric": name + (" (linear-weighted)" if weighted else ""), "kappa": kappa, "raw_agreement": raw, "n": n})
    tag = f".{judge_model}" if judge_model else ""
    with (out / f"agreement{tag}.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["metric", "kappa", "raw_agreement", "n"])
        w.writeheader(); w.writerows(res)
    md = [f"# Judge {judge_model or ''} vs human grader (blind sample)".replace("  ", " "), "",
          "| Metric | Cohen's kappa | Raw agreement | n |", "|---|---|---|---|"]
    md += [f"| {r['metric']} | {r['kappa']:.2f} | {r['raw_agreement']:.2f} | {r['n']} |" for r in res]
    if fab_counts:
        mad = sum(abs(h - j) for h, j in fab_counts) / len(fab_counts)
        md += ["", f"Fabricated-claim counts: mean absolute difference {mad:.2f} over {len(fab_counts)} answers "
                   f"(human total {sum(h for h, _ in fab_counts)}, judge total {sum(j for _, j in fab_counts)})."]
    if skipped:
        md += ["", f"{skipped} sheet rows had no matching judgment and were skipped."]
    (out / f"agreement{tag}.md").write_text("\n".join(md), encoding="utf-8")
    log("\n".join(md))
    return {"rows": res, "skipped": skipped}
