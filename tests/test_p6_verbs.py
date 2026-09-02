"""P6 — the four verbs, wired. Every form on every page must reach a handler that writes a row
and plans the right runs.

The runs are never actually executed here: `jobs.start` is replaced, and what it was asked to run
is what these tests read. That keeps the whole suite offline while still pinning the thing that
matters — that a click on this page starts exactly that work and no more.
"""
from __future__ import annotations

import pytest

from app import store


@pytest.fixture
def app(conn, monkeypatch):
    from fastapi.testclient import TestClient

    from app import jobs, main, pages, verbs
    monkeypatch.setattr(pages, "connection", lambda: conn)
    monkeypatch.setattr(verbs, "connection", lambda: conn)
    planned = []
    monkeypatch.setattr(jobs, "start", lambda factory, pid, runs: planned.append(list(runs)) or "j")
    monkeypatch.setattr(verbs.jobs, "start", jobs.start)
    monkeypatch.setattr(verbs.jobs, "ingest_chain",
                        lambda pid, mid, **k: planned.append([{"kind": "chain",
                                                               "material_id": mid}]) or "j")
    client = TestClient(main.app, follow_redirects=False)
    client.planned = planned
    return client


def kinds(planned):
    return [[r["kind"] for r in chain] for chain in planned]


def test_every_form_on_every_page_reaches_a_handler(app, analysed):
    """A form that posts to nothing is a button that lies. This walks the actions the pages
    actually render and asserts none of them 404."""
    import re
    seen = set()
    for url in (f"/p/{analysed['pid']}", f"/p/{analysed['pid']}/m/{analysed['grande']}", "/"):
        html = app.get(url).text
        seen |= set(re.findall(r'<form[^>]*action="([^"]+)"', html))
    assert seen, "no forms rendered — this test is not looking at the right pages"
    routes = [r for r in __import__("app.main", fromlist=["x"]).app.routes]
    posts = {getattr(r, "path", "") for r in routes if "POST" in getattr(r, "methods", set())}
    for action in seen:
        # A literal route wins; otherwise put the ids back into their placeholders and look again.
        pattern = re.sub(r"/m/[^/]+", "/m/{mid}", re.sub(r"/p/p[^/]*", "/p/{pid}", action))
        assert action in posts or pattern in posts, \
            f"{action} posts to nothing (also looked for {pattern})"


def test_adding_material_cuts_sentences_before_the_reading_starts(app, project, conn):
    r = app.post(f"/p/{project}/material",
                 data={"name": "Notes", "text": "First line here.\nSecond line follows on."})
    assert r.status_code == 303
    mid = store.materials(conn, project)[-1]["id"]
    assert store.sentences(conn, mid), "ids must exist before anything can cite them"
    assert kinds(app.planned) == [["chain"]]


def test_doubt_on_a_claim_goes_and_looks_instead_of_rewriting(app, analysed, conn):
    app.post(f"/p/{analysed['pid']}/react",
             data={"kind": "doubt", "claim_id": analysed["moment"], "text": "I don't buy it"})
    assert kinds(app.planned) == [["check"]]
    fb = store.project_feedback(conn, analysed["pid"])[-1]
    assert (fb["target_kind"], fb["kind"], fb["text"]) == ("moment", "doubt", "I don't buy it")


def test_agreement_records_and_runs_nothing(app, analysed, conn):
    app.post(f"/p/{analysed['pid']}/react",
             data={"kind": "agree", "claim_id": analysed["moment"]})
    assert app.planned == []
    assert store.project_feedback(conn, analysed["pid"])[-1]["kind"] == "agree"


def test_the_form_fields_say_which_target_without_naming_it(app, analysed, conn):
    """No hidden field says 'thread' or 'moment' — those words are banned from the page — so the
    target is read from which fields arrived. Each shape must land on the right one."""
    pid, mid = analysed["pid"], analysed["grande"]
    tid = list(analysed["themes"].values())[0]
    for data, expect in (
        ({"kind": "note", "text": "x", "claim_id": analysed["moment"]}, "moment"),
        ({"kind": "note", "text": "x", "theme_id": tid, "material_id": mid}, "thread"),
        ({"kind": "note", "text": "x", "theme_id": tid}, "theme"),
        ({"kind": "note", "text": "x", "material_id": mid}, "material_summary"),
        ({"kind": "note", "text": "x"}, "project_summary"),
    ):
        app.post(f"/p/{pid}/react", data=data)
        assert store.project_feedback(conn, pid)[-1]["target_kind"] == expect


def test_feedback_on_the_project_summary_re_synthesises_everything_and_never_re_reads(app,
                                                                                     analysed):
    app.post(f"/p/{analysed['pid']}/react",
             data={"kind": "note", "text": "the crossing is the whole story"})
    chain = kinds(app.planned)[0]
    assert chain.count("doc") == 2 and chain[-1] == "project"
    assert "read" not in chain and "frame" not in chain


def test_a_check_asks_the_material_and_a_blank_one_asks_nothing(app, analysed, conn):
    app.post(f"/p/{analysed['pid']}/check",
             data={"question": "Is religion mentioned?", "material_id": analysed["grande"]})
    assert kinds(app.planned) == [["check"]]
    app.post(f"/p/{analysed['pid']}/check", data={"question": "   "})
    assert kinds(app.planned) == [["check"]], "a blank question must not start a run"


def test_setting_a_focus_changes_the_next_reading_and_re_runs_nothing(app, analysed, conn):
    app.post(f"/p/{analysed['pid']}/focus", data={"focus": "how a living is made"})
    assert app.planned == []
    assert store.project(conn, analysed["pid"])["focus"] == "how a living is made"
    assert [f["target_kind"] for f in store.project_feedback(conn, analysed["pid"])].count(
        "focus") == 1


def test_re_framing_re_describes_and_moves_no_sentence(app, analysed, conn):
    before = store.sentences(conn, analysed["grande"])
    app.post(f"/p/{analysed['pid']}/m/{analysed['grande']}/reframe",
             data={"hint": "these are field notes, not an interview"})
    assert kinds(app.planned) == [["frame"]]
    assert store.sentences(conn, analysed["grande"]) == before


def test_a_post_redirects_so_a_refresh_never_repeats_the_work(app, analysed):
    r = app.post(f"/p/{analysed['pid']}/react",
                 data={"kind": "note", "text": "x", "material_id": analysed["grande"]})
    assert r.status_code == 303 and r.headers["location"]


def test_reading_again_is_work_not_something_the_researcher_said(app, analysed, conn):
    """The re-read button used to post a note whose words the app had written, which put
    sentences the researcher never typed into the record of what the researcher said. That record
    is the audit trail; a re-read is work and goes straight to the work."""
    pid, mid = analysed["pid"], analysed["grande"]
    doc = store.start_run(conn, pid, "doc", mid, "x")
    store.finish_run(conn, doc)
    later = store.start_run(conn, pid, "themes", None, "x")
    store.finish_run(conn, later)
    before = len(store.project_feedback(conn, pid))

    app.post(f"/p/{pid}/refresh", data={"material_id": mid})
    assert kinds(app.planned) == [["doc", "project"]]
    assert len(store.project_feedback(conn, pid)) == before, "no feedback may be invented"


def test_reading_again_ignores_a_material_that_is_already_current(app, analysed):
    app.post(f"/p/{analysed['pid']}/refresh", data={"material_id": analysed["grande"]})
    assert app.planned == []
