"""P7 — angles. `app/engine/angles.py`, `app/prompts/angles.md`, and read.md's new slot.

    angles.run(conn, mid) -> {"field", "subareas", "angles", "text", "dropped"}
    angles.block(conn, mid) -> the prose READ is shown

It runs after FRAME and before READ, persists through
`store.save_summary(conn, "material", mid, "angles", text)`, and writes nothing else.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from app import context, ingest, llm, store

angles = pytest.importorskip("app.engine.angles")

PROMPTS = Path(llm.__file__).resolve().parent / "prompts"


def _angle(n=1, questions=3):
    return {"name": f"Angle number {n}", "why": f"The material keeps returning to number {n}.",
            "questions": [f"What does the material say about {n}, part {q}?"
                          for q in range(questions)]}


def _answer(**over):
    a = {"field": "Social history of postwar labour migration",
         "subareas": ["Household economies", "Documents and legal status"],
         "angles": [_angle(n) for n in range(1, 7)]}
    a.update(over)
    return a


def _framed(conn, mid):
    store.save_frame(conn, mid, kind="interview", display="turns", title="Grande, M.",
                     speakers=[{"label": "PHILLIPS", "name": "Phillips", "role": "interviewer"},
                               {"label": "GRANDE", "name": "M. Grande", "role": "participant"}],
                     segments=[])
    store.save_summary(conn, "material", mid, "orientation",
                       "A 1978 oral history about leaving Italy for work.")


# ---- the caps ----------------------------------------------------------------------------------

def test_the_caps_hold(conn, grande, model):
    _framed(conn, grande)
    model.queue(_answer(angles=[_angle(n, questions=9) for n in range(1, 21)],
                        subareas=[f"Subarea {n}" for n in range(20)]))
    out = angles.run(conn, grande)
    assert len(out["angles"]) == angles.MAX_ANGLES
    assert all(len(a["questions"]) <= angles.MAX_QUESTIONS for a in out["angles"])
    assert len(out["subareas"]) <= angles.MAX_SUBAREAS
    text = store.get_summary(conn, "material", grande, "angles")["text"]
    assert "Angle number 8" in text and "Angle number 9" not in text


def test_over_long_text_is_trimmed_not_stored_raw(conn, grande, model):
    _framed(conn, grande)
    model.queue(_answer(field="field " * 40,
                        angles=[{"name": "name " * 40, "why": "why " * 200,
                                 "questions": ["question " * 90, "another question here"]}]))
    out = angles.run(conn, grande)
    a = out["angles"][0]
    assert len(a["name"].split()) <= angles.NAME_WORDS
    assert len(a["why"].split()) <= angles.WHY_WORDS
    assert max(len(q.split()) for q in a["questions"]) <= angles.QUESTION_WORDS
    assert len(out["field"].split()) <= angles.FIELD_WORDS


# ---- what is unusable never reaches the database -----------------------------------------------

def test_an_angle_that_asks_nothing_is_dropped_and_the_rest_stand(conn, grande, model):
    _framed(conn, grande)
    model.queue(_answer(angles=[_angle(1), {"name": "A heading, not an angle", "why": "because",
                                            "questions": ["only one question here?"]}]))
    out = angles.run(conn, grande)
    assert [a["name"] for a in out["angles"]] == ["Angle number 1"]
    assert "A heading, not an angle" in str(out["dropped"])
    assert "A heading, not an angle" not in store.get_summary(conn, "material", grande,
                                                              "angles")["text"]


def test_an_angle_with_no_name_or_no_reason_is_dropped(conn, grande, model):
    _framed(conn, grande)
    model.queue(_answer(angles=[{"name": "", "why": "w", "questions": ["a?", "b?"]},
                                {"name": "Nameless reason", "why": "  ",
                                 "questions": ["a?", "b?"]},
                                "a bare string, not an angle at all",
                                _angle(1)]))
    out = angles.run(conn, grande)
    assert [a["name"] for a in out["angles"]] == ["Angle number 1"]
    assert len(out["dropped"]) >= 2


def test_the_same_angle_twice_is_kept_once(conn, grande, model):
    _framed(conn, grande)
    model.queue(_answer(angles=[_angle(1), _angle(1), _angle(2)]))
    out = angles.run(conn, grande)
    assert [a["name"] for a in out["angles"]] == ["Angle number 1", "Angle number 2"]


def test_nothing_unknown_from_the_payload_reaches_the_stored_text(conn, grande, model):
    _framed(conn, grande)
    model.queue(_answer(angles=[dict(_angle(1), verdict="work is a necessity",
                                     sids=["S001"], confidence=0.9)],
                        codes=["Work"], summary="the reading found x"))
    out = angles.run(conn, grande)
    text = store.get_summary(conn, "material", grande, "angles")["text"]
    assert set(out["angles"][0]) == {"name", "why", "questions"}
    for stray in ("verdict", "work is a necessity", "S001", "confidence",
                  "the reading found x"):
        assert stray not in text


# ---- what is stored is prose a person reads ----------------------------------------------------

def test_the_stored_text_is_prose_a_person_could_read(conn, grande, model):
    _framed(conn, grande)
    model.queue(_answer())
    out = angles.run(conn, grande)
    text = store.get_summary(conn, "material", grande, "angles")["text"]
    assert text == out["text"]
    assert not any(ch in text for ch in "{}[]"), "a payload on the page is not prose"
    assert '"name"' not in text and '"questions"' not in text
    assert "Social history of postwar labour migration" in text
    assert "Household economies" in text
    assert "Angle number 1" in text
    assert "The material keeps returning to number 1." in text
    assert "What does the material say about 1, part 0?" in text
    said = [w for w in context._BANNED if w in text.lower()]
    assert not said, f"the page would say our own words: {said}"


def test_the_prose_survives_a_model_that_returns_almost_nothing(conn, grande, model):
    _framed(conn, grande)
    model.queue({"angles": []})
    out = angles.run(conn, grande)
    assert out["angles"] == []
    assert store.get_summary(conn, "material", grande, "angles") is not None


# ---- what the model is shown -------------------------------------------------------------------

def test_the_frame_and_the_description_reach_the_prompt(conn, project, grande, model):
    _framed(conn, grande)
    store.set_focus(conn, project, "I am looking for how work and papers hold each other up")
    store.set_brief(conn, project, "Two interviews so far, both about crossings.")
    store.save_theme(conn, project, tid=None, name="Work and trade", gist="how a living is made",
                     code_ids=[])
    model.queue(_answer())
    angles.run(conn, grande)
    shown = model.shown("angles")
    assert "interview" in shown.lower()
    assert "M. Grande" in shown and "Phillips" in shown
    assert "A 1978 oral history about leaving Italy for work." in shown
    assert "how work and papers hold each other up" in shown, "the focus goes in verbatim"
    assert "Two interviews so far" in shown
    assert "Work and trade" in shown


def test_angles_see_more_of_the_material_than_the_shape_check_does(conn, grande, model):
    """FRAME's budget answers 'what shape is this'. Angles answer 'what is this about', and what a
    first reading undercodes is past FRAME's first 6000 characters."""
    _framed(conn, grande)
    raw = store.material(conn, grande)["text"]
    middle = raw[8000:8080]
    assert middle not in ingest.head_and_tail(raw), "pick a snippet FRAME genuinely cannot see"
    model.queue(_answer())
    angles.run(conn, grande)
    assert middle in model.shown("angles")


def test_material_with_nobody_speaking_is_not_given_a_speaker(conn, project, model):
    mid = store.add_material(conn, project, "Notes", "Arrived before six, the stalls were quiet.")
    store.save_sentences(conn, mid, ingest.sentences(store.material(conn, mid)["text"]))
    store.save_frame(conn, mid, kind="fieldnotes", display="plain", title="Market notes",
                     speakers=[], segments=[])
    model.queue(_answer())
    angles.run(conn, mid)
    shown = model.shown("angles")
    assert "Nobody is marked as speaking" in shown
    assert "interviewer" not in shown.split("THE MATERIAL")[0].lower()


def test_the_prompt_states_its_caps_as_numbers_and_shows_the_shape(conn, grande, model):
    """A cap only in Python is a surprise; a cap only in the prompt is a request."""
    _framed(conn, grande)
    model.queue(_answer())
    angles.run(conn, grande)
    system = model.calls[-1]["system"]
    assert f" {angles.MAX_ANGLES} angles" in system
    assert f"2 to {angles.MAX_QUESTIONS} `questions`" in system
    assert str(angles.NAME_WORDS) in system and str(angles.WHY_WORDS) in system
    assert '"questions"' in system and '"field"' in system, "give it the worked shape"
    assert "WHERE TO LOOK" in system and "WHAT IS FOUND" in system


# ---- where it is stored, and what READ is shown -------------------------------------------------

def test_it_is_stored_as_angles_and_the_page_still_shows_the_description(conn, grande, model):
    _framed(conn, grande)
    model.queue(_answer())
    angles.run(conn, grande)
    assert store.get_summary(conn, "material", grande, "angles") is not None
    assert store.get_summary(conn, "material", grande, "reading") is None
    best = store.get_summary(conn, "material", grande)
    assert best["stage"] == "orientation", "the page shows what this material is, not the angles"


def test_a_rerun_supersedes_rather_than_piling_up(conn, grande, model):
    _framed(conn, grande)
    model.queue(_answer(), _answer(field="Something else entirely"))
    angles.run(conn, grande)
    angles.run(conn, grande)
    live = conn.execute("SELECT * FROM summary WHERE ref_id=? AND stage='angles' AND "
                        "status='live'", (grande,)).fetchall()
    assert len(live) == 1 and "Something else entirely" in live[0]["text"]


def test_the_block_read_is_shown_is_the_text_the_researcher_reads(conn, grande, model):
    _framed(conn, grande)
    assert angles.block(conn, grande).strip(), "an empty slot in a prompt comes back empty"
    model.queue(_answer())
    out = angles.run(conn, grande)
    assert angles.block(conn, grande) == out["text"]


# ---- read.md still compiles, with its new slot --------------------------------------------------

def test_read_md_compiles_with_its_new_slot_and_states_the_rule():
    text = (PROMPTS / "read.md").read_text()
    slots = sorted(set(re.findall(r"\{\{(\w+)\}\}", text)))
    assert "angles" in slots
    system, user = llm.prompt("read", **{s: f"<<{s}>>" for s in slots})
    assert "<<angles>>" in user, "the slot has to be somewhere the model will read it"
    assert "WHERE TO LOOK" in system and "WHAT IS FOUND" in system
    assert "never because an angle suggested it" in system


def test_angles_md_compiles_with_exactly_the_slots_the_engine_fills(conn, grande, model):
    text = (PROMPTS / "angles.md").read_text()
    slots = sorted(set(re.findall(r"\{\{(\w+)\}\}", text)))
    assert slots == ["brief", "focus", "frame", "material", "max_angles", "max_questions",
                     "orientation", "themes"]
    _framed(conn, grande)
    model.queue(_answer())
    angles.run(conn, grande)          # llm.prompt raises on a slot that drifted either way
    assert model.calls[-1]["label"] == "angles"
