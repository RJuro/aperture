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
SUMMARY_WORDS, PROJECT_WORDS, BRIEF_WORDS, CLAIM_WORDS, GIST_WORDS = 320, 400, 120, 30, 40

_CITE = re.compile(r"\s*\[([^\[\]]+)\]")


# ---- text ---------------------------------------------------------------------------------

def words(text, cap: int) -> str:
    """A cap the prompt also states as a number. Both, always: a cap only in the prompt is a
    request, and a cap only in Python is a surprise."""
    t = str(text or "").strip()
    return t if len(t.split()) <= cap else " ".join(t.split()[:cap]) + " …"


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

def doc(conn, mid: str, *, only_theme: str | None = None, run_id: str | None = None) -> dict:
    """Write this material's reading summary and its threads.

    `only_theme` restricts the rerun to one theme — a researcher reacted to one thread, so one
    thread is re-made and the summary, the brief and the people are left exactly as they are.
    """
    row = store.material(conn, mid)
    if row is None:
        raise ValueError(f"no material {mid!r}")
    pid = row["project_id"]
    proj = store.project(conn, pid)
    sents = store.sentences(conn, mid)
    nums = numbers(sents)
    live = {t["id"]: t for t in store.live_themes(conn, pid)}
    orientation = store.get_summary(conn, "material", mid, "orientation")

    if only_theme and only_theme not in live:
        # THEMES can merge a theme away between the reaction and this rerun. Nothing to rewrite,
        # and no call to make: say so rather than quietly re-reading the whole material.
        return {"summary": "", "threads": [], "anchors": dict.fromkeys(
            ("bound", "rebound", "unfound"), 0),
            "dropped": [f"theme {only_theme} is no longer live — its thread was not rewritten"]}

    if only_theme:
        task = (f'Rewrite ONE thread: the theme {only_theme} ("{live[only_theme]["name"]}"). '
                f"Return that one thread in `threads`, and nothing else in it. Return `summary`, "
                f"`brief` and `people` as empty — they are not being rewritten this time.")
        shown = [live[only_theme]]
    else:
        task = ("Write what the reading found in this material: a summary, one thread for every "
                "theme that has at least 2 quotable moments here, the people it names, and the "
                "brief for whoever reads the next piece.")
        shown = list(live.values())

    system, user = llm.prompt(
        "doc",
        task=task,
        brief=proj["brief"] or "Nothing yet — this is the first piece read.",
        focus=proj["focus"] or "Nothing in particular. Read it on its own terms.",
        frame=frame_block(conn, mid),
        orientation=orientation["text"] if orientation else "Not written.",
        themes=themes_block(shown),
        codes=codes_block(conn, mid),
        feedback=feedback_block(conn, pid, mid, only_theme),
        material=layout(conn, mid),
    )
    data = llm.chat_json(system, user, label="doc")

    stats, dropped, threads = anchor.new_stats(), [], []
    for t in data.get("threads") or []:
        if not isinstance(t, dict):
            continue
        tid = str(t.get("theme_id") or "").strip()
        if tid not in live:
            dropped.append(f"a thread named a theme that is not live ({tid or 'no id'}) — dropped")
            continue
        if only_theme and tid != only_theme:
            continue
        kept = []
        # Every moment is bound first and the cap applied to the SURVIVORS. Slicing first threw
        # away untested moments and could then leave the line under the floor — a thread dropped
        # for thinness that was never actually thin.
        for m in (t.get("moments") or []):
            if not isinstance(m, dict):
                continue
            claim = words(m.get("claim"), CLAIM_WORDS)
            quote = str(m.get("anchor") or "").strip()
            # The anchor law. The citation is a hint; the quote is the evidence.
            bound = anchor.apply(m, [cited(m.get("sid"), nums)], sents, stats)
            if not claim:
                dropped.append(f'a moment with no claim was dropped (quote: "{quote[:60]}")')
                continue
            if bound is None:
                dropped.append(f'a moment was dropped: its quote is not in this material — '
                               f'"{quote[:60]}"' if quote
                               else "a moment was dropped: it carried no quote")
                continue
            quote, sids = bound
            kept.append({"claim": claim, "anchor": quote, "sid": sids[0]})
        if len(kept) > MAX_MOMENTS:
            dropped.append(f'the line for "{live[tid]["name"]}" kept the first '
                           f'{MAX_MOMENTS} of {len(kept)} claims')
            kept = kept[:MAX_MOMENTS]
        if len(kept) < MIN_MOMENTS:
            dropped.append(f'the thread for "{live[tid]["name"]}" was dropped: {len(kept)} moment'
                           f'{"" if len(kept) == 1 else "s"} left after checking the quotes, '
                           f"{MIN_MOMENTS} needed")
            continue
        # save_moments orders by position in the material — the reader walks the material, not
        # the model's ranking — so these go through in the order they came.
        store.save_moments(conn, mid, tid, kept, run_id)
        threads.append({"theme_id": tid, "moments": kept})

    if stats["over_cap"]:
        dropped.append(f"{stats['over_cap']} quote(s) ran past the 12-word cap and were kept — "
                       "over-long is a prompt problem, not a grounding one")

    summary = words(data.get("summary"), SUMMARY_WORDS)
    if only_theme is not None:
        # One thread was reacted to, so one thread is re-made. The summary, the brief and the
        # people are not this rerun's to touch (PLAN.md §1).
        stored = store.get_summary(conn, "material", mid, "reading")
        summary = stored["text"] if stored else ""
    else:
        if summary:
            store.save_summary(conn, "material", mid, "reading", summary, run_id)
        # The one self-prompting slot in the system: DOC writes the brief, READ and DOC read it.
        if brief := words(data.get("brief"), BRIEF_WORDS):
            store.set_brief(conn, pid, brief)
        # Only when the model actually answered: an omitted field must not wipe what is stored.
        if "people" in data:
            store.save_people(conn, mid, [p for p in (data.get("people") or [])
                                          if isinstance(p, dict) and p.get("name")])

    return {"summary": summary, "threads": threads, "dropped": dropped,
            "anchors": {k: stats[k] for k in ("bound", "rebound", "unfound")}}


# ---- PROJECT ------------------------------------------------------------------------------

def project(conn, pid: str, *, run_id: str | None = None) -> dict:
    """The project summary. No new quotes at this level: a project claim rests on moments, cited
    by moment id in brackets, and a citation to a moment that is not live is stripped and said so.
    """
    proj = store.project(conn, pid)
    live_themes = {t["id"]: t for t in store.live_themes(conn, pid)}
    live_moments: dict[str, object] = {}
    blocks = []
    for m in store.materials(conn, pid):
        summary = store.get_summary(conn, "material", m["id"])
        lines = [f'## {m["title"] or m["name"]} — {m["kind"] or "kind not worked out"}',
                 f'what the reading found: {summary["text"] if summary else "not written yet"}']
        for tid, t in live_themes.items():
            rows = store.thread(conn, m["id"], tid)
            if not rows:
                continue
            lines.append(f'thread — {t["name"]} ({tid}):')
            for mo in rows:
                live_moments[mo["id"]] = mo
                lines.append(f'  [{mo["id"]}] {mo["claim"]} — quoted: "{mo["anchor"]}"')
        blocks.append("\n".join(lines))

    fb = [f'{(f["created_at"] or "")[:10]} — {f["kind"]}\n"{f["text"]}"'
          for f in store.project_feedback(conn, pid)
          if f["target_kind"] == "project_summary" and (f["text"] or "").strip()]

    system, user = llm.prompt(
        "project",
        focus=(proj["focus"] if proj else "") or "Nothing in particular.",
        themes=themes_block(list(live_themes.values())),
        feedback="\n\n".join(fb) or "The researcher has not said anything about the project yet.",
        materials="\n\n".join(blocks) or "No material has been read yet.",
    )
    data = llm.chat_json(system, user, label="project")

    summary, dangling = _strip_dangling(words(data.get("summary"), PROJECT_WORDS), live_moments)
    dropped = [f"the summary cited {len(dangling)} moment(s) that do not exist or are no longer "
               f"live — {', '.join(sorted(set(dangling)))} — and those citations were removed"] \
        if dangling else []

    gists = []
    for g in data.get("theme_gists") or []:
        if not isinstance(g, dict):
            continue
        tid = str(g.get("theme_id") or "").strip()
        if tid not in live_themes:
            dropped.append(f"a gist named a theme that is not live ({tid or 'no id'}) — dropped")
            continue
        ids = [str(i) for i in (g.get("moment_ids") or [])]
        keep, gone = [i for i in ids if i in live_moments], [i for i in ids if i not in
                                                             live_moments]
        if gone:
            dropped.append(f'the gist for "{live_themes[tid]["name"]}" cited {len(gone)} moment(s)'
                           f" that do not exist — {', '.join(sorted(set(gone)))} — dropped")
        gist = words(g.get("gist"), GIST_WORDS)
        if gist:
            # Written through the gist-only writer: `save_theme` also rewrites a theme's codes,
            # and the project synthesis does not know which codes belong where.
            store.set_theme_gist(conn, tid, gist)
        gists.append({"theme_id": tid, "gist": gist, "moment_ids": keep})

    store.save_summary(conn, "project", pid, "reading", summary, run_id)
    return {"summary": summary, "theme_gists": gists, "dropped": dropped}


def _strip_dangling(text: str, live: dict) -> tuple[str, list[str]]:
    """Remove `[moment id]` citations that point at nothing. A dangling citation is D15 wearing a
    different hat: a claim the researcher cannot open is a claim they must take on trust."""
    gone: list[str] = []

    def repl(m):
        ids = [i for i in re.split(r"[,;\s]+", m.group(1)) if i]
        keep = [i for i in ids if i in live]
        gone.extend(i for i in ids if i not in live)
        return f" [{', '.join(keep)}]" if keep else ""

    return _CITE.sub(repl, text or "").strip(), gone
