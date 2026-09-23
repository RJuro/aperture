"""P45 — what the review of the Livicia Antoine reading asked for, where Python can hold it.

Two of its points are bookkeeping. The angles named kinship and emotional management and no theme
took either up, with nothing on the page saying so: THEMES now says, for every angle of a material
just read, which theme took up its ground or why none did. And one line carried two claims on the
same sentence, counted as two findings: a line now keeps one moment to a passage.
"""
from __future__ import annotations

from app import store
from app.engine import angles, synth, themes

ANGLES = angles.prose("Domestic work", ["Care"], [
    {"name": "Kin as employer", "why": "Her grandchildren are the children she minds.",
     "questions": ["Who pays?", "Is it pay?"]},
    {"name": "Managing her own reactions", "why": "She says she pretends not to see.",
     "questions": ["What is not shown?", "To whom?"]},
    {"name": "How the interviewer is placed", "why": "The interviewer is named as a founder.",
     "questions": ["Who asks?", "What do the questions lead to?"]},
])


def test_the_angles_are_read_back_out_of_the_prose_they_are_kept_as():
    assert [n for n, _ in angles.listed(ANGLES)] == [
        "Kin as employer", "Managing her own reactions", "How the interviewer is placed"]
    assert angles.listed("") == [] and angles.listed("Where this material sits: x.") == []


def test_each_angle_says_which_theme_took_it_up_or_why_none_did(conn, project, grande, model):
    store.save_summary(conn, "material", grande, "angles", ANGLES)
    kin = store.save_theme(conn, project, tid=None, name="Family as the employer",
                           gist="a definition", code_ids=[])
    model.queue({"themes": [{"id": kin, "name": "Family as the employer", "gist": "a definition",
                             "code_names": [], "nearest": None}],
                 "lenses": [
        {"angle": "Kin as employer", "theme": kin},
        {"angle": "managing her OWN reactions", "theme": None,
         "why": "The codes mark no passage about it."},
        {"angle": "An angle this material never had", "theme": kin},
    ]})
    themes.run(conn, project, material_id=grande)

    said = store.get_summary(conn, "material", grande, "lenses")["text"].splitlines()
    assert said == ["Kin as employer — taken up by Family as the employer.",
                    "Managing her own reactions — no theme took this up: The codes mark no "
                    "passage about it.",
                    "How the interviewer is placed — the theme pass did not say."]
    # Never the material's account: a page asking for its best summary is not handed this.
    assert store.get_summary(conn, "material", grande)["stage"] != "lenses"


def test_the_pass_is_shown_the_angles_by_name(conn, project, grande, model):
    store.save_summary(conn, "material", grande, "angles", ANGLES)
    model.queue({"themes": []})
    themes.run(conn, project, material_id=grande)
    assert "- Managing her own reactions" in model.shown("themes")
    assert "She says she pretends" not in model.shown("themes")


def test_a_line_keeps_one_moment_to_a_passage(conn, project, grande, quote):
    sid, text = quote(grande)
    tid = store.save_theme(conn, project, tid=None, name="Work", gist="a living", code_ids=[])
    theme = dict(conn.execute("SELECT * FROM theme WHERE id=?", (tid,)).fetchone())
    anchor = " ".join(text.split()[:6])
    kept, dropped, _ = synth._thread_kept(
        conn, grande, tid,
        {"moments": [{"claim": "First.", "anchor": anchor, "sid": sid},
                     {"claim": "The same again.", "anchor": anchor, "sid": sid}],
         "summary": "s", "fit": ""},
        store.sentences(conn, grande), theme, project, run_id=None)
    assert [m["claim"] for m in kept] == ["First."]
    assert any(f"already has one on {sid}" in d for d in dropped)


def test_a_claim_a_little_over_the_ask_is_kept_whole(conn, project, grande, quote):
    """The prompt asks for 30 words; a 34-word claim used to reach the page cut off with "…"."""
    sid, text = quote(grande)
    tid = store.save_theme(conn, project, tid=None, name="Care", gist="care", code_ids=[])
    theme = dict(conn.execute("SELECT * FROM theme WHERE id=?", (tid,)).fetchone())
    claim = ("When the parent calls to ask what she gave the crying child, she answers that the "
             "child is hot or hungry and tells the parent to wash it and feed it, then burp it "
             "and sing.")
    assert 30 < len(claim.split()) <= synth.CLAIM_CAP
    kept, _, _ = synth._thread_kept(
        conn, grande, tid, {"moments": [{"claim": claim, "anchor": " ".join(text.split()[:6]),
                                         "sid": sid}], "summary": "s", "fit": ""},
        store.sentences(conn, grande), theme, project, run_id=None)
    assert kept[0]["claim"] == claim
