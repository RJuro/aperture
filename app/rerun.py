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

The researcher's own re-run verb is the exception and is `from_step` below: they say what to
do again and from where, so it may re-read and re-frame. Nothing in the feedback table can.

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


# ---- running one material again, because the researcher asked ------------------------------------
# Not feedback. Feedback runs one layer down and never re-reads (above); this is the researcher
# saying "do that again", from wherever they choose, and re-reading is the whole point of it. The
# order is the order material arrives in (`jobs.ingest_chain`), so "from the beginning" and "a
# fresh upload" do the same work in the same sequence.
CHAIN = ("frame", "angles", "read", "themes", "doc")

# What the page calls each of them. Three of our five names are ours, not the researcher's, and
# two of those the app may not print at all (PLAN.md §7) — even in a form value — so the form
# sends the words the page already uses on its receipt and this maps them back.
PAGE_NAMES = {"structure": "frame", "coding": "read", "synthesis": "doc"}


def from_step(mid: str, step: str, feedback_id: str | None = None, *,
              explore: bool = False) -> list[dict]:
    """Everything that happens to one material from `step` onward, then the corpus level.

    A note rides on every run rather than only the first, so each step that takes the
    researcher's words verbatim is handed them, and the synthesis at the end still counts the
    note among the material's open comments. A project that explores compares a reading's codes
    with the project's before the themes are revised, so its chain carries `reconcile` after
    `read` here as it does on upload.
    """
    if step not in CHAIN:
        raise KeyError(f"no such step {step!r}; expected one of {list(CHAIN)}")
    chain = list(CHAIN[CHAIN.index(step):])
    if explore and "read" in chain:
        chain.insert(chain.index("read") + 1, "reconcile")
    return [_run(k, mid, feedback_id=feedback_id) for k in chain] + [
        _run("accounts", feedback_id=feedback_id), _run("project", feedback_id=feedback_id)]


# ---- what a row of the table does ---------------------------------------------------------------

def _nothing(conn, fb) -> list[dict]:
    return []


def _check(conn, fb) -> list[dict]:
    return [_run("check", _material_of(conn, fb), feedback_id=fb["id"])]


def _doc_thread(conn, fb) -> list[dict]:
    """A thread's target id is "<material_id>:<theme_id>" — that material, that theme only, and
    then everything written over the claims that line has just replaced: the material's summary
    (over its lines as they now stand, no other line rewritten), the accounts, the corpus summary.

    The scoped run stays first and stays scoped: it is the only run that cannot pass this theme
    over, whatever the codes say, and the researcher asked about this line."""
    mid, tid = fb["target_id"].split(":", 1)
    return [_run("doc", mid, tid, fb["id"]), _run("summary", mid, feedback_id=fb["id"]),
            _run("accounts", feedback_id=fb["id"]), _run("project", feedback_id=fb["id"])]


def _doc_material(conn, fb) -> list[dict]:
    """A comment on a material's summary rewrites the summary over the lines that stand, then what
    is written over it. It does not re-read every line: the researcher who wants that has "run
    again from synthesis" and its note."""
    return [_run("summary", fb["target_id"], feedback_id=fb["id"]),
            _run("accounts", feedback_id=fb["id"]), _run("project", feedback_id=fb["id"])]


def _account(conn, fb) -> list[dict]:
    """One theme, rewritten across the corpus, and the corpus summary over it. Regrouping the
    whole codebook and re-reading every material that carries the theme — which is what this used
    to plan — answers a comment about one theme with work on all of them.

    PROJECT is not optional here: it is written from the accounts, so a theme the researcher has
    just corrected is quoted in the summary above it in the words it had before the correction.
    """
    return [_run("account", None, fb["target_id"], fb["id"]),
            _run("project", feedback_id=fb["id"])]


def _project_summary(conn, fb) -> list[dict]:
    """A comment on the corpus is answered at the corpus, and nowhere else.

    It deliberately does NOT re-read every material. That is what it used to do, and a scaling
    review measured the cost on a fifty-material corpus: one comment planned fifty syntheses,
    about seventeen hours and seven and a half million output tokens. It then rewrote every
    theme's account instead, which is the same mistake one layer up: the correction went into
    PROJECT's prompt alone, so twelve accounts were paid for and rewritten from evidence that had
    not moved, none of them ever shown the words that planned them. A comment that is really
    about one theme belongs on that theme, where it is one account and one summary.
    """
    return [_run("project", feedback_id=fb["id"])]


def _frame(conn, fb) -> list[dict]:
    return [_run("frame", fb["target_id"], None, fb["id"])]


# ---- the table ----------------------------------------------------------------------------------
# PLAN.md §1, second table. First matching row wins; "*" matches anything.
#
#   feedback on          its kind    runs
TABLE = [
    ("*",                "check",    _check),            # "check this against the material"
    # A comment on a claim: stored, shown, exported, and read by the next rewrite of this
    # material, which consumes it. Doubt about a claim is the check verb, one row up — the page
    # offers one free-text comment per block and nothing that sends a `doubt`.
    ("moment",           "*",        _nothing),
    ("thread",           "agree",    _nothing),          # assent is not an instruction
    ("material_summary", "agree",    _nothing),
    ("theme",            "agree",    _nothing),
    ("project_summary",  "agree",    _nothing),
    ("thread",           "*",        _doc_thread),       # DOC, that material, that theme
    ("material_summary", "*",        _doc_material),     # DOC, that material whole
    ("theme",            "*",        _account),          # that theme's account, rewritten
    ("project_summary",  "*",        _project_summary),
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
