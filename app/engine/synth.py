"""DOC and PROJECT — what the reading found in one material, and what it found across a project.

This is where the anchor law (PLAN.md §3.1) lives at runtime. Everything else here is bookkeeping
around three rules:

    the quote is authoritative, the citation is not   a real quote under a wrong sentence id is
                                                      REPAIRED, never dropped — D15, the defect
                                                      that taught two readers to distrust a system
                                                      that was right
    a quote that is nowhere is not a claim            the moment goes
    a thread of one moment is not a thread            it is dropped, and the drop is REPORTED,
                                                      because a silent drop is how a reading loses
                                                      material without anyone noticing

Passages are printed to the model under the numeric part of their sentence id (`S040` → `40`) and
a citation comes back as that number, mapped back here. Ids are the spine; the number is how the
material is laid out for a reader, on the page and in the prompt alike.

DOC also rewrites the brief. That is the one slot in this system where something a model wrote
enters another prompt — everything else the model writes is shown to a researcher and stops there.
"""
from __future__ import annotations

import re

from .. import anchor, llm, store

MIN_MOMENTS, MAX_MOMENTS = 4, 14
SUMMARY_WORDS, PROJECT_WORDS, BRIEF_WORDS, CLAIM_WORDS, GIST_WORDS = 320, 300, 120, 30, 40
# What the corpus may mean, as against what it shows: shorter, because it is the movement a
# researcher argues with rather than the one they cite.
INTERPRETATION_WORDS = 150
# What one theme amounts to in one material. Short, because the claims below it are the finding
# and this only says how they hang together.
THREAD_WORDS = 90

_CITE = re.compile(r"\s*\[([^\[\]]+)\]")


# ---- text ---------------------------------------------------------------------------------

def words(text, cap: int) -> str:
    """A cap the prompt also states as a number. Both, always: a cap only in the prompt is a
    request, and a cap only in Python is a surprise.

    Over-long text is cut back to the last sentence that fits, not to the last word. Cutting mid
    sentence produced summaries ending "What is thin: ... What …" — a paragraph the researcher
    reads first, ending in the middle of the clause that was about to say what was missing.
    """
    t = str(text or "").strip()
    if len(t.split()) <= cap:
        return t
    kept = " ".join(t.split()[:cap])
    end = max(kept.rfind(". "), kept.rfind("! "), kept.rfind("? "))
    # Only fall back to a hard cut if trimming to a sentence would throw away most of the text.
    return kept[:end + 1] if end > len(kept) * 0.6 else kept + " …"


def sid_num(sid) -> str:
    """The digits of a sentence id: `S040` → `40`. Only for reading a loose citation back."""
    return re.sub(r"\D", "", str(sid or "")).lstrip("0") or "0"


def numbers(sentences: list[tuple[str, str]]) -> dict[str, str]:
    """Both forms a model might cite → the real sentence id. Passages are printed under their
    real ids, so `S040` is the expected citation; a model that answers `40` or `40.` is still
    understood rather than punished for it."""
    out: dict[str, str] = {}
    for sid, _ in sentences:
        out[sid] = sid
        out[sid_num(sid)] = sid
    return out


def cited(token, nums: dict[str, str]) -> str:
    """One citation → a sentence id. An unreadable citation is passed through unchanged: it is
    the anchor, not this, that decides whether the claim survives."""
    raw = str(token or "").strip()
    return nums.get(raw) or nums.get(sid_num(raw)) or raw


# ---- what the model is shown --------------------------------------------------------------

def layout(conn, mid: str) -> str:
    """The material, laid out per its `display`, every line under its number.

    `turns` breaks at each turn (the speaker cue is in the text itself, so it is not repeated),
    `segments` prints each section's label where it starts, `plain` runs straight through.
    """
    row = store.material(conn, mid)
    display = (row["display"] if row else "") or "plain"
    labels = {s["sid"]: s["label"] for s in store.segments(conn, mid)}
    out: list[str] = []
    turn = object()
    for r in store.sentence_rows(conn, mid):
        if display == "segments" and r["sid"] in labels:
            out.append(f"\n[{labels[r['sid']]}]")
        if display == "turns" and r["turn_idx"] != turn:
            out.append("")
        turn = r["turn_idx"]
        out.append(f"{r['sid']}  {r['text']}")
    return "\n".join(out).strip() or "(this material has no text)"


def frame_block(conn, mid: str) -> str:
    row = store.material(conn, mid)
    lines = [f"kind: {row['kind'] or 'not yet worked out'}",
             f"laid out as: {row['display'] or 'plain'}",
             f"called: {row['title'] or row['name']}"]
    speakers = store.speakers(conn, mid)
    if speakers:
        lines.append("people who speak in it: " + "; ".join(
            f"{s['label']} = {s['name'] or s['label']} ({s['role'] or 'other'})"
            for s in speakers))
    else:
        lines.append("people who speak in it: none found — do not assume a speaker")
    segs = store.segments(conn, mid)
    if segs:
        lines.append("sections: " + "; ".join(f"{s['label']} (from {s['sid']})"
                                              for s in segs))
    return "\n".join(lines)


def codes_block(conn, mid: str) -> str:
    by_code: dict[tuple[str, str], list[str]] = {}
    for h in store.hits(conn, mid):
        by_code.setdefault((h["name"], h["definition"] or ""), []).append(h["sid"])
    if not by_code:
        return "Nothing has been marked in this material yet."
    out = []
    for (name, definition), nums in sorted(by_code.items()):
        shown = ", ".join(nums[:40]) + (" …" if len(nums) > 40 else "")
        out.append(f"{name} — {definition or 'no definition'} — {len(nums)} passages: {shown}")
    return "\n".join(out)


def themes_block(themes) -> str:
    if not themes:
        return "No themes yet. Return an empty list of threads."
    return "\n".join(f"{t['id']}  {t['name']} — {t['gist'] or 'no gist yet'}" for t in themes)


def feedback_block(conn, pid: str, mid: str, only_theme: str | None = None) -> str:
    """Every reaction that lands on this material, quoted verbatim with its date and what it is
    about. Python assembles it; no model ever paraphrases a researcher (PLAN.md §2)."""
    out = []
    for f in store.project_feedback(conn, pid):
        if f["consumed_by_run"]:
            continue                    # honoured by an earlier rewrite; history, not an order
        about = _about(conn, f, mid, only_theme)
        if about is None:
            continue
        said = f'"{f["text"]}"' if (f["text"] or "").strip() else "(no words, just the reaction)"
        out.append(f'{(f["created_at"] or "")[:10]} — on {about} — {f["kind"]}\n{said}')
    return "\n\n".join(out) or "The researcher has not said anything about this material yet."


def _about(conn, f, mid: str, only_theme: str | None) -> str | None:
    kind, target = f["target_kind"], str(f["target_id"] or "")
    if kind == "material_summary" and target == mid:
        return "what the reading found in this material"
    if kind == "thread" and target.startswith(f"{mid}:"):
        tid = target.split(":", 1)[1]
        return None if only_theme and tid != only_theme else f"the thread for theme {tid}"
    if kind == "moment":
        mo = store.moment(conn, target)
        if not mo or mo["material_id"] != mid:
            return None
        if only_theme and mo["theme_id"] != only_theme:
            return None
        return f'a moment in theme {mo["theme_id"]}: "{mo["claim"]}"'
    return None


# ---- DOC ----------------------------------------------------------------------------------

def _theme_codes_block(conn, mid: str, tid: str) -> str:
    hits: dict[str, list[str]] = {}
    for h in store.hits(conn, mid):
        hits.setdefault(h["name"], []).append(h["sid"])
    names = {c["name"] for c in store.theme_codes(conn, tid, mid)}
    lines = [f"- {n}: {', '.join(hits[n])}" for n in sorted(names) if n in hits]
    return "\n".join(lines) or "None of this theme's codes were marked here. Follow the definition."


def _claimed_block(conn, mid: str, tid: str) -> str:
    """Passages in this material another live theme has already claimed, with its claim.

    A real run recycled the same passages under three and four themes, twice with opposite
    valence. A line that cannot see what another theme has already read in a passage cannot tell
    whether it is adding a reading or repeating one under a second name.
    """
    rows = conn.execute(
        "SELECT mo.sid AS sid, mo.claim AS claim, t.name AS theme FROM moment mo "
        "JOIN theme t ON t.id = mo.theme_id "
        "WHERE mo.material_id=? AND mo.theme_id<>? AND mo.status='live' AND t.status='live'",
        (mid, tid)).fetchall()
    pos = store.sid_position(conn, mid)
    ordered = sorted(rows, key=lambda r: (pos.get(r["sid"], 10**9), r["theme"]))
    return "\n".join(f'{r["sid"]} — {r["theme"]} — {r["claim"]}' for r in ordered) or "None yet."


def _thread(conn, mid: str, tid: str, *, run_id: str | None) -> tuple[list[dict], list[str], dict]:
    """One theme's line through one material — one call, full attention.

    It used to be one call for every theme at once, plus the summary, plus the brief, plus the
    people. Six lines of four to fourteen claims each from a single answer is how lines come out
    thin: the model is rationing its attention across them. Now each line is its own call and the
    summary is written afterwards, over lines that exist.
    """
    row = store.material(conn, mid)
    pid = row["project_id"]
    proj = store.project(conn, pid)
    theme = conn.execute("SELECT * FROM theme WHERE id=?", (tid,)).fetchone()
    sents = store.sentences(conn, mid)
    nums = numbers(sents)

    system, user = llm.prompt(
        "thread",
        theme=f'{theme["id"]}  {theme["name"]} — {theme["gist"]}',
        codes=_theme_codes_block(conn, mid, tid),
        claimed=_claimed_block(conn, mid, tid),
        focus=proj["focus"] or "Nothing in particular. Follow the theme on its own terms.",
        frame=frame_block(conn, mid),
        feedback=feedback_block(conn, pid, mid, tid),
        material=layout(conn, mid),
        min_moments=MIN_MOMENTS, max_moments=MAX_MOMENTS, summary_words=THREAD_WORDS,
    )
    data = llm.chat_json(system, user, label="thread")

    stats, dropped, kept = anchor.new_stats(), [], []
    # Every moment is bound first and the cap applied to the SURVIVORS. Slicing first threw away
    # untested moments and could then leave the line under the floor.
    for m in data.get("moments") or []:
        if not isinstance(m, dict):
            continue
        claim = words(m.get("claim"), CLAIM_WORDS)
        quote = str(m.get("anchor") or "").strip()
        bound = anchor.apply(m, [cited(m.get("sid"), nums)], sents, stats)   # the anchor law
        if not claim:
            dropped.append(f'a moment with no claim was dropped (quote: "{quote[:60]}")')
            continue
        if bound is None:
            dropped.append(f'a moment was dropped: its quote is not in this material — "{quote[:60]}"'
                           if quote else "a moment was dropped: it carried no quote")
            continue
        quote, sids = bound
        kept.append({"claim": claim, "anchor": quote, "sid": sids[0]})
    if len(kept) > MAX_MOMENTS:
        dropped.append(f'the line for "{theme["name"]}" kept the first {MAX_MOMENTS} of {len(kept)} claims')
        kept = kept[:MAX_MOMENTS]
    if stats["over_cap"]:
        dropped.append(f"{stats['over_cap']} quote(s) ran past the 12-word cap and were kept")
    if len(kept) < MIN_MOMENTS:
        dropped.append(f'the line for "{theme["name"]}" was set aside: {len(kept)} claim'
                       f'{"" if len(kept) == 1 else "s"} left after checking the quotes, '
                       f"{MIN_MOMENTS} needed")
        return [], dropped, stats
    # Written only over a line that was kept: an account of claims that were thrown away would be
    # a reading with nothing under it, and the page cannot tell the two apart.
    if summary := words(data.get("summary"), THREAD_WORDS):
        store.save_summary(conn, "thread", f"{mid}:{tid}", "reading", summary, run_id)
    store.save_moments(conn, mid, tid, kept, run_id)     # ordered by position in the material
    return kept, dropped, stats


def doc(conn, mid: str, *, only_theme: str | None = None, run_id: str | None = None) -> dict:
    """Write this material's lines, then its summary over them.

    `only_theme` re-makes one line and leaves the summary, the questions and the people exactly as
    they are. Otherwise every live theme gets its own call, and the summary call sees the lines
    that actually exist rather than being asked to write them and introduce them in one breath.
    """
    row = store.material(conn, mid)
    if row is None:
        raise ValueError(f"no material {mid!r}")
    pid = row["project_id"]
    proj = store.project(conn, pid)
    live = {t["id"]: t for t in store.live_themes(conn, pid)}
    totals = anchor.new_stats()

    def tally(st):
        for k in totals:
            totals[k] += st.get(k, 0)

    if only_theme:
        if only_theme not in live:
            return {"summary": "", "threads": [], "anchors": dict.fromkeys(("bound", "rebound", "unfound"), 0),
                    "dropped": [f"theme {only_theme} is no longer live — its line was not rewritten"]}
        kept, dropped, st = _thread(conn, mid, only_theme, run_id=run_id)
        tally(st)
        stored = store.get_summary(conn, "material", mid, "reading")
        return {"summary": stored["text"] if stored else "",
                "threads": [{"theme_id": only_theme, "moments": kept}] if kept else [],
                "dropped": dropped, "anchors": {k: totals[k] for k in ("bound", "rebound", "unfound")}}

    threads, dropped = [], []
    for i, tid in enumerate(live, 1):
        llm.report(f"theme {i} of {len(live)}: {live[tid]['name']}")
        kept, d, st = _thread(conn, mid, tid, run_id=run_id)
        tally(st)
        dropped += d
        if kept:
            threads.append({"theme_id": tid, "moments": kept})

    shown = []
    for t in threads:
        shown.append(f'## {live[t["theme_id"]]["name"]}\n' + "\n".join(
            f'- {m["claim"]} — "{m["anchor"]}" [{m["sid"]}]' for m in t["moments"]))
    orientation = store.get_summary(conn, "material", mid, "orientation")
    system, user = llm.prompt(
        "doc",
        orientation=orientation["text"] if orientation else "Not written.",
        frame=frame_block(conn, mid),
        focus=proj["focus"] or "Nothing in particular. Read it on its own terms.",
        threads="\n\n".join(shown) or "No line held in this material.",
        feedback=feedback_block(conn, pid, mid, None),
        material=layout(conn, mid),
        summary_words=SUMMARY_WORDS, question_words=BRIEF_WORDS,
    )
    data = llm.chat_json(system, user, label="doc")

    if summary := words(data.get("summary"), SUMMARY_WORDS):
        store.save_summary(conn, "material", mid, "reading", summary, run_id)
    # The one self-prompting slot: QUESTIONS the corpus has left open, read only by the ideation
    # step for the next material. Never findings — conclusions flow up, only questions forward.
    if questions := words(data.get("questions"), BRIEF_WORDS):
        store.set_brief(conn, pid, questions)
    if "people" in data:
        store.save_people(conn, mid, [p for p in (data.get("people") or [])
                                      if isinstance(p, dict) and p.get("name")])
    return {"summary": summary, "threads": threads, "dropped": dropped,
            "anchors": {k: totals[k] for k in ("bound", "rebound", "unfound")}}


# ---- PROJECT ------------------------------------------------------------------------------

def project(conn, pid: str, *, run_id: str | None = None) -> dict:
    """The corpus summary, written over the theme accounts and the material summaries.

    In two movements, stored as two rows. What the corpus shows is what the researcher will cite;
    what it may mean is offered for them to argue with, and a page that ran the two together
    invited them to take the second on the authority of the first.

    It used to read every claim in every material — 210k tokens at fifty materials. It now reads
    what the layer below it concluded, which is what the account layer exists for. No new quotes
    at this level: a claim rests on claims below, cited by id, and a citation to a claim that is
    not live is stripped and said so.
    """
    proj = store.project(conn, pid)
    live_themes = {t["id"]: t for t in store.live_themes(conn, pid)}
    live_moments = {r["id"]: r for r in conn.execute(
        "SELECT m.* FROM moment m JOIN material x ON x.id=m.material_id "
        "WHERE x.project_id=? AND x.removed_at IS NULL AND m.status='live'", (pid,))}

    accounts = []
    for tid, t in live_themes.items():
        acc = store.get_summary(conn, "theme", tid)
        accounts.append(f'## {t["name"]} ({tid})\ndefinition: {t["gist"]}\n'
                        f'{acc["text"] if acc else "no account written yet"}')
    mats = []
    for m in store.materials(conn, pid):
        summary = store.get_summary(conn, "material", m["id"])
        mats.append(f'## {m["title"] or m["name"]} — {m["kind"] or "kind not worked out"}\n'
                    f'{summary["text"] if summary else "not read yet"}')

    fb = [f'{(f["created_at"] or "")[:10]} — {f["kind"]}\n"{f["text"]}"'
          for f in store.project_feedback(conn, pid)
          if f["target_kind"] == "project_summary" and (f["text"] or "").strip()]

    system, user = llm.prompt(
        "project",
        focus=(proj["focus"] if proj else "") or "Nothing in particular.",
        accounts="\n\n".join(accounts) or "No theme has an account yet.",
        materials="\n\n".join(mats) or "No material has been read yet.",
        feedback="\n\n".join(fb) or "The researcher has not said anything about the project yet.",
        summary_words=PROJECT_WORDS, interpretation_words=INTERPRETATION_WORDS,
    )
    data = llm.chat_json(system, user, label="project")

    # Two movements, two rows: what the corpus shows, and what it may mean. Kept apart because a
    # researcher must be able to cite the first while still arguing with the second.
    summary, dangling = _strip_dangling(words(data.get("summary"), PROJECT_WORDS), live_moments)
    reading_of, more = _strip_dangling(words(data.get("interpretation"), INTERPRETATION_WORDS),
                                       live_moments)
    dangling += more
    dropped = [f"the summary cited {len(dangling)} claim(s) that do not exist or are no longer live "
               f"— {', '.join(sorted(set(dangling)))} — and those citations were removed"] if dangling else []
    store.save_summary(conn, "project", pid, "reading", summary, run_id)
    # Written even when it is empty, so a fresh summary never sits over an older reading of it.
    store.save_summary(conn, "project", pid, "interpretation", reading_of, run_id)
    return {"summary": summary, "interpretation": reading_of, "dropped": dropped}


def _strip_dangling(text: str, live: dict) -> tuple[str, list[str]]:
    """Remove `[moment id]` citations that point at nothing, and an id repeated inside one
    bracket. A dangling citation is D15 wearing a different hat: a claim the researcher cannot
    open is a claim they must take on trust. A doubled one is thinner support dressed as two —
    `[mo1, mo1]` reads as two claims agreeing until you open them."""
    gone: list[str] = []

    def repl(m):
        ids = [i for i in re.split(r"[,;\s]+", m.group(1)) if i]
        keep = list(dict.fromkeys(i for i in ids if i in live))     # first occurrence wins
        gone.extend(i for i in ids if i not in live)
        return f" [{', '.join(keep)}]" if keep else ""

    return _CITE.sub(repl, text or "").strip(), gone
