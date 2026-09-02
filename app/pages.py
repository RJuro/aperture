"""GET routes. Each one is a context function and a template, and nothing else.

There is no client script anywhere in this app: a link is navigation, `:target` does the
highlighting, and `<details>` opens what is folded. A page with work running carries a five-second
meta refresh; an idle page carries none.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, Response
from jinja2 import Environment, FileSystemLoader

from . import context, db

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
_env.filters["txt"] = context.txt

_conn = None


def connection():
    """One connection for the process. Tests replace this whole function with their own."""
    global _conn
    if _conn is None:
        _conn = db.connect()
    return _conn


def _render(template: str, ctx: dict) -> str:
    if not ctx:
        raise HTTPException(status_code=404, detail="not here")
    return _env.get_template(template).render(**ctx)


@router.get("/", response_class=HTMLResponse)
def home() -> str:
    return _env.get_template("home.html").render(**context.home(connection()))


@router.get("/p/{pid}", response_class=HTMLResponse)
def project(pid: str) -> str:
    return _render("project.html", context.project_page(connection(), pid))


@router.get("/p/{pid}/t/{tid}", response_class=HTMLResponse)
def theme(pid: str, tid: str) -> str:
    return _render("theme.html", context.theme_page(connection(), pid, tid))


@router.get("/p/{pid}/export.md")
def export(pid: str) -> Response:
    body = _render("export.md", context.export(connection(), pid))
    return Response(body, media_type="text/markdown; charset=utf-8")


@router.get("/p/{pid}/m/{mid}", response_class=HTMLResponse)
def material(pid: str, mid: str, theme: str | None = None) -> str:
    return _render("material.html", context.material_page(connection(), pid, mid, theme))
