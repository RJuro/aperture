"""P12 — the export is a document a person can open at fifty materials.

One markdown file, in this order, each a heading a contents list points at:
  Across the corpus · Themes (definition, account, where it runs and does not) · Materials
  (before reading, after reading, every line with its claims and quotes) · Questions checked
  against the materials · Excluded from the analysis · Researcher feedback (with whether a rewrite
  honoured it) · Processing history (totals by kind — provider, model, tokens — not one row per
  run).
"""
from __future__ import annotations

import re

import pytest

from app import store


@pytest.fixture
def client(conn, monkeypatch):
    from fastapi.testclient import TestClient
    from app import main, pages
    monkeypatch.setattr(pages, "connection", lambda: conn, raising=False)
    return TestClient(main.app)


@pytest.fixture
def rich(conn, analysed):
    pid = analysed["pid"]
    tid = list(analysed["themes"].values())[0]
    store.save_summary(conn, "theme", tid, "reading", "ACCOUNT: where this theme holds and where it does not.")
    rid = store.start_run(conn, pid, "doc", analysed["grande"], "x")
    store.finish_run(conn, rid, tokens_in=1000, tokens_out=200,
                     notes=['the line for "Work and trade" was set aside: 3 claims left'])
    fid = store.add_feedback(conn, pid, "material_summary", analysed["grande"], "note", "the crossing is underplayed")
    store.consume_feedback(conn, fid, rid)
    store.add_feedback(conn, pid, "project_summary", pid, "note", "still open, not yet honoured")
    return analysed


def test_the_document_has_a_contents_list_that_matches_its_headings(client, rich):
    md = client.get(f"/p/{rich['pid']}/export.md").text
    heads = re.findall(r"^## (.+)$", md, re.M)
    for want in ("Across the corpus", "Themes", "Materials",
                 "Questions checked against the materials", "Excluded from the analysis",
                 "Researcher feedback", "Processing history"):
        assert want in heads, f"missing section {want!r}"
    contents = md.split("## ", 1)[0]
    for h in heads:
        assert h in contents, f"{h!r} is a heading but not in the contents list"
    assert (heads.index("Across the corpus") < heads.index("Themes") < heads.index("Materials")
            < heads.index("Processing history"))


def test_every_live_row_reaches_the_document(client, conn, rich):
    pid = rich["pid"]
    md = client.get(f"/p/{pid}/export.md").text
    assert store.get_summary(conn, "project", pid)["text"] in md
    for tid in rich["themes"].values():
        t = conn.execute("SELECT * FROM theme WHERE id=?", (tid,)).fetchone()
        assert t["name"] in md and t["gist"] in md
    assert "ACCOUNT: where this theme holds" in md
    for mid in (rich["grande"], rich["rodwin"]):
        assert store.get_summary(conn, "material", mid, "orientation")["text"] in md
        assert store.get_summary(conn, "material", mid, "reading")["text"] in md
        for m in store.moments(conn, mid):
            assert m["claim"] in md and m["anchor"] in md
    for c in store.checks(conn, pid):
        assert c["question"] in md and c["verdict"] in md and str(c["searched_n"]) in md
    assert 'was set aside: 3 claims left' in md
    assert "the crossing is underplayed" in md and "still open, not yet honoured" in md


def test_a_theme_section_says_where_it_runs_and_where_it_does_not(client, conn, rich):
    tid = list(rich["themes"].values())[0]
    conn.execute("UPDATE moment SET status='superseded' WHERE material_id=? AND theme_id=?", (rich["rodwin"], tid)); conn.commit()
    md = client.get(f"/p/{rich['pid']}/export.md").text
    # Anchored on the line, not the substring: "#### Materials where this theme appears" now
    # sits inside this very section.
    sect = md.split("\n## Themes\n", 1)[1].split("\n## Materials\n", 1)[0]
    assert "of 2 materials" in sect
    assert "does not" in sect.lower()
    rod = store.material(conn, rich["rodwin"])
    assert (rod["title"] or rod["name"]) in sect


def test_a_comment_says_whether_a_rewrite_honoured_it(client, rich):
    md = client.get(f"/p/{rich['pid']}/export.md").text
    sect = md.split("## Researcher feedback", 1)[1].split("## Processing history", 1)[0]
    assert "the crossing is underplayed" in sect and "honoured" in sect
    assert "still open, not yet honoured" in sect and "open" in sect


def test_runs_are_totals_by_kind_not_one_row_each(client, conn, rich):
    pid = rich["pid"]
    for _ in range(40):
        rid = store.start_run(conn, pid, "doc", rich["grande"], "x"); store.finish_run(conn, rid, tokens_in=10, tokens_out=5)
    md = client.get(f"/p/{pid}/export.md").text
    sect = md.split("## Processing history", 1)[1]
    assert sect.count("\n- ") < 15, "at fifty materials one row per run was 250 rows"
    assert "Writing what stands out" in sect, "the researcher's line for the step, not its stage name"
    assert "1400" in sect, "1000 + 40×10 input tokens, as one total"
    assert "mistral" in sect or "minimax" in sect


def test_a_claim_in_the_export_is_reachable_by_id(client, conn, rich):
    md = client.get(f"/p/{rich['pid']}/export.md").text
    first = store.moments(conn, rich["grande"])[0]
    assert first["sid"] in md


def test_the_document_never_shows_an_internal_claim_id(client, conn, rich):
    """On a page an internal id becomes a link. In a document it would sit there as an opaque
    token — the first review's complaint about the record — so each becomes the sentence id a
    reader can find in the same document."""
    first = store.moments(conn, rich["grande"])[0]
    store.save_summary(conn, "project", rich["pid"], "reading",
                       f"Work runs through it [{first['id']}] and beyond.")
    md = client.get(f"/p/{rich['pid']}/export.md").text
    assert first["id"] not in md
    assert f"[{first['sid']}]" in md
    assert "(frame)" not in md and "(doc)" not in md, "stage names are for the code"


def test_each_claim_is_printed_once_and_no_step_name_stands_in_for_a_state(client, conn, rich):
    """At fifty materials and twelve themes the record was 1.31 MB and 12,000 quoted claim lines
    for 6,000 claims — every claim once under its theme and once again under its material. And
    the material header read "interview · doc · ...": `doc` is the engine's word for a step, not
    a sentence about a material."""
    pid = rich["pid"]
    md = client.get(f"/p/{pid}/export.md").text
    first = store.moments(conn, rich["grande"])[0]
    themes = md.split("\n## Themes\n", 1)[1].split("\n## Materials\n", 1)[0]
    mats = md.split("\n## Materials\n", 1)[1]
    assert first["claim"] in themes and first["anchor"] in themes
    assert first["claim"] not in mats, "printed under its theme and again under its material"
    name = list(rich["themes"])[0]
    assert f"](#{name.lower().replace(' ', '-')})" in mats, \
        "a material must point at where its claims are printed"
    assert f" · {store.material(conn, rich['grande'])['state']} ·" not in md
