"""DIARIZE — who is speaking, when the material never says.

Runs only where it is needed. `turns.scan` looks for a `NAME:` cue at the start of every line
before the frame prompt is even built; when it finds none in an interview or a focus group, the
frame falls back to `plain` and the whole reading above it then treats the interviewer's questions
as the participant's words. One conflation at the bottom, inherited by every layer.

Mechanical first, model second, exactly as the frame works: Python has already looked and found
nothing, so the model is asked one narrow thing — where does the voice change — and everything it
points at is checked against the material. A passage that is not here is dropped and said so; an
entry that goes backwards is dropped and said so.

What survives is stored as this material's sections, because a section is already a label bound to
a passage and the page, the reading and the synthesis all know how to lay those out. The label the
model sees stays plain (`Participant`); the material's row carries the fact that it was estimated,
and the page adds that word where a reader sees it. A guess is never shown as a fact.
"""
from __future__ import annotations

import sqlite3

from .. import llm, store
from . import synth

MAX_POINTS = 300        # a change of voice per passage, for a very long transcript
LABEL_WORDS = 3         # "Participant 2" is a name; a sentence is not


def needed(frame_out: dict) -> bool:
    """Speech that does not say who is speaking. Anything else reads as it always did."""
    return (frame_out.get("kind") in ("interview", "focus_group")
            and not frame_out.get("speakers"))


def run(conn: sqlite3.Connection, mid: str) -> dict:
    """Estimate this material's speakers. Returns {"speakers", "dropped"}."""
    row = store.material(conn, mid)
    at_of = {sid: i for i, (sid, _) in enumerate(store.sentences(conn, mid))}
    system, user = llm.prompt("diarize", frame=synth.frame_block(conn, mid),
                              material=synth.layout(conn, mid), max_points=MAX_POINTS)
    out = llm.chat_json(system, user, label="diarize")

    dropped: list[str] = []
    kept: list[dict] = []
    at = -1
    for e in out.get("speakers") or []:
        if not isinstance(e, dict):
            continue
        sid = str(e.get("sid") or "").strip()
        who = " ".join(str(e.get("speaker") or "").split()[:LABEL_WORDS])
        if sid not in at_of:
            dropped.append(f"a change of speaker at {sid or '(no passage given)'}: that passage "
                           "is not in this material")
            continue
        if at_of[sid] <= at:
            dropped.append(f"a change of speaker at {sid}: it does not come after the one before")
            continue
        if not who:
            dropped.append(f"a change of speaker at {sid}: nobody was named")
            continue
        at = at_of[sid]
        if kept and kept[-1]["label"] == who:
            continue                    # the same voice again is not a change of voice
        kept.append({"sid": sid, "label": who})
        if len(kept) == MAX_POINTS:
            dropped.append(f"the material changes speaker more than {MAX_POINTS} times; the rest "
                           "was left as it was")
            break

    if not kept:
        dropped.append("nobody could be placed in this material, so it is shown as it stands")
        return {"speakers": [], "dropped": dropped}
    store.save_frame(conn, mid, kind=row["kind"], display="segments", title=row["title"],
                     speakers=[], segments=kept, year=row["year"] or "", estimated=True)
    return {"speakers": kept, "dropped": dropped}
