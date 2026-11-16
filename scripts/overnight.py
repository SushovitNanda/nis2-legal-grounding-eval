#!/usr/bin/env python3
"""The whole full run, with generation and grading side by side. Safe to stop and start again.

    python scripts/overnight.py               # everything
    python scripts/overnight.py --no-stretch  # leave out the pushback conditions
    python scripts/overnight.py --grade-only  # no generation: grade and analyse what exists

Two tracks run at the same time:

  generation  1 core models (C0, C1, C2): first repetition -> blind sample -> the other two
              -- generation then waits: the main judge grades the core (MAIN RESULT, analysed at
                 once), then the second judge grades it again (agreement between judges) --
              2 extra models (supplementary)
              3 pushback conditions (supplementary)
  grading     in passes of 40 answers: the main judge first, on everything; the second judge on
              C0, C1, C2 once the main judge has caught up; a judge that is not answering is skipped;
              after each round the tables, STATUS.txt and an interim analysis are rebuilt

Checkpoints: every answer and every judgment is appended to a file the moment it arrives
(results/full/answers.jsonl, judgments.jsonl). After a shutdown, run the same command again: finished
answers and judgments are skipped. Progress is in results/full/STATUS.txt and overnight.log.

Rate limit: the account has one limit for all keys and models, and it follows the size of the
prompts (measured 15 Nov 2026; four keys did not raise it). Each track is paced by input tokens per
minute and adjusts its own pace when the API refuses a call. While both tracks run, generation
starts with three quarters of the budget and grading with one quarter; while generation waits or is
finished, grading gets all of it. The two tracks share one budget: side by side gives early
results, not a shorter total. That is why the work is ordered by importance.

Not run: C4 (decree-law plus the legal-categories scheme). The scheme is not public, so the
condition could not be reproduced from the repository.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
import re
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN = "full"
OUT = ROOT / "results" / RUN
CORE = ["qwen3.5-397b", "qwen3.8-27b", "gemma-4-31b-it", "deepseek-v4-flash"]
# One supplementary model. glm-5.3-flash was tried and dropped on 15 Nov: at the settings common to
# all models (reasoning effort "medium", 12,000 output tokens) it spent the whole budget reasoning and
# returned no answer in 35 of 53 calls; with room to finish it reasoned for 16,000 to 45,000 tokens.
EXTRA = ["gemma-4-26b-a4b-it"]
JUDGE_MAIN = "qwen3.8-27b"                                 # config/models.json "judge"
JUDGE_2 = "gemma-4-31b-it"                                 # second judge, another family; both stayed up and cache the decree
CORE_CONDS = ["C0", "C1", "C2"]
PUSHBACK = ["C0p", "C1p"]
REPS = "3"
TPM_TOTAL, TPM_GEN, TPM_GRADE = 250_000, 150_000, 100_000   # starting paces; each adjusts itself
PASS_SIZE = "40"

_log_lock = threading.Lock()
gen_done = threading.Event()
gen_busy = threading.Event()     # set while the generation track is calling the API


def log(msg: str) -> None:
    line = f"{time.strftime('%a %H:%M:%S')}  {msg}"
    with _log_lock:
        print(line, flush=True)
        with (OUT / "overnight.log").open("a", encoding="utf-8") as f:
            f.write(line + "\n")


def nis2(track: str, *args: str, tpm: float = 0, tpm_max: float = 0) -> tuple[int, str]:
    env = dict(os.environ, PYTHONIOENCODING="utf-8", NIS2_MAX_RETRIES="2")
    for k in ("NIS2_KEYS", "NIS2_RPM", "NIS2_TPM", "NIS2_TPM_MAX"):
        env.pop(k, None)
    if tpm:
        env["NIS2_TPM"] = str(tpm)
    if tpm_max:
        env["NIS2_TPM_MAX"] = str(tpm_max)
    log(f"[{track}] nis2eval {' '.join(args)}" + (f"   (starting pace {tpm / 1000:.0f}k tokens a minute)" if tpm else ""))
    p = subprocess.Popen([sys.executable, "-u", "-m", "nis2eval", *args], cwd=ROOT, env=env, text=True,
                         encoding="utf-8", errors="replace", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = []
    for line in p.stdout:
        out.append(line)
        if line.strip():
            log(f"[{track}]   {line.rstrip()[:300]}")
    p.wait()
    return p.returncode, "".join(out)


def _rows(name: str) -> list[dict]:
    p = OUT / name
    out = []
    if p.exists():
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return out


def counts() -> tuple[dict, dict]:
    """(current answers by key, {judge: keys of answers it has graded in their current form})."""
    ok = {}
    for r in _rows("answers.jsonl"):
        if r.get("status") == "ok":
            ok[r["key"]] = r
    sha = {k: hashlib.sha1(r["answer"].encode("utf-8")).hexdigest()[:12] for k, r in ok.items()}
    judged = collections.defaultdict(set)
    for r in _rows("judgments.jsonl"):
        if r.get("status") == "ok" and r.get("judge_prompt") == "v2" and r["key"] in ok \
                and r.get("answer_sha", sha[r["key"]]) == sha[r["key"]]:
            judged[r["judge_model"]].add(r["key"])
    return ok, judged


def status() -> None:
    ok, judged = counts()
    by = collections.Counter((r["model"], r["condition"]) for r in ok.values())
    conds = sorted({c for _, c in by})
    lines = [f"Status at {time.strftime('%a %d %b %H:%M:%S')}   (target per cell: 66 = 22 questions x 3 repetitions)", "",
             "answers generated".ljust(24) + "".join(c.rjust(6) for c in conds)]
    for m in CORE + EXTRA:
        lines.append(m.ljust(24) + "".join(str(by.get((m, c), 0)).rjust(6) for c in conds))
    lines += ["", f"total answers: {len(ok)}"]
    for j in (JUDGE_MAIN, JUDGE_2):
        lines.append(f"graded by {j}: {len(judged.get(j, ()))}")
    lines.append(f"generation finished: {gen_done.is_set()}")
    (OUT / "STATUS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def is_up(model: str) -> bool:
    """One short call, no retries: is this model answering right now?"""
    code = subprocess.run([sys.executable, "-c",
                           "import sys; sys.path.insert(0, '.'); from nis2eval.llm import AdaptionClient; "
                           f"AdaptionClient(timeout=90, max_retries=0).generate({model!r}, 'Say: ok', temperature=0, "
                           "max_output_tokens=2000, reasoning_effort='low')"],
                          cwd=ROOT, env=dict(os.environ, PYTHONIOENCODING="utf-8"), capture_output=True).returncode
    return code == 0


def generate(models: list[str], conds: list[str], passes: int = 2, reps: str = REPS) -> None:
    up = [m for m in models if is_up(m)]
    if len(up) < len(models):
        log(f"[gen] not answering now, left for later: {[m for m in models if m not in up]}")
    if not up:
        return
    models = up
    gen_busy.set()
    try:
        for _ in range(passes):   # later passes only redo calls that failed (exit 2)
            code, _out = nis2("gen", "run", "--run", RUN, "--reps", reps, "--conditions", ",".join(conds),
                              "--models", ",".join(models), "--concurrency", "12", tpm=TPM_GEN)
            if code == 0:
                return
        log(f"[gen] !! some answers still missing for {models} / {conds}; run this script again later")
    finally:
        gen_busy.clear()


def wait_until_graded(judge: str, models: list[str], conds: list[str], slack: int = 6, max_hours: float = 8) -> None:
    """Hold generation back until `judge` has graded these answers (all but `slack`)."""
    t0 = time.time()
    said = 0.0
    while time.time() - t0 < max_hours * 3600 and not (OUT / "STOP").exists():
        ok, judged = counts()
        want = {k for k, r in ok.items() if r["model"] in models and r["condition"] in conds}
        left = len(want - judged.get(judge, set()))
        if left <= slack:
            return
        if time.time() - said > 900:
            log(f"[gen] waiting: {judge} still has {left} of {len(want)} answers to grade before generation goes on")
            said = time.time()
        time.sleep(30)


def core_analysis(judge: str) -> None:
    """The analyses of the core models for one judge, with the full 5,000 bootstrap resamples."""
    flag = [] if judge == JUDGE_MAIN else ["--judge", judge]
    cc = ",".join(CORE_CONDS)
    nis2("result", "score", "--run", RUN, "--judge", judge, "--tables-only")
    nis2("result", "analyze", "--run", RUN, "--conditions", cc, "--models", ",".join(CORE), "--tag", "core4", *flag)
    nis2("result", "analyze", "--run", RUN, "--conditions", cc, "--models", ",".join(m for m in CORE if m != judge),
         "--tag", "core-without-judge-model", *flag)
    if judge != JUDGE_MAIN:
        subprocess.run([sys.executable, str(ROOT / "scripts" / "judge_agreement.py"), "--run", RUN, "--a", JUDGE_MAIN, "--b", judge],
                       cwd=ROOT, env=dict(os.environ, PYTHONIOENCODING="utf-8"), capture_output=True)


def generation_track(stretch: bool) -> None:
    try:
        # First one complete repetition of every cell, then the blind sample from it: the human grader
        # gets her 25 answers hours before the other two repetitions are finished. Repetitions are
        # interchangeable, so drawing from the first one does not bias the sample.
        generate(CORE, CORE_CONDS, reps="1")
        nis2("gen", "blind", "--run", RUN, "--n", "25")
        generate(CORE, CORE_CONDS)
        generate(CORE, CORE_CONDS)                # what a model that was down still owes
        # Main result first: nothing else is generated until the core is graded.
        wait_until_graded(JUDGE_MAIN, CORE, CORE_CONDS)
        generate(CORE, CORE_CONDS)                # a last try for missing core answers, before the analysis
        wait_until_graded(JUDGE_MAIN, CORE, CORE_CONDS)
        core_analysis(JUDGE_MAIN)
        log("[gen] MAIN RESULT READY: results/full/analysis-core4 and analysis-core-without-judge-model")
        wait_until_graded(JUDGE_2, CORE, CORE_CONDS)
        core_analysis(JUDGE_2)
        log("[gen] SECOND JUDGE READY: results/full/judge_agreement.md and analysis-judge-" + JUDGE_2 + "-*")
        # Supplementary, only now.
        generate(EXTRA, CORE_CONDS)
        wait_until_graded(JUDGE_MAIN, EXTRA, CORE_CONDS)
        wait_until_graded(JUDGE_2, EXTRA, CORE_CONDS)
        if stretch:
            generate(CORE, PUSHBACK)              # pushback on the model's own answer
    except Exception as e:  # noqa: BLE001
        log(f"[gen] !! stopped: {e!r}")
    finally:
        gen_done.set()
        log("[gen] generation track finished")


def grading_track() -> None:
    idle = passes_after_done = 0
    while True:
        done_before = gen_done.is_set()
        left = 0
        # the second judge grades the core conditions only; the pushback answers get the main judge
        main_behind = False
        for judge, conds in ((JUDGE_MAIN, []), (JUDGE_2, ["--conditions", ",".join(CORE_CONDS)])):
            if judge == JUDGE_2 and main_behind:
                left += 1   # the main judge goes first: the second judge starts when the main one has caught up
                continue
            if not is_up(judge):
                log(f"[grade] {judge} is not answering; skipped this round")
                left += 1
                continue
            alone = not gen_busy.is_set()
            code, out = nis2("grade", "score", "--run", RUN, "--judge", judge, "--limit", PASS_SIZE,
                             "--concurrency", "8" if alone else "4", *conds, tpm=TPM_TOTAL if alone else TPM_GRADE,
                             tpm_max=TPM_TOTAL * 2.5 if alone else 0)
            m = re.search(r"(\d+) to judge", out)
            e = re.findall(r"\(errors: (\d+)\)", out)
            if judge == JUDGE_MAIN and m and int(m.group(1)) > int(PASS_SIZE):
                main_behind = True
            left += (int(m.group(1)) if m else 0) if code == 0 else 1
            left += int(e[-1]) if e else 0
            status()
        # interim numbers on whatever is graded so far; a failure here does not matter
        nis2("grade", "analyze", "--run", RUN, "--boot", "500", "--conditions", ",".join(CORE_CONDS), "--tag", "interim")
        if (OUT / "STOP").exists():
            break
        if left and not gen_busy.is_set() and not any(is_up(j) for j in (JUDGE_MAIN, JUDGE_2)):
            time.sleep(120)   # both judges down: wait, do not spin (161 empty rounds in ten minutes on 15 Nov)
        if done_before:
            passes_after_done += 1
            idle = idle + 1 if left == 0 else 0
            if idle >= 1 or passes_after_done >= 60:
                if left:
                    log(f"[grade] !! {left} judgments still missing; run this script again with --grade-only")
                break
        if left == 0:
            time.sleep(45)
    final_analysis()


def final_analysis() -> None:
    others = lambda j: ",".join(m for m in CORE + EXTRA if m != j)
    cc = ",".join(CORE_CONDS)
    for judge, flag in ((JUDGE_MAIN, []), (JUDGE_2, ["--judge", JUDGE_2])):
        nis2("final", "analyze", "--run", RUN, "--conditions", cc, "--models", ",".join(CORE + EXTRA), "--tag", "all-models", *flag)
        nis2("final", "analyze", "--run", RUN, "--conditions", cc, "--models", ",".join(CORE), "--tag", "core4", *flag)
        nis2("final", "analyze", "--run", RUN, "--conditions", cc, "--models", ",".join(m for m in CORE if m != judge),
             "--tag", "core-without-judge-model", *flag)
        nis2("final", "analyze", "--run", RUN, "--conditions", cc, "--models", others(judge),
             "--tag", "all-without-judge-model", *flag)
    nis2("final", "analyze", "--run", RUN, "--conditions", "C0,C0p,C1,C1p", "--models", ",".join(CORE), "--tag", "pushback")
    subprocess.run([sys.executable, str(ROOT / "scripts" / "judge_agreement.py"), "--run", RUN, "--a", JUDGE_MAIN, "--b", JUDGE_2],
                   cwd=ROOT, env=dict(os.environ, PYTHONIOENCODING="utf-8"), capture_output=True)
    status()
    log("[final] done")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-stretch", action="store_true")
    ap.add_argument("--grade-only", action="store_true", help="no generation: grade and analyse what exists")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.kernel32.SetThreadExecutionState(0x80000001)   # do not sleep while this runs
        except Exception:  # noqa: BLE001
            pass
    log("=== overnight run started ===")
    if a.grade_only:
        gen_done.set()
    else:
        gen_busy.set()
        threading.Thread(target=generation_track, args=(not a.no_stretch,), daemon=True).start()
    grading_track()
    return 0


if __name__ == "__main__":
    sys.exit(main())
