"""P10 — accounts. `app/accounts.py` (users, sessions, the admin page); the PIN gate is deleted.

    store.create_user(conn, name, password, is_admin=False) -> uid
    store.verify_user(conn, name, password) -> row | None          (scrypt, stdlib)
    store.users(conn) -> rows
    project.owner_id; store.create_project(conn, name, focus, owner_id)
    store.projects_for(conn, user_row) -> rows      (their own; every project for an admin)

Routes: GET/POST /login · POST /logout · GET /admin (admins only) · POST /admin/users.
Signed out, everything but /health, /static and /login redirects to /login.
A project that is not yours is 404, not 403 — its existence is not yours either.
On first boot, APERTURE_ADMIN=name:password creates the first admin if no user exists.
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


def login(client, name, pw):
    r = client.post("/login", data={"name": name, "password": pw})
    assert r.status_code == 303, r.text
    return r


@pytest.fixture
def people(conn):
    return {"admin": store.create_user(conn, "ada", "correct horse", is_admin=True),
            "ann": store.create_user(conn, "ann", "battery staple"),
            "bob": store.create_user(conn, "bob", "purple monkey")}


def test_a_password_is_never_stored_and_verifies_only_when_right(conn, people):
    row = conn.execute("SELECT * FROM user WHERE name='ann'").fetchone()
    assert "battery staple" not in " ".join(str(v) for v in tuple(row))
    assert store.verify_user(conn, "ann", "battery staple")["id"] == people["ann"]
    assert store.verify_user(conn, "ann", "wrong") is None
    assert store.verify_user(conn, "nobody", "battery staple") is None


def test_signed_out_everything_goes_to_login_except_what_the_container_needs(client, people):
    for url in ("/", "/p/anything", "/admin"):
        r = client.get(url)
        assert r.status_code == 303 and r.headers["location"].startswith("/login"), url
    assert client.get("/health").status_code == 200
    assert client.get("/login").status_code == 200


def test_a_user_sees_their_projects_and_nobody_elses(client, conn, people):
    mine = store.create_project(conn, "Ann's study", "", owner_id=people["ann"])
    theirs = store.create_project(conn, "Bob's study", "", owner_id=people["bob"])
    login(client, "ann", "battery staple")
    home = client.get("/").text
    assert "Ann's study" in home and "Bob's study" not in home
    assert client.get(f"/p/{mine}").status_code == 200
    assert client.get(f"/p/{theirs}").status_code == 404, "not 403: its existence is not hers"
    assert client.get(f"/p/{theirs}/runs").status_code == 404, "nor is what it is doing"
    assert client.get("/admin").status_code == 404


def test_an_admin_sees_everything_and_can_make_a_user(client, conn, people):
    store.create_project(conn, "Bob's study", "", owner_id=people["bob"])
    login(client, "ada", "correct horse")
    admin = client.get("/admin")
    assert admin.status_code == 200 and "Bob's study" in admin.text and "bob" in admin.text
    r = client.post("/admin/users", data={"name": "cyd", "password": "open sesame"})
    assert r.status_code == 303
    assert store.verify_user(conn, "cyd", "open sesame") is not None
    client.post("/logout")
    login(client, "cyd", "open sesame")
    assert client.get("/admin").status_code == 404, "a made user is not an admin"


def test_a_new_project_belongs_to_whoever_made_it(client, conn, people):
    login(client, "bob", "purple monkey")
    r = client.post("/p/new", data={"name": "Bob's new one", "focus": ""})
    assert r.status_code == 303
    pid = r.headers["location"].rsplit("/", 1)[-1]
    assert store.project(conn, pid)["owner_id"] == people["bob"]


def test_logout_ends_the_session(client, people):
    login(client, "ann", "battery staple")
    assert client.get("/").status_code == 200
    client.post("/logout")
    assert client.get("/").status_code == 303


def test_the_first_admin_comes_from_the_environment_once(conn, monkeypatch):
    monkeypatch.setenv("APERTURE_ADMIN", "root:first light")
    accounts.bootstrap(conn)
    assert store.verify_user(conn, "root", "first light")["is_admin"]
    store.create_user(conn, "later", "x")
    monkeypatch.setenv("APERTURE_ADMIN", "root2:should not happen")
    accounts.bootstrap(conn)
    assert store.verify_user(conn, "root2", "should not happen") is None, "only when no user exists"


def test_the_pin_gate_is_gone():
    from app import auth
    assert not hasattr(auth, "PinAuth"), "accounts replace the PIN; two gates is one too many"


def test_an_admin_is_told_when_data_is_not_on_persistent_storage(client, conn, people, monkeypatch):
    """A redeploy on to an unmounted data directory starts from an empty database — the loss the
    predecessor project already suffered once. The page says so, to administrators, while true."""
    import os
    login(client, "ada", "correct horse")
    monkeypatch.setenv("APERTURE_DATA_DIR", "/data")
    monkeypatch.setattr(os.path, "ismount", lambda p: False)
    assert "not on persistent storage" in client.get("/").text
    monkeypatch.setattr(os.path, "ismount", lambda p: True)
    assert "not on persistent storage" not in client.get("/").text
    client.post("/logout")
    login(client, "ann", "battery staple")
    monkeypatch.setattr(os.path, "ismount", lambda p: False)
    assert "not on persistent storage" not in client.get("/").text, "an ordinary user cannot act on it"


def test_a_user_can_change_their_own_password_and_only_with_the_current_one(client, conn, people):
    """The first admin's password arrives through an environment variable that the deployment
    log prints in clear; being able to change it is the fix, not a nicety."""
    assert client.get("/account").status_code == 303, "signed out, there is nothing to change"
    login(client, "ann", "battery staple")
    assert client.get("/account").status_code == 200
    r = client.post("/account", data={"current": "wrong", "new": "new-and-long", "again": "new-and-long"})
    assert r.status_code == 303 and "problem=" in r.headers["location"]
    assert store.verify_user(conn, "ann", "battery staple") is not None, "nothing changed"
    r = client.post("/account", data={"current": "battery staple", "new": "new-and-long", "again": "different"})
    assert "problem=" in r.headers["location"]
    r = client.post("/account", data={"current": "battery staple", "new": "new-and-long", "again": "new-and-long"})
    assert r.status_code == 303 and "problem=" not in r.headers["location"]
    assert store.verify_user(conn, "ann", "new-and-long") is not None
    assert store.verify_user(conn, "ann", "battery staple") is None
