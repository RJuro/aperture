"""TIGHTEN — take the addition out of a claim the check found only partly carried.

VERIFY rules on every claim against its own passage and Python owns the outcome: `not` sets the
claim aside, `partly` keeps it and MARKS it, so a reader sees which words were added before
deciding what to do with it. That mark was doing work a rewrite should do. On an eight-material
record 291 of 748 standing claims carried "the passage carries part of this" — two claims in five,
each of them a sentence a researcher has to correct in their own head every time they read it,
and each of them one motive, one manner or one hardened hedge away from being a claim the passage
simply carries.

So the marked claims are handed back with what the check named, and rewritten:

    a claim comes back     its text is replaced, the mark is lifted, and it is CHECKED AGAIN — a
                           rewrite that still over-reaches is marked again rather than trusted
    a claim comes back ""  nothing the passage says was left once the addition was gone. The
                           moment is set aside, with the same status the check itself leaves
    an id is left out      the claim and its mark stand exactly as they were

The quote never moves. A claim rests on the passage it was bound to and this pass may only take
words away from what was said about it; choosing a different passage would be a new reading, not a
tightening of this one.
"""
from __future__ import annotations

import os

from .. import llm, store
from . import synth, verify

# The same batch as the check, and for the same reason: these are the same claims with the same
# passages under them, a few of them, read in one judgement.
BATCH = verify.BATCH


def off() -> bool:
    """`APERTURE_TIGHTEN=off` skips the step. A harness measuring what the mark alone does needs
    the marked claims left standing, and a researcher who distrusts a rewrite of their reading
    needs the same switch."""
    return os.environ.get("APERTURE_TIGHTEN", "").strip().lower() == "off"


def claims_block(rows: list[dict], sents, where) -> str:
    return "\n\n".join(f'[{r["id"]}] {r["claim"]}\n'
                       f'the check found added: {r["support_note"] or "not said"}\n'
                       f'quoted: "{r["anchor"]}"\n'
                       f'the passage:\n{verify.passage(sents, where, r["sid"])}'
                       for r in rows)


def _ask(batch: list[dict], sents, where, frame: str) -> dict[str, str]:
    """One call, and the rewritten claims in its answer that are about claims in this batch.

    An empty string is an answer — it says the claim is nothing once the addition is gone — so it
    is carried back with the rest, and only an id this batch never asked about is dropped.
    """
    system, user = llm.prompt("tighten", frame=frame, count=len(batch),
                              claims=claims_block(batch, sents, where))
    data = llm.chat_json(system, user, label="tighten")
    mine = {r["id"] for r in batch}
    out: dict[str, str] = {}
    for c in (data.get("claims") if isinstance(data, dict) else None) or []:
        if not isinstance(c, dict) or "claim" not in c:
            continue
        cid = str(c.get("id") or "")
        if cid in mine:
            out[cid] = synth.words(c.get("claim"), synth.CLAIM_WORDS)
    return out


def run(conn, mid: str, *, run_id: str | None = None) -> dict:
    """Rewrite this material's partly-carried claims. Returns {"dropped"} for the run's notes."""
    if off():
        return {"dropped": []}
    rows = [dict(r) for r in conn.execute(
        "SELECT id, sid, claim, anchor, theme_id, support_note FROM moment "
        "WHERE material_id=? AND status='live' AND support='partly' ORDER BY position", (mid,))]
    if not rows:
        return {"dropped": []}           # nothing was marked: no call, and nothing to say about it

    llm.report(f"tightening {len(rows)} claims the check found only partly carried")
    sents = store.sentences(conn, mid)
    where = {sid: i for i, (sid, _) in enumerate(sents)}
    frame = synth.frame_block(conn, mid)

    written: dict[str, str] = {}
    for start in range(0, len(rows), BATCH):
        written |= _ask(rows[start:start + BATCH], sents, where, frame)

    dropped, rewritten, aside = [], [], []
    with store.atomic(conn) as tx:
        for r in rows:
            if r["id"] not in written:
                continue                 # an id the answer left out keeps its claim and its mark
            if text := written[r["id"]]:
                # The quote, the passage and the position are untouched; the mark goes, because
                # the words it was about are gone. Whether it deserves a new one is the check's to
                # say, below, and not this pass's.
                tx.execute("UPDATE moment SET claim=?, support='', support_note='' "
                           "WHERE id=? AND status='live'", (text, r["id"]))
                rewritten.append(r["id"])
            else:
                store.mark_support(tx, [(r["id"], "not", "tightened to nothing")])
                aside.append(r["id"])
                dropped.append("a claim tightened to nothing was set aside — "
                               f'"{synth.clip(r["claim"])}"')

    # Checked again, because a rewrite is a new claim: one that still reaches past its passage has
    # to be marked again rather than trusted for having been through here.
    lost = verify.run(conn, mid, ids=rewritten, run_id=run_id)["lost"] if rewritten else []

    # Every line this pass touched, over the claims as they now stand. `lost` is already among
    # them; the summary of a line whose claim was merely reworded is just as stale as one whose
    # claim went.
    touched = {r["theme_id"] for r in rows if r["id"] in written}
    for tid in list(dict.fromkeys(list(touched) + lost)):
        dropped += synth.line_summary(conn, mid, tid, run_id=run_id)

    still = conn.execute("SELECT COUNT(*) AS n FROM moment WHERE material_id=? AND status='live' "
                         "AND support='partly'", (mid,)).fetchone()["n"]
    dropped.append(f"{len(rewritten)} claims tightened, {len(aside)} set aside, "
                   f"{still} still partly carried")
    return {"dropped": dropped}
