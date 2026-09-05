"""P34 — flagging is not a resolution.

Five things a reading did instead of finishing what it started, each read off a real eight-material
record (`bench/records/ellis-8mat.md`):

    a line's summary said it predated the check     16 times, rather than being written again over
                                                    the claims that stand
    a claim was marked "partly carried"             291 of 748, the mark doing the work a rewrite
                                                    should do
    a summary sentence was flagged and kept         34 times, eleven of them saying what the
                                                    material IS — a date, an age, a place — which
                                                    the check was never shown the description for
    a reach counted a one-claim line whole          "7 of 8 materials" over lines of one
    the open questions ended in "…"                 mid-clause, in the one register a researcher
                                                    reads to decide what to look for next

`app/engine/tighten.py`, `synth.line_summary`, `verify.run`'s `lost`, `verify_summary.run`'s
`again`, `context._reach`, `store.open_questions`.
"""
from __future__ import annotations

import pytest

from app import context, store

synth = pytest.importorskip("app.engine.synth")
tighten = pytest.importorskip("app.engine.tighten")
verify = pytest.importorskip("app.engine.verify")


@pytest.fixture
def ready(conn, project, grande):
    """One material, framed and described, with two themes to follow through it."""
    store.save_frame(conn, grande, kind="interview", display="turns", title="Grande",
                     speakers=[{"label": "GRANDE", "name": "M. Grande", "role": "participant"}],
                     segments=[])
    store.save_summary(conn, "material", grande, "orientation",
                       "A 1978 oral history, recorded in Chicago.")
    work = store.save_theme(conn, project, tid=None, name="Work", gist="a living", code_ids=[])
    away = store.save_theme(conn, project, tid=None, name="Leaving", gist="the crossing",
                            code_ids=[])
    return {"pid": project, "mid": grande, "work": work, "away": away}


def _moments(quote, mid, n=5, at=40):
    return [{"claim": f"claim {i}", "anchor": " ".join(quote(mid, at=at + i * 9)[1].split()[:8]),
             "sid": quote(mid, at=at + i * 9)[0]} for i in range(n)]


def _write(conn, ready, tid, quote, n=5):
    """A line and its summary, written the way THREAD writes them — no model."""
    store.save_moments(conn, ready["mid"], tid, _moments(quote, ready["mid"], n))
    store.save_summary(conn, "thread", f'{ready["mid"]}:{tid}', "reading",
                       "an account of this line")


def _summary_of(conn, ready, tid) -> str:
    row = store.get_summary(conn, "thread", f'{ready["mid"]}:{tid}', "reading")
    return row["text"] if row else ""


def _labels(model) -> list[str]:
    return [c["label"] for c in model.calls]


# ---- a line's summary is written again over what stands ----------------------------------------

def test_only_a_line_that_lost_a_claim_is_summarised_again(ready, conn, model, quote):
    """The record said "(1 claim was set aside after checking; this summary predates that.)"
    sixteen times. A summary is ninety words over claims already in front of the model."""
    _write(conn, ready, ready["work"], quote)
    _write(conn, ready, ready["away"], quote)
    doomed = store.thread(conn, ready["mid"], ready["work"])[0]
    every = store.moments(conn, ready["mid"])

    model.queue({"verdicts": [{"id": m["id"],
                               "verdict": "not" if m["id"] == doomed["id"] else "supported",
                               "why": "not said here"} for m in every]})
    lost = verify.run(conn, ready["mid"])["lost"]
    assert lost == [ready["work"]], "the check names the line it took the claim from"

    model.queue({"summary": "written again over the four that stand"})
    synth.line_summary(conn, ready["mid"], ready["work"])

    assert _summary_of(conn, ready, ready["work"]) == "written again over the four that stand"
    assert _summary_of(conn, ready, ready["away"]) == "an account of this line", \
        "the line that lost nothing is not rewritten and is not paid for"
    assert _labels(model).count("line_summary") == 1


def test_the_line_summary_is_shown_the_theme_and_the_claims_that_stand(ready, conn, model, quote):
    _write(conn, ready, ready["work"], quote, n=3)
    marked = store.thread(conn, ready["mid"], ready["work"])[0]
    store.mark_support(conn, [(marked["id"], "partly", "'without complaint' is not there")])

    model.queue({"summary": "what this material says on work"})
    synth.line_summary(conn, ready["mid"], ready["work"])

    shown = model.shown("line_summary")
    assert "Work — a living" in shown
    for m in store.thread(conn, ready["mid"], ready["work"]):
        assert f'[{m["id"]}] {m["claim"]} — quoted "{m["anchor"]}"' in shown
    assert "— partly: 'without complaint' is not there" in shown, "what the check left on it"


def test_a_line_whose_every_claim_went_keeps_no_account_of_them(ready, conn, model, quote):
    """Nothing is asked of the model, and the paragraph about claims that are gone goes with
    them. The line is `thin`, which is said in the follow row and not here."""
    _write(conn, ready, ready["work"], quote, n=2)
    for m in store.thread(conn, ready["mid"], ready["work"]):
        store.mark_support(conn, [(m["id"], "not", "the passage says otherwise")])

    assert synth.line_summary(conn, ready["mid"], ready["work"]) == []
    assert _summary_of(conn, ready, ready["work"]) == ""
    assert not model.calls, "an empty line costs nothing"


# ---- the claims the check found only partly carried ---------------------------------------------

def _partly(conn, ready, quote, n=3):
    """A line of `n` claims, every one of them marked as only partly carried."""
    _write(conn, ready, ready["work"], quote, n=n)
    rows = store.thread(conn, ready["mid"], ready["work"])
    store.mark_support(conn, [(m["id"], "partly", f"'{m['claim']}' adds a manner") for m in rows])
    return rows


def test_a_tightened_claim_replaces_its_own_words_and_loses_its_mark(ready, conn, model, quote):
    """291 of 748 standing claims carried the mark. It is the addition that has to go, not the
    reader's confidence in the claim."""
    a, b, c = _partly(conn, ready, quote)
    model.queue({"claims": [{"id": a["id"], "claim": "He took factory work."},
                            {"id": b["id"], "claim": ""}]},
                {"verdicts": [{"id": a["id"], "verdict": "supported", "why": ""}]},
                {"summary": "written again over what stands"})
    out = tighten.run(conn, ready["mid"])

    kept = store.moment(conn, a["id"])
    assert kept["claim"] == "He took factory work."
    assert (kept["support"], kept["support_note"]) == ("", ""), "the mark went with the words"
    assert kept["anchor"] == a["anchor"] and kept["sid"] == a["sid"], "the quote never moves"

    gone = store.moment(conn, b["id"])
    assert gone["status"] == "superseded"
    assert any(n.startswith("a claim tightened to nothing was set aside —") for n in out["dropped"])

    left = store.moment(conn, c["id"])
    assert left["support"] == "partly" and left["claim"] == c["claim"], \
        "an id the answer left out keeps its claim and its mark"
    assert out["dropped"][-1] == "1 claims tightened, 1 set aside, 1 still partly carried"


def test_a_tightened_claim_is_checked_again(ready, conn, model, quote):
    """A rewrite is a new claim. One that still reaches past its passage is marked again rather
    than trusted for having been through here."""
    a, _b, _c = _partly(conn, ready, quote)
    model.queue({"claims": [{"id": a["id"], "claim": "He took factory work, reluctantly."}]},
                {"verdicts": [{"id": a["id"], "verdict": "partly", "why": "'reluctantly' added"}]},
                {"summary": "written again"})
    tighten.run(conn, ready["mid"])

    assert _labels(model) == ["tighten", "verify", "line_summary"]
    again = store.moment(conn, a["id"])
    assert (again["support"], again["support_note"]) == ("partly", "'reluctantly' added")
    assert f'[{a["id"]}]' in model.shown("verify"), "the rewritten claim, not the old one"


def test_the_pass_is_shown_what_the_check_named_the_quote_and_the_passage(ready, conn, model,
                                                                          quote):
    a, _b, _c = _partly(conn, ready, quote)
    model.queue({"claims": []})
    tighten.run(conn, ready["mid"])

    shown = model.shown("tighten")
    assert f'[{a["id"]}] {a["claim"]}' in shown
    assert f"the check found added: '{a['claim']}' adds a manner" in shown
    assert f'quoted: "{a["anchor"]}"' in shown
    assert a["sid"] in shown, "the passage with its neighbours"
    assert "kind: interview" in shown, "the frame"


def test_nothing_marked_is_no_call_at_all(ready, conn, model, quote):
    """The fake model raises on a call nobody expected, which is how this asserts there was
    none."""
    _write(conn, ready, ready["work"], quote)
    assert tighten.run(conn, ready["mid"]) == {"dropped": []}
    assert not model.calls


def test_the_pass_can_be_taken_out_of_the_chain(ready, conn, model, quote, monkeypatch):
    """The harness measures the mark against the rewrite, so it needs the marked claims left
    standing."""
    a, _b, _c = _partly(conn, ready, quote)
    monkeypatch.setenv("APERTURE_TIGHTEN", "off")
    assert tighten.run(conn, ready["mid"]) == {"dropped": []}
    assert not model.calls
    assert store.moment(conn, a["id"])["support"] == "partly"


def test_the_chain_tightens_each_material_after_its_lines_are_checked(conn, project, grande):
    """Right after DOC, in the same sequence as that material's synthesis — the mark is written
    by the check inside DOC and nothing else may be written over it first."""
    from app import jobs
    planned: list[dict] = []
    real = jobs.start
    jobs.start = lambda factory, pid, runs: planned.extend(runs)
    try:
        jobs.ingest_chain(project, [grande])
    finally:
        jobs.start = real
    kinds = [r["kind"] for r in planned]
    assert kinds[kinds.index("doc") + 1] == "tighten"
    assert jobs.line(conn, {"kind": "tighten", "material_id": grande}) == \
        "Tightening claims the check found only partly carried in DP-40 Grande"


# ---- the summary check, shown the description and given one rewrite -----------------------------

def _doc(model, conn, ready, quote, verdicts, summary, again=None):
    """One full DOC over one theme, whose summary check answers `verdicts`."""
    store.merge_theme(conn, ready["away"], ready["work"])   # one theme, so one THREAD call
    model.queue({"moments": _moments(quote, ready["mid"], 5), "summary": "an account"},
                {"verdicts": []},
                {"summary": summary, "questions": "", "people": []},
                {"verdicts": verdicts})
    if again is not None:
        model.queue({"summary": again, "questions": "", "people": []}, {"verdicts": []})
    return synth.doc(conn, ready["mid"])


FLAGGED = ("The reading follows work through this interview. "
           "This is a 1978 oral history recorded in Chicago.")


def test_the_summary_check_is_shown_what_the_material_is(ready, conn, model, quote):
    """Rule 2 judges a sentence about the material's kind or its date against the description, and
    the description was not in the prompt: eleven of one record's thirty-four flagged sentences
    were flagged for a date, an age or a place that only the description carries."""
    _doc(model, conn, ready, quote, [], FLAGGED)
    assert "A 1978 oral history, recorded in Chicago." in model.shown("verify_summary")


def test_a_flagged_summary_is_written_again_once_with_the_flags(ready, conn, model, quote):
    """Flagging and keeping is not a resolution. The writer is handed what the check named and one
    more attempt, and what is still flagged after it is kept with a note, as before."""
    out = _doc(model, conn, ready, quote,
               [{"n": 2, "verdict": "partly", "why": "'Chicago' is in no claim"}],
               FLAGGED, again="The reading follows work through this interview.")

    second = [c["user"] for c in model.calls if c["label"] == "doc"][-1]
    assert "THE CHECK FOUND these sentences go past the claims" in second
    assert "This is a 1978 oral history recorded in Chicago. — 'Chicago' is in no claim" in second
    assert _labels(model).count("doc") == 2 and _labels(model).count("verify_summary") == 2, \
        "one rewrite, never a loop"
    assert store.get_summary(conn, "material", ready["mid"], "reading")["text"] == \
        "The reading follows work through this interview."
    assert any("written again after the check flagged 1 sentence" in d for d in out["dropped"])


def test_what_the_rewrite_does_not_fix_is_kept_with_its_flag(ready, conn, model, quote):
    """The bound is the point: a second rewrite would be a loop over a judgement already made."""
    out = _doc(model, conn, ready, quote,
               [{"n": 2, "verdict": "partly", "why": "'Chicago' is in no claim"}],
               FLAGGED, again=FLAGGED)
    # The rewrite came back unchanged, and the second check (queued empty) ruled on nothing — so
    # the summary stands whole and no third attempt was made.
    assert store.get_summary(conn, "material", ready["mid"], "reading")["text"] == FLAGGED
    assert _labels(model).count("doc") == 2
    assert not any("set aside" in d for d in out["dropped"])


# ---- a reach that says how many of its lines are short -------------------------------------------

def _line(conn, pid, mid, tid, quote, n):
    store.save_moments(conn, mid, tid, _moments(quote, mid, n))


def test_a_reach_says_how_many_of_its_lines_are_sparse(conn, project, grande, rodwin, quote):
    """A line of one claim counts towards "7 of 8 materials" exactly as a line of twelve does. The
    count of carrying materials is unchanged — it still matches the cells — and the qualification
    follows it."""
    for mid in (grande, rodwin):
        store.save_frame(conn, mid, kind="interview", display="turns", title=mid, speakers=[],
                         segments=[])
    tid = store.save_theme(conn, project, tid=None, name="Work", gist="a living", code_ids=[])
    _line(conn, project, grande, tid, quote, synth.MIN_MOMENTS)
    _line(conn, project, rodwin, tid, quote, synth.MIN_MOMENTS)
    assert context.theme_page(conn, project, tid)["derivation"].startswith("2 of 2 materials ·")

    _line(conn, project, rodwin, tid, quote, synth.MIN_MOMENTS - 1)
    said = context.theme_page(conn, project, tid)["derivation"]
    assert said.startswith("2 of 2 materials (1 sparse) ·"), said


# ---- open questions, cut at a question ----------------------------------------------------------

QUESTIONS = "What became of the sisters? Whether the wage was ever enough is never asked. "


def test_the_register_is_cut_at_a_question_and_never_elided(conn, project, grande, rodwin):
    for mid in (grande, rodwin):
        store.save_summary(conn, "material", mid, "questions", QUESTIONS * 40)
    out = store.open_questions(conn, project)

    assert len(out) == 2
    for q in out:
        assert not q["text"].endswith("…") and "…" not in q["text"]
        assert q["text"].endswith("?") or q["text"].endswith(".")
    assert sum(len(q["text"].split()) for q in out) <= store.QUESTION_WORDS


def test_a_material_with_no_room_for_a_whole_question_is_counted_instead(conn, project, grande,
                                                                        rodwin):
    """A fragment of a question is worse than a material named as not shown: this register is
    what the next reading is told to look for."""
    for mid in (grande, rodwin):
        store.save_summary(conn, "material", mid, "questions", QUESTIONS * 40)
    out = store.open_questions(conn, project, cap=40)

    assert len(out) == 2, "one material's questions, and the line saying so"
    assert out[-1] == {"material_id": "", "material": "",
                       "text": "(questions from 1 more materials not shown)"}
    assert "(questions from 1 more materials not shown)" in \
        store.questions_text(conn, project, cap=40)


def test_nothing_is_said_about_materials_that_are_all_shown(conn, project, grande):
    store.save_summary(conn, "material", grande, "questions", "What became of the sisters?")
    assert store.questions_text(conn, project) == "From DP-40 Grande: What became of the sisters?"
