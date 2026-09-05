"""P23 — the three holds on a theme (PLAN.md §12). `theme.hold`, `theme_note`, the THEMES
enforcement per hold, and what DOC does with a candidate.

A four-interview project came back with twelve themes, eleven of them "in 4 of 4", and a ceiling
change left the set unable to move. Three consequences, each of them a rule here: a pattern seen
in one case is a candidate and not a category; saturation is counted per theme; and the analyst,
not the instrument, declares a theme final — after which new material is applied to it and what
pulls against it is logged, never written in.
"""
from __future__ import annotations

import sqlite3

import pytest

from app import db, store

synth = pytest.importorskip("app.engine.synth")
themes = pytest.importorskip("app.engine.themes")


def _ready(conn, mid):
    store.save_frame(conn, mid, kind="interview", display="turns", title=f"M{mid[-4:]}",
                     speakers=[], segments=[])
    store.save_summary(conn, "material", mid, "orientation", "A 1978 oral history.")


def _coded(conn, pid, mid, name) -> str:
    """One code, marked in this material. Returns its id."""
    store.save_codes(conn, pid, mid, [{"name": name, "definition": "making a living",
                                       "sids": [store.sentences(conn, mid)[5][0]]}])
    return [c["id"] for c in store.codebook(conn, pid) if c["name"] == name][0]


def _moments(quote, mid, n=5, at=40):
    return [{"claim": f"claim {i}", "anchor": " ".join(quote(mid, at=at + i * 9)[1].split()[:8]),
             "sid": quote(mid, at=at + i * 9)[0]} for i in range(n)]


def _doc_calls(model, quote, mid, lines=1):
    """What a full DOC of `mid` asks for: a line per theme followed, the check over the claims,
    the summary, and the check over the summary."""
    for i in range(lines):
        model.queue({"moments": _moments(quote, mid, 5, at=40 + i * 60)})
    model.queue({"verdicts": []})
    model.queue({"summary": "what the reading found", "questions": "what remains?", "people": []})
    model.queue({"verdicts": []})


def _candidate(conn, pid, name, code_ids) -> str:
    tid = store.save_theme(conn, pid, tid=None, name=name, gist="a living", code_ids=code_ids)
    store.set_hold(conn, tid, "candidate")
    return tid


# ---- born a candidate ---------------------------------------------------------------------

def test_a_new_theme_is_born_a_candidate_and_does_not_count_against_the_ceiling(conn, project,
                                                                               model):
    """A pattern the model saw in one material is not a project theme, so the set can go on
    growing at the cap: the four project themes stay four, and the fifth is a candidate."""
    cap = themes.ceiling(conn, project)
    live = [store.save_theme(conn, project, tid=None, name=f"T{i}", gist="g", code_ids=[])
            for i in range(cap)]
    model.queue({"themes": [{"id": t, "name": f"T{i}", "gist": "g", "code_names": []}
                            for i, t in enumerate(live)]
                 + [{"new": True, "name": "Seen once", "gist": "g", "code_names": []}]})
    themes.run(conn, project)

    assert len(store.live_themes(conn, project)) == cap
    coined = store.candidates(conn, project)
    assert [t["name"] for t in coined] == ["Seen once"]
    assert coined[0]["hold"] == "candidate"


def test_only_a_known_hold_can_be_set(conn, project):
    tid = store.save_theme(conn, project, tid=None, name="Work", gist="g", code_ids=[])
    with pytest.raises(ValueError):
        store.set_hold(conn, tid, "final")


# ---- promotion by recurrence ---------------------------------------------------------------

def test_a_candidate_a_second_material_holds_a_line_under_is_proposed_by_doc(conn, project, grande,
                                                                            rodwin, model, quote):
    """Recurrence is Python's, not the model's, and it is a proposal. The candidate came out of
    Grande; Rodwin's coding carries it too, and the corpus has now said it twice — which is a
    count of two materials, not a confirmation from two independent cases, so the theme is put to
    the researcher and stays a candidate until they promote it."""
    for mid in (grande, rodwin):
        _ready(conn, mid)
    cid = _coded(conn, project, grande, "Work")
    store.save_codes(conn, project, rodwin, [{"name": "Work", "definition": "making a living",
                                              "sids": [store.sentences(conn, rodwin)[5][0]]}])
    tid = _candidate(conn, project, "Work and staying", [cid])
    sid, text = quote(grande)
    store.save_moments(conn, grande, tid, [{"claim": "c", "anchor": " ".join(text.split()[:8]),
                                            "sid": sid}])
    assert store.live_themes(conn, project) == [], "a candidate is not in the project set"

    _doc_calls(model, quote, rodwin)
    synth.doc(conn, rodwin)

    assert store.live_themes(conn, project) == [], "a proposal does not make a project theme"
    assert [t["id"] for t in store.candidates(conn, project)] == [tid]
    assert conn.execute("SELECT proposed_at FROM theme WHERE id=?", (tid,)).fetchone()[0]


def test_a_candidate_is_followed_only_where_its_codes_fired_whatever_the_gate_says(
        conn, project, grande, rodwin, model, quote, monkeypatch):
    """`APERTURE_FOLLOW` is off here — the default, under which every project theme is followed
    wherever it goes. A candidate is gated all the same: it is one material's pattern, and what
    confirms it has to be the next material's coding, not a reader sent to find it."""
    monkeypatch.delenv("APERTURE_FOLLOW", raising=False)
    for mid in (grande, rodwin):
        _ready(conn, mid)
    cid = _coded(conn, project, grande, "Work")           # marked in Grande, nowhere else
    cand = _candidate(conn, project, "Work and staying", [cid])
    theme = store.save_theme(conn, project, tid=None, name="Leaving", gist="g", code_ids=[cid])

    _doc_calls(model, quote, rodwin)
    synth.doc(conn, rodwin)

    outcomes = store.followed(conn, project)
    assert outcomes[(cand, rodwin)] == "skipped"
    assert cand not in model.shown("thread")
    assert outcomes[(theme, rodwin)] == "line", "the project theme is followed as it always was"


def test_a_candidate_this_material_confirms_keeps_its_words_and_gathers_both_materials(
        conn, project, grande, rodwin, model):
    """Rule 15 asks for the codes THIS material carries, so what comes back is one material's
    worth. Replacing with it would strip the candidate of the codes it was coined from — and a
    candidate that no longer marks its own material is one nothing can confirm."""
    first = _coded(conn, project, grande, "Work")
    second = _coded(conn, project, rodwin, "Sending money home")
    cand = _candidate(conn, project, "Work and staying", [first])

    model.queue({"themes": [], "candidates": [{"id": cand, "name": "Reworded to fit",
                                               "gist": "widened", "code_names":
                                               ["Sending money home"]}]})
    themes.run(conn, project, material_id=rodwin)

    assert {c["id"] for c in store.theme_codes(conn, cand)} == {first, second}
    row = conn.execute("SELECT * FROM theme WHERE id=?", (cand,)).fetchone()
    assert (row["name"], row["gist"], row["hold"]) == ("Work and staying", "a living", "candidate")


# ---- frozen -------------------------------------------------------------------------------

def test_a_frozen_theme_keeps_its_words_cannot_be_merged_away_and_its_tension_is_kept_apart(
        conn, project, grande, model):
    """The researcher declared it final, so Python holds the line rather than the prompt: the
    rewrite is ignored, the fold is refused, and what pulled against the definition is a note
    beside the theme — the case for unfreezing it, never an edit to the gist."""
    frozen = store.save_theme(conn, project, tid=None, name="Work and staying",
                              gist="Earning as the condition of remaining.", code_ids=[])
    store.set_hold(conn, frozen, "frozen")
    other = store.save_theme(conn, project, tid=None, name="Leaving", gist="g", code_ids=[])
    long = ("Here the placing is done by other migrants rather than by officials which the gist "
            "as written does not foresee at all and would exclude outright today")
    assert len(long.split()) > themes.TENSION_WORDS
    model.queue({"themes": [{"id": frozen, "name": "Work, staying, and everything else",
                             "gist": "Widened to fit what turned up.", "code_names": [],
                             "merge_into": other},
                            {"id": other, "name": "Leaving", "gist": "g", "code_names": []}],
                 "tensions": [{"id": frozen, "note": long},
                              {"id": other, "note": "an open theme's note is not a tension"}]})
    themes.run(conn, project, material_id=grande, run_id="r1")

    row = conn.execute("SELECT * FROM theme WHERE id=?", (frozen,)).fetchone()
    assert row["name"] == "Work and staying"
    assert row["gist"] == "Earning as the condition of remaining."
    assert (row["status"], row["hold"]) == ("live", "frozen"), "a frozen theme is not folded away"
    assert store.theme_history(conn, frozen) == [], "and nothing was rewritten to be kept"

    notes = store.theme_notes(conn, frozen)
    assert len(notes) == 1 and notes[0]["material_id"] == grande and notes[0]["run_id"] == "r1"
    assert notes[0]["text"].split()[:themes.TENSION_WORDS] == long.split()[:themes.TENSION_WORDS]
    assert "outright" not in notes[0]["text"], "clipped to 25 words"
    assert store.theme_notes(conn, other) == [], "only a frozen theme has tensions"


# ---- the saturation signal ------------------------------------------------------------------

def test_stable_passes_counts_up_on_an_unchanged_pass_and_resets_on_a_change(conn, project, model):
    """Bookkeeping only: at three or more the page offers a Freeze control, and the researcher —
    not the instrument — decides."""
    tid = store.save_theme(conn, project, tid=None, name="Work", gist="g", code_ids=[])
    same = {"themes": [{"id": tid, "name": "Work", "gist": "g", "code_names": []}]}

    def passes() -> int:
        return conn.execute("SELECT stable_passes FROM theme WHERE id=?", (tid,)).fetchone()[0]

    model.queue(same)
    themes.run(conn, project)
    assert passes() == 0, "the first pass has nothing to be the same as"
    model.queue(same)
    themes.run(conn, project)
    assert passes() == 1
    model.queue({"themes": [{"id": tid, "name": "Work", "gist": "how a living is made",
                             "code_names": []}]})
    themes.run(conn, project)
    assert passes() == 0


# ---- what the model is shown -----------------------------------------------------------------

def test_the_prompt_shows_the_three_holds_apart_and_says_where_the_project_stands(
        conn, project, grande, model):
    _ready(conn, grande)
    cid = _coded(conn, project, grande, "Work")
    frozen = store.save_theme(conn, project, tid=None, name="Frozen one", gist="g", code_ids=[])
    store.set_hold(conn, frozen, "frozen")
    open_ = store.save_theme(conn, project, tid=None, name="Open one", gist="g", code_ids=[])
    cand = _candidate(conn, project, "Candidate one", [cid])

    model.queue({"themes": []})
    themes.run(conn, project, material_id=grande)
    shown = model.shown("themes")

    for head, tid in (("FROZEN THEMES —", frozen), ("OPEN THEMES —", open_),
                      ("CANDIDATES —", cand)):
        block = shown.split(head, 1)[1].split("\n\n")[1]
        assert tid in block, f"{tid} is not under {head}"
        others = {frozen, open_, cand} - {tid}
        assert not others & set(block.split()), "each hold in its own block"
    assert store.material(conn, grande)["title"] in shown.split("CANDIDATES —", 1)[1]
    assert "2 project themes are live." in shown
    assert "merge until at most" not in shown


def test_the_over_cap_sentence_appears_only_when_the_project_is_over_the_cap(conn, project, model):
    """A project that reached twelve under the old ceiling is asked to fold, and told the number.
    Python does not fold for it: that would be Python choosing which themes are lost."""
    cap = themes.ceiling(conn, project)
    for i in range(cap + 1):
        store.save_theme(conn, project, tid=None, name=f"T{i}", gist="g", code_ids=[])
    model.queue({"themes": []})
    themes.run(conn, project)
    assert (f"{cap + 1} project themes are live and the ceiling is {cap}: merge until at most "
            f"{cap} remain") in model.shown("themes")


# ---- migration -------------------------------------------------------------------------------

def test_a_database_from_before_the_holds_comes_up_with_its_thin_themes_as_candidates(tmp_path):
    """Every theme in an older database was a project theme, because that was the only kind. The
    ones a single material carries are what the new rule calls candidates, and that is half of
    what the four-interview record with eleven themes "in 4 of 4" was made of."""
    path = tmp_path / "old.db"
    old = sqlite3.connect(path)
    old.execute("CREATE TABLE theme (id TEXT PRIMARY KEY, project_id TEXT NOT NULL, "
                "name TEXT NOT NULL, gist TEXT DEFAULT '', status TEXT NOT NULL DEFAULT 'live', "
                "merged_into TEXT)")
    old.execute("CREATE TABLE material (id TEXT PRIMARY KEY, project_id TEXT NOT NULL, "
                "name TEXT NOT NULL, text TEXT NOT NULL, kind TEXT DEFAULT '', "
                "display TEXT DEFAULT 'plain', title TEXT DEFAULT '', year TEXT DEFAULT '', "
                "state TEXT NOT NULL DEFAULT 'added', created_at TEXT NOT NULL, "
                "speakers_estimated INTEGER DEFAULT 0)")
    old.execute("CREATE TABLE moment (id TEXT PRIMARY KEY, material_id TEXT NOT NULL, "
                "theme_id TEXT NOT NULL, sid TEXT NOT NULL, position INTEGER NOT NULL, "
                "claim TEXT NOT NULL, anchor TEXT NOT NULL, run_id TEXT, "
                "status TEXT NOT NULL DEFAULT 'live')")
    for mid in ("m1", "m2"):
        old.execute("INSERT INTO material (id, project_id, name, text, created_at) "
                    "VALUES (?,'p1',?,'t','2026-01-01')", (mid, mid))
    for tid, name in (("t1", "One material"), ("t2", "Two materials"), ("t3", "No material")):
        old.execute("INSERT INTO theme (id, project_id, name, gist) VALUES (?,'p1',?,'g')",
                    (tid, name))
    for i, (tid, mid) in enumerate((("t1", "m1"), ("t2", "m1"), ("t2", "m2"))):
        old.execute("INSERT INTO moment (id, material_id, theme_id, sid, position, claim, anchor) "
                    "VALUES (?,?,?,'S001',0,'c','a')", (f"mo{i}", mid, tid))
    old.commit()
    old.close()

    conn = db.connect(path)
    try:
        assert dict(conn.execute("SELECT id, hold FROM theme")) == {
            "t1": "candidate", "t2": "open", "t3": "candidate"}
        assert conn.execute("PRAGMA user_version").fetchone()[0] == db.SCHEMA_VERSION == 16
    finally:
        conn.close()
