"""Regression coverage for the background, removal, title and synthesis improvements."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from app import context, db, ingest, jobs, store, titles


def test_archive_titles_share_one_calm_display_standard():
    assert titles.standardize("**JOHANNES VON TRAPP INTERVIEW, 1995") == \
        "Johannes von Trapp interview, 1995"
    assert titles.standardize("CAROLE MICHAEL, ELLIS ISLAND ORAL HISTORY") == \
        "Carole Michael, Ellis Island oral history"
    assert titles.standardize("Mary Grande — interview, 1989") == \
        "Mary Grande — interview, 1989"


def test_the_title_is_composed_from_the_participants_the_kind_and_the_year():
    who = [{"label": "PHILLIPS", "name": "Phillips", "role": "interviewer"},
           {"label": "GRANDE", "name": "Mary Grande", "role": "participant"}]
    assert titles.compose("interview", who, "GRANDE, M. ORAL HISTORY", "1989") == \
        "Mary Grande — interview, 1989"
    assert titles.compose("interview", who, "GRANDE, M. ORAL HISTORY", "") == \
        "Mary Grande — interview"


def test_with_nobody_named_the_models_title_is_what_the_standard_is_built_on():
    assert titles.compose("interview", [{"label": "P1", "name": "", "role": "participant"}],
                          "CAROLE MICHAEL, ELLIS ISLAND ORAL HISTORY", "1995") == \
        "Carole Michael, Ellis Island oral history — interview, 1995"
    assert titles.compose("document", [], "**Ships' manifests", "1907") == \
        "Ships' manifests — document, 1907"


def test_two_participants_are_named_a_third_is_not_and_an_empty_frame_names_nothing(conn, project):
    three = [{"label": f"P{i}", "name": n, "role": "participant"}
             for i, n in enumerate(("Ana", "Bo", "Cai"))]
    assert titles.compose("focus_group", three[:2], "", "2019") == "Ana and Bo — focus group, 2019"
    assert titles.compose("focus_group", three, "", "2019") == "Ana and Bo — focus group, 2019"

    assert titles.compose("other", [], "", "") == ""
    mid = store.add_material(conn, project, "market-notes.txt", "Arrived before six.")
    store.save_frame(conn, mid, kind="other", display="plain", title="", speakers=[], segments=[])
    assert context._material_title(store.material(conn, mid)) == "market-notes.txt"


def test_a_database_from_before_the_standard_has_its_titles_composed_on_migration(tmp_path):
    """The participants are already in the database, so old material comes under the same
    standard without a model call."""
    conn = sqlite3.connect(tmp_path / "v5.db")
    conn.execute("CREATE TABLE material (id TEXT PRIMARY KEY, project_id TEXT NOT NULL, "
                 "name TEXT NOT NULL, text TEXT NOT NULL, kind TEXT DEFAULT '', "
                 "display TEXT DEFAULT 'plain', title TEXT DEFAULT '', "
                 "state TEXT NOT NULL DEFAULT 'added', created_at TEXT NOT NULL)")
    conn.execute("CREATE TABLE speaker (material_id TEXT NOT NULL, label TEXT NOT NULL, "
                 "name TEXT DEFAULT '', role TEXT DEFAULT 'other', "
                 "PRIMARY KEY (material_id, label))")
    conn.execute("INSERT INTO material VALUES ('m1', 'p1', 'grande.txt', 'Some text.', "
                 "'interview', 'turns', 'Ellis Island Oral History: Mary Grande', 'read', 'now')")
    conn.execute("INSERT INTO speaker VALUES ('m1', 'GRANDE', 'Mary Grande', 'participant')")

    db.migrate(conn)

    assert conn.execute("SELECT title, year FROM material").fetchone() == \
        ("Mary Grande — interview", "")


def test_a_job_is_committed_before_background_execution_begins(conn, project, grande, monkeypatch):
    launched = []
    monkeypatch.setattr(jobs, "_launch", lambda jid, pid, factory: launched.append((jid, pid)))

    jid = jobs.start(db.connect, project, [{"kind": "frame", "material_id": grande}])

    row = store.job(conn, jid)
    assert row["status"] == "queued"
    assert json.loads(row["runs_json"]) == [{"kind": "frame", "material_id": grande}]
    assert store.material(conn, grande)["state"] == "queued"
    assert launched == [(jid, project)]


def test_removing_material_excludes_its_evidence_and_invalidates_the_project_summary(
        conn, analysed):
    pid, gone, kept = analysed["pid"], analysed["grande"], analysed["rodwin"]
    before = len(store.moments(conn, gone))
    assert before and store.get_summary(conn, "project", pid)

    assert store.remove_material(conn, pid, gone)

    assert [m["id"] for m in store.materials(conn, pid)] == [kept]
    assert store.material(conn, gone) is None
    assert conn.execute("SELECT COUNT(*) FROM moment WHERE material_id=? AND status='live'",
                        (gone,)).fetchone()[0] == 0
    assert store.get_summary(conn, "project", pid) is None


def test_removal_rebuilds_every_remaining_material_then_the_corpus(monkeypatch):
    planned = []
    monkeypatch.setattr(jobs, "start", lambda factory, pid, runs: planned.extend(runs) or "j")
    jobs.removal_chain("p1", ["m1", "m2"])
    assert [r["kind"] for r in planned] == ["themes", "doc", "doc", "accounts", "project"]
    assert [r["material_id"] for r in planned if r["kind"] == "doc"] == ["m1", "m2"]


def test_project_prompt_requires_grounded_and_interpretive_synthesis():
    prompt = (Path(__file__).parent.parent / "app" / "prompts" / "project.md").read_text()
    assert "grounded synthesis" in prompt
    assert "interpretive synthesis" in prompt
    assert "visibly provisional" in prompt
