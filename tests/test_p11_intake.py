"""P11 — material intake. `app/intake.py`: files of several kinds become text; text becomes a
material; a material starts the chain. Nothing here decides what a material IS — FRAME does.

    intake.extract(filename, data: bytes) -> str          .txt .md .docx .pdf .csv
    intake.IntakeError                                     one sentence a person can read
    POST /p/{pid}/material  multipart `files` (one or many) and/or `name` + `text`

A CSV of open answers becomes ONE material whose passages are headed by respondent, so the frame
step can lay it out as segments and the reading can tell respondents apart.
"""
from __future__ import annotations

import io

import pytest

from app import store

intake = pytest.importorskip("app.intake")

TINY_PDF = b"""%PDF-1.1
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 300 144]/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj
4 0 obj<</Length 62>>stream
BT /F1 18 Tf 20 100 Td (The stall fed them, not the land.) Tj ET
endstream
endobj
5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj
trailer<</Root 1 0 R>>"""


def test_plain_text_and_markdown_pass_through(tmp_path):
    assert intake.extract("notes.txt", b"One line.\nTwo lines.") == "One line.\nTwo lines."
    assert "Two lines" in intake.extract("notes.md", b"# Heading\n\nTwo lines.")


def test_a_docx_yields_its_paragraphs_in_order():
    docx = pytest.importorskip("docx")
    d = docx.Document()
    d.add_paragraph("PHILLIPS: Tell me about the farm.")
    d.add_paragraph("GRANDE: We had a stall in the market.")
    buf = io.BytesIO(); d.save(buf)
    text = intake.extract("interview.docx", buf.getvalue())
    assert text.index("PHILLIPS") < text.index("GRANDE")
    assert "stall in the market" in text


def test_a_pdf_yields_its_text():
    pytest.importorskip("pypdf")
    text = intake.extract("scan.pdf", TINY_PDF)
    assert "The stall fed them" in text


def test_a_csv_of_open_answers_keeps_respondents_apart():
    csv = ("id,What was hardest?,What helped?\n"
           "R1,\"Leaving my mother behind, honestly.\",\"My cousin met me at the station.\"\n"
           "R2,\"The language, every single day.\",\"Nothing. I managed.\"\n").encode()
    text = intake.extract("survey.csv", csv)
    assert text.count("R1") == 1 and text.count("R2") == 1
    assert text.index("R1") < text.index("Leaving my mother") < text.index("R2") < text.index("managed")
    assert "What was hardest?" in text, "the question is kept beside its answer"


def test_a_kind_nobody_handles_fails_with_a_sentence():
    with pytest.raises(intake.IntakeError) as e:
        intake.extract("photo.png", b"\x89PNG....")
    assert "png" in str(e.value).lower() and "\n" not in str(e.value)


def test_an_unreadable_file_fails_with_a_sentence_not_a_trace():
    with pytest.raises(intake.IntakeError):
        intake.extract("broken.docx", b"not a zip at all")


@pytest.fixture
def client(conn, monkeypatch):
    from fastapi.testclient import TestClient
    from app import jobs, main, pages, verbs
    for mod in (pages, verbs):
        monkeypatch.setattr(mod, "connection", lambda: conn, raising=False)
    started = []
    monkeypatch.setattr(verbs.jobs, "ingest_chain", lambda pid, mid, **k: started.append(mid) or "j")
    c = TestClient(main.app, follow_redirects=False)
    c.started = started
    return c


def test_several_files_at_once_become_several_materials_each_starting_its_chain(client, conn, project):
    files = [("files", ("a.txt", b"First piece. It has sentences.", "text/plain")),
             ("files", ("b.md", b"# Second\n\nSecond piece here.", "text/markdown"))]
    r = client.post(f"/p/{project}/material", files=files)
    assert r.status_code == 303
    mats = store.materials(conn, project)
    assert [m["name"] for m in mats] == ["a.txt", "b.md"]
    assert all(store.sentences(conn, m["id"]) for m in mats), "ids exist before anything cites them"
    assert client.started == [m["id"] for m in mats]


def test_pasted_text_still_works(client, conn, project):
    r = client.post(f"/p/{project}/material", data={"name": "Pasted", "text": "Some pasted text."})
    assert r.status_code == 303
    assert store.materials(conn, project)[-1]["name"] == "Pasted"


def test_a_bad_file_makes_no_material_and_says_why(client, conn, project):
    r = client.post(f"/p/{project}/material", files=[("files", ("x.png", b"\x89PNG", "image/png"))])
    assert r.status_code == 303 and "problem=" in r.headers["location"]
    assert store.materials(conn, project) == [] and client.started == []
    page = client.get(f"/p/{project}?problem=png+is+not+a+kind+of+material+this+reads").text
    assert "png is not a kind of material this reads" in page


def test_an_empty_submission_makes_nothing(client, conn, project):
    client.post(f"/p/{project}/material", data={"name": "", "text": "   "})
    assert store.materials(conn, project) == []
