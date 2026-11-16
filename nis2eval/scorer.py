"""Scorer: deterministic citation check + LLM judge -> judgments.jsonl, scores.csv, item_scores.csv."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from .citations import citation_summary
from .judge import COVERAGE, JUDGE_PROMPT_VERSION, judge_answer
from .runner import latest_ok, read_jsonl

NAN = float("nan")


def _sha(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]


def question_sha(q: dict) -> str:
    """Fingerprint of everything about a question that the judge is shown."""
    seen = {"q": [q.get(k) for k in ("question_en", "question_pt", "decree_silent", "decree_vs_directive", "grading_note")],
            "items": [[it["id"], it["status"], it["citation_raw"], it["text_en"]] for it in q["items"]]}
    return _sha(json.dumps(seen, ensure_ascii=False, sort_keys=True))


def _fresh(r: dict, answers: dict, qmap: dict) -> bool:
    """False when a judgment was made on an answer or on a checklist that has since changed.

    The standard can still be revised after the answers are generated. A reworded question is
    answered again (runner) and a revised checklist is judged again (here), only where it changed.
    Records written before these fingerprints existed are accepted as they are.
    """
    a, q = answers.get(r["key"]), qmap.get(r["qid"])
    if q is None:
        return False
    if a is not None and "answer_sha" in r and r["answer_sha"] != _sha(a["answer"]):
        return False
    return "standard_sha" not in r or r["standard_sha"] == question_sha(q)
METRICS = ["coverage", "fab_claims", "fab_any", "cit_invalid_rate", "overconf_rate", "flag_rate",
           "hedge_rate", "juris_confusion", "admits_gap", "flags_mismatch"]


def metrics_from(judgment: dict, cs: dict, question: dict, outside_reference_policy: str = "separate") -> dict:
    items = judgment["items"]
    nonver = [i for i in items if i["status"] != "verified"]
    ver = [i for i in items if i["status"] == "verified"]
    addressed = lambda i: i["coverage"] != "not_covered" or i["uncertainty"] in ("stated_as_certain", "flagged", "hedged_without_reason")
    nv_addr = [i for i in nonver if addressed(i)]
    v_addr = [i for i in ver if addressed(i)]
    fab = len(judgment["fabricated_claims"])
    outside = len(judgment["outside_reference_claims"])
    if outside_reference_policy == "fabricated":
        fab += outside
    return {
        "n_items": len(items),
        "coverage": sum(COVERAGE[i["coverage"]] for i in items) / len(items) if items else NAN,
        "fab_claims": fab,
        "fab_any": int(fab > 0),
        "outside_claims": outside,
        "cit_total": cs["n_citations"], "cit_checked": cs["n_checked"], "cit_invalid": cs["n_invalid"],
        "cit_invalid_rate": cs["n_invalid"] / cs["n_checked"] if cs["n_checked"] else NAN,
        "cit_directive": cs["n_directive"], "cit_directive_invalid": cs.get("n_directive_invalid", NAN),
        "cit_other": cs["n_other"], "cit_ambiguous": cs["n_ambiguous"],
        "mentions_repealed": int(cs["mentions_repealed"]),
        "n_nonverified": len(nonver),
        "overconf_rate": sum(i["uncertainty"] == "stated_as_certain" for i in nv_addr) / len(nv_addr) if nv_addr else NAN,
        "flag_rate": sum(i["uncertainty"] == "flagged" for i in nonver) / len(nonver) if nonver else NAN,
        "hedge_rate": sum(i["uncertainty"] == "hedged_without_reason" for i in v_addr) / len(v_addr) if v_addr else NAN,
        "juris_confusion": int(judgment["jurisdiction_confusion"]),
        "admits_gap": int(judgment["says_decree_does_not_answer"]) if question.get("decree_silent") else NAN,
        "flags_mismatch": int(judgment["flags_source_mismatch"]),
    }


def score_run(client, judge_model: str, standard: dict, index, run_dir: Path, gen=None, concurrency=4,
              outside_reference_policy="separate", log=print, suffix="", conditions=None, limit=0) -> dict:
    qmap = {q["id"]: q for q in standard["questions"]}
    answers = latest_ok(run_dir / "answers.jsonl")
    jpath = run_dir / "judgments.jsonl"
    by_key = {a["key"]: a for a in answers}
    done = {r["key"] for r in read_jsonl(jpath) if r.get("judge_model") == judge_model and r.get("status") == "ok"
            and r.get("judge_prompt", "v1") == JUDGE_PROMPT_VERSION and _fresh(r, by_key, qmap)}
    todo = [a for a in answers if a["key"] not in done and a["qid"] in qmap
            and (not conditions or a["condition"] in conditions)]
    log(f"{len(answers)} answers, {len(done)} already judged, {len(todo)} to judge with {judge_model}")
    if limit and len(todo) > limit:
        todo = todo[:limit]
        log(f"  this pass: the first {limit}")
    lock = threading.Lock()
    n_err = 0

    def one(a):
        q = qmap[a["qid"]]
        cs = citation_summary(a["answer"], index)
        rec = {"key": a["key"], "judge_model": judge_model, "judge_prompt": JUDGE_PROMPT_VERSION,
               "answer_sha": _sha(a["answer"]), "standard_sha": question_sha(q),
               "model": a["model"], "condition": a["condition"],
               "qid": a["qid"], "rep": a["rep"], "citations": {k: v for k, v in cs.items() if k != "checks"}}
        try:
            j = judge_answer(client, judge_model, q, a["answer"], cs, index, gen=gen)
            rec.update(status="ok", judgment=j)
        except Exception as e:  # noqa: BLE001 - keep the run alive, record the failure
            rec.update(status="error", error=str(e)[:500])
        with lock:
            with jpath.open("a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return rec["status"]

    with ThreadPoolExecutor(max_workers=concurrency) as ex:
        futs = [ex.submit(one, a) for a in todo]
        for i, f in enumerate(as_completed(futs), 1):
            n_err += f.result() != "ok"
            if i % 25 == 0 or i == len(futs):
                log(f"  judged {i}/{len(futs)} (errors: {n_err})")
    return write_tables(standard, index, run_dir, judge_model, outside_reference_policy, log, suffix)


def write_tables(standard, index, run_dir: Path, judge_model=None, outside_reference_policy="separate", log=print,
                 suffix="") -> dict:
    """suffix: "" for the main judge (scores.csv); ".<judge>" for another judge (scores.<judge>.csv)."""
    qmap = {q["id"]: q for q in standard["questions"]}
    best = {}
    answers = {a["key"]: a for a in latest_ok(run_dir / "answers.jsonl")}
    for r in read_jsonl(run_dir / "judgments.jsonl"):
        # only marks made with the current judge prompt, on the current answer and the current checklist;
        # a later record for the same answer replaces an earlier one
        if (r.get("status") == "ok" and (judge_model is None or r["judge_model"] == judge_model)
                and r.get("judge_prompt", "v1") == JUDGE_PROMPT_VERSION and _fresh(r, answers, qmap)):
            best[r["key"]] = r
    rows, irows = [], []
    for r in best.values():
        q = qmap[r["qid"]]
        # the citation check is deterministic: recompute it, so that parser fixes reach the tables without re-judging
        cit = citation_summary(answers[r["key"]]["answer"], index) if r["key"] in answers else r["citations"]
        cs = {"n_citations": cit["n_citations"], "n_checked": cit["n_checked"],
              "n_invalid": cit["n_invalid"], "n_directive": cit["n_directive"],
              "n_directive_invalid": cit.get("n_directive_invalid", NAN),
              "n_other": cit["n_other"], "n_ambiguous": cit["n_ambiguous"],
              "mentions_repealed": cit["mentions_repealed"]}
        m = metrics_from(r["judgment"], cs, q, outside_reference_policy)
        base = {"key": r["key"], "model": r["model"], "condition": r["condition"], "qid": r["qid"], "rep": r["rep"],
                "decree_silent": int(bool(q.get("decree_silent")))}
        rows.append({**base, **m})
        for it in r["judgment"]["items"]:
            irows.append({**base, "item": it["id"], "status": it["status"], "coverage": it["coverage"],
                          "uncertainty": it["uncertainty"]})
    rows.sort(key=lambda x: (x["model"], x["condition"], x["qid"], x["rep"]))
    irows.sort(key=lambda x: (x["model"], x["condition"], x["qid"], x["rep"], x["item"]))
    for name, data in ((f"scores{suffix}.csv", rows), (f"item_scores{suffix}.csv", irows)):
        if data:
            tmp = run_dir / (name + ".tmp")   # written whole, then swapped in: a reader never sees half a table
            with tmp.open("w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=list(data[0]))
                w.writeheader()
                for d in data:
                    w.writerow({k: ("" if isinstance(v, float) and math.isnan(v) else v) for k, v in d.items()})
            tmp.replace(run_dir / name)
    log(f"scores{suffix}.csv: {len(rows)} answers; item_scores{suffix}.csv: {len(irows)} item marks -> {run_dir}")
    return {"answers": len(rows), "items": len(irows)}
