"""SCREEN — one look at a material's own account and its coding, deciding where a reading goes.

The back-fill of PLAN.md §14 sends a THREAD call into a material for every cell nobody had read.
On an eight-material corpus that was forty-five cells, and every one of those calls sends the
whole material again to ask a question most of them answer with nothing. This is the cheap look
before the expensive one: ONE call per material, shown that material's account and every passage
its coding marked, deciding a batch of themes at once.

It is deliberately NOT the code gate that docs/EVAL.md pass 3 measured and rejected. That gate
counted code hits and skipped the cell when the count was zero — twelve zero-hit cells, nine of
which still produced lines and four of those among the best in the set. A count knows nothing
about what the material says; this call reads the material's own account of itself and the
passages its reading marked, and rule 4 of the prompt puts every doubtful case on the expensive
side. Python enforces that default rather than trusting it: a theme the answer omits, or gives a
verdict nobody can read, is looked for.

What it writes is a fifth follow outcome, `screened`, and the words the look gave for passing the
theme over. It is weaker than 'looked for and found too thin' — nobody went to the material — and
stronger than 'not looked for here', where nothing looked at all. Every surface that states an
absence says which, and the account prompt is told it may not read this one as absence.
"""
from __future__ import annotations

from .. import llm, store
from . import memo, synth

# What the look is shown of the coding. Enough to recognise what a code is about and that it fired
# more than once, and no more: this call exists to be cheap, and a block that reprints half the
# material has given the saving back.
PASSAGES_PER_CODE = 4
CODES_SHOWN = 60

# The prompt asks for at most fifteen words of why; this is what Python holds it to.
WHY_WORDS = 15

# Which account of the material the look is shown, best first, and what to say above it. A memo is
# written over the passages the coding marked; a reading summary over the lines the synthesis
# wrote; an orientation is what was said about the material before anybody read it, and a look
# working from one is being told less than the other two — so it says so.
ACCOUNTS = (
    ("memo", "This is what the reading of this material found, written over the passages its "
             "coding marked."),
    ("reading", "This is what the reading of this material found, written over the lines the "
                "synthesis wrote."),
    ("orientation", "Nobody has written up what the reading found here yet. This is only what "
                    "the material was taken to be before it was read."),
)


def account_block(conn, mid: str) -> str:
    """This material's own account of itself, saying which kind of account it is.

    Which one exists depends on the method and on how far the chain has come, and the three are
    not equally strong. A look that cannot tell an orientation from a memo would weigh a guess
    made before the reading exactly as it weighs the reading's own conclusion.
    """
    for stage, said in ACCOUNTS:
        row = store.get_summary(conn, "material", mid, stage)
        if row and (row["text"] or "").strip():
            return f"{said}\n\n{row['text']}"
    return "Nothing has been written about this material yet — decide on the coding alone."


def themes_block(rows) -> str:
    return "\n".join(f'{r["id"]}  {r["name"]} — {r["gist"] or "no gist yet"}' for r in rows)


def run(conn, mid: str, theme_ids, *, run_id: str | None = None) -> dict:
    """Decide, in one call, which of these themes this material is worth reading for.

    Returns {"look": [theme id], "pass": [(theme id, why)], "dropped": [note]}. The `pass` themes
    have their follow row written here — `screened`, with the why — because that row is what makes
    the planned reading of that cell skippable and what every page prints instead of a claim. The
    `look` themes are written nowhere: their outcome is whatever the reading that follows finds.
    """
    if store.material(conn, mid) is None:
        raise ValueError(f"no material {mid!r}")
    wanted = list(dict.fromkeys(theme_ids))
    if not wanted:
        return {"look": [], "pass": [], "dropped": []}
    # Candidates as well as project themes — the back-fill reads for both — and by id, so a theme
    # merged away between the plan and this call is simply not decided on.
    found = {r["id"]: r for r in conn.execute(
        "SELECT id, name, gist FROM theme WHERE status='live' "
        f"AND id IN ({','.join('?' * len(wanted))})", wanted)}
    rows = [found[t] for t in wanted if t in found]
    if not rows:
        return {"look": [], "pass": [], "dropped": []}

    llm.report(f"deciding {len(rows)} themes from this material's account and its coding")
    data = llm.chat_json(*llm.prompt(
        "screen",
        frame=synth.frame_block(conn, mid),
        account=account_block(conn, mid),
        coded=memo.coded_block(conn, mid, per_code=PASSAGES_PER_CODE, codes=CODES_SHOWN),
        themes=themes_block(rows)), label="screen")

    said: dict[str, tuple[str, str]] = {}
    for v in (data.get("verdicts") if isinstance(data, dict) else None) or []:
        if not isinstance(v, dict):
            continue
        vid, verdict = str(v.get("id") or ""), str(v.get("verdict") or "").strip().lower()
        if vid in found and verdict in ("look", "pass"):
            said[vid] = (verdict, synth.words(v.get("why"), WHY_WORDS))

    look, passed, dropped = [], [], []
    for r in rows:
        verdict, why = said.get(r["id"], ("", ""))
        if verdict == "pass":
            passed.append((r["id"], why))
            continue
        # Rule 4's default, and it is Python's rather than the prompt's: an omitted theme, an
        # unreadable verdict and an answer that never came back all cost one line call, and a
        # theme quietly passed over on a silence costs a finding nobody will ever know was there.
        look.append(r["id"])
        if verdict != "look":
            dropped.append(f'the look said nothing that could be read about "{r["name"]}", so '
                           f'this material is read for it')
    # One transaction: these verdicts are one decision about this material, and a half-written one
    # would leave some cells cancelled and some planned by the same answer.
    if passed:
        with store.atomic(conn) as tx:
            for tid, why in passed:
                store.save_follow(tx, mid, tid, "screened", run_id, note=why)
    return {"look": look, "pass": passed, "dropped": dropped}
