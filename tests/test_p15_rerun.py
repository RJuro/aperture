"""P15 — running one material's analysis again, because the researcher asked.

    POST /p/{pid}/m/{mid}/rerun   from=structure|angles|coding|themes|synthesis   note=...

PLAN.md §1's third table, executable. This is the one verb that may re-read: feedback never
does, and `test_p4_rerun_jobs` still holds that line. Here the researcher has said *do that
again*, and from where, so re-reading is the point rather than the danger.

Two things the file exists to pin. A second reading REPLACES the first — leave the old code hits
in place and a material's codes and the theme grid count both readings. And a note reaches every
step that takes the researcher's words, verbatim, through the slot each of them already has.
"""
from __future__ import annotations

import pytest

from app import jobs, rerun, store

NOTE = "The bakery is the whole story here; the ship crossing is not."


@pytest.fixture
def app(conn, monkeypatch):
    """The verb's chain is planned but never run: what it asked for is what these tests read."""
    from fastapi.testclient import TestClient

    from app import main, pages, verbs
    monkeypatch.setattr(pages, "connection", lambda: conn)
    monkeypatch.setattr(verbs, "connection", lambda: conn)
    planned = []
    monkeypatch.setattr(jobs, "start", lambda factory, pid, runs: planned.append(list(runs)) or "j")
    client = TestClient(main.app, follow_redirects=False)
    client.planned = planned
    return client


def kinds(runs):
    return [r["kind"] for r in runs]


TAIL = ["accounts", "project"]


# ---- the chain ----------------------------------------------------------------------------------

@pytest.mark.parametrize("sent,expected", [
    ("structure", ["frame", "angles", "read", "themes", "doc"]),
    ("angles", ["angles", "read", "themes", "doc"]),
    ("coding", ["read", "themes", "doc"]),
    ("themes", ["themes", "doc"]),
    ("synthesis", ["doc"]),
])
def test_it_runs_everything_from_the_chosen_step_to_the_end(app, analysed, sent, expected):
    """Everything after the chosen step runs too: a reading that changed with a synthesis still
    written over the old one is worse than either."""
    pid, mid = analysed["pid"], analysed["grande"]
    r = app.post(f"/p/{pid}/m/{mid}/rerun", data={"from": sent})
    assert r.status_code == 303 and r.headers["location"] == f"/p/{pid}/m/{mid}"
    assert kinds(app.planned[-1]) == expected + TAIL
    assert all(x["material_id"] == mid for x in app.planned[-1][:len(expected)])
    assert not any(x["material_id"] for x in app.planned[-1][len(expected):]), \
        "the corpus level is about no one material"


def test_the_names_the_engine_uses_work_too(app, analysed):
    """The page sends what the page calls each step, because two of ours it may not print. The
    engine's own names are the same five steps and are accepted unchanged."""
    pid, mid = analysed["pid"], analysed["grande"]
    for sent in rerun.CHAIN:
        app.post(f"/p/{pid}/m/{mid}/rerun", data={"from": sent})
    assert [kinds(c)[0] for c in app.planned] == list(rerun.CHAIN)


def test_a_step_nobody_has_is_not_a_chain(app, analysed):
    pid, mid = analysed["pid"], analysed["grande"]
    assert app.post(f"/p/{pid}/m/{mid}/rerun", data={"from": "everything"}).status_code == 404
    assert app.post(f"/p/{pid}/m/nope/rerun", data={"from": "coding"}).status_code == 404
    assert app.planned == []


def test_from_the_beginning_is_the_chain_material_arrives_on(app, analysed):
    """"Reset" is not a separate path through the code: it is the upward chain, run again."""
    pid, mid = analysed["pid"], analysed["grande"]
    app.post(f"/p/{pid}/m/{mid}/rerun", data={"from": "structure"})
    assert kinds(app.planned[-1]) == list(rerun.CHAIN) + TAIL


# ---- the note -----------------------------------------------------------------------------------

def test_the_note_is_stored_once_and_rides_every_run(app, analysed, conn):
    pid, mid = analysed["pid"], analysed["grande"]
    app.post(f"/p/{pid}/m/{mid}/rerun", data={"from": "structure", "note": NOTE})
    said = store.feedback_for(conn, "material_summary", mid)
    assert [f["text"] for f in said] == [NOTE], "one note, stored once, in their own words"
    assert {x["feedback_id"] for x in app.planned[-1]} == {said[0]["id"]}


def test_no_note_is_no_comment_on_the_material(app, analysed, conn):
    pid, mid = analysed["pid"], analysed["grande"]
    app.post(f"/p/{pid}/m/{mid}/rerun", data={"from": "coding", "note": "   "})
    assert store.feedback_for(conn, "material_summary", mid) == []
    assert {x["feedback_id"] for x in app.planned[-1]} == {None}


def test_the_note_reaches_the_reading_and_the_ideation_verbatim(conn, analysed, model):
    """Not summarised, not reworded: the researcher's sentence, as they typed it. `_text` hands
    it to each step and each step's own slot delimits it."""
    pid, mid = analysed["pid"], analysed["grande"]
    fid = store.add_feedback(conn, pid, "material_summary", mid, "note", NOTE)
    model.queue({"field": "f", "subareas": [], "angles": []}, {"codes": []})
    jobs.run_now(conn, pid, rerun.from_step(mid, "angles", fid)[:2])
    assert kinds(rerun.from_step(mid, "angles", fid)[:2]) == ["angles", "read"]
    for label in ("angles", "read"):
        assert NOTE in model.shown(label), f"the note never reached {label}"


def test_without_a_note_each_says_the_researcher_said_nothing(conn, analysed, model):
    """The same default the other prompts use, so an empty slot never reads as an instruction."""
    pid, mid = analysed["pid"], analysed["grande"]
    model.queue({"field": "f", "subareas": [], "angles": []}, {"codes": []})
    jobs.run_now(conn, pid, rerun.from_step(mid, "angles")[:2])
    assert "The researcher has said nothing about what to look for here." in model.shown("angles")
    assert "The researcher has said nothing about this reading." in model.shown("read")


def test_the_note_is_still_open_when_the_synthesis_is_written(conn, analysed, model):
    """It rides every run, and is honoured by the last of them. Consumed at the first step it
    would already be gone from the material's open comments by the time the synthesis at the end
    of the same chain reads them — which is the one place a note about a material belongs."""
    pid, mid = analysed["pid"], analysed["grande"]
    fid = store.add_feedback(conn, pid, "material_summary", mid, "note", NOTE)
    model.queue({"codes": []}, {"themes": []},                    # read, themes
                {"moments": []}, {"moments": []},                 # one line per live theme
                {"verdicts": []},                                 # the claims against their passages
                {"summary": "s", "questions": "", "people": []})  # the summary over them
    jobs.run_now(conn, pid, rerun.from_step(mid, "read", fid)[:3])
    assert NOTE in model.shown("doc"), "the synthesis never saw it"
    assert store.feedback_for(conn, "material_summary", mid, open_only=True) == [], \
        "and once answered it is history, not a standing order"


# ---- a second reading replaces the first --------------------------------------------------------

def _coded(sids):
    return {"codes": [{"code": {"name": "Making a living", "definition": "how a living is made"},
                       "sids": sids}]}


def test_two_readings_leave_one_set_of_hits(conn, analysed, model):
    """Read twice, the old hits used to stay: the material's codes and the theme grid counted
    the first reading beside the second, and every derivation over them was wrong."""
    from app.engine import read
    pid, mid = analysed["pid"], analysed["grande"]
    sids = [s for s, _ in store.sentences(conn, mid)[10:14]]
    model.queue(_coded(sids), _coded(sids[:2]))
    read.run(conn, mid)
    assert len(store.hits(conn, mid)) == len(sids)
    read.run(conn, mid)
    assert [h["sid"] for h in store.hits(conn, mid)] == sids[:2], \
        "the second reading replaces the first, it does not join it"
    assert len(store.codebook(conn, pid)) == 1, "and it is the same code, not a second one"


def test_another_materials_coding_is_left_alone(conn, analysed, model):
    from app.engine import read
    pid, grande, rodwin = analysed["pid"], analysed["grande"], analysed["rodwin"]
    store.save_codes(conn, pid, rodwin, [{"name": "Elsewhere", "definition": "d",
                                          "sids": [store.sentences(conn, rodwin)[3][0]]}])
    model.queue(_coded([s for s, _ in store.sentences(conn, grande)[10:12]]))
    read.run(conn, grande)
    assert len(store.hits(conn, rodwin)) == 1


def test_a_code_left_with_nothing_loses_its_place_in_every_theme(conn, analysed, model):
    """Exactly what removing the material does. A theme that still gathered an abandoned code
    would say it rests on evidence that is no longer anywhere."""
    from app.engine import read
    pid, mid = analysed["pid"], analysed["grande"]
    tid = list(analysed["themes"].values())[0]
    store.save_codes(conn, pid, mid, [{"name": "Abandoned", "definition": "d",
                                       "sids": [store.sentences(conn, mid)[5][0]]}])
    cid = [c["id"] for c in store.codebook(conn, pid) if c["name"] == "Abandoned"][0]
    store.save_theme(conn, pid, tid=tid, name="Work and trade", gist="how a living is made",
                     code_ids=[cid])
    assert cid in [c["id"] for c in store.theme_codes(conn, tid)]
    model.queue(_coded([s for s, _ in store.sentences(conn, mid)[10:12]]))
    read.run(conn, mid)
    assert cid not in [c["id"] for c in store.theme_codes(conn, tid)]


# ---- whose material it is -----------------------------------------------------------------------

def test_a_stranger_cannot_run_anybody_elses_analysis(conn, monkeypatch):
    """404, not 403: that this material exists is not theirs to learn either."""
    from fastapi.testclient import TestClient

    from app import accounts, ingest, main, pages, verbs
    for mod in (pages, verbs, accounts):
        monkeypatch.setattr(mod, "connection", lambda: conn, raising=False)
    planned = []
    monkeypatch.setattr(jobs, "start", lambda factory, pid, runs: planned.append(list(runs)) or "j")
    store.create_user(conn, "ann", "battery staple")
    bob = store.create_user(conn, "bob", "purple monkey")
    pid = store.create_project(conn, "Bob's study", "", owner_id=bob)
    mid = store.add_material(conn, pid, "Notes", "First line here. Second line follows on.")
    store.save_sentences(conn, mid, ingest.sentences("First line here. Second line follows on."))

    client = TestClient(main.app, follow_redirects=False)
    client.post("/login", data={"name": "ann", "password": "battery staple"})
    r = client.post(f"/p/{pid}/m/{mid}/rerun", data={"from": "coding", "note": NOTE})
    assert r.status_code == 404
    assert planned == [] and store.feedback_for(conn, "material_summary", mid) == []


# ---- the page -----------------------------------------------------------------------------------

def test_the_page_offers_every_step_the_verb_accepts(app, analysed):
    """A form that offers a step the handler rejects is a button that lies."""
    import re
    html = app.get(f"/p/{analysed['pid']}/m/{analysed['grande']}").text
    assert f"/m/{analysed['grande']}/rerun" in html
    offered = re.findall(r'<option value="([^"]+)"', html)
    assert offered and all(rerun.PAGE_NAMES.get(v, v) in rerun.CHAIN for v in offered)
    assert len(offered) == len(rerun.CHAIN)
    assert 'name="note"' in html
