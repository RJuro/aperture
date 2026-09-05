"""READ — one piece of material becomes codes (L2 in the plan's §1).

The model is shown the brief, the researcher's focus in their own words, the live codebook, what
this material is and who speaks in it, and the material itself laid out the way its frame says it
should be — always as numbered sentence ids, because a code that cannot cite is a code that
cannot be checked. Where the project explores rather than building iteratively, the codebook is
the one thing it is not shown: that is the whole of the difference, and `MODE_RULE` is it.

Python rules on what comes back: a sentence id that is not in *this* material is dropped and
reported, the caps in the prompt are the caps enforced here, and a name may appear once. The
codes themselves are handed to `store.save_codes`, which owns reuse-by-name — nothing here
copies a payload field by field into a column list.
"""
from __future__ import annotations

import sqlite3

from .. import llm, store

MAX_CODES = 60      # codes accepted from one call
MAX_NEW = 12        # floor; the real cap scales with the material — see new_cap()

# What conditions the reading, by the project's method. An exploratory project shows the reading no
# project vocabulary at all, so the rule that tells it to reuse a name would be asking it to guess
# at names it cannot see; comparing what it made with the project's codes is a step of its own,
# after this one. An iterative project keeps the rule exactly as it has always stood.
MODE_RULE = {
    "explore": "Name codes for what this material says. You are shown no project codes; do not "
               "guess at them.",
    "iterative": "Reuse before you invent: if a code already in the codebook covers a passage, "
                 "cite it by its exact name as a plain string and make no second code for the "
                 "same idea.",
}
NO_CODEBOOK = ("No project vocabulary is shown for this reading: code this material on its own "
               "terms.")


def new_cap(n_passages: int) -> int:
    """How many new codes one material may found. Twelve was a fixed ceiling and it made the
    whole pyramid narrow at the base: a 433-passage interview yielded eleven codes, two
    interviews eighteen, six themes of three codes each. Roughly one new code per dozen
    passages, never fewer than fifteen, never more than fifty."""
    return max(15, min(50, n_passages // 12))


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


def _angles_block(conn: sqlite3.Connection, mid: str) -> str:
    """What the ideation step said might be worth looking for here.

    Places to look, never things to find. The reading is told so in the prompt, and the material
    is still the only thing that can put a code on the page. A material read before this step
    existed simply has none, and reads as it always did.
    """
    row = store.get_summary(conn, "material", mid, "angles")
    return (row["text"] if row and row["text"].strip() else
            "No angles were worked out for this material. Read it on its own terms.")


def run(conn: sqlite3.Connection, mid: str, *, feedback: str = "") -> dict:
    """Code one material. Returns {new, reused, hits, dropped_sids}.

    What the reading is shown depends on the project's method. An exploratory project shows it no
    codebook: the material is coded on its own terms, and RECONCILE compares what it made with the
    project's vocabulary afterwards. An iterative project shows it the codebook, as before. Either
    way the codes belong to the project — the codebook is one table for the whole of it — and the
    difference is only what this reading was allowed to see.

    `feedback` is the researcher's own words about this reading, verbatim, when they have
    asked for it to be read again. A reading that replaces this one replaces its hits too:
    left in place, the old ones would be counted beside the new in every code and theme.

    The old hits are cleared at the END, in the same transaction that writes the new ones. They
    used to be cleared before the call went out, so a 429 or a timeout took the previous coding
    with it and left the material uncoded — and every theme that gathered a code left with
    nothing lost the link as well. A reading that fails now leaves the reading before it exactly
    as it was.
    """
    m = store.material(conn, mid)
    pid = m["project_id"]
    proj = store.project(conn, pid)
    rows = store.sentence_rows(conn, mid)
    segments = store.segments(conn, mid)
    explore = proj["method"] == "explore"

    system, user = llm.prompt(
        "read",
        focus=_verbatim(proj["focus"], "The researcher has not said what they are looking for. "
                                       "Read this material on its own terms."),
        mode_rule=MODE_RULE["explore" if explore else "iterative"],
        codebook=NO_CODEBOOK if explore else _codebook_block(store.codebook(conn, pid)),
        frame=_frame_block(m, store.speakers(conn, mid), segments),
        material=_material_block(m, rows, segments),
        angles=_angles_block(conn, mid),
        feedback=_verbatim(feedback, "The researcher has said nothing about this reading."),
        max_codes=MAX_CODES, max_new=new_cap(len(rows)))
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
        if (is_new and n_new >= new_cap(len(rows))) or len(kept) >= MAX_CODES:
            continue
        n_new += is_new
        c["sids"] = sids
        kept[c["name"]] = c

    with store.atomic(conn) as tx:
        store.clear_hits(tx, pid, mid)
        saved = store.save_codes(tx, pid, mid, list(kept.values()), origin="read")
    return dict(saved, dropped_sids=dropped)
