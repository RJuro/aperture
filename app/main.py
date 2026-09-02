"""Aperture — a reading companion for qualitative material.

The app is server-rendered and has no client script. Routes come in two families: `pages` (GET,
each a pure render of one context function) and `verbs` (POST, each one of the researcher's four
actions). Both are attached here so that neither imports the other.
"""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from . import auth

app = FastAPI(title="Aperture")

app.add_middleware(auth.PinAuth)


@app.get("/health")
def health() -> dict:
    """Always reachable, never behind the PIN — the container's healthcheck hits it."""
    return {"ok": True}


_STATIC = Path(__file__).parent / "static"
if _STATIC.is_dir():
    app.mount("/static", StaticFiles(directory=_STATIC), name="static")


def data_dir() -> Path:
    d = Path(os.environ.get("APERTURE_DATA_DIR", Path(__file__).parent.parent / "data"))
    d.mkdir(parents=True, exist_ok=True)
    return d


# Routers are attached last so a partially built app still serves /health.
try:                                                    # pragma: no cover - wiring
    from . import pages
    app.include_router(pages.router)
except ImportError:
    pass
try:                                                    # pragma: no cover - wiring
    from . import verbs
    app.include_router(verbs.router)
except ImportError:
    pass
