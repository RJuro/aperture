"""P46 — the spoken brief: written over the record on request, then read aloud by Kokoro.

The text stands whether or not the voice answers, and a recording is never left playing over a
brief it no longer matches.
"""
from __future__ import annotations

import httpx
import pytest

from app import store, tts
from app.engine import brief


def test_the_brief_is_written_over_the_record_and_recorded(conn, analysed, model, monkeypatch):
    pid = analysed["pid"]
    said = {}

    def speak(text, into, title=""):
        said.update(text=text, title=title)
        into.parent.mkdir(parents=True, exist_ok=True)
        into.write_bytes(b"ID3")
    monkeypatch.setattr(tts, "speak", speak)
    model.queue({"brief": "This project reads two interviews."})
    brief.run(conn, pid, feedback="Keep it short.")
    brief.speak(conn, pid)

    assert store.get_summary(conn, "project", pid, "brief")["text"] == \
        "This project reads two interviews."
    assert brief.audio_path(pid).read_bytes() == b"ID3"
    assert said["title"].startswith("Aperture brief: ")
    shown = model.shown("brief")
    assert "Keep it short." in shown and "## Materials" in shown


def test_a_voice_that_fails_leaves_the_text_and_no_old_recording(conn, analysed, model,
                                                                  monkeypatch):
    pid = analysed["pid"]
    old = brief.audio_path(pid)
    old.parent.mkdir(parents=True, exist_ok=True)
    old.write_bytes(b"an older brief")

    def down(*a, **k):
        raise tts.SpeechError("the voice could not be reached")
    monkeypatch.setattr(tts, "speak", down)
    model.queue({"brief": "A new brief."})
    brief.run(conn, pid)
    brief.speak(conn, pid)
    assert store.get_summary(conn, "project", pid, "brief")["text"] == "A new brief."
    assert not old.exists()


def test_the_client_submits_polls_and_fetches(monkeypatch, tmp_path):
    monkeypatch.setenv("TTS_API_KEY", "k")
    monkeypatch.setattr(tts, "_sleep", lambda s: None)
    states = iter(["processing", "completed"])
    sent = {}

    def handler(req: httpx.Request) -> httpx.Response:
        assert req.headers["authorization"] == "Bearer k"
        if req.url.path == "/api/generate":
            sent["body"] = req.content
            return httpx.Response(200, json={"job_id": "j1", "status": "processing"})
        if req.url.path == "/api/status/j1":
            return httpx.Response(200, json={"status": next(states)})
        if req.url.path == "/api/audio/j1":
            return httpx.Response(200, content=b"ID3mp3")
        return httpx.Response(404)

    real = httpx.Client
    monkeypatch.setattr(tts.httpx, "Client",
                        lambda **k: real(transport=httpx.MockTransport(handler), **k))
    out = tts.speak("One — two.", tmp_path / "b.mp3", title="t")
    assert out.read_bytes() == b"ID3mp3"
    assert b"One, two." in sent["body"]


def test_no_key_is_a_sentence(monkeypatch, tmp_path):
    monkeypatch.delenv("TTS_API_KEY", raising=False)
    with pytest.raises(tts.SpeechError, match="TTS_API_KEY"):
        tts.speak("x", tmp_path / "b.mp3")



def test_what_a_voice_would_misread_is_taken_out_and_paragraphs_kept():
    got = tts.spoken("# Heading\nShe said so [LA S012] — see [the notes](https://x.org) "
                     "or www.x.org.\n\n\n\nNext **part**.")
    assert got == "Heading\nShe said so, see the notes or.\n\nNext part."


def test_a_status_request_that_stalls_is_waiting_not_failure(monkeypatch, tmp_path):
    monkeypatch.setenv("TTS_API_KEY", "k")
    monkeypatch.setattr(tts, "_sleep", lambda s: None)
    states = iter(["stall", "completed"])

    def handler(req: httpx.Request) -> httpx.Response:
        if req.url.path == "/api/generate":
            return httpx.Response(200, json={"job_id": "j1"})
        if req.url.path == "/api/status/j1":
            if next(states) == "stall":
                raise httpx.ReadTimeout("busy", request=req)
            return httpx.Response(200, json={"status": "completed"})
        return httpx.Response(200, content=b"ID3")

    real = httpx.Client
    monkeypatch.setattr(tts.httpx, "Client",
                        lambda **k: real(transport=httpx.MockTransport(handler), **k))
    assert tts.speak("x", tmp_path / "b.mp3").read_bytes() == b"ID3"
