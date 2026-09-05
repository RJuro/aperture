"""CHECK — the absence verb (PLAN.md §3.2).

A negative claim is something a researcher runs, never a sentence a model writes. Round 1's worst
defect was a confident "the material never mentions X" from a model that had not looked. So:

    it searches the set the researcher asked for            everything, or only the passages no
                                                            live moment rests on — and the result
                                                            says which
    the model returns quotes, not a conclusion               `found: [{anchor, sid}]`
    **the verdict is Python's**                              a quote that binds → found; no quote
                                                            that binds → not found, whatever the
                                                            model asserts in any other field

The inverse of round 1's defect is a model claiming support it cannot show, and the same guard
catches it: a claim without a findable quote is not believed.

Searching only the uncited remainder was the whole verb once, and it answered the wrong question.
"Did they join a union?" came back not found on a material whose sentence "We joined a union"
was already carrying a claim — the one passage that answers it was the one passage withheld. The
remainder search is still here, honestly named, and it is no longer the default.
"""
from __future__ import annotations

from .. import anchor, llm, store
from . import synth

# One call per chunk. The cap is characters of passage text, well above a full seed transcript
# (~28k) so an ordinary material is searched in one look and only a very long one is split.
CHUNK = 40000


# What the prompt is told about the set it is looking at. One sentence, because the model has to
# know whether "nothing here" is a statement about the material or about its remainder.
SCOPE_SAID = {
    "all": "These are every passage of this material, whether or not a claim already rests on "
           "one: nothing has been held back from you.",
    "unused": "These are not all the passages in the material. They are the ones no claim "
              "currently rests on, so \"not found here\" means \"not found outside what has "
              "already been claimed\".",
}


def run(conn, pid: str, kind: str, ref: str, question: str, scope: str = "all", *,
        run_id: str | None = None) -> dict:
    """Search for anything bearing on `question`. `kind` and `ref` say WHAT is searched — one
    material, one moment's material, the project; `scope` says WHICH of its passages: 'all' of
    them, or the 'unused' ones no live claim rests on.

    'all' is the default because that is what a researcher asking a question of the material
    means. 'unused' is a different question — what is in here that the reading has not used —
    and it is offered under that name.
    """
    scope = scope if scope in SCOPE_SAID else "all"
    found, searched = [], 0
    for mid in materials(conn, pid, kind, ref):
        row = store.material(conn, mid)
        passages = store.sentences(conn, mid) if scope == "all" else store.uncited(conn, mid)
        searched += len(passages)
        nums = synth.numbers(passages)
        stats = anchor.new_stats()
        for chunk in chunks(passages):
            system, user = llm.prompt(
                "check", question=question, scope=SCOPE_SAID[scope],
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
    cid = store.save_check(conn, pid, kind, ref, question, verdict, found, searched, run_id,
                           searched_scope=scope)
    return {"check_id": cid, "verdict": verdict, "anchors": found, "searched_n": searched,
            "searched_scope": scope}


def materials(conn, pid: str, kind: str, ref: str) -> list[str]:
    """What a check reads, per kind of target. A doubt lands on a moment or a thread; the material
    it belongs to is what gets searched."""
    if kind == "project":
        return [m["id"] for m in store.materials(conn, ref or pid)]
    if kind == "moment":
        mo = store.moment(conn, ref)
        return [mo["material_id"]] if mo else []
    if kind == "thread":
        return [str(ref).split(":", 1)[0]]
    return [ref] if store.material(conn, ref) else []


def chunks(passages: list[tuple[str, str]], budget: int = CHUNK) -> list[list[tuple[str, str]]]:
    out, cur, n = [], [], 0
    for p in passages:
        if cur and n + len(p[1]) > budget:
            out.append(cur)
            cur, n = [], 0
        cur.append(p)
        n += len(p[1])
    return out + ([cur] if cur else [])
