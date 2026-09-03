"""Accounts: who is signed in, and the page an admin makes people from.

A session is a random token in a row, not a signature over the user id. Both survive a restart;
the row survives it without a secret to configure, and signing out is a DELETE rather than a hope
that the browser dropped the cookie. One table, four statements, no key management.

There is no email, no reset and no roles beyond `is_admin`: an admin makes an account and says the
password out loud. A deployment with three researchers on it does not need more, and every one of
those features is a surface that has to be right.
"""
from __future__ import annotations

import os
import secrets
import sqlite3

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from . import context, store

router = APIRouter()

COOKIE = "aperture_session"
YEAR = 60 * 60 * 24 * 365


def connection():
    """The one connection the process already has. Tests replace this whole function."""
    from .pages import connection as _pages_connection
    return _pages_connection()


def _render(template: str, ctx: dict) -> str:
    from .pages import _env
    return _env.get_template(template).render(app_name=context.APP_NAME, **ctx)


# ---- who is signed in ---------------------------------------------------------------------------

def current_user(request: Request, conn: sqlite3.Connection) -> sqlite3.Row | None:
    token = request.cookies.get(COOKIE, "")
    if not token:
        return None
    return conn.execute("SELECT u.* FROM session s JOIN user u ON u.id = s.user_id "
                        "WHERE s.token = ?", (token,)).fetchone()


def anyone(conn: sqlite3.Connection) -> bool:
    """Whether this database has accounts at all. It is what turns the sign-in on: a database
    with none is a laptop, and asking a lone researcher to invent a password to read their own
    files is a lock on the inside of an empty room."""
    return conn.execute("SELECT 1 FROM user LIMIT 1").fetchone() is not None


def bootstrap(conn: sqlite3.Connection) -> None:
    """The first admin, from `APERTURE_ADMIN=name:password`, and only while there is nobody.
    A deployment cannot be signed into before it has an account, and the account cannot be made
    through a page that itself needs one."""
    spec = os.environ.get("APERTURE_ADMIN", "")
    if ":" not in spec or anyone(conn):
        return
    name, _, password = spec.partition(":")
    store.create_user(conn, name.strip(), password, is_admin=True)


def _admin(request: Request) -> sqlite3.Row:
    """An account that is not an admin is told the page is not there, the same as a project that
    is not theirs — what exists here is not theirs to learn."""
    user = getattr(request.state, "user", None)
    if user is None or not user["is_admin"]:
        raise HTTPException(status_code=404, detail="not here")
    return user


# ---- routes -------------------------------------------------------------------------------------

@router.get("/login", response_class=HTMLResponse)
def login_page() -> str:
    return _render("login.html", {"problem": ""})


@router.post("/login")
def sign_in(name: str = Form(...), password: str = Form("")):
    conn = connection()
    user = store.verify_user(conn, name.strip(), password)
    if user is None:
        return HTMLResponse(_render("login.html", {"problem": "That name and password do not "
                                                              "go together."}), status_code=401)
    token = secrets.token_urlsafe(32)
    conn.execute("INSERT INTO session (token, user_id, created_at) VALUES (?,?,?)",
                 (token, user["id"], store.now()))
    conn.commit()
    r = RedirectResponse("/", status_code=303)
    r.set_cookie(COOKIE, token, httponly=True, samesite="lax", max_age=YEAR)
    return r


@router.post("/logout")
def sign_out(request: Request):
    conn = connection()
    conn.execute("DELETE FROM session WHERE token=?", (request.cookies.get(COOKIE, ""),))
    conn.commit()
    r = RedirectResponse("/login", status_code=303)
    r.delete_cookie(COOKIE)
    return r


@router.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request, problem: str = "") -> str:
    user = _admin(request)
    conn = connection()
    return _render("admin.html", {
        "user": user, "problem": problem,
        "people": [dict(u) for u in store.users(conn)],
        "projects": [dict(p) for p in conn.execute(
            "SELECT p.*, u.name AS owner FROM project p LEFT JOIN user u ON u.id = p.owner_id "
            "ORDER BY p.created_at DESC")]})


@router.post("/admin/users")
def add_user(request: Request, name: str = Form(...), password: str = Form(...)):
    _admin(request)
    try:
        store.create_user(connection(), name.strip(), password)
    except sqlite3.IntegrityError:          # a name is how someone signs in, so it is theirs alone
        return RedirectResponse("/admin?problem=That+name+is+taken.", status_code=303)
    return RedirectResponse("/admin", status_code=303)
