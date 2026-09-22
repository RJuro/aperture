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


def abbreviate(title: str) -> str:
    """A code a citation can carry inline: "LA" for "Livicia Antoine interview, Domestic Workers
    United", "MG" for "Mary Grande — interview, 1974", "C12" for "Card 12".

    The initials of the first three words that name something, from the part of the title before
    its kind-and-year tail. Words like "interview" or "the" say nothing about which material this
    is, and a comma-clause is read only when the part before it is a single word — "Grande, M." is
    a surname and an initial, where "Livicia Antoine interview, Domestic Workers United" is a
    person and then an organisation. The first number rides along, since a researcher's own
    "Card 12" is told apart by it. A single word keeps two letters, so "Rodwin" is "Ro" and not a
    lone "R" that looks like a typo.

    Uniqueness is the caller's job: it needs the other materials, and this needs only a title.
    """
    head = str(title or "").split(" — ")[0]
    words: list[str] = []
    number = ""
    for part in head.split(","):
        tokens = re.findall(r"[^\W\d_]+|\d+", part)
        number = number or next((t for t in tokens if t.isdigit()), "")
        words += [t for t in tokens if not t.isdigit()
                  and t.lower() not in _QUIET and t.lower() not in _DESCRIPTORS]
        if len(words) >= 2:
            break
    if len(words) == 1 and not number:
        return words[0][:2].capitalize()
    return ("".join(w[0].upper() for w in words[:3]) + number) or head.strip()[:3].upper() or "?"


if __name__ == "__main__":
    for given, want in [("Livicia Antoine interview, Domestic Workers United", "LA"),
                        ("Mary Grande — interview, 1974", "MG"), ("Grande, M.", "GM"),
                        ("Card 12", "C12"), ("Rodwin", "Ro"), ("DP-40 Grande", "DG40"),
                        ("Focus group, nurses", "FN"), ("Élodie Ørsted", "ÉØ"), ("", "?")]:
        assert abbreviate(given) == want, (given, abbreviate(given), want)
    print("ok")
