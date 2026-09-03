"""P12 — the export is a document a person can open at fifty materials.

One markdown file, in this order, each a heading a contents list points at:
  Across the corpus · Themes (definition, account, where it runs and does not) · Materials
  (before reading, after reading, every line with its claims and quotes) · Checks · What the
  readings set aside · What the researcher said (with whether a rewrite honoured it) · Runs
  (totals by kind — provider, model, tokens — not one row per run).
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
    for want in ("Across the corpus", "Themes", "Materials", "Checks", "What the readings set aside",
                 "What the researcher said", "Runs"):
        assert want in heads, f"missing section {want!r}"
    contents = md.split("## ", 1)[0]
    for h in heads:
        assert h in contents, f"{h!r} is a heading but not in the contents list"
    assert heads.index("Across the corpus") < heads.index("Themes") < heads.index("Materials") < heads.index("Runs")


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
    sect = md.split("## Themes", 1)[1].split("## Materials", 1)[0]
    assert "of 2 materials" in sect
    assert "does not" in sect.lower()
    rod = store.material(conn, rich["rodwin"])
    assert (rod["title"] or rod["name"]) in sect


def test_a_comment_says_whether_a_rewrite_honoured_it(client, rich):
    md = client.get(f"/p/{rich['pid']}/export.md").text
    sect = md.split("## What the researcher said", 1)[1].split("## Runs", 1)[0]
    assert "the crossing is underplayed" in sect and "honoured" in sect
    assert "still open, not yet honoured" in sect and "open" in sect


def test_runs_are_totals_by_kind_not_one_row_each(client, conn, rich):
    pid = rich["pid"]
    for _ in range(40):
        rid = store.start_run(conn, pid, "doc", rich["grande"], "x"); store.finish_run(conn, rid, tokens_in=10, tokens_out=5)
    md = client.get(f"/p/{pid}/export.md").text
    sect = md.split("## Runs", 1)[1]
    assert sect.count("\n- ") < 15, "at fifty materials one row per run was 250 rows"
    assert "doc" in sect and "1400" in sect or "1,400" in sect   # 1000 + 40×10 input tokens
    assert "mistral" in sect or "minimax" in sect


def test_a_claim_in_the_export_is_reachable_by_id(client, conn, rich):
    md = client.get(f"/p/{rich['pid']}/export.md").text
    first = store.moments(conn, rich["grande"])[0]
    assert first["sid"] in md
