"""P31 — evidence first: what an exploratory project does after the reading. PLAN.md §13.

    app/engine/memo.py      MEMO      — one material's account on its own terms, over its passages
    themes.run_cross        THEMES    — one call per BATCH, over the codebook's own passages
    app/engine/residual.py  RESIDUAL  — the passages no code marked, read once against the themes

Pass 5 of docs/EVAL.md is why this file exists: two materials coded on their own terms produced
eight candidates and nothing across them. Reading one transcript at a time cannot find a pattern
that lives between transcripts, and a summary written over theme lines goes stale the moment the
themes move — which, in an exploratory project, is after every batch.

So the unit of expensive work becomes a reading of one material and a question asked of the
corpus. The three silences of §3 become four, and the fourth is the one this file cares about
most: `residual`, an absence somebody went and looked for.

Nothing here touches an `iterative` project. Its chain, its synthesis and its per-material THEMES
are what they have always been, and the tests that hold them are elsewhere.
"""
from __future__ import annotations

import pytest

from app import jobs, rerun, store
from app.engine import memo, residual, synth, themes


@pytest.fixture
def explored(conn, project, grande, rodwin):
    """An exploratory project with both materials framed, oriented and coded.

    One code — "Work and trade" — is marked in BOTH materials, because a cross-case pass has to be
    shown two materials' passages under one code or it is a per-material pass with extra steps.
    "Papers and permits" is marked in Grande alone, so one theme has a material its codes never
    fired in, which is what the gate and RESIDUAL are both about.
    """
    store.set_method(conn, project, "explore")
    for mid, title in ((grande, "Grande"), (rodwin, "Rodwin")):
        store.save_frame(conn, mid, kind="interview", display="turns", title=title,
                         speakers=[], segments=[])
        store.save_summary(conn, "material", mid, "orientation", "A 1978 oral history.")
        store.save_codes(conn, project, mid,
                         [{"name": "Work and trade", "definition": "how a living is made",
                           "sids": [store.sentences(conn, mid)[5][0]]}])
    store.save_codes(conn, project, grande,
                     [{"name": "Papers and permits", "definition": "documents and permission",
                       "sids": [store.sentences(conn, grande)[9][0]]}])
    codes = {c["name"]: c["id"] for c in store.codebook(conn, project)}
    work = store.save_theme(conn, project, tid=None, name="Work and trade", gist="a living",
                            code_ids=[codes["Work and trade"]])
    papers = store.save_theme(conn, project, tid=None, name="Papers", gist="documents",
                              code_ids=[codes["Papers and permits"]])
    return {"pid": project, "grande": grande, "rodwin": rodwin, "codes": codes,
            "work": work, "papers": papers}


def _marked(conn, mid: str) -> set[str]:
    return {h["sid"] for h in store.hits(conn, mid)}


def _memo_text(conn, mid: str) -> tuple[str, list[str]]:
    """A three-sentence memo over this material's own marked passages, the middle sentence citing
    nothing. Returns the memo and the sids it cites."""
    sids = sorted(_marked(conn, mid))
    said = [f"The stall is what fed them [{sids[0]}].",
            "The interviewer never asks what the wage was.",
            f"The crossing is told twice over [{sids[-1]}]."]
    return " ".join(said), sids


# ---- MEMO ---------------------------------------------------------------------------------------

def test_a_memo_sentence_that_cites_nothing_never_reaches_the_page(explored, conn, model):
    """The rule Python owns rather than the prompt. A sentence with no passage behind it may well
    be true and there is no way for a reader to find out, so it goes before anyone reads it — and
    the exclusion quotes it, the way VERIFY-SUMMARY quotes a sentence the claims do not carry."""
    mid = explored["grande"]
    text, sids = _memo_text(conn, mid)
    model.queue({"memo": text, "questions": "What did the wage buy?",
                 "people": [{"name": "M. Grande", "aliases": [], "role": "participant"}]})
    model.queue({"verdicts": []})

    out = memo.run(conn, mid)

    stored = store.get_summary(conn, "material", mid, "memo")["text"]
    assert "The stall is what fed them" in stored
    assert "The crossing is told twice over" in stored
    assert "the wage was" not in stored, "the sentence that cited nothing was dropped"
    assert any("cites no passage" in d for d in out["dropped"])
    assert any("The interviewer never asks" in d for d in out["dropped"]), "and it is quoted"
    # The questions and the people are saved exactly where DOC saves them, so ANGLES and the
    # record read them without knowing which method wrote them.
    assert store.get_summary(conn, "material", mid, "questions")["text"] == "What did the wage buy?"
    assert [p["name"] for p in store.people(conn, mid)] == ["M. Grande"]


def test_the_memo_is_checked_against_the_passages_it_cites_and_not_against_claims(explored, conn,
                                                                                  model):
    """A memo is written before any line exists, so VERIFY-SUMMARY cannot be shown the claims it
    ordinarily checks against. It is shown the cited passages instead — and a sentence they do not
    carry is set aside exactly as it would be under DOC."""
    mid = explored["grande"]
    text, sids = _memo_text(conn, mid)
    passages = dict(store.sentences(conn, mid))
    model.queue({"memo": text, "questions": "", "people": []})
    model.queue({"verdicts": [{"n": 2, "verdict": "not", "why": "no passage says this"}]})

    out = memo.run(conn, mid)

    shown = model.shown("verify_summary")
    assert passages[sids[0]] in shown, "the passage the memo says it rests on"
    assert not store.moments(conn, mid), "there are no claims yet; that is the whole point"
    # Sentence 2 of what survived the citation rule is the crossing; the check set it aside.
    stored = store.get_summary(conn, "material", mid, "memo")["text"]
    assert stored == "The stall is what fed them [%s]." % sids[0]
    assert any("set aside" in d for d in out["dropped"])


def test_the_memo_is_what_an_exploring_material_page_calls_the_reading(explored, conn):
    """`memo` outranks `reading` in `store.get_summary`, so the page shows it under the heading it
    shows a reading summary under. An iterative project has no memo and is unaffected."""
    from app import context
    mid = explored["grande"]
    store.save_summary(conn, "material", mid, "memo", "What this material says on its own terms.")
    page = context.material_page(conn, explored["pid"], mid)
    assert page["summary"]["stage"] == "memo"
    assert page["summary"]["text"] == "What this material says on its own terms."

    store.set_method(conn, explored["pid"], "iterative")
    store.save_summary(conn, "material", explored["rodwin"], "reading", "What the reading found.")
    other = context.material_page(conn, explored["pid"], explored["rodwin"])
    assert other["summary"]["stage"] == "reading"


# ---- DOC, in explore mode ------------------------------------------------------------------------

def test_an_exploring_synthesis_writes_lines_and_no_summary_at_all(explored, conn, model):
    """DOC still writes the lines, the check and the follow rows. It writes no summary beside the
    memo and makes no VERIFY-SUMMARY call: the memo is this material's account and it was written
    over the passages rather than over lines that have not settled."""
    mid, sids = explored["grande"], sorted(_marked(conn, explored["grande"]))
    passages = dict(store.sentences(conn, mid))
    quote = " ".join(passages[sids[0]].split()[:8])
    # Both of this project's codes fired in Grande, so the gate passes both themes through.
    for _ in (explored["work"], explored["papers"]):
        model.queue({"moments": [{"claim": "The stall fed them.", "anchor": quote,
                                  "sid": sids[0]}]})
    model.queue({"verdicts": []})

    out = synth.doc(conn, mid)

    assert [c["label"] for c in model.calls] == ["thread", "thread", "verify"], \
        "the lines and their check, and no summary call at all"
    assert out["summary"] == ""
    assert store.get_summary(conn, "material", mid, "reading") is None
    assert store.thread(conn, mid, explored["work"]), "the line was written all the same"
    assert store.followed(conn, explored["pid"])[(explored["work"], mid)] == "line"


def test_an_exploring_synthesis_gates_every_theme_on_its_codes(explored, conn, model):
    """The gate of §3 law 2 is on for an exploratory project without anyone setting a variable:
    after RECONCILE, a code that fired here means something across the corpus. Rodwin carries the
    work code and not the papers code, so exactly one line is asked for."""
    mid, sids = explored["rodwin"], sorted(_marked(conn, explored["rodwin"]))
    quote = " ".join(dict(store.sentences(conn, mid))[sids[0]].split()[:8])
    model.queue({"moments": [{"claim": "A living was made.", "anchor": quote, "sid": sids[0]}]})
    model.queue({"verdicts": []})

    synth.doc(conn, mid)

    assert len([c for c in model.calls if c["label"] == "thread"]) == 1
    assert explored["papers"] not in model.shown("thread")
    assert store.followed(conn, explored["pid"])[(explored["papers"], mid)] == "skipped"


def test_the_summary_step_rewrites_the_memo_where_a_project_explores(explored, conn, model):
    """"Write the account of this material again" is what a comment on the account asks for, and
    in an exploratory project that account is the memo. One kind of step, both methods."""
    mid = explored["grande"]
    text, sids = _memo_text(conn, mid)
    model.queue({"memo": text, "questions": "", "people": []})
    model.queue({"verdicts": []})

    synth.doc(conn, mid, summary_only=True)

    assert [c["label"] for c in model.calls] == ["memo", "verify_summary"]
    assert "The stall is what fed them" in store.get_summary(conn, "material", mid, "memo")["text"]
    assert store.get_summary(conn, "material", mid, "reading") is None


# ---- CROSS-CASE THEMES --------------------------------------------------------------------------

def test_the_cross_case_pass_is_shown_one_code_carried_by_two_materials(explored, conn, model):
    """What replaces the material. A code that fired in Grande and in Rodwin arrives with a
    passage from each, labelled by material — which is the only shape in which a pattern ACROSS
    materials is visible at all. One call for the batch, not one per material."""
    for mid in (explored["grande"], explored["rodwin"]):
        store.save_summary(conn, "material", mid, "memo", f"The memo of {mid}.")
    model.queue({"themes": [], "candidates": [], "tensions": []})

    themes.run_cross(conn, explored["pid"], [explored["grande"], explored["rodwin"]])

    assert len(model.calls) == 1, "one call for the whole batch"
    shown = model.shown("themes")
    under = shown.split("## Work and trade")[1].split("## ")[0]
    assert explored["grande"] in under and explored["rodwin"] in under, \
        "the one code both materials carry is evidenced from both"
    for mid in (explored["grande"], explored["rodwin"]):
        sid = sorted(_marked(conn, mid))[0]
        assert dict(store.sentences(conn, mid))[sid] in under, "verbatim, not by id alone"
        assert f"The memo of {mid}." in shown, "and each material's memo travels with it"
    # Law 5 withholds spread on purpose: the passages are the evidence, not a count of them.
    assert "materials carry" not in shown


def test_the_cross_case_pass_can_confirm_a_candidate_from_another_material(explored, conn, model):
    """A candidate is a pattern seen in one material; what promotes it is a second material's
    coding carrying it. Confirmation gathers its codes and leaves its words alone — the same rule
    the per-material pass follows, because `_apply` is one function serving both."""
    cand = store.save_theme(conn, explored["pid"], tid=None, name="The stall",
                            gist="what actually fed them", code_ids=[])
    store.set_hold(conn, cand, "candidate")
    model.queue({"themes": [], "tensions": [],
                 "candidates": [{"id": cand, "name": "Renamed by the model",
                                 "gist": "reworded too", "code_names": ["Work and trade"]}]})

    out = themes.run_cross(conn, explored["pid"], [explored["grande"], explored["rodwin"]])

    assert cand in out["themes"]
    row = [t for t in store.candidates(conn, explored["pid"]) if t["id"] == cand][0]
    assert row["name"] == "The stall" and row["gist"] == "what actually fed them"
    assert [c["id"] for c in store.theme_codes(conn, cand)] == [explored["codes"]["Work and trade"]]


def test_a_tension_raised_over_a_batch_says_which_material_raised_it(explored, conn, model):
    """`material_id` is not the pass's any more — it read several — so the answer names one, and
    an id that is not in the batch is not believed."""
    store.set_hold(conn, explored["work"], "frozen")
    model.queue({"themes": [], "candidates": [],
                 "tensions": [{"id": explored["work"], "material": explored["rodwin"],
                               "note": "Rodwin pulls this toward the market rather than the wage."},
                              {"id": explored["papers"], "material": "m-nobody",
                               "note": "not frozen, so not a tension at all"}]})

    themes.run_cross(conn, explored["pid"], [explored["grande"], explored["rodwin"]])

    notes = store.theme_notes(conn, explored["work"])
    assert [n["material_id"] for n in notes] == [explored["rodwin"]]
    assert store.theme_notes(conn, explored["papers"]) == []


def test_an_iterative_project_still_finds_themes_one_material_at_a_time(conn, project, grande,
                                                                       rodwin, monkeypatch):
    """Nothing in §13 reaches the other method. THEMES stays per material, with that material's
    own id on the run, and no cross-case pass is planned for it."""
    store.set_method(conn, project, "iterative")
    planned: list[dict] = []
    monkeypatch.setattr(jobs, "start", lambda factory, pid, runs: planned.extend(runs) or "j")
    jobs.ingest_chain(project, [grande, rodwin])

    passes = [r for r in planned if r["kind"] == "themes"]
    assert [r["material_id"] for r in passes] == [grande, rodwin]
    assert not any(r.get("materials") for r in passes), "no batch rides on an iterative pass"
    assert not any(r["kind"] in ("memo", "residual", "reconcile") for r in planned)


# ---- RESIDUAL -----------------------------------------------------------------------------------

@pytest.fixture
def unread(explored, conn):
    """Grande's papers theme skipped by the gate, as DOC would have left it, and its memo written.
    This is the state RESIDUAL is asked to say something about."""
    store.save_follow(conn, explored["grande"], explored["papers"], "skipped")
    store.save_summary(conn, "material", explored["grande"], "memo", "What the reading found.")
    return explored


def _unmarked(conn, mid: str) -> tuple[str, str]:
    """A passage no code touched, long enough to quote from."""
    marked = _marked(conn, mid)
    for sid, text in store.sentences(conn, mid):
        if sid not in marked and 6 <= len(text.split()) <= 40:
            return sid, text
    raise AssertionError("this material has no usable unmarked passage")


def test_residual_is_shown_the_unmarked_passages_and_nothing_the_coding_touched(unread, conn,
                                                                               model):
    """The remainder it reads is the one no CODE touched — not the one no claim rests on, which is
    a different remainder and a different question. This asks what the coding itself missed."""
    mid = unread["grande"]
    model.queue({"additions": [], "none_for": [], "note": ""})

    residual.run(conn, mid)

    shown = model.shown("residual")
    passages = dict(store.sentences(conn, mid))
    for sid in _marked(conn, mid):
        assert passages[sid] not in shown, "a passage the coding marked is not what it missed"
    sid, text = _unmarked(conn, mid)
    assert text in shown
    assert "What the reading found." in shown, "the memo travels with it, so it does not repeat it"
    assert unread["papers"] in shown and unread["work"] in shown, "the themes, by id"


def test_an_addition_from_the_remainder_becomes_a_verified_moment(unread, conn, model):
    """Anchored and verified like any other claim. It is added BESIDE the line that stands rather
    than replacing it: that line was written and checked minutes ago, and superseding it would
    give every claim of it a new id."""
    mid, tid = unread["grande"], unread["work"]
    sid, text = _unmarked(conn, mid)
    before = store.add_moments(conn, mid, tid, [{"claim": "already here", "sid": sid,
                                                 "anchor": " ".join(text.split()[:6])}])
    model.queue({"additions": [{"theme": tid, "claim": "The stall is what fed them.",
                                "anchor": " ".join(text.split()[:8]), "sid": sid}],
                 "none_for": [], "note": "Mostly the interviewer's questions about dates."})
    model.queue({"verdicts": []})

    out = residual.run(conn, mid)

    assert [c["label"] for c in model.calls] == ["residual", "verify"]
    claims = {m["claim"] for m in store.thread(conn, mid, tid)}
    assert claims == {"already here", "The stall is what fed them."}
    assert {m["id"] for m in store.thread(conn, mid, tid)} >= set(before), \
        "the line that already stood kept its ids"
    # Only the new claim is checked; the rest of the material was checked minutes ago.
    assert "already here" not in model.shown("verify")
    assert store.followed(conn, unread["pid"])[(tid, mid)] == "line"
    assert store.get_summary(conn, "material", mid, "residual")["text"].startswith("Mostly the")
    assert out["additions"] and not out["dropped"]


def test_an_addition_whose_quote_is_not_in_the_remainder_is_thrown_away(unread, conn, model):
    """The anchor law, against the unmarked passages only. A quote found in a passage the coding
    already marked is not something the coding missed."""
    mid = unread["grande"]
    marked = sorted(_marked(conn, mid))[0]
    already = " ".join(dict(store.sentences(conn, mid))[marked].split()[:8])
    model.queue({"additions": [{"theme": unread["work"], "claim": "Lifted from a marked passage.",
                                "anchor": already, "sid": marked}],
                 "none_for": [], "note": ""})

    out = residual.run(conn, mid)

    assert store.thread(conn, mid, unread["work"]) == []
    assert any("unmarked" in d for d in out["dropped"])
    assert [c["label"] for c in model.calls] == ["residual"], "nothing to verify"


def test_a_skip_the_remainder_held_nothing_under_becomes_a_searched_absence(unread, conn, model):
    """The finding this step mostly exists to produce. `residual` is only ever written over
    `skipped`: this pass read the remainder, not the material, and it cannot upgrade a line a
    reader was already sent to find and did not."""
    mid = unread["grande"]
    store.save_follow(conn, mid, unread["work"], "thin")
    model.queue({"additions": [], "none_for": [unread["papers"], unread["work"]], "note": ""})

    out = residual.run(conn, mid)

    outcomes = store.followed(conn, unread["pid"])
    assert outcomes[(unread["papers"], mid)] == "residual", "the gate passed it over; this looked"
    assert outcomes[(unread["work"], mid)] == "thin", "a theme looked for properly is left alone"
    assert out["none_for"] == sorted([unread["papers"], unread["work"]])


def test_the_theme_page_prints_the_searched_absence_as_its_own_kind_of_nothing(unread, conn,
                                                                              monkeypatch):
    """Three silences become four, and a reader must be able to tell them apart: an absence
    nobody looked for and an absence somebody looked for are not the same claim about the world."""
    from fastapi.testclient import TestClient

    from app import context, main, pages
    monkeypatch.setattr(pages, "connection", lambda: conn, raising=False)
    store.save_follow(conn, unread["grande"], unread["papers"], "residual")

    html = TestClient(main.app).get(f'/p/{unread["pid"]}/t/{unread["papers"]}').text
    section = html.split("Materials with no claims under this theme")[-1]
    under = section.split("Searched in the passages the coding did not mark — nothing found")
    assert len(under) == 2, "the heading a searched absence is named under"
    assert store.material(conn, unread["grande"])["title"] in under[1]
    assert "Not looked for here" not in section, "it is no longer that kind of nothing"
    assert context.ASSESSED_SAID["residual"] == \
        "Searched in the passages the coding did not mark — nothing found"


def test_the_account_is_told_that_this_absence_was_searched(unread, conn):
    """What ACCOUNT is shown about a material with no claim under this theme. A model that cannot
    tell a searched absence from an unsearched one writes both up the same way."""
    from app.engine import account
    store.save_follow(conn, unread["grande"], unread["papers"], "residual")
    absent = [{"material_id": unread["grande"], "title": "Grande", "name": "Grande",
               "kind": "interview"}]
    block = account._absent_block(conn, unread["pid"], unread["papers"], absent)
    assert "SEARCHED IN THE PASSAGES THE CODING DID NOT MARK AND NOT FOUND" in block


def test_a_database_made_before_the_fourth_outcome_learns_to_hold_it(tmp_path):
    """A CHECK constraint cannot be altered in place and `CREATE TABLE IF NOT EXISTS` leaves an
    existing table exactly as it was, so an older database would refuse to write `residual` — the
    step would fail on every material of every corpus already in the tool. The rows are copied
    into a table with the new constraint; the constraint itself is not weakened on the way."""
    import sqlite3

    from app import db
    path = tmp_path / "before-the-fourth-outcome.db"
    old = sqlite3.connect(path)
    old.executescript(
        "CREATE TABLE follow (id TEXT PRIMARY KEY, material_id TEXT NOT NULL, "
        "theme_id TEXT NOT NULL, outcome TEXT NOT NULL CHECK (outcome IN "
        "('line','thin','skipped')), run_id TEXT, status TEXT NOT NULL DEFAULT 'live');"
        "INSERT INTO follow VALUES ('f1','m1','t1','skipped','r1','live');"
        "INSERT INTO follow VALUES ('f2','m1','t2','line',NULL,'superseded');")
    old.commit()
    old.close()

    conn = db.connect(path)
    assert [tuple(r) for r in conn.execute("SELECT * FROM follow ORDER BY id")] == \
        [("f1", "m1", "t1", "skipped", "r1", "live"),
         ("f2", "m1", "t2", "line", None, "superseded")], "every row, every column"
    conn.execute("INSERT INTO follow VALUES ('f3','m1','t3','residual',NULL,'live')")
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO follow VALUES ('f4','m1','t4','whatever',NULL,'live')")
    conn.close()


# ---- the chain ----------------------------------------------------------------------------------

def _planned(monkeypatch, pid: str, mids: list[str]) -> list[dict]:
    got: list[dict] = []
    monkeypatch.setattr(jobs, "start", lambda factory, project, runs: got.extend(runs) or "j")
    jobs.ingest_chain(pid, mids)
    return got


def test_the_exploratory_chain_reads_each_material_then_asks_the_corpus_once(explored, conn,
                                                                            monkeypatch):
    """PLAN.md §13's order, executable. Each material framed, read, reconciled and memoed on its
    own; ONE cross-case pass over the batch; then each material's lines and the pass over what its
    coding did not mark; then the corpus level. THEMES per material is exactly what this replaces.
    """
    runs = _planned(monkeypatch, explored["pid"], [explored["grande"], explored["rodwin"]])
    assert [r["kind"] for r in runs] == \
        ["frame", "angles", "read", "reconcile", "memo"] * 2 + \
        ["themes", "doc", "residual", "doc", "residual", "accounts", "project"]

    cross = [r for r in runs if r["kind"] == "themes"]
    assert len(cross) == 1, "one question asked of the corpus, not one per material"
    assert cross[0]["material_id"] is None
    assert cross[0]["materials"] == [explored["grande"], explored["rodwin"]]
    assert jobs.line(conn, cross[0]) == "Finding themes across 2 materials"
    assert jobs.line(conn, {"kind": "memo", "material_id": explored["grande"]}) == \
        "Writing what Grande says on its own terms"
    assert jobs.line(conn, {"kind": "residual", "material_id": explored["grande"]}) == \
        "Reading what the coding did not mark in Grande"


def test_a_material_read_again_carries_the_same_chain_it_arrived_on(explored, conn):
    """A rerun that dropped a step would quietly read the old way. Over a batch of one, the
    cross-case pass takes that one material as its batch."""
    runs = rerun.from_step(explored["grande"], "frame", explore=True)
    assert [r["kind"] for r in runs] == \
        ["frame", "angles", "read", "reconcile", "memo", "themes", "doc", "residual",
         "accounts", "project"]
    cross = [r for r in runs if r["kind"] == "themes"][0]
    assert cross["material_id"] is None and cross["materials"] == [explored["grande"]]


def test_the_residual_pass_can_be_left_out_of_the_chain_entirely(explored, conn, monkeypatch):
    """It is a paid call per material, and §13 puts explore-R4 with and against without it among
    the conditions the evaluation compares. So the harness takes it out with a variable rather
    than with a second chain to keep in step."""
    monkeypatch.setenv("APERTURE_RESIDUAL", "off")
    kinds = [r["kind"] for r in _planned(monkeypatch, explored["pid"], [explored["grande"]])]
    assert kinds == ["frame", "angles", "read", "reconcile", "memo", "themes", "doc",
                     "accounts", "project"]
    assert "residual" not in [r["kind"] for r in
                              rerun.from_step(explored["grande"], "frame", explore=True)]

    monkeypatch.setenv("APERTURE_RESIDUAL", "on")
    assert "residual" in [r["kind"] for r in _planned(monkeypatch, explored["pid"],
                                                      [explored["grande"]])], \
        "anything but 'off' is the chain of §13 entire"
