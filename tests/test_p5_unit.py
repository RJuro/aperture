"""P5's own checks: the ones the contract tests cannot see.

Field coverage first, because the bug this phase is prone to is an explicit key list that drops a
column between the row and the page. These walk the real rows and assert every column arrives.
"""
from __future__ import annotations

import re

import pytest

from app import context, store

pytest.importorskip("app.pages")


@pytest.fixture
def client(conn, monkeypatch):
    from fastapi.testclient import TestClient
    from app import main, pages
    monkeypatch.setattr(pages, "connection", lambda: conn, raising=False)
    return TestClient(main.app)


def test_no_context_key_list_drops_a_column(conn, analysed):
    """Every column of every row reaches the page context. No key lists anywhere."""
    pid, mid = analysed["pid"], analysed["grande"]
    ctx = context.material_page(conn, pid, mid)
    assert set(dict(store.material(conn, mid))) <= set(ctx["material"])
    for card in ctx["cards"]:
        rows = {r["id"]: dict(r) for r in store.thread(conn, mid, card["id"])}
        assert rows, "a card with no moments should not be shown at all"
        for m in card["moments"]:
            assert rows[m["id"]].items() <= m.items()

    proj = context.project_page(conn, pid)
    for m, row in zip(proj["materials"], store.materials(conn, pid)):
        assert dict(row).items() <= m.items()
    for t, row in zip(proj["themes"], store.live_themes(conn, pid)):
        assert dict(row).items() <= t.items()

    exp = context.export(conn, pid)
    seen = {m["id"] for d in exp["materials"] for th in d["threads"] for m in th["moments"]}
    for d in exp["materials"]:
        assert {x["id"] for x in store.moments(conn, d["id"])} <= seen
    for c, row in zip(exp["checks"], store.checks(conn, pid)):
        assert dict(row).items() <= c.items()
    for r, row in zip(exp["runs"], store.runs(conn, pid)):
        assert dict(row).items() <= r.items()


def test_the_apps_own_strings_avoid_our_vocabulary(conn, analysed):
    pid = analysed["pid"]
    for ctx in (context.home(conn), context.project_page(conn, pid),
                context.material_page(conn, pid, analysed["grande"]),
                context.export(conn, pid)):
        for key in context.APP_AUTHORED:
            said = str(ctx.get(key, "")).lower()
            for word in context._BANNED:
                assert not re.search(rf"\b{re.escape(word)}s?\b", said), f"{word!r} in {key}"


def test_material_text_cannot_inject_markup(conn, project, client):
    from app import ingest
    hostile = 'GRANDE:\tShe said <script>alert("x")</script> & meant it.'
    mid = store.add_material(conn, project, "Hostile", hostile)
    store.save_sentences(conn, mid, ingest.sentences(hostile))
    sid = store.sentences(conn, mid)[0][0]
    tid = store.save_theme(conn, project, tid=None, name="T", gist="g", code_ids=[])
    store.save_moments(conn, mid, tid, [{"claim": "c", "anchor": "She said", "sid": sid}])
    html = client.get(f"/p/{project}/m/{mid}").text
    assert "<script" not in html.lower()
    assert "&lt;script&gt;" in html and "&amp; meant it" in html


def test_a_quote_is_marked_where_it_sits_and_the_rest_is_not(conn, project, client):
    from app import ingest
    raw = "A:\tOne two three four. Five six seven eight."
    mid = store.add_material(conn, project, "Small", raw)
    store.save_sentences(conn, mid, ingest.sentences(raw))
    sids = [s for s, _ in store.sentences(conn, mid)]
    tid = store.save_theme(conn, project, tid=None, name="T", gist="g", code_ids=[])
    store.save_moments(conn, mid, tid, [{"claim": "c", "anchor": "two three", "sid": sids[0]}])
    html = client.get(f"/p/{project}/m/{mid}").text
    assert re.findall(r"<mark>(.*?)</mark>", html) == ["two three"]
    assert "Five six seven eight." in html          # unmarked text is the coverage display


def test_a_quote_that_cannot_be_located_marks_its_whole_sentence(conn, project, client):
    from app import ingest
    raw = "A:\tOne two three four. Five six seven eight."
    mid = store.add_material(conn, project, "Small", raw)
    store.save_sentences(conn, mid, ingest.sentences(raw))
    sids = [s for s, _ in store.sentences(conn, mid)]
    tid = store.save_theme(conn, project, tid=None, name="T", gist="g", code_ids=[])
    store.save_moments(conn, mid, tid,
                       [{"claim": "c", "anchor": "four. Five six", "sid": sids[0]}])
    html = client.get(f"/p/{project}/m/{mid}").text
    assert re.findall(r"<mark>(.*?)</mark>", html) == ["A: One two three four."]


def test_the_export_carries_the_checks_quotes_and_every_run(conn, analysed, client):
    pid = analysed["pid"]
    store.save_check(conn, pid, "material", analysed["grande"], "Any mention of money?",
                     "found", [{"anchor": "my father was here", "sid": "S041"}], 12)
    rid = store.start_run(conn, pid, "doc", analysed["grande"], "Writing it up")
    store.finish_run(conn, rid, tokens_in=1234, tokens_out=567)
    md = client.get(f"/p/{pid}/export.md").text
    assert "my father was here" in md and "S041" in md
    r = dict(store.runs(conn, pid)[-1])
    assert r["provider"] in md and r["model"] in md and "1234" in md and "567" in md
    for f in store.project_feedback(conn, pid):
        assert f["kind"] in md


def test_an_unknown_project_or_material_is_not_found(client, analysed):
    assert client.get("/p/nope").status_code == 404
    assert client.get(f"/p/{analysed['pid']}/m/nope").status_code == 404
    assert client.get("/p/nope/export.md").status_code == 404
