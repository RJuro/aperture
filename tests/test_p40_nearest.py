"""P40 — what a theme is nearest to, and what sorts a passage into it rather than into that one.

A record came back with three themes about language and two about the same building, and no
reader of the definitions could say which passage belonged where. The calibration session the
record was judged against had made the point in one line: a theme that cannot say what separates
it from its neighbour is not a separate theme. So THEMES is asked, for every open theme and every
candidate, what it is most easily confused with and what tells the two apart — and Python holds
the answer to something a researcher can act on: a live theme of this project, a boundary of at
most twenty words, or nothing at all, which is also an answer.
"""
from __future__ import annotations

import pytest

from app import llm, store

themes = pytest.importorskip("app.engine.themes")

PROMPTS = llm.Path(llm.__file__).parent / "prompts"

DIFFERS = "This is the moment of noticing; that is the record written afterwards."


def _open(conn, pid, name) -> str:
    return store.save_theme(conn, pid, tid=None, name=name, gist="a definition", code_ids=[])


def _candidate(conn, pid, name) -> str:
    tid = _open(conn, pid, name)
    store.set_hold(conn, tid, "candidate")
    return tid


def _nearest(conn, tid):
    row = conn.execute("SELECT nearest_id, nearest_note FROM theme WHERE id=?", (tid,)).fetchone()
    return row["nearest_id"], row["nearest_note"]


# ---- what is stored ----------------------------------------------------------------------------

def test_an_open_theme_and_a_candidate_each_keep_what_they_are_nearest_to(conn, project, model):
    """Both holds are asked, because both are what the researcher sorts passages with. A frozen
    theme is the one hold that is not (its words are the researcher's), and a merged one is gone."""
    handover = _open(conn, project, "Handover as where errors are caught")
    paperwork = _open(conn, project, "Paperwork as protection")
    checking = _candidate(conn, project, "Asking a colleague to check")

    model.queue({"themes": [
        {"id": handover, "name": "Handover as where errors are caught", "gist": "a definition",
         "code_names": [], "nearest": {"id": paperwork, "differs": DIFFERS}},
        {"id": paperwork, "name": "Paperwork as protection", "gist": "a definition",
         "code_names": [], "nearest": {"id": handover, "differs": "This is what a record is for."}},
    ], "candidates": [
        {"id": checking, "code_names": [], "nearest": {"id": handover, "differs": DIFFERS}},
    ]})
    out = themes.run(conn, project)

    assert _nearest(conn, handover) == (paperwork, DIFFERS)
    assert _nearest(conn, checking) == (handover, DIFFERS)
    assert out["dropped"] == []


def test_a_nearest_that_is_not_a_live_theme_of_this_project_is_stored_as_none_and_said(
        conn, project, model):
    """The id has to name something the researcher can go and read beside this theme. A pointer to
    a theme of another project, to one folded away, or to this theme itself prints as a boundary
    that cannot be checked, so it is not stored — and the run says it was set aside."""
    tid = _open(conn, project, "Handover as where errors are caught")
    model.queue({"themes": [
        {"id": tid, "name": "Handover as where errors are caught", "gist": "a definition",
         "code_names": [], "nearest": {"id": "t0aa41", "differs": DIFFERS}},
    ], "candidates": []})

    out = themes.run(conn, project)

    assert _nearest(conn, tid) == (None, "")
    assert any("t0aa41" in note for note in out["dropped"]), out["dropped"]


def test_a_theme_is_not_nearest_to_itself(conn, project, model):
    """Its own id says nothing about where a passage goes, and two themes pointing at each other
    is what the duplicate check reads — one pointing at itself would read as a pair of one."""
    tid = _open(conn, project, "Handover as where errors are caught")
    model.queue({"themes": [
        {"id": tid, "name": "Handover as where errors are caught", "gist": "a definition",
         "code_names": [], "nearest": {"id": tid, "differs": DIFFERS}},
    ], "candidates": []})

    out = themes.run(conn, project)

    assert _nearest(conn, tid) == (None, "")
    assert out["dropped"]


def test_the_boundary_is_capped_at_twenty_words(conn, project, model):
    """The prompt asks for twenty and Python holds it, as everywhere else: a cap only in the
    prompt is a request. The researcher reads this under the definition; a paragraph there is a
    second gist."""
    tid = _open(conn, project, "Handover as where errors are caught")
    other = _open(conn, project, "Paperwork as protection")
    long = " ".join(f"w{i}" for i in range(1, 31))
    model.queue({"themes": [
        {"id": tid, "name": "Handover as where errors are caught", "gist": "a definition",
         "code_names": [], "nearest": {"id": other, "differs": long}},
    ], "candidates": []})

    themes.run(conn, project)

    _, note = _nearest(conn, tid)
    assert "w20" in note and "w21" not in note
    assert len(note.split()) <= themes.NEAREST_WORDS + 1     # the mark that says it was cut


def test_nothing_close_is_an_answer_and_not_a_gap(conn, project, model):
    """A theme with no neighbour is the ordinary case in a small set, and inventing one would put
    a boundary in the record that no passage supports. `null` is stored as it stands, silently."""
    tid = _open(conn, project, "Handover as where errors are caught")
    model.queue({"themes": [
        {"id": tid, "name": "Handover as where errors are caught", "gist": "a definition",
         "code_names": [], "nearest": None},
    ], "candidates": []})

    out = themes.run(conn, project)

    assert _nearest(conn, tid) == (None, "")
    assert out["dropped"] == []


def test_a_frozen_theme_is_not_asked_for_one_and_does_not_get_one(conn, project, model):
    """A frozen theme comes back with its id and its codes and nothing else (rule 14). What this
    material does to it is a tension, which the researcher reads and acts on; a boundary written
    over a definition they declared final would be the instrument revising it."""
    tid = _open(conn, project, "Handover as where errors are caught")
    store.set_hold(conn, tid, "frozen")
    other = _open(conn, project, "Paperwork as protection")
    model.queue({"themes": [
        {"id": tid, "code_names": [], "nearest": {"id": other, "differs": DIFFERS}},
        {"id": other, "name": "Paperwork as protection", "gist": "a definition",
         "code_names": []},
    ], "candidates": []})

    themes.run(conn, project)

    assert _nearest(conn, tid) == (None, "")
    for name in ("themes", "themes_cross"):
        assert "A frozen theme is not asked for one." in (PROMPTS / f"{name}.md").read_text()


# ---- what the model is shown ---------------------------------------------------------------

def test_both_prompts_ask_for_the_boundary_and_say_what_to_do_without_one(conn, project, model):
    """The rule's point: where the difference cannot be named, the two themes are one, and the
    answer says so with `merge_into` rather than with a boundary nobody could apply."""
    model.queue({"themes": [], "candidates": []})
    themes.run(conn, project)
    model.queue({"themes": [], "candidates": []})
    themes.run_cross(conn, project, [])

    shown = model.shown("themes")
    assert shown.count("most easily confused with") == 2, "both prompts ask"
    assert shown.count("give `merge_into` and no `nearest`") == 2
    assert shown.count('Write `"nearest": null` where nothing else is close') == 2


def test_the_prose_rules_reach_both_prompts(conn, project, model):
    """Names, gists, tension notes and now boundaries are all short prose a researcher reads, so
    both prompts carry the short block — from the file, at the end of the system message."""
    model.queue({"themes": [], "candidates": []})
    themes.run(conn, project)
    model.queue({"themes": [], "candidates": []})
    themes.run_cross(conn, project, [])

    shown = model.shown("themes")
    assert shown.count("HOW TO WRITE") == 2
    assert shown.count("Subject: a person, a group, a material, or the claims") == 2


def test_the_fold_criterion_is_shown_only_when_the_researcher_asked_to_consolidate(
        conn, project, model):
    """Told only to look for overlap, a reader folds two themes that speak about the same thing.
    The criterion is the calibration session's own, and it belongs to the pass that folds by
    definition rather than to the one folding down to a cap."""
    model.queue({"themes": [], "candidates": []})
    themes.run_cross(conn, project, [])
    assert "would sort every passage" not in model.shown("themes")

    model.calls.clear()
    model.queue({"themes": [], "candidates": []})
    themes.run_cross(conn, project, [], consolidating=True)
    shown = model.shown("themes")
    assert "Two themes are folded only when one definition would sort every passage of the other."\
        in shown
    assert "A shared subject is not a shared pattern, and similar wording is not a reason to fold."\
        in shown
