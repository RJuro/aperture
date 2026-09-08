"""How much of the prompts' own register came back in the prose a researcher reads.

A counter, never a gate. Nothing here rejects an answer or asks for it again: a retry is a whole
model call, and a sentence this flags may be the right sentence — the material itself sometimes
says "not X but Y", and then so must the claim. What it produces is a number on the run row and a
column in `eval_metrics`, read beside a reader's judgement in the way `docs/EVAL.md` requires of
every count: Python counts, readers score.

The patterns are seeded from one record (Ellis Island v3, GLM-5.2) and are deliberately
incomplete. `contrast` and `dash_fragment` are structural and should carry to any corpus;
`abstract_agent`, `announce` and `unscoped` are word lists, and a word list learned from one
domain is a hypothesis about the next. Grow them from the sentences readers flag under the
rubric's plain-statement check, and drop an entry that fires mostly on good sentences elsewhere.

Quoted spans are removed before counting. The style block governs the words the reading writes,
never the words the material said.
"""
from __future__ import annotations

import re

# A quotation is the material talking, and the rules do not reach it. Both plain and curly pairs,
# bounded so an unbalanced quote mark cannot swallow the rest of a summary.
_QUOTED = re.compile(r'"[^"]{0,300}"|“[^”]{0,300}”|\'[^\']{0,120}\'')

SMELLS: dict[str, list[re.Pattern]] = {
    # rule 4 — a correction manufactured before the useful half of the sentence
    "contrast": [
        re.compile(r"\bnot\s+(merely|simply|just|only)\b", re.I),
        re.compile(r"\bnot\s+\w+(\s+\w+){0,3},\s+but\b", re.I),
        re.compile(r",\s*not\s+(a|an|the)?\s*\w+\s*[.;]"),
        re.compile(r"\bless\s+\w+\s+than\b", re.I),
        re.compile(r"\bat once\b", re.I),
        re.compile(r"\bas much as\b", re.I),
    ],
    # rule 5 — a fragment standing in for a clause
    "dash_fragment": [
        re.compile(r"\s—\s[^—.?!]{1,25}[.;]"),
        re.compile(r":\s+[a-z][^.?!]{0,40}\.\s*$", re.M),
    ],
    # rule 2 — a verb the data cannot perform
    "abstract_agent": [
        re.compile(r"\b(narrates?|survives?\s+as|vanish(es)?|haunts?|enters?\s+as|demands?|"
                   r"coexists?|is\s+defined\s+by)\b", re.I),
    ],
    # rule 5 — a sentence that announces or evaluates instead of saying something
    "announce": [
        re.compile(r"\bmatters\s*\.", re.I),
        re.compile(r"^\s*one reading[:,]", re.I | re.M),
        re.compile(r"\b(at|lies)\s+the\s+heart\s+of\b", re.I),
        re.compile(r"\bin\s+two\s+registers\b", re.I),
        re.compile(r"\bwhat\s+\w+\s+does\s+to\s+another\b", re.I),
    ],
    # rule 3 — a claim about everything, with no scope in the sentence
    "unscoped": [
        re.compile(r"\b(the corpus|the material|these accounts)\s+"
                   r"(shows?|tells?|narrates?|says?|describes?)\b", re.I),
    ],
    # PROJECT rule 5 — a quantifier that speaks for every case, counted so a reader can check it
    # against the ids in the same bracket. The NEGATIVE form is why this exists: rule 5 named
    # "all", "every" and "consistently" and a corpus summary came back saying outputs were
    # "never accepted at face value" over a corpus where one participant accepted most of one.
    # A universal is often the right sentence, so this counts and a reader rules (docs/EVAL.md).
    "universal": [
        re.compile(r"\b(never|always|invariably|universally|unanimously|uniformly)\b", re.I),
        re.compile(r"\b(in|with)\s+(every|all|no)\s+(case|cases|instance|instances)\b", re.I),
        re.compile(r"\bwithout\s+exception\b", re.I),
        re.compile(r"\b(none|neither)\s+of\s+the\s+\w+", re.I),
        re.compile(r"\b(no|every|all|each)\s+"
                   r"(participants?|interviewees?|speakers?|materials?|accounts?|cases?)\b", re.I),
        re.compile(r"\b(everyone|nobody|no\s+one)\b", re.I),
    ],
}


def count(*texts: str) -> dict[str, int]:
    """How many times each kind fires across these pieces of prose. Kinds that fire none are left
    out, so an empty dict is the ordinary answer and reads as one."""
    found: dict[str, int] = {}
    for text in texts:
        bare = _QUOTED.sub(" ", text or "")
        for kind, patterns in SMELLS.items():
            n = sum(len(p.findall(bare)) for p in patterns)
            if n:
                found[kind] = found.get(kind, 0) + n
    return found


def note(*texts: str) -> str | None:
    """One line for the run row, or None where the prose is clean. It says what was counted and
    in what, and never says the prose is wrong: a researcher reading the row is the one who
    decides whether the sentence it points at earns its shape."""
    found = count(*texts)
    if not found:
        return None
    total = sum(found.values())
    parts = ", ".join(f"{k} {n}" for k, n in sorted(found.items()))
    return f"style: {total} phrase(s) of the kind the prose rules name ({parts})"
