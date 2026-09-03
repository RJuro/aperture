"""FRAME — what shape a piece of material has, and what it is.

The first thing that happens to any material, and the reason this tool is not an interview tool:
before anything is coded, it works out whether it is holding an interview, a focus group, field
notes, a document or open survey text, how that should be laid out, and writes a short account of
what the material is, so a freshly uploaded piece already reads as something.

Mechanical first, model second. `turns.scan` runs before the prompt is built and its counts go
*into* the prompt as evidence; the model names and roles what the scan found and never parses.
Then everything the model proposes is checked against the material before it reaches the database:
a speaker label must begin lines that are really there, a segment's quote must be locatable by
`anchor.bind`. Same law as the anchor, applied to structure — what cannot be found is dropped and
named in `dropped`.

Framing never writes a sentence. Sentence ids are the spine every code and moment cites, so a
re-frame re-describes and leaves them exactly where they were.
"""
from __future__ import annotations

import re
import sqlite3

from .. import anchor, ingest, llm, store, titles, turns

KINDS = ("interview", "focus_group", "fieldnotes", "document", "open_text", "other")
DISPLAYS = ("turns", "segments", "plain")
ROLES = ("interviewer", "participant", "other")

MAX_SEGMENTS = 12
TITLE_WORDS = 10
ORIENTATION_WORDS = 150


def _trim(value, cap: int) -> str:
    """Over-long text is cut, never rejected: the cap is a prompt-compliance signal and a title
    three words too long is still the right title."""
    return " ".join(str(value or "").split()[:cap])


def _year(value) -> str:
    """The year the material was made, or nothing. A four-digit number outside the range in which
    qualitative material is produced is a misreading, not a date."""
    v = str(value or "").strip()
    return v if re.fullmatch(r"\d{4}", v) and 1800 <= int(v) <= 2100 else ""


def _one_of(value, allowed: tuple[str, ...], fallback: str) -> str:
    v = str(value or "").strip().lower().replace(" ", "_").replace("-", "_")
    return v if v in allowed else fallback


def _scan_block(raw: str) -> str:
    """The counts, not a conclusion. A model told 'the speakers are X and Y' has nothing left to
    judge; a model shown 'PHILLIPS 77, BIRTH DATE 1' can see why one is a speaker."""
    counts = turns.scan(raw)
    if not counts:
        return ("No line in this material begins with a `NAME:` cue. The scan found nothing, so "
                "any speaker you propose is your own and must be visible at the start of lines.")
    rows = "\n".join(f"  {label}: {n} line{'' if n == 1 else 's'}"
                     for label, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])))
    recurring = turns.speakers(raw)
    tail = ", ".join(recurring) if recurring else (
        "none — every label above appears too rarely to be a speaker")
    return f"{rows}\n\nRecurring {turns.MIN_TURNS} times or more: {tail}"


def _correction_block(conn: sqlite3.Connection, mid: str, hint: str) -> str:
    """A re-frame is the researcher saying the layout is wrong. Their words go through verbatim,
    with what was said last time, so the model knows what it is correcting."""
    if not hint.strip():
        return ("THIS IS THE FIRST DESCRIPTION OF THIS MATERIAL\n\n"
                "Nobody has described it before, so there is nothing to correct.")
    row = store.material(conn, mid)
    speakers = store.speakers(conn, mid)
    segments = store.segments(conn, mid)
    said = "\n".join([
        f"  kind: {row['kind'] or '(none)'}",
        f"  display: {row['display'] or '(none)'}",
        f"  title: {row['title'] or '(none)'}",
        "  speakers: " + (", ".join(f"{s['label']} ({s['name'] or 'unnamed'}, {s['role']})"
                                    for s in speakers) or "none"),
        "  sections: " + (", ".join(s["label"] for s in segments) or "none"),
    ])
    return ("THE RESEARCHER SAYS THIS MATERIAL IS LAID OUT WRONG\n\n"
            "Their words, exactly as they wrote them:\n\n"
            f"  {hint.strip()}\n\n"
            "What was said about this material last time:\n\n"
            f"{said}\n\n"
            "Correct it. The researcher has the material in front of them; where they and the "
            "earlier description disagree, they are right.")


def _speakers(raw: str, proposed, dropped: list[str]) -> list[dict]:
    """Every label must be found at the start of lines in the material before it is used."""
    kept, seen = [], set()
    for s in proposed or []:
        if not isinstance(s, dict):
            continue
        label = str(s.get("label", "") or "").strip()
        if not label or label in seen:
            continue
        seen.add(label)
        n = turns.occurrences(raw, label)
        if n < turns.MIN_VERIFY:
            dropped.append(f"speaker {label!r}: {n} line starts in the material, "
                           f"{turns.MIN_VERIFY} needed")
            continue
        kept.append({"label": label, "name": str(s.get("name", "") or "").strip(),
                     "role": _one_of(s.get("role"), ROLES, "other")})
    return kept


def _segments(sentences: list[tuple[str, str]], proposed, dropped: list[str]) -> list[dict]:
    """Every section start must be a quote `anchor.bind` can locate. Nothing is cited yet, so an
    unfound anchor drops the section and a found one carries back the sid it was found at."""
    kept = []
    for s in proposed or []:
        if not isinstance(s, dict):
            continue
        quote = str(s.get("anchor", "") or "").strip()
        label = _trim(s.get("label"), TITLE_WORDS) or "Section"
        verdict = anchor.bind(quote, [], sentences)
        if verdict["verdict"] == "unfound" or not verdict["sids"]:
            dropped.append(f"section {label!r}: its quote is not in the material")
            continue
        kept.append({"sid": verdict["sids"][0], "label": label, "anchor": quote})
    if len(kept) > MAX_SEGMENTS:
        dropped += [f"section {s['label']!r}: past the {MAX_SEGMENTS}-section limit"
                    for s in kept[MAX_SEGMENTS:]]
        kept = kept[:MAX_SEGMENTS]
    return kept


def run(conn: sqlite3.Connection, mid: str, *, hint: str = "") -> dict:
    """Describe one material's shape and write its orientation. `hint` is a researcher saying the
    layout is wrong, and is passed to the model verbatim."""
    raw = store.material(conn, mid)["text"]
    system, user = llm.prompt("frame",
                              scan=_scan_block(raw),
                              correction=_correction_block(conn, mid, hint),
                              material=ingest.head_and_tail(raw))
    out = llm.chat_json(system, user, label="frame")

    dropped: list[str] = []
    kind = _one_of(out.get("kind"), KINDS, "other")
    display = _one_of(out.get("display"), DISPLAYS, "plain")
    year = _year(out.get("year"))
    speakers = _speakers(raw, out.get("speakers"), dropped)
    segments = _segments(store.sentences(conn, mid), out.get("segments"), dropped)
    # The naming standard is Python's, not a rule the model is asked to keep: the title is
    # composed from the speakers that survived verification and the kind that was coerced.
    title = titles.compose(kind, speakers, _trim(out.get("title"), TITLE_WORDS), year)
    orientation = _trim(out.get("orientation"), ORIENTATION_WORDS)

    # A layout with nothing to lay out is a layout the page cannot render. Both structured
    # displays fall back the same way, for the same reason: what the model proposed did not
    # survive being checked against the material, so there is nothing to show but the text.
    if display == "turns" and not speakers:
        dropped.append("display 'turns': no speaker survived, showing the material plain")
        display = "plain"
    if display == "segments" and not segments:
        dropped.append("display 'segments': no section survived, showing the material plain")
        display = "plain"

    store.save_frame(conn, mid, kind=kind, display=display, title=title, speakers=speakers,
                     segments=segments, year=year)
    store.save_summary(conn, "material", mid, "orientation", orientation)
    return {"kind": kind, "display": display, "title": title, "year": year, "speakers": speakers,
            "segments": segments, "orientation": orientation, "dropped": dropped}
