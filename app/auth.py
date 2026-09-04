"""The sign-in gate, one middleware. Signed out, everything goes to /login except /health and
/static — the container's healthcheck and the stylesheet must work before anyone has signed in.

A database with no accounts in it is open, which is how this runs on a laptop and how the suite
runs. A deployment gets its first account from `APERTURE_ADMIN` on first boot and is shut from
that moment on.

# ponytail: an instance deployed with APERTURE_ADMIN unset stays open until someone is created.
# If that ever needs to be impossible, refuse to start instead of opening.
"""
from __future__ import annotations

from urllib.parse import quote

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse

from . import accounts

OPEN = ("/health", "/static", "/favicon.ico")


class Accounts(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        path = request.url.path
        if path.startswith(OPEN):
            return await call_next(request)
        conn = accounts.connection()
        accounts.bootstrap(conn)
        request.state.user = user = accounts.current_user(request, conn)
        if user or path == "/login" or not accounts.anyone(conn):
            return await call_next(request)
        # Where they were going, so an invitation link works from cold: click it signed out, sign
        # in, and land on the project rather than on a home page that does not yet list it.
        where = path + (f"?{request.url.query}" if request.url.query else "")
        return RedirectResponse(f"/login?next={quote(where, safe='')}" if path != "/"
                                else "/login", status_code=303)
