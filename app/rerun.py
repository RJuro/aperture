"""Feedback in, the runs it plans out. PLAN.md §1's second table, executable.

One rule holds the whole design up: **feedback runs exactly one layer down, and never re-reads.**
A rerun that re-ran READ would re-code the material under the influence of the researcher's
opinion, which is precisely the failure the anchor law exists to prevent. So READ appears in no
row here, and FRAME appears in exactly one — the layout complaint, which is about the material's
*form* and touches no code, theme or moment (sentence ids never change).

Doubt on a moment plans a CHECK, not a rerun: a mediated researcher's criticism tested less
reliable than their assent, so doubt routes to verification against the material rather than to a
rewrite. Agreement and notes plan nothing now; they are stored, shown, and ride into the next
rerun as directives.

This module imports nothing from `app.engine` — it decides, it does not run. `jobs.py` runs.
"""
from __future__ import annotations

import sqlite3

from . import store


def feedback(conn: sqlite3.Connection, fid: str) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM feedback WHERE id=?", (fid,)).fetchone()


def _run(kind: str, material_id: str | None = None, theme_id: str | None = None,
         feedback_id: str | None = None) -> dict:
    """One planned run. `feedback_id` rides along so `jobs` can hand the verbatim text to the
    steps that take it as an argument — FRAME's hint, THEMES' feedback, CHECK's question."""
    return {"kind": kind, "material_id": material_id, "theme_id": theme_id,
            "feedback_id": feedback_id}


# ---- what a row of the table does ---------------------------------------------------------------

def _nothing(conn, fb) -> list[dict]:
    return []


def _check(conn, fb) -> list[dict]:
    return [_run("check", _material_of(conn, fb), feedback_id=fb["id"])]


def _doc_thread(conn, fb) -> list[dict]:
    """A thread's target id is "<material_id>:<theme_id>" — that material, that theme only."""
    mid, _, tid = fb["target_id"].partition(":")
    return [_run("doc", mid, tid or None, fb["id"])]


def _doc_material(conn, fb) -> list[dict]:
    return [_run("doc", fb["target_id"], None, fb["id"])]


def _themes_then_docs(conn, fb) -> list[dict]:
    """Regroup first, then re-synthesise every material where that theme has moments. The DOC runs
    are whole-material (no theme_id): THEMES may rename, merge or split, so the thread that comes
    out is not always the thread that went in."""
    return [_run("themes", feedback_id=fb["id"])] + [
        _run("doc", mid, None, fb["id"]) for mid in _materials_with_theme(conn, fb["target_id"])]


def _account(conn, fb) -> list[dict]:
    """One theme, rewritten across the corpus. Regrouping the whole codebook and re-reading every
    material that carries the theme — which is what this used to plan — answers a comment about
    one theme with work on all of them."""
    return [_run("account", None, fb["target_id"], fb["id"])]


def _accounts_then_project(conn, fb) -> list[dict]:
    """A comment on the corpus rewrites each theme's account, then the corpus summary over them.

    It deliberately does NOT re-read every material. That is what it used to do, and a scaling
    review measured the cost on a fifty-material corpus: one comment planned fifty syntheses,
    about seventeen hours and seven and a half million output tokens. The theme account exists
    precisely so that a corpus-level correction can be answered at corpus level — twelve short
    runs instead of fifty long ones. A comment that genuinely needs one material re-read belongs
    on that material, where it is one run.
    """
    themes = store.live_themes(conn, fb["project_id"])
    return [_run("account", None, t["id"], fb["id"]) for t in themes
            ] + [_run("project", feedback_id=fb["id"])]


def _frame(conn, fb) -> list[dict]:
    return [_run("frame", fb["target_id"], None, fb["id"])]


# ---- the table ----------------------------------------------------------------------------------
# PLAN.md §1, second table. First matching row wins; "*" matches anything.
#
#   feedback on          its kind    runs
TABLE = [
    ("*",                "check",    _check),            # "check this against the material"
    ("moment",           "doubt",    _check),            # CHECK, not a rerun
    ("moment",           "*",        _nothing),          # agree / note: stored, rides the next DOC
    ("thread",           "agree",    _nothing),          # assent is not an instruction
    ("material_summary", "agree",    _nothing),
    ("theme",            "agree",    _nothing),
    ("project_summary",  "agree",    _nothing),
    ("thread",           "*",        _doc_thread),       # DOC, that material, that theme
    ("material_summary", "*",        _doc_material),     # DOC, that material whole
    ("theme",            "*",        _account),          # that theme's account, rewritten
    ("project_summary",  "*",        _accounts_then_project),
    ("focus",            "*",        _nothing),          # shapes the next READ and every later DOC
    ("frame",            "*",        _frame),            # the only row that re-frames
]


def plan(conn: sqlite3.Connection, feedback_id: str) -> list[dict]:
    """The runs this piece of feedback plans, in the order they must happen."""
    fb = feedback(conn, feedback_id)
    if fb is None:
        raise KeyError(f"no feedback {feedback_id!r}")
    for target_kind, kind, runs in TABLE:
        if target_kind in ("*", fb["target_kind"]) and kind in ("*", fb["kind"]):
            return runs(conn, fb)
    return []


# ---- resolving a target to a material -----------------------------------------------------------

def _material_of(conn: sqlite3.Connection, fb: sqlite3.Row) -> str | None:
    """Which material this feedback is about, or None when it is about the project."""
    tk, target = fb["target_kind"], fb["target_id"]
    if tk == "moment":
        row = store.moment(conn, target)
        return row["material_id"] if row else None
    if tk == "thread":
        return target.partition(":")[0]
    if tk in ("material_summary", "frame"):
        return target
    return None


def _materials_with_theme(conn: sqlite3.Connection, tid: str) -> list[str]:
    return [r["id"] for r in conn.execute(
        "SELECT DISTINCT m.id AS id FROM moment mo JOIN material m ON m.id = mo.material_id "
        "WHERE mo.theme_id=? AND mo.status='live' ORDER BY m.created_at, m.id", (tid,))]
