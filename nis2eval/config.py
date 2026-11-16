from __future__ import annotations

import json
import os

from . import paths


def load_env(path=paths.ENV) -> dict:
    """Tiny .env reader. Accepts `KEY=value` and `key = value`; keys are case-insensitive."""
    out = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            out[k.strip().upper()] = v.strip().strip('"').strip("'")
    return out


def api_key() -> str:
    key = os.environ.get("ADAPTION_API_KEY") or load_env().get("ADAPTION_API_KEY")
    if not key:
        raise SystemExit("No API key. Put `adaption_api_key = pt_live_...` in .env or export ADAPTION_API_KEY.")
    return key


def api_keys() -> list[str]:
    """All keys: ADAPTION_API_KEY, ADAPTION_API_KEY_2, ... from the environment or .env, in name order.

    NIS2_KEYS="1,2" restricts a process to some of them (1-based), so that two jobs running side by
    side (generation and grading) do not draw on the same key's rate limit.
    """
    env = {**load_env(), **{k: v for k, v in os.environ.items() if k.upper().startswith("ADAPTION_API_KEY")}}
    names = sorted((k for k in env if k.upper().startswith("ADAPTION_API_KEY") and env[k]),
                   key=lambda k: (len(k), k))
    keys = list(dict.fromkeys(env[k] for k in names))
    if not keys:
        raise SystemExit("No API key. Put `adaption_api_key = pt_live_...` in .env or export ADAPTION_API_KEY.")
    pick = os.environ.get("NIS2_KEYS", "").strip()
    if pick:
        keys = [keys[int(i) - 1] for i in pick.split(",") if i.strip() and 0 < int(i) <= len(keys)] or keys
    return keys


def models_config() -> dict:
    return json.loads(paths.MODELS.read_text(encoding="utf-8"))
