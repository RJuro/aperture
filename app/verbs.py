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
from .pages import connection

router = APIRouter()


def _back(request: Request, fallback: str) -> RedirectResponse:
    """Back where they were, so a reaction leaves them looking at the same thing they reacted to.
    303 because this was a POST and the browser must follow it with a GET."""
    return RedirectResponse(request.headers.get("referer") or fallback, status_code=303)


def _mine(request: Request, conn, pid: str) -> None:
    """POSTs observe the same ownership boundary as project pages."""
    user = getattr(request.state, "user", None)
    project = store.project(conn, pid)
    if project is None or (user is not None and not user["is_admin"]
                           and project["owner_id"] != user["id"]):
        raise HTTPException(status_code=404, detail="not here")


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
    mids = []
    for piece_name, body in pieces:
        mid = store.add_material(conn, pid, piece_name, body)
        store.save_sentences(conn, mid, ingest.sentences(body))
        mids.append(mid)
    if not mids:
        return RedirectResponse(f"/p/{pid}", status_code=303)
    jobs.ingest_chain(pid, mids)
    # One piece: straight to it. Several: the project page, where they are all listed reading.
    return RedirectResponse(f"/p/{pid}/m/{mids[0]}" if len(mids) == 1 else f"/p/{pid}",
                            status_code=303)


@router.post("/p/{pid}/m/{mid}/remove")
def remove_material(request: Request, pid: str, mid: str):
    """Take material out now, then rebuild every corpus-level account in the background."""
    conn = connection()
    _mine(request, conn, pid)
    if not store.remove_material(conn, pid, mid):
        return _back(request, f"/p/{pid}")
    remaining = [m["id"] for m in store.materials(conn, pid)]
    if remaining:
        jobs.removal_chain(pid, remaining)
    else:
        store.clear_empty_project_analysis(conn, pid)
    return RedirectResponse(f"/p/{pid}", status_code=303)


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
def check(request: Request, pid: str, question: str = Form(...), material_id: str = Form("")):
    """"Check this against the material" — searches the passages no claim rests on."""
    conn = connection()
    _mine(request, conn, pid)
    if not question.strip():
        return _back(request, f"/p/{pid}")
    target_kind, target_id = ("material_summary", material_id) if material_id \
        else ("project_summary", pid)
    fid = store.add_feedback(conn, pid, target_kind, target_id, "check", question.strip())
    _go(conn, pid, fid)
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
        jobs.start(db.connect, pid, runs + [{"kind": "project"}])
    return _back(request, f"/p/{pid}")


@router.post("/p/{pid}/focus")
def focus(request: Request, pid: str, focus: str = Form("")):
    """What the researcher is looking for. Nothing re-runs: it shapes the next reading, and
    nothing already read is read again. Kept as feedback too, so the export shows its history."""
    conn = connection()
    _mine(request, conn, pid)
    store.set_focus(conn, pid, focus.strip())
    store.add_feedback(conn, pid, "focus", pid, "note", focus.strip())
    return _back(request, f"/p/{pid}")


@router.post("/p/{pid}/m/{mid}/reframe")
def reframe(request: Request, pid: str, mid: str, hint: str = Form("")):
    """"This is laid out wrong." Re-describes the material's shape and nothing else — no sentence
    moves, so every code and claim survives it."""
    conn = connection()
    _mine(request, conn, pid)
    fid = store.add_feedback(conn, pid, "frame", mid, "note", hint.strip())
    _go(conn, pid, fid)
    return _back(request, f"/p/{pid}/m/{mid}")
