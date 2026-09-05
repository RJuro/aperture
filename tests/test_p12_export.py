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

from app import context, store


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
        # Not the stored verdict word: an empty result is printed as what it is — nothing found
        # in the passages that were read — never as an absence from the material.
        assert c["question"] in md and str(c["searched_n"]) in md
        assert ("found —" if c["verdict"] == "found" else "nothing found —") in md
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
    assert "[[" not in md, "the model's own brackets are the ones to fill, not a second pair"
    assert "(frame)" not in md and "(doc)" not in md, "stage names are for the code"


def test_each_claim_is_printed_once_and_no_step_name_stands_in_for_a_state(client, conn, rich):
    """At fifty materials and twelve themes the record was 1.31 MB and 12,000 quoted claim lines
    for 6,000 claims — every claim once under its theme and once again under its material. The
    one printing is under the material, where the reading found it; the theme points at it. And
    the material header read "interview · doc · ...": `doc` is the engine's word for a step, not
    a sentence about a material."""
    pid = rich["pid"]
    md = client.get(f"/p/{pid}/export.md").text
    first = store.moments(conn, rich["grande"])[0]
    themes = md.split("\n## Themes\n", 1)[1].split("\n## Materials\n", 1)[0]
    mats = md.split("\n## Materials\n", 1)[1]
    title = context._material_title(store.material(conn, rich["grande"]))
    here = mats.split(f"### {title}\n", 1)[1].split("\n### ", 1)[0]
    assert here.count(first["claim"]) == 1 and first["anchor"] in here
    assert first["claim"] not in themes, "printed under its material and again under its theme"
    slug = re.sub(r"[^a-z0-9 -]", "", title.lower()).replace(" ", "-")
    assert f"](#{slug})" in themes, \
        "a theme must point at the material where its claims are printed"
    assert f" · {store.material(conn, rich['grande'])['state']} ·" not in md


def test_the_markdown_arrives_as_a_file_and_not_as_a_page_of_plain_text(client, conn, rich):
    """"The download is just leading to a website with plain text." It was: the browser rendered
    the markdown in a tab and there was nothing to keep."""
    r = client.get(f"/p/{rich['pid']}/export.md")
    assert r.headers["content-type"] == "text/markdown; charset=utf-8"
    assert r.headers["content-disposition"] == \
        f'attachment; filename="{store.project(conn, rich["pid"])["name"]}.md"'


def test_the_record_downloads_as_a_word_document(client, conn, rich):
    """The same record, in the form the researcher actually writes in. Built from the rendered
    markdown, so the structure has one home and the two versions cannot drift apart."""
    import io

    docx = pytest.importorskip("docx")
    pid = rich["pid"]
    r = client.get(f"/p/{pid}/export.docx")
    assert r.status_code == 200
    assert r.headers["content-disposition"] == 'attachment; filename="Test project.docx"'

    doc = docx.Document(io.BytesIO(r.content))
    paras = [p.text for p in doc.paragraphs]
    text = "\n".join(paras)
    assert "Test project" in paras[0] and "Aperture reading record" in paras
    assert store.get_summary(conn, "project", pid)["text"] in paras
    first = store.moments(conn, rich["grande"])[0]
    assert any(first["claim"] in p for p in paras)
    assert any(first["anchor"] in p and first["sid"] in p for p in paras), \
        "a claim without its quote and the passage it came from is an opinion"
    assert "Across the corpus" in paras and "Themes" in paras
    styles = {p.style.name for p in doc.paragraphs}
    assert {"Title", "Heading 1", "Heading 2", "List Bullet"} <= styles
    assert "**" not in text and "](#" not in text, "markdown leaked into the document"


def test_the_record_is_a_page_in_the_app_with_both_downloads_on_it(client, conn, rich):
    pid = rich["pid"]
    html = client.get(f"/p/{pid}/record").text
    assert store.get_summary(conn, "project", pid)["text"] in html
    first = store.moments(conn, rich["grande"])[0]
    assert first["claim"] in html and first["anchor"] in html
    assert "ACCOUNT: where this theme holds" in html
    for name in rich["themes"]:
        assert name in html, "the contents list names every theme"
    assert f'href="/p/{pid}/export.docx">Download as Word' in html
    assert f'href="/p/{pid}/export.md">Download as Markdown' in html
    assert f'href="/p/{pid}/m/{rich["grande"]}?theme=' in html, "a quote opens where it was said"


def test_the_record_and_its_downloads_are_only_for_whoever_owns_the_project(client, conn, rich):
    pid = rich["pid"]
    owner = store.create_user(conn, "ann", "battery staple")
    store.create_user(conn, "bob", "purple monkey")
    conn.execute("UPDATE project SET owner_id=? WHERE id=?", (owner, pid))
    conn.commit()
    client.post("/login", data={"name": "bob", "password": "purple monkey"})
    for tail in ("record", "export.docx", "export.md"):
        assert client.get(f"/p/{pid}/{tail}").status_code == 404, tail
    client.post("/logout")
    client.post("/login", data={"name": "ann", "password": "battery staple"})
    assert client.get(f"/p/{pid}/record").status_code == 200
