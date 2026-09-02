"""PIN gate for a shared deployment. Off entirely when APERTURE_PIN is unset (local dev).

One cookie, one small page, no dependency. /health and /static are always open so the container's
healthcheck and the stylesheet work before anyone logs in.
"""
from __future__ import annotations

import hmac
import os

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import HTMLResponse, RedirectResponse

COOKIE = "aperture_pin"
OPEN = ("/health", "/static", "/favicon.ico")

_PAGE = """<!doctype html><meta charset="utf-8"><title>Aperture</title>
<style>body{font:16px/1.5 system-ui;margin:20vh auto;max-width:20rem;padding:0 1rem}
input,button{font:inherit;padding:.5rem;width:100%;box-sizing:border-box;margin:.3rem 0}</style>
<h1>Aperture</h1><form method="post" action="/auth"><label>PIN<input name="pin" type="password"
autofocus></label><button>Enter</button>%s</form>"""


def pin() -> str:
    return os.environ.get("APERTURE_PIN", "").strip()


class PinAuth(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        want = pin()
        path = request.url.path
        if not want or path.startswith(OPEN):
            return await call_next(request)
        if path == "/auth":
            form = await request.form()
            if hmac.compare_digest(str(form.get("pin", "")), want):
                r = RedirectResponse("/", status_code=303)
                r.set_cookie(COOKIE, want, httponly=True, samesite="lax", max_age=60 * 60 * 24 * 30)
                return r
            return HTMLResponse(_PAGE % "<p>Not that one.</p>", status_code=401)
        if hmac.compare_digest(request.cookies.get(COOKIE, ""), want):
            return await call_next(request)
        return HTMLResponse(_PAGE % "", status_code=401)
