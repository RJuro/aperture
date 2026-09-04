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
    """One thread call's answer. `tid` is kept for the caller's bookkeeping; the answer itself
    carries only moments, because a thread call is about exactly one theme."""
    n = synth.MIN_MOMENTS + 1 if n is None else n
    return {"moments": [{"claim": f"claim {i}",
                         "anchor": " ".join(quote(mid, at=at + i * 9)[1].split()[:8]),
                         "sid": synth.sid_num(quote(mid, at=at + i * 9)[0])} for i in range(n)]}


def _full_doc(model, conn, pid, by_tid, summary="s", questions="q", verdicts=None):
    for t in store.live_themes(conn, pid):
        model.queue(by_tid.get(t["id"], {"moments": []}))
    model.queue({"verdicts": verdicts or []})
    model.queue({"summary": summary, "questions": questions, "people": []})


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
    _full_doc(model, conn, ready["pid"],
              {ready["a"]: _thread(quote, ready["mid"], ready["a"], synth.MAX_MOMENTS + 4)})
    synth.doc(conn, ready["mid"])
    assert len(store.thread(conn, ready["mid"], ready["a"])) == synth.MAX_MOMENTS


def test_one_theme_rerun_touches_that_thread_and_nothing_else(ready, conn, model, quote):
    _full_doc(model, conn, ready["pid"], {ready["a"]: _thread(quote, ready["mid"], ready["a"]),
                                          ready["b"]: _thread(quote, ready["mid"], ready["b"], at=90)},
              summary="the whole reading", questions="the first questions")
    synth.doc(conn, ready["mid"])
    before = [m["claim"] for m in store.thread(conn, ready["mid"], ready["b"])]

    model.queue(_thread(quote, ready["mid"], ready["a"], synth.MIN_MOMENTS, at=150),
                {"verdicts": []})
    synth.doc(conn, ready["mid"], only_theme=ready["a"])

    assert len(store.thread(conn, ready["mid"], ready["a"])) == synth.MIN_MOMENTS
    assert [m["claim"] for m in store.thread(conn, ready["mid"], ready["b"])] == before
    assert store.get_summary(conn, "material", ready["mid"], "reading")["text"] \
        == "the whole reading"
    assert store.project(conn, ready["pid"])["brief"] == "the first questions"


def test_feedback_on_another_thread_stays_out_of_a_one_theme_rerun(ready, conn, model, quote):
    store.add_feedback(conn, ready["pid"], "thread", f'{ready["mid"]}:{ready["a"]}', "note",
                       "Work is really about the stall.")
    store.add_feedback(conn, ready["pid"], "thread", f'{ready["mid"]}:{ready["b"]}', "note",
                       "Leaving is a different story.")
    model.queue(_thread(quote, ready["mid"], ready["a"]), {"verdicts": []})
    synth.doc(conn, ready["mid"], only_theme=ready["a"])
    shown = model.shown()
    assert "Work is really about the stall." in shown
    assert "Leaving is a different story." not in shown


def test_a_bracket_keeps_the_moment_ids_that_exist_and_loses_the_ones_that_do_not(ready, conn,
                                                                                 model, quote):
    _full_doc(model, conn, ready["pid"], {ready["a"]: _thread(quote, ready["mid"], ready["a"])})
    synth.doc(conn, ready["mid"])
    live = [m["id"] for m in store.moments(conn, ready["mid"])]
    model.queue({"summary": f"Both at once [{live[0]}, mo-ghost] and alone [mo-ghost]."})
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


def test_an_over_long_text_is_cut_back_to_a_whole_sentence():
    """The summary is the first thing a researcher reads. Cutting it at the word cap ended one
    real run with "What is thin: ... What …" — mid-clause, in the sentence about to say what the
    reading had missed."""
    text = ("One sentence here. Two sentences here. Three sentences here. "
            "And a fourth that runs past the cap and should not survive half-said.")
    out = synth.words(text, 14)
    assert out.endswith(".")
    assert "…" not in out
    assert out == "One sentence here. Two sentences here. Three sentences here."


def test_a_text_with_no_sentence_break_still_gets_cut_rather_than_kept_whole():
    out = synth.words("word " * 50, 10)
    assert out.endswith("…") and len(out.split()) == 11


def test_an_id_repeated_inside_one_bracket_is_kept_once():
    """`[mo1, mo1]` reads as two claims agreeing until the researcher opens them. One bracket,
    one mention of each claim; the first wins, so the order the model wrote survives."""
    text, gone = synth._strip_dangling(
        "Trade recurs [mo1, mo2, mo1] and pays [mo2, mo2].", {"mo1": 1, "mo2": 1})
    assert text == "Trade recurs [mo1, mo2] and pays [mo2]."
    assert gone == []


def test_a_repeat_and_a_dangling_id_in_one_bracket_are_both_dealt_with():
    text, gone = synth._strip_dangling("It holds [mo1, mo1, mo-gone].", {"mo1": 1})
    assert text == "It holds [mo1]."
    assert gone == ["mo-gone"]


# ---- a word in a script the material does not use ------------------------------------------

def test_a_word_in_a_script_the_material_never_uses_is_dropped_from_its_summary(ready, conn,
                                                                                 model, quote):
    """A summary of three English interviews came back with a Chinese token mid-sentence — the
    model's own vocabulary surfacing, not anything the material said."""
    _full_doc(model, conn, ready["pid"], {ready["a"]: _thread(quote, ready["mid"], ready["a"])},
              summary="Work is 工作 the condition of staying.")
    out = synth.doc(conn, ready["mid"])
    stored = store.get_summary(conn, "material", ready["mid"], "reading")["text"]
    assert stored == "Work is the condition of staying."
    assert any("工作" in d for d in out["dropped"])
    assert any(d.startswith("a word in a script the material does not use") for d in out["dropped"])


def test_a_material_written_in_cyrillic_keeps_its_cyrillic(conn, project, model):
    """The test is what the material in front of the reading uses, never a list of scripts this
    instrument approves of."""
    from app import ingest
    raw = "\n".join(["Она работала на рынке каждый день.",
                      "Отец уехал первым, в девятьсот десятом году.",
                      "Дети помогали в пекарне по утрам.",
                      "Мать говорила, что возвращаться было некуда.",
                      "Хлеб пекли до рассвета, каждое утро.",
                      "Деньги отправляли домой два раза в год."])
    mid = store.add_material(conn, project, "RU-1", raw)
    store.save_sentences(conn, mid, ingest.sentences(raw))
    store.save_frame(conn, mid, kind="document", display="plain", title="RU", speakers=[],
                     segments=[])
    tid = store.save_theme(conn, project, tid=None, name="Работа", gist="a living", code_ids=[])
    sents = store.sentences(conn, mid)
    model.queue({"moments": [{"claim": f"claim {i}", "anchor": sents[i][1], "sid": sents[i][0]}
                             for i in range(4)]})
    model.queue({"verdicts": []})
    model.queue({"summary": "Работа держит семью вместе.", "questions": "q", "people": []})
    out = synth.doc(conn, mid)
    assert store.get_summary(conn, "material", mid, "reading")["text"] \
        == "Работа держит семью вместе."
    assert not [d for d in out["dropped"] if "script" in d]
    assert tid


def test_a_quote_past_the_twelve_word_cap_is_named_in_the_exclusions(ready, conn, model, quote):
    """'3 quote(s) ran past the cap and were kept' told a researcher something had been let
    through without telling them which claim to go and look at."""
    long_sid, long_text = next((sid, t) for sid, t in store.sentences(conn, ready["mid"])
                               if len(t.split()) > 14)
    answer = _thread(quote, ready["mid"], ready["a"])
    answer["moments"][0] = {"claim": "a long one", "anchor": long_text, "sid": long_sid}
    _full_doc(model, conn, ready["pid"], {ready["a"]: answer})
    out = synth.doc(conn, ready["mid"])
    said = [d for d in out["dropped"] if "12-word cap" in d]
    assert said, out["dropped"]
    assert long_text[:60] in said[0] and "(Work)" in said[0]
