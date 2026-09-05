"""The four things a researcher does: add material, react, check, set a focus. Plus re-framing.

Every one is a POST that writes a row, works out what that row makes run, starts it in the
background, and redirects. Redirect-after-post, so a refresh never repeats an expensive run.

Which target a reaction is about is read from **which fields the form sent**, not from a hidden
`target_kind` string. That is P5's doing and it is right: a hidden input saying `value="moment"`
would put our own vocabulary on the page, where it is banned. The field names carry the meaning.

Nothing here decides what re-runs. `rerun.plan` owns that, from one table, and this module only
hands it a feedback id — so the rule that feedback never re-reads lives in one place and is
tested in one place.
"""
from __future__ import annotations

from urllib.parse import quote_plus

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import RedirectResponse

from . import db, ingest, intake, jobs, rerun, store
from .pages import _mine as pages_mine, connection

router = APIRouter()


def _back(request: Request, fallback: str) -> RedirectResponse:
    """Back where they were, so a reaction leaves them looking at the same thing they reacted to.
    303 because this was a POST and the browser must follow it with a GET."""
    return RedirectResponse(request.headers.get("referer") or fallback, status_code=303)


def _mine(request: Request, conn, pid: str) -> None:
    """Every verb here changes the project, so it takes owning it or being invited to edit it.

    The same function the pages use, one notch higher: there is one answer in this app to who may
    reach a project, and this asks it for a change rather than a look. A member invited to read
    gets the 404 a stranger gets — the project is, for the purpose of changing it, not there.
    """
    pages_mine(request, conn, pid, need="edit")


def _go(conn, pid: str, feedback_id: str) -> None:
    """Whatever this piece of feedback makes run, run it in the background."""
    if runs := rerun.plan(conn, feedback_id):
        jobs.start(db.connect, pid, runs)


def _target(claim_id: str, theme_id: str, material_id: str, pid: str) -> tuple[str, str]:
    """Which thing a reaction is about, from the fields the form sent."""
    if claim_id:
        return "moment", claim_id
    if theme_id and material_id:
        return "thread", f"{material_id}:{theme_id}"
    if theme_id:
        return "theme", theme_id
    if material_id:
        return "material_summary", material_id
    return "project_summary", pid


@router.post("/p/new")
def new_project(request: Request, name: str = Form(...), focus: str = Form("")):
    conn = connection()
    user = getattr(request.state, "user", None)
    pid = store.create_project(conn, name.strip() or "Untitled", focus.strip(),
                               owner_id=user["id"] if user else None)
    return RedirectResponse(f"/p/{pid}", status_code=303)


@router.post("/p/{pid}/material")
def add_material(request: Request, pid: str, files: list[UploadFile] = File(default=[]),
                 name: str = Form(""), text: str = Form("")):
    """Files and/or pasted text in, sentences out, and one reading over all of them.

    Extraction is synchronous and so is the sentence cut: ids are the spine every code and claim
    cites, so they exist before anything can cite them, and the chain that follows is the only
    part slow enough to be worth backgrounding.

    A file that cannot be read stops the whole submission. Half an upload landing is worse than
    none of it — the researcher dropped in a folder and has no way of knowing which four of five
    files became material.
    """
    conn = connection()
    _mine(request, conn, pid)
    pieces = []
    try:
        for f in files:
            if f.filename:
                pieces.append((f.filename, intake.extract(f.filename, f.file.read())))
    except intake.IntakeError as e:
        return RedirectResponse(f"/p/{pid}?problem={quote_plus(str(e))}", status_code=303)
    if text.strip():
        pieces.append((name.strip() or "Untitled", text))
    mids, again = [], []
    for piece_name, body in pieces:
        if store.has_text(conn, pid, body):
            again.append(piece_name)
            continue
        mid = store.add_material(conn, pid, piece_name, body)
        store.save_sentences(conn, mid, ingest.sentences(body))
        mids.append(mid)
    said = (f"{', '.join(again)} {'is' if len(again) == 1 else 'are'} already in this project."
            if again else "")
    where = f"?problem={quote_plus(said)}" if said else ""
    if not mids:
        return RedirectResponse(f"/p/{pid}{where}", status_code=303)
    jobs.ingest_chain(pid, mids)
    # One piece and nothing to report: straight to it. Otherwise the project page, where they are
    # all listed reading and where a message can be read.
    return RedirectResponse(f"/p/{pid}/m/{mids[0]}" if len(mids) == 1 and not where
                            else f"/p/{pid}{where}", status_code=303)


@router.post("/p/{pid}/m/{mid}/remove")
def remove_material(request: Request, pid: str, mid: str):
    """Take material out now, then rebuild every corpus-level account in the background."""
    conn = connection()
    _mine(request, conn, pid)
    if not store.remove_material(conn, pid, mid):
        return _back(request, f"/p/{pid}")
    if store.materials(conn, pid):
        jobs.resynthesis_chain(pid)
    else:
        store.clear_empty_project_analysis(conn, pid)
    return RedirectResponse(f"/p/{pid}", status_code=303)


@router.post("/p/{pid}/stop")
def stop(request: Request, pid: str):
    """Stop what is running for this project. The step in flight finishes; nothing after it starts."""
    conn = connection()
    _mine(request, conn, pid)
    store.stop_jobs(conn, pid)
    return _back(request, f"/p/{pid}")


@router.post("/p/{pid}/react")
def react(request: Request, pid: str, text: str = Form(""), kind: str = Form("note"),
          claim_id: str = Form(""), theme_id: str = Form(""), material_id: str = Form("")):
    """One free-text comment on one block of the account.

    There used to be Agree and Doubt buttons on every single claim. They were the wrong
    affordance twice over. A claim is the one thing that needs no affordance — its quote is
    sitting in the material beside it, so verifying it is a glance, not a click. And what
    actually wants correcting is a level up: how the reading synthesised, not whether one
    sentence is true. So the buttons are gone and each block takes a sentence instead, which
    goes to the model verbatim when that block is written again.

    An empty comment does nothing. Nothing here is a stance to be tallied.
    """
    conn = connection()
    _mine(request, conn, pid)
    if not text.strip():
        return _back(request, f"/p/{pid}")
    target_kind, target_id = _target(claim_id, theme_id, material_id, pid)
    fid = store.add_feedback(conn, pid, target_kind, target_id, "note", text.strip())
    _go(conn, pid, fid)
    return _back(request, f"/p/{pid}")


@router.post("/p/{pid}/check")
def check(request: Request, pid: str, question: str = Form(...), material_id: str = Form(""),
          scope: str = Form("all")):
    """"Check this against the material" — searches the material for what bears on a question.

    `scope` is which passages: everything, or only the ones no claim rests on yet. Everything is
    the default, because searching only the remainder answers a question the researcher did not
    ask — it returns "not found" on a material whose answer is the sentence a claim already
    rests on. Anything but the two known words is read as everything: a scope this app does not
    have must not silently narrow a search.
    """
    conn = connection()
    _mine(request, conn, pid)
    if not question.strip():
        return _back(request, f"/p/{pid}")
    target_kind, target_id = ("material_summary", material_id) if material_id \
        else ("project_summary", pid)
    fid = store.add_feedback(conn, pid, target_kind, target_id, "check", question.strip())
    # Not `_go`: the searched set is a setting on this run, and it travels with the run rather
    # than with the researcher's words.
    if runs := rerun.plan(conn, fid):
        jobs.start(db.connect, pid, [{**r, "scope": "unused" if scope == "unused" else "all"}
                                     for r in runs])
    return _back(request, f"/p/{pid}")


@router.post("/p/{pid}/refresh")
def refresh(request: Request, pid: str, material_id: str = Form("")):
    """Read a material again against the themes as they now stand.

    Deliberately NOT a piece of feedback. An earlier version posted this as a note whose words the
    app had written, which put sentences the researcher never typed into the record of what the
    researcher said — and that record is the audit trail of the analysis. A re-read is work, so it
    goes straight to the work.
    """
    conn = connection()
    _mine(request, conn, pid)
    stale = [m["id"] for m in store.out_of_date(conn, pid)]
    targets = [material_id] if material_id else stale
    if runs := [{"kind": "doc", "material_id": mid} for mid in targets if mid in stale]:
        # The accounts between the re-reading and the summary. A re-read supersedes the claims a
        # theme's account was written from, and the corpus summary is written from the accounts —
        # so this route used to end by summarising accounts that still cited claims it had just
        # replaced. The step writes only the themes whose evidence actually moved.
        jobs.start(db.connect, pid, runs + [{"kind": "accounts"}, {"kind": "project"}])
    return _back(request, f"/p/{pid}")


@router.post("/p/{pid}/resynthesise")
def resynthesise(request: Request, pid: str):
    """Write the corpus level again after a chain died on the way to it. Same work as a removal:
    the reading below is intact, only what is written over it is missing."""
    conn = connection()
    _mine(request, conn, pid)
    jobs.resynthesis_chain(pid)
    return RedirectResponse(f"/p/{pid}", status_code=303)


@router.post("/p/{pid}/focus")
def focus(request: Request, pid: str, focus: str = Form("")):
    """What the researcher is looking for. Nothing re-runs: it shapes the next reading, and
    nothing already read is read again. Kept as feedback too, so the export shows its history."""
    conn = connection()
    _mine(request, conn, pid)
    store.set_focus(conn, pid, focus.strip())
    store.add_feedback(conn, pid, "focus", pid, "note", focus.strip())
    return _back(request, f"/p/{pid}")


@router.post("/p/{pid}/m/{mid}/rerun")
def rerun_material(request: Request, pid: str, mid: str, step: str = Form("read", alias="from"),
                   note: str = Form("")):
    """"Run the analysis again", from wherever the researcher chose, over one material.

    The one verb that may re-read. Feedback never does — a rerun driven by an opinion would code
    the material under that opinion — but this is not feedback: it is the researcher saying do it
    again, and saying where from. Everything after that point runs too, because a reading that
    changed and a synthesis written over the old one is worse than either.

    A note is stored once, as a comment on this material, and rides on every run in the chain, so
    the steps that take the researcher's words verbatim are handed them and the record shows what
    was asked for.
    """
    conn = connection()
    _mine(request, conn, pid)
    m = store.material(conn, mid)
    step = rerun.PAGE_NAMES.get(step, step)
    if m is None or m["project_id"] != pid or step not in rerun.CHAIN:
        raise HTTPException(status_code=404, detail="not here")
    fid = (store.add_feedback(conn, pid, "material_summary", mid, "note", note.strip())
           if note.strip() else None)
    jobs.start(db.connect, pid, rerun.from_step(mid, step, fid))
    return RedirectResponse(f"/p/{pid}/m/{mid}", status_code=303)


@router.post("/p/{pid}/m/{mid}/reframe")
def reframe(request: Request, pid: str, mid: str, hint: str = Form("")):
    """"This is laid out wrong." Re-describes the material's shape and nothing else — no sentence
    moves, so every code and claim survives it."""
    conn = connection()
    _mine(request, conn, pid)
    fid = store.add_feedback(conn, pid, "frame", mid, "note", hint.strip())
    _go(conn, pid, fid)
    return _back(request, f"/p/{pid}/m/{mid}")


# ---- the hold on a theme --------------------------------------------------------------------------
# Not analysis: the researcher saying where a theme has got to. Freezing spends no model call — it
# changes what the next THEMES pass is allowed to do to the theme, which is why it is one click and
# why unfreezing is one click back.

def _theme(conn, pid: str, tid: str):
    """This project's theme, or a 404. The id arrives in the URL, so a member who may edit one
    project must not reach a theme in another through it."""
    row = conn.execute("SELECT id FROM theme WHERE id=? AND project_id=?", (tid, pid)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="not here")
    return row


@router.post("/p/{pid}/t/{tid}/hold")
def hold(request: Request, pid: str, tid: str, hold: str = Form(...)):
    """Freeze a theme, or unfreeze it. A frozen theme's name and gist are fixed: new material is
    applied to it and what pulls against it comes back as a note, never as a rewrite."""
    conn = connection()
    _mine(request, conn, pid)
    _theme(conn, pid, tid)
    if hold not in ("open", "frozen"):
        raise HTTPException(status_code=404, detail="not here")
    store.set_hold(conn, tid, hold)
    return _back(request, f"/p/{pid}/t/{tid}")


@router.post("/p/{pid}/t/{tid}/promote")
def promote(request: Request, pid: str, tid: str):
    """A candidate the researcher says is a theme already, without waiting for a second material
    to hold a line under it. The other way in is recurrence, and Python does that one."""
    conn = connection()
    _mine(request, conn, pid)
    _theme(conn, pid, tid)
    store.set_hold(conn, tid, "open")
    return _back(request, f"/p/{pid}/t/{tid}")


# ---- sharing ------------------------------------------------------------------------------------
# Not one of the researcher's verbs — nothing here spends a model call or moves a word of the
# analysis. It is here because this is where the POSTs live, and because it takes the same
# `_mine`, asked at the top notch: giving other people a way in is the owner's alone.

@router.post("/p/{pid}/share/link")
def share_link(request: Request, pid: str, role: str = Form("read")):
    """A new link of one kind. Two kinds exist and the role is checked here rather than trusted
    from the form — the table would refuse a third, but with a 500 rather than an answer."""
    conn = connection()
    user = pages_mine(request, conn, pid, need="owner")
    if role not in ("edit", "read"):
        raise HTTPException(status_code=404, detail="not here")
    store.add_invite(conn, pid, role, user["id"] if user else None)
    return RedirectResponse(f"/p/{pid}/share", status_code=303)


@router.post("/p/{pid}/share/revoke")
def share_revoke(request: Request, pid: str, token: str = Form(...)):
    """Shut one link. Whoever already came through it stays a member until they are removed."""
    conn = connection()
    pages_mine(request, conn, pid, need="owner")
    store.revoke_invite(conn, pid, token)
    return RedirectResponse(f"/p/{pid}/share", status_code=303)


@router.post("/p/{pid}/share/remove")
def share_remove(request: Request, pid: str, user_id: str = Form(...)):
    """Take somebody out of the project. The next page they ask for is a 404, like anyone else's."""
    conn = connection()
    pages_mine(request, conn, pid, need="owner")
    store.remove_member(conn, pid, user_id)
    return RedirectResponse(f"/p/{pid}/share", status_code=303)


# ---- the project itself ---------------------------------------------------------------------------

@router.post("/p/{pid}/rename")
def rename(request: Request, pid: str, name: str = Form(...)):
    conn = connection()
    pages_mine(request, conn, pid, need="owner")
    if name.strip():
        store.rename_project(conn, pid, name.strip())
    return RedirectResponse(f"/p/{pid}", status_code=303)


@router.post("/p/{pid}/remove")
def remove_project(request: Request, pid: str):
    """Owner only, and never one click: the form sits behind a fold that says what it does."""
    conn = connection()
    pages_mine(request, conn, pid, need="owner")
    store.remove_project(conn, pid)
    return RedirectResponse("/", status_code=303)
