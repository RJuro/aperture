"""One visible naming convention for every kind of material.

Python composes the title from what the frame validated — the participants it could find in the
material, the kind it settled on, the year it read — because a standard asked of the model is a
standard kept some of the time.  The model's own title is only the fallback for material with
nobody named in it, and it still arrives in all caps or wrapped in Markdown emphasis often enough
that `standardize` cleans it on the way past.
"""
from __future__ import annotations

import re

_QUIET = {"a", "an", "and", "at", "by", "de", "del", "der", "di", "for", "from", "in",
          "la", "le", "of", "on", "the", "to", "van", "von", "with"}
_DESCRIPTORS = {"document", "fieldnotes", "group", "history", "interview", "notes", "oral",
                "responses", "survey", "transcript"}
_KINDS = {"interview": "interview", "focus_group": "focus group", "fieldnotes": "field notes",
          "document": "document", "open_text": "open responses", "other": ""}


def standardize(value: str) -> str:
    """Strip presentation markup and turn all-caps archive labels into calm sentence case.

    Mixed-case titles are already editorial decisions and are left alone.  This deliberately does
    not attempt to infer missing dates, people, or document types.
    """
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    text = re.sub(r"^[#*_`\s]+|[#*_`\s]+$", "", text).strip()
    letters = [c for c in text if c.isalpha()]
    if not letters or sum(c.isupper() for c in letters) / len(letters) < .85:
        return text

    words = re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ]+(?:['’][A-Za-zÀ-ÖØ-öø-ÿ]+)?|[^A-Za-zÀ-ÖØ-öø-ÿ]+", text)
    seen_word = 0
    out = []
    for token in words:
        if not token[0].isalpha():
            out.append(token)
            continue
        low = token.lower()
        if seen_word and (low in _QUIET or low in _DESCRIPTORS):
            out.append(low)
        elif len(token) <= 4 and token in {"USA", "UK", "EU", "UN", "NATO"}:
            out.append(token)
        else:
            out.append(low[:1].upper() + low[1:])
        seen_word += 1
    return "".join(out)


def compose(kind: str, speakers: list[dict], model_title: str, year: str) -> str:
    """The title as Python writes it: who is in the material, what it is, when it was made.

    At most two participants, because a five-person focus group named in full is not a title.  An
    empty part takes its separator with it, so nothing ever ends in a dangling dash or comma, and
    material this composes nothing for gets `""` — `context._material_title` falls back to the
    filename, which is the only name such a piece has ever had.
    """
    named = [str(s.get("name") or "").strip() for s in speakers or []
             if s.get("role") == "participant"]
    head = " and ".join([n for n in named if n][:2]) or standardize(model_title)
    tail = ", ".join(p for p in (_KINDS.get(kind, ""), str(year or "").strip()) if p)
    return " — ".join(p for p in (head, tail) if p)
