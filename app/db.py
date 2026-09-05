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

from . import titles

SCHEMA_VERSION = 15

SCHEMA = """
CREATE TABLE IF NOT EXISTS user (
    id TEXT PRIMARY KEY, name TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL,
    is_admin INTEGER NOT NULL DEFAULT 0);

CREATE TABLE IF NOT EXISTS session (
    token TEXT PRIMARY KEY, user_id TEXT NOT NULL, created_at TEXT NOT NULL);

-- A standing invitation to one project, until it is revoked. The token is the whole secret,
-- so it is long and random; the row exists so that revoking one link does not disturb the other.
CREATE TABLE IF NOT EXISTS invite (
    token TEXT PRIMARY KEY, project_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('edit','read')),
    created_by TEXT, created_at TEXT NOT NULL, revoked_at TEXT);

-- Who, other than the owner, may open a project. Membership outlives the link that made it:
-- revoking a link closes the door, it does not put anyone already through it back outside.
CREATE TABLE IF NOT EXISTS member (
    project_id TEXT NOT NULL, user_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('edit','read')),
    joined_at TEXT NOT NULL, PRIMARY KEY (project_id, user_id));

CREATE TABLE IF NOT EXISTS project (
    id TEXT PRIMARY KEY, name TEXT NOT NULL, focus TEXT DEFAULT '',
    brief TEXT DEFAULT '', created_at TEXT NOT NULL, removed_at TEXT);

CREATE TABLE IF NOT EXISTS material (
    id TEXT PRIMARY KEY, project_id TEXT NOT NULL, name TEXT NOT NULL, text TEXT NOT NULL,
    kind TEXT DEFAULT '', display TEXT DEFAULT 'plain', title TEXT DEFAULT '',
    year TEXT DEFAULT '', state TEXT NOT NULL DEFAULT 'added', created_at TEXT NOT NULL,
    speakers_estimated INTEGER DEFAULT 0, case_id TEXT);

-- What the researcher says is one unit of analysis: a participant, an interview, a time point.
-- A file is not a case — two files from one participant are two materials and one case, and a
-- spreadsheet of forty respondents is one material — so recurrence, which is a claim about
-- independent cases, cannot be counted over files. A material in no case counts as its own.
-- Trailing underscore because CASE is reserved in SQL, as with `check_`.
CREATE TABLE IF NOT EXISTS case_ (
    id TEXT PRIMARY KEY, project_id TEXT NOT NULL, name TEXT NOT NULL,
    note TEXT DEFAULT '', created_at TEXT NOT NULL);

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

-- `hold` is who the theme belongs to now: a 'candidate' is a pattern seen in one material and
-- is the analyst's to promote (or Python's, by recurrence); an 'open' theme is the project's and
-- THEMES may still reword it; a 'frozen' one the researcher has declared final, and its words are
-- fixed here rather than by asking the model nicely. `status` stays live | merged.
-- `proposed_at` is when the corpus reached two cases under a candidate. It is a count, not a
-- confirmation, so it only puts the question to the researcher; the hold still changes by hand.
CREATE TABLE IF NOT EXISTS theme (
    id TEXT PRIMARY KEY, project_id TEXT NOT NULL, name TEXT NOT NULL, gist TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'live', merged_into TEXT,
    hold TEXT NOT NULL DEFAULT 'open',
    stable_passes INTEGER NOT NULL DEFAULT 0, pass_fingerprint TEXT NOT NULL DEFAULT '',
    proposed_at TEXT);

-- What pulled against a frozen theme's definition in one material, in at most 25 words. It is
-- shown to the researcher beside the theme and never written into the gist: new material is
-- applied to a frozen theme, and what does not fit is the case for unfreezing it, not a rewrite.
CREATE TABLE IF NOT EXISTS theme_note (
    id TEXT PRIMARY KEY, theme_id TEXT NOT NULL, material_id TEXT, run_id TEXT,
    text TEXT NOT NULL, created_at TEXT NOT NULL);

CREATE TABLE IF NOT EXISTS theme_history (
    theme_id TEXT NOT NULL, name TEXT NOT NULL, gist TEXT DEFAULT '', codes TEXT DEFAULT '',
    run_id TEXT, at TEXT NOT NULL);

CREATE TABLE IF NOT EXISTS theme_code (
    theme_id TEXT NOT NULL, code_id TEXT NOT NULL, PRIMARY KEY (theme_id, code_id));

CREATE TABLE IF NOT EXISTS moment (
    id TEXT PRIMARY KEY, material_id TEXT NOT NULL, theme_id TEXT NOT NULL, sid TEXT NOT NULL,
    position INTEGER NOT NULL, claim TEXT NOT NULL, anchor TEXT NOT NULL,
    run_id TEXT, status TEXT NOT NULL DEFAULT 'live',
    support TEXT DEFAULT '', support_note TEXT DEFAULT '');

-- What became of one theme in one material: 'line' where a line holds, 'thin' where it was
-- looked for and what came back was set aside, 'skipped' where none of the codes the theme
-- gathers marked this material and it was therefore never looked for. Written by DOC and
-- superseded per run the way a moment is. It exists because the three cannot be told apart from
-- anything else in the database — a line set aside and a line never written both leave no live
-- moment — and because a note in the run's own words would say the wrong thing the moment a
-- researcher renamed the theme.
CREATE TABLE IF NOT EXISTS follow (
    id TEXT PRIMARY KEY, material_id TEXT NOT NULL, theme_id TEXT NOT NULL,
    outcome TEXT NOT NULL CHECK (outcome IN ('line','thin','skipped')),
    run_id TEXT, status TEXT NOT NULL DEFAULT 'live');

CREATE TABLE IF NOT EXISTS summary (
    id TEXT PRIMARY KEY, scope TEXT NOT NULL, ref_id TEXT NOT NULL, stage TEXT NOT NULL,
    text TEXT NOT NULL, run_id TEXT, status TEXT NOT NULL DEFAULT 'live',
    fingerprint TEXT DEFAULT '');

CREATE TABLE IF NOT EXISTS person (
    material_id TEXT NOT NULL, name TEXT NOT NULL, aliases TEXT DEFAULT '',
    role TEXT DEFAULT '', PRIMARY KEY (material_id, name));

CREATE TABLE IF NOT EXISTS feedback (
    id TEXT PRIMARY KEY, project_id TEXT NOT NULL, target_kind TEXT NOT NULL,
    target_id TEXT NOT NULL, kind TEXT NOT NULL, text TEXT DEFAULT '',
    created_at TEXT NOT NULL, consumed_by_run TEXT);

-- `scope` is WHAT was searched (a material, the project); `searched_scope` is WHICH of its
-- passages — 'all' of them, or only the 'unused' ones no claim rests on yet. The two are stored
-- apart because a result that does not say which set it looked at cannot be read honestly a
-- month later: "not found" over the uncited remainder is not "not found in the material".
CREATE TABLE IF NOT EXISTS check_ (
    id TEXT PRIMARY KEY, project_id TEXT NOT NULL, scope TEXT NOT NULL, ref_id TEXT NOT NULL,
    question TEXT NOT NULL, verdict TEXT NOT NULL, anchors_json TEXT DEFAULT '[]',
    searched_n INTEGER DEFAULT 0, searched_scope TEXT DEFAULT 'unused', run_id TEXT,
    created_at TEXT NOT NULL);

CREATE TABLE IF NOT EXISTS run (
    id TEXT PRIMARY KEY, project_id TEXT NOT NULL, kind TEXT NOT NULL, material_id TEXT,
    provider TEXT DEFAULT '', model TEXT DEFAULT '', tokens_in INTEGER DEFAULT 0,
    tokens_out INTEGER DEFAULT 0, started TEXT, finished TEXT, error TEXT, line TEXT DEFAULT '',
    job_id TEXT, changed INTEGER DEFAULT 1);

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
    # A chain reads several materials at once, each on its own connection, so two writers meet.
    # WAL lets them read through each other and this makes the second one WAIT for the write lock
    # rather than raise "database is locked". Five seconds is also Python's own default; it is
    # said out loud because the parallel stages depend on it.
    conn.execute("PRAGMA busy_timeout=5000")
    migrate(conn)
    return conn


def migrate(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    # Columns added after v1. CREATE TABLE IF NOT EXISTS leaves an existing table alone, so a
    # database made before a column existed needs it added explicitly.
    have = {r[1] for r in conn.execute("PRAGMA table_info(run)")}
    if "notes" not in have:
        conn.execute("ALTER TABLE run ADD COLUMN notes TEXT DEFAULT ''")
    if "job_id" not in have:
        conn.execute("ALTER TABLE run ADD COLUMN job_id TEXT")
    if "changed" not in have:
        # Whether this run moved what it was written to move. Only THEMES clears it and only
        # `out_of_date` reads it: a pass that grouped nothing new staled nothing. It defaults to
        # 1 so a run nobody said anything about — every row written before this column — keeps
        # counting as it always did.
        conn.execute("ALTER TABLE run ADD COLUMN changed INTEGER DEFAULT 1")
    have = {r[1] for r in conn.execute("PRAGMA table_info(project)")}
    if "owner_id" not in have:
        conn.execute("ALTER TABLE project ADD COLUMN owner_id TEXT")
    if "removed_at" not in have:
        conn.execute("ALTER TABLE project ADD COLUMN removed_at TEXT")
    have = {r[1] for r in conn.execute("PRAGMA table_info(material)")}
    if "removed_at" not in have:
        conn.execute("ALTER TABLE material ADD COLUMN removed_at TEXT")
    if "year" not in have:
        conn.execute("ALTER TABLE material ADD COLUMN year TEXT DEFAULT ''")
        _recompose_titles(conn)
    if "speakers_estimated" not in have:
        conn.execute("ALTER TABLE material ADD COLUMN speakers_estimated INTEGER DEFAULT 0")
    if "case_id" not in have:
        # Null on every material read before cases existed, which is the honest reading of them:
        # nobody had said which files were one participant, so each one still counts as its own.
        conn.execute("ALTER TABLE material ADD COLUMN case_id TEXT")
    have = {r[1] for r in conn.execute("PRAGMA table_info(moment)")}
    if "support" not in have:
        # What checking the claim against its own passage found: '' where it was not checked or
        # the passage carries it, 'partly' where the claim adds something the passage does not
        # say, 'not' where the claim is set aside. Blank on every row written before the check
        # existed, which is exactly right — those claims were never checked.
        conn.execute("ALTER TABLE moment ADD COLUMN support TEXT DEFAULT ''")
        conn.execute("ALTER TABLE moment ADD COLUMN support_note TEXT DEFAULT ''")
    have = {r[1] for r in conn.execute("PRAGMA table_info(theme)")}
    if "hold" not in have:
        conn.execute("ALTER TABLE theme ADD COLUMN hold TEXT NOT NULL DEFAULT 'open'")
        conn.execute("ALTER TABLE theme ADD COLUMN stable_passes INTEGER NOT NULL DEFAULT 0")
        conn.execute("ALTER TABLE theme ADD COLUMN pass_fingerprint TEXT NOT NULL DEFAULT ''")
        # Every theme in an older database was a project theme, because that was the only kind.
        # The ones that would not be one under the new rule — a pattern carried by fewer than two
        # materials — go back to being candidates, which is where the four-interview record with
        # eleven themes "in 4 of 4" would have put half of its set.
        conn.execute(
            "UPDATE theme SET hold='candidate' WHERE status='live' AND id IN ("
            "  SELECT t.id FROM theme t"
            "  LEFT JOIN moment mo ON mo.theme_id = t.id AND mo.status='live'"
            "  LEFT JOIN material m ON m.id = mo.material_id AND m.removed_at IS NULL"
            "  GROUP BY t.id HAVING COUNT(DISTINCT m.id) < 2)")
    if "proposed_at" not in have:
        # Null everywhere, including on candidates a second material already carries: the next
        # DOC over the project puts the question again, and a proposal nobody was shown is not
        # one that was declined.
        conn.execute("ALTER TABLE theme ADD COLUMN proposed_at TEXT")
    have = {r[1] for r in conn.execute("PRAGMA table_info(check_)")}
    if "searched_scope" not in have:
        # Every check written before this column searched only the passages no claim rested on,
        # which is what the default says. A row that cannot say which set it read is a row whose
        # "not found" a reader has to guess at.
        conn.execute("ALTER TABLE check_ ADD COLUMN searched_scope TEXT DEFAULT 'unused'")
    have = {r[1] for r in conn.execute("PRAGMA table_info(summary)")}
    if "fingerprint" not in have:
        # What a theme's account was written from, so the step that writes every account can tell
        # which ones would come back word for word. Empty on every row written before this
        # column, which no fingerprint can equal, so each of those is written once more.
        conn.execute("ALTER TABLE summary ADD COLUMN fingerprint TEXT DEFAULT ''")
    conn.execute(f"PRAGMA user_version={SCHEMA_VERSION}")
    conn.commit()


def _recompose_titles(conn: sqlite3.Connection) -> None:
    """Material framed before Python composed titles, brought under the same standard once.

    The participants are already in the database, so this costs no model call. A material with
    none keeps the title it has, cleaned: a kind appended to a title that may already name its
    kind reads worse than the mixture this is fixing. No year, because none was ever stored.
    """
    for mid, kind, title in conn.execute("SELECT id, kind, title FROM material").fetchall():
        who = [{"name": n, "role": r} for n, r in
               conn.execute("SELECT name, role FROM speaker WHERE material_id=?", (mid,))]
        new = (titles.compose(kind or "", who, title or "", "")
               if any(s["role"] == "participant" and s["name"] for s in who)
               else titles.standardize(title or ""))
        if new != (title or ""):
            conn.execute("UPDATE material SET title=? WHERE id=?", (new, mid))


def new_id(prefix: str) -> str:
    """Short, readable, sortable-enough ids. Prefixed so a stray id in a log says what it is."""
    return f"{prefix}{uuid.uuid4().hex[:10]}"
