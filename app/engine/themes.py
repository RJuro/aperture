"""THEMES — the codebook becomes themes, across the whole project (L3 in the plan's §1).

The model is shown the themes that are live now with the codes they gather, the codebook with
how often each code was hit in each material — which is how it can see what spans the corpus and
what belongs to one interview only — the researcher's focus, and any feedback on the themes in
the researcher's own words.

Python rules on what comes back: a code name that is not in the codebook is ignored, no more
themes stay live than the corpus can populate (`ceiling`), and a theme the model wants folded into
another is *merged*, never deleted — a moment that cited it must still resolve to something.
"""
from __future__ import annotations

import sqlite3

from .. import llm, store

MAX_THEMES = 12

# The prompt asks for a name of at most eight words. This is the guard, and it sits above what is
# asked so an obedient answer is never touched: a blind reader of a real record met the heading
# "Cultural heritage as enrichment and as discipline to" and read the instrument, not the theme.
# A name that does run past the guard is cut at a word and says it was cut, the same way a quote
# is clipped for a set-aside note — a word cut in half reads as damage to the record.
NAME_WORDS = 12


def name_of(value) -> str:
    """A theme's name, whitespace normalised and never cut mid-word."""
    said = str(value or "").split()
    return " ".join(said) if len(said) <= NAME_WORDS else " ".join(said[:NAME_WORDS]) + " …"


def ceiling(conn: sqlite3.Connection, pid: str) -> int:
    """How many themes this project may carry, from how much material it has.

    Twelve themes over three interviews is what a flat cap bought: five of them resting on one
    material each, which is a coding scheme rather than a set of themes. Four, and one more for
    every material, keeps the ceiling below what the corpus can populate — and it is a ceiling,
    never a target, so `MAX_THEMES` still holds at the top.

    It used to rise by two a material, which put a four-interview project at the hard cap on the
    day its fourth interview was read: a record came back with twelve themes, eleven of them
    claimed in every one of the four materials. Rising by one, the same project may carry eight
    and the cap is not reached until eight materials — which is roughly where twelve themes stop
    being a coding scheme.
    """
    return min(MAX_THEMES, 4 + len(store.materials(conn, pid)))


def _verbatim(text: str, empty: str) -> str:
    text = (text or "").strip()
    return f'"""\n{text}\n"""' if text else empty


def _themes_block(conn: sqlite3.Connection, rows: list[sqlite3.Row]) -> str:
    if not rows:
        return "There are no themes yet. Every theme you return is a new one."
    out = []
    for t in rows:
        codes = ", ".join(c["name"] for c in store.theme_codes(conn, t["id"])) or "no codes yet"
        out.append(f'- id {t["id"]} · "{t["name"]}" — {t["gist"] or "no gist yet"}\n'
                   f"  gathers: {codes}")
    return "\n".join(out)


def _codebook_block(conn: sqlite3.Connection, pid: str) -> str:
    """Names and definitions. Nothing about where a code was found or how often.

    Three prompt rules in a row failed to keep location out of the gists. Shown material titles,
    the model wrote "absent from the bakery interview"; shown counts instead, it wrote "found in
    one of two materials". Whatever spread it is given, it echoes. So it is given none: grouping
    codes into themes is a judgement about meaning, and where a theme reaches is the account's
    conclusion, written later over the evidence. Remove the information and there is nothing to
    echo — a rule the model must obey is weaker than a fact it never sees.
    """
    codes = store.codebook(conn, pid)
    if not codes:
        return "The codebook is empty; nothing has been read yet."
    return "\n".join(f"- {c['name']} — {c['definition'] or 'no definition recorded'}" for c in codes)


def _material_block(conn: sqlite3.Connection, mid: str | None) -> str:
    """The material just read, with its codes marked by passage — so the theme set is revised by
    someone who has the text in front of them.

    A blind theorist, shown only code labels, over-generalises and writes findings into gists;
    the predecessor project learned that and fixed it the same way. At fifty materials the set is
    still revised one material at a time, which keeps this bounded."""
    if not mid:
        return "No material accompanies this pass; revise the themes from the codebook alone."
    from . import synth
    m = store.material(conn, mid)
    hits: dict[str, list[str]] = {}
    for h in store.hits(conn, mid):
        hits.setdefault(h["name"], []).append(h["sid"])
    marked = "\n".join(f"- {name}: {', '.join(sids)}" for name, sids in sorted(hits.items()))
    return (f"## {m['title'] or m['name']} ({m['kind'] or 'kind not worked out'})\n\n"
            f"CODES MARKED IN THIS MATERIAL, by passage:\n{marked or '- none'}\n\n"
            f"THE MATERIAL:\n{synth.layout(conn, mid)}")


def run(conn: sqlite3.Connection, pid: str, *, feedback: str = "",
        material_id: str | None = None, run_id: str | None = None) -> dict:
    """Revise the theme set in the light of one newly read material. Returns
    {themes: [tid], merged: [tid]}."""
    proj = store.project(conn, pid)
    cap = ceiling(conn, pid)
    system, user = llm.prompt(
        "themes",
        material=_material_block(conn, material_id),
        themes=_themes_block(conn, store.live_themes(conn, pid)),
        codebook=_codebook_block(conn, pid),
        focus=_verbatim(proj["focus"], "The researcher has not said what they are looking for. "
                                       "Group the codes on their own terms."),
        feedback=_verbatim(feedback, "The researcher has said nothing about the themes."),
        max_themes=cap)
    out = llm.chat_json(system, user, label="themes")

    by_name = {r["name"]: r["id"] for r in store.codebook(conn, pid)}
    live = {r["id"] for r in store.live_themes(conn, pid)}
    payload = [t for t in (out.get("themes") or []) if isinstance(t, dict)]

    # Merges first. With the set at its cap, 'merge A into B and add C' used to drop C —
    # the cap was checked before A had gone — so a full theme set could only ever shrink,
    # and a researcher's 'split this' did nothing, silently.
    merged: list[str] = []
    for t in [t for t in payload if t.get("merge_into")]:
        tid, into = t.get("id"), t.get("merge_into")
        if tid in live and into in live and tid != into:
            store.merge_theme(conn, tid, into)     # marked merged, its moments follow the target
            live.discard(tid)
            merged.append(tid)

    saved: list[str] = []
    for t in [t for t in payload if not t.get("merge_into")]:
        name = name_of(t.get("name"))
        if not name:
            continue
        tid = t.get("id")
        if tid in merged:
            continue                       # merged away this pass; not re-created
        if t.get("new") or tid not in live:
            tid = None
        if tid is None and len(live) >= cap:
            continue
        names = t.get("code_names") or []
        tid = store.save_theme(conn, pid, tid=tid, name=name, run_id=run_id,
                               gist=str(t.get("gist") or "").strip(),
                               code_ids=[by_name[n] for n in
                                         ([names] if isinstance(names, str) else names)
                                         if n in by_name])
        live.add(tid)
        saved.append(tid)

    return {"themes": saved, "merged": merged}
