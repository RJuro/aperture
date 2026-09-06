"""P38 — the tier above the themes, and where a material sits at the edge of a definition.

`app/engine/synth.py`, `app/prompts/project.md`, `app/prompts/thread.md`.

    synth.project(conn, pid) -> {"summary","overarching","interpretation","dropped"}
        one `project` call, stored as three rows: what the corpus shows, the overarching set that
        gathers its themes, and what it may mean
    synth.doc(conn, mid)     a line's `fit` — at most 25 words on how THIS material carries the
        theme in a way its definition did not foresee — kept as a theme note of kind `fit`

Three human coders reading the same corpus gathered twenty-eight themes into four; this level
returned a list, because nothing asked it for anything else. What these tests hold is the
validation rather than the writing: the tier itself is the model's, and Python's whole job is that
every live theme is accounted for and every id printed can be opened.
"""
from __future__ import annotations

import json

import pytest

from app import store

synth = pytest.importorskip("app.engine.synth")


@pytest.fixture
def corpus(conn, project, grande, quote):
    """Two open themes with a real claim each and an account over it — enough for the corpus
    summary to have themes to place and ids to cite."""
    store.save_summary(conn, "material", grande, "orientation", "A recorded interview.")
    store.save_summary(conn, "material", grande, "reading", "What the reading found here.")
    themes = {}
    for i, (name, gist) in enumerate((("Handover", "how a shift hands over"),
                                      ("Rostering", "how shifts are assigned"))):
        tid = store.save_theme(conn, project, tid=None, name=name, gist=gist, code_ids=[])
        sid, text = quote(grande, at=40 + i * 20)
        store.save_moments(conn, grande, tid, [{"claim": f"{name}: what was said",
                                                "anchor": " ".join(text.split()[:8]), "sid": sid}])
        store.save_summary(conn, "theme", tid, "reading", f"What {name} amounts to.")
        themes[name] = tid
    return {"pid": project, "mid": grande, "themes": themes,
            "ids": [m["id"] for m in store.moments(conn, grande)]}


def _tier(corpus, **over):
    """One overarching entry with every field filled, so a test only says what it is about."""
    a, b = corpus["themes"]["Handover"], corpus["themes"]["Rostering"]
    mo = corpus["ids"]
    return {"name": "What a shift is answerable for",
            "gathers": [a, b],
            "organising_idea": "Both name a point at which the ward is accountable.",
            "boundary": "This is the handing over; the nearest other is who is on the roster.",
            "exceptions": f"One claim describes a shift with no record kept [{mo[1]}].",
            "argument": f"The claims describe a handover [{mo[0]}] and a roster [{mo[1]}].",
            **over}


def _stored(conn, pid) -> dict:
    return json.loads(store.get_summary(conn, "project", pid, "overarching")["text"])


def _thread_call(conn, pid, mid, tid, model, **answer):
    """One line rewritten, which is one THREAD call and the check of what it kept."""
    model.queue({"moments": [], **answer})
    if answer.get("moments"):
        model.queue({"verdicts": []})
    return synth.doc(conn, mid, only_theme=tid)


# ---- the tier ------------------------------------------------------------------------------

def test_the_tier_is_stored_beside_the_summary_in_the_shape_the_page_reads(corpus, conn, model):
    """One row, one stage, one shape. Another step renders it, so the shape is the contract."""
    model.queue({"summary": f"Both recur [{corpus['ids'][0]}].",
                 "overarching": [_tier(corpus)],
                 "ungathered": [],
                 "interpretation": "This may mean the ward keeps track of itself."})
    out = synth.project(conn, corpus["pid"])
    stored = _stored(conn, corpus["pid"])
    assert stored == out["overarching"]
    assert set(stored) == {"overarching", "ungathered"}
    one = stored["overarching"][0]
    assert set(one) == {"name", "gathers", "organising_idea", "boundary", "exceptions", "argument"}
    assert one["gathers"] == [corpus["themes"]["Handover"], corpus["themes"]["Rostering"]]
    assert stored["ungathered"] == []
    # and the two movements that were there before it are still their own rows
    assert store.get_summary(conn, "project", corpus["pid"], "reading")["text"] == out["summary"]
    assert store.get_summary(conn, "project", corpus["pid"], "interpretation")["text"] \
        == out["interpretation"]


def test_a_theme_the_summary_placed_nowhere_is_ungathered_with_that_as_its_reason(corpus, conn,
                                                                                  model):
    """A theme missing from both lists reads on the page as a theme the analysis had nothing to
    say about. What happened is that the summary did not get to it, and those are opposite
    findings."""
    a, b = corpus["themes"]["Handover"], corpus["themes"]["Rostering"]
    model.queue({"summary": "Handover recurs.",
                 "overarching": [_tier(corpus, gathers=[a])],
                 "ungathered": []})
    out = synth.project(conn, corpus["pid"])
    assert out["overarching"]["ungathered"] == [{"id": b, "why": "not placed by the summary"}]


def test_a_theme_id_no_theme_has_is_dropped_and_the_run_says_so(corpus, conn, model):
    """A tier that gathers a theme which does not exist gathers nothing, and an id printed on the
    page sends the researcher looking for a theme they will not find."""
    a, b = corpus["themes"]["Handover"], corpus["themes"]["Rostering"]
    model.queue({"summary": "Handover recurs.",
                 "overarching": [_tier(corpus, gathers=[a, "t-does-not-exist"])],
                 "ungathered": [{"id": b, "why": "its own axis"},
                                {"id": "t-nor-this-one", "why": "invented"}]})
    out = synth.project(conn, corpus["pid"])
    assert out["overarching"]["overarching"][0]["gathers"] == [a]
    assert [u["id"] for u in out["overarching"]["ungathered"]] == [b]
    said = " ".join(out["dropped"])
    assert "t-does-not-exist" in said and "t-nor-this-one" in said


def test_a_citation_to_a_claim_that_is_not_live_is_stripped_from_the_argument(corpus, conn,
                                                                              model):
    """The same law the summary is held to: a claim the researcher cannot open is a claim they
    must take on trust."""
    mo = corpus["ids"][0]
    model.queue({"summary": "Both recur.",
                 "overarching": [_tier(corpus,
                                       argument=f"Both are described [{mo}, mo-ghost].",
                                       exceptions="Nothing else, except this [mo-also-ghost].")],
                 "ungathered": []})
    out = synth.project(conn, corpus["pid"])
    one = out["overarching"]["overarching"][0]
    assert one["argument"] == f"Both are described [{mo}]."
    assert "mo-also-ghost" not in one["exceptions"]
    assert any("mo-ghost" in n and "mo-also-ghost" in n for n in out["dropped"]), \
        "one note about missing ids, not one per movement"


def test_a_tier_that_came_back_empty_is_still_written_over_the_one_before_it(corpus, conn, model):
    """The reason `interpretation` is always written, applied here: a tier left standing from an
    earlier run gathers a theme set that has since moved."""
    model.queue({"summary": "Both recur.", "overarching": [_tier(corpus)], "ungathered": []})
    synth.project(conn, corpus["pid"])
    model.queue({"summary": "Both recur."})
    synth.project(conn, corpus["pid"])
    stored = _stored(conn, corpus["pid"])
    assert stored["overarching"] == [], "nothing was invented to fill the tier"
    assert sorted(u["id"] for u in stored["ungathered"]) == sorted(corpus["themes"].values())


def test_a_candidate_is_named_in_the_prompt_and_may_be_gathered(corpus, conn, model, quote):
    """A candidate's claims already reached this level; the candidate did not, so `gathers` could
    only ever name the open themes — and a corpus early in its reading has none of those."""
    cand = store.save_theme(conn, corpus["pid"], tid=None, name="Paperwork",
                            gist="what the ward writes down", code_ids=[])
    store.set_hold(conn, cand, "candidate")
    sid, text = quote(corpus["mid"], at=100)
    store.save_moments(conn, corpus["mid"], cand, [{"claim": "the form is filed",
                                                    "anchor": " ".join(text.split()[:8]),
                                                    "sid": sid}])
    model.queue({"summary": "Both recur.",
                 "overarching": [_tier(corpus, gathers=[corpus["themes"]["Handover"], cand])],
                 "ungathered": [{"id": corpus["themes"]["Rostering"], "why": "its own axis"}]})
    out = synth.project(conn, corpus["pid"])
    shown = model.shown("project")
    assert cand in shown and "what the ward writes down" in shown
    assert cand in out["overarching"]["overarching"][0]["gathers"]


# ---- the prose rules -----------------------------------------------------------------------

def test_the_style_block_reaches_the_calls_that_write_prose(corpus, conn, model, quote):
    model.queue({"moments": [], "summary": ""})
    model.queue({"summary": "", "questions": "", "people": []}, {"verdicts": []})
    synth.doc(conn, corpus["mid"], only_theme=corpus["themes"]["Handover"])
    model.queue({"summary": "Both recur."})
    synth.project(conn, corpus["pid"])
    for label in ("thread", "project"):
        assert "HOW TO WRITE" in model.shown(label), f"{label} was shown no prose rules"
        assert "Subject: a person, a group, a material, or the claims" in model.shown(label)


def test_what_the_counter_found_is_a_note_on_the_run(corpus, conn, model):
    """`prose.py` never rejects an answer. What it does is put a number where the researcher
    reading the run row will see it."""
    model.queue({"summary": "The corpus shows a pattern, not an exception.",
                 "overarching": [], "ungathered": []})
    out = synth.project(conn, corpus["pid"])
    assert any(n.startswith("style: ") for n in out["dropped"])


# ---- fit -----------------------------------------------------------------------------------

def test_a_line_that_sits_at_the_edge_of_its_definition_leaves_a_note(corpus, conn, model, quote):
    """The definition names a shift; this material carries the theme through an organisation. The
    note goes beside the theme and nothing about the definition changes."""
    tid, mid = corpus["themes"]["Handover"], corpus["mid"]
    sid, text = quote(mid, at=120)
    out = _thread_call(conn, corpus["pid"], mid, tid, model,
                       moments=[{"claim": "the agency hands over by fax",
                                 "anchor": " ".join(text.split()[:8]), "sid": sid}],
                       summary="One handover is described.",
                       fit="the case here is an agency, not a shift; the definition names shifts")
    notes = store.theme_notes(conn, tid)
    assert [n["kind"] for n in notes] == ["fit"]
    assert notes[0]["material_id"] == mid
    assert notes[0]["text"].startswith("the case here is an agency")
    assert out["threads"], "the line itself is unaffected"


def test_a_fit_on_a_line_that_came_back_empty_is_not_written(corpus, conn, model):
    """There is no line for it to be a note about. Filed anyway, it reads on the theme page as a
    note about a material this theme holds in."""
    tid = corpus["themes"]["Handover"]
    _thread_call(conn, corpus["pid"], corpus["mid"], tid, model,
                 summary="", fit="the case here is an agency, not a shift")
    assert store.theme_notes(conn, tid) == []


def test_a_fit_note_is_cut_to_the_note_it_is_meant_to_be(corpus, conn, model, quote):
    """Twenty-five words. Longer than that is a second account of the material, filed where a
    researcher is looking for one line."""
    tid, mid = corpus["themes"]["Handover"], corpus["mid"]
    sid, text = quote(mid, at=120)
    _thread_call(conn, corpus["pid"], mid, tid, model,
                 moments=[{"claim": "the agency hands over by fax",
                           "anchor": " ".join(text.split()[:8]), "sid": sid}],
                 summary="One handover is described.",
                 fit=" ".join(["word"] * 60))
    assert len(store.theme_notes(conn, tid)[0]["text"].split()) <= synth.FIT_WORDS + 1
