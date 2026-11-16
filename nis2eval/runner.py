"""Runner: questions x models x conditions x repetitions -> results/<run>/answers.jsonl.

Append-only with resume: every finished call is written at once, and a rerun skips
whatever is already there, so a crash or a rate limit loses nothing."""
from __future__ import annotations

import hashlib
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from . import contexts
from .llm import LLMError


BREAK_AFTER = 5


def answer_key(model, cond, qid, rep, lang) -> str:
    return hashlib.sha1(f"{contexts.PROMPT_VERSION}|{model}|{cond}|{qid}|{rep}|{lang}".encode()).hexdigest()[:16]


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    pass  # a half-written last line after a crash
    return out


def run(client, questions, models, conditions, reps, out_dir: Path, lang="pt", gen=None, concurrency=4,
        mock=False, log=print) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "answers.jsonl"
    # An answer counts as done only if it answers the question as it is worded now. If a question is
    # reworded after a run, the next pass asks it again; the newer record replaces the older (latest_ok).
    wording = {q["id"]: q[f"question_{lang}"] for q in questions}
    done, stale = {}, set()
    for r in read_jsonl(path):
        if r.get("status") != "ok":
            continue
        if "question" in r and r["qid"] in wording and r["question"] != wording[r["qid"]]:
            stale.add(r["key"]); done.pop(r["key"], None)
        else:
            stale.discard(r["key"]); done[r["key"]] = r
    if stale:
        log(f"!! {len(stale)} stored answers were given to an earlier wording of their question; asking again")
    gen = gen or {}
    usable = []
    for c in conditions:
        miss = contexts.missing_docs(c)
        if miss:
            log(f"!! skipping condition {c}: missing {', '.join(miss)}")
        else:
            usable.append(c)
    # base conditions first: pushback variants need the base answer
    ordered = sorted(usable, key=lambda c: c.endswith("p"))
    lock = threading.Lock()
    stats = {"ok": 0, "skipped": 0, "error": 0}
    # Circuit breaker: a model that is down costs about 10 minutes of retries per call. After
    # BREAK_AFTER failures in a row its remaining calls are left for the next pass (rerun = resume).
    streak: dict = {}
    tripped: set = set()

    def one(model, cond, q, rep):
        key = answer_key(model, cond, q["id"], rep, lang)
        if key in done:
            return "skipped"
        if model in tripped:
            return "error"
        prior = None
        if cond.endswith("p"):
            base = done.get(answer_key(model, contexts.base_condition(cond), q["id"], rep, lang))
            if not base:
                return "error"
            prior = base["answer"]
        instructions, inp = contexts.build_input(q, cond, lang, prior_answer=prior, tag_qid=mock)
        rec = {"key": key, "model": model, "condition": cond, "qid": q["id"], "rep": rep, "lang": lang,
               "question": q[f"question_{lang}"], "prompt_version": contexts.PROMPT_VERSION, "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
               "gen": {k: gen.get(k) for k in ("temperature", "max_output_tokens", "reasoning_effort")}}
        try:
            r = client.generate(model, inp, instructions=instructions, temperature=gen.get("temperature"),
                                max_output_tokens=gen.get("max_output_tokens"), reasoning_effort=gen.get("reasoning_effort"))
            rec.update(status="ok" if r["text"].strip() else "empty", answer=r["text"], usage=r["usage"],
                       api_status=r["status"], incomplete=r.get("incomplete"), latency_s=r["latency_s"])
        except LLMError as e:
            rec.update(status="error", error=str(e)[:800], answer="")
        with lock:
            with path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            if rec["status"] == "ok":
                done[key] = rec
            if rec["status"] == "error":  # an empty answer is the model's doing, not an outage
                streak[model] = streak.get(model, 0) + 1
                if streak[model] >= BREAK_AFTER and model not in tripped:
                    tripped.add(model)
                    log(f"!! {model}: {BREAK_AFTER} failed calls in a row ({rec['error'][:120]}). "
                        f"Leaving its remaining calls for the next pass.")
            else:
                streak[model] = 0
        return "ok" if rec["status"] == "ok" else "error"

    for phase in (False, True):
        # Order: repetition, then condition, then question, then model. Models are interleaved so that
        # the calls in flight are spread over all of them (one slow model does not hold every slot), and
        # a complete first repetition exists early, so grading and a first analysis can start on it.
        jobs = [(m, c, q, r) for r in range(reps) for c in ordered if c.endswith("p") == phase
                for q in questions for m in models]
        if not jobs:
            continue
        log(f"{len(jobs)} calls ({'pushback' if phase else 'base'} conditions: "
            f"{', '.join(c for c in ordered if c.endswith('p') == phase)})")
        with ThreadPoolExecutor(max_workers=concurrency) as ex:
            futs = [ex.submit(one, *j) for j in jobs]
            for i, f in enumerate(as_completed(futs), 1):
                stats[f.result()] += 1
                if i % 25 == 0 or i == len(futs):
                    log(f"  {i}/{len(futs)}  ok={stats['ok']} skipped={stats['skipped']} error={stats['error']}")
    return stats


def latest_ok(path: Path) -> list[dict]:
    """One record per key (the last successful one)."""
    best = {}
    for r in read_jsonl(path):
        if r.get("status") == "ok":
            best[r["key"]] = r
    return list(best.values())
