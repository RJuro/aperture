"""P17 — what the reader is left to work out for themselves.

A review of a real three-material reading found four places where the display made the researcher
do the analysis: twelve themes side by side with a tag saying how many materials each rested on,
so the corpus themes and the single-material motifs had to be told apart by eye; a claim count
that counted one passage once per theme that read it; feedback entries printed as ids; and one
flat list of everything every reading dropped, with the material's name repeated on each line.
"""
from __future__ import annotations

import pytest

from app import context, store


@pytest.fixture
def client(conn, monkeypatch):
    from fastapi.testclient import TestClient
    from app import main, pages
    monkeypatch.setattr(pages, "connection", lambda: conn, raising=False)
    return TestClient(main.app)


def _themes(text: str) -> str:
    """The themes section of a page or of the document, and nothing else — a theme's name is in
    the record's contents list long before the section that groups them."""
    if "\n## Themes\n" in text:
        return text.split("\n## Themes\n", 1)[1].split("\n## Materials\n", 1)[0]
    return text.split('id="themes"', 1)[1].split('id="materials"', 1)[0]


@pytest.fixture
def one_material(conn, project, grande):
    """One material, two themes over it, one passage read under both.

    Three passages: the first theme rests on A and B, the second on B and twice on C. So the
    second has three claims and two passages, and B is shared.
    """
    picked = []
    for sid, text in store.sentences(conn, grande):
        if 5 <= len(text.split()) <= 12:
            picked.append((sid, " ".join(text.split()[:8])))
        if len(picked) == 3:
            break
    (a, qa), (b, qb), (c, qc) = picked
    first = store.save_theme(conn, project, tid=None, name="Crossing the river",
                             gist="the water and what it cost", code_ids=[])
    second = store.save_theme(conn, project, tid=None, name="Money at home",
                              gist="what was sent back", code_ids=[])
    store.save_moments(conn, grande, first, [{"claim": "The river was the price", "anchor": qa,
                                              "sid": a},
                                             {"claim": "He paid to cross", "anchor": qb, "sid": b}])
    store.save_moments(conn, grande, second, [{"claim": "The crossing was paid for", "anchor": qb,
                                               "sid": b},
                                              {"claim": "Wages went home", "anchor": qc, "sid": c},
                                              {"claim": "And went home again", "anchor": qc,
                                               "sid": c}])
    return {"pid": project, "mid": grande, "first": first, "second": second, "shared": b}


def test_themes_across_materials_are_listed_apart_from_single_material_ones(client, conn,
                                                                            analysed):
    """Five of twelve themes rested on one interview each. Listed beside the ones that ran
    through the whole corpus, with only a tag to tell them apart, the reader did the filtering."""
    pid = analysed["pid"]
    solo = store.save_theme(conn, pid, tid=None, name="Only here", gist="a single material",
                            code_ids=[])
    # A pattern in one material is a candidate, and the second group is now exactly the
    # candidates: the recurrence rule picks out the same set the reach count used to.
    store.set_hold(conn, solo, "candidate")
    sid = store.moments(conn, analysed["grande"])[0]["sid"]
    store.save_moments(conn, analysed["grande"], solo,
                       [{"claim": "said once", "anchor": "x", "sid": sid}])
    for url in (f"/p/{pid}", f"/p/{pid}/record", f"/p/{pid}/export.md"):
        sect = _themes(client.get(url).text)
        across, single = sect.index("Across materials"), sect.index("In one material so far")
        assert across < single, f"the corpus themes come first on {url}"
        assert single < sect.index("Only here"), f"a one-material theme is in the second group ({url})"
        for name in analysed["themes"]:
            assert across < sect.index(name) < single, f"{name} is in the first group ({url})"


def test_a_project_with_one_material_shows_only_the_second_group(client, conn, one_material):
    pid = one_material["pid"]
    # With one material nothing has recurred, so every theme in the project is a candidate —
    # which is what leaves the first group empty.
    for tid in (one_material["first"], one_material["second"]):
        store.set_hold(conn, tid, "candidate")
    for url in (f"/p/{pid}", f"/p/{pid}/record", f"/p/{pid}/export.md"):
        sect = _themes(client.get(url).text)
        assert "Across materials" not in sect, f"nothing can span one material ({url})"
        assert "In one material so far" in sect
        assert "With one material, a theme cannot yet run across materials." in sect


def test_a_themes_count_is_claims_and_the_passages_those_claims_rest_on(client, one_material):
    """"81 of 818 passages" counted the same passage once per theme that read it."""
    pid, first = one_material["pid"], one_material["first"]
    for url in (f"/p/{pid}", f"/p/{pid}/record", f"/p/{pid}/export.md",
                f"/p/{pid}/t/{first}"):
        text = client.get(url).text
        assert "2 claims on 2 passages · 1 passage shared with other themes" in text, url
        if not url.endswith(first):
            assert "3 claims on 2 passages · 1 passage shared with other themes" in text, url


def test_nothing_is_said_about_sharing_when_no_passage_is_shared(client, analysed):
    sect = _themes(client.get(f"/p/{analysed['pid']}").text)
    assert "6 claims on 6 passages" in sect
    assert "shared" not in sect


def test_a_claim_whose_passage_another_theme_reads_says_which(client, one_material):
    """The same passage under three themes, and each theme's page showed it as its own."""
    d = one_material
    html = client.get(f'/p/{d["pid"]}/m/{d["mid"]}?theme={d["first"]}').text
    assert html.count("Also read under") == 1, "only the shared passage carries the line"
    assert f'href="?theme={d["second"]}#reading">Money at home</a>' in html


@pytest.mark.parametrize("looked_for, head", [(True, "Looked for and found too thin"),
                                              (False, "Not looked for here")])
def test_a_material_a_theme_never_reached_says_whether_it_was_looked_through(
        client, conn, analysed, looked_for, head):
    """Absence is two different findings — the theme was followed here and the line was too thin
    to keep, or none of its codes marked this material at all — and one list cannot say which.
    The record reads which from what DOC wrote down (`follow`), not from a guess."""
    pid, tid = analysed["pid"], list(analysed["themes"].values())[0]
    conn.execute("UPDATE moment SET status='superseded' WHERE material_id=? AND theme_id=?",
                 (analysed["rodwin"], tid))
    conn.commit()
    store.save_follow(conn, analysed["rodwin"], tid, "thin" if looked_for else "skipped", None)
    other = "Not looked for here" if looked_for else "Looked for and found too thin"
    for url in (f"/p/{pid}/record", f"/p/{pid}/export.md"):
        sect = _themes(client.get(url).text)
        assert head in sect and other not in sect, url
        assert "Materials where this theme does not appear" not in sect, url


def test_a_feedback_entry_names_what_it_was_about(client, conn, analysed):
    """`note on m4f1c…` is unreadable a month later, and a material that was later removed
    printed as its id in the record of what the researcher said."""
    pid, tid = analysed["pid"], list(analysed["themes"].values())[0]
    title = context._material_title(store.material(conn, analysed["grande"]))
    store.add_feedback(conn, pid, "material_summary", analysed["grande"], "note",
                       "the crossing is underplayed")
    store.add_feedback(conn, pid, "theme", tid, "note", "this reads as two themes")
    store.add_feedback(conn, pid, "project_summary", pid, "note", "too tidy")

    def said(text: str) -> str:
        if "## Researcher feedback" in text:
            return text.split("## Researcher feedback", 1)[1].split("## Processing", 1)[0]
        return text.split('id="feedback"', 1)[1].split('id="history"', 1)[0]

    for removed in (False, True):
        for url in (f"/p/{pid}/record", f"/p/{pid}/export.md"):
            sect = said(client.get(url).text)
            assert f"note on {title}: " in sect and "the crossing is underplayed" in sect
            assert "note on Work and trade: " in sect and "this reads as two themes" in sect
            assert "note on the project: " in sect and "too tidy" in sect
            assert "open" in sect, "and whether a rewrite has answered it"
            assert analysed["grande"] not in sect and tid not in sect, "an id is not a reference"
        if not removed:
            store.remove_material(conn, pid, analysed["grande"])


def test_what_the_readings_dropped_is_grouped_by_material(client, conn, analysed):
    """One flat list repeated the material's title on every line and scattered one material's
    drops through the whole log."""
    pid = analysed["pid"]
    for mid, note in ((analysed["grande"], 'the line for "Work and trade" was set aside: 3 left'),
                      (analysed["grande"], 'the line for "Leaving and arriving" was set aside: 2'),
                      (analysed["rodwin"], 'the line for "Work and trade" was set aside: 1 left')):
        rid = store.start_run(conn, pid, "doc", mid, "x")
        store.finish_run(conn, rid, notes=[note])
    name = context._material_title(store.material(conn, analysed["grande"]))
    md = client.get(f"/p/{pid}/export.md").text
    sect = md.split("## Excluded from the analysis", 1)[1].split("## Researcher feedback", 1)[0]
    assert sect.count(name) == 1, "the title is a heading, not a word on every line"
    assert f"### {name}" in sect
    assert sect.index(f"### {name}") < sect.index("was set aside: 3 left") < sect.index(
        "was set aside: 1 left"), "one material's drops sit together, under its own heading"

    html = client.get(f"/p/{pid}/record").text
    sect = html.split('id="excluded"', 1)[1].split('id="feedback"', 1)[0]
    assert f"<h3>{name}</h3>" in sect and sect.count(name) == 1
