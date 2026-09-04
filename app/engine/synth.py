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

import contextvars
import re
import textwrap
import unicodedata
from concurrent.futures import ThreadPoolExecutor

from .. import anchor, llm, store

MIN_MOMENTS, MAX_MOMENTS = 4, 14
SUMMARY_WORDS, PROJECT_WORDS, BRIEF_WORDS, CLAIM_WORDS, GIST_WORDS = 320, 300, 120, 30, 40
# What the corpus may mean, as against what it shows: shorter, because it is the movement a
# researcher argues with rather than the one they cite.
INTERPRETATION_WORDS = 150
# What one theme amounts to in one material. Short, because the claims below it are the finding
# and this only says how they hang together.
THREAD_WORDS = 90

# How many of a material's lines are written at once (see `doc`). Three, not all of them: a line is
# shown what the waves before it claimed here, and a wave of ten would show the tenth line nothing.
WAVE = 3

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


def clip(text, chars: int = 60) -> str:
    """Shorten a quote or a claim for a set-aside note, on a word boundary, and say so.

    A blind reader of a real record read `"...the savings built from factory an"` as damage to
    the record itself. The note is naming a claim so a researcher can go and find it; a word cut
    in half is a worse pointer than a shorter one.
    """
    t = " ".join(str(text or "").split())
    if len(t) <= chars:
        return t
    short = textwrap.shorten(t, chars, placeholder=" …")
    # One word longer than the whole budget leaves shorten nothing to keep — cut it hard.
    return short if len(short) > 1 else t[:chars - 1] + "…"



# The scripts a token can be written in that this instrument will question. Matched against the
# Unicode name of each character, so no table and no dependency: CJK UNIFIED IDEOGRAPH-4E2D,
# HANGUL SYLLABLE GA, CYRILLIC SMALL LETTER A.
_SCRIPTS = ("CJK", "HIRAGANA", "KATAKANA", "HANGUL", "CYRILLIC", "ARABIC", "HEBREW", "GREEK",
            "THAI")


def scripts(text) -> set[str]:
    """Which of those scripts these characters are written in."""
    out: set[str] = set()
    for ch in set(text or ""):
        name = unicodedata.name(ch, "")
        out |= {s for s in _SCRIPTS if s in name}
    return out


def foreign(text: str, allowed: str) -> tuple[str, list[str]]:
    """Drop any word written in a script the material and the researcher's focus never use.

    A summary of three English interviews came back with a Chinese token in the middle of a
    sentence — the model's own vocabulary surfacing, not anything the material said. The test is
    what the text in front of the reading is written in, never a list of scripts this instrument
    approves of, so material in Cyrillic keeps its Cyrillic and this does nothing at all.
    """
    if not scripts(text):
        return text, []                 # the ordinary case: nothing to weigh the material against
    ok = scripts(allowed)
    kept, dropped = [], []
    for token in (text or "").split():
        (dropped if scripts(token) - ok else kept).append(token)
    return (" ".join(kept) if dropped else text), dropped


def script_notes(dropped: list[str]) -> list[str]:
    return [f"a word in a script the material does not use was removed: {t}" for t in dropped]


def allowed_text(conn, pid: str, mid: str | None = None) -> str:
    """What a reading of this material — or of this corpus — may be written in.

    ponytail: without `mid` this reads every material's text. At fifty materials that is a few
    megabytes per call, next to a model call that takes a minute; pass the scripts down from the
    step above if it ever shows up in a profile.
    """
    proj = store.project(conn, pid)
    rows = [store.material(conn, mid)] if mid else store.materials(conn, pid)
    return " ".join([(proj["focus"] if proj else "") or ""]
                    + [r["text"] for r in rows if r is not None])


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


def _thread_prompt(conn, mid: str, tid: str) -> tuple[tuple[str, str], list, dict, str]:
    """What one line's call needs, read on THIS connection: the prompt, the passages its answer
    will be bound against, the theme, the project.

    Split out of `_thread` so a wave of lines can be prepared here, in theme order — each shown
    what the waves before it claimed — and the calls themselves made off in threads.
    """
    row = store.material(conn, mid)
    pid = row["project_id"]
    proj = store.project(conn, pid)
    theme = conn.execute("SELECT * FROM theme WHERE id=?", (tid,)).fetchone()
    prompt = llm.prompt(
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
    return prompt, store.sentences(conn, mid), theme, pid


def _thread_kept(conn, mid: str, tid: str, data: dict, sents: list, theme, pid: str, *,
                 run_id: str | None) -> tuple[list[dict], list[str], dict]:
    """One answer → this line's moments, bound against the material, capped and written.

    On the caller's connection, always: the calls of a wave run side by side, the writes that
    follow them do not.
    """
    nums = numbers(sents)
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
            dropped.append(f'a moment with no claim was dropped (quote: "{clip(quote)}")')
            continue
        if bound is None:
            dropped.append(f'a moment was dropped: its quote is not in this material — "{clip(quote)}"'
                           if quote else "a moment was dropped: it carried no quote")
            continue
        quote, sids = bound
        kept.append({"claim": claim, "anchor": quote, "sid": sids[0]})
    if len(kept) > MAX_MOMENTS:
        dropped.append(f'the line for "{theme["name"]}" kept the first {MAX_MOMENTS} of {len(kept)} claims')
        kept = kept[:MAX_MOMENTS]
    # Named, one by one. "3 quote(s) ran past the cap and were kept" told a researcher that
    # something had been let through without telling them which claim to go and look at.
    dropped += [f'a quote ran past the {anchor.ANCHOR_WORD_CAP}-word cap and was kept — '
                f'"{clip(m["anchor"])}" ({theme["name"]})'
                for m in kept if anchor.word_count(m["anchor"]) > anchor.ANCHOR_WORD_CAP]
    if len(kept) < MIN_MOMENTS:
        dropped.append(f'the line for "{theme["name"]}" was set aside: {len(kept)} claim'
                       f'{"" if len(kept) == 1 else "s"} left after checking the quotes, '
                       f"{MIN_MOMENTS} needed")
        return [], dropped, stats
    # Written only over a line that was kept: an account of claims that were thrown away would be
    # a reading with nothing under it, and the page cannot tell the two apart.
    summary, odd = foreign(words(data.get("summary"), THREAD_WORDS), allowed_text(conn, pid, mid))
    dropped += script_notes(odd)
    if summary:
        store.save_summary(conn, "thread", f"{mid}:{tid}", "reading", summary, run_id)
    store.save_moments(conn, mid, tid, kept, run_id)     # ordered by position in the material
    return kept, dropped, stats


def _thread(conn, mid: str, tid: str, *, run_id: str | None) -> tuple[list[dict], list[str], dict]:
    """One theme's line through one material — one call, full attention.

    It used to be one call for every theme at once, plus the summary, plus the brief, plus the
    people. Six lines of four to fourteen claims each from a single answer is how lines come out
    thin: the model is rationing its attention across them. Now each line is its own call and the
    summary is written afterwards, over lines that exist.
    """
    prompt, sents, theme, pid = _thread_prompt(conn, mid, tid)
    data = llm.chat_json(*prompt, label="thread")
    return _thread_kept(conn, mid, tid, data, sents, theme, pid, run_id=run_id)


def doc(conn, mid: str, *, only_theme: str | None = None, run_id: str | None = None) -> dict:
    """Write this material's lines, then its summary over them.

    `only_theme` re-makes one line and leaves the summary, the questions and the people exactly as
    they are. Otherwise every live theme gets its own call — in waves of `WAVE`, side by side —
    and the summary call sees the lines that actually exist rather than being asked to write them
    and introduce them in one breath.
    """
    from . import verify, verify_summary   # they read this module; imported here so neither waits on the other
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
        if kept:
            dropped += verify.run(conn, mid, theme_id=only_theme, run_id=run_id)["dropped"]
            kept = [dict(m) for m in store.thread(conn, mid, only_theme)]
        stored = store.get_summary(conn, "material", mid, "reading")
        return {"summary": stored["text"] if stored else "",
                "threads": [{"theme_id": only_theme, "moments": kept}] if kept else [],
                "dropped": dropped, "anchors": {k: totals[k] for k in ("bound", "rebound", "unfound")}}

    threads, dropped = [], []
    order = list(live)               # live_themes order, so the waves compose the same way twice
    # In waves, because this is the dominant cost of the whole chain — nine to ten calls at 60–80
    # s each, 1351 s for one nine-theme material — and the calls are not independent. The guard the
    # sequence existed for is kept whole: every line is shown what the waves BEFORE it claimed in
    # this material (`_claimed_block`, built here in theme order just before the wave goes out),
    # which is what stops one passage coming back under three themes. What a line no longer sees is
    # its own wave-mates, claiming at the same moment as it.
    #
    # Up to `jobs.PARALLEL` × WAVE calls are therefore in flight when DOC steps run side by side.
    # No semaphore: the provider answers over its rate limit with a 429 and `llm._ask` waits that
    # out, which is the same answer a semaphore would give more slowly.
    with ThreadPoolExecutor(max_workers=WAVE) as pool:
        for at in range(0, len(order), WAVE):
            wave = order[at:at + WAVE]
            prepared = [_thread_prompt(conn, mid, tid) for tid in wave]
            # Each in its OWN copy of this context, so `llm.usage` and `llm.report` are still this
            # step's — the tokens land on this run row (see llm.new_usage).
            answers = [f.result() for f in [
                pool.submit(contextvars.copy_context().run, llm.chat_json, *prompt,
                            label="thread") for prompt, *_ in prepared]]
            for tid, (_, sents, theme, tpid), data in zip(wave, prepared, answers):
                kept, d, st = _thread_kept(conn, mid, tid, data, sents, theme, tpid,
                                           run_id=run_id)
                tally(st)
                dropped += d
                if kept:
                    threads.append({"theme_id": tid, "moments": kept})
            llm.report(f"{min(at + WAVE, len(order))} of {len(order)} lines written")

    # Before the summary, never after: a summary written over a claim the passage does not carry
    # introduces that claim by name, and the claim is gone by the time anyone reads it.
    dropped += verify.run(conn, mid, run_id=run_id)["dropped"]
    threads = [t for t in ({"theme_id": t["theme_id"],
                            "moments": [dict(m) for m in store.thread(conn, mid, t["theme_id"])]}
                           for t in threads) if t["moments"]]

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

    summary, odd = foreign(words(data.get("summary"), SUMMARY_WORDS), allowed_text(conn, pid, mid))
    dropped += script_notes(odd)
    # Before it is stored, never after: the summary a researcher reads first is the one that was
    # checked against the claims under it, and a sentence they do not carry never reaches the page.
    summary, said = verify_summary.run(conn, mid, summary)
    dropped += said
    if summary:
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
    allowed = allowed_text(conn, pid)
    summary, dangling = _strip_dangling(words(data.get("summary"), PROJECT_WORDS), live_moments)
    reading_of, more = _strip_dangling(words(data.get("interpretation"), INTERPRETATION_WORDS),
                                       live_moments)
    dangling += more
    summary, odd = foreign(summary, allowed)
    reading_of, more_odd = foreign(reading_of, allowed)
    dropped = script_notes(odd + more_odd)
    if dangling:
        dropped.append(f"the summary cited {len(dangling)} claim(s) that do not exist or are no "
                       f"longer live — {', '.join(sorted(set(dangling)))} — and those citations "
                       "were removed")
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
