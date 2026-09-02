"""P0: the pieces every later phase stands on. These pass before any agent starts."""
from __future__ import annotations

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
