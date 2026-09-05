"""P27 — saying what was actually assessed, searched, read and kept.

Five silences the app used to fill in with something more confident than it knew:

    a pair with no examination row      was shown as "looked for and found too thin", which is an
                                        absence asserted over a reading that never happened
    a check                             searched only the passages no claim rested on, so the one
                                        sentence that answered the question was the one withheld
    a corpus summary with no accounts   was asked to cite claim ids it had never been shown
    the project's open questions        were whichever material finished writing them last
    "stable for N materials"            counted passes of the grouping step, not materials

Each test here asserts the honest behaviour. The audit's probes (docs/audits/2026-09-05-probes.py)
assert the defects, and the ones covered here are expected to fail against this revision.
"""
from __future__ import annotations

import pytest

from app import context, ingest, store

synth = pytest.importorskip("app.engine.synth")
check = pytest.importorskip("app.engine.check")


@pytest.fixture
def client(conn, monkeypatch):
    from fastapi.testclient import TestClient

    from app import main, pages
    monkeypatch.setattr(main, "conn", conn, raising=False)
    monkeypatch.setattr(pages, "connection", lambda: conn, raising=False)
    return TestClient(main.app)


@pytest.fixture
def union(conn, project):
    """One short material whose answer to a question is already carrying a claim — the audit's
    union case, small enough that every passage is countable."""
    raw = ("I worked at the bakery. We joined a union. My shift began at six. "
           "We voted for a strike. The shop closed on Sunday.")
    mid = store.add_material(conn, project, "Bakery", raw)
    store.save_sentences(conn, mid, ingest.sentences(raw))
    tid = store.save_theme(conn, project, tid=None, name="Work", gist="paid work", code_ids=[])
    sid, text = store.sentences(conn, mid)[1]
    assert "union" in text
    store.save_moments(conn, mid, tid, [{"claim": "She joined a union.", "anchor": "We joined a union",
                                         "sid": sid}])
    return {"pid": project, "mid": mid, "tid": tid, "sid": sid}


# ---- not assessed is a state -------------------------------------------------------------------

def test_a_pair_with_no_examination_row_is_not_assessed_rather_than_looked_for(conn, analysed):
    """`store.followed` has no entry for a material never read for a theme — a file uploaded
    since, or a theme worked out since — and every reader of it must say so."""
    pid, tid = analysed["pid"], list(analysed["themes"].values())[0]
    conn.execute("UPDATE moment SET status='superseded' WHERE material_id=? AND theme_id=?",
                 (analysed["rodwin"], tid))
    conn.commit()
    assert (tid, analysed["rodwin"]) not in store.followed(conn, pid)

    absent = context.theme_page(conn, pid, tid)["absent"]
    assert [m["assessed"] for m in absent] == [None]
    exported = [t for t in context.export(conn, pid)["themes"] if t["id"] == tid][0]
    assert [m["assessed"] for m in exported["absent"]] == [None]

    store.save_follow(conn, analysed["rodwin"], tid, "thin", None)
    assert [m["assessed"] for m in context.theme_page(conn, pid, tid)["absent"]] == ["thin"]
    store.save_follow(conn, analysed["rodwin"], tid, "skipped", None)
    assert [m["assessed"] for m in context.theme_page(conn, pid, tid)["absent"]] == ["skipped"]


HEADS = {None: "Not assessed yet", "thin": "Looked for and found too thin",
         "skipped": "Not looked for here"}


@pytest.mark.parametrize("outcome", list(HEADS))
def test_the_three_silences_have_their_own_headings_on_every_surface(client, conn, analysed,
                                                                    outcome):
    pid, tid = analysed["pid"], list(analysed["themes"].values())[0]
    conn.execute("UPDATE moment SET status='superseded' WHERE material_id=? AND theme_id=?",
                 (analysed["rodwin"], tid))
    conn.commit()
    if outcome:
        store.save_follow(conn, analysed["rodwin"], tid, outcome, None)
    rodwin, head = store.material(conn, analysed["rodwin"]), HEADS[outcome]
    others = set(HEADS.values()) - {head}
    for url in (f"/p/{pid}/t/{tid}", f"/p/{pid}/record", f"/p/{pid}/export.md"):
        page = client.get(url).text
        section = page.split("Materials where this theme appears")[-1]
        assert head in section, url
        assert rodwin["title"] in section, url
        for other in others:
            assert other not in section, f"{other!r} beside {head!r} on {url}"
    if outcome is None:
        assert "Not assessed yet — not read for this theme" in client.get(f"/p/{pid}/t/{tid}").text


def test_an_empty_cell_in_the_overview_says_which_kind_of_nothing_it_is(client, conn, analysed):
    """A dash has no room for a sentence, so it carries one: three different findings looked
    identical in that column."""
    pid, tid = analysed["pid"], list(analysed["themes"].values())[0]
    conn.execute("UPDATE moment SET status='superseded' WHERE material_id=? AND theme_id=?",
                 (analysed["rodwin"], tid))
    conn.commit()
    assert 'title="Not assessed yet — this material was not read for this theme">—' \
        in client.get(f"/p/{pid}").text
    store.save_follow(conn, analysed["rodwin"], tid, "skipped", None)
    assert 'title="Not looked for here — none of this theme&#39;s codes marked this material">—' \
        in client.get(f"/p/{pid}").text


# ---- a check searches what it was asked to -------------------------------------------------------

def test_a_check_searches_every_passage_by_default(union, conn, model):
    """The defect this replaces: "did they join a union?" came back not found on a material whose
    second sentence says they did, because that sentence was already carrying a claim."""
    model.queue({"found": [{"anchor": "We joined a union", "sid": union["sid"]}]})
    out = check.run(conn, union["pid"], "material", union["mid"], "Did they join a union?")
    assert "We joined a union." in model.shown("check")
    assert out["verdict"] == "found" and out["searched_n"] == 5
    assert out["searched_scope"] == "all"


def test_the_unused_scope_still_holds_back_what_is_already_claimed(union, conn, model):
    model.queue({"found": []})
    out = check.run(conn, union["pid"], "material", union["mid"], "Did they join a union?",
                    "unused")
    assert "We joined a union." not in model.shown("check")
    assert out["searched_n"] == 4 and out["searched_scope"] == "unused"


def test_the_prompt_says_which_set_of_passages_it_is_looking_at(union, conn, model):
    model.queue({"found": []}, {"found": []})
    check.run(conn, union["pid"], "material", union["mid"], "Anything about a union?")
    check.run(conn, union["pid"], "material", union["mid"], "Anything about a union?", "unused")
    first, second = [c["system"] + c["user"] for c in model.calls]
    assert "nothing has been held back from you" in first
    assert "no claim currently rests on" in second


def test_a_result_says_which_passages_were_searched_and_never_claims_the_material_has_none(
        client, union, conn, model):
    model.queue({"found": []}, {"found": []})
    check.run(conn, union["pid"], "material", union["mid"], "Is a church mentioned?")
    check.run(conn, union["pid"], "material", union["mid"], "Is a church mentioned?", "unused")
    said = [c["said"] for c in context._checks(conn, union["pid"])]
    assert said == ["nothing found — searched 5 of 5 passages",
                    "nothing found — searched 4 passages not yet cited"]
    for url in (f'/p/{union["pid"]}', f'/p/{union["pid"]}/record', f'/p/{union["pid"]}/export.md'):
        page = client.get(url).text
        assert "nothing found — searched 5 of 5 passages" in page, url
        assert "nothing found — searched 4 passages not yet cited" in page, url


def test_the_form_sends_a_scope_and_anything_else_searches_everything(client, conn, union,
                                                                     monkeypatch):
    """A scope this app does not have must widen the search, never narrow it."""
    from app import verbs
    planned: list[list[dict]] = []
    monkeypatch.setattr(verbs.jobs, "start", lambda f, pid, runs: planned.append(list(runs)) or "j")
    for sent, wanted in (("unused", "unused"), ("all", "all"), ("everything", "all"), (None, "all")):
        data = {"question": "Did they join a union?", "material_id": union["mid"]}
        if sent is not None:
            data["scope"] = sent
        client.post(f'/p/{union["pid"]}/check', data=data)
        assert [r["scope"] for r in planned[-1]] == [wanted], sent
    page = client.get(f'/p/{union["pid"]}/m/{union["mid"]}').text
    assert 'name="scope" value="all" checked' in page and 'name="scope" value="unused"' in page


# ---- a corpus summary with no accounts -----------------------------------------------------------

def _candidate(conn, pid, mid, quote, name="Bakery work"):
    tid = store.save_theme(conn, pid, tid=None, name=name, gist="a living", code_ids=[])
    store.set_hold(conn, tid, "candidate")
    sid, text = quote(mid, at=40)
    store.save_moments(conn, mid, tid, [{"claim": f"{name}: a claim", "sid": sid,
                                         "anchor": " ".join(text.split()[:8])}])
    return tid


def test_a_candidate_only_project_is_given_the_claims_its_summary_must_cite(conn, project, grande,
                                                                           quote, model):
    """One material, candidates only, so no theme has an account. The prompt requires every
    statement to cite a claim id; it used to be handed prose summaries and nothing to cite."""
    store.save_summary(conn, "material", grande, "reading", "The reading found work.")
    _candidate(conn, project, grande, quote)
    model.queue({"summary": "Work runs through it.", "interpretation": ""})
    synth.project(conn, project)
    shown = model.shown("project")
    for m in store.moments(conn, grande):
        assert m["id"] in shown and m["anchor"] in shown


def test_a_material_no_account_speaks_for_still_reaches_the_corpus_summary(conn, project, grande,
                                                                          rodwin, quote, model):
    """With accounts the inputs are unchanged — and a material whose only evidence is a candidate
    is otherwise a paragraph of prose with nothing under it."""
    tid = store.save_theme(conn, project, tid=None, name="Work", gist="a living", code_ids=[])
    sid, text = quote(grande, at=40)
    store.save_moments(conn, grande, tid, [{"claim": "carried", "sid": sid,
                                            "anchor": " ".join(text.split()[:8])}])
    store.save_summary(conn, "theme", tid, "reading", "ACCOUNT: where this theme holds.")
    _candidate(conn, project, rodwin, quote, name="Rodwin motif")

    model.queue({"summary": "Work runs through it.", "interpretation": ""})
    synth.project(conn, project)
    shown = model.shown("project")
    assert "ACCOUNT: where this theme holds." in shown
    assert store.moments(conn, rodwin)[0]["id"] in shown, "the material no account speaks for"
    assert store.moments(conn, grande)[0]["id"] not in shown, "the account already carries it"


# ---- the questions register ------------------------------------------------------------------

@pytest.mark.parametrize("order", [(0, 1), (1, 0)])
def test_both_materials_questions_survive_whichever_reading_finishes_last(conn, project, grande,
                                                                         rodwin, model, order):
    """The old brief was one column for the whole project, so two readings side by side left only
    the later writer's questions: project memory depended on completion order."""
    store.save_theme(conn, project, tid=None, name="Work", gist="a living", code_ids=[])
    mats = [grande, rodwin]
    for i in order:
        store.save_frame(conn, mats[i], kind="interview", display="turns", title=f"M{i}",
                         speakers=[], segments=[])
        model.queue({"moments": []},
                    {"summary": f"reading {i}", "questions": f"question {i}?", "people": []})
        synth.doc(conn, mats[i])

    text = store.questions_text(conn, project)
    assert "question 0?" in text and "question 1?" in text
    # Newest first, and labelled with the material that asked, so a question can be followed up.
    assert text.startswith(f"From M{order[-1]}")
    assert [q["material"] for q in store.open_questions(conn, project)] \
        == [f"M{order[-1]}", f"M{order[0]}"]


def test_open_questions_are_never_handed_over_as_a_materials_description(conn, project, grande):
    """Law 5. The stageless summary lookup feeds prompt slots that hold what the material is;
    questions are what the reading has left open, and are read only through the register."""
    store.save_summary(conn, "material", grande, "questions", "SELF-PROMPT what to look for next")
    assert store.get_summary(conn, "material", grande) is None


def test_the_questions_reach_ideation_and_the_record(conn, project, grande, rodwin, client, model):
    from app.engine import angles

    store.save_frame(conn, grande, kind="interview", display="turns", title="G", speakers=[],
                     segments=[])
    store.save_summary(conn, "material", grande, "questions", "what became of the sisters?")
    for url in (f"/p/{project}", f"/p/{project}/record", f"/p/{project}/export.md"):
        assert "what became of the sisters?" in client.get(url).text, url

    model.queue({"field": "labour history", "subareas": [], "angles": []})
    angles.run(conn, rodwin)
    assert "what became of the sisters?" in model.shown("angles")


def test_a_project_read_before_questions_were_kept_per_material_keeps_its_own(conn, project,
                                                                             grande, client):
    """The legacy column still reads, until a material writes questions of its own."""
    store.set_brief(conn, project, "the questions of an older project")
    assert store.questions_text(conn, project) == "the questions of an older project"
    assert "the questions of an older project" in client.get(f"/p/{project}/record").text
    store.save_summary(conn, "material", grande, "questions", "what the reading asks now")
    assert store.questions_text(conn, project) == "From DP-40 Grande: what the reading asks now"


def test_the_register_is_capped_and_says_so_in_whole_questions(conn, project, grande, rodwin):
    """The cap is allocated across the materials and each share is cut at a whole question, so a
    long register loses questions rather than ending in the middle of one (test_p34)."""
    store.save_summary(conn, "material", grande, "questions", "What became of the sisters? " * 60)
    store.save_summary(conn, "material", rodwin, "questions", "Who paid for the crossing? " * 60)
    out = store.open_questions(conn, project)
    assert sum(len(q["text"].split()) for q in out) <= store.QUESTION_WORDS
    assert not any("…" in q["text"] for q in out)
    assert len(out) == 2, "a capped register still names both materials"


# ---- a sparse line is shown as one ---------------------------------------------------------------

def test_a_line_under_the_floor_is_rendered_as_sparse(client, conn, analysed):
    """The reading keeps a line of one to three claims rather than dropping it whole, so the page
    has to say it is short: three claims and thirty read the same otherwise."""
    pid, mid = analysed["pid"], analysed["grande"]
    tid = list(analysed["themes"].values())[0]
    assert len(store.thread(conn, mid, tid)) < synth.MIN_MOMENTS
    cards = context.material_page(conn, pid, mid)["cards"]
    assert [c["sparse"] for c in cards if c["id"] == tid] == [True]
    assert "sparse · 3 claims" in client.get(f"/p/{pid}/m/{mid}").text
    assert "sparse · 3 claims" in client.get(f"/p/{pid}/record").text

    store.save_moments(conn, mid, tid, [{"claim": f"claim {i}", "sid": m["sid"],
                                         "anchor": m["anchor"]}
                                        for i, m in enumerate(store.thread(conn, mid, tid))
                                        for _ in range(2)][:synth.MIN_MOMENTS])
    cards = context.material_page(conn, pid, mid)["cards"]
    assert [c["sparse"] for c in cards if c["id"] == tid] == [False]
