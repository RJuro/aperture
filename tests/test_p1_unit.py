"""P1 unit checks — the caps and coercions the contract tests do not reach."""
from __future__ import annotations

import pytest

from app import store

frame = pytest.importorskip("app.engine.frame")


def _answer(**over):
    a = {"kind": "interview", "display": "turns", "title": "Grande, M.",
         "speakers": [{"label": "GRANDE", "name": "M. Grande", "role": "participant"}],
         "segments": [], "orientation": "An oral-history interview about a crossing."}
    a.update(over)
    return a


def test_the_scan_shows_header_labels_too_so_the_model_can_see_why_one_is_a_speaker(conn, grande,
                                                                                    model):
    model.queue(_answer())
    frame.run(conn, grande)
    shown = model.shown()
    assert "BIRTH DATE: 1 line" in shown, "a label that appears once is evidence, not noise"
    assert "PHILLIPS: 77 lines" in shown


def test_a_long_title_and_orientation_are_trimmed_not_rejected(conn, grande, model):
    """With nobody named, the model's title is what the composed one is built on, and the cap
    still applies to it."""
    model.queue(_answer(speakers=[], title=" ".join(f"w{i}" for i in range(30)),
                        orientation=" ".join(f"o{i}" for i in range(400))))
    out = frame.run(conn, grande)
    assert out["title"] == " ".join(f"w{i}" for i in range(frame.TITLE_WORDS)) + " — interview"
    assert len(out["orientation"].split()) == frame.ORIENTATION_WORDS
    assert store.material(conn, grande)["title"] == out["title"]


def test_more_than_twelve_sections_are_capped(conn, grande, model):
    sents = store.sentences(conn, grande)
    picks = [(sid, t) for sid, t in sents if len(t.split()) >= 6][:20]
    model.queue(_answer(display="segments",
                        segments=[{"anchor": " ".join(t.split()[:6]), "label": f"Part {i}"}
                                  for i, (_, t) in enumerate(picks)]))
    out = frame.run(conn, grande)
    assert len(out["segments"]) == frame.MAX_SEGMENTS
    assert len(store.segments(conn, grande)) == frame.MAX_SEGMENTS
    assert "Part 13" in str(out["dropped"])


def test_an_unknown_role_becomes_other_and_a_repeated_label_is_kept_once(conn, grande, model):
    model.queue(_answer(speakers=[{"label": "GRANDE", "name": "M. Grande", "role": "narrator"},
                                  {"label": "GRANDE", "name": "again", "role": "participant"}]))
    out = frame.run(conn, grande)
    assert [(s["label"], s["role"]) for s in out["speakers"]] == [("GRANDE", "other")]
    assert len(store.speakers(conn, grande)) == 1
