"""ACCOUNT — what one theme amounts to across every material that carries it.

Between the reading of one material and the summary of a whole project there was nothing that
gathered one theme's claims ACROSS materials. A theme was a name and forty words of gist, and at
fifty materials it would rest on some four hundred and fifty claims and still be forty words. Two
things followed, both measured on a fifty-material corpus: the project page had to render every
claim, because there was nothing smaller to render, and the PROJECT prompt had to read every
claim, because there was nothing smaller to read.

So: one run per theme, reading only that theme's claims, and what it writes is what the level
above can read instead of the claims themselves.

Two laws hold this module, and both of them are `synth.project`'s:

    no quotes of its own                at this level there is no material in front of the model.
                                        Its statements rest on claims already checked against the
                                        material they came from, cited by id in brackets.
    a citation to nothing is removed    and reported. `synth._strip_dangling` does it, so this
                                        level and the project level cannot drift into two
                                        conventions for one rule. What is shown to the model here
                                        is one theme's live claims, so the same pass also rejects
                                        an id borrowed from a neighbouring theme.

The absence is half of what this level is for. A theme that does not appear in nine of fifty
materials has said something about those nine, so they are named in the prompt and the model is
asked what their silence means. Python cannot search for what is not there (PLAN.md §3.2) — but
it can say exactly where it did not look, which is what `coverage` returns.

CLAIMS_SHOWN is what keeps this prompt flat. The budget is divided evenly over the materials that
carry the theme, so the prompt stops growing where the corpus does not: at two materials every
claim is shown, at fifty each material shows three, and every material is named and counted
either way. Each block prints its own derivation — `3 of 9 claims shown` — because a model told
only the three would weigh them as if they were all there was.
"""
from __future__ import annotations

import sqlite3

from .. import llm, store
from . import synth

ACCOUNT_WORDS_MIN, ACCOUNT_WORDS = 250, 350
GIST_WORDS = 40
CLAIMS_SHOWN = 150

# One pass over every material in the project, with this theme's live claims counted against it.
# A LEFT JOIN, not a loop: the materials with none are the ones this level most needs to name,
# and a per-material query would have to know to ask about them.
_COVERAGE = """
SELECT m.id AS material_id, m.name AS name, m.title AS title, m.kind AS kind,
       COUNT(mo.id) AS claims
  FROM material m
  LEFT JOIN moment mo ON mo.material_id = m.id AND mo.theme_id = ? AND mo.status = 'live'
 WHERE m.project_id = ?
 GROUP BY m.id
 ORDER BY m.created_at, m.id
"""

_CLAIMS = """
SELECT mo.id AS id, mo.material_id AS material_id, mo.claim AS claim, mo.anchor AS anchor
  FROM moment mo
  JOIN material m ON m.id = mo.material_id
 WHERE m.project_id = ? AND mo.theme_id = ? AND mo.status = 'live'
 ORDER BY m.created_at, m.id, mo.position
"""


def coverage(conn: sqlite3.Connection, pid: str, theme_id: str) -> dict:
    """The parts a page prints its derivation from: how many materials carry this theme out of how
    many, how many claims in all, and the count under every material including the zeroes.

    No percentage, by law (PLAN.md §3.4) — a page shows *"in 12 of 50 materials"* over rows it
    links to, and 24% is a number nobody can open.
    """
    rows = [dict(r) for r in conn.execute(_COVERAGE, (theme_id, pid))]
    return {"materials_with": sum(1 for r in rows if r["claims"]),
            "materials_total": len(rows),
            "claims": sum(r["claims"] for r in rows),
            "per_material": rows}


def _spread(rows: list, k: int) -> list:
    """`k` claims drawn evenly from across a material rather than the first `k` of them. The first
    three claims of a long line are all from its opening — the same defect the reading prompt
    warns about, one level up."""
    if k >= len(rows):
        return rows
    step = len(rows) / k
    return [rows[int(i * step)] for i in range(k)]


def _blocks(rows: list, carrying: list[dict]) -> tuple[str, int]:
    """One block per material that carries the theme, each headed by its own derivation."""
    by_material: dict[str, list] = {}
    for r in rows:
        by_material.setdefault(r["material_id"], []).append(r)

    if not carrying:                    # no material carries this theme; nothing to lay out
        return "", 0
    per, extra = divmod(CLAIMS_SHOWN, len(carrying))
    out, held_back = [], 0
    for i, m in enumerate(carrying):
        mine = by_material.get(m["material_id"], [])
        shown = _spread(mine, per + (1 if i < extra else 0))
        held_back += len(mine) - len(shown)
        count = (f'{len(shown)} of {m["claims"]} claims shown' if len(shown) < m["claims"]
                 else f'{m["claims"]} claims')
        head = f'## {m["title"] or m["name"]} — {m["kind"] or "kind not worked out"} — {count}'
        out.append("\n".join([head] + [f'[{r["id"]}] {r["claim"]} — quoted: "{r["anchor"]}"'
                                       for r in shown]))
    return "\n\n".join(out), held_back


def run(conn: sqlite3.Connection, pid: str, theme_id: str, *,
        run_id: str | None = None) -> dict:
    """What this theme amounts to across the corpus, and a gist rewritten to match.

    Returns {text, gist, dropped, coverage}. The prose is stored against the theme, and the gist
    goes through `store.set_theme_gist` — `save_theme` also rewrites which codes a theme gathers,
    and this level has never been told which codes belong where, so writing a gist through it
    would quietly empty the theme.
    """
    cover = coverage(conn, pid, theme_id)
    live_themes = {t["id"]: t for t in store.live_themes(conn, pid)}
    if theme_id not in live_themes:
        # Merged away between the run being queued and the run happening. Say so; do not spend a
        # call writing about a theme the project no longer has.
        return {"text": "", "gist": "", "coverage": cover,
                "dropped": [f"theme {theme_id} is not live in this project — "
                            "no account was written"]}

    theme = live_themes[theme_id]
    carrying = [m for m in cover["per_material"] if m["claims"]]
    absent = [m for m in cover["per_material"] if not m["claims"]]
    if not carrying:
        return {"text": "", "gist": "", "coverage": cover,
                "dropped": [f'no claim in this project rests on "{theme["name"]}" yet — '
                            "there is nothing to write an account from"]}

    rows = [dict(r) for r in conn.execute(_CLAIMS, (pid, theme_id))]
    materials, held_back = _blocks(rows, carrying)

    reach = (f'It runs through {cover["materials_with"]} of the '
             f'{cover["materials_total"]} materials in this project, '
             f'{cover["claims"]} claims in all')
    reach += f", of which {cover['claims'] - held_back} are shown below." if held_back else "."
    proj = store.project(conn, pid)

    system, user = llm.prompt(
        "account",
        theme=f'"{theme["name"]}" — {theme["gist"] or "no gist yet"}\n{reach}',
        focus=(proj["focus"] if proj else "") or "Nothing in particular.",
        materials=materials,
        absent="\n".join(f'{m["title"] or m["name"]} — {m["kind"] or "kind not worked out"}'
                         for m in absent)
        or "None. Every material in this project carries this theme somewhere.",
    )
    data = llm.chat_json(system, user, label="account")

    # Everything live under this theme, whether or not it was shown: the citations the model can
    # legitimately make. Anything else — invented, superseded, or another theme's — goes.
    live = {r["id"]: r for r in rows}
    text, gone = synth._strip_dangling(synth.words(data.get("account"), ACCOUNT_WORDS), live)

    dropped = []
    if gone:
        dropped.append(f"the account cited {len(gone)} id(s) that are not live claims under this "
                       f"theme — {', '.join(sorted(set(gone)))} — and those citations were removed")
    if held_back:
        dropped.append(f"{held_back} of {cover['claims']} claims were not shown to the model: "
                       f"{CLAIMS_SHOWN} is the most it reads at once, divided evenly over the "
                       f"{len(carrying)} materials that carry this theme")
    if not text:
        dropped.append("the account came back empty and nothing was stored")
    elif len(text.split()) < ACCOUNT_WORDS_MIN:
        dropped.append(f"the account came back at {len(text.split())} words, under the "
                       f"{ACCOUNT_WORDS_MIN} asked for")

    if text:
        store.save_summary(conn, "theme", theme_id, "reading", text, run_id)
    gist = synth.words(data.get("gist"), GIST_WORDS)
    if gist:
        store.set_theme_gist(conn, theme_id, gist)

    return {"text": text, "gist": gist, "dropped": dropped, "coverage": cover}
