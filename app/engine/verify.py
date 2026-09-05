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
    supported the claim stands and any earlier mark on it is lifted: a claim questioned on one
              pass and read as carried on this one must stop warning the researcher
    unchecked nobody ruled on it. Only what the check RETURNED is written, and a claim it left
              out is recorded as unchecked rather than counted as supported — an empty answer
              used to read as a clean bill of health for every claim in the batch and could lift
              a standing `partly` off one. A missing verdict still cannot delete a claim, and it
              cannot clear a qualification either: a claim already marked keeps its mark

The subset the check left out is asked for once more where the answer was cut short, and what
comes back a second time is written the same way; what is still missing stays unchecked.

One call per material over its live claims, so the check reads each passage once, and the
material summary is written afterwards — over claims that survived it.
"""
from __future__ import annotations

from collections import Counter

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


def _ask(batch: list[dict], sents, where, frame: str) -> dict[str, tuple[str, str]]:
    """One call, and the verdicts in its answer that are about claims in this batch.

    All three readable verdicts are carried back, `supported` included, because only a claim that
    was actually ruled on may be written: silence has to stay distinguishable from a clean bill of
    health. A verdict word that is none of the three is not a ruling and is left out with them.
    """
    system, user = llm.prompt("verify", frame=frame, count=len(batch),
                              claims=claims_block(batch, sents, where))
    data = llm.chat_json(system, user, label="verify")
    mine = {r["id"] for r in batch}
    out: dict[str, tuple[str, str]] = {}
    for v in (data.get("verdicts") if isinstance(data, dict) else None) or []:
        if not isinstance(v, dict):
            continue
        vid, verdict = str(v.get("id") or ""), str(v.get("verdict") or "").strip().lower()
        if vid in mine and verdict in ("supported", "partly", "not"):
            # '' is what a supported claim carries: the column says what is in question, and
            # nothing is.
            out[vid] = ("" if verdict == "supported" else verdict,
                        synth.words(v.get("why"), WHY_WORDS))
    return out


def _predating_summaries(conn, mid: str, gone: list[dict], run_id: str | None) -> None:
    """Say so on the line summaries whose claims this check has just taken away.

    A line's summary is written over its claims and stored before any of them is checked, so a
    paragraph about four claims can end up standing over a line of two — reading as authoritative
    about evidence that is no longer there (AR-05). Rewriting it properly means another model call
    over an answer nobody asked for; one sentence saying it predates the check costs nothing and
    tells the researcher exactly what they are looking at.
    """
    for tid, n in Counter(r["theme_id"] for r in gone).items():
        row = store.get_summary(conn, "thread", f"{mid}:{tid}", "reading")
        text = (row["text"] if row else "").strip()
        if not text:
            continue
        store.save_summary(conn, "thread", f"{mid}:{tid}", "reading",
                           f"{text} ({n} claim{'' if n == 1 else 's'} "
                           f"{'was' if n == 1 else 'were'} set aside after checking; this "
                           "summary predates that.)", run_id)


def run(conn, mid: str, *, theme_id: str | None = None, run_id: str | None = None) -> dict:
    """Check this material's live claims against their passages.

    Returns {"dropped", "set_aside", "marked"}. `theme_id` narrows it to one line, for the rerun
    that rewrites one line and must not pay to check the rest of the material again.
    """
    sql = ("SELECT id, sid, claim, anchor, theme_id, support FROM moment "
           "WHERE material_id=? AND status='live'"
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
        ruled |= _ask(batch, sents, where, frame)
        missing = [r for r in batch if r["id"] not in ruled]
        # Once, for the subset that came back unjudged, and only where SOME of the batch was
        # judged. An answer cut off part way is worth asking again; an answer that ruled on
        # nothing at all is a model declining the whole batch, and the identical prompt gets the
        # identical nothing. Those claims are recorded unchecked instead, where a researcher can
        # see them.
        # ponytail: one retry per batch, never a loop — raise the bound if real answers turn out
        # to arrive in thirds.
        if missing and len(missing) < len(batch):
            llm.report(f"asking again about {len(missing)} claims the check left out")
            ruled |= _ask(missing, sents, where, frame)

    # Only what came back is written. A claim nobody ruled on is recorded `unchecked`, and one
    # already carrying a mark keeps it: an omission says nothing about a claim, so it can neither
    # confirm it nor lift the qualification standing on it. `supported` still clears a mark,
    # because that is a ruling — the page would otherwise keep warning a researcher about words
    # that are no longer in question.
    # One transaction: a claim taken away and the note on the summary that stood over it are the
    # same finding, and the record must not be able to hold one without the other.
    with store.atomic(conn) as tx:
        store.mark_support(tx, [(r["id"], *ruled[r["id"]]) for r in rows if r["id"] in ruled]
                           + [(r["id"], "unchecked", "") for r in rows
                              if r["id"] not in ruled and not (r["support"] or "")])
        _predating_summaries(tx, mid, [r for r in rows
                                       if ruled.get(r["id"], ("", ""))[0] == "not"], run_id)
    claim = {r["id"]: r["claim"] for r in rows}
    return {
        "dropped": [f'a claim was set aside — its passage does not carry it: '
                    f'"{synth.clip(claim[i])}" ({why})'
                    for i, (verdict, why) in ruled.items() if verdict == "not"],
        "set_aside": [i for i, (verdict, _) in ruled.items() if verdict == "not"],
        "marked": [i for i, (verdict, _) in ruled.items() if verdict == "partly"],
    }
