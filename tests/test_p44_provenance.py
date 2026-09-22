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


def test_a_citation_carries_a_code_not_a_sentence(conn, analysed):
    """A title is a name when FRAME found a person and a sentence when it did not, and the head of
    it was what citations carried: "[S276 Livicia Antoine interview, Domestic Workers United]" at
    every citation in a summary. A code is the same length whatever the title is."""
    pid, mid = analysed["pid"], analysed["grande"]
    conn.execute("UPDATE material SET title=? WHERE id=?",
                 ("Livicia Antoine interview, Domestic Workers United", mid))
    conn.commit()
    assert context._shorts(conn, pid)[mid] == "LA"
    m = store.moments(conn, mid)[0]
    html = str(context.cite(f"A claim [{m['id']}].", context._cite_index(conn, pid), pid))
    assert f'<span class="cite-who">LA</span> {m["sid"]}</a>' in html
    assert "Domestic Workers United</span>" not in html, "the full title is the tooltip only"


def test_two_materials_with_the_same_initials_are_told_apart_in_the_order_they_came(conn, analysed):
    """The first MG stays MG when a second one arrives — a citation already read as MG must not
    come to mean somebody else."""
    pid = analysed["pid"]
    for mid, title in ((analysed["grande"], "Mary Grande"), (analysed["rodwin"], "Maria Gomez")):
        conn.execute("UPDATE material SET title=? WHERE id=?", (title, mid))
    conn.commit()
    shorts = context._shorts(conn, pid)
    assert (shorts[analysed["grande"]], shorts[analysed["rodwin"]]) == ("MG", "MG2")


def test_a_researchers_own_code_wins_and_a_derived_one_steps_around_it(conn, analysed):
    """A project with participant codes wants "P07" in its summary, not initials — and a derived
    code must never land on a code the researcher chose."""
    pid = analysed["pid"]
    conn.execute("UPDATE material SET title='Mary Grande' WHERE id=?", (analysed["grande"],))
    conn.execute("UPDATE material SET title='Rodwin' WHERE id=?", (analysed["rodwin"],))
    conn.commit()
    store.set_short_title(conn, analysed["rodwin"], "  M G  ")   # whitespace goes, as typed
    shorts = context._shorts(conn, pid)
    assert shorts[analysed["rodwin"]] == "MG", "taken as written"
    assert shorts[analysed["grande"]] == "MG2", "the derived one steps around it"
    store.set_short_title(conn, analysed["rodwin"], "")
    assert context._shorts(conn, pid)[analysed["rodwin"]] == "Ro", "empty is the derived code again"


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
    assert f'A finding [GM {m["sid"]}].' in text
    assert "- **GM** — Grande, M." in text, "and the record opens with the key to the codes"


def test_a_citation_with_no_material_name_still_prints_its_passage(conn):
    """The fallback is the old behaviour, never a bare space or a dangling separator."""
    assert context._cite_label({"sid": "S010", "material_short": ""}) == "S010"
    assert context._cite_label({"sid": "S010", "material_short": "Rodwin"}) == "Rodwin S010"


# ---- the source pane ----------------------------------------------------------------------------

def test_the_source_pane_names_the_text_and_the_theme_marked_in_it(conn, analysed, client):
    """`.record-pane` is sticky and the page head is not, so once a reader has scrolled a line of
    claims the pane is the only thing naming what they are looking at. It said "Source text" and
    "this theme" and neither of them was a name."""
    pid, mid = analysed["pid"], analysed["grande"]
    theme = store.live_themes(conn, pid)[0]
    html = client.get(f"/p/{pid}/m/{mid}?theme={theme['id']}").text
    head = html.split('class="record-head"', 1)[1].split("</section>", 1)[0]
    assert context._material_title(store.material(conn, mid)) in head
    assert theme["name"] in head
    assert "this theme" not in head
