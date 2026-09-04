"""P20 — a project is its owner's, and other people get in by invitation only.

    store.access(conn, pid, user_row) -> 'owner' | 'edit' | 'read' | None
    store.add_invite / invites / revoke_invite / join / members / remove_member
    store.projects_for -> owned and shared, each with `role` and `owner_name`

Routes: GET /p/{pid}/share (owner) · POST /p/{pid}/share/link · .../share/revoke ·
.../share/remove · GET /join/{token}.

The rule these tests exist for: an administrator makes accounts and resets passwords, and that is
not a way into anybody's material. Nothing in here is 403 — a project that is not open to you is
404, because its existence is not yours to learn either.
"""
from __future__ import annotations

import pytest

from app import store

accounts = pytest.importorskip("app.accounts")


@pytest.fixture
def client(conn, monkeypatch):
    from fastapi.testclient import TestClient
    from app import main, pages, verbs
    for mod in (pages, verbs, accounts):
        monkeypatch.setattr(mod, "connection", lambda: conn, raising=False)
    return TestClient(main.app, follow_redirects=False)


def second_browser():
    """A second browser on the same database — `client` has already pointed the app at it."""
    from fastapi.testclient import TestClient
    from app import main
    return TestClient(main.app, follow_redirects=False)


@pytest.fixture
def people(conn):
    return {"admin": store.create_user(conn, "ada", "correct horse", is_admin=True),
            "ann": store.create_user(conn, "ann", "battery staple"),
            "bob": store.create_user(conn, "bob", "purple monkey")}


def login(client, name, pw, **data):
    r = client.post("/login", data={"name": name, "password": pw, **data})
    assert r.status_code == 303, r.text
    return r


@pytest.fixture
def anns(conn, people):
    return store.create_project(conn, "Ann's study", "", owner_id=people["ann"])


def link(client, pid, role):
    """The token of a fresh invitation, read back off the owner's share page."""
    assert client.post(f"/p/{pid}/share/link", data={"role": role}).status_code == 303
    page = client.get(f"/p/{pid}/share").text
    return page.split("/join/")[-1].split('"')[0]


# ---- the boundary --------------------------------------------------------------------------------

def test_an_administrator_cannot_open_work_that_is_not_theirs(client, conn, people, anns):
    """The requirement in one test. Making accounts is not a reason to read the interviews in
    them, and an admin who could would be a second copy of every researcher's material."""
    login(client, "ada", "correct horse")
    assert client.get(f"/p/{anns}").status_code == 404
    assert client.get(f"/p/{anns}/record").status_code == 404
    assert client.get(f"/p/{anns}/export.md").status_code == 404
    assert client.get(f"/p/{anns}/share").status_code == 404
    assert client.post(f"/p/{anns}/focus", data={"focus": "mine now"}).status_code == 404
    assert "Ann's study" not in client.get("/").text, "nor is it on their list of projects"
    assert "Ann's study" in client.get("/admin").text, "the admin page still names it, to hand over"


def test_an_administrator_cannot_take_a_project_by_giving_it_to_themselves(client, conn, people,
                                                                          anns):
    """Reassignment stays for a project nobody owns — one made before accounts existed, or one
    whose owner was deleted — and is refused for every other, or it is the hole itself."""
    login(client, "ada", "correct horse")
    r = client.post("/admin/owner", data={"project_id": anns, "user_id": people["admin"]})
    assert r.status_code == 303 and "already+has+an+owner" in r.headers["location"]
    assert store.project(conn, anns)["owner_id"] == people["ann"]
    assert client.get(f"/p/{anns}").status_code == 404
    orphan = store.create_project(conn, "Made before accounts existed", "")
    assert client.post("/admin/owner",
                       data={"project_id": orphan, "user_id": people["bob"]}).status_code == 303
    assert store.project(conn, orphan)["owner_id"] == people["bob"]


def test_a_database_with_no_accounts_opens_everything(client, conn):
    """The laptop, unchanged: no accounts, no sign-in, every project open."""
    pid = store.create_project(conn, "On a laptop", "")
    assert store.access(conn, pid, None) == "owner"
    assert client.get(f"/p/{pid}").status_code == 200
    assert client.post(f"/p/{pid}/focus", data={"focus": "the crossing"}).status_code == 303
    assert store.project(conn, pid)["focus"] == "the crossing"


# ---- invitations ---------------------------------------------------------------------------------

def test_a_read_only_link_opens_the_project_and_refuses_every_change(client, conn, people, anns):
    login(client, "ann", "battery staple")
    token = link(client, anns, "read")
    client.post("/logout")
    login(client, "bob", "purple monkey")
    assert client.get(f"/p/{anns}").status_code == 404, "before the link, nothing"
    assert client.get(f"/join/{token}").headers["location"] == f"/p/{anns}"
    assert client.get(f"/p/{anns}").status_code == 200
    assert client.get(f"/p/{anns}/record").status_code == 200
    r = client.post(f"/p/{anns}/focus", data={"focus": "not his to set"})
    assert r.status_code == 404, "reading is not editing, and the refusal says nothing else"
    assert store.project(conn, anns)["focus"] == ""
    home = client.get("/").text
    assert "Ann's study" in home and "Shared by ann" in home and "read only" in home


def test_a_collaborate_link_allows_the_change_and_raises_a_reader(client, conn, people, anns):
    login(client, "ann", "battery staple")
    read_link, edit_link = link(client, anns, "read"), link(client, anns, "edit")
    client.post("/logout")
    login(client, "bob", "purple monkey")
    client.get(f"/join/{read_link}")
    assert store.access(conn, anns, store.verify_user(conn, "bob", "purple monkey")) == "read"
    client.get(f"/join/{edit_link}")
    assert store.access(conn, anns, store.verify_user(conn, "bob", "purple monkey")) == "edit"
    assert client.post(f"/p/{anns}/focus", data={"focus": "work and the crossing"}).status_code == 303
    assert store.project(conn, anns)["focus"] == "work and the crossing"
    client.get(f"/join/{read_link}")
    assert store.access(conn, anns, store.verify_user(conn, "bob", "purple monkey")) == "edit", \
        "a second link is not a demotion anybody asked for"
    assert client.get(f"/p/{anns}/share").status_code == 404, "sharing on is the owner's alone"
    assert client.post(f"/p/{anns}/share/link", data={"role": "edit"}).status_code == 404


def test_a_revoked_link_lets_nobody_new_in(client, conn, people, anns):
    login(client, "ann", "battery staple")
    token = link(client, anns, "read")
    assert client.post(f"/p/{anns}/share/revoke", data={"token": token}).status_code == 303
    assert f"/join/{token}" not in client.get(f"/p/{anns}/share").text
    client.post("/logout")
    login(client, "bob", "purple monkey")
    r = client.get(f"/join/{token}")
    assert r.status_code == 404 and "no longer open" in r.text
    assert "Ann's study" not in r.text, "a dead link says nothing about what it was for"
    assert client.get(f"/p/{anns}").status_code == 404


def test_the_owner_can_remove_a_member(client, conn, people, anns):
    login(client, "ann", "battery staple")
    token = link(client, anns, "edit")
    bob = second_browser()
    login(bob, "bob", "purple monkey")
    bob.get(f"/join/{token}")
    assert bob.get(f"/p/{anns}").status_code == 200
    assert "bob" in client.get(f"/p/{anns}/share").text
    assert client.post(f"/p/{anns}/share/remove",
                       data={"user_id": people["bob"]}).status_code == 303
    assert bob.get(f"/p/{anns}").status_code == 404
    assert bob.post(f"/p/{anns}/focus", data={"focus": "still not"}).status_code == 404


def test_an_invitation_works_from_a_cold_link(client, conn, people, anns):
    """Clicked while signed out: the sign-in remembers where they were going, so they land on the
    project rather than on a home page that does not yet list it."""
    login(client, "ann", "battery staple")
    token = link(client, anns, "read")
    client.post("/logout")
    r = client.get(f"/join/{token}")
    assert r.status_code == 303 and r.headers["location"] == f"/login?next=%2Fjoin%2F{token}"
    assert f'value="/join/{token}"' in client.get(f"/login?next=%2Fjoin%2F{token}").text
    r = login(client, "bob", "purple monkey", next=f"/join/{token}")
    assert r.headers["location"] == f"/join/{token}"
    assert client.get(f"/join/{token}").headers["location"] == f"/p/{anns}"


def test_a_next_that_leaves_this_site_is_ignored(client, people):
    """An open redirect on the sign-in page hands a phisher a page on our own host that lands the
    researcher, freshly signed in, somewhere else."""
    for away in ("https://example.invalid/", "//example.invalid/", "/\\example.invalid"):
        r = login(client, "ann", "battery staple", next=away)
        assert r.headers["location"] == "/", away
        client.post("/logout")
    assert login(client, "ann", "battery staple", next="/account").headers["location"] == "/account"
