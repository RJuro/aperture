"""THEMES — the codebook becomes themes, across the whole project (L3 in the plan's §1).

The model is shown the themes that are live now with the codes they gather, the codebook with
how often each code was hit in each material — which is how it can see what spans the corpus and
what belongs to one interview only — the researcher's focus, and any feedback on the themes in
the researcher's own words.

Python rules on what comes back: a code name that is not in the codebook is ignored, no more
themes stay live than the corpus can populate (`ceiling`), and a theme the model wants folded into
another is *merged*, never deleted — a moment that cited it must still resolve to something.

Since PLAN.md §12 the set stands in three holds and the rules differ per hold, which is why the
enforcement below runs in one fixed order — merges, then the project themes, then the candidates,
then the tensions. A frozen theme's words are fixed HERE, in Python: the prompt asks the model to
leave them alone, and a rule the model must obey is weaker than one it cannot break.
"""
from __future__ import annotations

import hashlib
import sqlite3

from .. import llm, store

MAX_THEMES = 12

# How many candidates one pass may coin. Candidates never count against the ceiling — a pattern
# seen once is not a category — so this is the only thing bounding them, and four is about what
# one material can honestly add.
MAX_NEW = 4

# A tension is a pointer, not an argument: enough to say what pulled and which way.
TENSION_WORDS = 25

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


def _themes_block(conn: sqlite3.Connection, rows: list[sqlite3.Row],
                  where: bool = False) -> str:
    """One of the three blocks the set is partitioned into. `where` adds the material a candidate
    was seen in — by id and by title, because an id on its own names nothing to a reader."""
    if not rows:
        return "None."
    out = []
    for t in rows:
        codes = ", ".join(c["name"] for c in store.theme_codes(conn, t["id"])) or "no codes yet"
        line = f'- id {t["id"]} · "{t["name"]}" — {t["gist"] or "no gist yet"}'
        if where:
            line += f'\n  seen in: {_seen_in(conn, t["id"])}'
        out.append(line + f"\n  gathers: {codes}")
    return "\n".join(out)


def _seen_in(conn: sqlite3.Connection, tid: str) -> str:
    """Which material a candidate came from: where the codes it gathers were actually marked.

    Not where its moments are. A candidate coined in this pass has no line under it yet — DOC
    writes those afterwards — and the one thing already true of it is that this material's
    reading marked the codes it gathers.
    """
    said = []
    for r in conn.execute("SELECT DISTINCT h.material_id AS mid FROM theme_code tc "
                          "JOIN code_hit h ON h.code_id = tc.code_id WHERE tc.theme_id=?", (tid,)):
        if m := store.material(conn, r["mid"]):
            said.append(f'{m["id"]} ({m["title"] or m["name"]})')
    return ", ".join(said) or "no material yet"


def ceiling_text(live: int, cap: int) -> str:
    """The ceiling slot: where the project stands against its cap, and what to do when it is over.

    Over-cap is asked for, never enforced. A project that reached twelve under the old ceiling
    cannot be cut to eight by Python without Python choosing which themes are lost; the model is
    told the number and asked to fold, and a fold carries its lines with it.
    """
    if live > cap:
        return (f"{live} project themes are live and the ceiling is {cap}: merge until at most "
                f"{cap} remain, folding the theme that gathers fewest codes into its nearest.")
    return f"{live} project themes are live."


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


def _code_ids(t: dict, by_name: dict[str, str]) -> list[str]:
    names = t.get("code_names") or []
    return [by_name[n] for n in ([names] if isinstance(names, str) else names) if n in by_name]


def _fingerprint(conn: sqlite3.Connection, t: sqlite3.Row) -> str:
    """What "this theme did not change" means: its words and what it gathers, nothing else."""
    codes = sorted(c["id"] for c in store.theme_codes(conn, t["id"]))
    parts = [t["name"], t["gist"] or "", *codes]
    return hashlib.sha256("\x1f".join(parts).encode()).hexdigest()[:16]


def run(conn: sqlite3.Connection, pid: str, *, feedback: str = "",
        material_id: str | None = None, run_id: str | None = None) -> dict:
    """Revise the theme set in the light of one newly read material. Returns
    {themes: [tid], merged: [tid]} — `themes` being every theme this pass wrote, candidates
    included."""
    proj = store.project(conn, pid)
    cap = ceiling(conn, pid)
    project_themes = store.live_themes(conn, pid)
    cands = store.candidates(conn, pid)
    system, user = llm.prompt(
        "themes",
        material=_material_block(conn, material_id),
        frozen=_themes_block(conn, [t for t in project_themes if t["hold"] == "frozen"]),
        open=_themes_block(conn, [t for t in project_themes if t["hold"] == "open"]),
        candidates=_themes_block(conn, cands, where=True),
        codebook=_codebook_block(conn, pid),
        focus=_verbatim(proj["focus"], "The researcher has not said what they are looking for. "
                                       "Group the codes on their own terms."),
        feedback=_verbatim(feedback, "The researcher has said nothing about the themes."),
        max_themes=cap, ceiling=ceiling_text(len(project_themes), cap), max_new=MAX_NEW)
    out = llm.chat_json(system, user, label="themes")

    by_name = {r["name"]: r["id"] for r in store.codebook(conn, pid)}
    rows = {t["id"]: t for t in list(project_themes) + list(cands)}
    payload = [t for t in (out.get("themes") or []) if isinstance(t, dict)]

    # Merges first. With the set at its cap, 'merge A into B and add C' used to drop C —
    # the cap was checked before A had gone — so a full theme set could only ever shrink,
    # and a researcher's 'split this' did nothing, silently.
    merged: list[str] = []
    for t in [t for t in payload if t.get("merge_into")]:
        tid, into = t.get("id"), t.get("merge_into")
        if tid not in rows or into not in rows or tid == into:
            continue                       # a target that is not live folds a theme into nothing
        if rows[tid]["hold"] == "frozen":
            continue                       # the researcher declared it final; it is not folded away
        store.merge_theme(conn, tid, into)         # marked merged, its moments follow the target
        rows.pop(tid)
        merged.append(tid)

    saved: list[str] = []
    # Then the project themes, and whatever came back in `themes` that is not one. A `new` theme
    # or an id nobody recognises is a pattern seen in this material and nowhere else, which is a
    # candidate — the model does not get to coin a project theme, because recurrence does that.
    leftover: list[dict] = []
    for t in [t for t in payload if not t.get("merge_into")]:
        tid = t.get("id")
        if tid in merged:
            continue                       # merged away this pass; not re-created
        row = None if t.get("new") else rows.get(tid)
        if row is None or row["hold"] == "candidate":
            leftover.append(t)
            continue
        frozen = row["hold"] == "frozen"
        # A frozen theme keeps the words the researcher froze, whatever came back for it; what
        # this material does to it is gathered as codes and said in `tensions`.
        name = row["name"] if frozen else name_of(t.get("name"))
        gist = row["gist"] if frozen else str(t.get("gist") or "").strip()
        if not name:
            continue
        store.save_theme(conn, pid, tid=tid, name=name, gist=gist, run_id=run_id,
                         code_ids=_code_ids(t, by_name))
        saved.append(tid)

    coined = 0
    for t in leftover + [t for t in (out.get("candidates") or []) if isinstance(t, dict)]:
        row = None if t.get("new") else rows.get(t.get("id"))
        if row is not None and row["hold"] == "candidate":
            # This material confirms a candidate from another one: its codes are gathered, its
            # words are left alone — rule 15, so that a candidate is not reworded to fit.
            # Added to what it already gathers, never replacing it: the answer names only the
            # codes THIS material carries, and a candidate that lost the codes it was coined
            # from would stop being marked in the material it came from.
            have = {c["id"] for c in store.theme_codes(conn, row["id"])}
            store.save_theme(conn, pid, tid=row["id"], name=row["name"], gist=row["gist"],
                             run_id=run_id,
                             code_ids=sorted(have | set(_code_ids(t, by_name))))
            saved.append(row["id"])
        elif coined < MAX_NEW and (name := name_of(t.get("name"))):
            tid = store.save_theme(conn, pid, tid=None, name=name, run_id=run_id,
                                   gist=str(t.get("gist") or "").strip(),
                                   code_ids=_code_ids(t, by_name))
            store.set_hold(conn, tid, "candidate")
            coined += 1
            saved.append(tid)

    # Tensions, for frozen themes only: they are the one hold whose definition Python refuses to
    # move, so they are also the one hold that needs somewhere for the pull to go.
    from . import synth
    for t in [t for t in (out.get("tensions") or []) if isinstance(t, dict)]:
        row = rows.get(t.get("id"))
        if row is None or row["hold"] != "frozen":
            continue
        if note := synth.words(t.get("note"), TENSION_WORDS):
            store.add_theme_note(conn, row["id"], material_id, run_id, note)

    # The saturation signal (PLAN.md §12), bookkeeping only: how many passes in a row this theme's
    # words and codes stood still. The researcher reads it and freezes; the instrument only counts.
    # Candidates are not counted — a pattern seen once cannot be stable.
    for t in store.live_themes(conn, pid):
        fp = _fingerprint(conn, t)
        conn.execute("UPDATE theme SET stable_passes=?, pass_fingerprint=? WHERE id=?",
                     (t["stable_passes"] + 1 if fp == t["pass_fingerprint"] else 0, fp, t["id"]))
    conn.commit()

    return {"themes": saved, "merged": merged}
