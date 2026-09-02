"""P4's own tests: what `jobs.py` does around a step, and the bits of `rerun.py` the contract
test in `test_p4_rerun_jobs.py` does not pin down.

Every engine step is stubbed here — this file is about the runner, not about what the runner runs.
"""
from __future__ import annotations

import pytest

from app import db, jobs, llm, rerun, store


def _stub(monkeypatch, **by_kind):
    """Replace every engine step with a recorder. `by_kind` swaps in a specific fake for one kind.
    Returns the list the recorders append to, in the order they ran."""
    ran: list[str] = []
    for kind, (line, _) in list(jobs.STEPS.items()):
        fn = by_kind.get(kind) or (lambda conn, pid, run, _k=kind: ran.append(_k))
        monkeypatch.setitem(jobs.STEPS, kind, (line, fn))
    return ran


# ---- the chain ----------------------------------------------------------------------------------

def test_the_upward_chain_runs_in_order_in_a_thread_of_its_own(conn, project, grande, monkeypatch):
    ran = _stub(monkeypatch)
    assert jobs.wait(jobs.ingest_chain(project, grande, conn_factory=db.connect), 10)
    assert ran == ["frame", "angles", "read", "themes", "doc", "accounts", "project"]
    assert [r["kind"] for r in store.runs(conn, project)] == ran
    assert all(r["finished"] and r["error"] is None for r in store.runs(conn, project))


def test_every_run_row_carries_a_sentence_a_researcher_can_read(conn, project, grande, monkeypatch):
    """The old engine's progress chip said `read` and nothing said what was being read."""
    _stub(monkeypatch)
    steps = ["frame", "angles", "read", "themes", "doc", "accounts", "project"]
    jobs.run_now(conn, project, [{"kind": k, "material_id": grande if k in
                                  ("frame", "angles", "read", "doc") else None} for k in steps])
    lines = [r["line"] for r in store.runs(conn, project)]
    assert len(lines) == len(steps)
    for kind, line in zip(steps, lines):
        assert line and line != kind, "the stage name is for the code, not for the person"
        assert " " in line and line[0].isupper()
    assert lines[steps.index("read")] == "Reading DP-40 Grande"
    assert lines[steps.index("doc")] == "Writing what stands out in DP-40 Grande"
    assert "look for" in lines[steps.index("angles")]


def test_a_thread_scoped_rerun_says_which_thread_it_is_rewriting(conn, project, grande, analysed,
                                                                 monkeypatch):
    _stub(monkeypatch)
    tid = analysed["themes"]["Work and trade"]
    jobs.run_now(conn, project, [{"kind": "doc", "material_id": analysed["grande"],
                                  "theme_id": tid}])
    assert store.runs(conn, project)[-1]["line"] == "Writing what stands out in Grande, M. on Work and trade"


def test_the_line_uses_the_title_the_frame_gave_it_once_there_is_one(conn, project, grande,
                                                                     monkeypatch):
    _stub(monkeypatch)
    store.save_frame(conn, grande, kind="interview", display="turns", title="Grande, M.",
                     speakers=[], segments=[])
    jobs.run_now(conn, project, [{"kind": "read", "material_id": grande}])
    assert store.runs(conn, project)[-1]["line"] == "Reading Grande, M."


# ---- when a step fails --------------------------------------------------------------------------

def test_a_failing_step_records_itself_and_stops_the_chain_without_killing_anything(
        conn, project, grande, monkeypatch):
    def boom(conn, pid, run):
        raise RuntimeError("the model said no")

    ran = _stub(monkeypatch, read=boom)
    jobs.run_now(conn, project, [{"kind": "frame", "material_id": grande},
                                 {"kind": "read", "material_id": grande},
                                 {"kind": "themes"},
                                 {"kind": "doc", "material_id": grande}])
    rows = store.runs(conn, project)
    assert [r["kind"] for r in rows] == ["frame", "read"], "the chain stops at the failure"
    assert ran == ["frame"], "and nothing after it runs"
    assert rows[0]["error"] is None
    assert "the model said no" in rows[1]["error"] and rows[1]["finished"]
    assert store.material(conn, grande)["state"] == "failed"


def test_a_chain_that_finishes_leaves_its_material_ready(conn, project, grande, monkeypatch):
    _stub(monkeypatch)
    jobs.run_now(conn, project, [{"kind": "frame", "material_id": grande},
                                 {"kind": "read", "material_id": grande}])
    assert store.material(conn, grande)["state"] == "ready"


def test_a_failure_in_a_background_chain_does_not_escape_the_thread(conn, project, grande,
                                                                    monkeypatch):
    def boom(conn, pid, run):
        raise RuntimeError("nope")

    _stub(monkeypatch, frame=boom)
    assert jobs.wait(jobs.ingest_chain(project, grande, conn_factory=db.connect), 10)
    assert "nope" in store.runs(conn, project)[-1]["error"]


def test_a_run_kind_nobody_can_run_is_refused_before_a_thread_is_started(project):
    with pytest.raises(ValueError):
        jobs.start(db.connect, project, [{"kind": "ponder"}])
    with pytest.raises(ValueError):
        jobs.run_now(db.connect(), project, [{"kind": "ponder"}])


# ---- tokens -------------------------------------------------------------------------------------

def test_the_tokens_a_step_spent_land_on_that_steps_run_row_and_no_other(conn, project, grande,
                                                                        monkeypatch):
    """`llm.usage` is reset around each run, so the second step is not billed for the first."""
    def spend(conn, pid, run):
        llm.usage["tokens_in"] += 1200
        llm.usage["tokens_out"] += 340

    _stub(monkeypatch, read=spend)
    llm.usage.update(tokens_in=99, tokens_out=99)        # left over from something earlier
    jobs.run_now(conn, project, [{"kind": "read", "material_id": grande},
                                 {"kind": "themes"}])
    rows = store.runs(conn, project)
    assert (rows[0]["tokens_in"], rows[0]["tokens_out"]) == (1200, 340)
    assert (rows[1]["tokens_in"], rows[1]["tokens_out"]) == (0, 0)


# ---- what the runner hands to the steps ---------------------------------------------------------

def test_the_researchers_words_reach_the_steps_that_take_them_verbatim(conn, project, grande,
                                                                       analysed, monkeypatch):
    got = {}

    def catch(conn, pid, run):
        got[run["kind"]] = jobs._text(conn, run)

    _stub(monkeypatch, frame=catch, themes=catch, check=catch)
    fid = store.add_feedback(conn, project, "frame", analysed["grande"], "note",
                             "this is not an interview, it is a set of notes")
    jobs.run_now(conn, project, rerun.plan(conn, fid))
    assert got["frame"] == "this is not an interview, it is a set of notes"


def test_doubt_on_a_moment_checks_against_that_moments_material(conn, analysed):
    """`check.run` needs a scope, and the runner takes it from the planned run's material."""
    fid = store.add_feedback(conn, analysed["pid"], "moment", analysed["moment"], "doubt", "no")
    assert rerun.plan(conn, fid)[0]["material_id"] == analysed["grande"]


def test_a_check_asked_anywhere_is_a_check(conn, analysed):
    fid = store.add_feedback(conn, analysed["pid"], "project_summary", analysed["pid"], "check",
                             "Does anyone mention money?")
    plan = rerun.plan(conn, fid)
    assert [p["kind"] for p in plan] == ["check"] and plan[0]["material_id"] is None


def test_a_comment_is_consumed_by_the_run_that_honours_it(conn, analysed, monkeypatch):
    """Fed in forever, a note from six months ago would still steer every rerun. A clean run
    consumes the comment that planned it; a failed one leaves it open to be tried again."""
    from app.engine import synth
    pid, mid = analysed["pid"], analysed["grande"]
    _stub(monkeypatch)
    fid = store.add_feedback(conn, pid, "material_summary", mid, "note", "the crossing is underplayed")
    assert "the crossing is underplayed" in synth.feedback_block(conn, pid, mid, None)
    jobs.run_now(conn, pid, rerun.plan(conn, fid))
    row = conn.execute("SELECT consumed_by_run FROM feedback WHERE id=?", (fid,)).fetchone()
    assert row[0] is not None
    assert "the crossing is underplayed" not in synth.feedback_block(conn, pid, mid, None)
    assert store.feedback_for(conn, "material_summary", mid), "still in the record for the export"


def test_a_failed_run_leaves_its_comment_open(conn, analysed, monkeypatch):
    def boom(conn, pid, run):
        raise RuntimeError("no")
    _stub(monkeypatch, doc=boom)
    fid = store.add_feedback(conn, analysed["pid"], "material_summary", analysed["grande"], "note", "x")
    jobs.run_now(conn, analysed["pid"], rerun.plan(conn, fid))
    assert conn.execute("SELECT consumed_by_run FROM feedback WHERE id=?", (fid,)).fetchone()[0] is None
