"""A file of some kind becomes text. That is the whole job.

Nothing here decides what a material *is* — no kind, no shape, no speakers. The frame step does
that, from the text, the same way for a pasted paragraph as for an uploaded document. So this
module is five small readers and a table of extensions, and it never grows a classifier.

A spreadsheet of open answers is the one shape that needs arranging rather than reading: a row is
a person, a column is a question, and both have to survive into the text or the reading cannot
tell one respondent from another. So each row becomes a headed block of `question: answer` lines.
It is still one material.

Failure is a sentence a person can read, never a traceback: the file that failed and what kind it
was, because the researcher chose the file and is the one who can choose a different one.
"""
from __future__ import annotations

import csv
import io
import os
import re

KINDS = (".txt", ".md", ".docx", ".pdf", ".csv")
_ID_MAX = 24            # longer than this, or with a space in it, and a first column is an answer


class IntakeError(Exception):
    """One sentence, no newline, naming the file and its kind."""


def _plain(data: bytes) -> str:
    """UTF-8, falling back to latin-1, which cannot fail — a transcript typed on an old machine
    is still a transcript, and refusing it teaches the researcher nothing."""
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("latin-1")


def _docx(data: bytes) -> str:
    import docx

    return "\n".join(p.text for p in docx.Document(io.BytesIO(data)).paragraphs)


# A page is laid out in columns when this share of its lines has a wide gap between two runs of
# text. Measured on thirteen real PDFs: single-column pages sat at 0–19%, two-column papers and a
# patent at 92–100%, nothing in between.
COLUMNS_AT = 0.5
_GAP = re.compile(r"\S {4,}\S")


def _page(page) -> str:
    """One page's text, words whole.

    pypdf's default reading starts a new line wherever the PDF starts a new run of text, and a
    run can start in the middle of a word. A Library of Congress transcript came out as "vacation
    d ays" and "why did we co me there" — 74 words split on its own pages, and on most real PDFs
    tried, 7 to 29 a page. Every quote across one of those splits is then correctly reported as
    not in the material, because it is not in what was stored: three of an interview's claims
    were thrown out that way, one of them the only record of her hours being cut.

    Layout mode reads by position and keeps words whole. On a page set in columns it would print
    the columns side by side, one line from each, which is worse than a split word — so such a
    page keeps the default reading order. ponytail: a column page still carries its default-mode
    splits; re-joining runs by glyph position is the upgrade if a two-column source matters.
    """
    laid = page.extract_text(extraction_mode="layout") or ""
    lines = [ln for ln in laid.split("\n") if ln.strip()]
    if lines and sum(bool(_GAP.search(ln)) for ln in lines) / len(lines) >= COLUMNS_AT:
        return page.extract_text() or ""
    # Layout mode indents with spaces to where the text sat on the page; the words are what matter.
    return "\n".join(re.sub(r"[ \t]+", " ", ln).strip() for ln in laid.split("\n"))


def _pdf(data: bytes) -> str:
    import pypdf

    # A PDF whose trailer was never written — truncated in transit, or from a sloppy generator —
    # has no cross-reference table to follow and pypdf refuses it outright. Handing it a trailer
    # that points nowhere sends it down its own rebuild path instead, which reads the objects.
    if b"startxref" not in data:
        data += b"\nstartxref\n0\n%%EOF\n"
    return "\n".join(_page(p) for p in pypdf.PdfReader(io.BytesIO(data)).pages)


def _csv(data: bytes) -> str:
    rows = list(csv.reader(io.StringIO(_plain(data), newline="")))
    if not rows:
        return ""
    header, blocks = rows[0], []
    for n, row in enumerate(rows[1:], start=1):
        if not any(c.strip() for c in row):
            continue
        first = row[0].strip()
        identifier = first and len(first) <= _ID_MAX and " " not in first and "\t" not in first
        lines = [first if identifier else f"Respondent {n}"]
        lines += [f"{q.strip()}: {a.strip()}"
                  for q, a in zip(header[1 if identifier else 0:], row[1 if identifier else 0:])
                  if a.strip()]
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


_READERS = {".txt": _plain, ".md": _plain, ".csv": _csv, ".docx": _docx, ".pdf": _pdf}


def extract(filename: str, data: bytes) -> str:
    """The text inside a file, or `IntakeError` saying why there is none."""
    ext = os.path.splitext(filename or "")[1].lower()
    read = _READERS.get(ext)
    if read is None:
        # The file, not the extension: twelve files go in at once and only one of them is wrong.
        raise IntakeError(f"{filename or 'that file'} is not a kind of material this reads — it "
                          f"takes {', '.join(KINDS[:-1])} and {KINDS[-1]}.")
    try:
        text = read(data)
    except Exception as e:                            # a trace helps nobody here, but its name does
        raise IntakeError(f"{filename} could not be opened as a {ext.lstrip('.')} file "
                          f"({type(e).__name__}).") from None
    if not text.strip():
        raise IntakeError(f"{filename} has no text in it.")
    return text
