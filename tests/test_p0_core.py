"""P0: the pieces every later phase stands on. These pass before any agent starts."""
from __future__ import annotations

import json

import pytest

from app import anchor, db, ingest, llm, store, turns


def test_a_recurring_label_is_a_speaker_and_a_header_line_is_not(grande, conn):
    raw = store.material(conn, grande)["text"]
    assert turns.speakers(raw) == ["PHILLIPS", "GRANDE"]
    assert turns.occurrences(raw, "BIRTH DATE") == 1      # present, but not a speaker
    assert turns.occurrences(raw, "NOBODY") == 0


def test_sentence_ids_are_dense_ordered_and_carry_their_speaker(grande, conn):
    rows = store.sentence_rows(conn, grande)
    assert [r["sid"] for r in rows] == [f"S{i:03d}" for i in range(len(rows))]
    assert any(r["speaker"] == "GRANDE" for r in rows)
    assert max(r["turn_idx"] for r in rows) > 50


def test_a_reframe_never_moves_a_sentence_id(grande, conn):
    """The whole reason re-framing is safe: codes and moments cite sids, and framing never
    re-ingests. If this breaks, a re-frame silently invalidates every citation in the project."""
    before = store.sentences(conn, grande)
    store.save_frame(conn, grande, kind="interview", display="turns", title="t",
                     speakers=[{"label": "GRANDE", "name": "M. Grande", "role": "participant"}],
                     segments=[])
    store.save_frame(conn, grande, kind="fieldnotes", display="plain", title="t2",
                     speakers=[], segments=[])
    assert store.sentences(conn, grande) == before


def test_a_rerun_supersedes_and_the_old_moment_is_still_there(conn, project, grande, quote):
    tid = store.save_theme(conn, project, tid=None, name="Work", gist="", code_ids=[])
    sid, text = quote(grande)
    store.save_moments(conn, grande, tid, [{"claim": "first", "anchor": text[:40], "sid": sid}])
    store.save_moments(conn, grande, tid, [{"claim": "second", "anchor": text[:40], "sid": sid}])
    assert [m["claim"] for m in store.thread(conn, grande, tid)] == ["second"]
    kept = conn.execute("SELECT claim FROM moment WHERE status='superseded'").fetchall()
    assert [r["claim"] for r in kept] == ["first"]


def test_uncited_is_the_one_derivation_behind_both_the_check_and_the_page(conn, project, grande,
                                                                         quote):
    tid = store.save_theme(conn, project, tid=None, name="T", gist="", code_ids=[])
    sid, text = quote(grande)
    store.save_moments(conn, grande, tid, [{"claim": "c", "anchor": text[:30], "sid": sid}])
    total = len(store.sentences(conn, grande))
    assert len(store.uncited(conn, grande)) == total - 1
    assert sid not in {s for s, _ in store.uncited(conn, grande)}


def test_the_orientation_survives_the_reading_summary(conn, grande):
    store.save_summary(conn, "material", grande, "orientation", "what this is")
    store.save_summary(conn, "material", grande, "reading", "what the reading found")
    assert store.get_summary(conn, "material", grande)["stage"] == "reading"
    assert store.get_summary(conn, "material", grande, "orientation")["text"] == "what this is"


def test_the_provider_is_chosen_by_env_and_never_guessed(monkeypatch):
    monkeypatch.setenv("APERTURE_PROVIDER", "mistral")
    assert (llm.provider(), llm.model()) == ("mistral", "glm-5-2")
    monkeypatch.setenv("APERTURE_PROVIDER", "minimax")
    assert (llm.provider(), llm.model()) == ("minimax", "MiniMax-M3")
    monkeypatch.setenv("APERTURE_PROVIDER", "openai")
    with pytest.raises(llm.LLMError):
        llm.provider()


def test_a_missing_key_is_an_error_not_a_silent_fallback(monkeypatch):
    monkeypatch.setenv("APERTURE_PROVIDER", "mistral")
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
    with pytest.raises(llm.LLMError, match="MISTRAL_API_KEY"):
        llm._endpoint()


def test_thinking_and_fences_are_stripped_before_json(monkeypatch):
    assert llm.parse("<think>weighing it up</think>\n```json\n{\"a\": [1]}\n```") == {"a": [1]}
    assert llm.parse('prelude {"b": 2} coda') == {"b": 2}


def test_replay_serves_a_recording_and_a_miss_is_loud(tmp_path, monkeypatch, real_chat_json):
    monkeypatch.setenv("APERTURE_REPLAY", str(tmp_path))
    key = llm._key("read", "sys", "usr")
    (tmp_path / f"{key}.json").write_text('{"codes": []}')
    assert real_chat_json("sys", "usr", label="read") == {"codes": []}
    with pytest.raises(llm.LLMError, match="no recording"):
        real_chat_json("sys", "different", label="read")


def test_a_prompt_slot_the_code_forgets_is_an_error(tmp_path, monkeypatch):
    d = tmp_path / "prompts"
    d.mkdir()
    (d / "t.md").write_text("System {{a}}\n---\nUser {{b}}")
    monkeypatch.setattr(llm, "__file__", str(tmp_path / "llm.py"))
    with pytest.raises(llm.LLMError, match="unfilled"):
        llm.prompt("t", a="x")
    with pytest.raises(llm.LLMError, match="no slot"):
        llm.prompt("t", a="x", b="y", c="z")
    assert llm.prompt("t", a="x", b="y") == ("System x", "User y")


def test_researcher_words_containing_braces_do_not_read_as_slots(tmp_path, monkeypatch):
    """The researcher's own words go into prompts verbatim, by law. A focus or a piece of
    feedback that happens to contain {{something}} must survive intact — not raise, and not be
    filled from a neighbouring slot."""
    d = tmp_path / "prompts"
    d.mkdir()
    (d / "t.md").write_text("Sys {{focus}}\n---\nUser {{material}}")
    monkeypatch.setattr(llm, "__file__", str(tmp_path / "llm.py"))
    system, user = llm.prompt("t", focus="watch for {{material}} please", material="the text")
    assert system == "Sys watch for {{material}} please"
    assert user == "User the text"


def test_a_real_environment_variable_beats_the_env_file(tmp_path, monkeypatch):
    """Production sets its configuration in Coolify. A .env that shipped in the image must never
    override it, or a deploy silently talks to the wrong endpoint with the wrong key."""
    import app as pkg
    f = tmp_path / ".env"
    f.write_text("APERTURE_PROVIDER=mistral\nMINIMAX_MODEL=from-the-file\n")
    monkeypatch.setenv("APERTURE_PROVIDER", "minimax")
    monkeypatch.delenv("MINIMAX_MODEL", raising=False)
    pkg.load_env(f)
    assert llm.provider() == "minimax"          # the environment wins
    assert llm.model() == "from-the-file"       # the file fills what the environment left unset


def test_a_missing_env_file_is_not_an_error(tmp_path):
    import app as pkg
    pkg.load_env(tmp_path / "nothing-here")


def test_a_reasoning_models_thinking_never_reaches_the_json():
    """A model that reasons returns content as typed blocks — a `thinking` block and a `text`
    block. Only the text is the answer. Joining them blindly splices the model's private
    deliberation into the JSON it is trying to emit, and the parse fails or, worse, doesn't."""
    blocks = [{"type": "thinking", "thinking": "Let me consider {\"codes\": [\"wrong\"]} first."},
              {"type": "text", "text": '{"codes": ['},
              {"type": "text", "text": '"right"]}'}]
    assert llm._content(blocks) == '{"codes": ["right"]}'
    assert llm._content("plain string") == "plain string"
    assert llm._content(None) == ""


def test_reasoning_effort_is_per_provider_and_can_be_turned_off(monkeypatch):
    monkeypatch.delenv("APERTURE_REASONING", raising=False)
    monkeypatch.setenv("APERTURE_PROVIDER", "mistral")
    assert llm.reasoning() == "high", "GLM reasons only when asked; off is a thinner reading"
    monkeypatch.setenv("APERTURE_PROVIDER", "minimax")
    assert llm.reasoning() == "", "M3 reasons by default and takes no instruction"
    monkeypatch.setenv("APERTURE_PROVIDER", "mistral")
    monkeypatch.setenv("APERTURE_REASONING", "off")
    assert llm.reasoning() == ""
    monkeypatch.setenv("APERTURE_REASONING", "low")
    assert llm.reasoning() == "low"


def test_a_call_that_only_describes_a_layout_is_not_asked_to_think(monkeypatch, real_chat_json):
    """Working out a layout is not judgement, and thinking about it is minutes and money spent
    copying labels a Python scan already found."""
    sent = []
    monkeypatch.setattr(llm, "_send", lambda body, timeout: sent.append(body) or '{"ok": 1}')
    monkeypatch.setenv("APERTURE_PROVIDER", "mistral")
    monkeypatch.setenv("MISTRAL_API_KEY", "k")

    real_chat_json("s", "u", label="frame")
    real_chat_json("s", "u", label="read")
    real_chat_json("s", "u", label="thread")
    real_chat_json("s", "u", label="account")
    assert "reasoning_effort" not in sent[0]
    assert sent[1]["reasoning_effort"] == "high", "a call that judges keeps the provider's default"
    assert sent[2]["reasoning_effort"] == "medium", \
        "one line per theme, measured as the dominant cost of the chain"
    assert sent[3]["reasoning_effort"] == "medium", \
        "one call per theme at the end of every chain, over claims already checked"

    monkeypatch.setenv("APERTURE_REASONING", "medium")
    real_chat_json("s", "u", label="frame")
    assert sent[4]["reasoning_effort"] == "medium", "the override turns the whole run up at once"


def test_a_busy_provider_is_waited_out_and_says_so_while_it_waits(monkeypatch, real_chat_json):
    """429 in the middle of the afternoon is not a failed reading. The waits are reported because
    a chain that goes quiet for four minutes is indistinguishable from a hung one."""
    waits, said, tries = [], [], []
    monkeypatch.setattr(llm, "_sleep", waits.append)
    monkeypatch.setattr(llm, "report", said.append)

    def busy_twice(body, timeout):
        tries.append(1)
        if len(tries) < 3:
            raise llm._Busy("429 from x: b'slow down'")
        return '{"ok": 1}'

    monkeypatch.setattr(llm, "_send", busy_twice)
    assert real_chat_json("s", "u", label="read") == {"ok": 1}
    assert waits == [15, 30]
    assert said == ["The model is busy; trying again in 15 s (attempt 1 of 5)",
                    "The model is busy; trying again in 30 s (attempt 2 of 5)"]


def test_a_provider_that_stays_busy_waits_five_times_and_then_the_error_stands(monkeypatch,
                                                                              real_chat_json):
    waits = []
    monkeypatch.setattr(llm, "_sleep", waits.append)

    def always(body, timeout):
        raise llm._Busy("503 from x: b'busy'", after="7")     # honoured over the schedule

    monkeypatch.setattr(llm, "_send", always)
    with pytest.raises(llm.LLMError, match="503"):
        real_chat_json("s", "u", label="read")
    assert waits == [7, 7, 7, 7, 7]


def test_a_loaded_provider_is_told_apart_from_one_that_is_refusing(monkeypatch):
    class Resp:
        status_code, headers = 429, {"retry-after": "7"}

        def read(self):
            return b"the model is busy"

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    class Client:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def stream(self, *a, **k):
            return Resp()

    monkeypatch.setattr(llm.httpx, "Client", Client)
    raised = {}
    for status in (429, 503, 401):
        Resp.status_code = status
        with pytest.raises(llm.LLMError) as e:
            llm._send({"model": "m"}, None)
        raised[status] = e.value
    assert isinstance(raised[429], llm._Busy) and raised[429].after == "7"
    assert isinstance(raised[503], llm._Busy)
    assert not isinstance(raised[401], llm._Busy), "a refusal is not something to wait out"


def _mock_httpx(monkeypatch, answer):
    """Every client `_send` opens, answered by `answer` over httpx's own MockTransport — no
    socket is opened, and the clients and responses are kept so a test can ask whether they were
    closed."""
    import contextlib
    real = llm.httpx.Client
    clients, responses = [], []

    class Client(real):
        def __init__(self, **kw):
            super().__init__(transport=llm.httpx.MockTransport(answer), **kw)
            clients.append(self)

        @contextlib.contextmanager
        def stream(self, *a, **k):
            with real.stream(self, *a, **k) as r:
                responses.append(r)
                yield r

    monkeypatch.setattr(llm.httpx, "Client", Client)
    return clients, responses


def test_nothing_is_left_open_by_a_call_that_ends_early_or_badly(monkeypatch):
    """A run of about sixty calls was seen holding sixty-one established sockets. `_send` opens a
    client per call inside a `with` and streams inside a nested one, so all three ways out have to
    leave both closed: the stream that ends, the stream this BREAKS out of at `[DONE]` with bytes
    still unread, and a 429 whose body is read and then raised over."""
    tail = b'data: {"choices":[{"delta":{"content":"NEVER READ"}}]}\n\n'

    def answer(request):
        body = json.loads(request.content)
        if body["model"] == "busy":
            return llm.httpx.Response(429, content=b"slow down", headers={"retry-after": "7"})
        sse = [b'data: {"choices":[{"delta":{"content":"{\\"ok\\": 1}"}}],'
               b'"usage":{"prompt_tokens":3,"completion_tokens":4}}\n\n']
        if body["model"] == "done":
            sse += [b"data: [DONE]\n\n", tail]
        return llm.httpx.Response(200, content=iter(sse),
                                  headers={"content-type": "text/event-stream"})

    clients, responses = _mock_httpx(monkeypatch, answer)
    llm.new_usage()
    assert llm._send({"model": "plain"}, None) == '{"ok": 1}', "a stream that simply ends"
    assert llm._send({"model": "done"}, None) == '{"ok": 1}', "and one broken out of at [DONE]"
    with pytest.raises(llm._Busy):
        llm._send({"model": "busy"}, None)

    assert len(clients) == len(responses) == 3
    assert [c.is_closed for c in clients] == [True] * 3, "a client was left open"
    assert [r.is_closed for r in responses] == [True] * 3, "a response was left unread and open"
    assert dict(llm.usage) == {"tokens_in": 6, "tokens_out": 8}, "and both calls were counted"


def test_switching_provider_cannot_inherit_the_other_ones_endpoint(monkeypatch):
    """A single global base-url override was a loaded gun: set it for one provider in .env,
    switch provider, and the new provider's key is sent to the old provider's endpoint. It cost
    a whole pipeline run — provider mistral, model MiniMax-M3, a 401 from minimaxi.com."""
    monkeypatch.setenv("MINIMAX_BASE_URL", "https://minimax.example/v1")
    monkeypatch.setenv("MINIMAX_MODEL", "pinned-to-minimax")
    monkeypatch.setenv("MISTRAL_API_KEY", "k")
    monkeypatch.setenv("APERTURE_PROVIDER", "mistral")
    base, _ = llm._endpoint()
    assert base == "https://api.mistral.ai/v1"
    assert llm.model() == "glm-5-2"
    monkeypatch.setenv("APERTURE_PROVIDER", "minimax")
    assert llm._endpoint()[0] == "https://minimax.example/v1"
    assert llm.model() == "pinned-to-minimax"
