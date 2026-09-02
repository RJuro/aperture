"""P5 — the pages. `app/context.py`, `app/pages.py`, `app/templates/`, `app/static/aperture.css`.

Built against the `analysed` fixture, so it needs no model and can be built beside the engine.

The tests are mostly field coverage, because the bug this phase is prone to has happened three
times: an explicit key list on the way to the page silently drops a validated quote, and a green
suite says nothing. So: walk the real rows and assert each one reaches the HTML.
"""
from __future__ import annotations

import re

import pytest

from app import store

pytest.importorskip("app.pages")
pytest.importorskip("app.context")


@pytest.fixture
def client(conn, monkeypatch):
    from fastapi.testclient import TestClient
    from app import main
    monkeypatch.setattr(main, "conn", conn, raising=False)
    from app import pages
    monkeypatch.setattr(pages, "connection", lambda: conn, raising=False)
    return TestClient(main.app)


def strip_material(html: str) -> str:
    """What the app says in its own voice: the page with quoted speech, the transcript and model
    prose removed. The banned-word check runs over this, never over the material itself."""
    html = re.sub(r"<mark\b.*?</mark>", " ", html, flags=re.S)
    html = re.sub(r"<(pre|blockquote|q)\b.*?</\1>", " ", html, flags=re.S)
    html = re.sub(r'<[^>]*class="[^"]*\b(material|claim|summary|gist)\b[^"]*".*?</[a-z]+>', " ",
                  html, flags=re.S)
    return html


def test_every_live_moment_reaches_its_material_page_claim_and_quote(client, conn, analysed):
    for mid in (analysed["grande"], analysed["rodwin"]):
        for tid in analysed["themes"].values():
            html = client.get(f"/p/{analysed['pid']}/m/{mid}?thread={tid}").text
            for m in store.thread(conn, mid, tid):
                assert m["claim"] in html, f"claim missing: {m['claim']}"
                assert m["anchor"] in html, f"quote missing: {m['anchor']}"


def test_every_quote_is_marked_inside_the_material_at_its_own_sentence(client, conn, analysed):
    tid = list(analysed["themes"].values())[0]
    html = client.get(f"/p/{analysed['pid']}/m/{analysed['grande']}?thread={tid}").text
    marks = re.findall(r"<mark[^>]*>(.*?)</mark>", html, re.S)
    for m in store.thread(conn, analysed["grande"], tid):
        assert any(m["anchor"] in x for x in marks), f"not highlighted: {m['anchor']}"
        assert re.search(rf'id="{m["sid"]}"', html), f"no target for {m['sid']}"


def test_the_material_page_shows_its_derivation_not_a_bare_number(client, conn, analysed):
    html = client.get(f"/p/{analysed['pid']}/m/{analysed['grande']}").text
    cited = len(store.cited_sids(conn, analysed["grande"]))
    total = len(store.sentences(conn, analysed["grande"]))
    assert str(cited) in html and str(total) in html


def test_the_reading_summary_wins_and_the_orientation_shows_before_it_exists(client, conn,
                                                                            analysed):
    html = client.get(f"/p/{analysed['pid']}/m/{analysed['rodwin']}").text
    assert store.get_summary(conn, "material", analysed["rodwin"], "reading")["text"] in html
    conn.execute("UPDATE summary SET status='superseded' WHERE scope='material' AND ref_id=? "
                 "AND stage='reading'", (analysed["rodwin"],))
    conn.commit()
    html = client.get(f"/p/{analysed['pid']}/m/{analysed['rodwin']}").text
    assert store.get_summary(conn, "material", analysed["rodwin"], "orientation")["text"] in html


def test_the_project_page_is_themes_by_material(client, conn, analysed):
    html = client.get(f"/p/{analysed['pid']}").text
    for name, tid in analysed["themes"].items():
        assert name in html
        for mid in (analysed["grande"], analysed["rodwin"]):
            first = store.thread(conn, mid, tid)[0]
            assert first["claim"] in html
            assert f"/m/{mid}" in html and f"thread={tid}" in html


def test_the_app_does_not_speak_our_vocabulary(client, analysed):
    from app import context
    for url in (f"/p/{analysed['pid']}", f"/p/{analysed['pid']}/m/{analysed['grande']}"):
        said = strip_material(client.get(url).text).lower()
        for word in context._BANNED:
            assert not re.search(rf"\b{re.escape(word)}s?\b", said), f"{word!r} on {url}"


def test_an_idle_page_carries_no_poller_and_a_running_one_does(client, conn, analysed):
    url = f"/p/{analysed['pid']}"
    assert "http-equiv" not in client.get(url).text
    store.start_run(conn, analysed["pid"], "doc", analysed["grande"],
                    "Writing what stands out in Grande")
    html = client.get(url).text
    assert "http-equiv" in html and "Writing what stands out in Grande" in html


def test_the_export_prints_the_whole_record(client, conn, analysed):
    md = client.get(f"/p/{analysed['pid']}/export.md").text
    assert store.get_summary(conn, "project", analysed["pid"])["text"] in md
    for mid in (analysed["grande"], analysed["rodwin"]):
        assert store.get_summary(conn, "material", mid, "orientation")["text"] in md
        assert store.get_summary(conn, "material", mid, "reading")["text"] in md
        for m in store.moments(conn, mid):
            assert m["claim"] in md and m["anchor"] in md
    for c in store.checks(conn, analysed["pid"]):
        assert c["question"] in md and c["verdict"] in md and str(c["searched_n"]) in md


def test_no_javascript_anywhere(client, analysed):
    for url in (f"/p/{analysed['pid']}", f"/p/{analysed['pid']}/m/{analysed['grande']}"):
        html = client.get(url).text
        assert "<script" not in html.lower()


def test_a_material_read_before_the_themes_changed_says_so_and_offers_a_way_back(client, conn,
                                                                                 analysed):
    """Themes go on changing as material arrives. A material synthesised against an older set is
    not wrong, but it answered a different question — and re-running one is minutes of thinking
    and real money, so the researcher is told rather than charged for it silently."""
    pid, mid = analysed["pid"], analysed["grande"]
    html = client.get(f"/p/{pid}").text
    assert "Read it again" not in html, "nothing has run yet, so nothing can be out of date"

    doc = store.start_run(conn, pid, "doc", mid, "x")
    store.finish_run(conn, doc)
    later = store.start_run(conn, pid, "themes", None, "x")
    store.finish_run(conn, later)

    stale = [m["id"] for m in store.out_of_date(conn, pid)]
    assert stale == [mid], "only the material read before the change is out of date"
    html = client.get(f"/p/{pid}").text
    assert "Read it again" in html and mid in html


def test_a_failed_run_does_not_make_everything_look_out_of_date(conn, analysed):
    pid, mid = analysed["pid"], analysed["grande"]
    doc = store.start_run(conn, pid, "doc", mid, "x")
    store.finish_run(conn, doc)
    bad = store.start_run(conn, pid, "themes", None, "x")
    store.finish_run(conn, bad, error="the model fell over")
    assert store.out_of_date(conn, pid) == []
