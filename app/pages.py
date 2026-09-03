"""GET routes. Each one is a context function and a template, and nothing else.

A link is navigation, `:target` does the highlighting, and `<details>` opens what is folded. The
one script in this app polls `/p/{pid}/runs` while work is running, so the progress line changes
without reloading the page under the reader; an idle page carries neither script nor refresh.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, Response
from jinja2 import Environment, FileSystemLoader

from . import context, db, store

router = APIRouter()

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
    return f"{d.day} {d.strftime('%B %Y')}"


def _plural(word: str, n) -> str:
    """'1 claim', '2 claims'. Every page prints counts, and '1 claims' is a typo the reader
    charges to the instrument."""
    return word if n == 1 else word + "s"


_env.filters["txt"] = context.txt
_env.filters["when"] = _when
_env.filters["plural"] = _plural

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


def _mine(request: Request, conn, pid: str):
    """The account reading this, having established the project is theirs to read.

    A project that is not yours is 404 and not 403: telling someone a project exists but is
    closed to them is still telling them it exists. `user` is None on a database with no
    accounts in it, and then every project is open."""
    user = getattr(request.state, "user", None)
    p = store.project(conn, pid)
    if p is None or (user is not None and not user["is_admin"]
                     and p["owner_id"] != user["id"]):
        raise HTTPException(status_code=404, detail="not here")
    return user


@router.get("/", response_class=HTMLResponse)
def home(request: Request) -> str:
    user = getattr(request.state, "user", None)
    return _env.get_template("home.html").render(**context.home(connection(), user))


@router.get("/p/{pid}", response_class=HTMLResponse)
def project(request: Request, pid: str, problem: str = "") -> str:
    conn = connection()
    user = _mine(request, conn, pid)
    ctx = context.project_page(conn, pid)
    return _render("project.html", ctx and {**ctx, "problem": problem}, user)


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
    return _render("theme.html", context.theme_page(conn, pid, tid), user)


@router.get("/p/{pid}/export.md")
def export(request: Request, pid: str) -> Response:
    conn = connection()
    _mine(request, conn, pid)
    body = _render("export.md", context.export(conn, pid))
    return Response(body, media_type="text/markdown; charset=utf-8")


@router.get("/p/{pid}/m/{mid}", response_class=HTMLResponse)
def material(request: Request, pid: str, mid: str, theme: str | None = None) -> str:
    conn = connection()
    user = _mine(request, conn, pid)
    return _render("material.html", context.material_page(conn, pid, mid, theme), user)
