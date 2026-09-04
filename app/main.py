"""Aperture — a reading companion for qualitative material.

The app is server-rendered and has no client script. Routes come in two families: `pages` (GET,
each a pure render of one context function) and `verbs` (POST, each one of the researcher's four
actions). Both are attached here so that neither imports the other.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from . import auth, jobs

# One line per model call and per step on stdout, which is what the host collects (docs/DEPLOY.md
# → Monitoring). uvicorn's own loggers carry their own handlers and do not propagate, so this
# configures the root logger and nothing is printed twice.
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
# httpx logs a line of its own for every request, which would print each model call twice.
logging.getLogger("httpx").setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Resume work committed before this process started."""
    jobs.resume_pending()
    yield

app = FastAPI(title="Aperture", lifespan=lifespan)

app.add_middleware(auth.Accounts)

@app.get("/health")
def health() -> dict:
    """Always reachable, never behind the sign-in — the container's healthcheck hits it."""
    return {"ok": True}


_STATIC = Path(__file__).parent / "static"
if _STATIC.is_dir():
    app.mount("/static", StaticFiles(directory=_STATIC), name="static")


# Routers are attached last so a partially built app still serves /health.
from . import accounts  # noqa: E402
app.include_router(accounts.router)
from . import pages  # noqa: E402
app.include_router(pages.router)
from . import verbs  # noqa: E402
app.include_router(verbs.router)
