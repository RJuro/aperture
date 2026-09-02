"""The anchor law: no claim reaches a researcher without a verbatim quote Python can find.

design/BLUEPRINT.md §3. Round 2's readers spent their entire door budget auditing the system's
claims instead of exploring the document, because a claim's truth was unknowable without
spending a door on it. An anchor is the check: a short verbatim quote, carried by the claim,
that Python locates character-for-character in the material. A reader sees the speaker's own
words before deciding whether the claim is worth a door.

It also closes D15, the round's most damaging defect. The base analysis claimed "another migrant
addresses unequal passenger treatment" — true of the interview — but bound it to the passages
about a theft in Trieste. Two readers opened those, found nothing of the sort, and concluded the
system was inflating. A true claim with bad pointers is worse than a false one: it teaches
distrust of a system that was right.

So the anchor, not the citation, is authoritative. `bind` locates the quote and reports:

    bound    the anchor is inside the cited span — the claim is what it says it is
    rebound  the anchor is real but lives elsewhere — the CITATION was wrong, and the
             corrected sids come back with it (this is the D15 repair)
    unfound  the anchor is nowhere in the document — the claim is ungrounded and its caller
             drops it, exactly as an ungrounded sentence id is dropped today

Pure functions over (sid, text) pairs — no DB, no LLM — so the rules live where they are
testable, and callers in read.py/synthesize.py only decide what to do with a verdict.
"""
from __future__ import annotations

import re
import unicodedata

# A quote is a pinpoint, not a paragraph. Over-long anchors are counted, never rejected: the cap
# is a prompt-compliance signal, and this module only rules on whether a claim is TRUE.
ANCHOR_WORD_CAP = 12

# How many consecutive sentences a single anchor may span. Sentence splitting is fine-grained
# here and a natural quote routinely crosses one boundary ("he fell or jumped or whatever, and
# he got killed" is two sentences in some transcripts); three is generous without letting an
# anchor roam a whole page.
SPAN = 3

_QUOTES = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"',
                         "–": "-", "—": "-", " ": " "})


def norm(s: str) -> str:
    """Whitespace-collapsed, case-folded, quote-normalised text for containment tests.

    Transcripts carry tabs and doubled spaces from their original typesetting ("PHILLIPS:\tAnd
    tell me"), and a model re-typing a quote will silently substitute a straight apostrophe for
    a curly one. Neither difference means the quote is not verbatim, so neither may decide
    whether a claim is grounded.
    """
    s = unicodedata.normalize("NFKC", s or "").translate(_QUOTES)
    return re.sub(r"\s+", " ", s).strip().casefold()


def word_count(anchor: str) -> int:
    return len((anchor or "").split())


def locate(anchor: str, sentences: list[tuple[str, str]]) -> list[str]:
    """Ids of every sentence where `anchor` starts, allowing it to run across up to SPAN
    sentences. `sentences` is [(sid, text), ...] in document order.

    An anchor spanning a boundary binds to the sentence it STARTS in — that is the passage a
    door should open on, and the exchange around it carries the rest.
    """
    a = norm(anchor)
    if not a:
        return []
    hits = []
    for i in range(len(sentences)):
        window = norm(" ".join(t for _, t in sentences[i:i + SPAN]))
        if a not in window:
            continue
        # The anchor STARTS here only if the window one sentence later no longer holds it.
        # Without this, a quote living in sentence i+1 also matches the window opening at i, and
        # every claim would bind a sentence early — a door opened next to its own evidence.
        nxt = norm(" ".join(t for _, t in sentences[i + 1:i + 1 + SPAN]))
        if a not in nxt:
            hits.append(sentences[i][0])
    return hits


def bind(anchor: str, cited_sids: list[str], sentences: list[tuple[str, str]]) -> dict:
    """Rule on one claim. Returns {verdict, sids, found_in, over_cap}.

    `cited_sids` and the ids in `sentences` must already be in the same id space — bare or
    doc-qualified, but not a mix; qualification is the caller's job because only the caller
    knows which document it is reading (read.py and synthesize.py qualify at different points).

    On `rebound`, `sids` is what the citation SHOULD have been. Callers repair rather than drop:
    the claim was true, and discarding true claims for their bookkeeping is how a system loses
    the material it correctly found.
    """
    found = locate(anchor, sentences)
    over_cap = word_count(anchor) > ANCHOR_WORD_CAP
    if not found:
        return {"verdict": "unfound", "sids": [], "found_in": [], "over_cap": over_cap}
    inside = [s for s in found if s in set(cited_sids)]
    if inside:
        return {"verdict": "bound", "sids": list(cited_sids), "found_in": found,
                "over_cap": over_cap}
    return {"verdict": "rebound", "sids": found, "found_in": found, "over_cap": over_cap}


def new_stats() -> dict:
    return {"bound": 0, "rebound": 0, "unfound": 0, "over_cap": 0, "missing": 0}


def apply(claim: dict, cited_sids: list[str], sentences: list[tuple[str, str]],
          stats: dict, *, key: str = "anchor") -> tuple[str, list[str]] | None:
    """Validate one claim's anchor in place against `sentences`, tallying into `stats`.

    Returns (anchor, sids) to keep, or None when the claim must be dropped. `missing` is
    tallied separately from `unfound`: a model that omitted the field is a prompt-compliance
    problem, while a quote that exists nowhere in the document is a grounding failure, and
    collapsing the two would hide whichever is actually happening.
    """
    anchor = str(claim.get(key, "") or "").strip()
    if not anchor:
        stats["missing"] += 1
        return None
    v = bind(anchor, cited_sids, sentences)
    if v["over_cap"]:
        stats["over_cap"] += 1
    stats[v["verdict"]] += 1
    if v["verdict"] == "unfound":
        return None
    return anchor, v["sids"]
