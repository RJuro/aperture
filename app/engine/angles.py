"""ANGLES — what would be worth looking at in this material, written before it is coded.

A first pass codes what is salient and misses what a thoughtful reader would have brought to the
material. So between describing a piece and reading it, the tool ideates: what perspectives does
this material invite, what broader area does it sit in, what areas are inside that, and what would
each of those ask of *this* text. The reading is then pointed at more than what shouts.

The whole of it rests on one rule, stated here, in `prompts/angles.md`, and again in
`prompts/read.md` because that is where it can do damage:

    an angle decides WHERE TO LOOK, never WHAT IS FOUND.

A sensitizing concept that becomes a finding is worse than no concept at all — the reading stops
being a reading of the material and becomes a reading of our suggestions. So an angle is a place
and a question, never a claim, and READ is told in its own rules to code only what the material
says.

Mechanical first, model second, as everywhere: the counts, lengths and shape of what comes back
are settled in Python before anything is stored, and nothing is copied field by field out of the
payload — the rows written here are built here.

What is stored is prose, not a payload. The researcher reads it on the page and READ is shown the
same text, so what the reading was pointed at is exactly what the researcher can see it was
pointed at.
"""
from __future__ import annotations

import sqlite3

from .. import ingest, llm, store

MAX_ANGLES = 8              # kept from one call; the prompt asks for 5 to 8
MIN_QUESTIONS = 2           # an angle that asks nothing is not an angle
MAX_QUESTIONS = 4
MAX_SUBAREAS = 6
NAME_WORDS = 8
WHY_WORDS = 40
QUESTION_WORDS = 25
FIELD_WORDS = 12
SUBAREA_WORDS = 8

# FRAME sees 6000 + 1500 characters, which is all a shape check needs: a transcript declares its
# layout in its first page. Angles are about what the material is *about*, and what a first
# reading undercodes sits in the middle and the late stretch — the part FRAME never sees. So the
# budget here is four times FRAME's: it takes both seed transcripts (21k and 28k characters)
# nearly whole, and it is still far less than READ already sends, which is every sentence.
HEAD, TAIL = 18000, 6000


def _trim(value, cap: int) -> str:
    """Over-long text is cut, never rejected — the cap is a prompt-compliance signal, and a
    question three words too long is still the right question."""
    return " ".join(str(value or "").split()[:cap])


def _verbatim(text: str, empty: str) -> str:
    """The researcher's own words, delimited rather than reworded."""
    text = (text or "").strip()
    return f'"""\n{text}\n"""' if text else empty


def _frame_block(m: sqlite3.Row, speakers: list[sqlite3.Row]) -> str:
    """What this material is and who is in it. Deliberately its own, small version rather than an
    import out of `read.py`: angles need no layout and no section list, and the two prompts should
    be free to say this differently."""
    out = [f"This material is: {m['kind'] or 'not yet described'}",
           f"Its title: {m['title'] or m['name']}"]
    if speakers:
        out.append("Who speaks in it:")
        out += [f"- {s['name'] or s['label']} ({s['role'] or 'other'})" for s in speakers]
    else:
        out.append("Nobody is marked as speaking in it: it is not a transcript of speech.")
    return "\n".join(out)


def _themes_block(rows: list[sqlite3.Row]) -> str:
    if not rows:
        return "This project has no themes yet; nothing has been grouped across materials."
    return "\n".join(f"- {t['name']} — {t['gist'] or 'no gist yet'}" for t in rows)


def _questions(raw) -> list[str]:
    if isinstance(raw, str):
        raw = [raw]
    out: list[str] = []
    for q in raw or []:
        q = _trim(q, QUESTION_WORDS)
        if q and q not in out:
            out.append(q)
    return out[:MAX_QUESTIONS]


def _angles(proposed, dropped: list[str]) -> list[dict]:
    """Nothing half-made is stored. An angle with no name cannot be shown, one with no reason
    cannot be judged by the researcher, and one with fewer than two questions is a heading."""
    kept: list[dict] = []
    seen: set[str] = set()
    for a in proposed or []:
        if not isinstance(a, dict):
            continue
        name = _trim(a.get("name"), NAME_WORDS)
        if not name:
            dropped.append("an angle with no name")
            continue
        if name.lower() in seen:
            dropped.append(f"angle {name!r}: proposed twice")
            continue
        why = _trim(a.get("why"), WHY_WORDS)
        if not why:
            dropped.append(f"angle {name!r}: nothing said about what invites it here")
            continue
        qs = _questions(a.get("questions"))
        if len(qs) < MIN_QUESTIONS:
            dropped.append(f"angle {name!r}: {len(qs)} question(s), {MIN_QUESTIONS} needed")
            continue
        seen.add(name.lower())
        kept.append({"name": name, "why": why, "questions": qs})
    if len(kept) > MAX_ANGLES:
        dropped += [f"angle {a['name']!r}: past the {MAX_ANGLES}-angle limit"
                    for a in kept[MAX_ANGLES:]]
        kept = kept[:MAX_ANGLES]
    return kept


def _subareas(proposed) -> list[str]:
    raw = [proposed] if isinstance(proposed, str) else (proposed or [])
    out = list(dict.fromkeys(s for s in (_trim(x, SUBAREA_WORDS) for x in raw) if s))
    return out[:MAX_SUBAREAS]


def prose(field: str, subareas: list[str], angles: list[dict]) -> str:
    """The stored text. A researcher reads this on the page, so it is written as something to
    read: where the material sits, what is inside that, and then each way in with what invites it
    and what it would ask."""
    out = []
    if field:
        out.append(f"Where this material sits: {field.rstrip('.')}.")
    if subareas:
        out.append("Areas inside that: " + "; ".join(s.rstrip(".") for s in subareas) + ".")
    if angles:
        out.append("Ways into this material — places to look, not things already found:")
        for a in angles:
            asks = "\n".join(f"    - {q}" for q in a["questions"])
            out.append(f"{a['name']}\n    {a['why']}\n{asks}")
    return "\n\n".join(out)


def block(conn: sqlite3.Connection, mid: str) -> str:
    """What READ is shown — the same prose the researcher reads. One text, two surfaces, so the
    two cannot disagree about what the reading was pointed at."""
    row = store.get_summary(conn, "material", mid, "angles")
    return ((row["text"] if row else "") or "").strip() or (
        "Nobody has ideated about this material yet. Read it on its own terms.")


def run(conn: sqlite3.Connection, mid: str) -> dict:
    """Ideate before this material is coded. Returns {field, subareas, angles, text, dropped} and
    stores the prose as this material's `angles` summary."""
    m = store.material(conn, mid)
    pid = m["project_id"]
    proj = store.project(conn, pid)
    described = store.get_summary(conn, "material", mid, "orientation")

    system, user = llm.prompt(
        "angles",
        frame=_frame_block(m, store.speakers(conn, mid)),
        orientation=((described["text"] if described else "") or "").strip()
                    or "Nothing has been written about this material yet.",
        questions=(proj["brief"] or "").strip()
              or "Nothing has been written about this corpus yet; this is an early piece.",
        themes=_themes_block(store.live_themes(conn, pid)),
        material=ingest.head_and_tail(m["text"], HEAD, TAIL),
        max_angles=MAX_ANGLES, max_questions=MAX_QUESTIONS)
    out = llm.chat_json(system, user, label="angles")

    dropped: list[str] = []
    field = _trim(out.get("field"), FIELD_WORDS)
    subareas = _subareas(out.get("subareas"))
    angles = _angles(out.get("angles"), dropped)
    text = prose(field, subareas, angles)

    store.save_summary(conn, "material", mid, "angles", text)
    return {"field": field, "subareas": subareas, "angles": angles, "text": text,
            "dropped": dropped}
