"""CHECK — the absence verb (PLAN.md §3.2).

A negative claim is something a researcher runs, never a sentence a model writes. Round 1's worst
defect was a confident "the material never mentions X" from a model that had not looked. So:

    it searches ONLY the passages no live moment rests on   what the reading already claims on has
                                                            been read; a check is for the rest
    the model returns quotes, not a conclusion               `found: [{anchor, sid}]`
    **the verdict is Python's**                              a quote that binds → found; no quote
                                                            that binds → not found, whatever the
                                                            model asserts in any other field

The inverse of round 1's defect is a model claiming support it cannot show, and the same guard
catches it: a claim without a findable quote is not believed.
"""
from __future__ import annotations

from .. import anchor, llm, store
from . import synth

# One call per chunk. The cap is characters of passage text, well above a full seed transcript
# (~28k) so an ordinary material is searched in one look and only a very long one is split.
CHUNK = 40000


def run(conn, pid: str, scope: str, ref_id: str, question: str, *,
        run_id: str | None = None) -> dict:
    """Search the uncited passages in scope for anything bearing on `question`."""
    found, searched = [], 0
    for mid in materials(conn, pid, scope, ref_id):
        row = store.material(conn, mid)
        passages = store.uncited(conn, mid)
        searched += len(passages)
        nums = synth.numbers(passages)
        stats = anchor.new_stats()
        for chunk in chunks(passages):
            system, user = llm.prompt(
                "check", question=question,
                material=f'{(row["title"] or row["name"]) if row else mid} — '
                         f'{(row["kind"] if row else "") or "kind not worked out"}',
                passages="\n".join(f"{sid}  {text}" for sid, text in chunk))
            data = llm.chat_json(system, user, label="check")
            for hit in data.get("found") or []:
                if not isinstance(hit, dict):
                    continue
                # The anchor law again, and here it is the whole verdict: the quote is bound
                # against the passages that were actually searched, or it does not count.
                bound = anchor.apply(hit, [synth.cited(hit.get("sid"), nums)], passages, stats)
                if bound:
                    found.append({"material_id": mid, "sid": bound[1][0], "anchor": bound[0]})

    verdict = "found" if found else "not found"
    cid = store.save_check(conn, pid, scope, ref_id, question, verdict, found, searched, run_id)
    return {"check_id": cid, "verdict": verdict, "anchors": found, "searched_n": searched}


def materials(conn, pid: str, scope: str, ref_id: str) -> list[str]:
    """What a check reads, per scope. A doubt lands on a moment or a thread; the material it
    belongs to is what gets searched."""
    if scope == "project":
        return [m["id"] for m in store.materials(conn, ref_id or pid)]
    if scope == "moment":
        mo = store.moment(conn, ref_id)
        return [mo["material_id"]] if mo else []
    if scope == "thread":
        return [str(ref_id).split(":", 1)[0]]
    return [ref_id] if store.material(conn, ref_id) else []


def chunks(passages: list[tuple[str, str]], budget: int = CHUNK) -> list[list[tuple[str, str]]]:
    out, cur, n = [], [], 0
    for p in passages:
        if cur and n + len(p[1]) > budget:
            out.append(cur)
            cur, n = [], 0
        cur.append(p)
        n += len(p[1])
    return out + ([cur] if cur else [])
