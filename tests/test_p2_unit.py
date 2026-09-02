"""P2's own checks: the validators the contract tests do not walk, and the three layouts.

Every assertion here is against a real payload shape or a real transcript — a validator checked
only against a payload invented to satisfy it is not a validator.
"""
from __future__ import annotations

import pytest

from app import store
from app.engine import read

read = pytest.importorskip("app.engine.read")
themes = pytest.importorskip("app.engine.themes")


def _framed(conn, mid, display="turns"):
    store.save_frame(conn, mid, kind="interview", display=display, title="Grande, M.",
                     speakers=[{"label": "PHILLIPS", "name": "Phillips", "role": "interviewer"},
                               {"label": "GRANDE", "name": "M. Grande", "role": "participant"}],
                     segments=[])


# ---- READ --------------------------------------------------------------------------------------

def test_new_codes_are_capped_in_proportion_to_the_material(conn, project, grande, model):
    _framed(conn, grande)
    model.queue({"codes": [{"code": {"name": f"C{i}", "definition": "d"}, "sids": ["S050"]}
                           for i in range(60)]})
    out = read.run(conn, grande)
    cap = read.new_cap(len(store.sentences(conn, grande)))   # scales with the material
    assert out["new"] == cap
    assert len(store.codebook(conn, project)) == cap


def test_a_repeated_name_becomes_one_code_and_keeps_both_sets_of_sids(conn, project, grande,
                                                                     model):
    _framed(conn, grande)
    model.queue({"codes": [{"code": {"name": "Work", "definition": "d"}, "sids": ["S050"]},
                           {"code": "Work", "sids": ["S051", "S050"]}]})
    out = read.run(conn, grande)
    assert len(store.codebook(conn, project)) == 1
    assert out["new"] == 1 and out["reused"] == 0
    assert {r["sid"] for r in store.hits(conn, grande)} == {"S050", "S051"}


def test_a_code_whose_every_sid_is_bogus_is_not_created(conn, project, grande, model):
    _framed(conn, grande)
    model.queue({"codes": [{"code": {"name": "Ghost", "definition": "d"}, "sids": ["S999999"]}]})
    out = read.run(conn, grande)
    assert store.codebook(conn, project) == [] and out["dropped_sids"] == ["S999999"]


def test_each_display_lays_the_material_out_its_own_way(conn, grande, model):
    """`turns` prefixes speakers, `segments` heads sections, `plain` is bare — and all three
    print every sentence id, because a code that cannot cite cannot be checked."""
    shown = {}
    for display in ("turns", "segments", "plain"):
        _framed(conn, grande, display=display)
        if display == "segments":
            store.save_frame(conn, grande, kind="interview", display="segments", title="t",
                             speakers=[], segments=[{"sid": "S050", "label": "Getting there"}])
        model.queue({"codes": []})
        model.calls.clear()
        read.run(conn, grande)
        shown[display] = model.shown()
    assert "[GRANDE]" in shown["turns"] and "[GRANDE]" not in shown["plain"]
    assert "## Getting there" in shown["segments"]
    for text in shown.values():
        assert "S050" in text and "S432" in text


def test_the_focus_reaches_the_reading_verbatim(conn, project, grande, model):
    conn.execute("UPDATE project SET focus=? WHERE id=?",
                 ("Why do people stay? Not why they leave.", project))
    _framed(conn, grande)
    model.queue({"codes": []})
    read.run(conn, grande)
    assert "Why do people stay? Not why they leave." in model.shown()


# ---- THEMES ------------------------------------------------------------------------------------

def test_an_unknown_code_name_is_ignored_and_a_known_one_is_gathered(conn, project, grande,
                                                                     model):
    _framed(conn, grande)
    model.queue({"codes": [{"code": {"name": "Work", "definition": "d"}, "sids": ["S050"]}]})
    read.run(conn, grande)
    model.queue({"themes": [{"new": True, "name": "Making a living", "gist": "g",
                             "code_names": ["Work", "No such code"]}]})
    out = themes.run(conn, project)
    assert [c["name"] for c in store.theme_codes(conn, out["themes"][0])] == ["Work"]


def test_no_more_than_twelve_themes_stay_live(conn, project, model):
    model.queue({"themes": [{"new": True, "name": f"T{i}", "gist": "g", "code_names": []}
                            for i in range(20)]})
    themes.run(conn, project)
    assert len(store.live_themes(conn, project)) == themes.MAX_THEMES


def test_a_merge_into_a_theme_that_is_not_live_is_refused(conn, project, model):
    a = store.save_theme(conn, project, tid=None, name="Work", gist="g", code_ids=[])
    model.queue({"themes": [{"id": a, "name": "Work", "gist": "g", "code_names": [],
                             "merge_into": "t-does-not-exist"}]})
    out = themes.run(conn, project)
    assert out["merged"] == []
    assert conn.execute("SELECT status FROM theme WHERE id=?", (a,)).fetchone()[0] == "live"


def test_the_codebook_shows_which_materials_a_code_spans(conn, project, grande, rodwin, model):
    for mid, title in ((grande, "Grande, M."), (rodwin, "Rodwin")):
        store.save_frame(conn, mid, kind="interview", display="turns", title=title,
                         speakers=[], segments=[])
        model.queue({"codes": [{"code": {"name": "Work", "definition": "d"}, "sids": ["S050"]}]})
        read.run(conn, mid)
    model.calls.clear()
    model.queue({"themes": []})
    themes.run(conn, project)
    shown = model.shown()
    assert "Grande" in shown and "Rodwin" in shown


def test_a_full_theme_set_can_turn_over(conn, project, model):
    """At the cap, 'merge A into B and add C' used to drop C because the cap was checked before
    A had gone. The set could only shrink, and 'split this theme' did nothing, silently."""
    from app.engine import themes
    ids = [store.save_theme(conn, project, tid=None, name=f"T{i}", gist="g", code_ids=[])
           for i in range(themes.MAX_THEMES)]
    model.queue({"themes": [{"id": ids[0], "name": "T0", "gist": "g", "code_names": [],
                             "merge_into": ids[1]},
                            {"new": True, "name": "Brand new", "gist": "g", "code_names": []}]})
    themes.run(conn, project)
    live = {t["name"] for t in store.live_themes(conn, project)}
    assert "Brand new" in live and "T0" not in live
    assert len(live) == themes.MAX_THEMES


def test_the_codebook_shown_to_themes_carries_counts_not_material_names(conn, analysed):
    """Handed material titles, the theme step wrote them straight back into gists — 'absent from
    the bakery interview' — a conclusion in the slot meant for a definition. Counts are
    structure; a title is an invitation."""
    from app.engine import themes
    block = themes._codebook_block(conn, analysed["pid"])
    for m in store.materials(conn, analysed["pid"]):
        assert (m["title"] or m["name"]) not in block
    assert "marked in" in block and "of 2 materials" in block
