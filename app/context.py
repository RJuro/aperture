"""One function per page. Each returns a plain dict; the template only renders it.

Two rules hold this file together.

**Nothing is copied field by field.** Rows go to the page as `dict(row)`, whole. Three times in
the old engine an explicit key list on the way to a template silently dropped a validated quote
and the suite stayed green, so there are no key lists here: if a column exists, the page has it.

**Our vocabulary stays in the code.** `_BANNED` is the design language — words that are genuinely
ours for a thing the page already names some other way, never a page's own ordinary English. It
is checked against `APP_AUTHORED` strings and against a rendered page's *visible text only* — an
attribute value, a URL or an element name is not a sentence a researcher reads, and forcing one of
those to dodge a banned word (a form's `action` once had to say `/compare` rather than
`/consolidate` for exactly this reason) fixed nothing a researcher could see. Variables, keys and
comments may say *moment*, *thread*, *frame*; the rendered page says *material*, *what this is*,
*what the reading found*, *Check this against the material*, *Reading record*.
"""
from __future__ import annotations

import json
import re

from markupsafe import Markup

from . import rerun, store, titles

APP_NAME = "Aperture"

# Words the app must never say in its own voice, in visible text. Narrowed from a longer list that
# reached into attribute values and element names, and that banned some perfectly ordinary English
# ("door", "frame", "gate", "slot", "weakest", "territory", "register lane", "exposure", "residue",
# "ledger", "roster", "steer", "delta", "friction", "panel", "consolidate") a page may legitimately
# need — while saying nothing at all about the confusing metaphors an actual review found ("carry",
# "fold", "hold", "open" for a theme's status). What is left is our own private word for something
# the page already names another way, so a researcher who reads it here would be reading jargon.
_BANNED = [
    "anchor", "standard coding", "absence check", "defensible account", "fact panel",
    "check-back", "checkback", "merge proposal", "moment", "thread",
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
            # The material's name, not only the passage id. A corpus summary cites across every
            # material at once, and "S155" alone says which passage but not which interview — a
            # researcher checking a claim was reading sid numbers for proximity to guess whether
            # two citations came from the same transcript. The name it already links to is the
            # answer, and the index has been carrying it all along.
            out.append(f'<a class="claim cite" href="/p/{pid}/m/{t["material_id"]}'
                       f'?theme={t["theme_id"]}#{t["sid"]}" title="{_esc(t["material_title"])}">'
                       f'{t["sid"]}<span class="cite-who">{_esc(t["material_short"])}</span></a>')
            at = m.end()
        out.append(f'<span class="summary">{_emph(_esc(part[at:]))}</span>')
        return "".join(out)

    # The summary is three hundred words of argument, and the model breaks it into paragraphs
    # where the argument turns. Rendering it as one block throws that structure away and gives the
    # researcher a wall to read; a blank line in, a paragraph out.
    paras = [p.strip() for p in re.split(r"\n\s*\n", _live_cites(text, index)) if p.strip()]
    return Markup("".join(f"<p>{one(p)}</p>" for p in paras) or "")


def _cite_label(t: dict) -> str:
    """A citation as a reader meets it in the record: which material, then which passage.

    The corpus summary cites across every material at once, so a bare `[S041]` names a passage in
    a document the reader must then work out. Two citations one line apart may be the same
    transcript or two, and the record gave no way to tell — the same gap the page had, in the
    document a blind judge reads. Separated by `;` where several are grouped, since a name and a
    passage id already sit either side of a space.
    """
    who = str(t.get("material_short") or "").strip()
    return f'{who} {t["sid"]}' if who else str(t["sid"])


def _short_title(row) -> str:
    """The material as a citation names it: whoever it is of, without the kind and the year.

    `titles.compose` writes "Mary Grande — interview, 1989"; inline in a three-hundred-word
    summary the tail is noise repeated at every citation, and the head is the whole question a
    reader is asking. The full title rides along as the link's tooltip.
    """
    return _material_title(row).split(" — ")[0].strip() or _material_title(row)


def _cite_index(conn, pid: str) -> dict:
    out = {}
    for mat in store.materials(conn, pid):
        short, full = _short_title(mat), _material_title(mat)
        for m in store.moments(conn, mat["id"]):
            out[m["id"]] = {**dict(m), "material_short": short, "material_title": full}
    return out


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
    said = (f"Claims cite {len(store.cited_sids(conn, mid))} "
            f"of {len(store.sentences(conn, mid))} passages")
    aside = store.set_aside_by_check(conn, mid)
    if not aside:
        return said
    one = aside == 1
    return (said + f", {_n(aside, 'claim')} excluded because "
            f"{'its' if one else 'their'} cited {'passage' if one else 'passages'} "
            f"did not support {'it' if one else 'them'}")


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


def _cases(conn, pid: str) -> dict[str, str] | None:
    """Material id → the case it counts under, or None where the researcher has grouped nothing.

    A file is not a case. Two files from one participant are two materials, a spreadsheet of
    forty respondents is one, and neither count can ground a statement about recurrence across
    independent cases — which is what "in 3 of 4 materials" was being read as. So where a
    researcher has said which materials are one case, every reach on every page counts cases;
    where they have not, None says so and nothing changes.
    """
    of = store.case_of(conn, pid)
    return of if any(cid != mid for mid, cid in of.items()) else None


def _reach(carrying: list[str], mids: list[str], of: dict | None,
           claims: dict[str, int] | None = None) -> tuple[int, int, str]:
    """How far a theme reaches, as the count it groups by, the whole it is out of, and the words.

    The material count stays beside the case count because the columns beside it are materials:
    law 4 wants the number derivable from the rows the page links to, and "2 of 3 cases" alone
    cannot be checked against four filled cells.

    `claims` is how many claims the theme holds in each material, and where a carrying line is
    shorter than a full one the reach says how many are: a line of one claim counts towards "7 of
    8 materials" exactly as a line of twelve does, and a reader weighing that number cannot see
    the difference. The count of carrying materials is untouched — it still matches the filled
    cells beside it — and the qualification follows it in a parenthesis.
    """
    from .engine import synth

    thin = sum(1 for m in carrying if (claims or {}).get(m, synth.MIN_MOMENTS) < synth.MIN_MOMENTS)
    # "Sparse" named the count without saying against what; a reader had no way to tell four claims
    # short of a floor they had never been told either. The floor itself says it.
    note = f"{thin} with fewer than {synth.MIN_MOMENTS} claims"
    if of is None:
        said = f"{len(carrying)} of {len(mids)} materials"
        return len(carrying), len(mids), f"{said} ({note})" if thin else said
    n, total = len({of[m] for m in carrying}), len({of[m] for m in mids})
    inside = _n(len(carrying), "material") + (f", {note}" if thin else "")
    return n, total, f"{n} of {total} cases ({inside})"


def _single_group() -> str:
    """The heading over the themes not yet a project theme. "In one material so far" and "in one
    case so far" were both false about some of the rows under them — a candidate can hold claims
    in several materials, or several cases, while it is still awaiting promotion — so the heading
    says what candidate status actually is and each row's own derivation line says how far it
    reaches (F4, `_reach`)."""
    return "Candidate themes"


def _proposal(t: dict, carried: int, of: dict | None) -> str:
    """What the page asks the researcher about a candidate the corpus has now said twice.

    A question, not a receipt: promotion is theirs (`/promote`), and the count is printed so
    they can see what it was counted over.
    """
    if t["hold"] != "candidate" or not t["proposed_at"]:
        return ""
    return (f'Found in {_n(carried, "case" if of else "material")} — '
            f'add it to the project themes?')


def _row(r) -> dict | None:
    return dict(r) if r is not None else None


def _material_title(row) -> str:
    return titles.standardize(row["title"] or row["name"])


def _source_name(row, display_title: str) -> str:
    """The file this material arrived as, where the composed title is not already it.

    A researcher who uploaded `NYC-OH-0412 transcript.docx` has no way back to the file on their
    own disk once FRAME has titled it "Mary Grande — interview, 1974", and the two names have to
    be matched up by hand to check a quote against the source. The filename was in the row the
    whole time (`material.name`); it was simply never shown once a title existed.
    """
    return "" if row["name"] == display_title else row["name"]


def _notes(conn, tid: str) -> list[dict]:
    """What the readings wrote beside a theme's definition, each with the material it came from
    and the `kind` that says which way the reading was going.

    A `tension` is what one material pulled against a FROZEN definition, and the tensions are the
    whole case for unfreezing it. A `fit` is where a material carries an OPEN theme in a way the
    definition did not foresee — a different kind of case, actor, setting or time. The page shows
    both, under separate headings: they are read for opposite reasons, and the pages gated the
    whole section on `hold == 'frozen'`, so the only note written about a definition that can
    still change was never printed anywhere at all.

    A note reads as an objection to the theme, so the material it was raised in is half of it: at
    twenty materials a note nobody can trace back to a reading cannot be followed up.
    """
    out = []
    for n in store.theme_notes(conn, tid):
        m = store.material(conn, n["material_id"])
        out.append({**dict(n), "display_title": _material_title(m) if m else ""})
    return out


def _nearest(conn, t) -> dict | None:
    """The live theme this one is most easily confused with, and what sorts a passage into this
    one rather than that (`store.set_nearest`).

    None where THEMES has not said — which is every theme named before the field existed, and
    every theme nothing is close to. A label with nothing after it tells a reader less than no
    label, so nothing is rendered there.
    """
    if not t["nearest_id"]:
        return None
    near = conn.execute("SELECT id, name FROM theme WHERE id=? AND status='live'",
                        (t["nearest_id"],)).fetchone()
    return {**dict(near), "note": t["nearest_note"] or ""} if near else None


def _overarching(conn, pid: str) -> dict:
    """The tier PROJECT wrote over the theme set: higher-order themes, each naming what it
    gathers and why, and every live theme the summary did not place.

    Three states are ordinary and none of them is an error. A project written before the tier
    existed has no row; a project whose themes would not group holds an empty list; and the row
    is the model's own JSON, which has failed to parse before now. A page that raised on any of
    them would take the whole project down for the sake of one section under the summary, so each
    is nothing rendered.

    `ungathered` is printed rather than hidden, for the reason the empty matrix cells are: a
    theme the summary could not place is a fact about the summary, and a researcher who cannot
    see it cannot ask why.
    """
    row = store.get_summary(conn, "project", pid, "overarching")
    try:
        got = json.loads(row["text"]) if row else {}
    except ValueError:
        got = {}
    if not isinstance(got, dict):
        got = {}
    names = {t["id"]: t["name"] for t in
             list(store.live_themes(conn, pid)) + list(store.candidates(conn, pid))}

    def entries(key) -> list[dict]:
        got_list = got.get(key)
        return [e for e in got_list if isinstance(e, dict)] if isinstance(got_list, list) else []

    def gathered(ids) -> list[dict]:
        # An id no live theme answers to is dropped rather than printed. The writer validates
        # these first; this is the second line, for a row whose themes have since been merged
        # away — and a link to a theme that is not there is worse than a shorter list.
        ids = ids if isinstance(ids, list) else []
        return [{"id": i, "name": names[i]} for i in ids if isinstance(i, str) and i in names]

    return {"overarching": [{**e, "gathers": gathered(e.get("gathers"))}
                            for e in entries("overarching")],
            "ungathered": [{**e, "name": names[e["id"]]} for e in entries("ungathered")
                           if isinstance(e.get("id"), str) and e["id"] in names]}


def _duplicates(conn, pid: str) -> list[dict]:
    """Pairs of project themes that may be one theme, worked out from the columns at no cost.

    Two ways a pair gets here. Each theme names the other as the one it is most easily confused
    with — the reading said twice that it could only just tell them apart. Or half or more of the
    codes the two gather are the same codes, which is the shape a split theme has: one pattern
    read under two names.

    This proposes and nothing else: no theme is merged here, and the page says which control
    does merge, because a list of pairs printed beside a button that merges reads as a queue.

    ponytail: every pair of live themes, which is a few dozen comparisons at a dozen themes. If a
    project ever holds hundreds, index the pairs by shared code instead.
    """
    themes = [dict(t) for t in store.live_themes(conn, pid)]
    codes: dict[str, set[str]] = {t["id"]: set() for t in themes}
    for r in conn.execute("SELECT theme_id, code_id FROM theme_code"):
        if r["theme_id"] in codes:
            codes[r["theme_id"]].add(r["code_id"])
    out = []
    for i, a in enumerate(themes):
        for b in themes[i + 1:]:
            why = []
            if a["nearest_id"] == b["id"] and b["nearest_id"] == a["id"]:
                why.append("each names the other as the theme it is most easily confused with")
            both, either = codes[a["id"]] & codes[b["id"]], codes[a["id"]] | codes[b["id"]]
            if either and len(both) / len(either) >= 0.5:
                # Law 4: the number is printed as what it was counted over, so a researcher can
                # see that a pair of one-code themes sharing that code is what fired the rule.
                why.append(f'{len(both)} of the {len(either)} codes the two gather are the same')
            if why:
                out.append({"a": a, "b": b, "why": " · ".join(why)})
    return out

def _recording(row) -> dict:
    """What the pages need to know about a material that arrived as a recording.

    The columns live on the material row and are read defensively: a database written before
    recordings existed has none of them, and a page that asked for one directly would break on
    every material added before the upgrade.
    """
    d = dict(row)
    seconds = d.get("audio_seconds") or 0
    return {"from_recording": bool(d.get("audio_file") or seconds),
            # The recording is kept after it has been transcribed — "run again from the
            # recording" is at the head of the chain and would fail on every recorded material
            # without it — so the file's presence cannot be what says the transcript is missing.
            # Its length is: `audio_seconds` is written only when a transcription has succeeded.
            "waiting": bool(d.get("audio_file")) and not seconds,
            "note": d.get("audio_note") or "",
            "cleaned": bool(d.get("audio_clean")),
            "length": _length(seconds)}


def _length(seconds: int) -> str:
    """A recording's length in the unit a researcher thinks in. Seconds are the file's business."""
    if not seconds:
        return ""
    minutes = round(seconds / 60)
    return f"{minutes} {'minute' if minutes == 1 else 'minutes'}" if minutes else "under a minute"


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
    # A recording is transcribed before there is anything to read in it, and that wait is minutes
    # long. Without a step of its own the receipt showed four waiting steps and no reason for it,
    # so the researcher could not tell a transcription running from an analysis that never began.
    rec = _recording(row)
    if rec["from_recording"]:
        labels = (("transcribe", "Transcription"),) + labels
        inferred["transcribe"] = not rec["waiting"] and bool((dict(row).get("text") or "").strip())
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


def _check_said(c: dict) -> str:
    """What one check found, and over which passages — one sentence, four surfaces.

    Never "the material contains none of it": an empty result is a statement about the passages
    that were read, and until the search could be asked to read all of them it was routinely a
    statement about the remainder, where the answer had already been claimed.
    """
    n = c.get("searched_n") or 0
    passages = "passage" if n == 1 else "passages"
    where = (f"searched {n} of {n} {passages}" if (c.get("searched_scope") or "unused") == "all"
             else f"searched {n} {passages} not yet cited")
    return f"found — {where}" if c.get("verdict") == "found" else f"nothing found — {where}"


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
        d["said"] = _check_said(d)
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
    # Where each material stands, for the rail's mark. A researcher with several materials could
    # otherwise only tell which one is read by opening it.
    # ponytail: four indexed queries per material, fine to about fifty; one grouped query over
    # `run` if a corpus ever makes the rail slow.
    nav_materials = []
    for m in store.materials(conn, pid):
        steps = _analysis_steps(conn, m)
        states = {s["state"] for s in steps}
        state = ("active" if "active" in states else "failed" if "failed" in states
                 else "done" if states == {"done"} else "waiting")
        said = {"active": "Being read", "done": "Read", "waiting": "Not read yet"}.get(state, "")
        # Nothing is being read in a recording whose transcript does not exist yet.
        if state == "active" and _recording(m)["waiting"]:
            said = "Being transcribed"
        if state == "failed":
            said = "Stopped: " + next(s["error"] for s in steps if s["state"] == "failed")
        nav_materials.append({**dict(m), "display_title": _material_title(m),
                              "reading_state": state, "reading_said": said})
    runs = [dict(r) for r in store.active_runs(conn, pid)]
    # The banner used to read run rows alone, and a job that is queued has none yet — so a page
    # whose work was waiting on another project's chain said nothing, offered no Stop and did not
    # poll. The committed job row is what exists first; the run line is only the wording.
    return {"app_name": APP_NAME, "css_v": _css_version(), "data_persistent": data_persistent(),
            "runs": runs,
            "working": bool(runs) or store.summary_state(conn, pid)["working"],
            "nav_materials": nav_materials,
            "nav_theme_count": len(store.live_themes(conn, pid))}


# What an empty cell means, in the five states `_assessed` tells apart. A hover title on a
# non-interactive span answers nobody using a keyboard or a touch screen, so the matrix instead
# prints `abbr` in the cell itself — plain visible text, needing no interaction to be read — and
# the page's legend spells out `label`/`explain` for whichever of these actually occur in it. The
# record and the theme page name these states in their own headings and keep their own words.
ASSESSED_SAID = {
    "thin": {"abbr": "thin", "label": "No retained claims",
             "explain": "The theme was assessed, but no claims were retained; review exclusions "
                        "before reading this as absence."},
    "screened": {"abbr": "screened", "label": "Source check skipped",
                 "explain": "A preliminary review of the summary and codes did not select this "
                            "theme for a source check."},
    "skipped": {"abbr": "skipped", "label": "No matching codes",
                "explain": "The initial coding did not trigger an assessment for this theme."},
    "residual": {"abbr": "residual", "label": "No match in uncoded passages",
                 "explain": "A search of passages without codes found nothing to add; this was "
                            "a limited search."},
    None: {"abbr": "not assessed", "label": "Not assessed",
           "explain": "This material has not been assessed for this theme."},
}

# The fixed order the review's own table uses, so the legend under the matrix reads as one list
# rather than in whatever order a dict happened to see the outcomes first.
_STATUS_ORDER = ("thin", "screened", "skipped", "residual", None)


def _assessed(outcomes: dict, tid: str, mid: str) -> str | None:
    """Which kind of nothing this material is for this theme: 'thin' where a reading under it was
    made and set aside, 'screened' where one call read this material's own account and its coding
    and did not send a reader to the material, 'skipped' where none of the theme's codes marked
    the material and it was never looked for, 'residual' where the skip was then searched in the
    passages no code marked and nothing was found, and None where the pair was never assessed at
    all.

    A missing row is the last state and not the first. A material uploaded and not yet read, and
    an older material never revisited for a theme developed since, both have no row — and both
    were shown as "looked for and found too thin", which asserts an absence over a reading that
    never happened. 'line' with no live claims left reads as thin: it was looked for, and what it
    found is no longer there.

    'screened' sits between 'thin' and 'skipped' and is neither of them. Something did look, so it
    is not a blank where nothing ever went; what it looked at was the account and the coding
    rather than the material, so it is not an absence in the material either.
    """
    outcome = outcomes.get((tid, mid))
    if outcome in (None, "skipped", "residual", "screened"):
        return outcome
    return "thin"


def _threads(conn, mid: str, themes: dict) -> list[dict]:
    """Every live moment on this material, grouped by its theme — built from the rows, so a theme
    that was merged away still carries its moments into the record."""
    from .engine import synth

    by: dict[str, list[dict]] = {}
    for m in store.moments(conn, mid):
        by.setdefault(m["theme_id"], []).append(dict(m))
    return [{"theme": themes.get(t, {"id": t, "name": t, "gist": ""}), "moments": ms,
             # A line of one to three claims is kept now rather than dropped whole, so the record
             # has to say it is one: three observations and thirty read the same on a page.
             "sparse": len(ms) < synth.MIN_MOMENTS,
             "summary": _row(store.get_summary(conn, "thread", f"{mid}:{t}", "reading"))}
            for t, ms in by.items()]


# ---- the comparison control (F1, F5) -------------------------------------------------------------

def _consolidate_estimate(conn, pid: str, cells: list[tuple[str, str]]) -> tuple[int, int]:
    """Every model call the whole planned operation makes (F5), not only the reading of the cells
    themselves. Certain: the comparison, one preliminary review and one verification per material
    with cells, and the project summary written last. Uncertain, because it depends on what the
    preliminary review sends a reader to: the cells themselves, one summary per touched material
    in an iterative project (an exploratory project's memo is written over passages and is not
    rewritten by this, PLAN.md §14), and every live theme's account — a consolidation ends by
    writing the theme set up as it now stands, whether or not a given theme's own cells changed.
    """
    mats = len({mid for _, mid in cells})
    proj = store.project(conn, pid)
    iterative = proj is not None and proj["method"] != "explore"
    extra = len(store.live_themes(conn, pid)) + (mats if iterative else 0)
    if rerun.screen_planned():
        floor = 2 + 2 * mats                     # comparison + a look and a verify per material + the project summary
        ceiling = floor + len(cells) + extra
    else:
        # Every planned cell is read for certain with the look off, so nothing here is uncertain.
        floor = ceiling = 2 + mats + len(cells) + extra
    return floor, ceiling


def _consolidate_control(conn, pid: str, n_themes: int, opening: list[tuple[str, str]],
                         every: list[tuple[str, str]]) -> dict:
    """Everything the comparison control prints, generated from current state (F1).

    `opening`'s threshold is never below two, and a theme no case carries at all is read for under
    both — so its pairs are always a subset of `every`'s, and equal counts mean equal sets. A
    researcher who switches to the wider scope is told its own threshold in the radio's own words,
    and the page shows each scope's numbers beside the choice that produces them rather than a
    count that would have to update itself without a script. Where the two coincide there is no
    choice to offer and the page says so in a sentence instead — `same`.
    """
    need = store.opening_need(conn, pid)
    total = len(set(store.case_of(conn, pid).values()))
    unit = "cases" if store.cases(conn, pid) else "materials"
    # A theme no case carries is read for under either threshold — it is the one theme that has to
    # be, because nothing has ever been read for it anywhere. Counted separately because the radio
    # labels describe thresholds in claims, and a theme with claims in nothing is described by
    # neither of them: on an eight-material corpus every remaining pair was one of these, so the
    # page offered a single radio saying "at least 4 of 8" over pairs that were nothing of the kind.
    held = store.carried_cases(conn, pid)
    never = len({tid for tid, _ in every if not held.get(tid)})

    def said(cells: list[tuple[str, str]]) -> str:
        """One scope's own price, printed in its own radio. Without a script the page cannot
        recompute when the choice changes, and a number beside the option that does not produce
        it is exactly the misdirection this control was rewritten to remove."""
        floor, ceiling = _consolidate_estimate(conn, pid, cells)
        calls = f"{floor}" if floor == ceiling else f"{floor}–{ceiling}"
        return f'{_n(len(cells), "theme/material pair")} to check · about {calls} model calls'

    return {"themes": n_themes, "unit": unit, "need": need, "total": total,
            "opening_n": len(opening), "all_n": len(every), "never": never,
            "opening_said": said(opening), "all_said": said(every),
            "same": len(opening) == len(every)}


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
        m["source_name"] = _source_name(m, m["display_title"])
        m["derivation"] = derivation(conn, m["id"])
        m["out_of_date"] = m["id"] in stale
        m["analysis"] = _analysis_steps(conn, m)
        m["analysis_done"] = sum(s["state"] == "done" for s in m["analysis"])
        # One word for where this material has got to, so the head can say how far the reading
        # has come without the reader counting four receipts across four rows.
        states = {s["state"] for s in m["analysis"]}
        m["reading"] = ("failed" if "failed" in states else "active" if "active" in states
                        else "done" if m["analysis_done"] == len(m["analysis"]) else "waiting")
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
    outcomes = store.followed(conn, pid)
    of = _cases(conn, pid)
    themes = []
    # Candidates are project themes' juniors, not a separate page: they belong under the same
    # headings, at the bottom, with the control that makes one a theme.
    for t in list(store.live_themes(conn, pid)) + list(store.candidates(conn, pid)):
        row = dict(t)
        # An empty cell has no room for a sentence, so it carries a short word instead — the five
        # reasons a cell is empty are not the same finding, and the legend under the table spells
        # out whichever of them this project actually has (F3).
        row["columns"] = [{"material_id": m["id"], "material": m,
                           "moments": [None] * counts.get((t["id"], m["id"]), 0),
                           "status": _assessed(outcomes, t["id"], m["id"]),
                           "abbr": ASSESSED_SAID[_assessed(outcomes, t["id"], m["id"])]["abbr"]}
                          for m in mats]
        carried, whole, said = _reach([c["material_id"] for c in row["columns"] if c["moments"]],
                                      [m["id"] for m in mats], of,
                                      {c["material_id"]: len(c["moments"]) for c in row["columns"]})
        # A theme resting on one case is a motif in that case, not a corpus theme, and listed
        # beside the others it reads as if it had the same reach. `single` is what the page
        # groups by, and it is the same threshold the proposal uses.
        row["single"] = carried < 2
        row["reach"], row["claims"] = carried, sum(len(c["moments"]) for c in row["columns"])
        # Three steps, so the table can set the strongest themes larger: carried by every
        # case, by several, or by one.
        row["tier"] = 3 if row["single"] else 1 if carried == whole else 2
        row["derivation"] = f'{said} · {_evidence(evidence.get(t["id"]))}'
        row["proposal"] = _proposal(row, carried, of)
        themes.append(row)
    # `live_themes` orders by name, which other pages depend on. Alphabetical here made a theme
    # every material carries with twenty claims look like one a single reading mentioned twice.
    # Frozen first: a theme the researcher has declared final is what the rest is now read
    # against, whatever its reach, and candidates come last because they are not yet themes.
    themes.sort(key=lambda r: (r["hold"] == "candidate", r["hold"] != "frozen",
                               -r["reach"], -r["claims"], r["name"]))
    # The legend under the matrix names only the statuses this project actually has — a project
    # with no screened cell need not explain what "screened" would have meant.
    present = {c["status"] for row in themes for c in row["columns"] if not c["moments"]}
    assessed_legend = [ASSESSED_SAID[k] for k in _STATUS_ORDER if k in present]
    opening, every = store.backfill_cells(conn, pid, "opening"), store.backfill_cells(conn, pid, "all")
    consolidate = (_consolidate_control(conn, pid, len(themes), opening, every)
                   if every or sum(t["hold"] == "candidate" for t in themes) > 1 else None)
    fb = [dict(f) for f in store.project_feedback(conn, pid)]
    index = _cite_index(conn, pid)
    summary = _row(store.get_summary(conn, "project", pid))
    # What it may mean, kept apart from what it shows: one is cited, the other argued with.
    reading_of = _row(store.get_summary(conn, "project", pid, "interpretation"))
    by_case: dict[str, list] = {}
    for m in mats:
        if m["case_id"]:
            by_case.setdefault(m["case_id"], []).append(m)
    return {**_shell(conn, pid), "project": dict(p), "materials": mats, "themes": themes,
            "cases": [{**dict(c), "materials": by_case.get(c["id"], [])}
                      for c in store.cases(conn, pid)],
            "single_group": _single_group(), "consolidate": consolidate,
            "assessed_legend": assessed_legend,
            "duplicates": _duplicates(conn, pid),
            **_overarching(conn, pid),
            "page_section": "overview", "reading": reading,
            "summary": summary,
            # The tier's own prose cites claims as the summary does, and the page turns each into
            # a link the same way — so the index travels whole rather than as one more `_html`.
            "cites": index,
            "summary_html": cite(summary["text"], index, pid) if summary else "",
            "interpretation": reading_of,
            "interpretation_html": cite(reading_of["text"], index, pid) if reading_of else "",
            "summary_state": store.summary_state(conn, pid),
            "focus_history": [f for f in fb if f["target_kind"] == "focus"],
            "questions": store.open_questions(conn, pid),
            "checks": _checks(conn, pid)}


def material_page(conn, pid: str, mid: str, theme_id: str | None = None) -> dict:
    from .engine import synth

    p, m = store.project(conn, pid), store.material(conn, mid)
    if p is None or m is None or m["project_id"] != pid:
        return {}
    mat = dict(m)
    mat["display_title"] = _material_title(m)
    mat["source_name"] = _source_name(m, mat["display_title"])
    mat["analysis"] = _analysis_steps(conn, m)
    # A material still waiting for its transcript has a placeholder for text and no claims, and
    # the page has to say that rather than print an empty reading. A transcription that stopped
    # is the same absence for a different reason, and the page must not offer either as reading.
    rec = _recording(m)
    failed = next((s for s in mat["analysis"]
                   if s["kind"] == "transcribe" and s["state"] == "failed"), None)
    mat["recording"] = {**rec,
                        # Transcribed is the transcript existing, not the wait being over: a
                        # transcription that stopped is also no longer waiting, and the head
                        # would have said the material was transcribed from a recording that
                        # was never transcribed at all.
                        "transcribed": rec["from_recording"] and not rec["waiting"],
                        "waiting": rec["waiting"] and not failed,
                        "error": failed["error"] if failed else ""}
    cards = []
    live = [dict(t) for t in store.themes_for_material(conn, pid, mid)]
    for t in live:
        ms = [dict(x) for x in store.thread(conn, mid, t["id"])]
        if not ms:
            continue
        for x in ms:
            x["reactions"] = [dict(f) for f in store.feedback_for(conn, "moment", x["id"])]
        cards.append({**dict(t), "moments": ms,
                      # A line kept below the floor is still a line; the page says which, so a
                      # reader does not weigh three claims as they would weigh thirty.
                      "sparse": len(ms) < synth.MIN_MOMENTS,
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
    outcomes, whys = store.followed(conn, pid), store.follow_notes(conn, pid)
    carrying, absent = [], []
    for m in cover["per_material"]:
        row = dict(m)
        row["display_title"] = _material_title(m)
        if m["claims"]:
            row["moments"] = [dict(x) for x in store.thread(conn, m["material_id"], tid)]
            carrying.append(row)
        else:
            # Which kind of nothing this is — set aside, passed over by the look, never looked
            # for, or never assessed — and, where the look said why, its words.
            row["assessed"] = _assessed(outcomes, tid, m["material_id"])
            row["screened_why"] = whys.get((tid, m["material_id"]), "")
            absent.append(row)
    summary = _row(store.get_summary(conn, "theme", tid))
    of = _cases(conn, pid)
    carried, _, said = _reach([m["material_id"] for m in cover["per_material"] if m["claims"]],
                              [m["material_id"] for m in cover["per_material"]], of,
                              {m["material_id"]: m["claims"] for m in cover["per_material"]})
    return {**_shell(conn, pid), "project": dict(p), "theme": dict(t),
            "page_section": "themes",
            "coverage": cover, "carrying": carrying, "absent": absent, "summary": summary,
            "summary_html": cite(summary["text"], _cite_index(conn, pid), pid) if summary else "",
            "derivation": f'{said} · {_evidence(store.theme_evidence(conn, pid).get(tid))}',
            "proposal": _proposal(dict(t), carried, of),
            "codes": [dict(c) for c in store.theme_codes(conn, tid)],
            "notes": _notes(conn, tid),
            "nearest": _nearest(conn, t),
            # Which overarching themes gather this one. A theme reads differently under an
            # argument that uses it, and the tier is otherwise only visible from the project page.
            "gathered_under": [o.get("name", "") for o in _overarching(conn, pid)["overarching"]
                               if any(g["id"] == tid for g in o["gathers"])],
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
        lambda m: "[" + "; ".join(_cite_label(index[i]) for i in _CITE.findall(m.group(1))) + "]",
        text)
    return _CITE.sub(lambda m: f"[{_cite_label(index[m.group(0)])}]", text)


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
    themes = {t["id"]: dict(t) for t in
              list(store.live_themes(conn, pid)) + list(store.candidates(conn, pid))}
    mats = []
    for m in store.materials(conn, pid):
        d = dict(m)
        d["display_title"] = _material_title(m)
        d["source_name"] = _source_name(m, d["display_title"])
        for stage in ("orientation", "reading", "angles", "memo", "residual"):
            d[stage] = _row(store.get_summary(conn, "material", m["id"], stage))
        # Where the project explores, the memo IS what the reading found and DOC wrote no summary
        # beside it, so it stands in the same place in the record (PLAN.md §13).
        d["reading"] = d["memo"] or d["reading"]
        d["people"] = [dict(x) for x in store.people(conn, m["id"])]
        d["speakers"] = [dict(x) for x in store.speakers(conn, m["id"])]
        d["threads"] = _threads(conn, m["id"], themes)
        d["derivation"] = derivation(conn, m["id"])
        mats.append(d)
    said = _export_comments(conn, pid)
    ctx = {"app_name": APP_NAME, "project": dict(p), "materials": mats,
            "questions": store.open_questions(conn, pid),
            "summary": _row(store.get_summary(conn, "project", pid)),
            **_overarching(conn, pid),
            "interpretation": _row(store.get_summary(conn, "project", pid, "interpretation")),
            "themes": _export_themes(conn, pid, aside),
            "single_group": _single_group(),
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

    The preposition and the possessive that hold the name go with it, or the line is left
    ungrammatical: "Writing the summary of again", "Comparing's codes with the project's".
    """
    from . import jobs
    return re.sub(r"\s*(in |of )?\{name\}('s)?", "", jobs.STEPS.get(kind, (kind,))[0])


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
    that was found and dropped.

    A carrying material arrives as its one-line summary for this theme, not as its claims. The
    claims are printed under the material they were read in, because that is the order the
    analysis was made in; here the theme is the cross-cut, short enough to read as an account.
    """
    from .engine import account

    out = []
    evidence = store.theme_evidence(conn, pid)
    outcomes, whys = store.followed(conn, pid), store.follow_notes(conn, pid)
    of = _cases(conn, pid)
    for t in list(store.live_themes(conn, pid)) + list(store.candidates(conn, pid)):
        cover = account.coverage(conn, pid, t["id"])
        carrying, absent = [], []
        for m in cover["per_material"]:
            row = dict(m)
            row["display_title"] = _material_title(m)
            if m["claims"]:
                row["summary"] = _row(store.get_summary(
                    conn, "thread", f'{m["material_id"]}:{t["id"]}', "reading"))
                carrying.append(row)
            else:
                # As on the theme page: 'thin', 'screened', 'skipped', 'residual', or None where
                # the theme and this material were never assessed against each other at all.
                row["assessed"] = _assessed(outcomes, t["id"], m["material_id"])
                row["screened_why"] = whys.get((t["id"], m["material_id"]), "")
                absent.append(row)
        carried, _, said = _reach([m["material_id"] for m in cover["per_material"] if m["claims"]],
                                  [m["material_id"] for m in cover["per_material"]], of,
                                  {m["material_id"]: m["claims"] for m in cover["per_material"]})
        out.append({**dict(t), "account": _row(store.get_summary(conn, "theme", t["id"])),
                    "carrying": carrying, "absent": absent,
                    "notes": _notes(conn, t["id"]), "nearest": _nearest(conn, t),
                    "single": carried < 2,
                    "derivation": f'in {said} · {_evidence(evidence.get(t["id"]))}',
                    "proposal": _proposal(dict(t), carried, of),
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
