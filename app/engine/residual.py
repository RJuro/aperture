"""RESIDUAL — what the coding did not mark, read once (PLAN.md §13).

The gate of §3 law 2 is on for an exploratory project: a theme is followed through a material only
where the codes it gathers fired there. That buys most of DOC's cost and it leaves a hole — the
passages no code touched are the ones nothing has read for anything, and "not looked for" is the
weakest of the four things the record can say about a theme in a material.

So one call per material after its lines: the unmarked passages, the theme set, and the memo. What
comes back is either an addition — a claim under an existing theme, anchored and verified like any
moment — or `none_for`, which is the finding this step mostly exists to produce:

    residual   the gate passed this theme over, and the passages the coding did not mark hold
               nothing under it either. An absence that was SEARCHED, cheaper than a THREAD call
               and stronger than "not looked for"

A theme that was looked for properly is left alone here. `residual` is only ever written over
`skipped`: this pass read the remainder, not the material, and it cannot upgrade a line that a
reader was already sent to find and did not.
"""
from __future__ import annotations

from .. import anchor, llm, store
from . import check, synth, verify

# What the note may cost the reader. The prompt asks for 40 words and this is the guard.
NOTE_WORDS = 40


def themes_block(conn, pid: str, mid: str) -> tuple[str, dict]:
    """The theme set this pass may add to: the project's themes and this material's candidates.

    Ids and gists only. The lines already written are not shown — the memo says what the reading
    found, and showing the claims as well would invite the same passage back under a second name.
    """
    rows = {t["id"]: t for t in
            list(store.live_themes(conn, pid)) + list(store.candidates(conn, pid, mid))}
    block = "\n".join(f'{t["id"]}  {t["name"]} — {t["gist"] or "no gist yet"}'
                      for t in rows.values())
    return block or "No themes yet. Return no additions.", rows


def run(conn, mid: str, *, run_id: str | None = None) -> dict:
    """Read this material's unmarked passages against its themes. Returns
    {additions, none_for, note, dropped}."""
    row = store.material(conn, mid)
    if row is None:
        raise ValueError(f"no material {mid!r}")
    pid = row["project_id"]
    # The passages no CODE touched — not the ones no claim rests on (`store.uncited`), which is a
    # different remainder and a different question. This one asks what the coding itself missed.
    marked = {h["sid"] for h in store.hits(conn, mid)}
    unmarked = [(sid, text) for sid, text in store.sentences(conn, mid) if sid not in marked]
    block, themes = themes_block(conn, pid, mid)
    if not unmarked or not themes:
        return {"additions": [], "none_for": [], "note": "", "dropped": []}

    memo = store.get_summary(conn, "material", mid, "memo")
    nums, stats = synth.numbers(unmarked), anchor.new_stats()
    additions: list[dict] = []
    none_for: set[str] = set(themes)
    note, dropped = "", []
    # Chunked exactly as CHECK chunks a search of the same kind of remainder, and the answers
    # merged: one call is the ordinary case and only a very long material is split.
    for part in check.chunks(unmarked):
        system, user = llm.prompt(
            "residual", themes=block,
            memo=memo["text"] if memo else "No memo was written for this material.",
            unmarked="\n".join(f"{sid}  {text}" for sid, text in part))
        data = llm.chat_json(system, user, label="residual")
        for a in data.get("additions") or []:
            if not isinstance(a, dict):
                continue
            tid = str(a.get("theme") or "")
            claim = synth.words(a.get("claim"), synth.CLAIM_WORDS)
            quote = str(a.get("anchor") or "").strip()
            if tid not in themes:
                dropped.append(f'an addition named a theme this project does not have: "{tid}"')
                continue
            # The anchor law, against the UNMARKED passages only: a quote found in a passage the
            # coding already marked is not something the coding missed.
            bound = anchor.apply(a, [synth.cited(a.get("sid"), nums)], part, stats)
            if not claim:
                dropped.append(f'an addition with no claim was dropped (quote: "{synth.clip(quote)}")')
                continue
            if bound is None:
                dropped.append(
                    "an addition was dropped: its quote is not in the passages the coding left "
                    f'unmarked — "{synth.clip(quote)}"' if quote else
                    "an addition was dropped: it carried no quote")
                continue
            additions.append({"theme_id": tid, "claim": claim, "anchor": bound[0],
                              "sid": bound[1][0]})
        # A theme the answer added to is not one the remainder held nothing under, whichever chunk
        # said so — `none_for` is about the material, and each call sees only part of it.
        none_for &= {str(t) for t in (data.get("none_for") or []) if str(t) in themes}
        note = note or synth.words(data.get("note"), NOTE_WORDS)

    return _apply(conn, mid, additions, none_for, note, run_id=run_id, dropped=dropped)


def _apply(conn, mid: str, additions: list[dict], none_for: set[str], note: str, *,
           run_id: str | None, dropped: list[str]) -> dict:
    """What the answer does to the record: the moments, their check, and the four-way outcome."""
    by_theme: dict[str, list[dict]] = {}
    for a in additions:
        by_theme.setdefault(a["theme_id"], []).append(a)
    # A theme this pass found something under is not one it found nothing under, whatever the
    # answer's own list says.
    none_for -= set(by_theme)
    ids: list[str] = []
    for tid, ms in by_theme.items():
        # Added beside the line that stands, never replacing it: it was written and checked
        # minutes ago, and superseding it would give every claim of it a new id.
        ids += store.add_moments(conn, mid, tid, ms, run_id)
    if ids:
        dropped += verify.run(conn, mid, ids=ids, run_id=run_id)["dropped"]

    outcomes = store.followed(conn, store.material(conn, mid)["project_id"])
    for tid in by_theme:
        # 'line' only where something survived the check; a theme whose every addition was set
        # aside is left saying whatever it said before this pass.
        if store.thread(conn, mid, tid):
            store.save_follow(conn, mid, tid, "line", run_id)
    for tid in sorted(none_for):
        # Only over a skip. A theme a reader was sent to find and did not find is 'thin', and this
        # pass read the remainder rather than the material: it cannot say more about that theme
        # than the reader who looked already did.
        if outcomes.get((tid, mid)) == "skipped":
            store.save_follow(conn, mid, tid, "residual", run_id)
    if note:
        store.save_summary(conn, "material", mid, "residual", note, run_id)
    return {"additions": additions, "none_for": sorted(none_for), "note": note,
            "dropped": dropped}
