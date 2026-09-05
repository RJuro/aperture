"""GET routes. Each one is a context function and a template, and nothing else.

A link is navigation, `:target` does the highlighting, and `<details>` opens what is folded. The
one script in this app polls `/p/{pid}/runs` while work is running, so the progress line changes
without reloading the page under the reader; an idle page carries neither script nor refresh.
"""
from __future__ import annotations

import re
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from jinja2 import Environment, FileSystemLoader

from . import context, db, store, word

router = APIRouter()

DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

_env = Environment(
    loader=FileSystemLoader(Path(__file__).parent / "templates"),
    # HTML is escaped; the export is markdown and must not be. Text that has to reach the page
    # character-for-character goes through `context.txt`, which escapes < > & and leaves the
    # speaker's own apostrophes alone.
    autoescape=lambda name: bool(name) and name.endswith(".html"),
    # trim_blocks stays off: the export is markdown, where a swallowed newline runs a
    # heading into the line above it.
    lstrip_blocks=True,
)


def _long(d) -> str:
    """'2 September 2026'."""
    return f"{d.day} {d.strftime('%B %Y')}"


def _when(iso: str) -> str:
    """A date a person reads: '2 September 2026', or 'today'. The page was printing
    2026-09-02T19:21:50.112+00:00 beside a project's name."""
    from datetime import date, datetime
    if not iso:
        return ""
    try:
        d = datetime.fromisoformat(str(iso).replace("Z", "+00:00")).date()
    except ValueError:
        return str(iso)[:10]
    if d == date.today():
        return "today"
    return _long(d)


def _plural(noun: str, n) -> str:
    """'1 claim', '2 claims'. Every page prints counts, and '1 claims' is a typo the reader
    charges to the instrument."""
    return noun if n == 1 else noun + "s"


_env.filters["txt"] = context.txt
# Model prose: the same escaping, plus the markdown emphasis the model writes regardless.
_env.filters["prose"] = context.prose
_env.filters["when"] = _when
_env.filters["plural"] = _plural
# The record page shows model prose, and a claim id in it is a link into the material it rests on.
_env.filters["cite"] = context.cite
# The anchor a Markdown renderer gives a heading: lowercase, punctuation dropped, spaces to
# hyphens. "Esther Horwitz — interview, 1991" becomes #esther-horwitz--interview-1991; a link
# built by lowercasing alone kept the dash and the comma and pointed at nothing.
_env.filters["slug"] = lambda s: re.sub(r"[^a-z0-9 -]", "", (s or "").lower()).replace(" ", "-")

_conn = None


def connection():
    """One connection for the process. Tests replace this whole function with their own."""
    global _conn
    if _conn is None:
        _conn = db.connect()
    return _conn


def _render(template: str, ctx: dict, user=None) -> str:
    if not ctx:
        raise HTTPException(status_code=404, detail="not here")
    return _env.get_template(template).render(user=user, **ctx)


# What each role may do, as a ladder. `read` opens pages, `edit` also runs the verbs that change
# the project, `owner` also gives it away.
RANK = {"read": 0, "edit": 1, "owner": 2}


def _mine(request: Request, conn, pid: str, need: str = "read"):
    """The account reading this, having established the project is open to it at `need` or above.

    Every GET and every POST in the app comes through here, so `store.access` is the single
    answer to who may see what. A project that is not yours is 404 and not 403: telling someone a
    project exists but is closed to them is still telling them it exists — and a reader who posts
    to a verb gets the same 404, because a member who may only read is, for that verb, exactly
    someone the project is not there for.
    """
    user = getattr(request.state, "user", None)
    role = store.access(conn, pid, user)
    if role is None or RANK[role] < RANK[need]:
        raise HTTPException(status_code=404, detail="not here")
    return user


@router.get("/", response_class=HTMLResponse)
def home(request: Request) -> str:
    user = getattr(request.state, "user", None)
    return _env.get_template("home.html").render(**context.home(connection(), user))


@router.get("/guide", response_class=HTMLResponse)
def guide(request: Request) -> str:
    """What each control does and what it lets a researcher say. No project: the guide is about
    the instrument, is reached from inside a project and from outside one, and must render either
    way — so it is given the two things `base.html` needs of every page and nothing else."""
    user = getattr(request.state, "user", None)
    return _render("guide.html", {"app_name": context.APP_NAME,
                                  "css_v": context._css_version()}, user)


@router.get("/p/{pid}", response_class=HTMLResponse)
def project(request: Request, pid: str, problem: str = "") -> str:
    conn = connection()
    user = _mine(request, conn, pid)
    ctx = context.project_page(conn, pid)
    # `role` only so the page can leave out the Share button for someone who cannot share. The
    # boundary is the routes below, not this.
    return _render("project.html", ctx and {**ctx, "problem": problem,
                                            "role": store.access(conn, pid, user)}, user)


@router.get("/p/{pid}/share", response_class=HTMLResponse)
def share(request: Request, pid: str, problem: str = "") -> str:
    """Who else may open this project, and the links that let them in. The owner's page: a
    collaborator reads the work, they do not hand it on."""
    conn = connection()
    user = _mine(request, conn, pid, need="owner")
    return _render("share.html", {
        **context._shell(conn, pid), "project": dict(store.project(conn, pid)),
        "problem": problem, "members": [dict(m) for m in store.members(conn, pid)],
        "invites": [dict(i) for i in store.invites(conn, pid)],
        # The link is going to be pasted into a mail, so it has to carry the host. `base_url` is
        # what this request arrived on, which is the address the owner is already looking at.
        "base": str(request.base_url).rstrip("/")}, user)


@router.get("/join/{token}", response_class=HTMLResponse)
def join(request: Request, token: str):
    """Take up an invitation. Signed out, the middleware has already sent them to /login with
    this path to come back to, so a link works from cold."""
    user = getattr(request.state, "user", None)
    conn = connection()
    if user is None:
        # No accounts at all: there is nobody for a membership to belong to, and everything is
        # open anyway.
        return RedirectResponse("/", status_code=303)
    if pid := store.join(conn, token, user["id"]):
        return RedirectResponse(f"/p/{pid}", status_code=303)
    return HTMLResponse(_render("share.html", {
        "app_name": context.APP_NAME, "css_v": context._css_version(),
        "problem": "That invitation is no longer open."}, user), status_code=404)


@router.get("/p/{pid}/runs")
def active_runs(request: Request, pid: str) -> list[dict]:
    """What is running now, for the one script in this app to poll. Empty means it has finished
    and the page is out of date."""
    conn = connection()
    _mine(request, conn, pid)
    return [{"line": r["line"]} for r in store.active_runs(conn, pid)]


@router.get("/p/{pid}/t/{tid}", response_class=HTMLResponse)
def theme(request: Request, pid: str, tid: str) -> str:
    conn = connection()
    user = _mine(request, conn, pid)
    ctx = context.theme_page(conn, pid, tid)
    # `role` as on the project page, and for the same reason: the Freeze and Promote controls are
    # the owner's and an invited editor's. The boundary is the verb, not this.
    return _render("theme.html", ctx and {**ctx, "role": store.access(conn, pid, user)}, user)


def _attachment(name: str, ext: str) -> dict:
    """A download that arrives as a file with the project's name on it, rather than a wall of
    plain text in a browser tab. Anything outside plain ASCII goes: a header is latin-1, and a
    filename is not the place to find out that a project is called something in Greek."""
    safe = re.sub(r"\s+", " ", re.sub(r"[^A-Za-z0-9 ._-]", "", name or "")).strip(" .")
    return {"content-disposition": f'attachment; filename="{safe or "reading record"}{ext}"'}


@router.get("/p/{pid}/export.md")
def export(request: Request, pid: str) -> Response:
    conn = connection()
    _mine(request, conn, pid)
    ctx = context.export(conn, pid)
    body = _render("export.md", ctx)
    return Response(body, media_type="text/markdown; charset=utf-8",
                    headers=_attachment(ctx["project"]["name"], ".md"))


@router.get("/p/{pid}/export.docx")
def export_docx(request: Request, pid: str) -> Response:
    """The same record, as a document a researcher can open, edit and hand in."""
    from datetime import date

    conn = connection()
    _mine(request, conn, pid)
    ctx = context.export(conn, pid)
    name = ctx["project"]["name"]
    body = word.document(_render("export.md", ctx), name, _long(date.today()))
    return Response(body, media_type=DOCX, headers=_attachment(name, ".docx"))


@router.get("/p/{pid}/record", response_class=HTMLResponse)
def record(request: Request, pid: str) -> str:
    conn = connection()
    user = _mine(request, conn, pid)
    return _render("record.html", context.record_page(conn, pid), user)


@router.get("/p/{pid}/m/{mid}", response_class=HTMLResponse)
def material(request: Request, pid: str, mid: str, theme: str | None = None) -> str:
    conn = connection()
    user = _mine(request, conn, pid)
    return _render("material.html", context.material_page(conn, pid, mid, theme), user)
