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
            html = client.get(f"/p/{analysed['pid']}/m/{mid}?theme={tid}").text
            for m in store.thread(conn, mid, tid):
                assert m["claim"] in html, f"claim missing: {m['claim']}"
                assert m["anchor"] in html, f"quote missing: {m['anchor']}"


def test_every_quote_is_marked_inside_the_material_at_its_own_sentence(client, conn, analysed):
    tid = list(analysed["themes"].values())[0]
    html = client.get(f"/p/{analysed['pid']}/m/{analysed['grande']}?theme={tid}").text
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
    """The grid carries counts that link, not every claim inline. At twelve themes and fifty
    materials the old table was 4,800 claim links and scrolled the whole page sideways; a count
    is legible, and the claims live on the theme's page and the material's."""
    html = client.get(f"/p/{analysed['pid']}").text
    for name, tid in analysed["themes"].items():
        assert name in html
        assert f"/t/{tid}" in html, "a theme's name must open the theme"
        for mid in (analysed["grande"], analysed["rodwin"]):
            n = len(store.thread(conn, mid, tid))
            assert f'?theme={tid}">{n}</a>' in html
    assert f"of {len(store.materials(conn, analysed['pid']))} materials" in html


def test_a_theme_has_a_page_of_its_own(client, conn, analysed):
    """The level a thematic analysis is written up at. Before it, a theme was a name, a gist and
    a row of cells — at fifty materials, four hundred claims and forty words about them."""
    pid = analysed["pid"]
    tid = list(analysed["themes"].values())[0]
    html = client.get(f"/p/{pid}/t/{tid}").text
    for mid in (analysed["grande"], analysed["rodwin"]):
        for m in store.thread(conn, mid, tid):
            assert m["claim"] in html and m["anchor"] in html
    assert "of 2 materials" in html


def test_the_theme_page_names_the_materials_the_theme_is_absent_from(client, conn, analysed):
    """Absence at corpus level is a finding. An empty cell in a grid says nothing; a named
    material under "materials where this theme does not appear" says the reading looked and
    claimed nothing."""
    pid = analysed["pid"]
    tid = list(analysed["themes"].values())[0]
    conn.execute("UPDATE moment SET status='superseded' WHERE material_id=? AND theme_id=?",
                 (analysed["rodwin"], tid))
    conn.commit()
    html = client.get(f"/p/{pid}/t/{tid}").text
    assert "Materials where this theme does not appear" in html
    row = store.material(conn, analysed["rodwin"])
    assert (row["title"] or row["name"]) in html


def test_both_movements_of_the_corpus_summary_are_shown_and_told_apart(client, conn, analysed):
    """What the corpus shows is cited; what it may mean is argued with. Run together on the page
    they would be read as one kind of sentence."""
    store.save_summary(conn, "project", analysed["pid"], "interpretation",
                       "Taken together, this suggests a single wage logic.")
    for url in (f"/p/{analysed['pid']}", f"/p/{analysed['pid']}/export.md"):
        text = client.get(url).text
        assert store.get_summary(conn, "project", analysed["pid"], "reading")["text"] in text
        assert "Taken together, this suggests a single wage logic." in text
        assert "What the material shows" in text and "What this may mean, so far" in text


def test_a_step_that_failed_says_what_stopped_it(client, conn, analysed):
    """The receipt marked a step failed and nothing said why, though the run row had the reason."""
    rid = store.start_run(conn, analysed["pid"], "read", analysed["grande"], "Reading Grande")
    store.finish_run(conn, rid, error="LLMError: the model returned no JSON")
    html = client.get(f"/p/{analysed['pid']}").text
    assert "LLMError: the model returned no JSON" in html


def test_a_summary_that_is_behind_or_broken_says_so_under_itself(client, conn, analysed):
    pid = analysed["pid"]
    assert "Written over all 2 materials" in client.get(f"/p/{pid}").text
    # A material read again after the summary counts as read since, added or not.
    store.save_summary(conn, "material", analysed["grande"], "reading", "read once more")
    html = client.get(f"/p/{pid}").text
    assert "1 material has been read since this was written" in html
    assert f'action="/p/{pid}/resynthesise"' in html
    jid = store.enqueue_job(conn, pid, [{"kind": "project"}])
    assert "being updated now" in client.get(f"/p/{pid}").text.lower()   # behind and working
    store.finish_job(conn, jid, "LLMError: the model said nothing")
    html = client.get(f"/p/{pid}").text
    assert "The last update did not finish: LLMError: the model said nothing" in html
    assert f'action="/p/{pid}/resynthesise"' in html


def test_the_app_does_not_speak_our_vocabulary(client, analysed):
    from app import context
    for url in (f"/p/{analysed['pid']}", f"/p/{analysed['pid']}/m/{analysed['grande']}"):
        said = strip_material(client.get(url).text).lower()
        for word in context._BANNED:
            assert not re.search(rf"\b{re.escape(word)}s?\b", said), f"{word!r} on {url}"


def test_an_idle_page_carries_no_poller_and_a_running_one_does(client, conn, analysed):
    """The poller replaces the line where it stands. A meta refresh reloaded the whole page and
    put the reader back at the top of it every fifteen seconds, which is unreadable while a chain
    runs — so it survives only inside <noscript>."""
    url = f"/p/{analysed['pid']}"
    idle = client.get(url).text
    assert "http-equiv" not in idle and "<script" not in idle.lower()
    store.start_run(conn, analysed["pid"], "doc", analysed["grande"],
                    "Writing what stands out in Grande")
    html = client.get(url).text
    assert "<noscript><meta http-equiv=\"refresh\" content=\"30\"></noscript>" in html
    assert "<script" in html and f"/p/{analysed['pid']}/runs" in html
    assert "Writing what stands out in Grande" in html


def test_what_is_running_is_readable_on_its_own_and_only_by_whoever_owns_it(client, conn,
                                                                           analysed):
    pid = analysed["pid"]
    assert client.get(f"/p/{pid}/runs").json() == []
    store.start_run(conn, pid, "doc", analysed["grande"], "Writing what stands out in Grande")
    store.start_run(conn, pid, "accounts", None, "Writing where each theme runs across everything")
    assert client.get(f"/p/{pid}/runs").json() == [
        {"line": "Writing what stands out in Grande"},
        {"line": "Writing where each theme runs across everything"}]
    assert client.get("/p/nope/runs").status_code == 404


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


def test_no_javascript_except_the_one_poller(client, analysed):
    """Nothing has run, so nothing is polling: the progress line is the only thing a script in
    this app is for."""
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
    assert "Reanalyse this material" not in html, \
        "nothing has run yet, so nothing can be out of date"

    doc = store.start_run(conn, pid, "doc", mid, "x")
    store.finish_run(conn, doc)
    later = store.start_run(conn, pid, "themes", None, "x")
    store.finish_run(conn, later)

    stale = [m["id"] for m in store.out_of_date(conn, pid)]
    assert stale == [mid], "only the material read before the change is out of date"
    html = client.get(f"/p/{pid}").text
    assert "Reanalyse this material" in html and mid in html


def test_a_failed_run_does_not_make_everything_look_out_of_date(conn, analysed):
    pid, mid = analysed["pid"], analysed["grande"]
    doc = store.start_run(conn, pid, "doc", mid, "x")
    store.finish_run(conn, doc)
    bad = store.start_run(conn, pid, "themes", None, "x")
    store.finish_run(conn, bad, error="the model fell over")
    assert store.out_of_date(conn, pid) == []


def test_what_a_reading_set_aside_is_shown_and_not_swallowed(client, conn, analysed):
    """A line too thin to keep is dropped whole. It was computed, reported, and thrown away by
    the runner — so an empty cell read as 'nothing here' when it meant 'three claims found and
    discarded'. The theme page says so where it names absences."""
    pid, mid = analysed["pid"], analysed["grande"]
    rid = store.start_run(conn, pid, "doc", mid, "x")
    store.finish_run(conn, rid, notes=['the line for "Work and trade" was dropped: 3 claims left'])
    assert 'the line for "Work and trade" was dropped: 3 claims left' in store.set_aside(conn, pid)

    html = client.get(f"/p/{pid}/m/{mid}").text
    assert "Excluded from the analysis" in html and "was dropped: 3 claims left" in html

    tid = list(analysed["themes"].values())[0]
    conn.execute("UPDATE moment SET status='superseded' WHERE material_id=? AND theme_id=?",
                 (analysed["rodwin"], tid))
    conn.commit()
    theme = client.get(f"/p/{pid}/t/{tid}").text
    assert "Materials where this theme does not appear" in theme
    assert "Excluded from the analysis" in theme, \
        "an absence must not be asserted without the drops beside it"


def test_a_project_whose_work_is_only_queued_still_says_it_is_working(client, conn, analysed):
    """The banner reads run rows; the job row is what exists first. Between the redirect and the
    worker's first run row — and for as long as another project holds the runner — the page said
    nothing at all while the work was genuinely queued."""
    pid = analysed["pid"]
    store.enqueue_job(conn, pid, [{"kind": "project"}])
    html = client.get(f"/p/{pid}").text
    assert "Waiting for other work to finish." in html
    assert f'action="/p/{pid}/stop"' in html
    assert "<script" in html and f"/p/{pid}/runs" in html
    assert '<noscript><meta http-equiv="refresh" content="30"></noscript>' in html


def test_the_poller_does_not_reload_over_what_is_being_typed(client, conn, analysed):
    """The reload arrives on a ten-second timer, and a browser never restores a file input."""
    store.start_run(conn, analysed["pid"], "doc", analysed["grande"], "Writing Grande")
    html = client.get(f"/p/{analysed['pid']}").text
    assert "The reading has finished — reload to see it." in html
    assert "textarea" in html.split("<script", 1)[1] and "files.length" in html


def test_a_quote_that_crosses_a_sentence_boundary_marks_the_quote_and_not_the_cue(client, conn,
                                                                                  project):
    """A quote may run across up to three sentences, and the page attached it to the sentence it
    starts in — where it is not — so the whole of that sentence was marked, speaker cue and all,
    and the second half of the quote was left plain. Law 1 is that a claim shows the words it
    rests on."""
    from app import ingest
    raw = "GRANDE:\tMy mother missed it a lot. But I am sorry to say it."
    mid = store.add_material(conn, project, "Small", raw)
    store.save_sentences(conn, mid, ingest.sentences(raw))
    sids = [s for s, _ in store.sentences(conn, mid)]
    tid = store.save_theme(conn, project, tid=None, name="T", gist="g", code_ids=[])
    store.save_moments(conn, mid, tid, [{"claim": "c", "anchor": "missed it a lot. But I am",
                                         "sid": sids[0]}])
    html = client.get(f"/p/{project}/m/{mid}").text
    marked = " ".join(re.findall(r"<mark>(.*?)</mark>", html))
    assert marked == "missed it a lot. But I am"
    assert "GRANDE" not in marked and "My mother" not in marked
