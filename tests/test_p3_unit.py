"""P3's own checks: the parts of synth/check the contract tests do not walk.

Chunking never fires on a seed transcript, `only_theme` has no contract test, and the citation
maths (a number back to a sentence id, a bracket back to a moment id) is where a quiet mistake
would look exactly like a model being vague.
"""
from __future__ import annotations

import pytest

from app import store

check = pytest.importorskip("app.engine.check")
synth = pytest.importorskip("app.engine.synth")


@pytest.fixture
def ready(conn, project, grande):
    store.save_frame(conn, grande, kind="interview", display="turns", title="Grande",
                     speakers=[{"label": "GRANDE", "name": "M. Grande", "role": "participant"}],
                     segments=[])
    store.save_summary(conn, "material", grande, "orientation", "A 1978 oral history.")
    return {"pid": project, "mid": grande,
            "a": store.save_theme(conn, project, tid=None, name="Work", gist="a living",
                                  code_ids=[]),
            "b": store.save_theme(conn, project, tid=None, name="Leaving", gist="the crossing",
                                  code_ids=[])}


def _thread(quote, mid, tid, n=None, at=40):
    n = synth.MIN_MOMENTS + 1 if n is None else n
    return {"theme_id": tid,
            "moments": [{"claim": f"claim {i}",
                         "anchor": " ".join(quote(mid, at=at + i * 9)[1].split()[:8]),
                         "sid": synth.sid_num(quote(mid, at=at + i * 9)[0])} for i in range(n)]}


def test_a_citation_reads_back_from_the_number_the_material_was_printed_under(conn, ready):
    sents = store.sentences(conn, ready["mid"])
    nums = synth.numbers(sents)
    sid = sents[40][0]
    assert synth.cited(synth.sid_num(sid), nums) == sid      # what the layout prints
    assert synth.cited(sid, nums) == sid                     # the id itself, if the model echoes
    assert synth.cited(40, nums) == sid                      # a bare integer
    assert synth.cited("S9999", nums) == "S9999"             # nonsense passes through to the law


def test_the_layout_prints_every_passage_under_its_own_number(conn, ready):
    laid = synth.layout(conn, ready["mid"])
    for sid, text in store.sentences(conn, ready["mid"])[:20]:
        assert f"{synth.sid_num(sid)}  {text}" in laid


def test_a_thread_is_capped(ready, conn, model, quote):
    model.queue({"summary": "s", "threads": [_thread(quote, ready["mid"], ready["a"], synth.MAX_MOMENTS + 4)],
                 "brief": "b", "people": []})
    synth.doc(conn, ready["mid"])
    assert len(store.thread(conn, ready["mid"], ready["a"])) == synth.MAX_MOMENTS


def test_one_theme_rerun_touches_that_thread_and_nothing_else(ready, conn, model, quote):
    model.queue({"summary": "the whole reading", "brief": "the first brief", "people": [],
                 "threads": [_thread(quote, ready["mid"], ready["a"]),
                             _thread(quote, ready["mid"], ready["b"], at=90)]})
    synth.doc(conn, ready["mid"])
    before = [m["claim"] for m in store.thread(conn, ready["mid"], ready["b"])]

    model.queue({"summary": "SHOULD NOT BE SAVED", "brief": "SHOULD NOT BE SAVED", "people": [],
                 "threads": [{"theme_id": ready["a"],
                              "moments": _thread(quote, ready["mid"], ready["a"], synth.MIN_MOMENTS,
                                                 at=150)["moments"]},
                             _thread(quote, ready["mid"], ready["b"], at=200)]})
    synth.doc(conn, ready["mid"], only_theme=ready["a"])

    assert len(store.thread(conn, ready["mid"], ready["a"])) == synth.MIN_MOMENTS
    assert [m["claim"] for m in store.thread(conn, ready["mid"], ready["b"])] == before
    assert store.get_summary(conn, "material", ready["mid"], "reading")["text"] \
        == "the whole reading"
    assert store.project(conn, ready["pid"])["brief"] == "the first brief"


def test_feedback_on_another_thread_stays_out_of_a_one_theme_rerun(ready, conn, model, quote):
    store.add_feedback(conn, ready["pid"], "thread", f'{ready["mid"]}:{ready["a"]}', "note",
                       "Work is really about the stall.")
    store.add_feedback(conn, ready["pid"], "thread", f'{ready["mid"]}:{ready["b"]}', "note",
                       "Leaving is a different story.")
    model.queue({"summary": "s", "brief": "b", "people": [],
                 "threads": [_thread(quote, ready["mid"], ready["a"])]})
    synth.doc(conn, ready["mid"], only_theme=ready["a"])
    shown = model.shown()
    assert "Work is really about the stall." in shown
    assert "Leaving is a different story." not in shown


def test_a_bracket_keeps_the_moment_ids_that_exist_and_loses_the_ones_that_do_not(ready, conn,
                                                                                 model, quote):
    model.queue({"summary": "s", "threads": [_thread(quote, ready["mid"], ready["a"])],
                 "brief": "b", "people": []})
    synth.doc(conn, ready["mid"])
    live = [m["id"] for m in store.moments(conn, ready["mid"])]
    model.queue({"summary": f"Both at once [{live[0]}, mo-ghost] and alone [mo-ghost].",
                 "theme_gists": []})
    out = synth.project(conn, ready["pid"])
    assert out["summary"] == f"Both at once [{live[0]}] and alone."
    assert out["dropped"]


def test_a_project_check_searches_every_material_and_counts_them_all(conn, project, grande,
                                                                    rodwin, model):
    model.queue({"found": []}, {"found": []})
    out = check.run(conn, project, "project", project, "Is religion mentioned?")
    assert out["searched_n"] == len(store.uncited(conn, grande)) + len(store.uncited(conn, rodwin))
    assert out["verdict"] == "not found"
    assert len(model.calls) == 2, "one call per material, and no material left unsearched"


def test_long_material_is_chunked_and_nothing_is_lost():
    passages = [(f"S{i:03d}", "x" * 100) for i in range(100)]
    got = check.chunks(passages, budget=1000)
    assert len(got) == 10
    assert [p for c in got for p in c] == passages
