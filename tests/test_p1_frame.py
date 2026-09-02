"""P1 — the frame. `app/engine/frame.py` and `app/prompts/frame.md`.

    frame.run(conn, mid, *, hint='') -> {"kind","display","title","speakers","segments",
                                         "orientation","dropped"}

It persists through `store.save_frame` and `store.save_summary(..., 'orientation', ...)`, and it
never writes a sentence.
"""
from __future__ import annotations

import pytest

from app import store

frame = pytest.importorskip("app.engine.frame")


def _answer(**over):
    a = {"kind": "interview", "display": "turns", "title": "Grande, M.",
         "speakers": [{"label": "PHILLIPS", "name": "Phillips", "role": "interviewer"},
                      {"label": "GRANDE", "name": "M. Grande", "role": "participant"}],
         "segments": [], "orientation": "An oral-history interview about a crossing."}
    a.update(over)
    return a


def test_the_model_is_shown_what_the_scan_found_not_asked_to_parse(conn, grande, model):
    model.queue(_answer())
    frame.run(conn, grande)
    shown = model.shown()
    assert "PHILLIPS" in shown and "GRANDE" in shown
    assert "77" in shown or "75" in shown, "the recurrence counts are the evidence, show them"


def test_a_speaker_the_model_invents_is_dropped(conn, grande, model):
    """The anchor law applied to structure: a label must be found in the text to be used."""
    model.queue(_answer(speakers=[{"label": "GRANDE", "name": "M. Grande", "role": "participant"},
                                  {"label": "NARRATOR", "name": "Narrator", "role": "other"}]))
    out = frame.run(conn, grande)
    labels = {s["label"] for s in store.speakers(conn, grande)}
    assert labels == {"GRANDE"}
    assert "NARRATOR" in str(out["dropped"])


def test_with_no_speaker_surviving_the_display_falls_back_to_plain(conn, project, model):
    mid = store.add_material(conn, project, "Notes", "Some field notes.\nNo speakers here at all.")
    from app import ingest
    store.save_sentences(conn, mid, ingest.sentences(store.material(conn, mid)["text"]))
    model.queue(_answer(kind="fieldnotes", display="turns",
                        speakers=[{"label": "OBSERVER", "name": "me", "role": "other"}]))
    out = frame.run(conn, mid)
    assert out["display"] == "plain"
    assert store.material(conn, mid)["display"] == "plain"


def test_with_no_section_surviving_the_display_falls_back_to_plain(conn, grande, model):
    """The symmetric case to the speaker fallback, and for the same reason: a structured display
    with nothing left to structure is one the page cannot render."""
    model.queue(_answer(display="segments",
                        segments=[{"anchor": "words that appear nowhere at all", "label": "Ghost"}]))
    out = frame.run(conn, grande)
    assert out["display"] == "plain"
    assert store.material(conn, grande)["display"] == "plain"
    assert store.segments(conn, grande) == []


def test_a_segment_whose_quote_is_not_there_is_dropped_and_a_real_one_is_bound(conn, grande,
                                                                              model, quote):
    sid, text = quote(grande)
    real = " ".join(text.split()[:8])
    model.queue(_answer(display="segments",
                        segments=[{"anchor": real, "label": "The crossing"},
                                  {"anchor": "words that appear nowhere at all", "label": "Ghost"}]))
    out = frame.run(conn, grande)
    segs = store.segments(conn, grande)
    assert [s["label"] for s in segs] == ["The crossing"]
    assert segs[0]["sid"] == sid
    assert "Ghost" in str(out["dropped"])


def test_an_unknown_kind_or_display_does_not_reach_the_database(conn, grande, model):
    model.queue(_answer(kind="haiku", display="carousel"))
    frame.run(conn, grande)
    row = store.material(conn, grande)
    assert row["kind"] in {"interview", "focus_group", "fieldnotes", "document", "open_text",
                           "other"}
    assert row["display"] in {"turns", "segments", "plain"}


def test_the_orientation_is_stored_as_orientation_not_as_the_reading(conn, grande, model):
    model.queue(_answer(orientation="A 1978 oral history about leaving Italy."))
    frame.run(conn, grande)
    assert store.get_summary(conn, "material", grande, "orientation")["text"].startswith("A 1978")
    assert store.get_summary(conn, "material", grande, "reading") is None


def test_a_reframe_shows_the_hint_and_leaves_every_sentence_alone(conn, grande, model):
    model.queue(_answer(), _answer(kind="fieldnotes", display="plain", speakers=[]))
    frame.run(conn, grande)
    before = store.sentences(conn, grande)
    frame.run(conn, grande, hint="this is not an interview, it is a set of notes")
    assert "not an interview" in model.calls[-1]["user"]
    assert store.sentences(conn, grande) == before
    assert store.material(conn, grande)["kind"] == "fieldnotes"
