"""Model access. Adaption's hosted models are called through its Responses API
(POST {base_url}/responses, bearer auth, streamed). A deterministic MockClient lets the whole
pipeline run offline for tests - its outputs are NOT results."""
from __future__ import annotations

import hashlib
import json
import os
import random
import re
import sys
import threading
import time

import requests

from . import config

RETRY_STATUS = {408, 409, 425, 429, 500, 502, 503, 504, 520, 522, 524, 529}


class LLMError(RuntimeError):
    pass


class AdaptionClient:
    def __init__(self, base_url: str | None = None, key: str | None = None, timeout: int = 900, max_retries: int = 6):
        # NIS2_MAX_RETRIES: a model whose provider is down (HTTP 502 for hours on 15 Nov) must fail fast,
        # or its retries hold every worker and the healthy models wait behind it.
        max_retries = int(os.environ.get("NIS2_MAX_RETRIES") or max_retries)
        cfg = config.models_config()
        self.base_url = (base_url or cfg["api"]["base_url"]).rstrip("/")
        # Several keys are used side by side: each call goes to the key with the fewest calls in
        # flight, and a key that answers 429 rests for a minute while the others carry on.
        self.keys = [key] if key else config.api_keys()
        self.key = self.keys[0]
        self.timeout = timeout
        self.max_retries = max_retries
        self._lock = threading.Lock()
        self._inflight = [0] * len(self.keys)
        self._resting = [0.0] * len(self.keys)
        self._quiet_until = 0.0          # after a 429 no new call starts for a while, on any key
        # The account has one rate limit for all keys and models, and it follows the size of the prompts:
        # 15 short calls a minute pass, 15 calls carrying the 50,000-token decree do not (measured
        # 15 Nov 2026; four keys did not raise it). NIS2_TPM paces this process by input tokens per
        # minute so that calls are not sent only to be refused. The pace adjusts itself: down by a
        # quarter on every 429, up by 7% after each minute without one, up to a ceiling. Two jobs side by side
        # share the limit: give each its part.
        tpm = float(os.environ.get("NIS2_TPM") or 0)
        # ceiling: NIS2_TPM_MAX (default 15% above the start). A 429 at pace P lowers the ceiling to
        # 0.92 P, so the pace settles just under the limit instead of climbing into it again and again.
        self._tpm, self._tpm_min = tpm, max(30000.0, tpm / 6)
        self._tpm_max = float(os.environ.get("NIS2_TPM_MAX") or 0) or tpm * 1.15
        self._tpm_floor_max = tpm * 0.6
        self._next_slot = 0.0
        self._last_change = time.time()
        self._warm: set = set()          # (model, document prefix) already sent once
        self._warming: dict = {}
        self._sessions = []
        for k in self.keys:
            s = requests.Session()
            s.headers.update({"Authorization": f"Bearer {k}", "Content-Type": "application/json"})
            self._sessions.append(s)
        self.session = self._sessions[0]

    def _take(self) -> int:
        with self._lock:
            now = time.time()
            free = [i for i in range(len(self.keys)) if self._resting[i] <= now] or list(range(len(self.keys)))
            i = min(free, key=lambda j: (self._inflight[j], self._resting[j], random.random()))
            self._inflight[i] += 1
            return i

    def _give(self, i: int, rate_limited: bool = False) -> None:
        with self._lock:
            self._inflight[i] -= 1
            if rate_limited:
                self._resting[i] = time.time() + 60
                self._quiet_until = max(self._quiet_until, time.time() + 20)
                if self._tpm:
                    self._tpm_max = max(self._tpm_floor_max, min(self._tpm_max, self._tpm * 0.92))
                    self._tpm = max(self._tpm_min, self._tpm * 0.75)
                    self._last_change = time.time()

    def _warm_gate(self, model: str, input):
        """One call at a time for a long document that this model has not seen yet.

        The provider caches a long prompt prefix after the first call. Twelve cold calls with the same
        50,000-token document at once is what set off the rate limit (15 Nov); one call first, then
        the rest, does not. Returns a token for the call that goes first, None for all the others.
        """
        text = input if isinstance(input, str) else str((input[0] or {}).get("content", "")) if input else ""
        if len(text) < 20000:
            return None
        k = (model, hashlib.sha1(text[:4000].encode("utf-8")).hexdigest())
        with self._lock:
            if k in self._warm:
                return None
            lk = self._warming.setdefault(k, threading.Lock())
        lk.acquire()
        with self._lock:
            if k in self._warm:
                lk.release()
                return None
        return k, lk

    def _warm_done(self, gate, ok: bool) -> None:
        if gate:
            k, lk = gate
            if ok:
                with self._lock:
                    self._warm.add(k)
            lk.release()

    def list_models(self) -> list[str]:
        r = self.session.get(f"{self.base_url}/models", params={"type": "hosted"}, timeout=60)
        r.raise_for_status()
        data = r.json()
        items = data.get("data", data) if isinstance(data, dict) else data
        return [m.get("id") if isinstance(m, dict) else str(m) for m in items]

    def generate(self, model: str, input, instructions: str | None = None, temperature: float | None = None,
                 max_output_tokens: int | None = None, reasoning_effort: str | None = None) -> dict:
        """`input` is a string or a list of {"role", "content"} messages.
        `reasoning_effort`: "low" | "medium" | "xhigh" (the API default when omitted) | "none".
        Returns {"text", "usage", "status", "model", "latency_s"}."""
        # Streamed: Adaption's gateway answers 504 after 60 s without a byte, and the hosted models
        # reason for a long time before the first word (seen in the smoke test, 14 Nov 2026).
        body = {"model": model, "input": input, "store": False, "stream": True}
        if instructions:
            body["instructions"] = instructions
        if temperature is not None:
            body["temperature"] = temperature
        if max_output_tokens:
            body["max_output_tokens"] = max_output_tokens
        if reasoning_effort:
            body["reasoning"] = {"effort": reasoning_effort}
        last = None
        gate = self._warm_gate(model, input)
        try:
            result = self._generate(model, body)
        except BaseException:
            self._warm_done(gate, False)
            raise
        self._warm_done(gate, True)
        return result

    def _generate(self, model: str, body: dict) -> dict:
        last = None
        inp = body["input"]
        chars = len(inp) if isinstance(inp, str) else sum(len(str(m.get("content", ""))) for m in inp)
        tokens = (chars + len(body.get("instructions") or "")) / 3.2 + 300   # rough; only used for pacing
        for attempt in range(self.max_retries + 1):
            pause = self._quiet_until - time.time()
            if pause > 0:
                time.sleep(pause + random.random() * 5)
            if self._tpm:
                with self._lock:
                    now = time.time()
                    if now - self._last_change > 60:
                        self._tpm = min(self._tpm_max, self._tpm * 1.07)
                        self._last_change = now
                    slot = max(self._next_slot, now)
                    self._next_slot = slot + 60.0 * tokens / self._tpm
                if slot > time.time():
                    time.sleep(slot - time.time())
            t0 = time.time()
            rate_limited = False
            ki = self._take()
            try:
                # read timeout = longest silence tolerated between two events, not the whole call
                with self._sessions[ki].post(f"{self.base_url}/responses", data=json.dumps(body), stream=True,
                                       timeout=(30, min(self.timeout, 240))) as r:
                    if r.status_code == 200:
                        d, deltas, err = _read_stream(r, deadline=t0 + self.timeout)
                        text = (_output_text(d) if d else "") or deltas
                        status = (d or {}).get("status") or ("completed" if text and not err else "failed")
                        if err or status == "failed" or (not d and not text):
                            last = f"failed: {err or (d or {}).get('error') or 'stream ended without a response'}"
                        else:
                            return {"text": text, "usage": d.get("usage") or {}, "status": status,
                                    "incomplete": (d.get("incomplete_details") or {}).get("reason"),
                                    "model": d.get("model", model), "latency_s": round(time.time() - t0, 2)}
                    elif r.status_code in RETRY_STATUS:
                        last = f"HTTP {r.status_code}: {r.text[:300]}"
                        rate_limited = r.status_code == 429
                        if rate_limited:
                            print(f"  (429 rate limit, model {model}; pace now {self._tpm * 0.75 / 1000:.0f}k tokens a minute)"
                                  if self._tpm else f"  (429 rate limit on key {ki + 1} of {len(self.keys)}, model {model})",
                                  file=sys.stderr, flush=True)
                    else:  # 400/401/403/404/422: retrying will not help
                        raise LLMError(f"HTTP {r.status_code} for model {model}: {r.text[:600]}")
            except requests.RequestException as e:
                last = f"network: {e}"
            finally:
                self._give(ki, rate_limited)
            if attempt < self.max_retries:
                # 429 = "Inference rate limit reached for this user; retry after 60 seconds" (all models).
                # With another key free, go to it at once; with every key resting, wait the minute out.
                with self._lock:
                    all_resting = all(t > time.time() for t in self._resting)
                if rate_limited:
                    wait = 60 + 20 * random.random() if all_resting else 1 + 2 * random.random()
                else:
                    wait = min(90, 2 ** attempt * 2) + random.random()
                time.sleep(wait)
        raise LLMError(f"gave up on {model} after {self.max_retries + 1} attempts: {last}")


def _read_stream(r, deadline: float):
    """Read server-sent events. Returns (final response object or None, concatenated text deltas, error or None)."""
    final, deltas, err = None, [], None
    r.encoding = "utf-8"
    for line in r.iter_lines(decode_unicode=True):
        if time.time() > deadline:
            return None, "".join(deltas), "timed out mid-stream"
        if not line or not line.startswith("data:"):
            continue
        payload = line[5:].strip()
        if payload == "[DONE]":
            break
        try:
            ev = json.loads(payload)
        except json.JSONDecodeError:
            continue
        ty = ev.get("type")
        if ty == "response.output_text.delta":
            deltas.append(ev.get("delta") or "")
        elif ty in ("response.completed", "response.incomplete", "response.failed"):
            final = ev.get("response") or final
        elif ty == "error":
            err = json.dumps(ev.get("error") or ev, ensure_ascii=False)[:300]
    if final is None and not err and not deltas:
        err = "stream ended without a response"
    return final, "".join(deltas), err


def _output_text(d: dict) -> str:
    if isinstance(d.get("output_text"), str) and d["output_text"]:
        return d["output_text"]
    parts = []
    for item in d.get("output") or []:
        content = item.get("content")
        if isinstance(content, str):
            parts.append(content)
        for c in content or [] if isinstance(content, list) else []:
            if c.get("type") in ("output_text", "text") and c.get("text"):
                parts.append(c["text"])
    return "".join(parts)


class MockClient:
    """Offline stand-in. Answers are assembled from the reference standard with a
    condition-dependent amount of coverage and planted errors, so that every stage
    (runner, scorer, analysis, blind sample, agreement) can be exercised without a key.
    Mock answers carry [[item:x]] markers that the mock judge reads."""

    def __init__(self, standard: dict):
        self.q = {q["id"]: q for q in standard["questions"]}

    def list_models(self):
        return ["mock-large", "mock-small"]

    def generate(self, model, input, instructions=None, temperature=None, max_output_tokens=None, reasoning_effort=None):
        text = input if isinstance(input, str) else "\n".join(str(m.get("content", "")) for m in input)
        if instructions and "JUDGE" in instructions:
            return {"text": self._judge(text), "usage": {"input_tokens": len(text) // 4, "output_tokens": 200},
                    "status": "completed", "incomplete": None, "model": model, "latency_s": 0.0}
        m = re.search(r"\[qid:(L\d-\d\d)\]", text)
        q = self.q[m.group(1)] if m else next(iter(self.q.values()))
        has_decree = "Decreto-Lei n.º 125/2025, de 4 de dezembro" in text and "<documento" in text
        has_directive = "<documento" in text and not has_decree
        seed = int(hashlib.sha256((model + text[-400:] + str(temperature)).encode()).hexdigest(), 16) % 10**8
        seed += random.randrange(10**6)  # repetitions differ, as with temperature > 0
        rng = random.Random(seed)
        p_cov = (0.85 if has_decree else 0.35 if has_directive else 0.5) - (0.1 if "small" in model else 0)
        out = []
        for it in q["items"]:
            if rng.random() < p_cov:
                cert = "certain"
                if it["status"] != "verified":
                    cert = "flagged" if rng.random() < (0.6 if has_decree else 0.25) else "certain"
                cite = f" ({it['citation_raw']})" if it["citation_raw"].startswith("art") else ""
                hedge = " Isto depende de regulamentação do CNCS e não pode ser afirmado com certeza." if cert == "flagged" else ""
                out.append(f"[[item:{it['id']}:{cert}]] {it['text_en']}{cite}.{hedge}")
        if not has_decree and rng.random() < 0.6:
            out.append("[[fab]] Nos termos do artigo 142.º, n.º 3, a notificação é feita em 48 horas.")
        if (has_directive and rng.random() < 0.8) or (not has_decree and rng.random() < 0.3):
            out.append("[[juris]] Nos termos do artigo 23.º, n.º 4, da Diretiva (UE) 2022/2555, alerta precoce em 24 horas e notificação em 72 horas.")
        if has_directive and rng.random() < 0.4:
            out.append("[[mismatch]] Nota: o texto fornecido é a Diretiva e não a lei portuguesa de transposição.")
        if q.get("decree_silent") and rng.random() < (0.7 if has_decree else 0.3):
            out.append("[[gap]] O decreto-lei não fixa este valor; remete para regulamentação.")
        ans = "\n".join(out) or "Não sei responder."
        return {"text": ans, "usage": {"input_tokens": len(text) // 4, "output_tokens": len(ans) // 4},
                "status": "completed", "incomplete": None, "model": model, "latency_s": 0.0}

    def _judge(self, text: str) -> str:
        ans = text.split("<answer>", 1)[-1].split("</answer>", 1)[0]
        ids = re.findall(r'^- id: ([a-z]) \| status: ([a-z ]+)', text, flags=re.M)
        marks = dict(re.findall(r"\[\[item:([a-z]):(certain|flagged)\]\]", ans))
        items = []
        for iid, status in ids:
            cov = "covered" if iid in marks else "not_covered"
            unc = "not_addressed" if iid not in marks else ("flagged" if marks[iid] == "flagged" else "stated_as_certain")
            items.append({"id": iid, "coverage": cov, "uncertainty": unc, "quote": ""})
        return json.dumps({
            "items": items,
            "fabricated_claims": [{"claim": "art. 142.º, n.º 3: 48 horas", "why": "no such article"}] if "[[fab]]" in ans else [],
            "outside_reference_claims": [],
            "jurisdiction_confusion": {"present": "[[juris]]" in ans, "examples": []},
            "says_decree_does_not_answer": "[[gap]]" in ans,
            "flags_source_mismatch": "[[mismatch]]" in ans,
        })
