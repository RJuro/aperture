"""P33 — consolidate: the theme set compared against the whole corpus, once, on purpose.
PLAN.md §14.

    store.backfill_cells   the (theme, material) cells nobody read for a theme two cases carry
    store.settle_holds     the count rule, run when the looking is finished — `OPEN_AT`
    rerun.consolidate_plan the four movements: compare · back-fill · count · write up
    themes.CONSOLIDATING   the one sentence the ceiling slot carries from this route and no other
    synth._candidate_claims a proposed candidate's evidence reaching the corpus summary

An eight-material record is why this file exists: 28 themes and 748 claims, three of them open and
twenty-five candidates, fourteen resting on one material and three of them about language. The
corpus summary was written over the three. Nothing was broken — the chain revises the set one
material at a time and never goes back, promotion is the researcher's, and accounts are for open
and frozen themes only. The verb that asks how the set stands *as a set* simply did not exist.
"""
from __future__ import annotations

import pytest

from app import context, ingest, jobs, rerun, store

synth = pytest.importorskip("app.engine.synth")
themes = pytest.importorskip("app.engine.themes")


# ---- a corpus with holes in it -------------------------------------------------------------------

def _material(conn, pid: str, n: int) -> str:
    """One short material. Real ingestion, invented text: nothing here is about what the reading
    finds, only about which cells were never read at all."""
    text = (f"SPEAKER: Material {n} begins here. The work was hard and the days were long. "
            "They left in the spring and did not come back.")
    mid = store.add_material(conn, pid, f"Material {n}", text)
    store.save_sentences(conn, mid, ingest.sentences(text))
    return mid


def _line(conn, mid: str, tid: str) -> str:
    """A live claim under this theme in this material, and the follow row that says a line holds
    — which is what makes the material one of the cases carrying it."""
    sid, text = store.sentences(conn, mid)[1]
    store.save_moments(conn, mid, tid, [{"claim": f"a claim about {tid}",
                                         "anchor": " ".join(text.split()[:6]), "sid": sid}])
    store.save_follow(conn, mid, tid, "line")
    return store.thread(conn, mid, tid)[0]["id"]


@pytest.fixture
def corpus(conn, project):
    """Six materials, two candidates. `wide` holds a line in two of them; `narrow` in one.

    The holes are the point: `wide` was skipped in one material, found too thin in another, and
    was never assessed at all in the last two.
    """
    mids = [_material(conn, project, n) for n in range(6)]
    wide = store.save_theme(conn, project, tid=None, name="Wide", gist="in two so far",
                            code_ids=[])
    narrow = store.save_theme(conn, project, tid=None, name="Narrow", gist="in one so far",
                              code_ids=[])
    for t in (wide, narrow):
        store.set_hold(conn, t, "candidate")
    _line(conn, mids[0], wide)
    _line(conn, mids[1], wide)
    _line(conn, mids[0], narrow)
    store.save_follow(conn, mids[2], wide, "skipped")
    store.save_follow(conn, mids[3], wide, "thin")
    return {"pid": project, "mids": mids, "wide": wide, "narrow": narrow}


# ---- what the preview promises -------------------------------------------------------------------

def test_the_preview_counts_the_cells_nobody_read_for_a_theme_two_cases_carry(corpus, conn):
    """Not assessed and not looked for are the two cells a consolidation goes back for. A line
    that was looked for and found too thin is a finding and is left alone; a theme one case
    carries is one material's motif and does not send a reader through the corpus after it."""
    cells = store.backfill_cells(conn, corpus["pid"])
    mids = corpus["mids"]
    assert cells == [(corpus["wide"], mids[2]),      # skipped — never looked for
                     (corpus["wide"], mids[4]),      # no row at all
                     (corpus["wide"], mids[5])]
    assert not [c for c in cells if c[0] == corpus["narrow"]], "one case carries it"
    assert (corpus["wide"], mids[3]) not in cells, "thin is an answer, not a hole"

    said = context.project_page(conn, corpus["pid"])["consolidate"]
    assert said == "2 themes to compare · 3 cells to read (about 4 model calls)"


def test_the_control_is_offered_only_when_it_would_do_something(conn, project):
    """A project with one theme, read everywhere, has nothing to compare and no hole to fill —
    and a paid verb that would change nothing must not be on the page asking to be pressed."""
    mid = _material(conn, project, 0)
    tid = store.save_theme(conn, project, tid=None, name="Only", gist="g", code_ids=[])
    _line(conn, mid, tid)
    assert context.project_page(conn, project)["consolidate"] == "", "nothing to do"

    second = store.save_theme(conn, project, tid=None, name="Other", gist="g", code_ids=[])
    for t in (tid, second):
        store.set_hold(conn, t, "candidate")
    said = context.project_page(conn, project)["consolidate"]
    assert said.startswith("2 themes to compare · 0 cells"), "two candidates are worth comparing"


# ---- the plan -----------------------------------------------------------------------------------

def test_the_plan_compares_reads_every_counted_cell_then_counts_and_writes_up(corpus, conn):
    """The shape of it, and the promise the preview made: the plan produces exactly the cells the
    page printed, each of them scoped to one theme."""
    plan = rerun.consolidate_plan(conn, corpus["pid"], "the language themes are one")
    assert [r["kind"] for r in plan] == (
        ["consolidate"] + ["doc"] * 3 + ["summary"] * 3 + ["settle", "accounts", "project"])
    assert plan[0]["note"] == "the language themes are one"
    assert all(r["theme_id"] == corpus["wide"] for r in plan if r["kind"] == "doc")
    assert ([(r["theme_id"], r["material_id"]) for r in plan if r["kind"] == "doc"]
            == store.backfill_cells(conn, corpus["pid"])), "the preview's count is this count"
    # A note is about the theme set; fifty line calls cannot fold anything, so none is shown it.
    assert not [r for r in plan[1:] if r.get("note")]
    # Every kind is an ordinary run kind, so a restart resumes this like any other chain.
    assert not {r["kind"] for r in plan} - set(jobs.STEPS)


def test_an_exploring_project_rewrites_no_material_summary(corpus, conn):
    """Its account of a material is the memo, written over passages rather than over lines, so a
    back-filled line does not go stale under it. An iterative project's summary does."""
    store.set_method(conn, corpus["pid"], "explore")
    plan = rerun.consolidate_plan(conn, corpus["pid"])
    assert [r["kind"] for r in plan] == (
        ["consolidate"] + ["doc"] * 3 + ["settle", "accounts", "project"])


# ---- the pass itself ---------------------------------------------------------------------------

def test_only_a_consolidation_asks_the_model_to_fold(corpus, conn, model):
    """The cross-case pass is unchanged; what a consolidation adds is one sentence in the ceiling
    slot, because here a fold is what the researcher asked for rather than what the cap forces."""
    model.queue({"themes": [], "candidates": []})
    themes.run_cross(conn, corpus["pid"], corpus["mids"])
    assert themes.CONSOLIDATING not in model.shown("themes")

    model.calls.clear()
    model.queue({"themes": [], "candidates": []})
    themes.run_cross(conn, corpus["pid"], corpus["mids"], consolidating=True)
    shown = model.shown("themes")
    assert themes.CONSOLIDATING in shown
    assert "merge_into" in shown and "still a candidate here" in shown


def test_a_fold_carries_its_lines(corpus, conn, model):
    """Merged, never deleted (`store.merge_theme`): a claim written under the theme that was
    folded away still resolves, now under the one it was folded into."""
    wide, narrow = corpus["wide"], corpus["narrow"]
    mid = corpus["mids"][0]
    moved = store.thread(conn, mid, narrow)[0]["id"]
    model.queue({"themes": [{"id": narrow, "merge_into": wide}], "candidates": []})

    out = themes.run_cross(conn, corpus["pid"], corpus["mids"], consolidating=True)

    assert out["merged"] == [narrow]
    assert moved in [m["id"] for m in store.thread(conn, mid, wide)], "the line went with it"
    assert store.thread(conn, mid, narrow) == []
    folded = conn.execute("SELECT status, merged_into FROM theme WHERE id=?", (narrow,)).fetchone()
    assert (folded["status"], folded["merged_into"]) == ("merged", wide), "merged, never deleted"


def test_a_back_filled_cell_is_looked_for_whatever_the_codes_say(corpus, conn, model, monkeypatch):
    """The cell is a person asking, so the gate is off (PLAN.md §3, law 2) — this theme gathers no
    code that fired in this material and the line is written all the same. What comes back is a
    line, or thin where the answer held nothing; never 'not looked for' again."""
    monkeypatch.setenv("APERTURE_FOLLOW", "marked")
    pid, mid = corpus["pid"], corpus["mids"][4]
    _sid, text = store.sentences(conn, mid)[1]
    model.queue({"moments": [{"claim": "the days were long", "sid": _sid,
                              "anchor": " ".join(text.split()[:6])}], "summary": "a line"})
    model.queue({"verdicts": []})

    jobs.run_now(conn, pid, [{"kind": "doc", "material_id": mid, "theme_id": corpus["wide"]}])

    assert [c["label"] for c in model.calls] == ["thread", "verify"]
    assert store.followed(conn, pid)[(corpus["wide"], mid)] == "line"
    assert store.thread(conn, mid, corpus["wide"]), "and the claim is there to read"


def test_a_cell_that_was_looked_for_and_held_nothing_is_thin_and_not_a_hole(corpus, conn, model):
    """The four silences stay four. A cell read by the back-fill and found empty is an absence
    somebody went and looked for, and the next consolidation leaves it alone."""
    pid, mid = corpus["pid"], corpus["mids"][5]
    model.queue({"moments": [], "summary": ""})
    synth.doc(conn, mid, only_theme=corpus["wide"])
    assert store.followed(conn, pid)[(corpus["wide"], mid)] == "thin"
    assert (corpus["wide"], mid) not in store.backfill_cells(conn, pid)


# ---- the count rule ------------------------------------------------------------------------------

def test_the_count_opens_a_candidate_half_the_cases_carry_and_only_proposes_the_rest(corpus, conn):
    """`OPEN_AT` is half, rounded up, never fewer than two — six materials, so three. This is the
    only place a count promotes, and it may because the looking has just finished: every cell a
    two-case theme had never been read in has been read by the time this runs."""
    pid, mids = corpus["pid"], corpus["mids"]
    _line(conn, mids[2], corpus["wide"])                  # a third case carries it
    assert store.OPEN_AT == 0.5

    said = store.settle_holds(conn, pid)

    assert said["opened"] == [corpus["wide"]]
    assert store.live_themes(conn, pid)[0]["id"] == corpus["wide"], "it is a project theme now"
    left = {t["id"]: t for t in store.candidates(conn, pid)}
    assert corpus["narrow"] in left and not left[corpus["narrow"]]["proposed_at"], "one case only"

    # And two cases is still a question: proposed, not opened.
    _line(conn, mids[1], corpus["narrow"])
    said = store.settle_holds(conn, pid)
    assert said["opened"] == [] and said["proposed"] == [corpus["narrow"]]
    assert store.candidates(conn, pid)[0]["hold"] == "candidate"


def test_the_count_never_touches_a_hold_the_researcher_set(corpus, conn):
    """A frozen theme is the researcher's declaration and an open one is their promotion. Neither
    is undone by arithmetic, whatever the corpus now carries."""
    pid = corpus["pid"]
    store.set_hold(conn, corpus["wide"], "frozen")
    store.set_hold(conn, corpus["narrow"], "open")

    store.settle_holds(conn, pid)

    holds = {t["id"]: t["hold"] for t in store.live_themes(conn, pid)}
    assert holds[corpus["wide"]] == "frozen"
    assert holds[corpus["narrow"]] == "open", "one case, and still the researcher's theme"


def test_two_materials_of_one_case_are_one_case_here_too(corpus, conn):
    """Everything that counts recurrence counts cases (`store.carried_cases`). Two files from one
    participant carrying a candidate are one case saying it twice."""
    pid, mids = corpus["pid"], corpus["mids"]
    store.add_case(conn, pid, "Participant one", [mids[0], mids[1]])

    assert store.settle_holds(conn, pid) == {"opened": [], "proposed": []}
    assert not [t for t in store.candidates(conn, pid) if t["proposed_at"]]
    assert store.backfill_cells(conn, pid) == [], "and there is no two-case theme to back-fill"


# ---- what the corpus summary now sees -----------------------------------------------------------

def test_the_corpus_summary_reads_a_proposed_candidates_claims_even_beside_an_account(corpus, conn,
                                                                                      model):
    """Accounts are written for open and frozen themes only, so a candidate in seven of eight
    materials was in this prompt nowhere at all — and PROJECT may state nothing it cannot cite.
    Its claims go in as claims, by id, never as an account's conclusions."""
    pid, mids = corpus["pid"], corpus["mids"]
    opened = store.save_theme(conn, pid, tid=None, name="Open", gist="promoted", code_ids=[])
    for mid in (mids[0], mids[1]):
        _line(conn, mid, opened)
    store.save_summary(conn, "theme", opened, "reading", "What this theme amounts to.")
    assert store.propose_by_recurrence(conn, pid) == [corpus["wide"]], "two cases: a question"
    carried = [m["id"] for m in store.moments(conn, mids[0]) if m["theme_id"] == corpus["wide"]]
    assert carried, "the candidate holds a claim in a material the account already speaks for"

    model.queue({"summary": "The corpus shows one thing.", "interpretation": ""})
    synth.project(conn, pid)

    shown = model.shown("project")
    for cid in carried:
        assert cid in shown, "a proposed candidate's evidence reaches the corpus summary"


def test_an_unproposed_candidate_still_only_fills_the_gaps(corpus, conn, model):
    """One case is not a pattern the corpus repeated. Its claims are still the only evidence for a
    material no account speaks for — that rule is unchanged — but they do not follow it into a
    material an account already covers."""
    pid, mids = corpus["pid"], corpus["mids"]
    opened = store.save_theme(conn, pid, tid=None, name="Open", gist="promoted", code_ids=[])
    _line(conn, mids[0], opened)
    store.save_summary(conn, "theme", opened, "reading", "What this theme amounts to.")
    narrow_claim = [m["id"] for m in store.moments(conn, mids[0])
                    if m["theme_id"] == corpus["narrow"]]

    model.queue({"summary": "The corpus shows one thing.", "interpretation": ""})
    synth.project(conn, pid)

    assert narrow_claim and narrow_claim[0] not in model.shown("project")


# ---- who may press it ---------------------------------------------------------------------------

@pytest.fixture
def client(conn, monkeypatch):
    from fastapi.testclient import TestClient

    from app import accounts, main, pages, verbs
    for mod in (pages, verbs, accounts):
        monkeypatch.setattr(mod, "connection", lambda: conn, raising=False)
    return TestClient(main.app, follow_redirects=False)


def _login(client, name: str, password: str) -> None:
    assert client.post("/login", data={"name": name, "password": password}).status_code == 303


def test_a_member_who_may_only_read_cannot_start_it(conn, client):
    """It is a paid verb that rewrites the theme set, so it takes editing the project. A project
    that is not yours to change is 404, not 403 — the refusal says nothing about what is there."""
    ann = store.create_user(conn, "ann", "battery staple")
    bob = store.create_user(conn, "bob", "purple monkey")
    pid = store.create_project(conn, "Ann's study", owner_id=ann, method="iterative")
    token = store.add_invite(conn, pid, "read", ann)
    _login(client, "bob", "purple monkey")
    store.join(conn, token, bob)

    assert client.get(f"/p/{pid}").status_code == 200, "reading it is fine"
    assert client.post(f"/p/{pid}/compare", data={"note": ""}).status_code == 404


def test_the_owner_starts_one_chain_and_lands_back_on_the_themes(conn, client, monkeypatch):
    """Redirect after post, like every other verb: a refresh must not buy the corpus twice."""
    started: list = []
    monkeypatch.setattr(jobs, "start", lambda factory, pid, runs: started.append(runs) or "job1")
    ann = store.create_user(conn, "ann", "battery staple")
    pid = store.create_project(conn, "Ann's study", owner_id=ann, method="iterative")
    mid = _material(conn, pid, 0)
    tid = store.save_theme(conn, pid, tid=None, name="Wide", gist="g", code_ids=[])
    store.set_hold(conn, tid, "candidate")
    _line(conn, mid, tid)
    _line(conn, _material(conn, pid, 1), tid)
    _material(conn, pid, 2)                     # never read for this theme: one cell to fill
    _login(client, "ann", "battery staple")

    r = client.post(f"/p/{pid}/compare", data={"note": "fold the language themes"})

    assert r.status_code == 303 and r.headers["location"] == f"/p/{pid}#themes"
    assert len(started) == 1 and started[0][0]["kind"] == "consolidate"
    assert started[0][0]["note"] == "fold the language themes"


def test_the_page_offers_it_in_the_researchers_words(conn, client):
    """`consolidate` is our word for this (`context._BANNED`) and a form's action attribute is on
    the page like anything else, so neither the control nor the path says it."""
    import re

    from tests.test_p5_pages import strip_material

    ann = store.create_user(conn, "ann", "battery staple")
    pid = store.create_project(conn, "Ann's study", owner_id=ann, method="iterative")
    mid = _material(conn, pid, 0)
    tid = store.save_theme(conn, pid, tid=None, name="Wide", gist="g", code_ids=[])
    store.set_hold(conn, tid, "candidate")
    _line(conn, mid, tid)
    _line(conn, _material(conn, pid, 1), tid)
    _material(conn, pid, 2)                     # never read for this theme: one cell to fill
    _login(client, "ann", "battery staple")

    html = client.get(f"/p/{pid}").text
    assert "Compare every theme across the corpus" in html
    assert "1 cell to read (about 2 model calls)" in html
    said = strip_material(html).lower()
    for word in context._BANNED:
        assert not re.search(rf"\b{re.escape(word)}s?\b", said), f"{word!r} on the project page"


def test_nothing_here_ever_reaches_a_model_by_accident(corpus, conn):
    """The count rule and the plan are arithmetic over rows. A researcher who presses this and
    then looks at the preview again must not have paid for the looking."""
    store.settle_holds(conn, corpus["pid"])
    rerun.consolidate_plan(conn, corpus["pid"], "")
    context.project_page(conn, corpus["pid"])
