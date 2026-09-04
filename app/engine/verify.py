"""VERIFY — does the passage say what the claim says?

The anchor law (PLAN.md §3.1) rules that the quote is really there. It cannot rule on what was
built on top of it, and that is where the worst of a real three-interview run went wrong: "he
took factory work without complaint" over a passage saying only that he got a job in a factory,
"she adapted well" over a passage saying she made others adapt. The quote was verbatim, the
citation was right, and the claim carried a manner the material never contained. It is the one
failure a reader cannot catch without going back to the text — which is the labour this
instrument exists to spare them.

So every claim is read once more against its own passage, and Python owns the outcome:

    not       the passage does not carry the claim. It is set aside, with the same status a
              rerun leaves behind, and the exclusion names the claim and why
    partly    the claim stands and is MARKED, wherever it is read: a reader sees which words
              were added before deciding what to do with it
    supported nothing happens, and a claim the check did not rule on is treated as supported.
              The prompt says so. A missing verdict must not be able to delete a claim

One call per material over its live claims, so the check reads each passage once, and the
material summary is written afterwards — over claims that survived it.
"""
from __future__ import annotations

from .. import llm, store
from . import synth

# Claims per call. Sixty claims with three sentences of passage each is a prompt a model can hold
# in one judgement; a whole fifty-claim-per-theme corpus in one call is not.
BATCH = 60
WHY_WORDS = 12


def passage(sents: list[tuple[str, str]], where: dict[str, int], sid: str) -> str:
    """The sentence the quote was bound to, with the one before and the one after it.

    One sentence alone reads as an assertion out of context and a whole material re-reads the
    material. The neighbours are what carry a manner, a cause or a comparison when the text
    genuinely has one.
    """
    i = where.get(sid)
    if i is None:
        return "(this passage is no longer in the material)"
    return "\n".join(f"{s}  {t}" for s, t in sents[max(0, i - 1):i + 2])


def claims_block(rows: list[dict], sents: list[tuple[str, str]], where: dict[str, int]) -> str:
    return "\n\n".join(f'[{r["id"]}] {r["claim"]}\n'
                       f'quoted: "{r["anchor"]}"\n'
                       f'the passage:\n{passage(sents, where, r["sid"])}'
                       for r in rows)


def run(conn, mid: str, *, theme_id: str | None = None, run_id: str | None = None) -> dict:
    """Check this material's live claims against their passages.

    Returns {"dropped", "set_aside", "marked"}. `theme_id` narrows it to one line, for the rerun
    that rewrites one line and must not pay to check the rest of the material again.
    """
    sql = ("SELECT id, sid, claim, anchor FROM moment WHERE material_id=? AND status='live'"
           + (" AND theme_id=? " if theme_id else " ") + "ORDER BY position")
    rows = [dict(r) for r in conn.execute(sql, (mid, theme_id) if theme_id else (mid,))]
    if not rows:
        return {"dropped": [], "set_aside": [], "marked": []}

    llm.report(f"checking {len(rows)} claims against their passages")
    sents = store.sentences(conn, mid)
    where = {sid: i for i, (sid, _) in enumerate(sents)}
    frame = synth.frame_block(conn, mid)

    ruled: dict[str, tuple[str, str]] = {}
    for start in range(0, len(rows), BATCH):
        batch = rows[start:start + BATCH]
        system, user = llm.prompt("verify", frame=frame, count=len(batch),
                                  claims=claims_block(batch, sents, where))
        data = llm.chat_json(system, user, label="verify")
        mine = {r["id"] for r in batch}
        for v in data.get("verdicts") or []:
            if not isinstance(v, dict):
                continue
            vid, verdict = str(v.get("id") or ""), str(v.get("verdict") or "").strip().lower()
            # An id from nowhere is ignored; `supported` and anything unreadable leave the claim
            # exactly as the reading wrote it.
            if vid in mine and verdict in ("not", "partly"):
                ruled[vid] = (verdict, synth.words(v.get("why"), WHY_WORDS))

    # Every claim that was checked, not only the ones ruled against: a claim marked `partly` on
    # an earlier pass and read as supported on this one must lose the mark, or the page keeps
    # warning a researcher about words that are no longer in question.
    store.mark_support(conn, [(r["id"], *ruled.get(r["id"], ("", ""))) for r in rows])
    claim = {r["id"]: r["claim"] for r in rows}
    return {
        "dropped": [f'a claim was set aside — its passage does not carry it: '
                    f'"{synth.clip(claim[i])}" ({why})'
                    for i, (verdict, why) in ruled.items() if verdict == "not"],
        "set_aside": [i for i, (verdict, _) in ruled.items() if verdict == "not"],
        "marked": [i for i, (verdict, _) in ruled.items() if verdict == "partly"],
    }
