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
    assert jobs.wait(jobs.ingest_chain(project, [grande], conn_factory=db.connect), 10)
    # A new project explores, so each reading is followed by the comparison of what it named with
    # the project's vocabulary. `test_p28_method` holds the iterative chain, which has neither.
    assert ran == ["frame", "angles", "read", "reconcile", "themes", "doc", "accounts", "project"]
    assert [r["kind"] for r in store.runs(conn, project)] == ran
    assert all(r["finished"] and r["error"] is None for r in store.runs(conn, project))


def test_one_upload_of_several_files_is_one_chain_with_one_tail(conn, project, grande, rodwin,
                                                                monkeypatch):
    """Five files used to mean five chains, each re-finding themes and rewriting the corpus
    summary behind the four still waiting behind it.

    Two materials are framed, ideated, read and written up beside each other now (`jobs._stages`),
    so what holds is each material's own order, THEMES one at a time in the planned order, and one
    tail for the upload — not one flat list of twelve.
    """
    ran = _stub(monkeypatch)
    assert jobs.wait(jobs.ingest_chain(project, [grande, rodwin], conn_factory=db.connect), 10)
    assert sorted(ran) == sorted(["frame", "angles", "read", "reconcile"] * 2 +
                                 ["themes", "themes", "doc", "doc", "accounts", "project"])
    assert ran[8:10] == ["themes", "themes"], "after every material has been read"
    assert ran[-2:] == ["accounts", "project"], "and the corpus level once, at the end"
    rows = store.runs(conn, project)
    for mid in (grande, rodwin):
        assert [r["kind"] for r in rows if r["material_id"] == mid] == \
            ["frame", "angles", "read", "reconcile", "themes", "doc"], \
            "one material's own order is kept"
    assert [r["material_id"] for r in rows if r["kind"] == "themes"] == [grande, rodwin]
    assert {r["material_id"] for r in rows if r["kind"] == "doc"} == {grande, rodwin}


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


def test_the_corpus_level_is_left_to_the_last_chain_in_the_queue(conn, project, monkeypatch):
    """Two uploads a minute apart are two chains, each ending in the accounts and the corpus
    summary. The first used to write both over material the second had not read yet."""
    ran = _stub(monkeypatch)
    tail = [{"kind": "accounts"}, {"kind": "project"}]
    first, second = (store.enqueue_job(conn, project, tail) for _ in range(2))

    store.start_job(conn, first)
    jobs.run_now(conn, project, tail, job=first)
    assert ran == [], "the second chain is still reading"
    rows = store.runs(conn, project)
    assert [r["kind"] for r in rows] == ["accounts", "project"]
    # On the line. In the notes it printed under "Excluded from the analysis", which is where a
    # claim the reading dropped is listed.
    assert all(r["line"] == jobs.LEFT_TO_THE_LAST and r["error"] is None for r in rows)
    assert not any(jobs.LEFT_TO_THE_LAST in (r["notes"] or "") for r in rows)

    store.finish_job(conn, first)
    store.start_job(conn, second)
    jobs.run_now(conn, project, tail, job=second)
    assert ran == ["accounts", "project"], "the last chain writes them once"


def test_a_question_waiting_its_turn_does_not_cost_the_upload_its_corpus_summary(
        conn, project, grande, monkeypatch):
    """Any second job of any kind used to make the running chain leave the corpus level to the
    chain that follows — and a check job, an account job or a doc job never writes it."""
    ran = _stub(monkeypatch)
    tail = [{"kind": "accounts"}, {"kind": "project"}]
    mine = store.enqueue_job(conn, project, tail)
    store.enqueue_job(conn, project, [{"kind": "check", "material_id": grande}])

    store.start_job(conn, mine)
    jobs.run_now(conn, project, tail, job=mine)
    assert ran == ["accounts", "project"], "nothing behind it will write the corpus summary"


def test_a_step_can_say_where_it_has_got_to_on_its_own_run_row(conn, project, grande, monkeypatch):
    """A step is one model call or twelve, and between them the page said nothing at all. The
    hook is live only while a step runs — outside one there is no row to write on."""
    seen = []

    def slow(conn_, pid, run):
        llm.report("busy")
        seen.append(store.runs(conn_, pid)[-1]["line"])

    _stub(monkeypatch, read=slow)
    jobs.run_now(conn, project, [{"kind": "read", "material_id": grande}])
    assert seen == ["Reading DP-40 Grande — busy"]

    llm.report("nobody is listening to this")
    assert store.runs(conn, project)[-1]["line"] == "Reading DP-40 Grande — busy"


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
    assert jobs.wait(jobs.ingest_chain(project, [grande], conn_factory=db.connect), 10)
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


def test_a_check_on_a_claim_searches_that_claims_material(conn, analysed):
    """`check.run` needs a scope, and the runner takes it from the planned run's material."""
    fid = store.add_feedback(conn, analysed["pid"], "moment", analysed["moment"], "check",
                             "does anyone else say this?")
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


def test_a_comment_on_a_claim_is_consumed_by_the_rewrite_that_answers_it(conn, analysed,
                                                                         monkeypatch):
    """A note on a claim plans no run of its own, so nothing ever stamped it honoured: it went
    into every later prompt for that material for ever, and the export kept calling it open."""
    from app.engine import synth
    pid, mid = analysed["pid"], analysed["grande"]
    _stub(monkeypatch)

    def consumed(fid):
        return conn.execute("SELECT consumed_by_run FROM feedback WHERE id=?",
                            (fid,)).fetchone()[0]

    here = store.moment(conn, analysed["moment"])
    elsewhere = next(m for m in store.moments(conn, mid) if m["theme_id"] != here["theme_id"])
    mine = store.add_feedback(conn, pid, "moment", here["id"], "note", "this overstates it")
    theirs = store.add_feedback(conn, pid, "moment", elsewhere["id"], "note", "and so does this")
    assert rerun.plan(conn, mine) == [], "a claim is checked against the material, not rewritten"
    assert "this overstates it" in synth.feedback_block(conn, pid, mid, None)

    jobs.run_now(conn, pid, [{"kind": "doc", "material_id": mid, "theme_id": here["theme_id"]}])
    assert consumed(mine) and not consumed(theirs), "one line's rewrite answers one line"

    jobs.run_now(conn, pid, [{"kind": "doc", "material_id": mid}])
    assert consumed(theirs)
    assert "and so does this" not in synth.feedback_block(conn, pid, mid, None)
    assert len(store.feedback_for(conn, "moment", elsewhere["id"])) == 1, "still in the record"


def test_a_failed_run_leaves_its_comment_open(conn, analysed, monkeypatch):
    def boom(conn, pid, run):
        raise RuntimeError("no")
    _stub(monkeypatch, doc=boom, summary=boom)
    fid = store.add_feedback(conn, analysed["pid"], "material_summary", analysed["grande"], "note", "x")
    jobs.run_now(conn, analysed["pid"], rerun.plan(conn, fid))
    assert conn.execute("SELECT consumed_by_run FROM feedback WHERE id=?", (fid,)).fetchone()[0] is None
