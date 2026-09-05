"""P29 — a file is not a case, and recurrence is a proposal (audit findings 11 and 12).

Two files from one participant were two materials; a spreadsheet of forty respondents was one.
Both are true counts of files and neither can ground "this recurred across independent cases",
which is what *"in 3 of 4 materials"* was being read as — and what a candidate's automatic
promotion on two materials' live claims was printed as. So the researcher says which materials
are one case, every reach on every page counts those, and recurrence puts a question to them
instead of answering it.
"""
from __future__ import annotations

import pytest

from app import ingest, store

accounts = pytest.importorskip("app.accounts")


@pytest.fixture
def client(conn, monkeypatch):
    from fastapi.testclient import TestClient
    from app import main, pages, verbs
    for mod in (pages, verbs, accounts):
        monkeypatch.setattr(mod, "connection", lambda: conn, raising=False)
    return TestClient(main.app, follow_redirects=False)


@pytest.fixture
def corpus(conn, analysed, quote):
    """The analysed project plus a field note, so a case of two materials can be one of several.

    Three materials: the two interviews, which a researcher will call one participant, and a note
    that stands on its own. "Work and trade" runs through all three; "Leaving and arriving" only
    through the two interviews.
    """
    pid = analysed["pid"]
    text = ("The market opened late that winter. Nobody came down from the hill before noon. "
            "The bakery kept its shutters up until the road was clear.")
    note = store.add_material(conn, pid, "Field note", text)
    store.save_sentences(conn, note, ingest.sentences(text))
    store.save_frame(conn, note, kind="field_note", display="plain", title="Field note",
                     speakers=[], segments=[])
    sid, said = store.sentences(conn, note)[0]
    anchor = " ".join(said.split()[:8])
    store.save_moments(conn, note, analysed["themes"]["Work and trade"],
                       [{"claim": "the market kept its own hours", "anchor": anchor, "sid": sid}])
    # A theme only the note carries, so the second group is never empty and the heading over it
    # can be asserted with and without cases.
    solo = store.save_theme(conn, analysed["pid"], tid=None, name="Only in the note",
                            gist="one material so far", code_ids=[])
    store.save_moments(conn, note, solo,
                       [{"claim": "nobody came down", "anchor": anchor, "sid": sid}])
    return {**analysed, "note": note, "solo": solo}


def _pages(client, pid: str) -> list[str]:
    """Every page that prints a theme's reach, so one assertion covers all of them."""
    return [client.get(url).text
            for url in (f"/p/{pid}", f"/p/{pid}/record", f"/p/{pid}/export.md")]


def _grouped(client, pid: str) -> list[str]:
    """The two pages that group themes by reach. The overview groups by hold instead — a
    candidate is one material's pattern whatever else is true — so it is not one of them."""
    return [client.get(url).text for url in (f"/p/{pid}/record", f"/p/{pid}/export.md")]


# ---- reach counted over cases -------------------------------------------------------------------

def test_with_no_case_defined_the_wording_is_exactly_what_it_was(client, corpus):
    """Nothing changes for a project whose materials nobody has grouped. A material in no case is
    its own case, so counting cases and counting materials would give the same number — and the
    page says materials, because that is what its columns are."""
    for page in _pages(client, corpus["pid"]):
        assert "3 of 3 materials · 7 claims" in page
        assert "2 of 3 materials · 6 claims" in page
        assert "cases" not in page.split('id="themes"')[-1].split('id="materials"')[0]
    for page in _grouped(client, corpus["pid"]):
        assert "In one material so far" in page


def test_two_materials_in_one_case_count_as_one_in_reach(client, conn, corpus):
    """The two interviews are one participant. A theme carried by both of them is carried by one
    case, and the material count stays beside it because the columns are still materials."""
    store.add_case(conn, corpus["pid"], "Participant 1", [corpus["grande"], corpus["rodwin"]])
    for page in _pages(client, corpus["pid"]):
        assert "2 of 2 cases (3 materials) · 7 claims" in page, "the note is its own case"
        assert "1 of 2 cases (2 materials) · 6 claims" in page
        assert "of 3 materials ·" not in page, "no reach is still counted in files"


def test_a_theme_carried_by_one_case_is_grouped_with_the_singles(client, conn, corpus):
    """Two materials of one case are not recurrence, so the theme leaves the first group — and
    the heading over the second one follows what it is now counting."""
    pid = corpus["pid"]
    store.add_case(conn, pid, "Participant 1", [corpus["grande"], corpus["rodwin"]])
    for page in _grouped(client, pid):
        assert "In one material so far" not in page
        assert page.index("In one case so far") < page.rindex("Leaving and arriving")


def test_the_theme_page_derives_its_reach_the_same_way(client, conn, corpus):
    pid, tid = corpus["pid"], corpus["themes"]["Leaving and arriving"]
    assert "2 of 3 materials · 6 claims" in client.get(f"/p/{pid}/t/{tid}").text
    store.add_case(conn, pid, "Participant 1", [corpus["grande"], corpus["rodwin"]])
    assert "1 of 2 cases (2 materials) · 6 claims" in client.get(f"/p/{pid}/t/{tid}").text


# ---- making and unmaking a case -----------------------------------------------------------------

def test_a_case_is_made_from_materials_and_gives_one_back(client, conn, corpus):
    pid = corpus["pid"]
    r = client.post(f"/p/{pid}/cases",
                    data={"name": "Participant 1",
                          "material_id": [corpus["grande"], corpus["rodwin"]]})
    assert r.status_code == 303
    assert [c["name"] for c in store.cases(conn, pid)] == ["Participant 1"]
    assert client.post(f"/p/{pid}/cases/remove",
                       data={"material_id": corpus["rodwin"]}).status_code == 303
    assert store.case_of(conn, pid)[corpus["rodwin"]] == corpus["rodwin"], "its own case again"
    assert "2 of 3 materials · 6 claims" not in client.get(f"/p/{pid}").text, \
        "one material is still in a case, so the page still counts cases"


def test_a_case_of_the_same_name_takes_in_later_material(client, conn, corpus):
    """A participant's second interview arrives a week after the first. The form makes cases, so
    without this the researcher would have to rebuild the case every time."""
    pid = corpus["pid"]
    client.post(f"/p/{pid}/cases", data={"name": "P1", "material_id": [corpus["grande"]]})
    client.post(f"/p/{pid}/cases", data={"name": "P1", "material_id": [corpus["rodwin"]]})
    assert len(store.cases(conn, pid)) == 1
    of = store.case_of(conn, pid)
    assert of[corpus["grande"]] == of[corpus["rodwin"]]


def test_a_reader_cannot_make_a_case_or_break_one(client, conn, corpus):
    pid = corpus["pid"]
    people = {n: store.create_user(conn, n, "correct horse battery") for n in ("ann", "bob")}
    conn.execute("UPDATE project SET owner_id=? WHERE id=?", (people["ann"], pid))
    conn.commit()
    store.join(conn, store.add_invite(conn, pid, "read", None), people["bob"])
    assert client.post("/login", data={"name": "bob",
                                       "password": "correct horse battery"}).status_code == 303
    assert "Make a case" not in client.get(f"/p/{pid}").text
    assert client.post(f"/p/{pid}/cases", data={"name": "P1",
                                                "material_id": [corpus["grande"]]}).status_code == 404
    assert client.post(f"/p/{pid}/cases/remove",
                       data={"material_id": corpus["grande"]}).status_code == 404
    assert store.cases(conn, pid) == []


# ---- recurrence proposes; the researcher promotes -------------------------------------------------

def _candidate(conn, corpus, mids) -> str:
    """A candidate carrying one claim in each of `mids`."""
    tid = store.save_theme(conn, corpus["pid"], tid=None, name="Waiting out the winter",
                           gist="what is done while nothing moves", code_ids=[])
    store.set_hold(conn, tid, "candidate")
    for mid in mids:
        m = store.moments(conn, mid)[0]
        store.save_moments(conn, mid, tid,
                           [{"claim": "said here too", "anchor": m["anchor"], "sid": m["sid"]}])
    return tid


def test_a_candidate_two_cases_carry_is_proposed_and_not_promoted(client, conn, corpus):
    """The count is a question. It reaches the page as one, beside the control that answers it,
    and the theme is still a candidate until the researcher presses it."""
    pid = corpus["pid"]
    tid = _candidate(conn, corpus, [corpus["grande"], corpus["rodwin"]])
    assert store.propose_by_recurrence(conn, pid) == [tid]

    assert conn.execute("SELECT hold FROM theme WHERE id=?", (tid,)).fetchone()[0] == "candidate"
    for url in (f"/p/{pid}", f"/p/{pid}/t/{tid}"):
        page = client.get(url).text
        assert "Found in 2 materials — promote?" in page, url
        assert f'action="/p/{pid}/t/{tid}/promote"' in page, url


def test_the_proposal_counts_cases_where_the_researcher_has_defined_them(client, conn, corpus):
    pid = corpus["pid"]
    tid = _candidate(conn, corpus, [corpus["grande"], corpus["note"]])
    store.add_case(conn, pid, "Participant 1", [corpus["grande"], corpus["rodwin"]])
    assert store.propose_by_recurrence(conn, pid) == [tid]
    assert "Found in 2 cases — promote?" in client.get(f"/p/{pid}/t/{tid}").text


def test_two_materials_of_one_case_do_not_propose_anything(conn, corpus):
    """The whole point of finding 12: two files from one participant are one case, and one case
    saying a thing twice is the same person saying it twice."""
    pid = corpus["pid"]
    tid = _candidate(conn, corpus, [corpus["grande"], corpus["rodwin"]])
    store.add_case(conn, pid, "Participant 1", [corpus["grande"], corpus["rodwin"]])
    assert store.propose_by_recurrence(conn, pid) == []
    assert conn.execute("SELECT proposed_at FROM theme WHERE id=?", (tid,)).fetchone()[0] is None


def test_a_proposal_is_withdrawn_when_the_claims_fall_back_under_two_cases(conn, corpus):
    pid = corpus["pid"]
    tid = _candidate(conn, corpus, [corpus["grande"], corpus["rodwin"]])
    assert store.propose_by_recurrence(conn, pid) == [tid]
    store.add_case(conn, pid, "Participant 1", [corpus["grande"], corpus["rodwin"]])

    assert store.propose_by_recurrence(conn, pid) == [], "nothing newly proposed"
    assert conn.execute("SELECT proposed_at FROM theme WHERE id=?", (tid,)).fetchone()[0] is None


def test_the_researcher_still_promotes_from_the_proposal(client, conn, corpus):
    pid = corpus["pid"]
    tid = _candidate(conn, corpus, [corpus["grande"], corpus["rodwin"]])
    store.propose_by_recurrence(conn, pid)
    assert client.post(f"/p/{pid}/t/{tid}/promote").status_code == 303
    assert conn.execute("SELECT hold FROM theme WHERE id=?", (tid,)).fetchone()[0] == "open"
    assert tid in [t["id"] for t in store.live_themes(conn, pid)]
