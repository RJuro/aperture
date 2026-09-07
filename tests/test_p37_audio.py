"""P37 — a recording becomes material. `app/audio.py`, `app/engine/asr.py`.

    audio.seconds / prepare / chunking / split      the file, before any model sees it
    asr.run(conn, mid, run_id=…)                    the call, the chunks, the voices
    POST /p/{pid}/material  files=…  audio_note=…  audio_clean=…

Nothing here reaches the transcriber: `httpx.post` is stubbed the way the suite stubs
`llm.chat_json` everywhere else, and the two optional passes go through the ordinary `model`
fixture. The tests that need ffmpeg say so and skip without it.

What this file exists to pin: the transcript is Aperture's own turn format and `turns.scan` reads
it back; a chunk boundary is invisible; and every proposal the two model passes make is disposed
of by Python — an omitted voice, an invented one, a tidy that is really a rewrite.
"""
from __future__ import annotations

import io
import json
import shutil
import wave

import pytest

from app import audio, db, ingest, jobs, rerun, store, turns
from app.engine import asr

HAS_FFMPEG = shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None
needs_ffmpeg = pytest.mark.skipif(not HAS_FFMPEG, reason="ffmpeg is not on this host")

NOTE = ('Two people: the interviewer L. Byrne and R. Okafor, who talks about the move to the '
        'coast and about her mother\'s "packing shed" in Tilbury.')


# ---- helpers -------------------------------------------------------------------------------

def wav(path, seconds=1.0, rate=16000, channels=1):
    """A real WAV of silence. A splitter that only works on a toy fixture does not work."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(channels)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b"\x00\x00" * int(rate * seconds) * channels)
    return path


def recording(conn, pid, name="interview.wav", note=NOTE, clean=False, seconds=1.0):
    """A material that arrived as a recording, exactly as the upload verb leaves one."""
    mid = store.add_material(conn, pid, name, audio.NOT_YET)
    src = wav(db.data_dir() / "tmp" / name, seconds=seconds)
    with src.open("rb") as fh:
        store.save_audio(conn, mid, name, fh, note=note, clean=clean)
    return mid


def answer(*speeches, status=200, usage=None):
    """One transcriber answer. `speeches` are (speaker, text) in order."""
    return {"status": status,
            "body": {"text": " ".join(t for _s, t in speeches),
                     "model": "voxtral-mini-latest", "language": "en",
                     "segments": [{"speaker": s, "start": i, "end": i + 1, "text": t}
                                  for i, (s, t) in enumerate(speeches)],
                     "usage": usage or {"prompt_audio_seconds": 61.0, "prompt_tokens": 900,
                                        "completion_tokens": 120}}}


@pytest.fixture
def transcriber(monkeypatch):
    """`httpx.post`, replaced. `.queue(...)` sets what the next requests answer; `.sent` records
    the form fields, so a test can assert what was actually sent to the API."""
    class Fake:
        def __init__(self):
            self.answers, self.sent = [], []

        def queue(self, *answers):
            self.answers.extend(answers)
            return self

        def __call__(self, url, *, headers=None, files=None, data=None, timeout=None):
            self.sent.append({"url": url, "headers": headers or {}, "data": data or {},
                              "file": files["file"][0]})
            if not self.answers:
                raise AssertionError("unexpected transcription request")
            got = self.answers.pop(0)

            class Reply:
                status_code = got["status"]
                text = json.dumps(got["body"])

                def json(self):
                    return got["body"]

            return Reply()

    fake = Fake()
    monkeypatch.setattr(asr.httpx, "post", fake)
    monkeypatch.setenv("MISTRAL_API_KEY", "test-key-not-used")
    return fake


# ---- the file ------------------------------------------------------------------------------

def test_a_wav_says_how_long_it_is_without_ffmpeg(tmp_path, monkeypatch):
    """The one path a laptop without ffmpeg still has. `shutil.which` is emptied so a stray
    subprocess would fail loudly rather than pass this by accident."""
    monkeypatch.setattr(audio.shutil, "which", lambda name: None)
    assert audio.seconds(wav(tmp_path / "a.wav", seconds=3.0)) == pytest.approx(3.0)


def test_a_file_already_mono_16k_and_small_is_left_alone(tmp_path, monkeypatch):
    monkeypatch.setattr(audio.shutil, "which", lambda name: None)
    path = wav(tmp_path / "a.wav")
    assert audio.prepare(path, tmp_path / "work") == path
    assert not (tmp_path / "work").exists(), "nothing was written, so nothing was converted"


def test_without_ffmpeg_a_conversion_says_what_is_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(audio.shutil, "which", lambda name: None)
    stereo = wav(tmp_path / "b.wav", rate=44100, channels=2)
    with pytest.raises(audio.AudioError) as e:
        audio.prepare(stereo, tmp_path / "work")
    assert "ffmpeg" in str(e.value) and "install" in str(e.value)
    assert "\n" not in str(e.value), "one sentence, not a traceback"


def test_a_long_recording_is_chunked_by_duration(tmp_path, monkeypatch):
    monkeypatch.setattr(audio.shutil, "which", lambda name: None)
    monkeypatch.setattr(audio, "MAX_SECONDS", 2)
    path = wav(tmp_path / "a.wav", seconds=5.0)
    per = audio.chunking(path)
    assert per is not None and per == pytest.approx(5 / 3), "three even pieces, not 2+2+1"
    monkeypatch.setattr(audio, "MAX_SECONDS", 60)
    assert audio.chunking(path) is None


def test_a_big_recording_is_chunked_by_size(tmp_path, monkeypatch):
    """Even a short file goes in pieces when it is too large to send whole."""
    monkeypatch.setattr(audio.shutil, "which", lambda name: None)
    path = wav(tmp_path / "a.wav", seconds=4.0)
    monkeypatch.setattr(audio, "MAX_BYTES", path.stat().st_size // 2 + 1)
    assert audio.chunking(path) == pytest.approx(2.0)


@needs_ffmpeg
def test_the_chunks_carry_where_they_start_in_the_recording(tmp_path):
    pieces = audio.split(wav(tmp_path / "a.wav", seconds=6.0), 2.0, tmp_path / "work")
    assert [round(base, 3) for _p, base in pieces] == [0.0, 2.0, 4.0]
    assert all(p.exists() and p.stat().st_size for p, _b in pieces)
    assert all(audio.seconds(p) <= 2.1 for p, _b in pieces)


@needs_ffmpeg
def test_a_stereo_recording_becomes_mono_16k_and_much_smaller(tmp_path):
    """The conversion the whole audio path rests on: an hour of this would be 600 MB and is not."""
    stereo = wav(tmp_path / "big.wav", seconds=5.0, rate=48000, channels=2)
    out = audio.prepare(stereo, tmp_path / "work")
    assert out != stereo and out.suffix == ".flac"
    assert out.stat().st_size < stereo.stat().st_size / 5
    assert audio.seconds(out) == pytest.approx(5.0, abs=0.2)
    assert audio.prepare(out, tmp_path / "again") == out, "what this module made, it does not redo"


# ---- the terms the transcriber is told to expect ---------------------------------------------

def test_the_note_becomes_context_bias_without_a_model(model):
    """The names in the researcher's note are what the transcriber is told to expect, found by a
    regular expression rather than a call.

    Every term is one word. The API takes these as repeated form fields and reads them as a
    comma-separated list, so it refuses a term with a space in it — `Context bias item
    'Paul Sigrist' must not contain commas or whitespace`, a 400 that fails the whole recording.
    A name therefore goes in as its parts, which is where the mis-hearing was anyway.
    """
    note = ('Two people, R. Okafor and the interviewer L. Byrne, about the move to the coast. '
            'She calls it the "packing shed".')
    bias = asr.context_bias(note)
    assert "Okafor" in bias and "Byrne" in bias and "packing" in bias and "shed" in bias
    assert not [t for t in bias if " " in t or "," in t], bias
    assert not model.calls, "capital letters are not worth a model call"
    assert len(asr.context_bias(" ".join(f"Name{i}" for i in range(200)))) <= asr.BIAS_MAX

def test_context_bias_stops_at_the_api_ceiling():
    note = ", ".join(f"Name{i}" for i in range(300))
    assert len(asr.context_bias(note)) == asr.BIAS_MAX == 100


# ---- the transcript ---------------------------------------------------------------------------

def test_the_transcript_is_read_back_as_turns(conn, project, transcriber):
    mid = recording(conn, project)
    transcriber.queue(answer(("speaker_0", "Tell me about the coast."),
                             ("speaker_1", "We went down in the spring."),
                             ("speaker_1", "My mother stayed."),
                             ("speaker_0", "And after that?")))
    out = asr.run(conn, mid)
    text = store.material(conn, mid)["text"]
    assert turns.scan(text) == {"SPEAKER A": 2, "SPEAKER B": 1}
    assert "We went down in the spring. My mother stayed." in text, "one voice, one turn"
    assert out["seconds"] == 61.0 and store.material(conn, mid)["audio_seconds"] == 61.0


def test_the_form_fields_are_the_documented_ones(conn, project, transcriber):
    mid = recording(conn, project)
    transcriber.queue(answer(("speaker_0", "Tell me about the coast.")))
    asr.run(conn, mid)
    sent = transcriber.sent[0]
    assert sent["url"].endswith("/audio/transcriptions")
    assert sent["headers"]["Authorization"].startswith("Bearer ")
    assert sent["data"]["model"] == "voxtral-mini-latest"
    assert sent["data"]["diarize"] == "true"
    assert sent["data"]["timestamp_granularities"] == ["segment"]
    # One word per term, never a phrase: the API refuses a bias item containing a space.
    assert "Okafor" in sent["data"]["context_bias"]
    assert not [t for t in sent["data"]["context_bias"] if " " in t]
    assert "language" not in sent["data"], "the model detects it; the host's locale must not"


def test_a_chunk_boundary_is_invisible(conn, project, transcriber, monkeypatch, model):
    """Two chunks, differently numbered voices, one person. The seam must not become a turn."""
    mid = recording(conn, project, clean=True)
    path = store.audio_path(conn, mid)
    monkeypatch.setattr(audio, "chunking", lambda p: 12.0)
    monkeypatch.setattr(audio, "split", lambda p, per, into=None: [(path, 0.0), (path, 12.0)])
    transcriber.queue(answer(("speaker_0", "We went down in the spring.")),
                      answer(("speaker_7", "And we never went back.")))
    model.queue({"voices": [{"speaker": "SPEAKER A", "role": "participant", "name": "R. Okafor"}]},
                {"voices": [{"speaker": "SPEAKER A", "role": "participant", "name": "R. Okafor"}]},
                {"lines": []}, {"lines": []})
    monkeypatch.setattr(asr.llm, "chat_json", model)
    out = asr.run(conn, mid)
    text = store.material(conn, mid)["text"]
    assert text.count("R. OKAFOR:") == 1, "the seam is not a turn"
    assert "We went down in the spring. And we never went back." in text
    assert [s["chunk"] for s in out["segments"]] == [0, 1]
    assert [s["start"] for s in out["segments"]] == [0.0, 12.0], "offset by the chunk's base"
    assert len(transcriber.sent) == 2


# ---- the optional pass ------------------------------------------------------------------------

def test_without_the_pass_no_model_is_asked_anything(conn, project, transcriber, model,
                                                     monkeypatch):
    mid = recording(conn, project, clean=False)
    monkeypatch.setattr(asr.llm, "chat_json", model)
    transcriber.queue(answer(("speaker_0", "Tell me about the coast."),
                             ("speaker_1", "We went down in the spring.")))
    asr.run(conn, mid)
    assert model.calls == []
    assert "SPEAKER A:" in store.material(conn, mid)["text"]


def test_the_pass_names_the_voices_and_python_disposes(conn, project, transcriber, model,
                                                       monkeypatch):
    """An omitted voice is `other` with no name, an invented one is dropped, a made-up role is
    `other`. The model proposes; nothing it says reaches the transcript unchecked."""
    mid = recording(conn, project, clean=True)
    monkeypatch.setattr(asr.llm, "chat_json", model)
    # Three turns each for the two who carry the interview: `turns.MIN_TURNS` is what separates a
    # speaker from a header label, and a label that recurs twice is not yet a speaker.
    transcriber.queue(answer(("speaker_0", "Tell me about the coast."),
                             ("speaker_1", "We went down in the spring."),
                             ("speaker_0", "And after?"),
                             ("speaker_1", "We stayed a year."),
                             ("speaker_0", "Who was with you?"),
                             ("speaker_1", "My mother, at first."),
                             ("speaker_2", "Mum, the door.")))
    model.queue({"voices": [
        {"speaker": "SPEAKER A", "role": "interviewer", "name": "L. Byrne"},
        {"speaker": "SPEAKER B", "role": "narrator", "name": "R. Okafor"},
        {"speaker": "SPEAKER Z", "role": "participant", "name": "Nobody At All"},
    ]}, {"lines": []})
    out = asr.run(conn, mid)
    text = store.material(conn, mid)["text"]
    assert "L. BYRNE:" in text
    assert "R. OKAFOR:" in text, "a made-up role loses the role, not the name"
    assert "Nobody At All" not in text and "NOBODY AT ALL" not in text
    assert "OTHER:" in text, "the voice the model left out is another voice"
    roles = {s["label"]: s["role"] for s in store.speakers(conn, mid)}
    assert roles["R. OKAFOR"] == "other" and roles["L. BYRNE"] == "interviewer"
    said = " ".join(out["dropped"])
    assert "SPEAKER Z" in said and "SPEAKER C" in said and "narrator" in said


def test_a_tidy_inside_the_gate_is_taken_and_one_past_it_is_not(conn, project, transcriber,
                                                                model, monkeypatch):
    mid = recording(conn, project, clean=True)
    monkeypatch.setattr(asr.llm, "chat_json", model)
    rough = "we came through the docks at tilbury in 1921 my father worked there"
    rewrite = "The family disembarked at the port and my father found employment nearby that year"
    transcriber.queue(answer(("speaker_0", rough), ("speaker_1", rewrite.lower())))
    model.queue({"voices": []}, {"lines": [
        {"n": 0, "text": "We came through the docks at Tilbury in 1921. My father worked there.",
         "why": "sentence boundaries"},
        {"n": 1, "text": "He got a job at the packing shed and never spoke about the crossing.",
         "why": "rewritten"},
    ]})
    out = asr.run(conn, mid)
    text = store.material(conn, mid)["text"]
    assert "We came through the docks at Tilbury in 1921. My father worked there." in text
    assert rewrite.lower() in text, "the line past the gate is put back exactly as it was heard"
    assert "1 line(s) accepted" in " ".join(out["dropped"])
    assert "1 rejected" in " ".join(out["dropped"])


def test_the_gate_is_about_words_not_punctuation():
    assert asr.within_gate("we had a stall in the market", "We had a stall in the market.")
    assert asr.within_gate("we came through tilbury", "We came through Tilbury.")
    assert not asr.within_gate("we had a stall in the market",
                               "We ran a shop in the town square, mostly.")
    assert not asr.within_gate("we had a stall in the market",
                               "We had a stall in the market and my mother sold there too.")


# ---- what is stored ----------------------------------------------------------------------------

def test_the_speakers_came_from_the_recording_and_are_not_estimated(conn, project, transcriber,
                                                                    model, monkeypatch):
    mid = recording(conn, project, clean=True)
    monkeypatch.setattr(asr.llm, "chat_json", model)
    transcriber.queue(answer(("speaker_0", "Tell me about the coast."),
                             ("speaker_1", "We went down in the spring."),
                             ("speaker_0", "And after?"),
                             ("speaker_1", "We stayed a year."),
                             ("speaker_0", "Who was with you?"),
                             ("speaker_1", "My mother, at first.")))
    model.queue({"voices": [{"speaker": "SPEAKER A", "role": "interviewer", "name": "L. Byrne"},
                            {"speaker": "SPEAKER B", "role": "participant", "name": "R. Okafor"}]},
                {"lines": []})
    asr.run(conn, mid)
    rows = store.segments(conn, mid)
    assert [r["label"] for r in rows] == ["L. BYRNE", "R. OKAFOR"] * 3
    assert all(r["sid"] for r in rows)
    assert store.material(conn, mid)["speakers_estimated"] == 0, \
        "'estimated' is for the guessing path, and these voices were heard"


def test_the_text_and_its_sentences_appear_only_after_the_step(conn, project, transcriber):
    mid = recording(conn, project)
    assert store.material(conn, mid)["text"] == audio.NOT_YET
    assert store.sentences(conn, mid) == [], "no id is cut before there is anything to cite"
    transcriber.queue(answer(("speaker_0", "Tell me about the coast."),
                             ("speaker_1", "We went down in the spring.")))
    asr.run(conn, mid)
    rows = store.sentences(conn, mid)
    assert rows and store.material(conn, mid)["text"] != audio.NOT_YET
    assert [sid for sid, _t in rows] == [r["sid"] for r in ingest.sentences(
        store.material(conn, mid)["text"])]


def test_a_failed_transcription_leaves_the_placeholder_and_says_why(conn, project, transcriber):
    mid = recording(conn, project)
    transcriber.queue({"status": 413, "body": {"message": "file too large"}})
    with pytest.raises(asr.ASRError) as e:
        asr.run(conn, mid)
    assert "413" in str(e.value)
    assert store.material(conn, mid)["text"] == audio.NOT_YET
    assert store.sentences(conn, mid) == []
    assert store.audio_path(conn, mid).exists(), "the recording stays; they can run it again"


def test_no_key_is_one_sentence_naming_the_variable(conn, project, transcriber, monkeypatch):
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
    mid = recording(conn, project)
    with pytest.raises(asr.ASRError) as e:
        asr.run(conn, mid)
    assert "MISTRAL_API_KEY" in str(e.value) and "APERTURE_PROVIDER" in str(e.value)


def test_the_transcription_lands_on_the_run_row(conn, project, transcriber):
    """A paid call inside a step is part of what the reading cost, whatever endpoint it went to."""
    from app import llm
    mid = recording(conn, project)
    rid = store.start_run(conn, project, "transcribe", mid, "Transcribing interview.wav")
    llm.new_usage(rid)
    transcriber.queue(answer(("speaker_0", "Tell me about the coast.")))
    asr.run(conn, mid, run_id=rid)
    assert llm.usage["tokens_in"] == 900 and llm.usage["tokens_out"] == 120
    call = store.calls(conn, rid)[0]
    assert call["label"] == "asr" and call["provider"] == "mistral"
    assert call["model"] == "voxtral-mini-latest" and call["status"] == "ok"


# ---- the chain -----------------------------------------------------------------------------------

def test_an_uploaded_recording_is_transcribed_first(conn, project, monkeypatch):
    """One submission may mix a recording and a document; only the recording is transcribed."""
    from fastapi.testclient import TestClient

    from app import main, pages, verbs
    monkeypatch.setattr(pages, "connection", lambda: conn)
    monkeypatch.setattr(verbs, "connection", lambda: conn)
    planned = []
    monkeypatch.setattr(jobs, "start", lambda factory, pid, runs: planned.append(list(runs)) or "j")
    client = TestClient(main.app, follow_redirects=False)

    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(16000)
        w.writeframes(b"\x00\x00" * 16000)
    r = client.post(f"/p/{project}/material",
                    files=[("files", ("chat.m4a", buf.getvalue(), "audio/mp4")),
                           ("files", ("notes.txt", b"PHILLIPS: Tell me.\n\nGRANDE: I will.",
                                      "text/plain"))],
                    data={"audio_note": NOTE, "audio_clean": "on"})
    assert r.status_code == 303
    rows = store.materials(conn, project)
    recorded = [m for m in rows if m["audio_file"]]
    assert len(recorded) == 1 and recorded[0]["name"] == "chat.m4a"
    assert recorded[0]["text"] == audio.NOT_YET
    assert recorded[0]["audio_note"] == NOTE and recorded[0]["audio_clean"] == 1
    assert (db.data_dir() / recorded[0]["audio_file"]).exists()

    mine = [x["kind"] for x in planned[-1] if x.get("material_id") == recorded[0]["id"]]
    assert mine[0] == "transcribe" and mine[1] == "frame"
    other = [m for m in rows if not m["audio_file"]][0]
    assert "transcribe" not in [x["kind"] for x in planned[-1]
                                if x.get("material_id") == other["id"]]


def test_only_a_recording_can_be_run_again_from_one(conn, project):
    assert rerun.chain_for(True)[0] == "transcribe"
    assert "transcribe" not in rerun.chain_for(False)
    assert [r["kind"] for r in rerun.from_step("m1", "transcribe", recorded=True)][:2] == \
        ["transcribe", "frame"]
    with pytest.raises(KeyError):
        rerun.from_step("m1", "transcribe")


def test_removing_the_material_deletes_the_recording(conn, project):
    mid = recording(conn, project)
    path = store.audio_path(conn, mid)
    assert path.exists()
    assert store.remove_material(conn, project, mid)
    assert not path.exists(), "a gigabyte per interview is not ours to keep after it is gone"
