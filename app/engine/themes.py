"""THEMES — the codebook becomes themes, across the whole project (L3 in the plan's §1).

The model is shown the themes that are live now with the codes they gather, the codebook with
how often each code was hit in each material — which is how it can see what spans the corpus and
what belongs to one interview only — the researcher's focus, and any feedback on the themes in
the researcher's own words.

Python rules on what comes back: a code name that is not in the codebook is ignored, no more than
`MAX_THEMES` themes stay live, and a theme the model wants folded into another is *merged*, never
deleted — a moment that cited it must still resolve to something.
"""
from __future__ import annotations

import sqlite3

from .. import llm, store

MAX_THEMES = 12


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
    codes = store.codebook(conn, pid)
    if not codes:
        return "The codebook is empty; nothing has been read yet."
    counts: dict[str, dict[str, int]] = {}
    for m in store.materials(conn, pid):
        label = m["title"] or m["name"]
        for h in store.hits(conn, m["id"]):
            counts.setdefault(h["id"], {})
            counts[h["id"]][label] = counts[h["id"]].get(label, 0) + 1
    out = []
    for c in codes:
        where = counts.get(c["id"]) or {}
        spread = ("; ".join(f"{k} {v}" for k, v in where.items())
                  if where else "no sentences yet")
        out.append(f"- {c['name']} — {c['definition'] or 'no definition recorded'}\n"
                   f"  found in: {spread}")
    return "\n".join(out)


def run(conn: sqlite3.Connection, pid: str, *, feedback: str = "") -> dict:
    """Group the codebook into themes. Returns {themes: [tid], merged: [tid]}."""
    proj = store.project(conn, pid)
    system, user = llm.prompt(
        "themes",
        themes=_themes_block(conn, store.live_themes(conn, pid)),
        codebook=_codebook_block(conn, pid),
        focus=_verbatim(proj["focus"], "The researcher has not said what they are looking for. "
                                       "Group the codes on their own terms."),
        feedback=_verbatim(feedback, "The researcher has said nothing about the themes."),
        max_themes=MAX_THEMES)
    out = llm.chat_json(system, user, label="themes")

    by_name = {r["name"]: r["id"] for r in store.codebook(conn, pid)}
    live = {r["id"] for r in store.live_themes(conn, pid)}
    payload = [t for t in (out.get("themes") or []) if isinstance(t, dict)]

    saved: list[str] = []
    for t in [t for t in payload if not t.get("merge_into")]:
        name = str(t.get("name") or "").strip()
        if not name:
            continue
        tid = t.get("id")
        if t.get("new") or tid not in live:
            tid = None
        if tid is None and len(live) >= MAX_THEMES:
            continue
        names = t.get("code_names") or []
        tid = store.save_theme(conn, pid, tid=tid, name=name,
                               gist=str(t.get("gist") or "").strip(),
                               code_ids=[by_name[n] for n in
                                         ([names] if isinstance(names, str) else names)
                                         if n in by_name])
        live.add(tid)
        saved.append(tid)

    merged: list[str] = []
    for t in [t for t in payload if t.get("merge_into")]:
        tid, into = t.get("id"), t.get("merge_into")
        if tid in live and into in live and tid != into:
            store.merge_theme(conn, tid, into)     # marked merged, its moments follow the target
            live.discard(tid)
            saved[:] = [s for s in saved if s != tid]
            merged.append(tid)

    return {"themes": saved, "merged": merged}
