"""Background run chains: a list of planned runs, executed in order, off the request thread.

Threads and a dict. No Celery, no Redis, no queue server — this is a single-user instrument and a
chain is a handful of model calls in sequence.

Two things this module exists to get right.

**The line.** Every step writes a `run` row, and that row carries a sentence a researcher can
read. The old engine's progress chip said `read`, and nothing on the page said what was being done
to which material. The stage name still goes in `kind`, for the code; `line` is for the person.

**Stopping.** An error records itself on its own run row and stops that chain. It does not kill the
process, it does not take the next chain with it, and it leaves the material's state saying so.

`app/engine/*` is imported lazily, inside the step, so this module and `rerun.py` import cleanly
while those modules are still being built.
"""
from __future__ import annotations

import sqlite3
import threading
from collections.abc import Callable, Iterable

from . import db, llm, rerun, store


# ---- the steps ----------------------------------------------------------------------------------

def _text(conn: sqlite3.Connection, run: dict) -> str:
    """The researcher's own words, verbatim, for the steps that take them as an argument."""
    fid = run.get("feedback_id")
    fb = rerun.feedback(conn, fid) if fid else None
    return fb["text"] if fb else ""


def _frame(conn, pid, run):
    from .engine import frame
    return (frame.run(conn, run["material_id"], hint=_text(conn, run)) or {}).get("dropped")


def _angles(conn, pid, run):
    from .engine import angles
    angles.run(conn, run["material_id"])


def _read(conn, pid, run):
    from .engine import read
    read.run(conn, run["material_id"])


def _themes(conn, pid, run):
    from .engine import themes
    themes.run(conn, pid, feedback=_text(conn, run), material_id=run.get("material_id"),
               run_id=run.get("run_id"))


def _doc(conn, pid, run):
    from .engine import synth
    out = synth.doc(conn, run["material_id"], only_theme=run.get("theme_id"))
    return (out or {}).get("dropped")


def _accounts(conn, pid, run):
    """Every live theme's account, expanded when this step runs rather than when it was planned —
    the theme set is only known after THEMES has been over the new material."""
    from .engine import account
    for t in store.live_themes(conn, pid):
        account.run(conn, pid, t["id"], run_id=run.get("run_id"))


def _account(conn, pid, run):
    from .engine import account
    account.run(conn, pid, run["theme_id"], run_id=run.get("run_id"))


def _project(conn, pid, run):
    from .engine import synth
    return (synth.project(conn, pid) or {}).get("dropped")


def _check(conn, pid, run):
    from .engine import check
    mid = run.get("material_id")
    check.run(conn, pid, "material" if mid else "project", mid or pid, _text(conn, run))


#                 line a person can read              what it calls
STEPS: dict[str, tuple[str, Callable]] = {
    "frame":   ("Working out how this is laid out",   _frame),
    "angles":  ("Working out what to look for in {name}", _angles),
    "read":    ("Reading {name}",                     _read),
    "themes":  ("Finding themes",                     _themes),
    "doc":     ("Writing what stands out in {name}", _doc),
    "account":  ("Writing where a theme runs across everything", _account),
    "accounts": ("Writing where each theme runs across everything", _accounts),
    "project": ("Updating the project summary",       _project),
    "check":   ("Checking that against the material", _check),
}


def _name(conn: sqlite3.Connection, mid: str | None) -> str:
    row = store.material(conn, mid) if mid else None
    if row is None:
        return "the material"
    return row["title"] or row["name"]


def line(conn: sqlite3.Connection, run: dict) -> str:
    """What the page says while this step runs."""
    kind, mid = run["kind"], run.get("material_id")
    if kind == "doc" and run.get("theme_id"):
        theme = conn.execute("SELECT name FROM theme WHERE id=?",
                             (run["theme_id"],)).fetchone()
        if theme:
            return (f"Writing what stands out in {_name(conn, mid)} "
                    f"on {theme['name']}")
    return STEPS[kind][0].format(name=_name(conn, mid))


# ---- running them -------------------------------------------------------------------------------

def _known(runs: list[dict]) -> list[dict]:
    unknown = sorted({r["kind"] for r in runs} - set(STEPS))
    if unknown:
        raise ValueError(f"no such run kind: {unknown}; expected one of {sorted(STEPS)}")
    return runs


def run_now(conn: sqlite3.Connection, pid: str, runs: Iterable[dict]) -> list[str]:
    """Run a chain to completion on this connection and return the run ids. `start` is this, in a
    thread; call it directly when you want the chain to have landed before you look."""
    runs = _known(list(runs))
    ids, touched, failed = [], [], None
    for run in runs:
        kind, mid = run["kind"], run.get("material_id")
        rid = store.start_run(conn, pid, kind, mid, line(conn, run))
        ids.append(rid)
        if mid:
            touched.append(mid)
            store.set_state(conn, mid, kind)
        # ponytail: llm.usage is one module-level dict, so two chains at once would share a
        # counter. One chain at a time is the whole of this instrument; give the run its own
        # counter if chains ever overlap.
        llm.usage.update(tokens_in=0, tokens_out=0)
        error, notes = None, None
        try:
            notes = STEPS[kind][1](conn, pid, run)
        except Exception as e:                          # the chain stops; the process does not
            error = f"{type(e).__name__}: {e}"
            failed = mid
        store.finish_run(conn, rid, error=error, tokens_in=llm.usage.get("tokens_in", 0),
                         tokens_out=llm.usage.get("tokens_out", 0),
                         notes=[str(n) for n in (notes or [])])
        if not error and run.get("feedback_id"):
            store.consume_feedback(conn, run["feedback_id"], rid)
        if error:
            break
    for mid in dict.fromkeys(touched):                  # in order, without repeats
        store.set_state(conn, mid, "failed" if mid == failed else "ready")
    return ids


_JOBS: dict[str, threading.Thread] = {}


def start(conn_factory: Callable[[], sqlite3.Connection], pid: str,
          runs: Iterable[dict]) -> str:
    """Run these in order, in the background, and return the job id.

    `conn_factory` is called *inside* the worker. `db.connect` passes check_same_thread=False, but
    that only silences the guard — one connection object still must not be worked from two threads.
    """
    runs = _known(list(runs))
    job = db.new_id("j")

    def work() -> None:
        conn = conn_factory()
        try:
            run_now(conn, pid, runs)
        finally:
            conn.close()

    t = threading.Thread(target=work, name=job, daemon=True)
    _JOBS[job] = t
    t.start()
    return job


def wait(job: str, timeout: float = 60.0) -> bool:
    """True once that chain has finished. For tests, and for a caller that must not race it."""
    t = _JOBS.get(job)
    if t is not None:
        t.join(timeout)
        return not t.is_alive()
    return True


# ---- the chain material arrives on --------------------------------------------------------------

def ingest_chain(pid: str, mid: str, conn_factory: Callable = db.connect) -> str:
    """Up: ingest → FRAME → READ → THEMES → DOC → PROJECT.

    Ingest itself is Python and already done by the time this is called — text became sentences
    when the material was added, synchronously, because ids are the spine everything else cites.
    This is the model half.
    """
    return start(conn_factory, pid, [
        {"kind": "frame", "material_id": mid},
        {"kind": "angles", "material_id": mid},
        {"kind": "read", "material_id": mid},
        {"kind": "themes", "material_id": mid},
        {"kind": "doc", "material_id": mid},
        # Accounts are planned when the chain reaches them, not now: THEMES has not run yet, so
        # the live theme set at this moment is the old one.
        {"kind": "accounts"},
        {"kind": "project"},
    ])
