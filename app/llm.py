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

import contextlib
import contextvars
import hashlib
import json
import logging
import os
import re
import threading
import time
from collections.abc import Callable, MutableMapping
from pathlib import Path

import httpx

# One line per model call on stdout, where the host collects it (docs/DEPLOY.md → Monitoring).
# Ids, counts and seconds only: the prompt, the material and the model's answer never go in here.
log = logging.getLogger("aperture")

# base url · key variable · default model · default reasoning effort
# M3 reasons by default and takes no effort parameter. GLM on Mistral reasons only when asked:
# left alone it answered a full interview in 4.4k output tokens against M3's 62.8k and found
# a third fewer claims, so "off" is not a neutral default here — it is a thinner reading.
PROVIDERS = {
    "minimax": ("https://api.minimaxi.com/v1", "MINIMAX_API_KEY", "MiniMax-M3", ""),
    "mistral": ("https://api.mistral.ai/v1", "MISTRAL_API_KEY", "glm-5-2", "high"),
}
DEFAULT_PROVIDER = "minimax"
IDLE_TIMEOUT = 180.0

# What a call is asked to think, by what it is for. FRAME describes a layout and names labels a
# Python scan already found; ANGLES ranges rather than weighs. THREAD judges evidence like the
# rest, but it runs once per theme: at the provider default one nine-theme material's DOC step
# measured 1351 s and 151,768 output tokens, the dominant cost of the whole chain. ACCOUNT is the
# same shape of cost — one call per theme at the end of every chain — over claims already checked
# against the material. Every other call — READ, THEMES, DOC, PROJECT, CHECK — keeps the
# provider's default.
EFFORT = {"frame": "", "angles": "low", "thread": "medium", "account": "medium",
          "verify": "medium", "verify_summary": "medium"}

_THINK = re.compile(r"<think>.*?</think>", re.S)
_FENCE = re.compile(r"^\s*```(?:json)?\s*|\s*```\s*$", re.S)

# Seconds between attempts while the provider is loaded. Five waits, then the error stands.
BUSY_WAITS = (15, 30, 60, 120, 240)
_sleep = time.sleep

# The token counter and the progress hook are PER CONTEXT, not per process. A chain runs several
# materials side by side (`jobs.PARALLEL`), and one module-level dict billed one material's tokens
# to another material's run row — which is why nothing could run in parallel before. A thread
# started with `contextvars.copy_context().run` inherits both, and `jobs` replaces both around
# every step, so each step's tokens and each step's progress line land on its own row.
_usage: contextvars.ContextVar[dict] = contextvars.ContextVar("usage")
_report: contextvars.ContextVar[Callable[[str], None]] = contextvars.ContextVar(
    "report", default=lambda msg: None)

# Which run row a call made from here belongs to. Beside the counter rather than inside it: the
# counter is a dict several calls of one wave SHARE, and `dict(llm.usage)` is read as a pair of
# totals in three places. Outside a step there is no run, and such a call still records itself.
_run: contextvars.ContextVar[str | None] = contextvars.ContextVar("run", default=None)

# THIS call's own usage, as the provider reported it — never the step counter's before/after
# difference. A wave of THREAD calls shares one step counter, so a difference measured around one
# call includes whatever its wave-mates spent in the same seconds; the `call` row has to be this
# call's alone (AR-09). Set fresh per attempt in `chat_json`, filled in `_send`.
_call: contextvars.ContextVar[dict | None] = contextvars.ContextVar("call", default=None)


class _Usage(MutableMapping):
    """`llm.usage`, one counter per context. A mapping rather than a function so no caller
    changed: `usage["tokens_in"] += n`, `usage.get(...)`, `usage.update(...)` and `dict(usage)`
    all still mean what they meant when this was a module-level dict."""

    def _d(self) -> dict:
        d = _usage.get(None)
        if d is None:
            d = {"tokens_in": 0, "tokens_out": 0}
            _usage.set(d)
        return d

    def __getitem__(self, k):
        return self._d()[k]

    def __setitem__(self, k, v):
        self._d()[k] = v

    def __delitem__(self, k):
        del self._d()[k]

    def __iter__(self):
        return iter(self._d())

    def __len__(self):
        return len(self._d())

    def __repr__(self):
        return repr(self._d())


usage = _Usage()

# A wave of THREAD calls shares one counter (the dict its context inherited), and `+=` on a dict is
# read-then-write. Without this two calls that finish together bill one of them to nobody.
_TOKENS = threading.Lock()


def new_usage(run_id: str | None = None) -> None:
    """Start this context's counter at zero, as a NEW dict — a context that inherited another
    step's counter must not go on adding to it — and say which run row the calls made from here
    belong to, so each of them can record itself under the step that paid for it."""
    _usage.set({"tokens_in": 0, "tokens_out": 0})
    _run.set(run_id)


def report(msg: str) -> None:
    """Where the step has got to, on the row the page is already reading. Outside a step nobody
    is listening; while several steps run at once each one writes on its own row."""
    _report.get()(msg)


@contextlib.contextmanager
def reporting(hook: Callable[[str], None]):
    """`report` writes here for the length of this step, in this context and no other."""
    token = _report.set(hook)
    try:
        yield
    finally:
        _report.reset(token)


def _tally(u: dict) -> None:
    """This call's own counters, out of one streamed usage object.

    Four, not two: input, cached input, visible output and reasoning output. A counter the
    provider does not mention is LEFT OUT here and therefore stored NULL — a zero would claim the
    call cached nothing, which is not what a provider that never mentions caching has said, and a
    saving nobody can measure is a saving nobody may claim (AR-09).

    Both the nested shape the OpenAI-compatible providers document and a flat one are read, since
    the two this speaks to do not agree on where they put it.
    """
    mine = _call.get()
    if mine is None:
        return
    mine["tokens_in"] = mine.get("tokens_in", 0) + (u.get("prompt_tokens") or 0)
    mine["tokens_out"] = mine.get("tokens_out", 0) + (u.get("completion_tokens") or 0)
    for key, block, field in (
            ("tokens_cached", "prompt_tokens_details", "cached_tokens"),
            ("tokens_reasoning", "completion_tokens_details", "reasoning_tokens")):
        d = u.get(block)
        got = d.get(field) if isinstance(d, dict) else None
        if got is None:
            got = u.get(field)
        if got is not None:
            mine[key] = mine.get(key, 0) + got


def _now() -> str:
    """The wall clock every other row in this database is stamped with."""
    from . import store
    return store.now()


def _record(label: str, attempt: int, got: dict, started: str, seconds: float, status: str,
            error: str = "") -> None:
    """One `call` row for one attempt (AR-09), so a step's dozen calls are no longer one total.

    On its OWN connection: a call runs in whatever thread its wave put it in, and a sqlite
    connection belongs to one thread. Opening one costs a couple of milliseconds against a call
    that costs a minute. A failure here is logged and swallowed — bookkeeping must never be able
    to lose an answer that has already been paid for.

    ponytail: a connection per attempt, re-running the migration each time. A connection cached
    per thread if a wave ever shows up in a profile.
    """
    try:
        from . import db, store
        conn = db.connect()
        try:
            store.save_call(conn, _run.get(), label, attempt, provider(), model(),
                            reasoning(label), got, started, seconds, status, error)
        finally:
            conn.close()
    except Exception as e:                  # noqa: BLE001 — never the calling step's problem
        log.warning("call label=%s not recorded: %.80s", label, e)


class LLMError(RuntimeError):
    pass


class _Busy(LLMError):
    """A provider that is loaded, not one that is refusing: 429, or anything 5xx. Waiting is the
    answer, so this is retried where a plain LLMError is not. `after` is its Retry-After header."""

    def __init__(self, message: str, after: str = "", status: int = 0):
        super().__init__(message)
        self.after, self.status = after, status


def provider() -> str:
    name = (os.environ.get("APERTURE_PROVIDER") or DEFAULT_PROVIDER).strip().lower()
    if name not in PROVIDERS:
        raise LLMError(f"unknown provider {name!r}; choose one of {sorted(PROVIDERS)}")
    return name


def model() -> str:
    """This provider's model. Overrides are per provider — `MISTRAL_MODEL`, `MINIMAX_MODEL` —
    so switching provider cannot inherit the other one's settings."""
    p = provider()
    return os.environ.get(f"{p.upper()}_MODEL") or PROVIDERS[p][2]


def reasoning(label: str = "") -> str:
    """How hard the model should think on this call, where the provider takes an instruction.
    `off` sends nothing; a provider whose default is already to reason is left alone. The env
    override is global on purpose: it is how a whole run is turned up or down at once."""
    v = os.environ.get("APERTURE_REASONING")
    if v is None:
        v = PROVIDERS[provider()][3]
        v = EFFORT.get(label, v) if v else v     # a provider that takes no effort is sent none
    else:
        v = v.strip().lower()
    return "" if v in ("", "off", "none", "default") else v


def _endpoint() -> tuple[str, str]:
    p = provider()
    base_default, key_env, _, _ = PROVIDERS[p]
    # Per provider, deliberately. A single global APERTURE_BASE_URL was a loaded gun: set it for
    # one provider in .env, switch APERTURE_PROVIDER, and the new provider's key goes to the old
    # provider's endpoint. That is a 401 if you are lucky and a silent mis-route if you are not.
    base = os.environ.get(f"{p.upper()}_BASE_URL") or base_default
    key = os.environ.get(key_env, "").strip()
    if not key:
        raise LLMError(f"set {key_env} for provider {p!r}")
    return base.rstrip("/"), key


def _key(label: str, system: str, user: str) -> str:
    h = hashlib.sha256(f"{label}\x00{system}\x00{user}".encode()).hexdigest()[:16]
    return f"{label or 'call'}-{h}"


def _content(delta) -> str:
    """The answer out of one streamed delta, whatever shape the provider sends it in.

    A model that reasons may return content as a list of typed blocks rather than a string —
    a `thinking` block and a `text` block. Only the text is the answer; the reasoning is
    discarded here exactly as `<think>...</think>` is discarded below. Joining the blocks
    blindly would splice the model's private deliberation into the JSON it is trying to emit.
    """
    if isinstance(delta, str):
        return delta
    if isinstance(delta, list):
        return "".join(b.get("text") or "" for b in delta
                       if isinstance(b, dict) and b.get("type") in (None, "text"))
    return ""


_RAW_IN_STRING = {"\n": "\\n", "\r": "\\r", "\t": "\\t"}


def _repair(text: str) -> str:
    """Escape what a model leaves raw inside a long string: an unescaped `"` and a raw newline.

    The failure this exists for: the PROJECT step asks for a 300-word summary and a 150-word
    interpretation, and the model writes a term in quotes — `she called it "the shop" and left` —
    or lets a line break into the value. `json.loads` dies at column 420, the one-more-try gets the
    same kind of answer, and nine THREAD calls and a DOC call are thrown away by one stray quote.

    The rule, in one sentence: walking the text with a stack of open containers, a `"` inside a
    string closes it only when the next non-space character is the one the grammar expects there —
    `:` for a string in key position, `,` `}` `]` (or end of text) for one in value position —
    and every other `"` is an inner quote and gets escaped.

    Key position is what makes `the sign said "closed": nobody came` repairable: a bare greedy rule
    would take the `"` before that `:` as the end of the value, because `:` follows it. Here the
    string is a value, `:` is not in its follow set, and the quote is escaped like any other.

    ponytail: an inner quote that happens to be followed by `,` `}` or `]` — `he said "no", then
    left` — still reads as a close and the repair still fails, landing on the one-more-try as
    before. Fixing that needs backtracking; do it if the logs ever show one.
    """
    out: list[str] = []
    stack: list[str] = []           # the open containers, innermost last
    want_key = False                # is the next string a key?
    in_string = is_key = False
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if in_string:
            if c == "\\" and i + 1 < n:               # an escape the model got right, kept whole
                out.append(text[i:i + 2])
                i += 2
                continue
            if c in _RAW_IN_STRING:
                out.append(_RAW_IN_STRING[c])
            elif c == '"':
                j = i + 1
                while j < n and text[j] in " \t\r\n":
                    j += 1
                after = text[j] if j < n else ""
                if (after == ":") if is_key else (after in ",}]" or j >= n):
                    in_string = False
                    out.append('"')
                else:
                    out.append('\\"')
            else:
                out.append(c)
            i += 1
            continue
        if c == '"':
            in_string, is_key = True, want_key
        elif c in "{[":
            stack.append(c)
            want_key = c == "{"
        elif c in "}]":
            if stack:
                stack.pop()
            want_key = False
        elif c == ":":
            want_key = False
        elif c == ",":
            want_key = bool(stack) and stack[-1] == "{"
        out.append(c)
        i += 1
    return "".join(out)


def parse(raw: str, label: str = "") -> dict:
    """Model text → dict. Strips thinking and code fences, then finds the outermost JSON object.
    A slice that still will not parse gets one repair pass (see `_repair`) before it is given up
    on, so the one-more-try in `chat_json` is spent on real failures rather than a stray quote."""
    text = _FENCE.sub("", _THINK.sub("", raw or "")).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end <= start:
            raise LLMError(f"no JSON object in model output: {text[:200]!r}")
        sliced = text[start:end + 1]
        try:
            return json.loads(sliced)
        except json.JSONDecodeError:
            out = json.loads(_repair(sliced))           # still bad → raises, as it did before
            log.info("llm label=%s json=repaired", label)
            return out


def _ask(system: str, user: str, timeout: float | None, effort: str = "", label: str = "") -> str:
    """One streamed call; the model's text, thinking and all, as it arrived."""
    body = {"model": model(), "stream": True, "stream_options": {"include_usage": True},
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}]}
    if effort:
        body["reasoning_effort"] = effort
    # A busy provider is not a failed call. It is the middle of the afternoon, and the answer is
    # to wait — saying so, because a silent chain that takes four minutes looks like a hang.
    for i, wait in enumerate(BUSY_WAITS, 1):
        try:
            return _send(body, timeout)
        # A stream that stalls or drops is the same kind of failure as a busy provider: the answer
        # never arrived, nothing was written, and the thing to do is ask again. Untreated it cost a
        # whole chain — one THEMES call went quiet for longer than IDLE_TIMEOUT and the four
        # syntheses, the theme accounts and the corpus summary after it never ran, with a raw
        # exception name under an empty summary as the only word of what had happened.
        except (_Busy, httpx.TransportError) as e:
            busy = e.after if isinstance(e, _Busy) else ""
            pause = int(busy) if busy.strip().isdigit() else wait
            report(f"{'The model is busy' if isinstance(e, _Busy) else 'The model went quiet'}; "
                   f"trying again in {pause} s (attempt {i} of {len(BUSY_WAITS)})")
            log.info("llm label=%s busy=%s wait=%ss try=%d/%d", label,
                     getattr(e, "status", 0) or type(e).__name__, pause, i, len(BUSY_WAITS))
            _sleep(pause)
    return _send(body, timeout)         # the sixth try, and its error is the one that stands


def _send(body: dict, timeout: float | None) -> str:
    """The request itself, so what is sent can be looked at without a network."""
    base, key = _endpoint()
    chunks: list[str] = []
    with httpx.Client(timeout=httpx.Timeout(30.0, read=timeout or IDLE_TIMEOUT)) as client:
        with client.stream("POST", f"{base}/chat/completions",
                           headers={"Authorization": f"Bearer {key}"}, json=body) as r:
            if r.status_code >= 400:
                detail = f"{r.status_code} from {base}: {r.read()[:300]!r}"
                if r.status_code == 429 or r.status_code >= 500:
                    raise _Busy(detail, r.headers.get("retry-after", ""), r.status_code)
                raise LLMError(detail)
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
                    chunks.append(_content((choice.get("delta") or {}).get("content")))
                if u := ev.get("usage"):
                    with _TOKENS:
                        usage["tokens_in"] += u.get("prompt_tokens", 0) or 0
                        usage["tokens_out"] += u.get("completion_tokens", 0) or 0
                    _tally(u)               # and again on this call's own row, unshared

    return "".join(chunks)


def chat_json(system: str, user: str, *, label: str = "", timeout: float | None = None) -> dict:
    """The only way this codebase talks to a model."""
    replay = os.environ.get("APERTURE_REPLAY")
    if replay:
        path = Path(replay) / f"{_key(label, system, user)}.json"
        if not path.exists():
            raise LLMError(f"no recording for {label!r} at {path}. Record one with "
                           f"APERTURE_RECORD, or fix the prompt back to what was recorded.")
        return json.loads(path.read_text())

    # A model that reasons well still drops an unescaped quote into a long string now and then,
    # and a project summary is two long strings. The second answer nearly always parses; after
    # two the failure is real and lands on the run row as before.
    t0 = time.monotonic()
    spent = usage.get("tokens_in", 0), usage.get("tokens_out", 0)     # this context's, so far
    got: dict = {}
    for attempt in (1, 2):
        # An ATTEMPT is a request that was answered or that failed trying. A wait for a loaded
        # provider is not one: `_ask` may send the same body six times over four minutes without
        # anything coming back or being charged, and counting those as attempts would turn one
        # afternoon of 429s into a record of six analytical readings that never happened.
        got, began, t1 = {}, _now(), time.monotonic()
        _call.set(got)
        try:
            raw = _ask(system, user, timeout, reasoning(label), label)
        except Exception as e:
            # The provider's own error, hard-truncated. What the model was SHOWN is never in it.
            _record(label, attempt, got, began, time.monotonic() - t1, "failed",
                    f"{type(e).__name__}: {e}"[:200])
            log.error("llm label=%s failed=%s: %.120s", label, type(e).__name__, e)
            raise
        try:
            out = parse(raw, label)
        except (json.JSONDecodeError, LLMError) as e:
            # That it would not parse, never the answer itself — here as on the log line below:
            # the answer is the material talked back, and neither leaves with its words in it.
            _record(label, attempt, got, began, time.monotonic() - t1, "invalid_json",
                    "the model's answer was not JSON")
            if attempt == 2:
                log.error("llm label=%s failed=LLMError: the model's answer was not JSON, twice",
                          label)
                raise LLMError(f"the model's answer was not JSON, twice: {e}") from e
            log.info("llm label=%s json=retry", label)
        else:
            _record(label, attempt, got, began, time.monotonic() - t1, "ok")
            break
    log.info("llm label=%s provider=%s model=%s in=%d out=%d%s s=%.1f", label, provider(), model(),
             usage.get("tokens_in", 0) - spent[0], usage.get("tokens_out", 0) - spent[1],
             # Only where the provider said so. Silence is not a cache miss.
             f" cached={got['tokens_cached']}" if "tokens_cached" in got else "",
             time.monotonic() - t0)
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

    # Validate against the TEMPLATE, before anything is substituted, and then substitute in a
    # single pass that never rescans what it just wrote. Both matter: the researcher's own words
    # go into these prompts verbatim by law, and a focus or a piece of feedback that happens to
    # contain {{...}} must not read as a slot — it would have killed the run, or worse, filled
    # itself from a neighbouring slot.
    wanted = set(re.findall(r"\{\{(\w+)\}\}", text))
    if extra := sorted(set(slots) - wanted):
        raise LLMError(f"{path} has no slot(s) {extra}")
    if missing := sorted(wanted - set(slots)):
        raise LLMError(f"{path}: unfilled slots {missing}")

    def fill(s: str) -> str:
        return re.sub(r"\{\{(\w+)\}\}", lambda m: str(slots[m.group(1)]), s)

    return fill(head).strip(), fill(body).strip()
