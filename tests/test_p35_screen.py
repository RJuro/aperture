"""P35 — the look before the reading: one call per material deciding a batch of cells.

    screen.run              the account, the coding and a batch of themes; verdicts Python owns
    rerun.consolidate_plan  one look and one check per material, not two calls per cell
    jobs._doc               a cell the look passed over, cancelled on its own row without a call
    synth.doc(check=False)  the line written, the check left to the material's one verify step
    context._assessed       the fifth kind of nothing, on the page, the record and the account

The researcher's complaint is the whole of this file: comparing every theme across an
eight-material corpus planned forty-five cells and ninety-one calls, and every one of those calls
sent the whole material again to ask a question most of them answered with nothing. What is not
being built is the code gate docs/EVAL.md pass 3 rejected — a count of hits, which skipped twelve
cells of which nine still produced lines and four were among the best. This call reads the
material's own account of itself and its coding, and every doubtful case still costs a reading.
"""
from __future__ import annotations

import pytest

from app import context, ingest, jobs, rerun, store

screen = pytest.importorskip("app.engine.screen")
synth = pytest.importorskip("app.engine.synth")


def _material(conn, pid: str, n: int) -> str:
    text = (f"SPEAKER: Material {n} begins here. The work was hard and the days were long. "
            "They left in the spring and did not come back.")
    mid = store.add_material(conn, pid, f"Material {n}", text)
    store.save_sentences(conn, mid, ingest.sentences(text))
    return mid


def _line(conn, mid: str, tid: str) -> None:
    sid, text = store.sentences(conn, mid)[1]
    store.save_moments(conn, mid, tid, [{"claim": f"a claim about {tid}",
                                         "anchor": " ".join(text.split()[:6]), "sid": sid}])
    store.save_follow(conn, mid, tid, "line")


def _coded(conn, pid: str, mid: str, name: str, definition: str, at: int = 1) -> None:
    """One code with one passage under it, so the look has a coding to read."""
    sid, _ = store.sentences(conn, mid)[at]
    store.save_codes(conn, pid, mid, [{"name": name, "definition": definition, "sids": [sid]}])


@pytest.fixture
def corpus(conn, project):
    """Four materials; `wide` holds a line in two of them and has never been read for in the
    other two. Those two cells are exactly what a consolidation goes back for."""
    mids = [_material(conn, project, n) for n in range(4)]
    wide = store.save_theme(conn, project, tid=None, name="Wide", gist="in two so far",
                            code_ids=[])
    other = store.save_theme(conn, project, tid=None, name="Other", gist="in two so far",
                             code_ids=[])
    for t in (wide, other):
        store.set_hold(conn, t, "candidate")
    for mid in mids[:2]:
        _line(conn, mid, wide)
        _line(conn, mid, other)
    for mid in mids:
        _coded(conn, project, mid, "leaving", "going away and staying gone")
    return {"pid": project, "mids": mids, "wide": wide, "other": other}


# ---- what the look is shown, and what it is not --------------------------------------------------

def test_the_look_sees_the_account_the_coding_and_every_theme_id_and_nothing_else(corpus, conn,
                                                                                  model):
    """One call, four slots. The material's own text is NOT one of them — that is the expensive
    call this exists to avoid — and every theme it must decide is in it, so the answer can be
    read against a known list rather than trusted."""
    pid, mid = corpus["pid"], corpus["mids"][2]
    store.save_summary(conn, "material", mid, "reading", "What the reading of this one found.")
    model.queue({"verdicts": [{"id": corpus["wide"], "verdict": "look", "why": "the leaving code"},
                              {"id": corpus["other"], "verdict": "pass", "why": "nothing here"}]})

    out = screen.run(conn, mid, [corpus["wide"], corpus["other"]])

    assert [c["label"] for c in model.calls] == ["screen"], "one call for the batch"
    shown = model.shown("screen")
    assert "What the reading of this one found." in shown, "the material's own account"
    assert "leaving — going away and staying gone" in shown, "and its coding, with definitions"
    assert corpus["wide"] in shown and corpus["other"] in shown, "every theme it must decide"
    assert "They left in the spring and did not come back." not in shown, "not the material"
    assert out["look"] == [corpus["wide"]]
    assert out["pass"] == [(corpus["other"], "nothing here")]


def test_the_account_is_the_best_one_that_exists_and_says_which_it_is(corpus, conn, model):
    """A memo, a reading summary and an orientation are not equally strong, and a look that
    cannot tell them apart weighs a guess made before the reading as the reading's conclusion."""
    pid, mid = corpus["pid"], corpus["mids"][2]
    store.save_summary(conn, "material", mid, "orientation", "What this was taken to be.")
    model.queue({"verdicts": []})
    screen.run(conn, mid, [corpus["wide"]])
    said = model.shown("screen")
    assert "before it was read" in said and "What this was taken to be." in said

    model.calls.clear()
    store.save_summary(conn, "material", mid, "memo", "What this material says on its own terms.")
    model.queue({"verdicts": []})
    screen.run(conn, mid, [corpus["wide"]])
    said = model.shown("screen")
    assert "What this material says on its own terms." in said
    assert "the passages its coding marked" in said, "and it says which kind of account this is"


# ---- what Python does with the answer ------------------------------------------------------------

def test_a_pass_writes_the_fifth_outcome_with_its_words(corpus, conn, model):
    """`screened`, and why — the one outcome a researcher cannot reconstruct from the rows,
    because nothing else in the database records what was looked at."""
    pid, mid = corpus["pid"], corpus["mids"][2]
    model.queue({"verdicts": [{"id": corpus["wide"], "verdict": "pass",
                               "why": "the leaving code is about a wedding, not this"}]})

    screen.run(conn, mid, [corpus["wide"]])

    assert store.followed(conn, pid)[(corpus["wide"], mid)] == "screened"
    assert (store.follow_notes(conn, pid)[(corpus["wide"], mid)]
            == "the leaving code is about a wedding, not this")


def test_an_omitted_or_unreadable_verdict_is_looked_for(corpus, conn, model):
    """Rule 4's default, enforced in Python rather than trusted to the model. A missed theme costs
    a finding; a reading costs a call. Nothing is written for these: their outcome is whatever the
    reading that follows finds."""
    pid, mid = corpus["pid"], corpus["mids"][2]
    model.queue({"verdicts": [{"id": corpus["wide"], "verdict": "maybe", "why": "unsure"}]})

    out = screen.run(conn, mid, [corpus["wide"], corpus["other"]])

    assert set(out["look"]) == {corpus["wide"], corpus["other"]} and out["pass"] == []
    assert (corpus["wide"], mid) not in store.followed(conn, pid), "nothing was decided"
    assert len(out["dropped"]) == 2, "and the run row says both were left undecided"


# ---- the plan, and the cancelling --------------------------------------------------------------

def test_the_back_fill_looks_once_and_checks_once_per_material(corpus, conn):
    """Two calls per cell became one look and one check per MATERIAL, whatever the cell count:
    the look reads one account and one coding, and VERIFY reads each passage once for the whole
    material — a material that gained nine lines was paying nine times over the same text."""
    pid, mids = corpus["pid"], corpus["mids"]
    plan = rerun.consolidate_plan(conn, pid, scope="all")

    assert [r["kind"] for r in plan] == (
        ["consolidate"] + ["screen", "doc", "doc", "verify"] * 2 + ["summary"] * 2
        + ["settle", "accounts", "project"])
    looks = [r for r in plan if r["kind"] == "screen"]
    assert [r["material_id"] for r in looks] == [mids[2], mids[3]]
    assert all(sorted(r["themes"]) == sorted([corpus["wide"], corpus["other"]]) for r in looks)
    assert [r["material_id"] for r in plan if r["kind"] == "verify"] == [mids[2], mids[3]]


def test_the_switch_takes_the_look_out_and_every_cell_is_read(corpus, conn, monkeypatch):
    """The evaluation compares the chain with the look against the chain without it, so the look
    has to come out without a second plan to maintain."""
    monkeypatch.setenv("APERTURE_SCREEN", "off")
    plan = rerun.consolidate_plan(conn, corpus["pid"], scope="all")

    assert not [r for r in plan if r["kind"] == "screen"]
    assert [r["kind"] for r in plan].count("doc") == 4, "every planned cell still runs"


def _block(conn, pid: str, mid: str) -> list[dict]:
    """One material's part of the plan — its look, its cells and its check — as a job, so the
    cancelling can be asked the question it actually asks: was this decided by THIS chain?"""
    plan = rerun.consolidate_plan(conn, pid, scope="all")
    return [r for r in plan if r.get("material_id") == mid
            and r["kind"] in ("screen", "doc", "verify")]


def _as_job(conn, pid: str, runs: list[dict]) -> str:
    jid = store.enqueue_job(conn, pid, runs)
    store.start_job(conn, jid)
    jobs.run_now(conn, pid, runs, job=jid)
    return jid


def test_a_cell_the_look_passed_over_is_cancelled_on_its_own_row_without_a_call(corpus, conn,
                                                                               model):
    """Not deleted from the plan: a run row that ran nothing must say why, or a researcher cannot
    tell a cell that was decided from one nobody ever planned."""
    pid, mid = corpus["pid"], corpus["mids"][2]
    model.queue({"verdicts": [{"id": corpus["wide"], "verdict": "pass", "why": "nothing on it"},
                              {"id": corpus["other"], "verdict": "pass", "why": "nor this"}]})
    # No THREAD answer is queued: a second model call here would raise, which is the assertion.
    job = _as_job(conn, pid, _block(conn, pid, mid))

    assert [c["label"] for c in model.calls] == ["screen"], "one call, no reading, no check"
    rows = [dict(r) for r in conn.execute(
        "SELECT kind, line, error FROM run WHERE job_id=? AND kind='doc'", (job,))]
    assert len(rows) == 2, "both cells still have a row of their own"
    assert all(r["error"] is None and "Passed over by the look at Material 2" in r["line"]
               for r in rows), "each saying why it ran nothing"


def test_a_theme_the_look_sends_a_reader_to_is_read_and_checked_once_after(corpus, conn, model):
    """The other half of the split: the line is written and its follow row recorded, and the
    material's single check — not one per line — rules on the claims and rewrites the summary of
    any line it took a claim away from."""
    pid, mid = corpus["pid"], corpus["mids"][2]
    sid, text = store.sentences(conn, mid)[1]
    model.queue({"verdicts": [{"id": corpus["wide"], "verdict": "look", "why": "the code"},
                              {"id": corpus["other"], "verdict": "pass", "why": "no"}]})
    model.queue({"moments": [{"claim": "the days were long", "sid": sid,
                              "anchor": " ".join(text.split()[:6])}], "summary": "a line"})
    model.queue({"verdicts": []})                       # the material's one check

    _as_job(conn, pid, _block(conn, pid, mid))

    assert [c["label"] for c in model.calls] == ["screen", "thread", "verify"]
    assert store.followed(conn, pid)[(corpus["wide"], mid)] == "line"
    assert store.followed(conn, pid)[(corpus["other"], mid)] == "screened"


def test_a_line_that_lost_a_claim_in_that_check_is_summarised_again(corpus, conn, model):
    """A line's summary is written with the THREAD answer, before any claim is checked, so a
    paragraph about two claims can end up standing over a line of one. The material's single check
    owes those rewrites exactly as DOC's own check does."""
    pid, mid = corpus["pid"], corpus["mids"][2]
    (sid, text), (sid2, text2) = store.sentences(conn, mid)[1:3]
    model.queue({"moments": [{"claim": "the days were long", "sid": sid,
                              "anchor": " ".join(text.split()[:6])},
                             {"claim": "they did not come back", "sid": sid2,
                              "anchor": " ".join(text2.split()[:6])}],
                 "summary": "a paragraph about two claims, one of which is about to go"})
    synth.doc(conn, mid, only_theme=corpus["wide"], check=False)
    gone, stands = [m["id"] for m in store.thread(conn, mid, corpus["wide"])]

    model.queue({"verdicts": [{"id": gone, "verdict": "not", "why": "the passage does not say it"},
                              {"id": stands, "verdict": "supported", "why": ""}]})
    model.queue({"summary": "a paragraph about the one claim that stands"})
    notes = jobs.STEPS["verify"][1](conn, pid, {"kind": "verify", "material_id": mid})

    assert [c["label"] for c in model.calls] == ["thread", "verify", "line_summary"]
    assert len(store.thread(conn, mid, corpus["wide"])) == 1, "the check took one away"
    said = store.get_summary(conn, "thread", f'{mid}:{corpus["wide"]}', "reading")
    assert said["text"] == "a paragraph about the one claim that stands"
    assert any("set aside" in n for n in notes), "and the run row says what went"


def test_the_line_is_written_without_a_check_when_the_material_will_be_checked_once(corpus, conn,
                                                                                   model):
    """`check=False` is what makes one check per material possible: the line and its follow row
    are written, and nothing is verified or re-summarised until the material's own check runs."""
    pid, mid = corpus["pid"], corpus["mids"][2]
    sid, text = store.sentences(conn, mid)[1]
    model.queue({"moments": [{"claim": "the days were long", "sid": sid,
                              "anchor": " ".join(text.split()[:6])}], "summary": "a line"})

    synth.doc(conn, mid, only_theme=corpus["wide"], check=False)

    assert [c["label"] for c in model.calls] == ["thread"], "no check, no re-summary"
    assert store.followed(conn, pid)[(corpus["wide"], mid)] == "line"
    assert store.thread(conn, mid, corpus["wide"]), "and the claim is there to read"


# ---- the fifth state, on every surface ----------------------------------------------------------

SAID = "Looked at from this material's own account and its coding, and not pursued"


def test_the_fifth_state_is_said_on_the_page_the_record_and_the_account(corpus, conn):
    """Weaker than 'looked for and found too thin' and stronger than 'not looked for here', and
    printed as its own kind of nothing wherever an absence is stated (PLAN.md §3, law 2)."""
    from app.engine import account

    pid, mid = corpus["pid"], corpus["mids"][2]
    store.save_follow(conn, mid, corpus["wide"], "screened", note="the code is about a wedding")

    assert context._assessed(store.followed(conn, pid), corpus["wide"], mid) == "screened"
    assert context.ASSESSED_SAID["screened"]["label"] == "Source check skipped"

    page = context.theme_page(conn, pid, corpus["wide"])
    said = [m for m in page["absent"] if m["material_id"] == mid][0]
    assert said["assessed"] == "screened"
    assert said["screened_why"] == "the code is about a wedding", "with what the look said"

    absent = [{"material_id": mid, "title": "Material 2", "name": "Material 2", "kind": "interview"}]
    block = account._absent_block(conn, pid, corpus["wide"], absent)
    assert "NOT PURSUED" in block and "not an absence in it" in block
    assert "the code is about a wedding" in block


def test_the_page_and_the_record_print_it_where_an_absence_would_go(corpus, conn, monkeypatch):
    """Rendered, not only in the dict: this is the sentence that stops a reader treating a cell
    nobody read as a silence in the material."""
    from fastapi.testclient import TestClient

    from app import accounts, main, pages, verbs
    pid, mid = corpus["pid"], corpus["mids"][2]
    store.save_follow(conn, mid, corpus["wide"], "screened", note="nothing about official papers")
    for mod in (pages, verbs, accounts):
        monkeypatch.setattr(mod, "connection", lambda: conn, raising=False)
    client = TestClient(main.app, follow_redirects=False)

    # The theme page, the record and the export all use the same short label for this state
    # (§4 F3 of the review); the reason recorded for this pair is what tells them apart.
    theme = client.get(f"/p/{pid}/t/{corpus['wide']}").text
    assert "Source check skipped" in theme and "nothing about official papers" in theme
    record = client.get(f"/p/{pid}/record").text
    assert "Source check skipped" in record and "nothing about official papers" in record
    export = client.get(f"/p/{pid}/export.md").text
    assert "Source check skipped" in export and "nothing about official papers" in export


# ---- what the preview promises -------------------------------------------------------------------

def test_the_preview_prints_the_range_the_plan_would_actually_build(corpus, conn):
    """Law 4: the number is the rows it is over. The floor is the comparison, a look and a check
    for each material with cells, and the project summary — certain — and the ceiling adds every
    cell, a summary of each touched material, and every live theme's account (F5)."""
    pid = corpus["pid"]
    cells = store.backfill_cells(conn, pid, "all")
    plan = rerun.consolidate_plan(conn, pid, scope="all")
    floor = len([r for r in plan if r["kind"] in ("consolidate", "screen", "verify")])
    assert (floor, len(cells)) == (5, 4), "one comparison, two looks, two checks, four cells"

    said = context.project_page(conn, pid)["consolidate"]
    # Both candidates are carried by exactly two of the four materials — the wider scope's own
    # threshold — so the default scope reads the same cells the wider one would.
    assert said["opening_n"] == said["all_n"] == len(cells) == 4 and said["same"]
    # 2 (comparison + project summary) + 2 (a look and a check for each of the two materials) = 6;
    # + the 4 cells + 2 material summaries (iterative, one per touched material) + 0 live themes.
    assert said["opening_said"] == "4 theme/material pairs to check · about 6–12 model calls"


def test_with_the_look_off_the_preview_offers_no_range_it_cannot_deliver(corpus, conn, monkeypatch):
    """Every planned cell is then read, so the floor IS the ceiling and the page says one number."""
    monkeypatch.setenv("APERTURE_SCREEN", "off")
    plan = rerun.consolidate_plan(conn, corpus["pid"], scope="all")
    said = context.project_page(conn, corpus["pid"])["consolidate"]

    # 2 + 2 materials read + the 4 cells (all certain, with no look to defer any of them) + the 2
    # material summaries + 0 live themes = 10, and nothing here is left uncertain.
    assert said["opening_said"] == "4 theme/material pairs to check · about 10 model calls"
    assert len([r for r in plan if r["kind"] in ("consolidate", "doc", "verify")]) == 7


def test_nothing_here_reaches_a_model_by_accident(corpus, conn):
    """The plan and the preview are arithmetic over rows, as they were before the look existed."""
    rerun.consolidate_plan(conn, corpus["pid"], scope="all")
    context.project_page(conn, corpus["pid"])
