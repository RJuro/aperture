"""P3 — synthesis and checking. `app/engine/synth.py`, `app/engine/check.py`, and the prompts
`thread.md`, `doc.md`, `project.md`, `check.md`.

    synth.doc(conn, mid, *, only_theme=None) -> {"summary","threads","anchors","dropped"}
        one `thread` call per live theme (in live_themes order, in waves of `synth.WAVE` side
        by side), then one `doc` call for the summary — unless only_theme, which is one `thread`
        call and nothing else
    synth.project(conn, pid) -> {"summary","interpretation","dropped"}   one `project` call over
        the accounts, stored as two rows: what the corpus shows, and what it may mean
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


def _moments(quote, mid, n=5, at=40):
    return [{"claim": f"claim {i}", "anchor": " ".join(quote(mid, at=at + i * 9)[1].split()[:8]),
             "sid": quote(mid, at=at + i * 9)[0]} for i in range(n)]


def queue_doc(model, conn, pid, moments_by_theme, summary="what the reading found",
              questions="what remains open?", people=None):
    """The answers a full DOC needs, in the order it asks: one thread per live theme, the check
    of every claim against its passage, the summary, then the check of that summary against the
    claims. A test that forgets the order gets 'unexpected model call', which is the point."""
    for t in store.live_themes(conn, pid):
        model.queue({"moments": moments_by_theme.get(t["id"], [])})
    model.queue({"verdicts": []})
    model.queue({"summary": summary, "questions": questions, "people": people or []})
    model.queue({"verdicts": []})           # and the summary against the claims


def test_a_quote_that_is_not_in_the_material_drops_its_moment(ready, conn, model, quote):
    ms = _moments(quote, ready["mid"], 5) + [
        {"claim": "invented", "anchor": "a phrase that is simply not present", "sid": "S050"}]
    queue_doc(model, conn, ready["pid"], {ready["tid"]: ms})
    out = synth.doc(conn, ready["mid"])
    claims = [m["claim"] for m in store.thread(conn, ready["mid"], ready["tid"])]
    assert "invented" not in claims and len(claims) == 5
    assert out["anchors"]["unfound"] == 1


def test_a_real_quote_with_the_wrong_id_is_repaired_not_dropped(ready, conn, model, quote):
    """The quote is authoritative, the citation is not. A mis-cited true claim looked false to
    two readers in round 2 — this is the fix, and it must not silently become a drop."""
    ms = _moments(quote, ready["mid"], 5)
    right_sid = ms[0]["sid"]
    ms[0]["sid"] = "S002"
    queue_doc(model, conn, ready["pid"], {ready["tid"]: ms})
    out = synth.doc(conn, ready["mid"])
    assert out["anchors"]["rebound"] == 1
    assert right_sid in {m["sid"] for m in store.thread(conn, ready["mid"], ready["tid"])}


def test_a_sparse_line_is_kept_and_only_an_empty_one_is_thin(ready, conn, model, quote):
    """The four-claim floor was a deletion rule and it took one to three sound observations away
    as a group. A sparse line is kept — the page reads `sparse` off the count — and only a
    completed answer that holds nothing at all leaves the theme with no line here."""
    queue_doc(model, conn, ready["pid"], {ready["tid"]: _moments(quote, ready["mid"], 3)})
    synth.doc(conn, ready["mid"])
    kept = store.thread(conn, ready["mid"], ready["tid"])
    assert len(kept) == 3 < synth.MIN_MOMENTS, "kept, and short enough for the page to mark it"
    assert store.followed(conn, ready["pid"])[(ready["tid"], ready["mid"])] == "line"

    queue_doc(model, conn, ready["pid"], {})            # the same line, now holding nothing
    synth.doc(conn, ready["mid"])
    assert store.thread(conn, ready["mid"], ready["tid"]) == []
    assert store.followed(conn, ready["pid"])[(ready["tid"], ready["mid"])] == "thin"


def test_moments_are_stored_in_material_order_whatever_order_the_model_gave(ready, conn, model,
                                                                           quote):
    ms = _moments(quote, ready["mid"], 5)
    ms.reverse()
    queue_doc(model, conn, ready["pid"], {ready["tid"]: ms})
    synth.doc(conn, ready["mid"])
    pos = store.sid_position(conn, ready["mid"])
    got = [pos[m["sid"]] for m in store.thread(conn, ready["mid"], ready["tid"])]
    assert got == sorted(got)


def test_each_line_is_its_own_call_and_the_summary_comes_after_the_lines(ready, conn, project,
                                                                           model, quote):
    """One call for six lines plus a summary is how lines come out thin — the model rations its
    attention. Each line gets a call; the summary is written over lines that exist."""
    t2 = store.save_theme(conn, project, tid=None, name="Leaving", gist="the crossing",
                          code_ids=[])
    queue_doc(model, conn, ready["pid"], {ready["tid"]: _moments(quote, ready["mid"], 5),
                                          t2: _moments(quote, ready["mid"], 4, at=120)})
    synth.doc(conn, ready["mid"])
    labels = [c["label"] for c in model.calls]
    assert labels == ["thread", "thread", "verify", "doc", "verify_summary"]
    shown_to_summary = model.calls[-1]["user"]
    assert "claim 0" in shown_to_summary, "the summary must see the lines it introduces"


def claimed_block(user: str) -> str:
    """The `{{claimed}}` slot out of a thread prompt — what that line was told other themes have
    already claimed in this material."""
    head = "the other theme's name, and its claim:\n\n"
    rest = user.split(head, 1)[1]
    return rest.split("\n\nWHAT THE RESEARCHER", 1)[0].strip()


def test_a_line_is_shown_what_another_theme_has_already_claimed_here(ready, conn, project, model,
                                                                     quote):
    """The same passages came back under three and four themes, twice with opposite valence. A
    line that cannot see the other reading cannot tell it is repeating one under a second name.

    Lines are written in waves of `synth.WAVE` now, so the rule is per wave: a wave sees every
    earlier wave's claims and not its own. Four themes, three in the first wave and one in the
    second — the first three are shown nothing, the fourth is shown all three.
    """
    for name, gist in (("Arriving", "the other end"), ("Crossing", "the water"),
                       ("Leaving", "the crossing")):
        store.save_theme(conn, project, tid=None, name=name, gist=gist, code_ids=[])
    order = [t["id"] for t in store.live_themes(conn, ready["pid"])]   # by name: Work is last
    assert len(order) == synth.WAVE + 1
    by_theme = {tid: _moments(quote, ready["mid"], 5, at=40 + i * 60)
                for i, tid in enumerate(order)}
    queue_doc(model, conn, ready["pid"], by_theme)
    synth.doc(conn, ready["mid"])

    shown = [claimed_block(c["user"]) for c in model.calls if c["label"] == "thread"]
    assert shown[:synth.WAVE] == ["None yet."] * synth.WAVE, "the first wave had nothing to see"
    # The whole of the first wave, whichever answer each of its lines happened to be given.
    for t in store.live_themes(conn, ready["pid"])[:synth.WAVE]:
        assert f'— {t["name"]} —' in shown[-1]
    for m in [m for tid in order[:synth.WAVE] for m in by_theme[tid]]:
        assert m["sid"] in shown[-1] and m["claim"] in shown[-1]


def test_three_lines_are_written_at_once_and_the_reading_is_the_one_a_sequence_writes(
        ready, conn, project, quote, monkeypatch):
    """Six themes, two waves. The barrier is the assertion that three calls are genuinely in
    flight together: it releases only when three lines are inside it at the same moment, and it
    is met twice. The distinct `claimed` blocks are the other half — two of them, one per wave."""
    import threading
    import time
    for name in ("Arriving", "Crossing", "Leaving", "Money", "Returning"):
        store.save_theme(conn, project, tid=None, name=name, gist=f"about {name}", code_ids=[])
    order = [t["id"] for t in store.live_themes(conn, ready["pid"])]
    assert len(order) == 6
    answers = {tid: _moments(quote, ready["mid"], 5, at=40 + i * 55)
               for i, tid in enumerate(order)}

    spans, seen, lock = [], [], threading.Lock()
    at_once = threading.Barrier(synth.WAVE, timeout=5)

    def fake(system, user, *, label="", timeout=None):
        """Answers from the theme in front of it, so a wave and a sequence are shown the same
        material and answer it the same way whatever order the calls arrive in."""
        if label != "thread":
            return ({"verdicts": []} if label.startswith("verify")
                    else {"summary": "what the reading found", "questions": "q", "people": []})
        tid = next(t for t in order if f"{t}  " in user)
        started = time.monotonic()
        if at_once is not None:
            at_once.wait()
        with lock:
            seen.append(claimed_block(user))
            spans.append((started, time.monotonic()))
        return {"moments": answers[tid]}

    monkeypatch.setattr(synth.llm, "chat_json", fake)
    synth.doc(conn, ready["mid"])
    in_waves = _reading(conn, ready["mid"])

    assert len(seen) == 6
    assert len(set(seen)) == 2, "one claimed block per wave, not one per line"
    assert seen.count("None yet.") == synth.WAVE
    overlap = max(sum(1 for b in spans if b[0] < a[1] and a[0] < b[1]) for a in spans)
    assert overlap == synth.WAVE, f"{overlap} calls overlapped, expected {synth.WAVE}"

    # The same answers, one line at a time: the chain gets faster and the reading does not move.
    at_once, seen[:] = None, []
    monkeypatch.setattr(synth, "WAVE", 1)
    synth.doc(conn, ready["mid"])
    assert len(seen) == 6 and len(set(seen)) == 6, "a sequence really is one line at a time"
    assert _reading(conn, ready["mid"]) == in_waves


def _reading(conn, mid: str) -> list[tuple]:
    """Every live moment in this material, by theme name — what two runs must agree on."""
    return sorted((r["name"], r["sid"], r["position"], r["claim"], r["anchor"]) for r in
                  conn.execute("SELECT m.*, t.name FROM moment m JOIN theme t ON t.id=m.theme_id "
                               "WHERE m.material_id=? AND m.status='live'", (mid,)))


def test_the_orientation_and_the_feedback_are_both_shown_verbatim(ready, conn, model, quote):
    store.add_feedback(conn, ready["pid"], "material_summary", ready["mid"], "note",
                       "He never says why they chose Trieste.")
    queue_doc(model, conn, ready["pid"], {ready["tid"]: _moments(quote, ready["mid"])})
    synth.doc(conn, ready["mid"])
    shown = model.shown("doc")
    assert "A 1978 oral history." in shown
    assert "He never says why they chose Trieste." in shown


def test_no_prose_the_system_wrote_about_the_corpus_reaches_a_line_or_a_summary(ready, conn,
                                                                                 model, quote):
    """Law 5. The brief used to reach READ and DOC as 'what this corpus is like' and became a
    finding carried forward as an instruction. It reaches nothing here now."""
    store.set_brief(conn, ready["pid"], "THE CORPUS SHOWS women's labour is treated as ordinary")
    queue_doc(model, conn, ready["pid"], {ready["tid"]: _moments(quote, ready["mid"])})
    synth.doc(conn, ready["mid"])
    assert "THE CORPUS SHOWS" not in model.shown()


def test_the_summary_the_questions_and_the_people_are_written(ready, conn, model, quote):
    queue_doc(model, conn, ready["pid"], {ready["tid"]: _moments(quote, ready["mid"])},
              summary="what the reading found", questions="why Trieste? what became of the brother?",
              people=[{"name": "M. Grande", "aliases": ["Grande"], "role": "participant"}])
    synth.doc(conn, ready["mid"])
    assert store.get_summary(conn, "material", ready["mid"], "reading")["text"] \
        == "what the reading found"
    assert store.get_summary(conn, "material", ready["mid"], "orientation") is not None
    assert store.get_summary(conn, "material", ready["mid"], "questions")["text"] \
        == "why Trieste? what became of the brother?"
    assert [p["name"] for p in store.people(conn, ready["mid"])] == ["M. Grande"]


def test_a_one_line_rerun_makes_one_call_and_leaves_the_summary_alone(ready, conn, model, quote):
    queue_doc(model, conn, ready["pid"], {ready["tid"]: _moments(quote, ready["mid"])},
              summary="the whole reading", questions="q1")
    synth.doc(conn, ready["mid"])
    model.queue({"moments": _moments(quote, ready["mid"], 5, at=150)}, {"verdicts": []})
    out = synth.doc(conn, ready["mid"], only_theme=ready["tid"])
    assert [c["label"] for c in model.calls][-2:] == ["thread", "verify"]
    assert len(out["threads"]) == 1
    assert store.get_summary(conn, "material", ready["mid"], "reading")["text"] == "the whole reading"
    assert store.get_summary(conn, "material", ready["mid"], "questions")["text"] == "q1"


def test_the_project_level_reads_the_accounts_and_may_not_introduce_a_quote(ready, conn, model,
                                                                             quote):
    queue_doc(model, conn, ready["pid"], {ready["tid"]: _moments(quote, ready["mid"])})
    synth.doc(conn, ready["mid"])
    store.save_summary(conn, "theme", ready["tid"], "reading", "ACCOUNT TEXT about work")
    live = [m["id"] for m in store.moments(conn, ready["mid"])]
    model.queue({"summary": f"Work runs through it [{live[0]}] and beyond [mo-does-not-exist]."})
    out = synth.project(conn, ready["pid"])
    assert "ACCOUNT TEXT about work" in model.shown("project"), "project reads the accounts"
    assert "claim 0" not in model.shown("project"), "…and not every claim in every material"
    text = store.get_summary(conn, "project", ready["pid"])["text"]
    assert live[0] in text and "mo-does-not-exist" not in text
    assert out["dropped"]


def test_what_the_corpus_shows_and_what_it_may_mean_are_two_rows(ready, conn, model, quote):
    """A reader must be able to cite the first and argue with the second, so they are stored
    apart and the plain call still hands back the grounded one."""
    queue_doc(model, conn, ready["pid"], {ready["tid"]: _moments(quote, ready["mid"])})
    synth.doc(conn, ready["mid"])
    live = [m["id"] for m in store.moments(conn, ready["mid"])]
    model.queue({"summary": f"Work recurs [{live[0]}].",
                 "interpretation": f"Taken together, this suggests a wage logic "
                                   f"[{live[0]}, mo-does-not-exist]."})
    out = synth.project(conn, ready["pid"])
    pid = ready["pid"]
    assert store.get_summary(conn, "project", pid, "reading")["text"] == out["summary"]
    assert store.get_summary(conn, "project", pid, "interpretation")["text"] == out["interpretation"]
    assert store.get_summary(conn, "project", pid)["stage"] == "reading"
    assert "Taken together" in out["interpretation"]
    assert "mo-does-not-exist" not in out["interpretation"], "a dangling citation survived"
    assert out["dropped"]
    shown = model.shown("project")
    assert str(synth.PROJECT_WORDS) in shown and str(synth.INTERPRETATION_WORDS) in shown


def test_an_interpretation_is_never_left_standing_over_a_newer_summary(ready, conn, model, quote):
    queue_doc(model, conn, ready["pid"], {ready["tid"]: _moments(quote, ready["mid"])})
    synth.doc(conn, ready["mid"])
    model.queue({"summary": "first", "interpretation": "an early reading of it"})
    synth.project(conn, ready["pid"])
    model.queue({"summary": "second"})
    synth.project(conn, ready["pid"])
    assert store.get_summary(conn, "project", ready["pid"], "interpretation")["text"] == ""


def test_the_project_level_leaves_a_themes_definition_alone(ready, conn, model, quote):
    """Law 5: a gist defines, an account concludes. The project step used to sharpen gists into
    findings about the materials in front of it; now it writes only its own summary."""
    queue_doc(model, conn, ready["pid"], {ready["tid"]: _moments(quote, ready["mid"])})
    synth.doc(conn, ready["mid"])
    model.queue({"summary": "s", "theme_gists": [{"theme_id": ready["tid"], "gist": "SHOULD NOT LAND"}]})
    synth.project(conn, ready["pid"])
    assert conn.execute("SELECT gist FROM theme WHERE id=?", (ready["tid"],)).fetchone()[0] == "a living"


def test_the_unused_scope_searches_only_what_no_moment_rests_on(ready, conn, model, quote):
    """The residual search, now asked for by name. It is a different question from the default —
    what is in here the reading has not used — and it says so on the page and in the record."""
    queue_doc(model, conn, ready["pid"], {ready["tid"]: _moments(quote, ready["mid"])})
    synth.doc(conn, ready["mid"])
    uncited = len(store.uncited(conn, ready["mid"]))
    model.queue({"found": []})
    out = check.run(conn, ready["pid"], "material", ready["mid"], "Is religion mentioned?",
                    "unused")
    assert out["searched_n"] == uncited
    assert out["verdict"] == "not found"
    cited = store.cited_sids(conn, ready["mid"])
    shown_to_check = model.shown("check")
    assert not any(sid in shown_to_check for sid in cited), "a check re-read a cited passage"
    assert "S0" in model.shown("thread"), "a line must be shown sentence ids — it has to cite them"


def test_the_verdict_is_pythons_and_the_model_cannot_talk_its_way_to_found(ready, conn, model):
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
