"""P2 — codes and themes. `app/engine/read.py`, `app/engine/themes.py`, their two prompts.

    read.run(conn, mid) -> {"new", "reused", "hits", "dropped_sids"}
    themes.run(conn, pid, *, feedback="") -> {"themes": [...], "merged": [...]}
"""
from __future__ import annotations

import pytest

from app import store

read = pytest.importorskip("app.engine.read")
themes = pytest.importorskip("app.engine.themes")


def _framed(conn, mid):
    store.save_frame(conn, mid, kind="interview", display="turns", title="Grande, M.",
                     speakers=[{"label": "GRANDE", "name": "M. Grande", "role": "participant"}],
                     segments=[])


def test_a_sid_that_is_not_in_this_material_is_dropped_not_stored(conn, grande, model):
    _framed(conn, grande)
    model.queue({"codes": [{"code": {"name": "Work", "definition": "making a living"},
                            "sids": ["S050", "S999999"]}]})
    out = read.run(conn, grande)
    assert "S999999" in out["dropped_sids"]
    assert {r["sid"] for r in store.hits(conn, grande)} == {"S050"}


def test_the_frame_is_shown_to_the_reading(conn, grande, model):
    """READ must know what it is reading — who speaks and what kind of material this is."""
    _framed(conn, grande)
    model.queue({"codes": []})
    read.run(conn, grande)
    shown = model.shown()
    assert "interview" in shown.lower()
    assert "M. Grande" in shown or "GRANDE" in shown


def test_an_existing_code_is_reused_by_name_and_keeps_its_id(conn, project, grande, rodwin, model):
    _framed(conn, grande)
    _framed(conn, rodwin)
    model.queue({"codes": [{"code": {"name": "Work", "definition": "d"}, "sids": ["S050"]}]},
                {"codes": [{"code": "Work", "sids": ["S050"]}]})
    read.run(conn, grande)
    first = {r["id"] for r in store.codebook(conn, project)}
    out = read.run(conn, rodwin)
    assert {r["id"] for r in store.codebook(conn, project)} == first
    assert out["reused"] == 1 and out["new"] == 0


def test_the_caps_hold(conn, grande, model):
    _framed(conn, grande)
    model.queue({"codes": [{"code": {"name": f"C{i}", "definition": "d"}, "sids": ["S050"]}
                           for i in range(60)]})
    read.run(conn, grande)
    assert len(store.hits(conn, grande)) <= 40


def test_a_merged_theme_is_marked_not_deleted_and_its_moments_follow(conn, project, grande, model,
                                                                    quote):
    a = store.save_theme(conn, project, tid=None, name="Work", gist="g", code_ids=[])
    b = store.save_theme(conn, project, tid=None, name="Labour", gist="g", code_ids=[])
    sid, text = quote(grande)
    store.save_moments(conn, grande, b, [{"claim": "c", "anchor": " ".join(text.split()[:6]),
                                          "sid": sid}])
    model.queue({"themes": [{"id": a, "name": "Work", "gist": "how a living is made",
                             "code_names": []},
                            {"id": b, "name": "Labour", "gist": "g", "code_names": [],
                             "merge_into": a}]})
    themes.run(conn, project)
    row = conn.execute("SELECT * FROM theme WHERE id=?", (b,)).fetchone()
    assert row["status"] == "merged" and row["merged_into"] == a
    assert len(store.thread(conn, grande, a)) == 1


def test_theme_feedback_reaches_the_prompt_verbatim(conn, project, model):
    store.save_theme(conn, project, tid=None, name="Work", gist="g", code_ids=[])
    model.queue({"themes": []})
    themes.run(conn, project, feedback="Work and money are not the same thing.")
    assert "Work and money are not the same thing." in model.shown()
