"""P13 — reading a material without diarization, and what each theme amounts to here.

Three things, all of them about what a researcher actually reads:

    an interview with no `NAME:` cue is not a monologue      `app/engine/diarize.py`
    a theme's line through one material gets a short account `synth._thread`
    the material page lists the themes it found, with those accounts

The estimate is the delicate one. Nothing in the material says who is speaking, so Python cannot
verify a speaker the way it verifies a quote; what it can do is check every passage the model
points at, drop what is not there, and mark the result as an estimate wherever a reader sees it.
"""
from __future__ import annotations

import pytest

from app import ingest, jobs, store

diarize = pytest.importorskip("app.engine.diarize")
synth = pytest.importorskip("app.engine.synth")


# A real exchange with nothing marking who speaks — the shape `turns.scan` cannot read.
NO_CUES = """Thank you for making the time. Could you tell me where you grew up?
I was born in a village outside the city, on the north bank of the river.
My father worked the land and my mother took in sewing for the neighbours.
And did you think then that you would leave?
Never. Leaving was what other people did, and then one winter it was us.
We sold the mule and we sold the good chairs and we went down to the port.
What do you remember of the crossing itself?
Water, mostly. I remember being told not to look at the water and looking at it.
"""


@pytest.fixture
def client(conn, monkeypatch):
    from fastapi.testclient import TestClient
    from app import main
    monkeypatch.setattr(main, "conn", conn, raising=False)
    from app import pages
    monkeypatch.setattr(pages, "connection", lambda: conn, raising=False)
    return TestClient(main.app)


def _material(conn, pid, name, raw):
    mid = store.add_material(conn, pid, name, raw)
    store.save_sentences(conn, mid, ingest.sentences(raw))
    return mid


def _frame_answer(**over):
    a = {"kind": "interview", "display": "plain", "title": "An interview", "speakers": [],
         "segments": [], "orientation": "An interview with nobody's name on the lines."}
    a.update(over)
    return a


# ---- 1. who is speaking, when the material does not say -----------------------------------------

def test_an_interview_with_no_cues_is_given_estimated_speakers(conn, project, model):
    mid = _material(conn, project, "Untitled interview", NO_CUES)
    sids = [s for s, _ in store.sentences(conn, mid)]
    model.queue(_frame_answer(), {"speakers": [
        {"sid": sids[0], "speaker": "Interviewer"},
        {"sid": sids[1], "speaker": "Participant"},
        {"sid": "S999", "speaker": "Interviewer"}]})
    jobs.run_now(conn, project, [{"kind": "frame", "material_id": mid}])

    row = store.material(conn, mid)
    assert row["display"] == "segments"
    assert row["speakers_estimated"] == 1
    assert [(s["sid"], s["label"]) for s in store.segments(conn, mid)] == [
        (sids[0], "Interviewer"), (sids[1], "Participant")]


def test_a_passage_that_is_not_in_the_material_is_dropped_and_said_so(conn, project, model):
    mid = _material(conn, project, "Untitled interview", NO_CUES)
    sids = [s for s, _ in store.sentences(conn, mid)]
    model.queue(_frame_answer(), {"speakers": [
        {"sid": sids[0], "speaker": "Interviewer"},
        {"sid": "S404", "speaker": "Participant"},
        {"sid": sids[1], "speaker": "Participant"},
        {"sid": sids[0], "speaker": "Interviewer"}]})
    jobs.run_now(conn, project, [{"kind": "frame", "material_id": mid}])

    said = " ".join(store.set_aside(conn, project, mid))
    assert "S404" in said, "a passage that is not there must be reported, not silently skipped"
    assert [s["sid"] for s in store.segments(conn, mid)] == sids[:2], "and order only ever goes on"


def test_the_run_says_what_it_is_doing_and_the_page_marks_the_estimate(conn, project, model,
                                                                      client):
    mid = _material(conn, project, "Untitled interview", NO_CUES)
    sids = [s for s, _ in store.sentences(conn, mid)]
    model.queue(_frame_answer(), {"speakers": [{"sid": sids[0], "speaker": "Participant"}]})
    jobs.run_now(conn, project, [{"kind": "frame", "material_id": mid}])

    lines = [r["line"] for r in store.runs(conn, project)]
    assert any(x.startswith("Working out who is speaking in ") for x in lines)

    sid, text = store.sentences(conn, mid)[1]
    tid = store.save_theme(conn, project, tid=None, name="Leaving", gist="the crossing",
                           code_ids=[])
    store.save_moments(conn, mid, tid, [{"claim": "the village is behind them",
                                         "anchor": " ".join(text.split()[:6]), "sid": sid}])
    html = client.get(f"/p/{project}/m/{mid}").text
    assert "Participant · estimated" in html, "a guess must never be shown as a fact"
    # The model is shown the plain label: the marker is the page's, not the material's.
    assert "[Participant]" in synth.layout(conn, mid) and "estimated" not in synth.layout(conn, mid)


def test_a_transcript_that_says_who_speaks_is_never_estimated(conn, project, grande, model):
    model.queue({"kind": "interview", "display": "turns", "title": "Grande",
                 "speakers": [{"label": "PHILLIPS", "name": "Phillips", "role": "interviewer"},
                              {"label": "GRANDE", "name": "M. Grande", "role": "participant"}],
                 "segments": [], "orientation": "An oral history."})
    jobs.run_now(conn, project, [{"kind": "frame", "material_id": grande}])
    assert [c["label"] for c in model.calls] == ["frame"], "nothing to work out; do not pay for it"
    assert store.material(conn, grande)["speakers_estimated"] == 0


def test_material_that_is_not_speech_is_never_estimated(conn, project, model):
    mid = _material(conn, project, "Notes", "Arrived before six. The stalls were still shut.")
    model.queue(_frame_answer(kind="fieldnotes"))
    jobs.run_now(conn, project, [{"kind": "frame", "material_id": mid}])
    assert [c["label"] for c in model.calls] == ["frame"]
    assert store.material(conn, mid)["display"] == "plain"


def test_a_reframe_works_out_who_is_speaking_again(conn, project, model):
    """A re-frame re-describes the material's form, and who is speaking is part of its form."""
    mid = _material(conn, project, "Untitled interview", NO_CUES)
    sids = [s for s, _ in store.sentences(conn, mid)]
    model.queue(_frame_answer(), {"speakers": [{"sid": sids[0], "speaker": "Interviewer"}]},
                _frame_answer(), {"speakers": [{"sid": sids[1], "speaker": "Participant"}]})
    jobs.run_now(conn, project, [{"kind": "frame", "material_id": mid}])
    fid = store.add_feedback(conn, project, "frame", mid, "note",
                             "the first line is the interviewer, not the participant")
    jobs.run_now(conn, project, [{"kind": "frame", "material_id": mid, "feedback_id": fid}])
    assert [(s["sid"], s["label"]) for s in store.segments(conn, mid)] == [(sids[1], "Participant")]
    assert store.material(conn, mid)["speakers_estimated"] == 1


# ---- 2. a short account of what one theme amounts to here ---------------------------------------

@pytest.fixture
def ready(conn, project, grande, quote):
    store.save_frame(conn, grande, kind="interview", display="turns", title="Grande",
                     speakers=[{"label": "GRANDE", "name": "M. Grande", "role": "participant"}],
                     segments=[])
    store.save_summary(conn, "material", grande, "orientation", "A 1978 oral history.")
    tid = store.save_theme(conn, project, tid=None, name="Work", gist="a living", code_ids=[])
    return {"pid": project, "mid": grande, "tid": tid}


def _moments(quote, mid, n=5, at=40):
    return [{"claim": f"claim {i}", "anchor": " ".join(quote(mid, at=at + i * 9)[1].split()[:8]),
             "sid": quote(mid, at=at + i * 9)[0]} for i in range(n)]


def test_a_line_carries_a_short_account_of_what_it_amounts_to(ready, conn, model, quote):
    said = "The stall fed them and the farm did not. " * 30
    model.queue({"moments": _moments(quote, ready["mid"], 5), "summary": said})
    model.queue({"verdicts": []})
    model.queue({"summary": "what the reading found", "questions": "", "people": []})
    model.queue({"verdicts": []})
    synth.doc(conn, ready["mid"])

    row = store.get_summary(conn, "thread", f'{ready["mid"]}:{ready["tid"]}', "reading")
    assert row is not None, "the account is stored against this material and this theme"
    assert row["text"].startswith("The stall fed them")
    assert len(row["text"].split()) <= synth.THREAD_WORDS, "the cap is Python's as well as the prompt's"
    assert "at most 90 words" in model.shown("thread")


def test_a_line_set_aside_leaves_no_account_behind(ready, conn, model, quote):
    """Three claims is not a line, and an account of a line that was not kept would be a reading
    with nothing under it."""
    model.queue({"moments": _moments(quote, ready["mid"], 3), "summary": "an account of nothing"})
    model.queue({"summary": "what the reading found", "questions": "", "people": []})
    out = synth.doc(conn, ready["mid"])
    assert any("set aside" in d for d in out["dropped"])
    assert store.get_summary(conn, "thread", f'{ready["mid"]}:{ready["tid"]}', "reading") is None


def test_the_account_is_on_the_material_page_and_in_the_record(ready, conn, model, quote, client):
    model.queue({"moments": _moments(quote, ready["mid"], 5),
                 "summary": "The stall, not the land, is what fed this household."})
    model.queue({"verdicts": []})
    model.queue({"summary": "what the reading found", "questions": "", "people": []})
    model.queue({"verdicts": []})
    synth.doc(conn, ready["mid"])

    html = client.get(f'/p/{ready["pid"]}/m/{ready["mid"]}?theme={ready["tid"]}').text
    assert "The stall, not the land, is what fed this household." in html
    md = client.get(f'/p/{ready["pid"]}/export.md').text
    assert "The stall, not the land, is what fed this household." in md


# ---- 3. what the reading found, theme by theme --------------------------------------------------

def test_the_material_page_lists_every_theme_it_found_here(conn, analysed, client):
    """The tab strip says which themes are here; it does not say what any of them found. Under the
    summary, each one gets its name, how much it rests on, and its account."""
    from app import context
    pid, mid = analysed["pid"], analysed["grande"]
    first, second = list(analysed["themes"].values())
    store.save_summary(conn, "thread", f"{mid}:{first}", "reading",
                       "Work is trade here, and the land is somewhere already left.")
    absent = store.save_theme(conn, pid, tid=None, name="Never present here",
                              gist="nothing in this material", code_ids=[])

    cards = {c["id"]: c for c in context.material_page(conn, pid, mid)["cards"]}
    assert set(cards) == {first, second}, "a theme with nothing here is not listed"
    assert cards[first]["summary"]["text"].startswith("Work is trade here")
    assert cards[second]["summary"] is None

    html = client.get(f"/p/{pid}/m/{mid}").text
    assert "Themes in this material" in html
    assert f'?theme={second}"' in html, "each one is a way into its own line"
    assert "Work is trade here, and the land is somewhere already left." in html
    assert "the crossing and after" in html, "with no account yet, the definition stands in"
    assert "3 claims" in html
    assert "Never present here" not in html and absent not in html


def test_the_record_says_how_much_each_theme_rests_on_in_each_material(conn, analysed, client):
    pid, mid = analysed["pid"], analysed["grande"]
    tid = list(analysed["themes"].values())[0]
    store.save_summary(conn, "thread", f"{mid}:{tid}", "reading", "Work is trade here.")
    md = client.get(f"/p/{pid}/export.md").text
    assert "#### Work and trade\n\n3 claims\n" in md
    assert "Work is trade here." in md
