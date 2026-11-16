"""Smoke test (task S2): which models are up, does the whole decree fit, how good is the
Portuguese, what does a call cost, and does the model know the decree at all (cutoff probe)."""
from __future__ import annotations

import json
import time

from . import config, contexts, paths
from .llm import LLMError

PROBES = {
    "pt_quality": ("Explique em duas frases, em português europeu, o que é uma contraordenação.", None),
    "knows_decree": ("O que é o Decreto-Lei n.º 125/2025, de 4 de dezembro, e quando entrou em vigor? "
                     "Se não souber ou não tiver a certeza, diga-o.", None),
    "training_cutoff": ("What is your training data cutoff date? Answer with the month and year only.", None),
}
CONTEXT_QUESTION = ("Segundo o artigo 44.º, n.º 1, do regime, qual é o prazo do relatório final e a partir de quando se conta? "
                    "Responda numa frase.")


def run_smoke(client, models: list[str] | None = None, with_context=True, log=print) -> dict:
    cfg = config.models_config()
    wanted = models or [m["id"] for m in cfg["test_models"]] + [cfg["judge"]["id"]]
    prices = {m["id"]: m for m in cfg["test_models"] + [cfg["judge"]]}
    report = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "available": None, "models": {}}
    try:
        report["available"] = client.list_models()
        log("hosted models visible to this key: " + ", ".join(report["available"]))
    except Exception as e:  # noqa: BLE001
        log(f"could not list models ({e}); testing the configured ones directly")
    decree = contexts._doc("decree")
    ctx_prompt = (f"{contexts.DOC_INTRO['decree']['pt']}\n\n<documento tipo=\"decree\">\n{decree}\n</documento>\n\n{CONTEXT_QUESTION}")
    # The hosted models reason before answering and the reasoning counts against max_output_tokens,
    # so the probes get a generous budget; "incomplete" is recorded when a model still runs out.
    budget = 2000

    def probe(mid):
        r = {"listed": (mid in report["available"]) if report["available"] else None}
        for name, (prompt, _) in PROBES.items():
            try:
                g = client.generate(mid, prompt, temperature=0, max_output_tokens=budget)
                r[name] = {"text": g["text"].strip()[:600], "usage": g["usage"], "latency_s": g["latency_s"],
                           "incomplete": g.get("incomplete")}
                log(f"[{mid}] {name}: {g['text'].strip()[:160]!r}" + (f" (incomplete: {g['incomplete']})" if g.get("incomplete") else ""))
            except LLMError as e:
                r[name] = {"error": str(e)[:300]}
                log(f"[{mid}] {name}: ERROR {str(e)[:200]}")
        if with_context:
            try:
                g = client.generate(mid, ctx_prompt, temperature=0, max_output_tokens=budget)
                u = g["usage"] or {}
                ok = "30 dias" in g["text"] and ("fim do impacto" in g["text"] or "fim de impacto" in g["text"])
                p = prices.get(mid, {})
                cost = (u.get("input_tokens", 0) * p.get("in", 0) + u.get("output_tokens", 0) * p.get("out", 0)) / 1e6
                r["full_decree"] = {"fits": True, "answer_correct": ok, "text": g["text"].strip()[:300],
                                    "input_tokens": u.get("input_tokens"), "usage": u, "credits_this_call": round(cost, 4),
                                    "latency_s": g["latency_s"], "incomplete": g.get("incomplete")}
                log(f"[{mid}] full decree: fits, {u.get('input_tokens')} input tokens, {g['latency_s']} s, "
                    f"answer {'correct' if ok else 'CHECK BY HAND'}: {g['text'].strip()[:140]!r}")
            except LLMError as e:
                r["full_decree"] = {"fits": False, "error": str(e)[:300]}
                log(f"[{mid}] full decree: FAILED {str(e)[:200]}")
        return mid, r

    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=len(wanted)) as ex:  # one model must not hold up the others
        for mid, r in ex.map(probe, wanted):
            report["models"][mid] = r
    paths.RESULTS.mkdir(exist_ok=True)
    (paths.RESULTS / "smoke.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    log(f"\nreport: {paths.RESULTS / 'smoke.json'}")
    log("Next: copy each model's stated cutoff into config/models.json (training_cutoff) and drop any model "
        "that failed the full-decree call.")
    return report


def estimate(standard: dict, models_cfg: dict, conditions, reps: int, log=print) -> dict:
    """Rough token and credit budget before launching (no API calls)."""
    nq = len(standard["questions"])
    doc_tokens = {}
    for c in conditions:
        if contexts.missing_docs(c):
            doc_tokens[c] = None
            continue
        doc_tokens[c] = sum(contexts.approx_tokens(contexts._doc(d)) for d in contexts.CONDITION_DOCS[contexts.base_condition(c)])
    total = 0.0
    rows = []
    for m in models_cfg["test_models"]:
        tin = sum((doc_tokens[c] or 0) + 200 for c in conditions) * nq * reps
        tout = 3500 * nq * reps * len(conditions)  # measured in the pilot: answer + reasoning at effort "medium"
        cost = (tin * m["in"] + tout * m["out"]) / 1e6
        total += cost
        rows.append((m["id"], tin, tout, cost))
    j = models_cfg["judge"]
    n_ans = nq * reps * len(conditions) * len(models_cfg["test_models"])
    # the judge reads the full decree-law (prompt v2) plus rubric, checklist and answer; about 3,000 output tokens with reasoning
    jin, jout = n_ans * (contexts.approx_tokens(contexts._doc("decree")) + 6000), n_ans * 3000
    jcost = (jin * j["in"] + jout * j["out"]) / 1e6
    log(f"{nq} questions x {len(models_cfg['test_models'])} models x {len(conditions)} conditions x {reps} reps = {n_ans} answers")
    log("approx. document tokens per condition: " + ", ".join(f"{c}={v if v is not None else 'MISSING'}" for c, v in doc_tokens.items()))
    for mid, tin, tout, cost in rows:
        log(f"  {mid:22s} in ~{tin / 1e6:6.2f}M  out ~{tout / 1e6:5.2f}M  ~{cost:7.2f} credits (no cache discount)")
    log(f"  judge {j['id']:16s} in ~{jin / 1e6:6.2f}M  out ~{jout / 1e6:5.2f}M  ~{jcost:7.2f} credits")
    log(f"  TOTAL ~{total + jcost:.1f} credits (docs pricing of 14 Nov 2026; token counts are estimates)")
    return {"answers": n_ans, "credits": total + jcost}
