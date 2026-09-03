"""One SQLite database for everything, under $APERTURE_DATA_DIR.

The old engine kept a database per project plus a registry to list them, which bought nothing: a
single-user instrument holds a handful of projects, and the project page wants to join across
materials anyway. One file, WAL, foreign keys on.

Rows are never deleted by the analysis. A rerun *supersedes*: the old row's status becomes
'superseded' and the new one is inserted, so the export can show what a piece of feedback changed.
"""
from __future__ import annotations

import os
import sqlite3
import uuid
from pathlib import Path

SCHEMA_VERSION = 5

SCHEMA = """
CREATE TABLE IF NOT EXISTS user (
    id TEXT PRIMARY KEY, name TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL,
    is_admin INTEGER NOT NULL DEFAULT 0);

CREATE TABLE IF NOT EXISTS session (
    token TEXT PRIMARY KEY, user_id TEXT NOT NULL, created_at TEXT NOT NULL);

CREATE TABLE IF NOT EXISTS project (
    id TEXT PRIMARY KEY, name TEXT NOT NULL, focus TEXT DEFAULT '',
    brief TEXT DEFAULT '', created_at TEXT NOT NULL);

CREATE TABLE IF NOT EXISTS material (
    id TEXT PRIMARY KEY, project_id TEXT NOT NULL, name TEXT NOT NULL, text TEXT NOT NULL,
    kind TEXT DEFAULT '', display TEXT DEFAULT 'plain', title TEXT DEFAULT '',
    state TEXT NOT NULL DEFAULT 'added', created_at TEXT NOT NULL);

CREATE TABLE IF NOT EXISTS sentence (
    material_id TEXT NOT NULL, idx INTEGER NOT NULL, sid TEXT NOT NULL,
    turn_idx INTEGER, speaker TEXT DEFAULT '', text TEXT NOT NULL,
    PRIMARY KEY (material_id, sid));

CREATE TABLE IF NOT EXISTS speaker (
    material_id TEXT NOT NULL, label TEXT NOT NULL, name TEXT DEFAULT '',
    role TEXT DEFAULT 'other', PRIMARY KEY (material_id, label));

CREATE TABLE IF NOT EXISTS segment (
    material_id TEXT NOT NULL, idx INTEGER NOT NULL, sid TEXT NOT NULL, label TEXT NOT NULL,
    PRIMARY KEY (material_id, idx));

CREATE TABLE IF NOT EXISTS code (
    id TEXT PRIMARY KEY, project_id TEXT NOT NULL, name TEXT NOT NULL,
    definition TEXT DEFAULT '', origin TEXT DEFAULT 'read');

CREATE TABLE IF NOT EXISTS code_hit (
    code_id TEXT NOT NULL, material_id TEXT NOT NULL, sid TEXT NOT NULL,
    PRIMARY KEY (code_id, material_id, sid));

CREATE TABLE IF NOT EXISTS theme (
    id TEXT PRIMARY KEY, project_id TEXT NOT NULL, name TEXT NOT NULL, gist TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'live', merged_into TEXT);

CREATE TABLE IF NOT EXISTS theme_history (
    theme_id TEXT NOT NULL, name TEXT NOT NULL, gist TEXT DEFAULT '', codes TEXT DEFAULT '',
    run_id TEXT, at TEXT NOT NULL);

CREATE TABLE IF NOT EXISTS theme_code (
    theme_id TEXT NOT NULL, code_id TEXT NOT NULL, PRIMARY KEY (theme_id, code_id));

CREATE TABLE IF NOT EXISTS moment (
    id TEXT PRIMARY KEY, material_id TEXT NOT NULL, theme_id TEXT NOT NULL, sid TEXT NOT NULL,
    position INTEGER NOT NULL, claim TEXT NOT NULL, anchor TEXT NOT NULL,
    run_id TEXT, status TEXT NOT NULL DEFAULT 'live');

CREATE TABLE IF NOT EXISTS summary (
    id TEXT PRIMARY KEY, scope TEXT NOT NULL, ref_id TEXT NOT NULL, stage TEXT NOT NULL,
    text TEXT NOT NULL, run_id TEXT, status TEXT NOT NULL DEFAULT 'live');

CREATE TABLE IF NOT EXISTS person (
    material_id TEXT NOT NULL, name TEXT NOT NULL, aliases TEXT DEFAULT '',
    role TEXT DEFAULT '', PRIMARY KEY (material_id, name));

CREATE TABLE IF NOT EXISTS feedback (
    id TEXT PRIMARY KEY, project_id TEXT NOT NULL, target_kind TEXT NOT NULL,
    target_id TEXT NOT NULL, kind TEXT NOT NULL, text TEXT DEFAULT '',
    created_at TEXT NOT NULL, consumed_by_run TEXT);

CREATE TABLE IF NOT EXISTS check_ (
    id TEXT PRIMARY KEY, project_id TEXT NOT NULL, scope TEXT NOT NULL, ref_id TEXT NOT NULL,
    question TEXT NOT NULL, verdict TEXT NOT NULL, anchors_json TEXT DEFAULT '[]',
    searched_n INTEGER DEFAULT 0, run_id TEXT, created_at TEXT NOT NULL);

CREATE TABLE IF NOT EXISTS run (
    id TEXT PRIMARY KEY, project_id TEXT NOT NULL, kind TEXT NOT NULL, material_id TEXT,
    provider TEXT DEFAULT '', model TEXT DEFAULT '', tokens_in INTEGER DEFAULT 0,
    tokens_out INTEGER DEFAULT 0, started TEXT, finished TEXT, error TEXT, line TEXT DEFAULT '');

CREATE TABLE IF NOT EXISTS job (
    id TEXT PRIMARY KEY, project_id TEXT NOT NULL, runs_json TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'queued', created_at TEXT NOT NULL,
    started_at TEXT, finished_at TEXT, error TEXT DEFAULT '');

CREATE INDEX IF NOT EXISTS ix_material_project ON material(project_id);
CREATE INDEX IF NOT EXISTS ix_sentence_material ON sentence(material_id, idx);
CREATE INDEX IF NOT EXISTS ix_hit_material ON code_hit(material_id);
CREATE INDEX IF NOT EXISTS ix_moment_thread ON moment(material_id, theme_id, status);
CREATE INDEX IF NOT EXISTS ix_summary_ref ON summary(scope, ref_id, status);
CREATE INDEX IF NOT EXISTS ix_feedback_target ON feedback(target_kind, target_id);
CREATE INDEX IF NOT EXISTS ix_run_project ON run(project_id, started);
CREATE INDEX IF NOT EXISTS ix_job_status ON job(status, created_at);
"""


def data_dir() -> Path:
    d = Path(os.environ.get("APERTURE_DATA_DIR") or Path(__file__).resolve().parent.parent / "data")
    d.mkdir(parents=True, exist_ok=True)
    return d


def connect(path: str | Path | None = None) -> sqlite3.Connection:
    """Open (creating and migrating as needed) the database. Rows come back as `sqlite3.Row`, so
    every caller reads columns by name — a positional read is how a field gets silently dropped."""
    conn = sqlite3.connect(path or data_dir() / "aperture.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    migrate(conn)
    return conn


def migrate(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    # Columns added after v1. CREATE TABLE IF NOT EXISTS leaves an existing table alone, so a
    # database made before a column existed needs it added explicitly.
    have = {r[1] for r in conn.execute("PRAGMA table_info(run)")}
    if "notes" not in have:
        conn.execute("ALTER TABLE run ADD COLUMN notes TEXT DEFAULT ''")
    have = {r[1] for r in conn.execute("PRAGMA table_info(project)")}
    if "owner_id" not in have:
        conn.execute("ALTER TABLE project ADD COLUMN owner_id TEXT")
    have = {r[1] for r in conn.execute("PRAGMA table_info(material)")}
    if "removed_at" not in have:
        conn.execute("ALTER TABLE material ADD COLUMN removed_at TEXT")
    conn.execute(f"PRAGMA user_version={SCHEMA_VERSION}")
    conn.commit()


def new_id(prefix: str) -> str:
    """Short, readable, sortable-enough ids. Prefixed so a stray id in a log says what it is."""
    return f"{prefix}{uuid.uuid4().hex[:10]}"
