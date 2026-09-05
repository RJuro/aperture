"""MEMO — what one material says on its own terms (PLAN.md §13).

Where a project explores, this is the account of a material a researcher reads first, and it is
written over the passages the reading coded rather than over theme lines. That is the whole reason
it exists: DOC's summary is written over the lines, so it goes stale the moment the themes move,
and in an exploratory project the themes move after every batch. A memo written over passages is
still true when the theme set turns over underneath it.

Three rules Python owns, not the prompt:

    a sentence that cites nothing is not a finding   it is dropped before anyone reads it, and the
                                                     exclusion quotes it — the same treatment
                                                     VERIFY-SUMMARY gives a sentence the claims do
                                                     not carry
    a sentence is checked against what it cites      VERIFY-SUMMARY again, with the cited passages
                                                     standing in for the claims: there are no
                                                     claims yet when this runs
    the questions and the people are DOC's           the memo carries what DOC's summary carried
                                                     for an iterative project, saved the same way,
                                                     so nothing downstream has to know which
                                                     method wrote them

One transaction after validation, as READ and THREAD do: the memo, its questions and its people
are one finding about this material and the record must not hold a third of it.
"""
from __future__ import annotations

import re

from .. import llm, store
from . import synth, verify_summary

# What the memo may cost the reader. Shorter than DOC's summary (320) because it is prose over
# passages rather than an introduction to lines a reader is about to walk.
MEMO_WORDS = 250

# A citation as the prompt asks for it: `[S118, S120]`. Only the bracketed groups are read, so a
# passage id in the middle of a sentence is not mistaken for one.
_CITE = re.compile(r"\[([^\[\]]+)\]")


def coded_block(conn, mid: str) -> str:
    """The passages the reading marked, each under its code with the code's definition.

    Grouped by code and printed with the passage's own text, because the memo rests on these and
    cites their ids: a list of ids under a label is not evidence anyone can write from.
    """
    text = dict(store.sentences(conn, mid))
    by_code: dict[tuple[str, str], list[str]] = {}
    for h in store.hits(conn, mid):
        by_code.setdefault((h["name"], h["definition"] or ""), []).append(h["sid"])
    if not by_code:
        return "The reading marked nothing in this material."
    out = []
    for (name, definition), sids in sorted(by_code.items()):
        out.append(f"## {name} — {definition or 'no definition recorded'}")
        out += [f"{sid}  {text.get(sid, '')}" for sid in sids]
    return "\n".join(out)


def _uncited(memo: str, nums: dict[str, str], sids: set[str]) -> tuple[str, list[str], set[str]]:
    """The memo with every sentence that cites no passage of this material removed.

    Returns the text to check, the exclusions, and the passage ids the surviving sentences rest
    on. A sentence with no citation is the model's own — it may be true, and there is no way for
    a reader to find out — so it goes before anyone reads it rather than being marked afterwards.
    """
    kept_paragraphs, notes, cited = [], [], set()
    for paragraph in re.split(r"\n\s*\n", memo):
        kept = []
        for said in verify_summary.sentences(paragraph):
            here = {synth.cited(t, nums) for group in _CITE.findall(said)
                    for t in re.split(r"[,;\s]+", group) if t}
            here &= sids
            if not here:
                notes.append("a sentence of the memo was set aside — it cites no passage: "
                             f'"{synth.clip(said)}"')
                continue
            cited |= here
            kept.append(said)
        if kept:
            kept_paragraphs.append(" ".join(kept))
    return "\n\n".join(kept_paragraphs), notes, cited


def evidence_block(conn, mid: str, sids: set[str]) -> str:
    """The passages the memo cites, in the order they appear, as VERIFY-SUMMARY's evidence.

    It ordinarily checks a summary against the claims below it; a memo has none — it is written
    before any line — so what it is checked against is the passages it says it rests on.
    """
    return "\n".join(f'[{sid}] "{text}"' for sid, text in store.sentences(conn, mid)
                     if sid in sids)


def run(conn, mid: str, *, run_id: str | None = None) -> dict:
    """Write this material's memo, its questions and its people. Returns {memo, dropped}."""
    row = store.material(conn, mid)
    if row is None:
        raise ValueError(f"no material {mid!r}")
    pid = row["project_id"]
    proj = store.project(conn, pid)
    orientation = store.get_summary(conn, "material", mid, "orientation")
    said_here = synth.feedback_block(conn, pid, mid, None)
    slots = dict(
        orientation=orientation["text"] if orientation else "Not written.",
        frame=synth.frame_block(conn, mid),
        focus=(proj["focus"] if proj else "") or "Nothing in particular. Read it on its own terms.",
        coded=coded_block(conn, mid),
        material=synth.layout(conn, mid),
        memo_words=MEMO_WORDS, question_words=synth.BRIEF_WORDS,
    )
    data = llm.chat_json(*llm.prompt("memo", feedback=said_here, **slots), label="memo")

    sents = store.sentences(conn, mid)
    nums, sids = synth.numbers(sents), {sid for sid, _ in sents}
    memo, odd = synth.foreign(synth.words(data.get("memo"), MEMO_WORDS),
                              synth.allowed_text(conn, pid, mid))
    dropped = synth.script_notes(odd)
    memo, said, cited = _uncited(memo, nums, sids)
    dropped += said

    def again(flags: str):
        """The memo once more, shown what the check flagged, and the passages the NEW memo cites —
        a rewrite may drop a citation, and checking it against the first memo's evidence would
        judge it on passages it no longer rests on. The flags are the instrument's own prose, so
        they go into the feedback slot as their own labelled paragraph (PLAN.md §3 law 5)."""
        second = llm.chat_json(*llm.prompt("memo", feedback=f"{said_here}\n\n{flags}", **slots),
                               label="memo")
        text, strange = synth.foreign(synth.words(second.get("memo"), MEMO_WORDS),
                                      synth.allowed_text(conn, pid, mid))
        text, notes, now = _uncited(text, nums, sids)
        dropped.extend(synth.script_notes(strange) + notes)
        return text, evidence_block(conn, mid, now)

    # Before it is stored, never after — the same rule DOC follows: the account a researcher reads
    # first is the one that was checked against what it says it rests on.
    memo, said = verify_summary.run(conn, mid, memo, evidence=evidence_block(conn, mid, cited),
                                    again=again)
    dropped += said

    questions = synth.words(data.get("questions"), synth.BRIEF_WORDS)
    with store.atomic(conn) as tx:
        if memo:
            store.save_summary(tx, "material", mid, "memo", memo, run_id)
        # The one self-prompting slot, saved exactly where DOC saves it, so ANGLES reads the two
        # methods' questions without knowing which wrote them (PLAN.md §2).
        if questions:
            store.save_summary(tx, "material", mid, "questions", questions, run_id)
        if "people" in data:
            store.save_people(tx, mid, [p for p in (data.get("people") or [])
                                        if isinstance(p, dict) and p.get("name")])
    return {"memo": memo, "questions": questions, "dropped": dropped}
