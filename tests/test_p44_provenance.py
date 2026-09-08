"""A citation says which material it came from, and the excluded list says what it excluded.

    context.cite(text, index, pid)          the page: a link carrying the material's name
    context._export_resolve_all(...)        the record: `[Mary Grande S070]`, not `[S070]`

Both from one researcher reading her own corpus back. On the citation: *"I don't know whose
verbatim it is [...] I can actually deduct it because some of the numbers are very close to each
other."* Working provenance out from the proximity of passage ids is the page failing at its one
job — the corpus summary cites across every material at once, and the index has carried the
material id all along to build the link with.

On the drawer: *"I'm very confused by the analysis details and what was dropped."* It was headed
"Excluded from the analysis" and listed, among things that were excluded, notes reporting that a
quote had been KEPT. Four different events under one heading, described with five verbs, one of
them printing an internal id at a researcher.
"""
from __future__ import annotations

import pytest

from app import context, store


@pytest.fixture
def client(conn, monkeypatch):
    from fastapi.testclient import TestClient
    from app import main, pages
    monkeypatch.setattr(main, "conn", conn, raising=False)
    monkeypatch.setattr(pages, "connection", lambda: conn, raising=False)
    return TestClient(main.app)


# ---- the page -----------------------------------------------------------------------------------

def test_a_citation_carries_the_material_it_rests_on(conn, analysed):
    pid, mid = analysed["pid"], analysed["grande"]
    m = store.moments(conn, mid)[0]
    index = context._cite_index(conn, pid)
    html = str(context.cite(f"A claim [{m['id']}].", index, pid))
    assert f'#{m["sid"]}' in html, "still links to the passage"
    assert index[m["id"]]["material_short"] in html, "and now says which material that is"


def test_the_short_name_drops_the_kind_and_keeps_the_person(conn, analysed):
    """`titles.compose` writes "M. Grande — interview, 1989"; inline at every citation the tail is
    noise repeated at every id, and the head is the whole question the reader is asking."""
    mid = analysed["grande"]
    conn.execute("UPDATE material SET title=? WHERE id=?", ("M. Grande — interview, 1989", mid))
    conn.commit()
    row = store.material(conn, mid)
    assert context._short_title(row) == "M. Grande"
    assert context._material_title(row) == "M. Grande — interview, 1989"


def test_a_title_with_no_kind_is_left_whole(conn, analysed):
    """A material named only by its file has no tail to drop, and losing part of it would leave
    the citation naming something that is not the material."""
    row = store.material(conn, analysed["grande"])
    assert context._short_title(row) == context._material_title(row) == "Grande, M."


def test_two_materials_cite_under_two_names(conn, analysed):
    pid = analysed["pid"]
    a = store.moments(conn, analysed["grande"])[0]
    b = store.moments(conn, analysed["rodwin"])[0]
    index = context._cite_index(conn, pid)
    assert index[a["id"]]["material_short"] != index[b["id"]]["material_short"]
    html = str(context.cite(f"One [{a['id']}] and another [{b['id']}].", index, pid))
    for m in (a, b):
        assert index[m["id"]]["material_short"] in html


def test_the_full_title_rides_along_as_the_links_tooltip(conn, analysed):
    pid, mid = analysed["pid"], analysed["grande"]
    m = store.moments(conn, mid)[0]
    html = str(context.cite(f"A claim [{m['id']}].", context._cite_index(conn, pid), pid))
    assert f'title="{context._material_title(store.material(conn, mid))}"' in html


# ---- the record ---------------------------------------------------------------------------------

def test_the_record_names_the_material_beside_the_passage(conn, analysed, client):
    pid = analysed["pid"]
    m = store.moments(conn, analysed["grande"])[0]
    store.save_summary(conn, "project", pid, "reading", f"A finding [{m['id']}].")
    text = client.get(f"/p/{pid}/export.md").text
    assert f'A finding [Grande, M. {m["sid"]}].' in text


def test_a_citation_with_no_material_name_still_prints_its_passage(conn):
    """The fallback is the old behaviour, never a bare space or a dangling separator."""
    assert context._cite_label({"sid": "S010", "material_short": ""}) == "S010"
    assert context._cite_label({"sid": "S010", "material_short": "Rodwin"}) == "Rodwin S010"
