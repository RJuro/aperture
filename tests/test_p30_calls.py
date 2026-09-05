"""P30 — one record per model call, a synthesis that resumes, and one lock per project.

Three findings of the audit, and they are one finding: a STEP was the smallest thing this
instrument could see, record or stop.

    a step's dozen calls were one pair of totals   no attempt, no cached input, no reasoning
                                                   split, and a per-call log line whose before/
                                                   after difference could include a wave-mate's
                                                   tokens
    a synthesis was one step                       an interruption half way through replayed
                                                   every line that had already been written,
                                                   checked and paid for
    one lock held the whole process                a long corpus held every unrelated project on
                                                   the instance behind it

The rule underneath the `call` table: **unknown is NULL, never nought.** A provider that says
nothing about caching has not said that nothing was cached, and a saving nobody can measure is a
saving nobody may claim.
"""
from __future__ import annotations

import json
import threading
import time

import pytest

from app import db, jobs, llm, store
from app.engine import synth


# ---- a provider, without a socket ---------------------------------------------------------------

def _provider(monkeypatch, usage: dict, answer: str = '{"ok": 1}'):
    """One streamed answer followed by one usage object, over httpx's own MockTransport.

    Through the real `_send`, deliberately: the field names this reads — `prompt_tokens_details.
    cached_tokens` and the rest — are only worth testing where they are read out of a response a
    provider could actually have sent.
    """
    real = llm.httpx.Client

    def reply(request):
        sse = (b'data: {"choices":[{"delta":{"content":' + json.dumps(answer).encode() + b'}}],'
               b'"usage":' + json.dumps(usage).encode() + b'}\n\n')
        return llm.httpx.Response(200, content=iter([sse]),
                                  headers={"content-type": "text/event-stream"})

    class Client(real):
        def __init__(self, **kw):
            super().__init__(transport=llm.httpx.MockTransport(reply), **kw)

    monkeypatch.setattr(llm.httpx, "Client", Client)


@pytest.fixture
def step(conn, project):
    """A run row to bill calls to, and the context that says so."""
    rid = store.start_run(conn, project, "thread", None, "Writing a line")
    llm.new_usage(rid)
    return rid


# ---- what one call leaves behind ----------------------------------------------------------------

def test_a_call_records_its_run_its_tokens_and_that_it_was_answered(conn, step, real_chat_json,
                                                                    monkeypatch):
    _provider(monkeypatch, {"prompt_tokens": 7692, "completion_tokens": 1681})
    assert real_chat_json("a system message", "the material", label="thread") == {"ok": 1}

    row, = store.calls(conn, step)
    assert (row["run_id"], row["label"], row["attempt"], row["status"]) == \
        (step, "thread", 1, "ok")
    assert (row["tokens_in"], row["tokens_out"]) == (7692, 1681)
    assert (row["provider"], row["model"]) == ("minimax", "MiniMax-M3")
    assert row["seconds"] >= 0 and row["started"] and row["finished"]


def test_a_provider_that_says_nothing_about_caching_leaves_it_null(conn, step, real_chat_json,
                                                                   monkeypatch):
    """Nought would assert that this call cached nothing, which is not what silence says."""
    _provider(monkeypatch, {"prompt_tokens": 100, "completion_tokens": 40})
    real_chat_json("s", "u", label="thread")

    row, = store.calls(conn, step)
    assert row["tokens_cached"] is None and row["tokens_reasoning"] is None


def test_the_four_counters_are_kept_apart_where_the_provider_reports_them(conn, step,
                                                                          real_chat_json,
                                                                          monkeypatch):
    """Cached input and reasoning output are what the stable-prefix ordering and the per-stage
    effort settings would have to be measured against. Aggregated away, neither can be."""
    _provider(monkeypatch, {"prompt_tokens": 9000, "completion_tokens": 400,
                            "prompt_tokens_details": {"cached_tokens": 7800},
                            "completion_tokens_details": {"reasoning_tokens": 310}})
    real_chat_json("s", "u", label="thread")

    row, = store.calls(conn, step)
    assert (row["tokens_in"], row["tokens_cached"]) == (9000, 7800)
    assert (row["tokens_out"], row["tokens_reasoning"]) == (400, 310)


def test_a_second_try_at_an_answer_that_would_not_parse_is_a_second_row(conn, step,
                                                                        real_chat_json,
                                                                        monkeypatch):
    answers = ["the model wrote prose instead", '{"ok": 1}']
    monkeypatch.setattr(llm, "_ask", lambda *a, **k: answers.pop(0))
    assert real_chat_json("s", "u", label="thread") == {"ok": 1}

    one, two = store.calls(conn, step)
    assert (one["attempt"], one["status"]) == (1, "invalid_json")
    assert (two["attempt"], two["status"]) == (2, "ok")
    assert "prose instead" not in (one["error"] or ""), \
        "that it would not parse, never the answer: the answer is the material talked back"


def test_a_wait_for_a_busy_provider_is_not_an_attempt(conn, step, real_chat_json, monkeypatch):
    """Three requests, one answer. A 429 charges nothing and reads nothing, and counting those
    as attempts would turn one rate-limited afternoon into a record of readings that never
    happened."""
    tries = []

    def busy_twice(body, timeout):
        tries.append(1)
        if len(tries) < 3:
            raise llm._Busy("429 from x: b'slow down'")
        llm._tally({"prompt_tokens": 10, "completion_tokens": 2})
        return '{"ok": 1}'

    monkeypatch.setattr(llm, "_send", busy_twice)
    monkeypatch.setattr(llm, "_sleep", lambda seconds: None)
    real_chat_json("s", "u", label="thread")

    rows = store.calls(conn, step)
    assert len(tries) == 3
    assert [(r["attempt"], r["status"], r["tokens_in"]) for r in rows] == [(1, "ok", 10)]


def test_a_call_that_never_came_back_is_recorded_as_failed(conn, step, real_chat_json,
                                                           monkeypatch):
    def refused(body, timeout):
        raise llm.LLMError("401 from x: b'no'")

    monkeypatch.setattr(llm, "_send", refused)
    with pytest.raises(llm.LLMError):
        real_chat_json("s", "u", label="thread")

    row, = store.calls(conn, step)
    assert row["status"] == "failed" and "401" in row["error"]
    assert row["tokens_in"] is None, "nothing was reported, so nothing is claimed"


def test_a_call_made_outside_a_step_is_still_recorded(conn, project, real_chat_json, monkeypatch):
    """There is no run to bill it to, which is a fact about the call and not a reason to lose it."""
    llm.new_usage()
    _provider(monkeypatch, {"prompt_tokens": 3, "completion_tokens": 4})
    real_chat_json("s", "u", label="check")

    row, = conn.execute("SELECT * FROM call WHERE label='check'").fetchall()
    assert row["run_id"] is None and row["status"] == "ok"


# ---- a synthesis that resumes -------------------------------------------------------------------

def _synth_stub(monkeypatch, seen: list):
    """A model that answers by label and records what it was shown."""
    def chat(system, user, *, label="", timeout=None):
        seen.append({"label": label, "user": user})
        if label == "thread":
            return {"moments": [], "summary": ""}
        if label in ("verify", "verify_summary"):
            return {"verdicts": []}
        if label == "doc":
            return {"summary": "what the reading found", "questions": "", "people": []}
        raise AssertionError(f"no canned answer for {label!r}")

    monkeypatch.setattr(llm, "chat_json", chat)
    return seen


def test_a_resumed_synthesis_follows_only_the_themes_the_first_attempt_never_reached(
        conn, analysed, monkeypatch):
    """The failure this exists for: a DOC over nine themes dies on the ninth and the rerun asks
    for all nine again — eight lines already written, checked and paid for."""
    pid, mid = analysed["pid"], analysed["grande"]
    written, left = analysed["themes"]["Leaving and arriving"], analysed["themes"]["Work and trade"]

    first = store.start_run(conn, pid, "doc", mid, "Writing what stands out")
    store.save_follow(conn, mid, written, "line", first)     # one wave got through, then the crash
    store.finish_run(conn, first, error="interrupted: the application restarted")

    seen = _synth_stub(monkeypatch, [])
    second = store.start_run(conn, pid, "doc", mid, "Writing what stands out")
    synth.doc(conn, mid, run_id=second, skip_done=first)

    threads = [c["user"] for c in seen if c["label"] == "thread"]
    assert len(threads) == 1, "one line, not two"
    assert left in threads[0] and written not in threads[0]

    # ...and the summary is still written over the WHOLE material, not over today's half of it.
    shown = next(c["user"] for c in seen if c["label"] == "doc")
    assert "## Leaving and arriving" in shown


def test_without_an_interrupted_attempt_every_theme_is_followed_as_before(conn, analysed,
                                                                          monkeypatch):
    seen = _synth_stub(monkeypatch, [])
    rid = store.start_run(conn, analysed["pid"], "doc", analysed["grande"], "again")
    synth.doc(conn, analysed["grande"], run_id=rid)

    assert len([c for c in seen if c["label"] == "thread"]) == 2


def test_a_finished_line_is_recorded_as_the_wave_ends_and_not_only_at_the_end(conn, analysed,
                                                                              monkeypatch):
    """What makes resuming possible at all: the `follow` row for a theme is written when its wave
    lands, so a step that dies half way still says how far it got."""
    monkeypatch.setattr(synth, "WAVE", 1)
    pid, mid = analysed["pid"], analysed["grande"]
    seen: list = []

    def chat(system, user, *, label="", timeout=None):
        seen.append(label)
        if label == "thread" and len(seen) > 1:
            raise llm.LLMError("the model went quiet")
        return {"moments": [], "summary": ""}

    monkeypatch.setattr(llm, "chat_json", chat)
    rid = store.start_run(conn, pid, "doc", mid, "Writing what stands out")
    with pytest.raises(llm.LLMError):
        synth.doc(conn, mid, run_id=rid)

    assert store.followed_in_run(conn, mid, rid) == {analysed["themes"]["Leaving and arriving"]}


def test_a_stop_between_waves_prevents_the_next_waves_calls(conn, analysed, monkeypatch):
    """A model call cannot be taken back once sent, so the only stop worth having is one that is
    asked BEFORE the next one. It used to be asked between planned steps, and a synthesis is one
    step holding a dozen paid calls."""
    monkeypatch.setattr(synth, "WAVE", 1)
    seen, halt = [], []

    def chat(system, user, *, label="", timeout=None):
        seen.append(label)
        halt.append(1)                          # the researcher presses stop during the first wave
        return {"moments": [], "summary": ""}

    monkeypatch.setattr(llm, "chat_json", chat)
    rid = store.start_run(conn, analysed["pid"], "doc", analysed["grande"], "Writing")
    out = synth.doc(conn, analysed["grande"], run_id=rid, stop=lambda: bool(halt))

    assert seen == ["thread"], "no second line, no check, no summary"
    assert out["summary"] == ""


def test_a_line_the_researcher_asked_for_again_ignores_what_an_attempt_already_reached(
        conn, analysed, monkeypatch):
    """`skip_done` is for a step a restart cut in half. A person asking for one line again is not
    that, and the answer to a person is not silence."""
    pid, mid = analysed["pid"], analysed["grande"]
    tid = analysed["themes"]["Work and trade"]
    first = store.start_run(conn, pid, "doc", mid, "Writing what stands out")
    store.save_follow(conn, mid, tid, "line", first)

    seen = _synth_stub(monkeypatch, [])
    synth.doc(conn, mid, only_theme=tid, run_id="r2", skip_done=first)
    assert [c["label"] for c in seen] == ["thread"]


# ---- one lock per project -----------------------------------------------------------------------

def _stub_steps(monkeypatch, fn):
    for kind, (text, _) in list(jobs.STEPS.items()):
        monkeypatch.setitem(jobs.STEPS, kind, (text, fn))


def test_two_projects_chains_do_not_wait_on_each_other(conn, monkeypatch):
    """The barrier is the assertion: it releases only when both projects' steps are inside it at
    the same moment. Under the old process-wide lock it would time out, the step would fail, and
    the job would come back failed rather than finished."""
    a = store.create_project(conn, "One corpus", focus="")
    b = store.create_project(conn, "Another corpus", focus="")
    met = threading.Barrier(2, timeout=5)

    def step(c, project_id, run):
        met.wait()                          # BrokenBarrier if the two chains are serialised

    _stub_steps(monkeypatch, step)

    ja = jobs.start(db.connect, a, [{"kind": "themes"}])
    jb = jobs.start(db.connect, b, [{"kind": "themes"}])
    assert jobs.wait(ja, 10) and jobs.wait(jb, 10)

    assert [store.job(conn, j)["status"] for j in (ja, jb)] == ["finished", "finished"]
    assert [r["error"] for r in store.runs(conn, a) + store.runs(conn, b)] == [None, None]


def test_one_projects_chains_still_take_their_turn(conn, monkeypatch):
    """Its codebook, its themes and its summaries are one shared state; two chains over them
    would be two writers on the same theme rows."""
    pid = store.create_project(conn, "One corpus", focus="")
    lock, live, most = threading.Lock(), [], []

    def step(c, project_id, run):
        with lock:
            live.append(1)
            most.append(len(live))
        time.sleep(0.05)
        with lock:
            live.pop()

    _stub_steps(monkeypatch, step)
    js = [jobs.start(db.connect, pid, [{"kind": "themes"}]) for _ in range(2)]
    assert all(jobs.wait(j, 10) for j in js)
    assert most == [1, 1], "one chain of this project at a time, as it always was"


def test_the_shared_budget_caps_what_is_in_flight_across_every_project():
    """Not the machine — the provider's rate limit, which is one budget however many projects are
    reading at once."""
    assert jobs.CALLS._value == jobs.PARALLEL


# ---- the stable half of a THREAD prompt goes first ----------------------------------------------

def test_the_thread_prompt_leads_with_the_material_and_ends_with_the_theme(conn, analysed):
    mid = analysed["grande"]
    (_, user), *_ = synth._thread_prompt(conn, mid, analysed["themes"]["Work and trade"])

    at = [user.index(h) for h in ("THE MATERIAL.", "HOW THIS MATERIAL IS LAID OUT",
                                  "WHAT THE RESEARCHER IS LOOKING FOR",
                                  "THE THEME you are following",
                                  "WHERE THE READING ALREADY MARKED",
                                  "PASSAGES IN THIS MATERIAL ALREADY CARRYING",
                                  "WHAT THE RESEARCHER SAID")]
    assert user.startswith("THE MATERIAL.") and at == sorted(at)


def test_two_themes_of_one_material_share_that_prefix(conn, analysed):
    """The point of the order: what changes between one material's theme calls is at the end of
    the message, so everything before it is one long identical prefix. Whether a provider serves
    it from a cache is the provider's business — `call.tokens_cached` is where that is read, and
    a NULL there means it never said."""
    import os.path
    mid = analysed["grande"]
    a = synth._thread_prompt(conn, mid, analysed["themes"]["Work and trade"])[0][1]
    b = synth._thread_prompt(conn, mid, analysed["themes"]["Leaving and arriving"])[0][1]

    shared = os.path.commonprefix([a, b])
    assert "WHAT THE RESEARCHER IS LOOKING FOR" in shared, "the whole stable half is shared"
    # The heading is the same in both and rides in the prefix with everything above it; what the
    # prefix stops at is the first character that differs, which is this theme's own id.
    assert analysed["themes"]["Work and trade"] not in shared
    assert len(shared) > 0.8 * min(len(a), len(b)), "and it is most of the message"
