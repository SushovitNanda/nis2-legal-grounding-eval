"""Command line:  python -m nis2eval <command> [options]

  index      build data/decree/dl_index.json from the decree text
  directive  build data/directive/directive_index.json and cross-check the Portuguese C2 text
             against the official English PDF
  validate   check standard.json (schema + every citation against the index)
  estimate   token / credit budget for a run (no API calls)
  smoke      S2: probe the models (availability, Portuguese, full-decree fit, cutoff)
  run        S4/S6/S7: generate answers (resumable)
  score      S5: citation check + LLM judge -> scores.csv
  analyze    S9: tables, bootstrap intervals, figures
  blind      S8: export the blind sample for the human grader
  agreement  S11: judge vs human grader (Cohen's kappa)
  demo       run the whole pipeline offline with mock models (pipeline test, not results)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import config, contexts, paths
from .decree_index import DecreeIndex, build_index
from .standard import load_standard, questions, validate


def _client(mock: bool, std):
    if mock:
        from .llm import MockClient
        return MockClient(std)
    from .llm import AdaptionClient
    return AdaptionClient()


def main(argv=None):
    ap = argparse.ArgumentParser(prog="nis2eval", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("index")
    sub.add_parser("directive")
    sub.add_parser("validate")

    def common(p):
        p.add_argument("--run", default="pilot", help="run name -> results/<run>/")
        p.add_argument("--standard", default=str(paths.STANDARD))
        p.add_argument("--mock", action="store_true", help="offline mock models (pipeline test only)")

    p = sub.add_parser("estimate"); common(p)
    p.add_argument("--conditions", default="C0,C1,C2"); p.add_argument("--reps", type=int, default=3)
    p = sub.add_parser("smoke"); p.add_argument("--models", default=""); p.add_argument("--no-context", action="store_true")
    p = sub.add_parser("run"); common(p)
    p.add_argument("--models", default="", help="comma list; default = test_models in config/models.json")
    p.add_argument("--conditions", default="C0,C1,C2", help="C0,C1,C2 core; C3,C4 stretch; add 'p' for pushback, e.g. C1p")
    p.add_argument("--reps", type=int, default=3)
    p.add_argument("--questions", default="", help="comma list of question ids")
    p.add_argument("--batch", type=int, default=0, help="1 or 2: only that batch of the standard")
    p.add_argument("--lang", default="pt", choices=["pt", "en"])
    p.add_argument("--concurrency", type=int, default=0)
    p = sub.add_parser("score"); common(p)
    p.add_argument("--judge", default=""); p.add_argument("--concurrency", type=int, default=0)
    p.add_argument("--conditions", default="", help="comma list: judge only answers given under these conditions")
    p.add_argument("--limit", type=int, default=0, help="judge at most this many answers in this pass")
    p.add_argument("--outside-reference", default="separate", choices=["separate", "fabricated"])
    p.add_argument("--tables-only", action="store_true", help="rebuild the CSVs from judgments.jsonl without calling the judge")
    p = sub.add_parser("analyze"); common(p); p.add_argument("--boot", type=int, default=5000)
    p.add_argument("--models", default="", help="comma list: analyse only these models (writes to analysis-<tag>/)")
    p.add_argument("--tag", default="", help="suffix of the output folder when --models is used (default: 'subset')")
    p.add_argument("--judge", default="", help="analyse another judge's tables (scores.<judge>.csv)")
    p.add_argument("--conditions", default="", help="comma list: analyse only these conditions")
    p = sub.add_parser("blind"); common(p); p.add_argument("--n", type=int, default=25); p.add_argument("--seed", type=int, default=2026)
    p.add_argument("--force", action="store_true", help="draw a new sample even if one was already exported")
    p = sub.add_parser("agreement"); common(p); p.add_argument("--sheet", default="")
    p.add_argument("--judge", default="", help="use this judge's marks when judgments.jsonl holds more than one judge")
    p = sub.add_parser("demo")
    a = ap.parse_args(argv)

    if a.cmd == "index":
        d = build_index()
        paths.DECREE_INDEX.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
        print({k: len(v["articles"]) for k, v in d["sections"].items()}, "->", paths.DECREE_INDEX)
        return 0
    if a.cmd == "directive":
        from .directive_index import build_directive_index, crosscheck
        d = build_directive_index()
        paths.DIRECTIVE_INDEX.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
        arts = d["sections"]["diretiva"]["articles"]
        print(f"{len(arts)} articles, {sum(len([p for p in v['paragraphs'] if p != '0']) for v in arts.values())} "
              f"numbered paragraphs -> {paths.DIRECTIVE_INDEX}")
        if not paths.DIRECTIVE_TXT_EN.exists():
            print("no English text to cross-check against: run scripts/extract_directive_en.py")
            return 0
        return 1 if crosscheck() else 0
    index = DecreeIndex.load()
    if a.cmd == "validate":
        probs = validate(load_standard(), index)
        std = load_standard()
        n_items = sum(len(q["items"]) for q in std["questions"])
        print(f"{len(std['questions'])} questions, {n_items} items; {len(probs)} problems")
        print("\n".join(probs))
        return 1 if probs else 0
    if a.cmd == "demo":
        return demo(index)
    if a.cmd == "smoke":
        from .llm import AdaptionClient
        from .smoke import run_smoke
        # short timeout and few retries: the smoke test should report a stuck model, not wait for it
        run_smoke(AdaptionClient(timeout=300, max_retries=1), [m for m in a.models.split(",") if m] or None, with_context=not a.no_context)
        return 0

    std = load_standard(Path(a.standard))
    cfg = config.models_config()
    if a.cmd in ("run", "score") and sys.platform == "win32" and not a.mock:
        try:  # long jobs: ask Windows not to sleep while this process lives (ES_CONTINUOUS | ES_SYSTEM_REQUIRED)
            import ctypes
            ctypes.windll.kernel32.SetThreadExecutionState(0x80000001)
        except Exception:  # noqa: BLE001
            pass
    run_dir = paths.RESULTS / a.run
    if a.cmd == "estimate":
        from .smoke import estimate
        estimate(std, cfg, a.conditions.split(","), a.reps)
        return 0
    if a.cmd == "run":
        from .runner import run
        models = [m for m in a.models.split(",") if m] or (["mock-large", "mock-small"] if a.mock else [m["id"] for m in cfg["test_models"]])
        qs = questions(std, [q for q in a.questions.split(",") if q] or None, a.batch or None)
        stats = run(_client(a.mock, std), qs, models, a.conditions.split(","), a.reps, run_dir, lang=a.lang,
                    gen=cfg["generation"], concurrency=a.concurrency or cfg.get("concurrency", 4), mock=a.mock)
        print(stats, "->", run_dir / "answers.jsonl")
        return 0 if not stats["error"] else 2
    if a.cmd == "score":
        from .scorer import score_run, write_tables
        judge = a.judge or ("mock-judge" if a.mock else cfg["judge"]["id"])
        suffix = "" if (a.mock or judge == cfg["judge"]["id"]) else f".{judge}"   # another judge keeps its own tables
        if a.tables_only:
            write_tables(std, index, run_dir, judge, a.outside_reference, suffix=suffix)
            return 0
        if not a.mock:  # a judge that is down would cost about 10 minutes of retries per answer
            from .llm import AdaptionClient, LLMError
            try:
                AdaptionClient(timeout=150, max_retries=1).generate(judge, "Say: ok", temperature=0, max_output_tokens=2000,
                                                                    reasoning_effort="low")
            except LLMError as e:
                print(f"Judge {judge} is not answering ({str(e)[:160]}).\nNothing was scored. Try again later, or pass "
                      f"--judge with a model that is up (fallback in config/models.json: {cfg['fallbacks']['judge']}).")
                return 3
        score_run(_client(a.mock, std), judge, std, index, run_dir, gen=cfg["judge_generation"],
                  concurrency=a.concurrency or cfg.get("concurrency", 4), outside_reference_policy=a.outside_reference,
                  suffix=suffix, conditions=[c for c in a.conditions.split(",") if c] or None, limit=a.limit)
        return 0
    if a.cmd == "analyze":
        from .analysis import analyse
        analyse(run_dir, n_boot=a.boot, models=[m for m in a.models.split(",") if m] or None, tag=a.tag or "subset",
                judge=a.judge or None, conditions=[c for c in a.conditions.split(",") if c] or None)
        return 0
    if a.cmd == "blind":
        from .blind import export_sample
        export_sample(run_dir, std, n=a.n, seed=a.seed, force=a.force)
        return 0
    if a.cmd == "agreement":
        from .blind import agreement
        agreement(run_dir, Path(a.sheet) if a.sheet else None, judge_model=a.judge or None)
        return 0


def demo(index) -> int:
    """End-to-end pipeline on mock models. Everything it writes is synthetic."""
    import csv
    import random
    import shutil
    from .analysis import analyse
    from .blind import agreement, export_sample
    from .llm import MockClient
    from .runner import run
    from .scorer import score_run
    std = load_standard()
    run_dir = paths.RESULTS / "demo-mock"
    shutil.rmtree(run_dir, ignore_errors=True)
    client = MockClient(std)
    conds = [c for c in ["C0", "C1", "C2", "C1p"] if not contexts.missing_docs(c)]
    run(client, std["questions"], ["mock-large", "mock-small"], conds, 3, run_dir, mock=True)
    score_run(client, "mock-judge", std, index, run_dir)
    analyse(run_dir, n_boot=1000)
    out = export_sample(run_dir, std, conditions=tuple(conds))
    # simulate a human grader who mostly agrees with the judge
    rng = random.Random(1)
    rows = list(csv.DictReader((out / "grading_sheet.csv").open(encoding="utf-8-sig")))
    key = json.loads((out / "KEY_do_not_send.json").read_text())
    from .runner import read_jsonl
    judg = {r["key"]: r["judgment"] for r in read_jsonl(run_dir / "judgments.jsonl")}
    for r in rows:
        j = judg[key[r["answer_id"]]["key"]]
        if r["row"] == "ITEM":
            ji = next(i for i in j["items"] if i["id"] == r["item"])
            r["coverage"] = ji["coverage"] if rng.random() < 0.85 else "partial"
            r["uncertainty"] = ji["uncertainty"]
        else:
            r["n_fabricated_claims"] = len(j["fabricated_claims"])
            r["jurisdiction_confusion"] = "yes" if j["jurisdiction_confusion"] else "no"
    with (out / "grading_sheet.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    agreement(run_dir)
    print(f"\nDEMO OK - synthetic outputs in {run_dir} (mock models: NOT results)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
