"""P3 — synthesis and checking. `app/engine/synth.py`, `app/engine/check.py`, three prompts.

    synth.doc(conn, mid, *, only_theme=None) -> {"summary","threads","anchors","dropped"}
    synth.project(conn, pid) -> {"summary","theme_gists","dropped"}
    check.run(conn, pid, scope, ref_id, question) -> {"check_id","verdict","anchors","searched_n"}

This is where the anchor law lives at runtime, so most of these tests are that law.
"""
from __future__ import annotations

import pytest

from app import store

synth = pytest.importorskip("app.engine.synth")
check = pytest.importorskip("app.engine.check")


@pytest.fixture
def ready(conn, project, grande, quote):
    store.save_frame(conn, grande, kind="interview", display="turns", title="Grande",
                     speakers=[{"label": "GRANDE", "name": "M. Grande", "role": "participant"}],
                     segments=[])
    store.save_summary(conn, "material", grande, "orientation", "A 1978 oral history.")
    tid = store.save_theme(conn, project, tid=None, name="Work", gist="a living", code_ids=[])
    return {"pid": project, "mid": grande, "tid": tid}


def _moments(quote, mid, tid, n=3, at=40):
    ms = [{"claim": f"claim {i}", "anchor": " ".join(quote(mid, at=at + i * 9)[1].split()[:8]),
           "sid": quote(mid, at=at + i * 9)[0]} for i in range(n)]
    return {"theme_id": tid, "moments": ms}


def test_a_quote_that_is_not_in_the_material_drops_its_moment(ready, conn, model, quote):
    t = _moments(quote, ready["mid"], ready["tid"], 3)
    t["moments"].append({"claim": "invented", "anchor": "a phrase that is simply not present",
                         "sid": "S050"})
    model.queue({"summary": "s", "threads": [t], "brief": "b", "people": []})
    out = synth.doc(conn, ready["mid"])
    claims = [m["claim"] for m in store.thread(conn, ready["mid"], ready["tid"])]
    assert "invented" not in claims and len(claims) == 3
    assert out["anchors"]["unfound"] == 1


def test_a_real_quote_with_the_wrong_id_is_repaired_not_dropped(ready, conn, model, quote):
    """The quote is authoritative, the citation is not. A mis-cited true claim looked false to
    two readers in round 2 — this is the fix, and it must not silently become a drop."""
    t = _moments(quote, ready["mid"], ready["tid"], 3)
    right_sid = t["moments"][0]["sid"]
    t["moments"][0]["sid"] = "S002"
    model.queue({"summary": "s", "threads": [t], "brief": "b", "people": []})
    out = synth.doc(conn, ready["mid"])
    assert out["anchors"]["rebound"] == 1
    assert right_sid in {m["sid"] for m in store.thread(conn, ready["mid"], ready["tid"])}


def test_a_thread_too_thin_to_be_a_thread_is_dropped_and_said_so(ready, conn, model, quote):
    t = _moments(quote, ready["mid"], ready["tid"], 1)
    model.queue({"summary": "s", "threads": [t], "brief": "b", "people": []})
    out = synth.doc(conn, ready["mid"])
    assert store.thread(conn, ready["mid"], ready["tid"]) == []
    assert out["dropped"], "a dropped thread must be reported, not swallowed"


def test_moments_are_stored_in_material_order_whatever_order_the_model_gave(ready, conn, model,
                                                                           quote):
    t = _moments(quote, ready["mid"], ready["tid"], 3)
    t["moments"].reverse()
    model.queue({"summary": "s", "threads": [t], "brief": "b", "people": []})
    synth.doc(conn, ready["mid"])
    pos = store.sid_position(conn, ready["mid"])
    got = [pos[m["sid"]] for m in store.thread(conn, ready["mid"], ready["tid"])]
    assert got == sorted(got)


def test_the_orientation_and_the_feedback_are_both_shown_verbatim(ready, conn, model, quote):
    store.add_feedback(conn, ready["pid"], "material_summary", ready["mid"], "note",
                       "He never says why they chose Trieste.")
    model.queue({"summary": "s", "threads": [_moments(quote, ready["mid"], ready["tid"])],
                 "brief": "b", "people": []})
    synth.doc(conn, ready["mid"])
    shown = model.shown()
    assert "A 1978 oral history." in shown
    assert "He never says why they chose Trieste." in shown


def test_the_reading_summary_and_the_brief_are_both_written(ready, conn, model, quote):
    model.queue({"summary": "what the reading found", "threads": [
        _moments(quote, ready["mid"], ready["tid"])], "brief": "next time, watch for work",
        "people": [{"name": "M. Grande", "aliases": ["Grande"], "role": "participant"}]})
    synth.doc(conn, ready["mid"])
    assert store.get_summary(conn, "material", ready["mid"], "reading")["text"] \
        == "what the reading found"
    assert store.get_summary(conn, "material", ready["mid"], "orientation") is not None
    assert store.project(conn, ready["pid"])["brief"] == "next time, watch for work"
    assert [p["name"] for p in store.people(conn, ready["mid"])] == ["M. Grande"]


def test_the_project_level_may_not_introduce_a_quote_of_its_own(ready, conn, model, quote):
    model.queue({"summary": "s", "threads": [_moments(quote, ready["mid"], ready["tid"])],
                 "brief": "b", "people": []})
    synth.doc(conn, ready["mid"])
    live = [m["id"] for m in store.moments(conn, ready["mid"])]
    model.queue({"summary": f"Work runs through it [{live[0]}] and beyond [mo-does-not-exist].",
                 "theme_gists": [{"theme_id": ready["tid"], "gist": "a living",
                                  "moment_ids": live[:1] + ["mo-nope"]}]})
    out = synth.project(conn, ready["pid"])
    text = store.get_summary(conn, "project", ready["pid"])["text"]
    assert live[0] in text
    assert "mo-does-not-exist" not in text and "mo-nope" not in str(out.get("theme_gists"))
    assert out["dropped"]


def test_a_check_searches_only_what_no_moment_rests_on(ready, conn, model, quote):
    model.queue({"summary": "s", "threads": [_moments(quote, ready["mid"], ready["tid"])],
                 "brief": "b", "people": []})
    synth.doc(conn, ready["mid"])
    uncited = len(store.uncited(conn, ready["mid"]))
    model.queue({"found": []})
    out = check.run(conn, ready["pid"], "material", ready["mid"], "Is religion mentioned?")
    assert out["searched_n"] == uncited
    assert out["verdict"] == "not found"
    cited = store.cited_sids(conn, ready["mid"])
    assert not any(sid in model.shown() for sid in cited), "a check must not re-read cited passages"


def test_the_verdict_is_pythons_and_the_model_cannot_talk_its_way_to_found(ready, conn, model):
    """Round 1's worst defect was a confident negative claim from a model that never looked. The
    inverse guard: a model that claims support without producing a findable quote is not believed."""
    model.queue({"found": [{"anchor": "a phrase that is simply not present", "sid": "S050"}],
                 "supported": True})
    out = check.run(conn, ready["pid"], "material", ready["mid"], "Is religion mentioned?")
    assert out["verdict"] == "not found"
    assert out["anchors"] == []


def test_a_found_check_carries_the_quote_that_makes_it_true(ready, conn, model, quote):
    sid, text = quote(ready["mid"], at=80)
    model.queue({"found": [{"anchor": " ".join(text.split()[:8]), "sid": sid}]})
    out = check.run(conn, ready["pid"], "material", ready["mid"], "Does he mention the crossing?")
    assert out["verdict"] == "found"
    assert out["anchors"] and out["anchors"][0]["sid"] == sid
    assert store.checks(conn, ready["pid"])[-1]["verdict"] == "found"
