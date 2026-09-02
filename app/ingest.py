"""Raw text → numbered sentences. Mechanical, deterministic, no model, no spaCy.

Sentence ids are the spine of everything: codes cite them, moments cite them, quotes are bound to
them, the page targets them. So ids are assigned once, at ingest, and never change — a re-frame
re-describes the material's shape but never re-ingests, which is what lets codes and moments
survive it.
"""
from __future__ import annotations

import re

from . import turns

# Split after . ! ? … when followed by space and something that plausibly starts a sentence.
# Guarded against the common abbreviations and initials that litter transcripts.
_ABBREV = r"(?<!\bMr)(?<!\bMrs)(?<!\bMs)(?<!\bDr)(?<!\bSt)(?<!\bNo)(?<!\bvs)(?<!\betc)(?<![A-Z])"
_SPLIT = re.compile(rf"{_ABBREV}(?<=[.!?…])[\"')\]]*\s+(?=[\"'(\[]*[A-Z0-9])")
MAX_SENTENCE = 600     # a run-on line without punctuation is cut rather than swallowing a page


def split_sentences(line: str) -> list[str]:
    parts = [p.strip() for p in _SPLIT.split(line or "") if p and p.strip()]
    out: list[str] = []
    for p in parts:
        while len(p) > MAX_SENTENCE:
            cut = p.rfind(" ", 0, MAX_SENTENCE) or MAX_SENTENCE
            out.append(p[:cut].strip())
            p = p[cut:].strip()
        if p:
            out.append(p)
    return out


def sentences(text: str) -> list[dict]:
    """[{idx, sid, turn_idx, speaker, text}] in document order.

    Lines are the outer unit so a transcript's turn structure survives; sentences are split inside
    a line. A blank line is a paragraph break and is not a sentence.
    """
    lines = (text or "").lstrip("\ufeff").splitlines()
    known = turns.speakers(text or "")
    assigned = turns.assign(lines, known)
    out: list[dict] = []
    for line, (turn_idx, speaker) in zip(lines, assigned):
        if not line.strip():
            continue
        for s in split_sentences(line):
            i = len(out)
            out.append({"idx": i, "sid": f"S{i:03d}", "turn_idx": turn_idx,
                        "speaker": speaker, "text": s})
    return out


def head_and_tail(text: str, head: int = 6000, tail: int = 1500) -> str:
    """What the frame prompt sees of a long piece: the opening, where the shape declares itself,
    and the end, where a transcript's closing exchange or a document's sign-off sits."""
    text = text or ""
    if len(text) <= head + tail:
        return text
    return f"{text[:head]}\n\n[... {len(text) - head - tail} characters not shown ...]\n\n{text[-tail:]}"
