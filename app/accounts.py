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
import re
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

LOCAL = re.compile(r"/[A-Za-z0-9/_.~%!$&'()*+,;=:@?-]*")


def _local(where: str) -> str:
    """Where to go after signing in, and only somewhere on this site.

    Anything else is an open redirect: a link to our own sign-in page that lands the researcher,
    freshly signed in, on somebody else's. A path, then, and not '//host' — which a browser reads
    as another site — and nothing that could break out of the header.
    """
    return where if where.startswith("/") and not where.startswith("//") \
        and LOCAL.fullmatch(where) else "/"


@router.get("/login", response_class=HTMLResponse)
def login_page(next: str = "") -> str:
    return _render("login.html", {"problem": "", "next": _local(next)})


@router.post("/login")
def sign_in(name: str = Form(...), password: str = Form(""), next: str = Form("/")):
    conn = connection()
    user = store.verify_user(conn, name.strip(), password)
    if user is None:
        return HTMLResponse(_render("login.html", {"problem": "That name and password do not "
                                                              "go together.",
                                                   "next": _local(next)}), status_code=401)
    token = secrets.token_urlsafe(32)
    conn.execute("INSERT INTO session (token, user_id, created_at) VALUES (?,?,?)",
                 (token, user["id"], store.now()))
    conn.commit()
    r = RedirectResponse(_local(next), status_code=303)
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
            "WHERE p.removed_at IS NULL ORDER BY p.created_at DESC")]})


@router.get("/admin/runs", response_class=HTMLResponse)
def admin_runs_page(request: Request) -> str:
    """What the instrument has been doing, across every project — the `run` table has held it all
    along and only each project's owner could see it. Counts, ids and times: this page is how an
    administrator sees that a model call has been hanging for an hour, not what it was reading."""
    user = _admin(request)
    conn = connection()
    return _render("admin_runs.html", {
        "user": user,
        "days": [dict(d) for d in store.runs_by_day(conn)],
        "runs": [dict(r) for r in store.recent_runs(conn)]})


@router.post("/admin/users")
def add_user(request: Request, name: str = Form(...), password: str = Form(...)):
    _admin(request)
    try:
        store.create_user(connection(), name.strip(), password)
    except sqlite3.IntegrityError:          # a name is how someone signs in, so it is theirs alone
        return RedirectResponse("/admin?problem=That+name+is+taken.", status_code=303)
    return RedirectResponse("/admin", status_code=303)


@router.post("/admin/password")
def reset_password(request: Request, user_id: str = Form(...), password: str = Form(...)):
    """A researcher who forgets their password is otherwise locked out for good: there is no
    email and no reset, and the name is taken for ever."""
    _admin(request)
    store.set_password(connection(), user_id, password)
    return RedirectResponse("/admin?problem=That+password+has+been+changed.", status_code=303)


@router.post("/admin/owner")
def set_owner(request: Request, project_id: str = Form(...), user_id: str = Form(...)):
    """Put a project nobody owns back into somebody's hands — and nothing else.

    An administrator cannot open other people's projects, and reassignment must not be the way
    round that: giving yourself a project you cannot read is reading it. `store.set_owner`
    refuses any project whose owner still exists, so this is only ever the rescue it was added
    for — one made before accounts existed, or one whose owner account is gone.
    """
    _admin(request)
    if not store.set_owner(connection(), project_id, user_id):
        return RedirectResponse("/admin?problem=That+project+already+has+an+owner.+Only+its+"
                                "owner+can+share+it.", status_code=303)
    return RedirectResponse("/admin?problem=That+project+has+a+new+owner.", status_code=303)


@router.get("/account", response_class=HTMLResponse)
def account_page(request: Request, problem: str = "") -> str:
    user = getattr(request.state, "user", None)
    if user is None:
        return RedirectResponse("/login", status_code=303)
    return _render("account.html", {"user": dict(user), "problem": problem})


@router.post("/account")
def change_password(request: Request, current: str = Form(""), new: str = Form(""),
                    again: str = Form("")):
    """Change your own password: the current one to prove it is you, the new one twice."""
    conn = connection()
    user = getattr(request.state, "user", None)
    if user is None:
        return RedirectResponse("/login", status_code=303)
    if store.verify_user(conn, user["name"], current) is None:
        return RedirectResponse("/account?problem=The+current+password+is+not+right.", status_code=303)
    if len(new) < 8 or new != again:
        return RedirectResponse("/account?problem=The+new+password+must+be+at+least+8+characters+and+typed+the+same+twice.",
                                status_code=303)
    store.set_password(conn, user["id"], new)
    store.sign_out_others(conn, user["id"], keep=request.cookies.get(COOKIE, ""))
    # The old redirect landed on the projects list with nothing said, which looked exactly like a
    # failure. The account page already has a slot for a sentence.
    return RedirectResponse("/account?problem=Your+password+has+been+changed.", status_code=303)
