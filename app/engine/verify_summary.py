"""VERIFY-SUMMARY — do the claims carry the sentences written over them?

VERIFY reads each claim against its own passage. Nothing read the summary, and the summary is what
a researcher reads first. A blind judge of a real record found the material summaries carrying
details the claims do not: an institution, a place, a number that appears in the material but in
no claim and no quote. DOC is shown the material as well as the lines, so it can reach past its
evidence without inventing anything at all — and a reader who trusts the summary has no way to
tell which half of a sentence rests on a claim they can open.

So the summary is split into sentences and read once more against the claims it was written over,
and Python owns the outcome, exactly as it does for a claim:

    not       the claims do not carry this sentence. It is removed from the summary before the
              summary is stored, and the exclusion quotes it and says why
    partly    the sentence stands and the exclusion says it goes past the claims, so a researcher
              reads the summary knowing which sentence to weigh
    supported nothing happens. A sentence the check did not rule on is KEPT and not marked — it
              is not thereby supported either, and nothing about it is written down or cleared.
              A missing verdict must not be able to delete a sentence, and it must not be able to
              vouch for one

One call per material, between the summary being written and its being stored, so the summary that
reaches the page and the record is the verified one.

ponytail: with no live claim in the material there is nothing to verify against, so the call is
skipped and the summary stands. Deleting a whole summary because its material's only line was set
aside would leave the page with no reading at all; the set-aside line already says so.
"""
from __future__ import annotations

import re

from .. import llm, store
from . import synth

WHY_WORDS = 12

# A sentence ends at . ! or ? before a space or the end of the text — except after an initial or a
# common abbreviation, where the stop belongs to the word. No dependency and no model: the split
# only has to be good enough to quote a sentence back to a researcher.
_END = re.compile(r"[.!?]+(?=\s|$)")
_ABBREV = re.compile(r"(?:\b[A-Za-z]|\bMr|\bMrs|\bMs|\bDr|\bProf|\bSt|\bvs|\betc|\bNo"
                     r"|\be\.g|\bi\.e)\.$", re.I)


def sentences(text: str) -> list[str]:
    """One paragraph into its sentences, in order."""
    out, start = [], 0
    for m in _END.finditer(text):
        piece = text[start:m.end()]
        if _ABBREV.search(piece.rstrip()):
            continue                     # "M." or "etc." — the stop is part of the word
        out.append(piece.strip())
        start = m.end()
    tail = text[start:].strip()
    return [s for s in out + [tail] if s]


def claims_block(rows) -> str:
    return "\n".join(f'[{r["id"]}] {r["claim"]} — "{r["anchor"]}" [{r["sid"]}]' for r in rows)


def run(conn, mid: str, summary: str, *, evidence: str | None = None) -> tuple[str, list[str]]:
    """Check one material's summary against its live claims. Returns the summary to store and the
    notes for the run row.

    `evidence` replaces those claims with something else the caller has already assembled, and is
    the MEMO's case: a memo is written before any line exists, so what it can be checked against
    is the passages it cites rather than claims that are not there yet. Left unset, this is the
    path DOC has always taken, to the character.
    """
    text = str(summary or "").strip()
    paragraphs = [sentences(p) for p in re.split(r"\n\s*\n", text)]
    numbered = [s for p in paragraphs for s in p]
    against = evidence if evidence is not None else claims_block(store.moments(conn, mid))
    if not numbered or not against.strip():
        return text, []

    llm.report("checking the summary against the claims")
    system, user = llm.prompt(
        "verify_summary",
        frame=synth.frame_block(conn, mid),
        sentences="\n".join(f"{i}. {s}" for i, s in enumerate(numbered, 1)),
        claims=against)
    data = llm.chat_json(system, user, label="verify_summary")

    ruled: dict[int, tuple[str, str]] = {}
    for v in data.get("verdicts") or []:
        if not isinstance(v, dict):
            continue
        verdict = str(v.get("verdict") or "").strip().lower()
        try:
            n = int(v.get("n"))
        except (TypeError, ValueError):
            continue
        # A number from nowhere is ignored; `supported` and anything unreadable leave the sentence
        # exactly as DOC wrote it.
        if 1 <= n <= len(numbered) and verdict in ("not", "partly"):
            ruled[n] = (verdict, synth.words(v.get("why"), WHY_WORDS))
    if not ruled:
        return text, []                  # untouched, to the character

    notes, kept_paragraphs, n = [], [], 0
    for paragraph in paragraphs:
        kept = []
        for said in paragraph:
            n += 1
            verdict, why = ruled.get(n, ("", ""))
            if verdict == "not":
                notes.append("a sentence of the summary was set aside — the claims do not carry "
                             f'it: "{synth.clip(said)}" ({why})')
                continue
            if verdict == "partly":
                notes.append("a sentence of the summary goes past the claims: "
                             f'"{synth.clip(said)}" ({why})')
            kept.append(said)
        if kept:
            kept_paragraphs.append(" ".join(kept))
    return "\n\n".join(kept_paragraphs), notes
