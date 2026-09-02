"""READ — one piece of material becomes codes (L2 in the plan's §1).

The model is shown the brief, the researcher's focus in their own words, the live codebook, what
this material is and who speaks in it, and the material itself laid out the way its frame says it
should be — always as numbered sentence ids, because a code that cannot cite is a code that
cannot be checked.

Python rules on what comes back: a sentence id that is not in *this* material is dropped and
reported, the caps in the prompt are the caps enforced here, and a name may appear once. The
codes themselves are handed to `store.save_codes`, which owns reuse-by-name — nothing here
copies a payload field by field into a column list.
"""
from __future__ import annotations

import sqlite3

from .. import llm, store

MAX_CODES = 40      # codes accepted from one call
MAX_NEW = 12        # of those, how many may be names the codebook has never seen


def _verbatim(text: str, empty: str) -> str:
    """The researcher's own words, delimited rather than reworded."""
    text = (text or "").strip()
    return f'"""\n{text}\n"""' if text else empty


def _codebook_block(rows: list[sqlite3.Row]) -> str:
    if not rows:
        return "The codebook is empty. Every code you make here is a new one."
    return "\n".join(f"- {r['name']} — {r['definition'] or 'no definition recorded'}"
                     for r in rows)


def _frame_block(m: sqlite3.Row, speakers: list[sqlite3.Row],
                 segments: list[sqlite3.Row]) -> str:
    out = [f"This material is: {m['kind'] or 'not yet described'}",
           f"Its title: {m['title'] or m['name']}",
           f"It is laid out as: {m['display'] or 'plain'}"]
    if speakers:
        out.append("Who speaks in it:")
        out += [f"- {s['label']} — {s['name'] or s['label']} ({s['role'] or 'other'})"
                for s in speakers]
    else:
        out.append("Nobody is marked as speaking in it: it is not a transcript of speech.")
    if segments:
        out.append("Its sections, in order: " + ", ".join(s["label"] for s in segments))
    return "\n".join(out)


def _material_block(m: sqlite3.Row, rows: list[sqlite3.Row],
                    segments: list[sqlite3.Row]) -> str:
    """Numbered sentences, grouped the way the material's own shape asks for."""
    display = m["display"] or "plain"
    if display == "turns":
        out, turn = [], object()
        for r in rows:
            if r["turn_idx"] != turn:
                turn = r["turn_idx"]
                out.append(f"\n[{r['speaker']}]" if r["speaker"] else "\n[no speaker]")
            out.append(f"{r['sid']}  {r['text']}")
        return "\n".join(out).strip()
    if display == "segments" and segments:
        heads = {s["sid"]: s["label"] for s in segments}
        out = []
        for r in rows:
            if r["sid"] in heads:
                out.append(f"\n## {heads[r['sid']]}")
            out.append(f"{r['sid']}  {r['text']}")
        return "\n".join(out).strip()
    return "\n".join(f"{r['sid']}  {r['text']}" for r in rows)


def _code_of(entry: dict) -> dict:
    """`code` is either an existing name or `{name, definition}`; a flat entry is tolerated too."""
    c = entry.get("code", entry)
    if isinstance(c, str):
        return {"name": c.strip(), "definition": ""}
    if not isinstance(c, dict):
        return {"name": "", "definition": ""}
    return {"name": str(c.get("name") or "").strip(),
            "definition": str(c.get("definition") or "").strip()}


def _sids_of(entry: dict, valid: set[str], dropped: list[str]) -> list[str]:
    raw = entry.get("sids") or []
    if isinstance(raw, str):
        raw = [raw]
    out = []
    for s in raw:
        s = str(s).strip()
        if s in valid:
            if s not in out:
                out.append(s)
        elif s and s not in dropped:
            dropped.append(s)
    return out


def run(conn: sqlite3.Connection, mid: str) -> dict:
    """Code one material. Returns {new, reused, hits, dropped_sids}."""
    m = store.material(conn, mid)
    pid = m["project_id"]
    proj = store.project(conn, pid)
    rows = store.sentence_rows(conn, mid)
    segments = store.segments(conn, mid)

    system, user = llm.prompt(
        "read",
        brief=(proj["brief"] or "").strip()
              or "Nothing has been written about this corpus yet; this is an early reading.",
        focus=_verbatim(proj["focus"], "The researcher has not said what they are looking for. "
                                       "Read this material on its own terms."),
        codebook=_codebook_block(store.codebook(conn, pid)),
        frame=_frame_block(m, store.speakers(conn, mid), segments),
        material=_material_block(m, rows, segments),
        max_codes=MAX_CODES, max_new=MAX_NEW)
    out = llm.chat_json(system, user, label="read")

    valid = {r["sid"] for r in rows}
    known = {r["name"] for r in store.codebook(conn, pid)}
    dropped: list[str] = []
    kept: dict[str, dict] = {}
    n_new = 0
    for entry in out.get("codes") or []:
        if not isinstance(entry, dict):
            continue
        c = _code_of(entry)
        sids = _sids_of(entry, valid, dropped)
        if not c["name"] or not sids:
            continue
        if c["name"] in kept:                       # names are unique; the hits are not lost
            kept[c["name"]]["sids"] += [s for s in sids if s not in kept[c["name"]]["sids"]]
            continue
        is_new = c["name"] not in known
        if (is_new and n_new >= MAX_NEW) or len(kept) >= MAX_CODES:
            continue
        n_new += is_new
        c["sids"] = sids
        kept[c["name"]] = c

    return dict(store.save_codes(conn, pid, mid, list(kept.values()), origin="read"),
                dropped_sids=dropped)
