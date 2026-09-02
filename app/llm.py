"""One structured call to an OpenAI-compatible chat endpoint.

Two providers, both first-class, chosen by APERTURE_PROVIDER and never inferred from which key
happens to be set:

    minimax (default)  https://api.minimaxi.com/v1   MINIMAX_API_KEY   MiniMax-M3
    mistral            https://api.mistral.ai/v1     MISTRAL_API_KEY   glm-5-2

Calls are STREAMED, which makes `timeout` an idle timeout: the call runs as long as tokens keep
arriving and dies only after that many seconds of silence. This matters — a long <think> trace on
a full transcript legitimately runs minutes, and a fixed total cap strangles healthy calls while
still not catching a real hang. Learned the hard way in the old engine.

Thinking stays on; `<think>...</think>` is stripped before the JSON is parsed.

Tests never reach the network. APERTURE_REPLAY=<dir> serves recorded answers and raises on a miss;
APERTURE_RECORD=<dir> writes each live answer there. That is the whole record/replay loop: run a
phase once against M3, commit the recordings, and the suite replays them offline forever.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path

import httpx

PROVIDERS = {
    "minimax": ("https://api.minimaxi.com/v1", "MINIMAX_API_KEY", "MiniMax-M3"),
    "mistral": ("https://api.mistral.ai/v1", "MISTRAL_API_KEY", "glm-5-2"),
}
DEFAULT_PROVIDER = "minimax"
IDLE_TIMEOUT = 180.0

_THINK = re.compile(r"<think>.*?</think>", re.S)
_FENCE = re.compile(r"^\s*```(?:json)?\s*|\s*```\s*$", re.S)

# Set by jobs.py around a run so usage lands on the right run row.
usage: dict = {"tokens_in": 0, "tokens_out": 0}


class LLMError(RuntimeError):
    pass


def provider() -> str:
    name = (os.environ.get("APERTURE_PROVIDER") or DEFAULT_PROVIDER).strip().lower()
    if name not in PROVIDERS:
        raise LLMError(f"unknown provider {name!r}; choose one of {sorted(PROVIDERS)}")
    return name


def model() -> str:
    return os.environ.get("APERTURE_MODEL") or PROVIDERS[provider()][2]


def _endpoint() -> tuple[str, str]:
    base_default, key_env, _ = PROVIDERS[provider()]
    base = os.environ.get("APERTURE_BASE_URL") or base_default
    key = os.environ.get(key_env, "").strip()
    if not key:
        raise LLMError(f"set {key_env} for provider {provider()!r}")
    return base.rstrip("/"), key


def _key(label: str, system: str, user: str) -> str:
    h = hashlib.sha256(f"{label}\x00{system}\x00{user}".encode()).hexdigest()[:16]
    return f"{label or 'call'}-{h}"


def parse(raw: str) -> dict:
    """Model text → dict. Strips thinking and code fences, then finds the outermost JSON object."""
    text = _FENCE.sub("", _THINK.sub("", raw or "")).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end <= start:
            raise LLMError(f"no JSON object in model output: {text[:200]!r}")
        return json.loads(text[start:end + 1])


def chat_json(system: str, user: str, *, label: str = "", timeout: float | None = None) -> dict:
    """The only way this codebase talks to a model."""
    replay = os.environ.get("APERTURE_REPLAY")
    if replay:
        path = Path(replay) / f"{_key(label, system, user)}.json"
        if not path.exists():
            raise LLMError(f"no recording for {label!r} at {path}. Record one with "
                           f"APERTURE_RECORD, or fix the prompt back to what was recorded.")
        return json.loads(path.read_text())

    base, key = _endpoint()
    body = {"model": model(), "stream": True, "stream_options": {"include_usage": True},
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}]}
    chunks: list[str] = []
    with httpx.Client(timeout=httpx.Timeout(30.0, read=timeout or IDLE_TIMEOUT)) as client:
        with client.stream("POST", f"{base}/chat/completions",
                           headers={"Authorization": f"Bearer {key}"}, json=body) as r:
            if r.status_code >= 400:
                raise LLMError(f"{r.status_code} from {base}: {r.read()[:300]!r}")
            for line in r.iter_lines():
                if not line.startswith("data: "):
                    continue
                payload = line[6:].strip()
                if payload == "[DONE]":
                    break
                try:
                    ev = json.loads(payload)
                except json.JSONDecodeError:
                    continue
                for choice in ev.get("choices") or []:
                    chunks.append((choice.get("delta") or {}).get("content") or "")
                if u := ev.get("usage"):
                    usage["tokens_in"] += u.get("prompt_tokens", 0) or 0
                    usage["tokens_out"] += u.get("completion_tokens", 0) or 0

    out = parse("".join(chunks))
    if record := os.environ.get("APERTURE_RECORD"):
        d = Path(record)
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{_key(label, system, user)}.json").write_text(json.dumps(out, indent=1,
                                                                       ensure_ascii=False))
    return out


def prompt(name: str, **slots: str) -> tuple[str, str]:
    """Load `prompts/<name>.md` and fill its slots. The file is split at the first line that is
    exactly `---`: everything above is the system message, everything below the user message.

    Slots are `{{name}}`. A slot the file does not use is an error — it means the prompt and the
    code that fills it have drifted apart, which is exactly the bug this catches."""
    path = Path(__file__).parent / "prompts" / f"{name}.md"
    text = path.read_text()
    head, _, body = text.partition("\n---\n")
    if not body:
        raise LLMError(f"{path} has no '---' line separating system from user message")
    for slot, value in slots.items():
        token = "{{%s}}" % slot
        if token not in text:
            raise LLMError(f"{path} has no slot {token}")
        head, body = head.replace(token, str(value)), body.replace(token, str(value))
    if left := re.findall(r"\{\{(\w+)\}\}", head + body):
        raise LLMError(f"{path}: unfilled slots {sorted(set(left))}")
    return head.strip(), body.strip()
