"""BRIEF — the project's record, told to someone who has not read it, and then spoken.

Only on request. One call over the record the export prints — the same text a researcher would
hand a colleague — then Kokoro reads what came back. The text is the project's `brief` summary;
the audio sits beside the database. A voice that cannot be reached leaves the text standing, and
an old recording is removed rather than left playing over a brief it no longer matches.
"""
from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

from .. import db, llm, store, tts

log = logging.getLogger(__name__)

# About five minutes read aloud, asked for as an aim with room above it: asked for 750 as a cap,
# a two-interview project came back cut before its ending, nine themes deep.
AIM_WORDS, BRIEF_WORDS = 650, 800

# The record is long where a corpus is: every claim of every material is printed in full at the
# end of it. The themes, their accounts and each material's summary come first.
# ponytail: a flat cut at the per-material claims; select claims per theme if a corpus outgrows it.
RECORD_CHARS = 150_000
CUT = ("\n\n(The claims printed material by material were left out here: the record is too long "
       "for one brief.)")


def audio_path(pid: str) -> Path:
    return db.data_dir() / "briefs" / f"{pid}.mp3"


def record(conn: sqlite3.Connection, pid: str) -> str:
    from .. import context, pages
    md = pages._render("export.md", context.export(conn, pid))
    if len(md) > RECORD_CHARS:
        md = md.split("\n## Materials\n")[0][:RECORD_CHARS] + CUT
    return md


def run(conn: sqlite3.Connection, pid: str, *, feedback: str = "",
        run_id: str | None = None) -> None:
    """Write the brief. Nothing is returned for the run row: its notes are printed under
    "Excluded from the analysis", and neither step here excludes anything. The page says when a
    brief has no recording; the reason goes to the log."""
    from . import synth
    proj = store.project(conn, pid)
    system, user = llm.prompt(
        "brief", record=record(conn, pid), brief_words=BRIEF_WORDS, aim_words=AIM_WORDS,
        focus=proj["focus"] or "The researcher has not said what they are looking for.",
        feedback=feedback.strip() or "The researcher has said nothing about this brief.")
    out = llm.chat_json(system, user, label="brief")
    text = synth.words(out.get("brief") if isinstance(out, dict) else "", BRIEF_WORDS)
    if not text:
        log.warning("brief project=%s came back empty; the one before it stands", pid)
        return
    store.save_summary(conn, "project", pid, "brief", text, run_id)
    # The recording that stood is for the brief that just went: gone now, so the page never plays
    # it over this one. `speak` makes the new one.
    audio_path(pid).unlink(missing_ok=True)


def speak(conn: sqlite3.Connection, pid: str) -> None:
    """Read the live brief aloud. Its own step, because a cold voice can take ten minutes and the
    writing step holds one of the process's model-call permits for as long as it runs."""
    row = store.get_summary(conn, "project", pid, "brief")
    if row is None or not row["text"].strip() or audio_path(pid).exists():
        return                              # nothing to read, or this brief is already recorded
    try:
        tts.speak(row["text"], audio_path(pid),
                  title=f"Aperture brief: {store.project(conn, pid)['name']}")
    except tts.SpeechError as e:
        audio_path(pid).unlink(missing_ok=True)
        log.warning("brief project=%s written and not spoken: %s", pid, e)
