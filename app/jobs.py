"""Background run chains: a list of planned runs, executed in order, off the request thread.

Threads and a dict. No Celery, no Redis, no queue server — this is a single-user instrument and a
chain is a handful of model calls in sequence.

Two things this module exists to get right.

**The line.** Every step writes a `run` row, and that row carries a sentence a researcher can
read. The old engine's progress chip said `read`, and nothing on the page said what was being done
to which material. The stage name still goes in `kind`, for the code; `line` is for the person.

**Stopping.** An error records itself on its own run row and stops that chain. It does not kill the
process, it does not take the next chain with it, and it leaves the material's state saying so.

**What runs beside what.** A chain is a list of STAGES, not a flat list of steps. What one
material does to itself — framing it, working out what to look for, writing up what stands out —
runs beside what another material is doing to itself; everything that touches what the PROJECT
shares runs on its own. `_stages` says which is which and `PARALLEL` says how many at once.

`app/engine/*` is imported lazily, inside the step, so this module and `rerun.py` import cleanly
while those modules are still being built.
"""
from __future__ import annotations

import contextvars
import json
import logging
import sqlite3
import threading
import time
from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor

from . import db, llm, rerun, store

# What the host's log says a chain did. Ids only — a material's title is usually a person's name.
log = logging.getLogger("aperture")


# ---- the steps ----------------------------------------------------------------------------------

def _text(conn: sqlite3.Connection, run: dict) -> str:
    """The researcher's own words, verbatim, for the steps that take them as an argument."""
    fid = run.get("feedback_id")
    fb = rerun.feedback(conn, fid) if fid else None
    return fb["text"] if fb else ""


def _frame(conn, pid, run):
    """FRAME, and — only for speech that never says who is speaking — one more call to work it out.

    Not a chain entry: whether it is needed depends on what FRAME just found, which nobody knows
    when the chain is planned. It writes its own run row so the page can say what it is doing, and
    it runs again after a re-frame under exactly the same condition.
    """
    from .engine import diarize, frame
    mid = run["material_id"]
    out = frame.run(conn, mid, hint=_text(conn, run)) or {}
    notes = list(out.get("dropped") or [])
    if not diarize.needed(out):
        return notes
    spent = dict(llm.usage)                 # the framing call's, which the row above still wants
    rid = store.start_run(conn, pid, "diarize", mid,
                          line(conn, {"kind": "diarize", "material_id": mid}))
    llm.usage.update(tokens_in=0, tokens_out=0)
    try:
        said = (diarize.run(conn, mid) or {}).get("dropped") or []
    except Exception as e:                  # its own row carries the reason; the chain stops
        store.finish_run(conn, rid, error=f"{type(e).__name__}: {e}")
        raise
    store.finish_run(conn, rid, tokens_in=llm.usage.get("tokens_in", 0),
                     tokens_out=llm.usage.get("tokens_out", 0), notes=said)
    llm.usage.update(**spent)
    return notes + said


def _diarize(conn, pid, run):
    from .engine import diarize
    return (diarize.run(conn, run["material_id"]) or {}).get("dropped")


def _angles(conn, pid, run):
    from .engine import angles
    angles.run(conn, run["material_id"], feedback=_text(conn, run))


def _read(conn, pid, run):
    from .engine import read
    read.run(conn, run["material_id"], feedback=_text(conn, run))


def _reconcile(conn, pid, run):
    """Only where the project explores: the reading was shown no codebook, so what it named is
    compared with the project's vocabulary here rather than during the reading."""
    from .engine import reconcile
    return (reconcile.run(conn, run["material_id"]) or {}).get("dropped")


def _theme_set(conn, pid) -> list[tuple]:
    return [(t["id"], t["name"], t["gist"]) for t in store.live_themes(conn, pid)]


def _themes(conn, pid, run):
    """THEMES, and whether it moved the set — created, merged, renamed or redefined a theme.

    `out_of_date` measures every material against it, and most passes over new material leave the
    set exactly as it stands. Unrecorded, each of those marked every other material as analysed
    before the themes last changed, which was not true and cost a call each to answer.
    """
    from .engine import themes
    before = _theme_set(conn, pid)
    themes.run(conn, pid, feedback=_text(conn, run), material_id=run.get("material_id"),
               run_id=run.get("run_id"))
    if _theme_set(conn, pid) == before and run.get("run_id"):
        store.mark_unchanged(conn, run["run_id"])


def _doc(conn, pid, run):
    from .engine import synth
    out = synth.doc(conn, run["material_id"], only_theme=run.get("theme_id"),
                    run_id=run.get("run_id"))
    return (out or {}).get("dropped")


def _summary(conn, pid, run):
    """The material's summary over its lines as they stand: what a comment on one line, or on the
    summary itself, actually asks for. No line is rewritten here."""
    from .engine import synth
    out = synth.doc(conn, run["material_id"], summary_only=True, run_id=run.get("run_id"))
    return (out or {}).get("dropped")


def _accounts(conn, pid, run):
    """Every live theme's account, expanded when this step runs rather than when it was planned —
    the theme set is only known after THEMES has been over the new material.

    A theme whose definition and whose live claims are exactly what the stored account was written
    from is left alone. Every chain ends here — every upload, every removal, every retry — and an
    upload that touched one theme was paying for twelve accounts, eleven of which would have come
    back word for word. `_account`, which the researcher asks for by hand, always runs.
    """
    from .engine import account
    themes = store.live_themes(conn, pid)
    wrote = 0
    for i, t in enumerate(themes, 1):
        stored = store.get_summary(conn, "theme", t["id"], "reading")
        # An open comment on the theme is an input the fingerprint cannot see: it is what the
        # researcher said, not what the project holds. Skipped on the strength of unmoved
        # evidence, a theme with one waiting would never be written again and the comment would
        # never be answered.
        if (stored and stored["fingerprint"] == account.fingerprint(conn, pid, t["id"])
                and not store.feedback_for(conn, "theme", t["id"], open_only=True)):
            continue
        wrote += 1
        llm.report(f"theme {i} of {len(themes)}: {t['name']}")
        account.run(conn, pid, t["id"], run_id=run.get("run_id"))
    if run.get("run_id"):
        store.set_run_line(conn, run["run_id"], accounts_line(wrote, len(themes)))


def accounts_line(wrote: int, total: int) -> str:
    """What the accounts step leaves on its row: what it wrote, and what it did not have to."""
    said = f"Wrote {wrote} of {total} theme accounts"
    return said + (f" — {total - wrote} unchanged" if wrote < total else "")


def _account(conn, pid, run):
    from .engine import account
    account.run(conn, pid, run["theme_id"], run_id=run.get("run_id"))


def _project(conn, pid, run):
    from .engine import synth
    return (synth.project(conn, pid, run_id=run.get("run_id")) or {}).get("dropped")


def _check(conn, pid, run):
    from .engine import check
    mid = run.get("material_id")
    # `scope` is which passages the researcher asked for — it rides on the planned run rather than
    # on the feedback row, because it is a setting on the search and not a word they wrote.
    check.run(conn, pid, "material" if mid else "project", mid or pid, _text(conn, run),
              run.get("scope") or "all")


#                 line a person can read              what it calls
STEPS: dict[str, tuple[str, Callable]] = {
    "frame":   ("Working out how this is laid out",   _frame),
    "diarize": ("Working out who is speaking in {name}", _diarize),
    "angles":  ("Working out what to look for in {name}", _angles),
    "read":    ("Reading {name}",                     _read),
    "reconcile": ("Comparing {name}'s codes with the project's", _reconcile),
    "themes":  ("Finding themes",                     _themes),
    "doc":     ("Writing what stands out in {name}", _doc),
    "summary": ("Writing the summary of {name} again", _summary),
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


LEFT_TO_THE_LAST = "Left for the chain that follows — more material is still to be read."


def _another_chain(conn: sqlite3.Connection, pid: str, job: str | None, kind: str) -> bool:
    """Whether the corpus level should be left to a later chain.

    Two uploads a minute apart are two chains, and each one ends in the accounts and the corpus
    summary. Written by the first, they are written over material the second has not read yet —
    and the page says "Updating the project summary" twice for one answer. The last chain in the
    queue writes them once.

    Only a chain that will itself write the corpus level counts. Any waiting job used to, so a
    question typed into the check box while an upload was reading left that upload with no theme
    accounts and no corpus summary, and nothing behind it to write them.
    """
    if kind not in ("accounts", "project"):
        return False
    return any(r["kind"] in ("accounts", "project") for row in conn.execute(
        "SELECT runs_json FROM job WHERE project_id=? AND status IN ('queued','running') "
        "AND id<>?", (pid, job or "")) for r in json.loads(row["runs_json"]))


# How many materials a chain works on at once. Four: the provider rate-limits, so more calls in
# flight than that is more 429s, not more throughput.
PARALLEL = 4

# The kinds a material may run while another material is running them, in the groups they may
# form. Each of these is shown only its own material and writes only its own material's rows.
#
# THEMES is absent by law: it revises one set shared by the whole project, so it runs strictly one
# material at a time, and every material is read before any of them moves the set.
SIDE_BY_SIDE = ({"frame", "angles", "read", "reconcile"}, {"doc"})

# ...and inside such a stage, these still take their turn, in the order the chain planned them.
# READ is SHOWN the project codebook and `store.save_codes` reuses a code by name: two readings at
# once would each be shown a codebook without the other's codes, and would coin two rows for one
# name. So the framing and the ideation of the next material overlap a reading, and the readings
# themselves queue behind each other exactly as they always have. RECONCILE writes the codebook
# too — it merges rows away — so it takes the same turn.
IN_TURN = {"read", "reconcile"}


def _stages(runs: list[dict]) -> list[list[list[dict]]]:
    """The planned chain, grouped into stages. A stage is a list of sequences that run side by
    side; a sequence is one material's runs in the order they were planned. Anything that is not a
    block of per-material steps over more than one material becomes a stage of one sequence of one
    run — which is what every step of this chain used to be.

    Grouping, not planning: `ingest_chain` still decides what runs and in what order, and this
    only says which of those may happen at the same time.
    """
    stages: list[list[list[dict]]] = []
    i = 0
    while i < len(runs):
        kinds = next((g for g in SIDE_BY_SIDE if runs[i]["kind"] in g), set())
        by_material: dict[str, list[dict]] = {}
        j = i
        while j < len(runs) and runs[j]["kind"] in kinds and runs[j].get("material_id"):
            by_material.setdefault(runs[j]["material_id"], []).append(runs[j])
            j += 1
        if len(by_material) > 1:
            stages.append(list(by_material.values()))
            i = j
        else:
            stages.append([[runs[i]]])
            i += 1
    return stages


def _step(conn: sqlite3.Connection, pid: str, run: dict, *, job: str | None,
          last_feedback: dict) -> tuple[str, str]:
    """One planned step: its own run row, its own token counter, its own progress line, its own
    error. Returns (run id, error)."""
    kind, mid = run["kind"], run.get("material_id")
    base = line(conn, run)
    rid = store.start_run(conn, pid, kind, mid, base, job)
    run["run_id"] = rid
    log.info("step kind=%s project=%s material=%s started", kind, pid, mid or "-")
    t0 = time.monotonic()
    if mid:
        store.set_state(conn, mid, kind)
    # This step's tokens, in this thread's context and no other (see llm.new_usage).
    llm.new_usage()
    error, notes = None, None
    try:
        # Where the step has got to, on the row the page is already reading. Only for the length
        # of the step: nothing outside one has a row to write on.
        with llm.reporting(lambda msg: store.set_run_line(conn, rid, f"{base} — {msg}")):
            # On the line, not in the notes: the notes are what a reading threw away, and the
            # page prints them under "Excluded from the analysis", where this read as a claim
            # that had been dropped.
            if _another_chain(conn, pid, job, kind):
                store.set_run_line(conn, rid, LEFT_TO_THE_LAST)
            else:
                notes = STEPS[kind][1](conn, pid, run)
    except Exception as e:                              # the sequence stops; the process does not
        error = f"{type(e).__name__}: {e}"
    store.finish_run(conn, rid, error=error, tokens_in=llm.usage.get("tokens_in", 0),
                     tokens_out=llm.usage.get("tokens_out", 0),
                     notes=[str(n) for n in (notes or [])])
    if error:
        # Eighty characters, not the whole reason: the one message here that runs longer quotes
        # the model's answer back (`no JSON object in model output: ...`), and the material is
        # nobody's business but its owner's — who reads the reason in full on the run row.
        log.error("step kind=%s project=%s material=%s failed: %.80s", kind, pid, mid or "-",
                  error)
    else:
        log.info("step kind=%s project=%s material=%s finished s=%.1f in=%d out=%d", kind, pid,
                 mid or "-", time.monotonic() - t0, llm.usage.get("tokens_in", 0),
                 llm.usage.get("tokens_out", 0))
    # Honoured by the LAST run that was shown it, not the first. One note can ride a whole
    # chain — and consumed at the first step, it would be gone from the open comments the
    # synthesis at the end of that same chain is written from.
    if not error and run.get("feedback_id") and last_feedback.get(run["feedback_id"]) == id(run):
        fb = rerun.feedback(conn, run["feedback_id"])
        # A comment on a theme is honoured by `account.run` itself, at the moment it stores an
        # account written with those words in front of the model. Honoured here instead, it was
        # closed by the last step of the plan whether or not anything had read it — a theme left
        # as it stood, or an account that came back empty, still marked the instruction answered.
        if fb is None or fb["target_kind"] != "theme":
            store.consume_feedback(conn, run["feedback_id"], rid)
    if not error and kind in ("doc", "summary") and mid:
        # A rewrite answers every comment it was shown, not only the one that planned it.
        store.consume_material_feedback(conn, pid, mid, rid, run.get("theme_id"))
    return rid, error or ""


def _sequence(conn: sqlite3.Connection, pid: str, seq: list[dict], job: str | None,
              last_feedback: dict, turn: tuple = (None, None)) -> tuple:
    """One material's steps, in order, on this connection. Returns (run ids, materials touched,
    the material it failed on, why). A failure stops THIS sequence and no other."""
    before, after = turn
    # One material's turn at the shared codebook covers every step that writes it, not each of
    # them separately: the reading and the comparison that follows it are one turn, and the next
    # material waits for both. Set after each of them, the turn would end at the reading and let
    # the next material read while this one was still merging codes away underneath it.
    turning = [r for r in seq if r["kind"] in IN_TURN]
    ids, touched, failed, error = [], [], None, ""
    for run in seq:
        if job and store.job(conn, job)["status"] != "running":
            break                                   # stopped by the researcher between steps
        if before is not None and turning and run is turning[0]:
            before.wait()
        rid, error = _step(conn, pid, run, job=job, last_feedback=last_feedback)
        if after is not None and turning and run is turning[-1]:
            after.set()
        ids.append(rid)
        if run.get("material_id"):
            touched.append(run["material_id"])
        if error:
            failed = run.get("material_id")
            break
    return ids, touched, failed, error


def _together(pid: str, stage: list[list[dict]], job: str | None, last_feedback: dict) -> list:
    """Every material in this stage at once: one thread each, capped at PARALLEL.

    Each thread opens its OWN connection — one sqlite connection must not be shared across
    threads — and runs in its own copy of this context, so `llm.usage` and `llm.report` are the
    thread's own and one material's tokens cannot land on another material's row.
    """
    done = [threading.Event() for _ in stage]

    def one(k: int, seq: list[dict]):
        conn = db.connect()
        try:
            return _sequence(conn, pid, seq, job, last_feedback,
                             turn=(done[k - 1] if k else None, done[k]))
        finally:
            done[k].set()          # a material that failed must not leave the next one waiting
            conn.close()

    with ThreadPoolExecutor(max_workers=min(PARALLEL, len(stage))) as pool:
        futures = [pool.submit(contextvars.copy_context().run, one, k, seq)
                   for k, seq in enumerate(stage)]
        return [f.result() for f in futures]


def run_now(conn: sqlite3.Connection, pid: str, runs: Iterable[dict], *,
            job: str | None = None) -> list[str]:
    """Run a chain to completion on this connection and return the run ids. `start` is this, in a
    thread; call it directly when you want the chain to have landed before you look.

    The chain is a list of stages: what one material does to itself runs beside what another
    material is doing to itself, and everything that touches what the project shares — THEMES, the
    accounts, the corpus summary — runs on its own, as it always did.
    """
    runs = _known(list(runs))
    # Which planned run is the last that carries each note. Decided here because the runs no
    # longer finish in one order, and the rule is unchanged: the last run that was shown a note
    # consumes it.
    last_feedback = {r["feedback_id"]: id(r) for r in runs if r.get("feedback_id")}
    ids, touched, failed, reason = [], [], [], ""
    for stage in _stages(runs):
        if job and store.job(conn, job)["status"] != "running":
            break
        results = (_together(pid, stage, job, last_feedback) if len(stage) > 1
                   else [_sequence(conn, pid, stage[0], job, last_feedback)])
        for seq_ids, seq_touched, seq_failed, seq_error in results:
            ids += seq_ids
            touched += seq_touched
            if seq_error:
                failed.append(seq_failed)
                reason = reason or seq_error
        if reason:
            # One material's failure does not stop the others in its stage, and it does stop the
            # chain: THEMES over a half-read corpus is worse than a chain the researcher can start
            # again. The step that will not run carries the reason, so the page says why it
            # stopped rather than simply ending.
            if len(stage) > 1 and (nxt := next((r for r in runs if "run_id" not in r), None)):
                rid = store.start_run(conn, pid, nxt["kind"], nxt.get("material_id"),
                                      line(conn, nxt), job)
                ids.append(rid)
                names = ", ".join(_name(conn, m) for m in dict.fromkeys(failed) if m)
                store.finish_run(conn, rid, error=f"not run — {names or 'an earlier step'} did "
                                                  f"not finish: {reason}")
            break
    for mid in dict.fromkeys(touched):                  # in order, without repeats
        store.set_state(conn, mid, "failed" if mid in failed else "ready")
    return ids


_JOBS: dict[str, threading.Thread] = {}
_RUNNER_LOCK = threading.Lock()


def _launch(job: str, pid: str, conn_factory: Callable[[], sqlite3.Connection]) -> None:
    def work() -> None:
        conn = conn_factory()
        error, t0 = "", 0.0
        try:
            row = store.job(conn, job)
            if row is None or row["status"] != "queued":
                return                              # already run, or stopped before it began
            runs = _known(json.loads(row["runs_json"]))
            store.start_job(conn, job)
            t0 = time.monotonic()
            log.info("job id=%s project=%s started steps=%d", job, pid, len(runs))
            # One chain at a time in this process. The parallelism is INSIDE a chain (see
            # `_stages`); two chains at once would be two projects' worth of calls in flight
            # against a provider that rate-limits, and two writers on shared theme rows.
            with _RUNNER_LOCK:
                ids = run_now(conn, pid, runs, job=job)
            if ids:
                failed = conn.execute("SELECT error FROM run WHERE id=?", (ids[-1],)).fetchone()
                error = (failed["error"] if failed else "") or ""
        except Exception as exc:  # a broken queue item is recorded; the worker stays alive
            error = f"{type(exc).__name__}: {exc}"
        finally:
            try:
                if t0:                              # a job that never started says nothing
                    state = store.job(conn, job)
                    said = "failed" if error else (
                        "stopped" if state and state["status"] == "stopped" else "finished")
                    (log.error if error else log.info)("job id=%s project=%s %s s=%.1f",
                                                       job, pid, said, time.monotonic() - t0)
                store.finish_job(conn, job, error)
            finally:
                conn.close()

    t = threading.Thread(target=work, name=job, daemon=True)
    _JOBS[job] = t
    t.start()


def start(conn_factory: Callable[[], sqlite3.Connection], pid: str,
          runs: Iterable[dict]) -> str:
    """Persist these steps, run them off-request, and return the job id.

    The row is committed before the thread starts, so leaving the page has no bearing on the work.
    `resume_pending` picks it up after a process restart. Chains for one project are serialised
    because their codebook, themes and summaries are shared state.
    """
    runs = _known(list(runs))
    conn = conn_factory()
    try:
        job = store.enqueue_job(conn, pid, runs)
    finally:
        conn.close()
    _launch(job, pid, conn_factory)
    return job


def resume_pending(conn_factory: Callable[[], sqlite3.Connection] = db.connect) -> list[str]:
    """Resume work committed before this process started (or stopped unexpectedly)."""
    conn = conn_factory()
    try:
        store.close_orphaned_runs(conn)          # before relaunching: the new attempt writes its own
        rows = [dict(r) for r in store.pending_jobs(conn)]
        for row in rows:
            alive = _JOBS.get(row["id"])
            if row["status"] == "running" and not (alive is not None and alive.is_alive()):
                store.requeue_job(conn, row["id"])   # queued again, minus the steps already done
    finally:
        conn.close()
    launched = []
    for row in rows:
        current = _JOBS.get(row["id"])
        if current is not None and current.is_alive():
            continue
        _launch(row["id"], row["project_id"], conn_factory)
        launched.append(row["id"])
    return launched


def wait(job: str, timeout: float = 60.0) -> bool:
    """True once that chain has finished. For tests, and for a caller that must not race it."""
    t = _JOBS.get(job)
    if t is not None:
        t.join(timeout)
        return not t.is_alive()
    return True


# ---- the chain material arrives on --------------------------------------------------------------

def ingest_chain(pid: str, mids: Iterable[str], conn_factory: Callable = db.connect) -> str:
    """Up: FRAME → ANGLES → READ for each material, then THEMES and DOC for each, then the tail.

    Where the project explores, RECONCILE follows each reading: that reading was shown no
    codebook, so what it named is compared with the project's vocabulary in a step of its own,
    before THEMES gathers any of it. Where the project is built iteratively the chain is exactly
    what it has always been.

    One upload is one chain, whatever it carried. Five files used to start five chains, and each
    of them found themes again and rewrote the corpus summary with four of the five still unread.

    The runner stages this (see `_stages`): the per-material steps run side by side, THEMES one
    material at a time, then each material's synthesis side by side again, then the tail.

    ponytail: a step that fails stops its own material and then the chain — the other files in
    the stage finish, but nothing after it runs, so a file later in the same upload can be left
    queued and unread. Give the researcher a way to run the rest if a failure mid-upload turns
    out to be common.

    Ingest itself is Python and already done by the time this is called — text became sentences
    when the material was added, synchronously, because ids are the spine everything else cites.
    This is the model half.
    """
    mids = list(mids)
    conn = conn_factory()
    try:
        proj = store.project(conn, pid)
    finally:
        conn.close()
    # A project this cannot read has no method to honour, and the chain that has always run is the
    # one to plan for it.
    per_material = (("frame", "angles", "read", "reconcile")
                    if proj is not None and proj["method"] == "explore"
                    else ("frame", "angles", "read"))
    return start(conn_factory, pid, [
        *({"kind": k, "material_id": mid} for mid in mids
          for k in per_material),
        # THEMES takes one material because it must see that material's codes by passage; every
        # piece is read before any of them moves the theme set, so DOC writes against the set as
        # it finally stands.
        *({"kind": "themes", "material_id": mid} for mid in mids),
        *({"kind": "doc", "material_id": mid} for mid in mids),
        # Accounts are planned when the chain reaches them, not now: THEMES has not run yet, so
        # the live theme set at this moment is the old one.
        {"kind": "accounts"},
        {"kind": "project"},
    ])


def resynthesis_chain(pid: str, conn_factory: Callable = db.connect) -> str:
    """Write the corpus level again over the reading as it stands: every account, then the summary.

    What material leaves behind, and what a failed chain leaves behind, are the same job. Nothing
    below the corpus level is redone: `store.remove_material` has already dropped the orphaned
    codes and retired the themes left without any, and what stayed was read on its own terms, not
    against what went — so no material's synthesis is now wrong. Where the themes did move under
    one, `store.out_of_date` says so on its row and the researcher decides whether rereading it is
    worth the money; this used to spend a call on every remaining material to answer that for them.
    """
    return start(conn_factory, pid, [{"kind": "accounts"}, {"kind": "project"}])
