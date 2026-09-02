"""Aperture — a reading companion for qualitative material.

Configuration is read here, at package import, so every entry point sees the same environment:
the server, a one-off script, a test.
"""
from __future__ import annotations

import os
from pathlib import Path


def load_env(path: Path | None = None) -> None:
    """Read a gitignored `.env` at the repo root into the environment, without a dependency.

    A real environment variable always wins — production sets them in Coolify and must not be
    overridden by a file that happened to ship in the image.
    """
    path = path or Path(__file__).resolve().parent.parent / ".env"
    if not path.is_file():
        return
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_env()
