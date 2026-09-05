"""P23 — candidate, open, frozen (PLAN.md §12).

A four-interview project came back with twelve themes, eleven of them "in 4 of 4", and no way to
say that one of them was finished. Three holds answer it: a pattern in one material is a
*candidate*, a project theme still developing is *open*, and a theme the researcher has declared
final is *frozen* — after which new material is applied to it and what pulls against it comes back
as a note beside it rather than as a rewrite of its gist.

These are the pages' half: the two verbs, what each page shows, and who may press anything.
"""
from __future__ import annotations

import re

import pytest

from app import db, store

accounts = pytest.importorskip("app.accounts")


@pytest.fixture
def client(conn, monkeypatch):
    from fastapi.testclient import TestClient
    from app import main, pages, verbs
    for mod in (pages, verbs, accounts):
        monkeypatch.setattr(mod, "connection", lambda: conn, raising=False)
    return TestClient(main.app, follow_redirects=False)


@pytest.fixture
def holds(conn, quote, analysed):
    """The analysed project, plus a candidate in each material — one per material, which is what
    makes a candidate a candidate."""
    pid, grande, rodwin = analysed["pid"], analysed["grande"], analysed["rodwin"]
    out = dict(analysed)
    for key, mid, name, at in (("here", grande, "Only in Grande", 150),
                               ("there", rodwin, "Only in Rodwin", 150)):
        tid = store.save_theme(conn, pid, tid=None, name=name, gist="one material so far",
                               code_ids=[])
        sid, text = quote(mid, at=at)
        store.save_moments(conn, mid, tid, [{"claim": f"{name} says so",
                                             "anchor": " ".join(text.split()[:8]), "sid": sid}])
        store.set_hold(conn, tid, "candidate")
        out[key] = tid
    out["work"] = analysed["themes"]["Work and trade"]
    out["leaving"] = analysed["themes"]["Leaving and arriving"]
    return out


def note(conn, tid: str, mid: str, text: str, at: str = "2026-09-03T09:00:00+00:00") -> None:
    """A tension note, as the engine writes one: what pulled against a frozen definition, in the
    material it was read in."""
    conn.execute("INSERT INTO theme_note (id, theme_id, material_id, run_id, text, created_at) "
                 "VALUES (?,?,?,?,?,?)", (db.new_id("tn"), tid, mid, None, text, at))
    conn.commit()


# ---- the two verbs -------------------------------------------------------------------------------

def test_freezing_and_unfreezing_are_one_click_each(client, conn, holds):
    pid, tid = holds["pid"], holds["work"]
    assert client.post(f"/p/{pid}/t/{tid}/hold", data={"hold": "frozen"}).status_code == 303
    assert store.live_themes(conn, pid) and _hold(conn, tid) == "frozen"
    assert client.post(f"/p/{pid}/t/{tid}/hold", data={"hold": "open"}).status_code == 303
    assert _hold(conn, tid) == "open"


def test_a_hold_the_app_does_not_have_is_refused(client, conn, holds):
    """`candidate` included: a theme is demoted by nobody. Recurrence made it a theme."""
    pid, tid = holds["pid"], holds["work"]
    for bad in ("candidate", "merged", "", "OPEN"):
        assert client.post(f"/p/{pid}/t/{tid}/hold", data={"hold": bad}).status_code == 404
    assert _hold(conn, tid) == "open"


def test_a_theme_in_another_project_is_not_reachable_through_this_ones_url(client, conn, holds):
    """The theme id arrives in the URL, so editing one project must not be a way into another."""
    other = store.create_project(conn, "Someone else's", "")
    theirs = store.save_theme(conn, other, tid=None, name="Theirs", gist="", code_ids=[])
    assert client.post(f"/p/{holds['pid']}/t/{theirs}/hold",
                       data={"hold": "frozen"}).status_code == 404
    assert client.post(f"/p/{holds['pid']}/t/{theirs}/promote").status_code == 404
    assert _hold(conn, theirs) == "open"


def test_promoting_a_candidate_makes_it_a_project_theme(client, conn, holds):
    pid, tid = holds["pid"], holds["here"]
    assert tid not in [t["id"] for t in store.live_themes(conn, pid)]
    assert client.post(f"/p/{pid}/t/{tid}/promote").status_code == 303
    assert _hold(conn, tid) == "open"
    assert tid in [t["id"] for t in store.live_themes(conn, pid)]


def _hold(conn, tid: str) -> str:
    return conn.execute("SELECT hold FROM theme WHERE id=?", (tid,)).fetchone()["hold"]


# ---- who may press anything ----------------------------------------------------------------------

@pytest.fixture
def invited(conn, holds):
    """The project as somebody's, with a second account invited to read it and a third to edit."""
    people = {n: store.create_user(conn, n, "correct horse battery") for n in ("ann", "bob", "cat")}
    conn.execute("UPDATE project SET owner_id=? WHERE id=?", (people["ann"], holds["pid"]))
    conn.commit()
    for name, role in (("bob", "read"), ("cat", "edit")):
        store.join(conn, store.add_invite(conn, holds["pid"], role, None), people[name])
    return people


def login(client, name):
    assert client.post("/login", data={"name": name,
                                       "password": "correct horse battery"}).status_code == 303


def test_a_reader_is_shown_no_controls_and_cannot_post_one(client, conn, holds, invited):
    pid, tid, cand = holds["pid"], holds["work"], holds["here"]
    login(client, "bob")
    r = client.get(f"/p/{pid}/t/{tid}")
    assert r.status_code == 200, "a reader still reads everything"
    theme = r.text
    assert "Open" in theme, "the hold itself is part of the reading, and everyone sees it"
    assert "Freeze" not in theme and "/hold" not in theme
    assert "Promote" not in client.get(f"/p/{pid}").text
    assert client.post(f"/p/{pid}/t/{tid}/hold", data={"hold": "frozen"}).status_code == 404
    assert client.post(f"/p/{pid}/t/{cand}/promote").status_code == 404
    assert _hold(conn, tid) == "open"


def test_an_invited_editor_is_shown_them_and_may_press_them(client, conn, holds, invited):
    pid, tid, cand = holds["pid"], holds["work"], holds["here"]
    login(client, "cat")
    assert client.get(f"/p/{pid}/t/{tid}").status_code == 200
    assert "Freeze" in client.get(f"/p/{pid}/t/{tid}").text
    assert "Promote" in client.get(f"/p/{pid}").text
    assert client.post(f"/p/{pid}/t/{tid}/hold", data={"hold": "frozen"}).status_code == 303
    assert client.post(f"/p/{pid}/t/{cand}/promote").status_code == 303
    assert (_hold(conn, tid), _hold(conn, cand)) == ("frozen", "open")


# ---- the pages -----------------------------------------------------------------------------------

def _themes(html: str) -> str:
    return html.split('id="themes"', 1)[1].split('id="materials"', 1)[0]


def test_the_overview_leads_with_the_frozen_and_ends_with_the_candidates(client, conn, holds):
    """A frozen theme comes first however far the open ones reach: it is what the rest is now
    read against. Candidates are the second group, each with the control that ends it."""
    pid = holds["pid"]
    _claims(conn, holds, holds["work"], 6)          # the open theme carries the most claims
    sect = _themes(client.get(f"/p/{pid}").text)
    assert sect.index("Work and trade") < sect.index("Leaving and arriving"), \
        "claims order the open themes, as they always did"
    store.set_hold(conn, holds["leaving"], "frozen")
    sect = _themes(client.get(f"/p/{pid}").text)
    assert sect.index("Leaving and arriving") < sect.index("Work and trade"), \
        "frozen first, though the open theme carries more claims"
    assert "Frozen</span>" in sect
    across, single = sect.index("Across materials"), sect.index("In one material so far")
    assert across < sect.index("Leaving and arriving") < single
    assert single < sect.index("Only in Grande") and single < sect.index("Only in Rodwin")
    assert f'action="/p/{pid}/t/{holds["here"]}/promote"' in sect


def _claims(conn, holds, tid: str, n: int) -> None:
    rows = [dict(m) for m in store.moments(conn, holds["grande"])][:1] * n
    store.save_moments(conn, holds["grande"], tid,
                       [{"claim": f"more {i}", "anchor": r["anchor"], "sid": r["sid"]}
                        for i, r in enumerate(rows)])


def test_unchanged_for_is_said_at_three_passes_and_only_while_the_theme_is_open(client, conn,
                                                                                holds):
    """The count is bookkeeping — Python compares one fingerprint per pass — and it is shown
    beside Freeze because the researcher freezes, not the instrument.

    Passes, not materials: the count rises on a rerun of one material too, and "stable for 3
    materials" read as saturation across three cases, which is a claim nothing here measured.
    """
    pid, tid = holds["pid"], holds["work"]
    url = f"/p/{pid}/t/{tid}"
    conn.execute("UPDATE theme SET stable_passes=2 WHERE id=?", (tid,))
    conn.commit()
    assert "unchanged for" not in client.get(url).text
    conn.execute("UPDATE theme SET stable_passes=3 WHERE id=?", (tid,))
    conn.commit()
    page = client.get(url).text
    assert "unchanged for 3 passes" in page
    assert "stable for" not in page, "passes are not materials and must not be called them"
    store.set_hold(conn, tid, "frozen")
    page = client.get(url).text
    assert "unchanged for" not in page, "a frozen theme is not still steadying"
    assert "Frozen" in page and "Unfreeze" in page


def test_a_candidates_page_says_so_and_offers_the_one_way_out(client, holds):
    page = client.get(f"/p/{holds['pid']}/t/{holds['here']}").text
    assert "Candidate — found in one material so far" in page
    assert "Promote" in page and "Freeze" not in page


def test_a_frozen_theme_shows_what_has_pulled_against_it_and_where_from(client, conn, holds):
    """The notes are the case for unfreezing, so each carries the material it was raised in."""
    pid, tid = holds["pid"], holds["work"]
    url = f"/p/{pid}/t/{tid}"
    note(conn, tid, holds["rodwin"], "Here the trade is unpaid and family, not work.")
    assert "pulled against" not in client.get(url).text, "an open theme is still being written"
    store.set_hold(conn, tid, "frozen")
    page = client.get(url).text
    assert "What has pulled against this definition" in page
    assert "Here the trade is unpaid and family, not work." in page
    row = re.search(r"<li[^>]*>((?:(?!</li>).)*unpaid and family(?:(?!</li>).)*)</li>", page, re.S)
    assert row and "Rodwin" in row.group(1), "the material the note came from, beside the note"


def test_a_material_shows_its_own_candidates_and_no_other_materials(client, holds):
    page = client.get(f"/p/{holds['pid']}/m/{holds['grande']}").text
    assert "Only in Grande" in page and "Candidate</span>" in page
    assert "Only in Rodwin" not in page, "a candidate belongs to the material that holds it"
    assert "Work and trade" in page, "every project theme is still read here"


def test_the_record_prints_each_hold_and_the_notes_under_the_theme(client, conn, holds):
    pid = holds["pid"]
    store.set_hold(conn, holds["leaving"], "frozen")
    note(conn, holds["leaving"], holds["grande"], "The arrival is not spoken of as leaving.")
    for url in (f"/p/{pid}/record", f"/p/{pid}/export.md"):
        text = _themes(client.get(url).text) if "record" in url else client.get(url).text
        assert "· frozen" in text and "· open" in text and "· candidate" in text, url
        assert "What has pulled against this definition" in text, url
        assert "The arrival is not spoken of as leaving." in text, url
        assert "Grande" in text
