"""P38 — what a researcher sees and types when the material is a recording.

Two things are new on the pages. The Add-material drawer asks the two questions a transcript needs
answered — who is in the recording, and whether to have the voices named — and the material page
tells a researcher which of three states their recording is in: waiting for its transcript, read
from one, or stopped before there was one. The receipt gains a step for the wait, because minutes
of nothing happening is exactly when a page has to say what it is doing.

The engine's columns are added here rather than in `db.py`: these tests are written against the
upload contract while the transcription itself is built beside them, and a page that reads the
columns defensively is the same page either way.
"""
from __future__ import annotations

import re

import pytest

from app import context, store
from tests.test_p5_pages import strip_material

AUDIO_COLUMNS = (("audio_file", "TEXT DEFAULT ''"), ("audio_note", "TEXT DEFAULT ''"),
                 ("audio_clean", "INTEGER DEFAULT 0"), ("audio_seconds", "INTEGER DEFAULT 0"))


@pytest.fixture
def client(conn, monkeypatch):
    from fastapi.testclient import TestClient
    from app import main, pages
    monkeypatch.setattr(main, "conn", conn, raising=False)
    monkeypatch.setattr(pages, "connection", lambda: conn, raising=False)
    return TestClient(main.app)


@pytest.fixture(autouse=True)
def audio_columns(conn):
    """The engine's columns, added where the pages phase can see them. Guarded, because the two
    branches merge and whichever lands second must not fail on a column that already exists."""
    have = {r["name"] for r in conn.execute("PRAGMA table_info(material)")}
    for name, decl in AUDIO_COLUMNS:
        if name not in have:
            conn.execute(f"ALTER TABLE material ADD COLUMN {name} {decl}")
    conn.commit()


def recording(conn, mid: str, *, file: str = "", note: str = "", clean: int = 0,
              seconds: int = 0) -> None:
    conn.execute("UPDATE material SET audio_file=?, audio_note=?, audio_clean=?, audio_seconds=? "
                 "WHERE id=?", (file, note, clean, seconds, mid))
    conn.commit()


NOTE = ("Two people: Paul Sigrist asking the questions, Mary Grande answering. She talks about "
        "the crossing in 1921 and her father's bakery in Brooklyn.")


# ---- the drawer ---------------------------------------------------------------------------

def drawer(html: str) -> str:
    found = re.search(r'<details class="add-drawer".*?</details>\s*</div>', html, re.S)
    assert found, "no Add-material drawer on the project page"
    return found.group(0)


def test_the_one_file_field_takes_recordings_and_names_what_it_takes(client, project):
    field = drawer(client.get(f"/p/{project}").text)
    accept = re.search(r'name="files"[^>]*accept="([^"]*)"', field)
    assert accept, "the file field lost its accept list"
    taken = set(accept.group(1).split(","))
    for ext in (".txt", ".md", ".docx", ".pdf", ".csv", ".mp3", ".wav", ".m4a", ".flac", ".ogg",
                ".mp4", ".m4v", ".mov", ".aac", ".opus", ".webm"):
        assert ext in taken, f"{ext} is not accepted"
        assert ext in field, f"{ext} is accepted but never named to the researcher"
    assert "transcribed" in field, "nothing says a recording is transcribed first"
    assert field.count('type="file"') == 1, "audio must go in the same field as documents"


def test_the_drawer_asks_who_is_in_the_recording_and_whether_to_name_the_voices(client, project):
    field = drawer(client.get(f"/p/{project}").text)
    assert '<textarea name="audio_note"' in field
    assert 'name="audio_clean"' in field and 'type="checkbox"' in field
    # The naming is what the description buys, and the second reading's price and its limit are
    # both decisions taken here, not after the upload.
    assert "numbered" in field and "named" in field
    assert "two model calls" in field
    assert "reword" in field
    # A researcher uploading a PDF must not be left wondering what these two fields will do.
    assert "ignored when the upload contains no recording" in field
    assert f'href="/guide?from=/p/{project}#recordings"' in field


def test_the_drawer_keeps_the_paste_path_and_one_submission(client, project):
    field = drawer(client.get(f"/p/{project}").text)
    assert field.count("<form") == 1, "the drawer is one form and one submission"
    assert 'name="name"' in field and '<textarea name="text"' in field


# ---- the receipt --------------------------------------------------------------------------

def steps(conn, mid: str) -> list[tuple[str, str]]:
    m = store.material(conn, mid)
    return [(s["label"], s["state"]) for s in context._analysis_steps(conn, m)]


def test_a_material_that_never_had_a_recording_has_the_four_steps(conn, grande):
    assert [s[0] for s in steps(conn, grande)] == ["Structure", "Angles", "Coding", "Synthesis"]


def test_a_recording_waiting_for_its_transcript_shows_the_step_it_is_waiting_on(conn, project,
                                                                               grande):
    recording(conn, grande, file="ellis.m4a", seconds=2760)
    assert steps(conn, grande)[0] == ("Transcription", "waiting")
    store.start_run(conn, project, "transcribe", grande, "Transcribing DP-40 Grande")
    assert steps(conn, grande)[0] == ("Transcription", "active")


def test_the_step_is_done_once_the_transcript_stands_in_the_material(conn, grande):
    """The file is kept only until it has been transcribed, so its absence is the fact — and the
    same receipt has to be right for a recording added before any run row was written for it."""
    recording(conn, grande, seconds=2760)
    assert steps(conn, grande)[0] == ("Transcription", "done")


def test_a_transcription_that_stopped_says_so_with_its_reason(conn, project, grande):
    recording(conn, grande, file="ellis.m4a", seconds=2760)
    rid = store.start_run(conn, project, "transcribe", grande, "Transcribing DP-40 Grande")
    store.finish_run(conn, rid, error="the recording could not be converted")
    first = context._analysis_steps(conn, store.material(conn, grande))[0]
    assert (first["label"], first["state"]) == ("Transcription", "failed")
    assert first["error"] == "the recording could not be converted"


# ---- the material page --------------------------------------------------------------------

def test_a_recording_being_transcribed_says_so_instead_of_showing_an_empty_reading(client, conn,
                                                                                   analysed):
    pid = analysed["pid"]
    # Until the transcript lands the material's text is a placeholder and it has no claims: this
    # is the page a researcher meets for the several minutes the transcription takes.
    mid = store.add_material(conn, pid, "Ellis interview", "Being transcribed.")
    recording(conn, mid, file="ellis.m4a", note=NOTE, seconds=2760)
    store.start_run(conn, pid, "transcribe", mid, "Transcribing Ellis interview")
    html = client.get(f"/p/{pid}/m/{mid}").text
    assert "This recording is being transcribed. The analysis starts when it is done" in html
    assert "Transcribed from a recording" not in html, "it has not been transcribed yet"
    assert "This material is being read in the background" not in html


def test_a_transcribed_material_says_where_its_text_came_from(client, conn, analysed):
    pid, mid = analysed["pid"], analysed["grande"]
    recording(conn, mid, note=NOTE, clean=1, seconds=2760)
    html = client.get(f"/p/{pid}/m/{mid}").text
    assert "Transcribed from a recording of 46 minutes." in html
    assert "A second reading named each voice" in html
    # The researcher's own words, unedited, and labelled as theirs.
    assert "Your description of the recording" in html and NOTE in html


def test_without_the_second_reading_the_page_says_the_voices_are_numbered(client, conn, analysed):
    pid, mid = analysed["pid"], analysed["grande"]
    recording(conn, mid, seconds=61)
    html = client.get(f"/p/{pid}/m/{mid}").text
    assert "Transcribed from a recording of 1 minute." in html
    assert "The voices are numbered as the transcriber separated them." in html
    assert "Your description of the recording" not in html, "there is no description to show"


def test_a_material_that_never_had_a_recording_says_nothing_about_one(client, conn, analysed):
    html = client.get(f"/p/{analysed['pid']}/m/{analysed['grande']}").text
    assert "Transcribed from a recording" not in html
    assert "Transcription" not in html


def test_a_stopped_transcription_is_not_reported_as_a_reading(client, conn, analysed):
    """Something else in the project is running, which is what used to make this page claim the
    material was being read while the only step it ever had had stopped."""
    pid = analysed["pid"]
    mid = store.add_material(conn, pid, "Ellis interview", "Being transcribed.")
    recording(conn, mid, file="ellis.m4a", seconds=2760)
    rid = store.start_run(conn, pid, "transcribe", mid, "Transcribing Ellis interview")
    store.finish_run(conn, rid, error="the recording could not be converted")
    store.start_run(conn, pid, "doc", analysed["grande"], "Writing what stands out in Grande")
    html = client.get(f"/p/{pid}/m/{mid}").text
    assert "The transcription stopped: the recording could not be converted" in html
    assert "This material is being read in the background" not in html
    assert "This recording is being transcribed" not in html
    # The wait is over, but there is no transcript: the head must not say it came from one.
    assert "Transcribed from a recording" not in html


def test_the_recording_pages_add_no_javascript(client, conn, analysed):
    """The run poller is the only script in this app, and nothing is running here."""
    pid, mid = analysed["pid"], analysed["grande"]
    recording(conn, mid, note=NOTE, clean=1, seconds=2760)
    for url in (f"/p/{pid}", f"/p/{pid}/m/{mid}", "/guide"):
        assert "<script" not in client.get(url).text.lower()


def test_the_recording_pages_do_not_speak_our_vocabulary(client, conn, analysed):
    pid, mid = analysed["pid"], analysed["grande"]
    recording(conn, mid, file="ellis.m4a", note=NOTE, clean=1, seconds=2760)
    for url in (f"/p/{pid}", f"/p/{pid}/m/{mid}", "/guide"):
        said = strip_material(re.sub(r"<code>.*?</code>", " ", client.get(url).text,
                                     flags=re.S)).lower()
        for word in context._BANNED:
            assert not re.search(rf"\b{re.escape(word)}s?\b", said), f"{word!r} on {url}"


# ---- the guide ----------------------------------------------------------------------------

def test_the_guide_answers_what_happens_to_a_recording(client):
    html = client.get("/guide").text
    assert 'id="recordings"' in html
    assert 'href="#recordings"' in html, "the contents list does not reach it"
    for said in ("Voxtral", "exactly as", "may not reword", "is not transcribed a second time"):
        assert said in html, f"the recordings section does not say: {said}"


def test_the_project_page_help_links_all_reach_a_real_section(client, conn, project, grande):
    from tests.test_p32_guide import SECTIONS, helps
    asked = helps(client.get(f"/p/{project}").text)
    assert "recordings" in asked, "the drawer lost its way to the recordings section"
    assert asked <= set(SECTIONS), f"help links at nothing: {sorted(asked - set(SECTIONS))}"
