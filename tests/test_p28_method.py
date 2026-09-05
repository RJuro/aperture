"""P28 — the method is a choice the researcher makes, and the reading obeys it.

    project.method ∈ 'explore' | 'iterative'
    store.set_method / codes_only_in / codes_elsewhere / merge_code / note_code
    app/engine/reconcile.py — the comparison an exploratory reading needs afterwards

Every project until now was built iteratively: READ was shown the whole project codebook and told
to reuse before inventing, ANGLES was shown the themes. The tool promised each material was read
on its own terms, and it was not. These tests hold the two methods apart — what each shows the
model, what each plans — and hold the migration that leaves existing projects as they were.
"""
from __future__ import annotations

import sqlite3

import pytest

from app import db, jobs, store
from app.engine import angles, read, reconcile

accounts = pytest.importorskip("app.accounts")


def _sids(conn, mid: str, n: int = 1) -> list[str]:
    return [s for s, _ in store.sentences(conn, mid)[:n]]


def _coded(conn, pid: str, mid: str, name: str, definition: str, n: int = 1) -> None:
    store.save_codes(conn, pid, mid,
                     [{"name": name, "definition": definition, "sids": _sids(conn, mid, n)}])


# ---- the column ---------------------------------------------------------------------------------

def test_a_new_project_explores_and_an_older_one_is_left_building_iteratively(conn, tmp_path):
    """The default is the promise the tool makes; the migration is the promise it already made to
    projects that exist. A researcher whose corpus was read one way must not find, after an
    upgrade, that the next material was read another."""
    assert store.project(conn, store.create_project(conn, "New work"))["method"] == "explore"

    path = tmp_path / "before-the-choice.db"
    old = sqlite3.connect(path)
    old.execute("CREATE TABLE project (id TEXT PRIMARY KEY, name TEXT NOT NULL, "
                "focus TEXT DEFAULT '', brief TEXT DEFAULT '', created_at TEXT NOT NULL, "
                "removed_at TEXT)")
    old.execute("INSERT INTO project (id, name, created_at) VALUES ('pold','Older work','2026-01')")
    old.commit()
    old.close()
    migrated = db.connect(path)
    assert store.project(migrated, "pold")["method"] == "iterative"
    migrated.close()


def test_the_method_is_one_of_two_things_and_anything_else_is_refused(conn):
    pid = store.create_project(conn, "New work")
    assert store.set_method(conn, pid, "iterative") is True
    assert store.project(conn, pid)["method"] == "iterative"
    assert store.set_method(conn, pid, "grounded theory") is False
    assert store.project(conn, pid)["method"] == "iterative", "and nothing was written"
    other = store.create_project(conn, "Third", method="whatever the form said")
    assert store.project(conn, other)["method"] == "explore"


# ---- what the reading is shown ------------------------------------------------------------------

def test_an_exploratory_reading_is_shown_no_project_codes(conn, project, grande, rodwin, model):
    # A name the prompt's own worked example does not use, or this would pass on the example.
    _coded(conn, project, rodwin, "Papers and permits", "Passages about documents.")
    model.queue({"codes": []})
    read.run(conn, grande)
    shown = model.shown("read")
    assert "Papers and permits" not in shown, "the codebook prescribes nothing about this material"
    assert read.NO_CODEBOOK in shown
    assert read.MODE_RULE["explore"] in shown
    assert read.MODE_RULE["iterative"] not in shown


def test_an_iterative_reading_is_shown_the_codebook_and_told_to_reuse_it(conn, project, grande,
                                                                         rodwin, model):
    _coded(conn, project, rodwin, "Papers and permits", "Passages about documents.")
    store.set_method(conn, project, "iterative")
    model.queue({"codes": []})
    read.run(conn, grande)
    shown = model.shown("read")
    assert "Papers and permits" in shown and "Passages about documents." in shown
    assert read.MODE_RULE["iterative"] in shown
    assert read.NO_CODEBOOK not in shown


def test_an_exploratory_ideation_is_shown_no_themes(conn, project, grande, model):
    """The questions still travel — they are questions, and law 5 lets those forward. What the
    corpus has been grouped into does not."""
    store.save_theme(conn, project, tid=None, name="Work and trade", gist="how a living is made",
                     code_ids=[])
    store.save_summary(conn, "material", grande, "orientation", "A 1978 oral history.")
    store.set_brief(conn, project, "What did the crossing cost?")
    model.queue({"field": "Migration", "subareas": [], "angles": []})
    angles.run(conn, grande)
    shown = model.shown("angles")
    assert "Work and trade" not in shown and "how a living is made" not in shown
    assert angles.NO_THEMES in shown
    assert "What did the crossing cost?" in shown, "the open questions are unaffected"


# ---- the comparison that follows an exploratory reading -----------------------------------------

@pytest.fixture
def two_readings(conn, project, grande, rodwin):
    """One material's own codes beside a vocabulary another material already carries."""
    _coded(conn, project, rodwin, "Leaving home", "Passages about departure.")
    _coded(conn, project, grande, "Sea crossing", "Passages about the voyage itself.", n=2)
    return {"pid": project, "mid": grande}


def test_the_comparison_is_shown_this_reading_s_codes_and_the_project_s(conn, two_readings, model):
    model.queue({"relations": []})
    out = reconcile.run(conn, two_readings["mid"])
    shown = model.shown("reconcile")
    assert "Sea crossing" in shown and "Passages about the voyage itself." in shown
    assert "Leaving home" in shown and "Passages about departure." in shown
    example = store.sentences(conn, two_readings["mid"])[0][1]
    assert example[:40] in shown, "and one sentence the code was put on"
    assert out["considered"] == 1


def test_the_same_code_is_merged_and_keeps_its_place_in_a_theme(conn, two_readings, model):
    pid, mid = two_readings["pid"], two_readings["mid"]
    local = store.codes_only_in(conn, pid, mid)[0]
    keeper = store.codes_elsewhere(conn, pid, mid)[0]
    tid = store.save_theme(conn, pid, tid=None, name="Leaving", gist="departure and after",
                           code_ids=[local["id"]])
    model.queue({"relations": [{"local": "Sea crossing", "relation": "same",
                                "project": "Leaving home", "why": "one name covers both"}]})
    assert reconcile.run(conn, mid)["merged"] == 1
    assert [c["name"] for c in store.codebook(conn, pid)] == ["Leaving home"]
    assert {h["name"] for h in store.hits(conn, mid)} == {"Leaving home"}
    assert len(store.hits(conn, mid)) == 2, "the reading's own sentences, under the other name"
    assert [c["id"] for c in store.theme_codes(conn, tid)] == [keeper["id"]]


def test_a_narrower_code_is_left_standing_and_the_relation_is_written_beside_it(conn, two_readings,
                                                                                model):
    pid, mid = two_readings["pid"], two_readings["mid"]
    model.queue({"relations": [{"local": "Sea crossing", "relation": "narrower",
                                "project": "Leaving home",
                                "why": "the crossing is one part of leaving"}]})
    assert reconcile.run(conn, mid) == {"considered": 1, "merged": 0, "noted": 1, "dropped": []}
    row = next(c for c in store.codebook(conn, pid) if c["name"] == "Sea crossing")
    assert row["note"] == 'narrower than "Leaving home" — the crossing is one part of leaving'
    assert len(store.hits(conn, mid)) == 2, "its hits are where the reading put them"


def test_a_relation_that_is_not_one_of_the_four_changes_nothing_and_is_reported(conn, two_readings,
                                                                                model):
    pid, mid = two_readings["pid"], two_readings["mid"]
    model.queue({"relations": [{"local": "Sea crossing", "relation": "much like",
                                "project": "Leaving home", "why": ""},
                               {"local": "A code nobody made", "relation": "same",
                                "project": "Leaving home", "why": ""}]})
    out = reconcile.run(conn, mid)
    assert (out["merged"], out["noted"]) == (0, 0) and len(out["dropped"]) == 2
    assert len(store.codebook(conn, pid)) == 2, "both codes stand exactly as they were"


def test_the_chain_runs_the_comparison_and_keeps_what_it_set_aside(conn, two_readings, model):
    """The step as the chain calls it: its own run row, its own line, its own notes."""
    pid, mid = two_readings["pid"], two_readings["mid"]
    model.queue({"relations": [{"local": "Sea crossing", "relation": "wider",
                                "project": "Leaving home", "why": "leaving is one voyage of many"},
                               {"local": "A code nobody made", "relation": "same",
                                "project": "Leaving home", "why": ""}]})
    jobs.run_now(conn, pid, [{"kind": "reconcile", "material_id": mid}])
    row = next(r for r in store.runs(conn, pid) if r["kind"] == "reconcile")
    assert row["error"] is None and row["finished"]
    assert row["line"] == "Comparing DP-40 Grande's codes with the project's"
    assert "A code nobody made" in row["notes"]


def test_a_name_the_project_already_has_is_settled_without_asking_anyone(conn, project, grande,
                                                                        rodwin, model):
    """`save_codes` reuses a code by name, so an exact match is one row already. Nothing is left
    to compare, and the step spends nothing."""
    _coded(conn, project, rodwin, "Leaving home", "Passages about departure.")
    _coded(conn, project, grande, "Leaving home", "Passages about departure.")
    out = reconcile.run(conn, grande)
    assert out == {"considered": 0, "merged": 0, "noted": 0, "dropped": []}
    assert model.calls == [], "no model call at all"
    assert len(store.codebook(conn, project)) == 1


def test_the_first_material_has_nothing_to_be_compared_with(conn, project, grande, model):
    _coded(conn, project, grande, "Sea crossing", "Passages about the voyage itself.")
    assert reconcile.run(conn, grande)["considered"] == 1
    assert model.calls == []


# ---- the chain ----------------------------------------------------------------------------------

def _planned(monkeypatch, pid: str, mids: list[str]) -> list[str]:
    """The kinds `jobs.ingest_chain` would queue, without the job row or the thread."""
    got: list[dict] = []
    monkeypatch.setattr(jobs, "start", lambda factory, project, runs: got.extend(runs))
    jobs.ingest_chain(pid, mids)
    return [r["kind"] for r in got]


def test_only_an_exploratory_project_plans_the_comparison(conn, project, grande, monkeypatch):
    assert _planned(monkeypatch, project, [grande])[:4] == \
        ["frame", "angles", "read", "reconcile"]
    store.set_method(conn, project, "iterative")
    assert "reconcile" not in _planned(monkeypatch, project, [grande]), \
        "an iterative reading was shown the codebook; there is nothing to reconcile afterwards"


def test_the_comparison_takes_the_same_turn_as_the_reading(conn):
    """It writes the shared codebook — it merges rows away — so it may not run beside another
    material's reading of the same codebook."""
    assert "reconcile" in jobs.IN_TURN and "read" in jobs.IN_TURN
    assert {"read", "reconcile"} <= jobs.SIDE_BY_SIDE[0]


def test_the_line_a_researcher_reads_names_the_material(conn, project, grande):
    assert jobs.line(conn, {"kind": "reconcile", "material_id": grande}) == \
        "Comparing DP-40 Grande's codes with the project's"


# ---- the choice, on the page --------------------------------------------------------------------

@pytest.fixture
def client(conn, monkeypatch):
    from fastapi.testclient import TestClient
    from app import main, pages, verbs
    for mod in (pages, verbs, accounts):
        monkeypatch.setattr(mod, "connection", lambda: conn, raising=False)
    return TestClient(main.app, follow_redirects=False)


@pytest.fixture
def people(conn):
    return {"ann": store.create_user(conn, "ann", "battery staple"),
            "bob": store.create_user(conn, "bob", "purple monkey")}


def login(client, name, pw):
    assert client.post("/login", data={"name": name, "password": pw}).status_code == 303


def test_the_new_project_form_carries_the_choice(client, conn, people):
    login(client, "ann", "battery staple")
    assert "Explore the material" in client.get("/").text
    r = client.post("/p/new", data={"name": "Built up", "focus": "", "method": "iterative"})
    assert r.status_code == 303
    pid = r.headers["location"].rsplit("/", 1)[-1]
    assert store.project(conn, pid)["method"] == "iterative"
    assert "Built iteratively" in client.get(f"/p/{pid}").text


def test_the_owner_changes_the_method_and_a_collaborator_cannot(client, conn, people):
    login(client, "ann", "battery staple")
    pid = store.create_project(conn, "Ann's study", "", owner_id=people["ann"])
    assert client.post(f"/p/{pid}/method", data={"method": "iterative"}).status_code == 303
    assert store.project(conn, pid)["method"] == "iterative"
    assert "Built iteratively" in client.get(f"/p/{pid}").text

    assert client.post(f"/p/{pid}/share/link", data={"role": "edit"}).status_code == 303
    token = client.get(f"/p/{pid}/share").text.split("/join/")[-1].split('"')[0]
    from fastapi.testclient import TestClient
    from app import main
    bob = TestClient(main.app, follow_redirects=False)
    login(bob, "bob", "purple monkey")
    assert bob.get(f"/join/{token}").status_code == 303
    assert bob.post(f"/p/{pid}/method", data={"method": "explore"}).status_code == 404
    assert store.project(conn, pid)["method"] == "iterative"
