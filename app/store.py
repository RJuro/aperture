"""Every write to the database goes through here.

Two reasons it is one module. Reruns must *supersede* rather than overwrite, and that rule is easy
to forget at a call site — so callers say `save_moments` and the superseding is not theirs to
remember. And the engine modules are built in parallel; sharing one writer keeps them from
inventing three different ideas of what a thread is.

The reading rule this file exists to enforce: **nothing is copied field by field out of a payload
into a fixed key list.** Three times in the old engine a validated quote was dropped on the way to
the page by exactly that — an insert that listed the columns it knew about and silently lost the
one added last. Here, rows are built from dicts and tests walk real payloads.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

from . import db


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ---- projects and material --------------------------------------------------------------------

def create_project(conn: sqlite3.Connection, name: str, focus: str = "") -> str:
    pid = db.new_id("p")
    conn.execute("INSERT INTO project (id, name, focus, created_at) VALUES (?,?,?,?)",
                 (pid, name, focus, now()))
    conn.commit()
    return pid


def add_material(conn: sqlite3.Connection, pid: str, name: str, text: str) -> str:
    mid = db.new_id("m")
    conn.execute("INSERT INTO material (id, project_id, name, text, state, created_at) "
                 "VALUES (?,?,?,?,'added',?)", (mid, pid, name, text, now()))
    conn.commit()
    return mid


def set_state(conn: sqlite3.Connection, mid: str, state: str) -> None:
    conn.execute("UPDATE material SET state=? WHERE id=?", (state, mid))
    conn.commit()


def material(conn: sqlite3.Connection, mid: str) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM material WHERE id=?", (mid,)).fetchone()


def materials(conn: sqlite3.Connection, pid: str) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM material WHERE project_id=? ORDER BY created_at, id",
                        (pid,)).fetchall()


def project(conn: sqlite3.Connection, pid: str) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM project WHERE id=?", (pid,)).fetchone()


# ---- sentences --------------------------------------------------------------------------------

def save_sentences(conn: sqlite3.Connection, mid: str, rows: list[dict]) -> None:
    """Written once, at ingest, and never again — ids are the spine everything else cites."""
    conn.executemany(
        "INSERT OR REPLACE INTO sentence (material_id, idx, sid, turn_idx, speaker, text) "
        "VALUES (?,?,?,?,?,?)",
        [(mid, r["idx"], r["sid"], r.get("turn_idx"), r.get("speaker", ""), r["text"])
         for r in rows])
    conn.commit()


def sentences(conn: sqlite3.Connection, mid: str) -> list[tuple[str, str]]:
    """[(sid, text)] in order — the shape `anchor.locate` and `anchor.bind` take."""
    return [(r["sid"], r["text"]) for r in conn.execute(
        "SELECT sid, text FROM sentence WHERE material_id=? ORDER BY idx", (mid,))]


def sentence_rows(conn: sqlite3.Connection, mid: str) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM sentence WHERE material_id=? ORDER BY idx", (mid,)).fetchall()


def sid_position(conn: sqlite3.Connection, mid: str) -> dict[str, int]:
    """sid → document position, so moments can be ordered by where they fall in the material."""
    return {r["sid"]: r["idx"] for r in conn.execute(
        "SELECT sid, idx FROM sentence WHERE material_id=?", (mid,))}


# ---- frame ------------------------------------------------------------------------------------

def save_frame(conn: sqlite3.Connection, mid: str, *, kind: str, display: str, title: str,
               speakers: list[dict], segments: list[dict]) -> None:
    """The material's shape. Replaces any earlier frame — a re-frame re-describes, and because it
    never touches `sentence`, every code and moment survives it."""
    conn.execute("UPDATE material SET kind=?, display=?, title=? WHERE id=?",
                 (kind, display, title, mid))
    conn.execute("DELETE FROM speaker WHERE material_id=?", (mid,))
    conn.executemany("INSERT OR REPLACE INTO speaker (material_id, label, name, role) "
                     "VALUES (?,?,?,?)",
                     [(mid, s["label"], s.get("name", ""), s.get("role", "other"))
                      for s in speakers])
    conn.execute("DELETE FROM segment WHERE material_id=?", (mid,))
    conn.executemany("INSERT OR REPLACE INTO segment (material_id, idx, sid, label) "
                     "VALUES (?,?,?,?)",
                     [(mid, i, s["sid"], s["label"]) for i, s in enumerate(segments)])
    conn.commit()


def speakers(conn: sqlite3.Connection, mid: str) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM speaker WHERE material_id=?", (mid,)).fetchall()


def segments(conn: sqlite3.Connection, mid: str) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM segment WHERE material_id=? ORDER BY idx", (mid,)).fetchall()


# ---- codes ------------------------------------------------------------------------------------

def codebook(conn: sqlite3.Connection, pid: str) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM code WHERE project_id=? ORDER BY name", (pid,)).fetchall()


def save_codes(conn: sqlite3.Connection, pid: str, mid: str, codes: list[dict],
               origin: str = "read") -> dict:
    """`codes` is [{name, definition, sids}]. An existing name keeps its id and gains hits; a new
    name gets one. Returns {new, reused, hits} for the run line."""
    known = {r["name"]: r["id"] for r in codebook(conn, pid)}
    new = reused = hits = 0
    for c in codes:
        name = (c.get("name") or "").strip()
        if not name:
            continue
        cid = known.get(name)
        if cid is None:
            cid = db.new_id("c")
            known[name] = cid
            conn.execute("INSERT INTO code (id, project_id, name, definition, origin) "
                         "VALUES (?,?,?,?,?)", (cid, pid, name, c.get("definition", ""), origin))
            new += 1
        else:
            reused += 1
            if c.get("definition"):
                conn.execute("UPDATE code SET definition=? WHERE id=? AND definition=''",
                             (c["definition"], cid))
        for sid in c.get("sids") or []:
            conn.execute("INSERT OR IGNORE INTO code_hit (code_id, material_id, sid) "
                         "VALUES (?,?,?)", (cid, mid, sid))
            hits += 1
    conn.commit()
    return {"new": new, "reused": reused, "hits": hits}


def hits(conn: sqlite3.Connection, mid: str) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT c.id, c.name, c.definition, h.sid FROM code_hit h JOIN code c ON c.id=h.code_id "
        "WHERE h.material_id=? ORDER BY c.name", (mid,)).fetchall()


# ---- themes -----------------------------------------------------------------------------------

def live_themes(conn: sqlite3.Connection, pid: str) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM theme WHERE project_id=? AND status='live' ORDER BY name",
                        (pid,)).fetchall()


def save_theme(conn: sqlite3.Connection, pid: str, *, tid: str | None, name: str, gist: str,
               code_ids: list[str]) -> str:
    tid = tid or db.new_id("t")
    if conn.execute("SELECT 1 FROM theme WHERE id=?", (tid,)).fetchone():
        conn.execute("UPDATE theme SET name=?, gist=? WHERE id=?", (name, gist, tid))
    else:
        conn.execute("INSERT INTO theme (id, project_id, name, gist) VALUES (?,?,?,?)",
                     (tid, pid, name, gist))
    conn.execute("DELETE FROM theme_code WHERE theme_id=?", (tid,))
    conn.executemany("INSERT OR IGNORE INTO theme_code (theme_id, code_id) VALUES (?,?)",
                     [(tid, c) for c in code_ids])
    conn.commit()
    return tid


def merge_theme(conn: sqlite3.Connection, tid: str, into: str) -> None:
    """Merged, never deleted: a moment that cited the old theme still resolves."""
    conn.execute("UPDATE theme SET status='merged', merged_into=? WHERE id=?", (into, tid))
    conn.execute("UPDATE moment SET theme_id=? WHERE theme_id=?", (into, tid))
    conn.commit()


def theme_codes(conn: sqlite3.Connection, tid: str) -> list[sqlite3.Row]:
    return conn.execute("SELECT c.* FROM theme_code tc JOIN code c ON c.id=tc.code_id "
                        "WHERE tc.theme_id=? ORDER BY c.name", (tid,)).fetchall()


# ---- moments and threads ----------------------------------------------------------------------

def save_moments(conn: sqlite3.Connection, mid: str, theme_id: str, moments: list[dict],
                 run_id: str | None = None) -> int:
    """Replace one thread. The old moments become 'superseded' rather than vanishing, so the
    export can show what a piece of feedback changed. `moments` is [{claim, anchor, sid}] and is
    ordered here by position in the material — the reader walks the material, not the model's
    output order."""
    conn.execute("UPDATE moment SET status='superseded' "
                 "WHERE material_id=? AND theme_id=? AND status='live'", (mid, theme_id))
    pos = sid_position(conn, mid)
    ordered = sorted(moments, key=lambda m: pos.get(m["sid"], 10**9))
    for i, m in enumerate(ordered):
        conn.execute("INSERT INTO moment (id, material_id, theme_id, sid, position, claim, "
                     "anchor, run_id, status) VALUES (?,?,?,?,?,?,?,?,'live')",
                     (db.new_id("mo"), mid, theme_id, m["sid"], i, m["claim"], m["anchor"], run_id))
    conn.commit()
    return len(ordered)


def thread(conn: sqlite3.Connection, mid: str, theme_id: str) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM moment WHERE material_id=? AND theme_id=? AND status='live'"
                        " ORDER BY position", (mid, theme_id)).fetchall()


def moments(conn: sqlite3.Connection, mid: str) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM moment WHERE material_id=? AND status='live' "
                        "ORDER BY position", (mid,)).fetchall()


def moment(conn: sqlite3.Connection, moment_id: str) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM moment WHERE id=?", (moment_id,)).fetchone()


def cited_sids(conn: sqlite3.Connection, mid: str) -> set[str]:
    return {r["sid"] for r in conn.execute(
        "SELECT DISTINCT sid FROM moment WHERE material_id=? AND status='live'", (mid,))}


def uncited(conn: sqlite3.Connection, mid: str) -> list[tuple[str, str]]:
    """The passages no live moment rests on — what a check searches, and what the unmarked text on
    the page shows. One derivation, two surfaces, so they cannot disagree."""
    cited = cited_sids(conn, mid)
    return [(sid, text) for sid, text in sentences(conn, mid) if sid not in cited]


# ---- summaries --------------------------------------------------------------------------------

def save_summary(conn: sqlite3.Connection, scope: str, ref_id: str, stage: str, text: str,
                 run_id: str | None = None) -> str:
    """stage is 'orientation' (what this material is, written at framing) or 'reading' (what the
    reading found). Both are kept: the export shows what the analysis added to a description."""
    conn.execute("UPDATE summary SET status='superseded' "
                 "WHERE scope=? AND ref_id=? AND stage=? AND status='live'", (scope, ref_id, stage))
    sid_ = db.new_id("s")
    conn.execute("INSERT INTO summary (id, scope, ref_id, stage, text, run_id, status) "
                 "VALUES (?,?,?,?,?,?,'live')", (sid_, scope, ref_id, stage, text, run_id))
    conn.commit()
    return sid_


def get_summary(conn: sqlite3.Connection, scope: str, ref_id: str,
                stage: str | None = None) -> sqlite3.Row | None:
    """Without `stage`, the reading summary if there is one, else the orientation — which is what
    a page wants: the best account that exists right now."""
    if stage:
        return conn.execute("SELECT * FROM summary WHERE scope=? AND ref_id=? AND stage=? "
                            "AND status='live'", (scope, ref_id, stage)).fetchone()
    return conn.execute(
        "SELECT * FROM summary WHERE scope=? AND ref_id=? AND status='live' "
        "ORDER BY CASE stage WHEN 'reading' THEN 0 ELSE 1 END LIMIT 1", (scope, ref_id)).fetchone()


def save_people(conn: sqlite3.Connection, mid: str, people: list[dict]) -> None:
    conn.execute("DELETE FROM person WHERE material_id=?", (mid,))
    conn.executemany("INSERT OR REPLACE INTO person (material_id, name, aliases, role) "
                     "VALUES (?,?,?,?)",
                     [(mid, p["name"], ", ".join(p.get("aliases") or []), p.get("role", ""))
                      for p in people if p.get("name")])
    conn.commit()


def people(conn: sqlite3.Connection, mid: str) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM person WHERE material_id=? ORDER BY name", (mid,)).fetchall()


# ---- feedback and checks ----------------------------------------------------------------------

def add_feedback(conn: sqlite3.Connection, pid: str, target_kind: str, target_id: str,
                 kind: str, text: str = "") -> str:
    fid = db.new_id("f")
    conn.execute("INSERT INTO feedback (id, project_id, target_kind, target_id, kind, text, "
                 "created_at) VALUES (?,?,?,?,?,?,?)",
                 (fid, pid, target_kind, target_id, kind, text, now()))
    conn.commit()
    return fid


def feedback_for(conn: sqlite3.Connection, target_kind: str, target_id: str) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM feedback WHERE target_kind=? AND target_id=? "
                        "ORDER BY created_at", (target_kind, target_id)).fetchall()


def project_feedback(conn: sqlite3.Connection, pid: str) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM feedback WHERE project_id=? ORDER BY created_at",
                        (pid,)).fetchall()


def save_check(conn: sqlite3.Connection, pid: str, scope: str, ref_id: str, question: str,
               verdict: str, anchors: list[dict], searched_n: int,
               run_id: str | None = None) -> str:
    cid = db.new_id("k")
    conn.execute("INSERT INTO check_ (id, project_id, scope, ref_id, question, verdict, "
                 "anchors_json, searched_n, run_id, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                 (cid, pid, scope, ref_id, question, verdict,
                  json.dumps(anchors, ensure_ascii=False), searched_n, run_id, now()))
    conn.commit()
    return cid


def checks(conn: sqlite3.Connection, pid: str) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM check_ WHERE project_id=? ORDER BY created_at",
                        (pid,)).fetchall()


# ---- runs -------------------------------------------------------------------------------------

def start_run(conn: sqlite3.Connection, pid: str, kind: str, mid: str | None, line: str) -> str:
    from . import llm
    rid = db.new_id("r")
    conn.execute("INSERT INTO run (id, project_id, kind, material_id, provider, model, started, "
                 "line) VALUES (?,?,?,?,?,?,?,?)",
                 (rid, pid, kind, mid, llm.provider(), llm.model(), now(), line))
    conn.commit()
    return rid


def finish_run(conn: sqlite3.Connection, rid: str, *, error: str | None = None,
               tokens_in: int = 0, tokens_out: int = 0) -> None:
    conn.execute("UPDATE run SET finished=?, error=?, tokens_in=?, tokens_out=? WHERE id=?",
                 (now(), error, tokens_in, tokens_out, rid))
    conn.commit()


def active_runs(conn: sqlite3.Connection, pid: str) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM run WHERE project_id=? AND finished IS NULL "
                        "ORDER BY started", (pid,)).fetchall()


def runs(conn: sqlite3.Connection, pid: str) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM run WHERE project_id=? ORDER BY started", (pid,)).fetchall()
