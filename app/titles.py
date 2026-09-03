"""One visible naming convention for every kind of material.

The model writes titles for new material, but older imports and archive filenames often arrive in
all caps or wrapped in Markdown emphasis.  Normalising at both write and display time means the
themes table never becomes a mixture of archival shouting and sentence case.
"""
from __future__ import annotations

import re

_QUIET = {"a", "an", "and", "at", "by", "de", "del", "der", "di", "for", "from", "in",
          "la", "le", "of", "on", "the", "to", "van", "von", "with"}
_DESCRIPTORS = {"document", "fieldnotes", "group", "history", "interview", "notes", "oral",
                "responses", "survey", "transcript"}


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
