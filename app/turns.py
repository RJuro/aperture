"""Who speaks, mechanically. No model involved.

A speaker cue looks like `NAME:` at the start of a line, but so does an archival header line
(`BIRTH DATE:  1910`). A name earns turn status by RECURRING: an interviewer speaks dozens of
times, a header label once. Ported from the old engine, where this rule was found by watching it
fail on real transcripts.

This module runs BEFORE the model on every ingest, and its result goes into the frame prompt. The
model names and roles what was found here; it never parses. When the model proposes a label of its
own (material this scan cannot read), `occurrences` is what verifies it exists before it is used.
"""
from __future__ import annotations

import re

# A cue is an upper-case-ish name followed by a colon at a line start. Kept deliberately narrow:
# a false positive costs a wrongly split turn, which is visible on the page.
CUE = re.compile(r"^[ \t]*([A-Z][A-Za-z'.\- ]{1,28}?)[ \t]*:", re.MULTILINE)
MIN_TURNS = 3          # recurrence: what separates a speaker from a header label
MIN_VERIFY = 2         # a model-proposed label must appear at least this often to be believed


def scan(text: str) -> dict[str, int]:
    """Every `NAME:` at a line start, with how often it recurs. The raw evidence the frame prompt
    is shown, so the model can see what the scan saw rather than being told a conclusion."""
    counts: dict[str, int] = {}
    for m in CUE.finditer(text or ""):
        name = m.group(1).strip()
        counts[name] = counts.get(name, 0) + 1
    return counts


def speakers(text: str) -> list[str]:
    """Labels that recur often enough to be speakers, most frequent first."""
    counts = scan(text)
    return sorted((k for k, v in counts.items() if v >= MIN_TURNS),
                  key=lambda k: (-counts[k], k))


def occurrences(text: str, label: str) -> int:
    """How many line starts carry this exact label. The verification the frame law rests on: a
    speaker the model proposes must be found in the text, the same way a quote must be."""
    return scan(text).get((label or "").strip(), 0)


def assign(lines: list[str], known: list[str]) -> list[tuple[int, str]]:
    """(turn index, speaker) for each line, carrying the current speaker forward across the lines
    of one turn. Lines before the first cue belong to turn 0 with no speaker — front matter."""
    out: list[tuple[int, str]] = []
    turn, who = 0, ""
    for line in lines:
        m = CUE.match(line or "")
        if m and m.group(1).strip() in known:
            turn += 1
            who = m.group(1).strip()
        out.append((turn, who))
    return out
