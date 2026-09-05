"""P4 — which way feedback runs. `app/rerun.py` and `app/jobs.py`.

    rerun.plan(conn, feedback_id) -> [{"kind","material_id","theme_id"}]   kind in
        frame|read|themes|doc|project|check

This file is PLAN.md §1's table, executable. The rule the whole design rests on: feedback runs one
layer down and **never re-reads**. A rerun that re-ran READ would re-code the material under the
influence of the researcher's opinion, which is the failure mode the anchor law exists to prevent.
"""
from __future__ import annotations

import pytest

from app import jobs, store

rerun = pytest.importorskip("app.rerun")


def kinds(plan):
    return [p["kind"] for p in plan]


@pytest.fixture
def state(conn, analysed):
    return analysed


def _plan(conn, pid, kind, target_id, fb_kind="note", text="x"):
    fid = store.add_feedback(conn, pid, kind, target_id, fb_kind, text)
    return rerun.plan(conn, fid)


def test_doubt_about_a_claim_is_a_check_and_never_a_rerun(conn, state):
    """Doubt reaches the table as the check verb. The page offers one free-text comment per
    block and no `doubt` at all, so the row that matched one was unreachable."""
    plan = _plan(conn, state["pid"], "moment", state["moment"], "check", "I don't buy this")
    assert kinds(plan) == ["check"]


def test_a_comment_on_a_claim_runs_nothing_now(conn, state):
    assert _plan(conn, state["pid"], "moment", state["moment"], "note", "overstated") == []
    assert _plan(conn, state["pid"], "moment", state["moment"], "agree", "") == []


def test_feedback_on_a_thread_rewrites_that_line_and_everything_written_over_it(conn, state):
    """The line first, scoped to the theme the comment is about — the only run that cannot pass
    that theme over. Then the material's summary over its lines as they now stand — not every line
    again; a comment on one line once re-threaded the whole material to refresh one paragraph —
    and the accounts and corpus summary written over the claims it replaced."""
    tid = list(state["themes"].values())[0]
    plan = _plan(conn, state["pid"], "thread", f"{state['grande']}:{tid}")
    assert kinds(plan) == ["doc", "summary", "accounts", "project"]
    assert plan[0]["material_id"] == state["grande"] and plan[0]["theme_id"] == tid
    assert plan[1]["material_id"] == state["grande"] and not plan[1]["theme_id"]


def test_feedback_on_a_materials_summary_writes_that_summary_again_over_its_lines(conn, state):
    plan = _plan(conn, state["pid"], "material_summary", state["grande"])
    assert kinds(plan) == ["summary", "accounts", "project"]
    assert plan[0]["material_id"] == state["grande"] and not plan[0].get("theme_id")


def test_a_comment_on_a_theme_is_answered_at_the_theme(conn, state):
    """It used to regroup the whole codebook and re-read every material carrying the theme —
    answering a comment about one theme with work on all of them. One account now."""
    tid = list(state["themes"].values())[0]
    plan = _plan(conn, state["pid"], "theme", tid)
    assert kinds(plan) == ["account", "project"], "the summary is written from the accounts"
    assert plan[0]["theme_id"] == tid


def test_a_comment_on_the_corpus_is_answered_at_the_corpus(conn, state):
    """This planned one synthesis per material, which a scaling review measured on fifty
    materials at about seventeen hours. Then it rewrote every theme's account instead — the same
    mistake one layer up, since the words went to PROJECT alone and no account was ever shown
    them. A comment about one theme belongs on that theme."""
    plan = _plan(conn, state["pid"], "project_summary", state["pid"])
    assert kinds(plan) == ["project"]
    assert "doc" not in kinds(plan), "a comment on the corpus must not re-read every material"


def test_no_feedback_anywhere_ever_re_reads_or_re_frames(conn, state):
    """The one invariant that makes reruns cheap and safe."""
    tid = list(state["themes"].values())[0]
    targets = [("moment", state["moment"], "doubt"), ("moment", state["moment"], "agree"),
               ("thread", f"{state['grande']}:{tid}", "note"),
               ("material_summary", state["grande"], "note"), ("theme", tid, "note"),
               ("project_summary", state["pid"], "note"), ("focus", state["pid"], "note")]
    for kind, target, fb in targets:
        assert "read" not in kinds(_plan(conn, state["pid"], kind, target, fb))
        assert "frame" not in kinds(_plan(conn, state["pid"], kind, target, fb))


def test_only_a_layout_complaint_re_frames_and_it_touches_nothing_else(conn, state):
    plan = _plan(conn, state["pid"], "frame", state["grande"], "note", "these are notes")
    assert kinds(plan) == ["frame"]
    assert plan[0]["material_id"] == state["grande"]


def test_setting_a_focus_runs_nothing_and_shapes_what_comes_next(conn, state):
    assert _plan(conn, state["pid"], "focus", state["pid"]) == []


def test_every_progress_line_is_in_the_researchers_words(conn, state):
    """A running line is shown on the page verbatim, so it obeys the same vocabulary rule as any
    other app-authored sentence. These lines were written before the rule and two of them broke
    it — which is why they are checked here rather than trusted."""
    import re

    from app import context, jobs

    tid = list(state["themes"].values())[0]
    lines = []
    for kind in ("frame", "read", "themes", "doc", "project", "check"):
        line, _ = jobs.STEPS[kind]
        lines.append(jobs.line_for(conn, kind, state["grande"], None)
                     if hasattr(jobs, "line_for") else line)
    lines.append(str(jobs.STEPS["doc"][0]))
    for line in lines:
        for word in context._BANNED:
            assert not re.search(rf"\b{re.escape(word)}s?\b", str(line), re.I), \
                f"{word!r} in a progress line: {line!r}"


def test_a_planned_step_that_never_died_has_nothing_to_resume(conn, state):
    """`skip_done` is handed to DOC by the runner and is the id of an attempt a restart cut in
    half. An ordinary planned step has none and follows every theme as it always did."""
    assert jobs._resuming(conn, {"kind": "doc", "material_id": state["grande"]}) is None


def test_a_synthesis_a_restart_cut_in_half_is_resumed_rather_than_replayed(conn, state):
    """`store.requeue_job` drops only the steps that finished cleanly, so the step running now is
    a second attempt at the same step of the same job — and the first attempt's run row is how
    DOC learns which of its dozen calls it does not have to make again."""
    jid = store.enqueue_job(conn, state["pid"], [{"kind": "doc", "material_id": state["grande"]}])
    died = store.start_run(conn, state["pid"], "doc", state["grande"], "Writing", jid)
    store.finish_run(conn, died, error="interrupted: the application restarted")

    assert jobs._resuming(conn, {"kind": "doc", "material_id": state["grande"],
                                 "job_id": jid, "run_id": "r2"}) == died
