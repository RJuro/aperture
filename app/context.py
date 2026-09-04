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

from . import store, titles

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
# model's. Only these are ours to police. `line` is ours too: a run's progress line is written by
# jobs.py, and it once said "threads" to a researcher.
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


# The model writes markdown whatever it is asked for, and a summary reached the page reading
# `*Belonging, identity, and return* follows an economic crossing` — asterisks and all. Emphasis
# is turned into markup AFTER escaping, so nothing in the prose can become markup that way.
# Both delimiters must touch a non-space character, which leaves `2 * 3` and a lone footnote
# star alone, and `_` is only a delimiter off a word boundary, so `mo_1` stays as written.
_EMPH = re.compile(r"\*\*(?=\S)(.+?)(?<=\S)\*\*|(?<![\w*])([*_])(?=\S)(.+?)(?<=\S)\2(?!\w)")


def _emph(html: str) -> str:
    """Escaped prose with markdown emphasis rendered. Only ever called on escaped text."""
    return _EMPH.sub(lambda m: f"<strong>{m[1]}</strong>" if m[1] is not None
                     else f"<em>{m[3]}</em>", html)


def prose(s) -> Markup:
    """`txt` for model prose: escaped, then its markdown emphasis rendered.

    Only for sentences the model wrote — a theme's gist, a thread's account. A quote, a name, a
    speaker label or the researcher's own words stay on `txt`, where an asterisk is an asterisk.
    """
    return Markup(_emph(_esc(s)))


# A project claim rests on moments, not on new quotes, so PROJECT cites moment ids in its prose.
_CITE = re.compile(r"\bmo[0-9a-f]{6,}\b")


def _live_cites(text: str, index: dict) -> str:
    """Prose with every citation whose claim is no longer live taken out — brackets, separator
    and all.

    A rerun below the corpus level supersedes the moments the corpus summary cites, and nothing
    re-runs the summary on that path, so its citations rot. The page was printing the raw ids as
    if they were words and the record was leaving the brackets standing empty. A citation that
    cannot be resolved is not a citation; it is nothing.

    And one passage is one citation: two claims can rest on the same passage, and both renderers
    below turn a claim into the passage it rests on — a link on the page, a sentence id in the
    record. `[S223, S223]` reached a blind judge of the record, who read it as two sources
    agreeing. The first claim on a passage keeps the citation and the rest go, separator and all.
    """
    def group(m):
        ids = _CITE.findall(m.group(0))
        if not ids:                       # [sic], [laughs] — the model's other brackets stay
            return m.group(0)
        live: dict[tuple, str] = {}
        for i in ids:                     # by PASSAGE, not by id: same sid in two materials is
            if i in index:                # two passages, and both are still worth citing
                live.setdefault((index[i]["material_id"], index[i]["sid"]), i)
        head = m.group(0)[:m.group(0).index("[")]
        return f'{head}[{", ".join(live.values())}]' if live else ""

    text = re.sub(r"[ ]*\[[^\[\]]*\]", group, text or "")
    return _CITE.sub(lambda m: m.group(0) if m.group(0) in index else "", text)


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
            out.append(f'<span class="summary">{_emph(_esc(part[at:m.start()]))}</span>')
            out.append(f'<a class="claim cite" href="/p/{pid}/m/{t["material_id"]}'
                       f'?theme={t["theme_id"]}#{t["sid"]}">{t["sid"]}</a>')
            at = m.end()
        out.append(f'<span class="summary">{_emph(_esc(part[at:]))}</span>')
        return "".join(out)

    # The summary is three hundred words of argument, and the model breaks it into paragraphs
    # where the argument turns. Rendering it as one block throws that structure away and gives the
    # researcher a wall to read; a blank line in, a paragraph out.
    paras = [p.strip() for p in re.split(r"\n\s*\n", _live_cites(text, index)) if p.strip()]
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


def _find(text: str, q: str) -> int:
    # ponytail: exact, then same-length case-fold. A quote re-typed with different punctuation
    # falls through to its whole sentence, which is the honest fallback.
    i = text.find(q)
    if i < 0 and len(text.casefold()) == len(text) and len(q.casefold()) == len(q):
        i = text.casefold().find(q.casefold())
    return i


def _mark(text: str, spans: list[list[int]]) -> str:
    """`text` with each span wrapped in `<mark>`, escaped before any markup is inserted."""
    clipped = [(max(s, 0), min(e, len(text))) for s, e in spans]
    out, at = [], 0
    for s, e in _merge([x for x in clipped if x[1] > x[0]]):
        s, e = max(s, at), max(e, at)
        out.append(_esc(text[at:s]))
        out.append(f"<mark>{_esc(text[s:e])}</mark>")
        at = e
    out.append(_esc(text[at:]))
    return "".join(out)


def _sentences(rows, quotes_by_sid: dict[str, list[str]]) -> str:
    """One block's sentences, each in its own span so it stays a link target, with every quote
    marked where it actually is.

    A quote may run across up to three sentences (`anchor.SPAN`), and it is attached to the one it
    starts in. Searching that one sentence for it found nothing and marked the whole of it
    instead — speaker cue and all — while the rest of the quote went unmarked. So the search runs
    over the block, and the mark is split at the boundary it crosses.

    Whitespace is collapsed: transcripts carry tabs from their original typesetting, and a quote
    is validated against collapsed text, so the page must show collapsed text or the mark misses.
    """
    texts = [" ".join(r["text"].split()) for r in rows]
    starts, at = [], 0
    for t in texts:
        starts.append(at)
        at += len(t) + 1                      # the single space the sentences are joined with
    joined = " ".join(texts)
    spans = []
    for i, r in enumerate(rows):
        for q in quotes_by_sid.get(r["sid"], []):
            q = (q or "").strip()
            if not q:
                continue
            j = _find(joined, q)
            spans.append((j, j + len(q)) if j >= 0
                         else (starts[i], starts[i] + len(texts[i])))
    return " ".join(
        f'<span class="s" id="{r["sid"]}">'
        f'{_mark(texts[i], [[s - starts[i], e - starts[i]] for s, e in spans])}</span>'
        for i, r in enumerate(rows))


def blocks(conn, mid: str, display: str, quotes_by_sid: dict[str, list[str]]) -> list[dict]:
    """The material laid out as the frame says it should be: grouped speaker turns, labelled
    sections, or plain blocks. Unmarked text is what the reading did not claim on."""
    rows = [dict(r) for r in store.sentence_rows(conn, mid)]

    def block(group, label="", n=None):
        return {"label": label, "n": n, "html": Markup(_sentences(group, quotes_by_sid))}

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
        # An estimated speaker is marked where the reader meets it. The label the model was shown
        # stays plain; this word is the page's, and it is the difference between a guess and a fact.
        mark = " \u00b7 estimated" if store.material(conn, mid)["speakers_estimated"] else ""
        starts = {s["sid"]: s["label"] + mark for s in store.segments(conn, mid)}
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
    said = (f"claims rest on {len(store.cited_sids(conn, mid))} "
            f"of {len(store.sentences(conn, mid))} passages")
    aside = store.set_aside_by_check(conn, mid)
    return said + (f", {aside} set aside as not carried by their passages" if aside else "")


def _n(n: int, noun: str) -> str:
    return f'{n} {noun}{"" if n == 1 else "s"}'


def _evidence(row: dict | None) -> str:
    """A theme's count in claims AND in the passages those claims rest on.

    Two claims on one passage are one piece of evidence read twice, and a passage another theme
    reads as well is evidence two themes are dividing between them. Counting claims alone made
    both look like more material than the reading has.
    """
    r = row or {"claims": 0, "passages": 0, "shared": 0}
    out = f'{_n(r["claims"], "claim")} on {_n(r["passages"], "passage")}'
    if r["shared"]:
        out += f' · {_n(r["shared"], "passage")} shared with other themes'
    return out


def _row(r) -> dict | None:
    return dict(r) if r is not None else None


def _material_title(row) -> str:
    return titles.standardize(row["title"] or row["name"])


def _analysis_steps(conn, row) -> list[dict]:
    """A compact receipt of which material-level analyses have actually landed."""
    mid = row["id"]
    finished = {r["kind"] for r in conn.execute(
        "SELECT kind FROM run WHERE material_id=? AND finished IS NOT NULL AND error IS NULL", (mid,))}
    active = {r["kind"] for r in conn.execute(
        "SELECT kind FROM run WHERE material_id=? AND finished IS NULL", (mid,))}
    failed_row = conn.execute("SELECT kind, error FROM run WHERE material_id=? AND error IS NOT "
                              "NULL ORDER BY rowid DESC LIMIT 1", (mid,)).fetchone()
    inferred = {
        "frame": bool(row["title"] or row["kind"]),
        "angles": store.get_summary(conn, "material", mid, "angles") is not None,
        "read": conn.execute("SELECT 1 FROM code_hit WHERE material_id=? LIMIT 1", (mid,)).fetchone()
                is not None,
        "doc": store.get_summary(conn, "material", mid, "reading") is not None,
    }
    labels = (("frame", "Structure"), ("angles", "Angles"), ("read", "Coding"),
              ("doc", "Synthesis"))
    out = []
    for kind, label in labels:
        state = "done" if kind in finished or inferred[kind] else "waiting"
        if kind in active:
            state = "active"
        elif failed_row and failed_row["kind"] == kind and state != "done":
            state = "failed"
        # A step marked failed and nothing else said what happened; the reason was on the run row
        # the whole time, and a researcher who cannot see it cannot tell a bad file from a dead
        # model.
        out.append({"kind": kind, "label": label, "state": state,
                    "error": failed_row["error"] if state == "failed" else ""})
    return out


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
            d["material_name"] = _material_title(m) if m else ""
        else:
            d["material_name"] = ""
        out.append(d)
    return out


def _css_version() -> str:
    """The stylesheet's mtime, appended to its URL. A browser cached the old file across a design
    change and the page ran rules that no longer existed; a versioned URL is the whole fix."""
    import os
    p = os.path.join(os.path.dirname(__file__), "static", "aperture.css")
    try:
        return str(int(os.stat(p).st_mtime))
    except OSError:
        return "0"


def data_persistent() -> bool:
    """Whether the data directory is a mounted volume. On a laptop APERTURE_DATA_DIR is unset and
    nothing is said; in a container it must be a mount, or a redeploy starts from an empty
    database — the loss the predecessor project already suffered once."""
    import os
    d = os.environ.get("APERTURE_DATA_DIR")
    return True if not d else os.path.ismount(d)


def _shell(conn, pid: str) -> dict:
    nav_materials = [{**dict(m), "display_title": _material_title(m)}
                     for m in store.materials(conn, pid)]
    runs = [dict(r) for r in store.active_runs(conn, pid)]
    # The banner used to read run rows alone, and a job that is queued has none yet — so a page
    # whose work was waiting on another project's chain said nothing, offered no Stop and did not
    # poll. The committed job row is what exists first; the run line is only the wording.
    return {"app_name": APP_NAME, "css_v": _css_version(), "data_persistent": data_persistent(),
            "runs": runs,
            "working": bool(runs) or store.summary_state(conn, pid)["working"],
            "nav_materials": nav_materials,
            "nav_theme_count": len(store.live_themes(conn, pid))}


def _threads(conn, mid: str, themes: dict) -> list[dict]:
    """Every live moment on this material, grouped by its theme — built from the rows, so a theme
    that was merged away still carries its moments into the record."""
    by: dict[str, list[dict]] = {}
    for m in store.moments(conn, mid):
        by.setdefault(m["theme_id"], []).append(dict(m))
    return [{"theme": themes.get(t, {"id": t, "name": t, "gist": ""}), "moments": ms,
             "summary": _row(store.get_summary(conn, "thread", f"{mid}:{t}", "reading"))}
            for t, ms in by.items()]


# ---- the pages ----------------------------------------------------------------------------------

def home(conn, user=None) -> dict:
    """Their projects. `user` is None on a database with no accounts in it, and then it is all of
    them — see `store.projects_for`."""
    return {"data_persistent": data_persistent(), "app_name": APP_NAME, "runs": [], "user": user,
            "projects": [dict(r) for r in store.projects_for(conn, user)]}


def project_page(conn, pid: str) -> dict:
    p = store.project(conn, pid)
    if p is None:
        return {}
    mats = [dict(m) for m in store.materials(conn, pid)]
    stale = {m["id"] for m in store.out_of_date(conn, pid)}
    for m in mats:
        m["display_title"] = _material_title(m)
        m["derivation"] = derivation(conn, m["id"])
        m["out_of_date"] = m["id"] in stale
        m["analysis"] = _analysis_steps(conn, m)
        m["analysis_done"] = sum(s["state"] == "done" for s in m["analysis"])
        # One word for where this material has got to, so the head can say how far the reading
        # has come without the reader counting four receipts across four rows.
        states = {s["state"] for s in m["analysis"]}
        m["reading"] = ("failed" if "failed" in states else "active" if "active" in states
                        else "done" if m["analysis_done"] == 4 else "waiting")
    reading = {k: sum(1 for m in mats if m["reading"] == k)
               for k in ("done", "active", "failed", "waiting")}
    # One query for the whole grid rather than themes x materials calls to `thread`: at twelve
    # themes and fifty materials that loop was six hundred queries to render a table of counts.
    counts: dict[tuple[str, str], int] = {}
    for r in conn.execute(
            "SELECT theme_id, material_id, COUNT(*) AS n FROM moment "
            "WHERE status='live' GROUP BY theme_id, material_id"):
        counts[(r["theme_id"], r["material_id"])] = r["n"]
    evidence = store.theme_evidence(conn, pid)
    themes = []
    for t in store.live_themes(conn, pid):
        row = dict(t)
        row["columns"] = [{"material_id": m["id"], "material": m,
                           "moments": [None] * counts.get((t["id"], m["id"]), 0)}
                          for m in mats]
        carried = sum(1 for c in row["columns"] if c["moments"])
        # A theme resting on one material is a motif in that material, not a corpus theme, and
        # listed beside the others it reads as if it had the same reach. `single` is what the
        # page groups by.
        row["single"] = carried < 2
        row["reach"], row["claims"] = carried, sum(len(c["moments"]) for c in row["columns"])
        # Three steps, so the table can set the strongest themes larger: carried by every
        # material, by several, or by one.
        row["tier"] = 3 if row["single"] else 1 if carried == len(mats) else 2
        row["derivation"] = (f'{carried} of {len(mats)} materials · '
                             f'{_evidence(evidence.get(t["id"]))}')
        themes.append(row)
    # `live_themes` orders by name, which other pages depend on. Alphabetical here made a theme
    # every material carries with twenty claims look like one a single reading mentioned twice.
    themes.sort(key=lambda r: (-r["reach"], -r["claims"], r["name"]))
    fb = [dict(f) for f in store.project_feedback(conn, pid)]
    index = _cite_index(conn, pid)
    summary = _row(store.get_summary(conn, "project", pid))
    # What it may mean, kept apart from what it shows: one is cited, the other argued with.
    reading_of = _row(store.get_summary(conn, "project", pid, "interpretation"))
    return {**_shell(conn, pid), "project": dict(p), "materials": mats, "themes": themes,
            "page_section": "overview", "reading": reading,
            "summary": summary,
            "summary_html": cite(summary["text"], index, pid) if summary else "",
            "interpretation": reading_of,
            "interpretation_html": cite(reading_of["text"], index, pid) if reading_of else "",
            "summary_state": store.summary_state(conn, pid),
            "focus_history": [f for f in fb if f["target_kind"] == "focus"],
            "checks": _checks(conn, pid)}


def material_page(conn, pid: str, mid: str, theme_id: str | None = None) -> dict:
    p, m = store.project(conn, pid), store.material(conn, mid)
    if p is None or m is None or m["project_id"] != pid:
        return {}
    mat = dict(m)
    mat["display_title"] = _material_title(m)
    mat["analysis"] = _analysis_steps(conn, m)
    cards = []
    live = [dict(t) for t in store.live_themes(conn, pid)]
    for t in live:
        ms = [dict(x) for x in store.thread(conn, mid, t["id"])]
        if not ms:
            continue
        for x in ms:
            x["reactions"] = [dict(f) for f in store.feedback_for(conn, "moment", x["id"])]
        cards.append({**dict(t), "moments": ms,
                      "summary": _row(store.get_summary(conn, "thread", f'{mid}:{t["id"]}',
                                                        "reading")),
                      "codes": [dict(c) for c in store.theme_codes(conn, t["id"], mid)]})
    selected = next((c for c in cards if c["id"] == theme_id), None) or (cards[0] if cards else None)
    # Which other themes read the same passage. One query over this material's live claims: the
    # reader was seeing a claim as if the passage under it belonged to the theme they are in.
    names = {t["id"]: t["name"] for t in live}
    also: dict[str, list[str]] = {}
    for x in store.moments(conn, mid):
        also.setdefault(x["sid"], []).append(x["theme_id"])
    quotes: dict[str, list[str]] = {}
    for x in (selected["moments"] if selected else []):
        quotes.setdefault(x["sid"], []).append(x["anchor"])
        x["also_under"] = [{"id": t, "name": names[t]}
                           for t in dict.fromkeys(also.get(x["sid"], []))
                           if t != selected["id"] and t in names]
    summary = _row(store.get_summary(conn, "material", mid))
    return {**_shell(conn, pid), "project": dict(p), "material": mat, "cards": cards,
            "page_section": "materials",
            "selected": selected, "derivation": derivation(conn, mid),
            "summary": summary,
            "summary_html": cite(summary["text"], _cite_index(conn, pid), pid) if summary else "",
            "people": [dict(x) for x in store.people(conn, mid)],
            "speakers": [dict(x) for x in store.speakers(conn, mid)],
            "blocks": blocks(conn, mid, mat.get("display") or "plain", quotes),
            "set_aside": store.set_aside(conn, pid, mid),
            "checks": _checks(conn, pid, mid)}


def theme_page(conn, pid: str, tid: str) -> dict:
    """One theme across the whole corpus — the level the analysis is actually written up at.

    Before this page a theme was a name, forty words, and a row of table cells: at fifty
    materials it would have carried four hundred claims and still forty words. The account is the
    prose; the coverage line is the derivation; and the materials WITHOUT the theme are named,
    because at corpus level absence is as much a finding as presence and nothing else shows it.
    """
    from .engine import account

    p = store.project(conn, pid)
    t = conn.execute("SELECT * FROM theme WHERE id=? AND project_id=?", (tid, pid)).fetchone()
    if p is None or t is None:
        return {}
    cover = account.coverage(conn, pid, tid)
    carrying, absent = [], []
    for m in cover["per_material"]:
        row = dict(m)
        row["display_title"] = _material_title(m)
        if m["claims"]:
            row["moments"] = [dict(x) for x in store.thread(conn, m["material_id"], tid)]
            carrying.append(row)
        else:
            absent.append(row)
    summary = _row(store.get_summary(conn, "theme", tid))
    return {**_shell(conn, pid), "project": dict(p), "theme": dict(t),
            "page_section": "themes",
            "coverage": cover, "carrying": carrying, "absent": absent, "summary": summary,
            "summary_html": cite(summary["text"], _cite_index(conn, pid), pid) if summary else "",
            "derivation": (f'{cover["materials_with"]} of {cover["materials_total"]} materials'
                           f' · {_evidence(store.theme_evidence(conn, pid).get(tid))}'),
            "codes": [dict(c) for c in store.theme_codes(conn, tid)],
            "set_aside": store.set_aside(conn, pid)}


# The model brackets its citations, as the prompt asks it to: `[mo7c1d4af9]`, `[mo7c1d, mo90b2]`.
_CITE_GROUP = re.compile(r"\[\s*(mo[0-9a-f]{6,}(?:[\s,]+mo[0-9a-f]{6,})*)\s*\]")


def _export_resolve_ids(text: str, index: dict) -> str:
    """Model prose cites claims by internal id. On a page those become links; in a document they
    would sit there as opaque tokens — the first review's complaint about the record. Each becomes
    the sentence id a reader can find in the same document.

    A citation the model had already bracketed came out bracketed twice, `[[S041]]`, because the
    id is replaced by a bracketed id: the brackets the model wrote are the ones to fill.
    """
    text = _live_cites(text, index)
    text = _CITE_GROUP.sub(
        lambda m: "[" + ", ".join(index[i]["sid"] for i in _CITE.findall(m.group(1))) + "]", text)
    return _CITE.sub(lambda m: f"[{index[m.group(0)]['sid']}]", text)


def export(conn, pid: str, resolve: bool = True) -> dict:
    """The whole record as one document.

    Sectioned rather than flat, because at fifty materials the flat version was unreadable: the
    corpus, then each theme across the corpus, then each material, then the checks, what the
    readings set aside, what the researcher said, the runs as totals, and how the themes were
    renamed. `runs` stays the rows — the template groups them; a page that printed one line per
    run printed two hundred and fifty of them.
    """
    p = store.project(conn, pid)
    if p is None:
        return {}
    aside = _export_set_aside(conn, pid)
    themes = {t["id"]: dict(t) for t in store.live_themes(conn, pid)}
    mats = []
    for m in store.materials(conn, pid):
        d = dict(m)
        d["display_title"] = _material_title(m)
        for stage in ("orientation", "reading", "angles"):
            d[stage] = _row(store.get_summary(conn, "material", m["id"], stage))
        d["people"] = [dict(x) for x in store.people(conn, m["id"])]
        d["speakers"] = [dict(x) for x in store.speakers(conn, m["id"])]
        d["threads"] = _threads(conn, m["id"], themes)
        d["derivation"] = derivation(conn, m["id"])
        mats.append(d)
    said = _export_comments(conn, pid)
    ctx = {"app_name": APP_NAME, "project": dict(p), "materials": mats,
            "summary": _row(store.get_summary(conn, "project", pid)),
            "interpretation": _row(store.get_summary(conn, "project", pid, "interpretation")),
            "themes": _export_themes(conn, pid, aside),
            "checks": _checks(conn, pid),
            "set_aside": aside,
            "feedback": said,
            "focus_history": [f for f in said if f["target_kind"] == "focus"],
            "theme_history": _export_theme_history(conn, pid),
            "runs": [{**dict(r), "step": _export_step(r["kind"])}
                     for r in store.runs(conn, pid)]}
    # `resolve` is off for the record page: there a claim id becomes a link into the material it
    # rests on, and only a document — which has no links — needs it printed as a sentence id.
    return _export_resolve_all(ctx, _cite_index(conn, pid)) if resolve else ctx


def record_page(conn, pid: str) -> dict:
    """The record as a page in the app, from the same context the downloads are built from.

    Nothing here is new: it is the document, in the app's own two registers — the reading face for
    what the model and the app say, monospace for the material's own words — with the citations
    live and the two downloads at the top. `runs` belongs to the shell, which is why the record's
    own runs travel as `history`.
    """
    ctx = export(conn, pid, resolve=False)
    if not ctx:
        return {}
    return {**ctx, "history": ctx["runs"], **_shell(conn, pid),
            "cites": _cite_index(conn, pid), "page_section": "record"}


def _export_resolve_all(obj, index: dict):
    """Every prose string in the export context, with internal claim ids turned into sentence ids.
    Walks the whole context rather than naming fields — a named list is how a field gets missed."""
    if isinstance(obj, str):
        # A string that IS an id is a row's identifier and stays exactly as it is — the first
        # version of this walk turned every moment's own `id` into "[S040]" and a column-coverage
        # test caught it. Only text that CONTAINS an id among other words is prose citing a claim.
        if _CITE.fullmatch(obj.strip()):
            return obj
        return _export_resolve_ids(obj, index) if _CITE.search(obj) else obj
    if isinstance(obj, dict):
        return {k: _export_resolve_all(v, index) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_export_resolve_all(v, index) for v in obj]
    return obj



def _export_step(kind: str) -> str:
    """What a run of this kind was doing, in the words the app already uses while it runs.

    `kind` alone is a machine label — a researcher reading `doc — 2 runs` learns nothing. The
    material's name comes out of the line: a totals row is every run of that step, not one
    material's.
    """
    from . import jobs
    return re.sub(r"\s*(in )?\{name\}", "", jobs.STEPS.get(kind, (kind,))[0])


def _export_names(conn, pid: str) -> dict[str, str]:
    """Material id → what a person calls it. An id in a document is not a reference.

    Every material the project has ever held, not only the live ones: a note about a material
    that was later removed still has to name it, and `store.materials` would leave it printing
    as `m4f1c…` in the record of what the researcher said.
    """
    return {m["id"]: _material_title(m) for m in
            conn.execute("SELECT * FROM material WHERE project_id=?", (pid,))}


def _export_set_aside(conn, pid: str) -> list[dict]:
    """What the readings dropped, newest first, each with the material it came from.

    `store.set_aside` returns the notes alone, which is right for one material's page and wrong
    here: at fifty materials a note that names no material cannot be followed up.
    """
    names = _export_names(conn, pid)
    out = []
    for r in conn.execute("SELECT notes, material_id FROM run WHERE project_id=? "
                          "AND notes NOT IN ('', '[]') ORDER BY rowid DESC", (pid,)):
        try:
            notes = json.loads(r["notes"])
        except ValueError:
            continue
        out += [{"note": n, "material": names.get(r["material_id"], "")} for n in notes]
    return out


def _export_themes(conn, pid: str, aside: list[dict]) -> list[dict]:
    """Each live theme across the corpus: where it runs, where it does not, and — beside the
    absence — any note that named it on the way out, so a silence is never asserted over a line
    that was found and dropped."""
    from .engine import account

    out = []
    evidence = store.theme_evidence(conn, pid)
    for t in store.live_themes(conn, pid):
        cover = account.coverage(conn, pid, t["id"])
        carrying, absent = [], []
        for m in cover["per_material"]:
            row = dict(m)
            row["display_title"] = _material_title(m)
            if m["claims"]:
                row["moments"] = [dict(x) for x in store.thread(conn, m["material_id"], t["id"])]
                carrying.append(row)
            else:
                absent.append(row)
        out.append({**dict(t), "account": _row(store.get_summary(conn, "theme", t["id"])),
                    "carrying": carrying, "absent": absent,
                    "single": cover["materials_with"] < 2,
                    "derivation": (f'in {cover["materials_with"]} of {cover["materials_total"]} '
                                   f'materials · {_evidence(evidence.get(t["id"]))}'),
                    "set_aside": [n for n in aside if t["name"] and t["name"] in n["note"]]})
    return out


def _export_theme_history(conn, pid: str) -> list[dict]:
    """Every theme that was renamed or rewritten, with what it used to say. Merged themes are in
    here too: the evolution of a theme is the analysis, and a merge is part of it."""
    out = []
    for t in conn.execute("SELECT * FROM theme WHERE project_id=? ORDER BY name", (pid,)):
        rows = [dict(h) for h in store.theme_history(conn, t["id"])]
        if rows:
            out.append({**dict(t), "history": rows})
    return out


def _export_comments(conn, pid: str) -> list[dict]:
    """Every comment, with the thing it was about named and whether a rewrite has honoured it.

    A comment is an instruction for the next rewrite of one block. Printed as `theme t3f9…` it is
    unreadable a month later, and printed without its outcome it cannot be audited: the researcher
    needs to see which of their objections the analysis has actually answered.
    """
    names = _export_names(conn, pid)
    themes = {t["id"]: t["name"] for t in
              conn.execute("SELECT id, name FROM theme WHERE project_id=?", (pid,))}
    runs = {r["id"]: dict(r) for r in store.runs(conn, pid)}

    def about(f) -> str:
        kind, ref = f["target_kind"], f["target_id"]
        if kind in ("project_summary", "focus"):
            return "the project"
        if kind == "theme":
            return themes.get(ref, ref)
        if kind == "thread":
            mid, _, tid = ref.partition(":")
            return f'{names.get(mid, mid)}, under {themes.get(tid, tid)}'
        if kind == "moment":
            x = store.moment(conn, ref)
            return (f'a claim in {names.get(x["material_id"], "")} [{x["sid"]}]' if x
                    else "a claim")
        return names.get(ref, ref)      # material_summary, frame — both name a material

    out = []
    for f in store.project_feedback(conn, pid):
        d, r = dict(f), runs.get(f["consumed_by_run"])
        d["about"] = about(f)
        d["outcome"] = (f'honoured by a rewrite on {(r["finished"] or r["started"] or "")[:10]}'
                        if r else "open")
        out.append(d)
    return out
