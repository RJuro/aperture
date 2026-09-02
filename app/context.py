"""One function per page. Each returns a plain dict; the template only renders it.

Two rules hold this file together.

**Nothing is copied field by field.** Rows go to the page as `dict(row)`, whole. Three times in
the old engine an explicit key list on the way to a template silently dropped a validated quote
and the suite stayed green, so there are no key lists here: if a column exists, the page has it.

**Our vocabulary stays in the code.** `_BANNED` is the design language — it names things
precisely for us and would be jargon on the page. Variables, keys and comments may say *moment*,
*thread*, *frame*; the rendered page says *material*, *what this is*, *what the reading found*,
*Check this against the material*, *Reading record*.
"""
from __future__ import annotations

import json
import re

from markupsafe import Markup

from . import store

APP_NAME = "Aperture"

# Words the app must never say in its own voice. Checked against APP_AUTHORED strings and against
# rendered pages with quoted material, marks and model prose stripped out.
_BANNED = [
    "panel", "standard coding", "friction", "merge proposal", "consolidate", "weakest", "door",
    "anchor", "exposure", "ledger", "residue", "territory", "territories", "register lane",
    "roster", "slot", "steer", "gate", "check-back", "checkback", "delta", "fact panel",
    "absence check", "defensible account", "frame", "moment", "thread",
]

# Context keys whose strings this app wrote, as opposed to the researcher's, the material's or the
# model's. Only these are ours to police. `line` is deliberately absent: a run's progress line is
# written by jobs.py and shown verbatim, the same as any other text we did not author.
APP_AUTHORED = ("app_name", "derivation", "kind", "state", "stage", "verdict", "line")

PARA = 5        # sentences per block when the material has no structure to group by


# ---- escaping ----------------------------------------------------------------------------------

def _esc(s) -> str:
    """Text-node escaping and nothing else.

    Straight quotes and apostrophes are left exactly as they are: a quote that was validated
    character-for-character against the material must reach the page character-for-character, and
    `&#39;` is not what the speaker said. Never use this inside an attribute.
    """
    s = "" if s is None else str(s)
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def txt(s) -> Markup:
    return Markup(_esc(s))


# A project claim rests on moments, not on new quotes, so PROJECT cites moment ids in its prose.
_CITE = re.compile(r"\bmo[0-9a-f]{6,}\b")


def cite(text: str, index: dict, pid: str) -> Markup:
    """Model prose with each moment id it cites turned into a link into the material it rests on.

    Every run of prose is wrapped separately, because model prose is not the app speaking and must
    never be read as if it were.
    """
    def one(part: str) -> str:
        """One paragraph: prose escaped, citations turned into links into the material."""
        out, at = [], 0
        for m in _CITE.finditer(part):
            t = index.get(m.group(0))
            if t is None:
                continue
            out.append(f'<span class="summary">{_esc(part[at:m.start()])}</span>')
            out.append(f'<a class="claim cite" href="/p/{pid}/m/{t["material_id"]}'
                       f'?thread={t["theme_id"]}#{t["sid"]}">{t["sid"]}</a>')
            at = m.end()
        out.append(f'<span class="summary">{_esc(part[at:])}</span>')
        return "".join(out)

    # The summary is three hundred words of argument, and the model breaks it into paragraphs
    # where the argument turns. Rendering it as one block throws that structure away and gives the
    # researcher a wall to read; a blank line in, a paragraph out.
    paras = [p.strip() for p in re.split(r"\n\s*\n", text or "") if p.strip()]
    return Markup("".join(f"<p>{one(p)}</p>" for p in paras) or "")


def _cite_index(conn, pid: str) -> dict:
    return {m["id"]: dict(m) for mat in store.materials(conn, pid)
            for m in store.moments(conn, mat["id"])}


# ---- the material, with this theme's quotes marked ----------------------------------------------

def _merge(spans: list[tuple[int, int]]) -> list[list[int]]:
    out: list[list[int]] = []
    for s, e in sorted(spans):
        if out and s <= out[-1][1]:
            out[-1][1] = max(out[-1][1], e)
        else:
            out.append([s, e])
    return out


def _mark(text: str, quotes: list[str]) -> str:
    """`text` with each quote wrapped in `<mark>`, escaped before any markup is inserted.

    A quote that cannot be located exactly marks its whole sentence: the reader must still see
    that the reading rested here, and a lost mark is worse than a wide one.
    """
    spans = []
    for q in quotes:
        q = (q or "").strip()
        if not q:
            continue
        i = text.find(q)
        if i < 0 and len(text.casefold()) == len(text) and len(q.casefold()) == len(q):
            # ponytail: exact, then same-length case-fold. A quote re-typed with different
            # punctuation falls through to the whole sentence, which is the honest fallback.
            i = text.casefold().find(q.casefold())
        spans.append((0, len(text)) if i < 0 else (i, i + len(q)))
    if not spans:
        return _esc(text)
    out, at = [], 0
    for s, e in _merge(spans):
        s, e = max(s, at), max(e, at)
        out.append(_esc(text[at:s]))
        out.append(f"<mark>{_esc(text[s:e])}</mark>")
        at = e
    out.append(_esc(text[at:]))
    return "".join(out)


def _sentence(row, quotes: list[str]) -> str:
    # Whitespace is collapsed: transcripts carry tabs from their original typesetting, and a quote
    # is validated against collapsed text, so the page must show collapsed text or the mark misses.
    return (f'<span class="s" id="{row["sid"]}">'
            f'{_mark(" ".join(row["text"].split()), quotes)}</span>')


def blocks(conn, mid: str, display: str, quotes_by_sid: dict[str, list[str]]) -> list[dict]:
    """The material laid out as the frame says it should be: grouped speaker turns, labelled
    sections, or plain blocks. Unmarked text is what the reading did not claim on."""
    rows = [dict(r) for r in store.sentence_rows(conn, mid)]

    def block(group, label="", n=None):
        return {"label": label, "n": n,
                "html": Markup(" ".join(_sentence(r, quotes_by_sid.get(r["sid"], []))
                                        for r in group))}

    out: list[dict] = []
    if display == "turns":
        cur, at = [], None
        for r in rows:
            if cur and r["turn_idx"] != at:
                out.append(block(cur, n=at))
                cur = []
            at = r["turn_idx"]
            cur.append(r)
        if cur:
            out.append(block(cur, n=at))
        return out
    if display == "segments":
        starts = {s["sid"]: s["label"] for s in store.segments(conn, mid)}
        cur, label = [], ""
        for r in rows:
            if r["sid"] in starts:
                if cur:
                    out.append(block(cur, label=label))
                    cur = []
                label = starts[r["sid"]]
            cur.append(r)
        if cur:
            out.append(block(cur, label=label))
        return out
    # ponytail: ingest keeps sentences, not blank lines, so plain material is blocked in fives.
    # Record line offsets at ingest if real paragraphs ever matter.
    return [block(rows[i:i + PARA]) for i in range(0, len(rows), PARA)]


# ---- shared pieces ------------------------------------------------------------------------------

def derivation(conn, mid: str) -> str:
    """Law 4: a number is printed as the derivation it came from, never as a bare figure."""
    return (f"claims rest on {len(store.cited_sids(conn, mid))} "
            f"of {len(store.sentences(conn, mid))} passages")


def _row(r) -> dict | None:
    return dict(r) if r is not None else None


def _checks(conn, pid: str, ref_id: str | None = None) -> list[dict]:
    """Whole rows, with the stored quotes decoded — a check without its quotes is an opinion."""
    out = []
    for c in store.checks(conn, pid):
        if ref_id is not None and c["ref_id"] != ref_id:
            continue
        d = dict(c)
        try:
            d["anchors"] = json.loads(d.get("anchors_json") or "[]")
        except ValueError:
            d["anchors"] = []
        # A check on the project page is otherwise an orphaned question: at twenty materials the
        # list says what was asked and never of what.
        if c["scope"] == "material":
            m = store.material(conn, c["ref_id"])
            d["material_name"] = (m["title"] or m["name"]) if m else ""
        else:
            d["material_name"] = ""
        out.append(d)
    return out


def _shell(conn, pid: str) -> dict:
    return {"app_name": APP_NAME, "runs": [dict(r) for r in store.active_runs(conn, pid)]}


def _threads(conn, mid: str, themes: dict) -> list[dict]:
    """Every live moment on this material, grouped by its theme — built from the rows, so a theme
    that was merged away still carries its moments into the record."""
    by: dict[str, list[dict]] = {}
    for m in store.moments(conn, mid):
        by.setdefault(m["theme_id"], []).append(dict(m))
    return [{"theme": themes.get(t, {"id": t, "name": t, "gist": ""}), "moments": ms}
            for t, ms in by.items()]


# ---- the pages ----------------------------------------------------------------------------------

def home(conn) -> dict:
    rows = conn.execute("SELECT * FROM project ORDER BY created_at DESC").fetchall()
    return {"app_name": APP_NAME, "runs": [], "projects": [dict(r) for r in rows]}


def project_page(conn, pid: str) -> dict:
    p = store.project(conn, pid)
    if p is None:
        return {}
    mats = [dict(m) for m in store.materials(conn, pid)]
    stale = {m["id"] for m in store.out_of_date(conn, pid)}
    for m in mats:
        m["derivation"] = derivation(conn, m["id"])
        m["out_of_date"] = m["id"] in stale
    themes = []
    for t in store.live_themes(conn, pid):
        row = dict(t)
        row["columns"] = [{"material": m,
                           "moments": [dict(x) for x in store.thread(conn, m["id"], t["id"])]}
                          for m in mats]
        themes.append(row)
    fb = [dict(f) for f in store.project_feedback(conn, pid)]
    summary = _row(store.get_summary(conn, "project", pid))
    return {**_shell(conn, pid), "project": dict(p), "materials": mats, "themes": themes,
            "summary": summary,
            "summary_html": cite(summary["text"], _cite_index(conn, pid), pid) if summary else "",
            "focus_history": [f for f in fb if f["target_kind"] == "focus"],
            "checks": _checks(conn, pid)}


def material_page(conn, pid: str, mid: str, theme_id: str | None = None) -> dict:
    p, m = store.project(conn, pid), store.material(conn, mid)
    if p is None or m is None or m["project_id"] != pid:
        return {}
    mat = dict(m)
    cards = []
    for t in store.live_themes(conn, pid):
        ms = [dict(x) for x in store.thread(conn, mid, t["id"])]
        if not ms:
            continue
        for x in ms:
            x["reactions"] = [dict(f) for f in store.feedback_for(conn, "moment", x["id"])]
        cards.append({**dict(t), "moments": ms,
                      "codes": [dict(c) for c in store.theme_codes(conn, t["id"], mid)]})
    selected = next((c for c in cards if c["id"] == theme_id), None) or (cards[0] if cards else None)
    quotes: dict[str, list[str]] = {}
    for x in (selected["moments"] if selected else []):
        quotes.setdefault(x["sid"], []).append(x["anchor"])
    summary = _row(store.get_summary(conn, "material", mid))
    return {**_shell(conn, pid), "project": dict(p), "material": mat, "cards": cards,
            "selected": selected, "derivation": derivation(conn, mid),
            "summary": summary,
            "summary_html": cite(summary["text"], _cite_index(conn, pid), pid) if summary else "",
            "people": [dict(x) for x in store.people(conn, mid)],
            "speakers": [dict(x) for x in store.speakers(conn, mid)],
            "blocks": blocks(conn, mid, mat.get("display") or "plain", quotes),
            "checks": _checks(conn, pid, mid)}


def export(conn, pid: str) -> dict:
    p = store.project(conn, pid)
    if p is None:
        return {}
    themes = {t["id"]: dict(t) for t in store.live_themes(conn, pid)}
    mats = []
    for m in store.materials(conn, pid):
        d = dict(m)
        d["orientation"] = _row(store.get_summary(conn, "material", m["id"], "orientation"))
        d["reading"] = _row(store.get_summary(conn, "material", m["id"], "reading"))
        d["people"] = [dict(x) for x in store.people(conn, m["id"])]
        d["speakers"] = [dict(x) for x in store.speakers(conn, m["id"])]
        d["threads"] = _threads(conn, m["id"], themes)
        d["derivation"] = derivation(conn, m["id"])
        mats.append(d)
    return {"app_name": APP_NAME, "project": dict(p), "materials": mats,
            "summary": _row(store.get_summary(conn, "project", pid)),
            "themes": list(themes.values()),
            "checks": _checks(conn, pid),
            "feedback": [dict(f) for f in store.project_feedback(conn, pid)],
            "runs": [dict(r) for r in store.runs(conn, pid)]}
