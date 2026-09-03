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

import hashlib
import json
import secrets
import sqlite3
from collections import Counter
from datetime import datetime, timezone

from . import db


def now() -> str:
    """Milliseconds, not seconds. Two runs of a chain can finish inside the same second, and
    `out_of_date` compares their times to decide whether a material was read before the themes
    changed — at second precision that comparison silently answers "no" every time."""
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


# ---- projects and material --------------------------------------------------------------------

def create_project(conn: sqlite3.Connection, name: str, focus: str = "",
                   owner_id: str | None = None) -> str:
    pid = db.new_id("p")
    conn.execute("INSERT INTO project (id, name, focus, created_at, owner_id) VALUES (?,?,?,?,?)",
                 (pid, name, focus, now(), owner_id))
    conn.commit()
    return pid


def add_material(conn: sqlite3.Connection, pid: str, name: str, text: str) -> str:
    mid = db.new_id("m")
    conn.execute("INSERT INTO material (id, project_id, name, text, state, created_at) "
                 "VALUES (?,?,?,?,'added',?)", (mid, pid, name, text, now()))
    conn.commit()
    return mid


def set_state(conn: sqlite3.Connection, mid: str, state: str) -> None:
    conn.execute("UPDATE material SET state=? WHERE id=? AND removed_at IS NULL", (state, mid))
    conn.commit()


def material(conn: sqlite3.Connection, mid: str) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM material WHERE id=? AND removed_at IS NULL", (mid,)).fetchone()


def materials(conn: sqlite3.Connection, pid: str) -> list[sqlite3.Row]:
    # rowid, not id, breaks the tie: ids are random, and several files uploaded together land in
    # the same millisecond, so ordering by id shuffles one submission's materials on the page.
    return conn.execute("SELECT * FROM material WHERE project_id=? AND removed_at IS NULL "
                        "ORDER BY created_at, rowid",
                        (pid,)).fetchall()


def remove_material(conn: sqlite3.Connection, pid: str, mid: str) -> bool:
    """Remove one material from the live corpus while keeping its source row recoverable.

    Evidence derived from it is taken out of every live calculation immediately. Orphaned codes
    are removed from the live codebook; old run rows remain as the audit record of what happened.
    """
    row = conn.execute("SELECT id FROM material WHERE id=? AND project_id=? AND removed_at IS NULL",
                       (mid, pid)).fetchone()
    if row is None:
        return False
    at = now()
    conn.execute("UPDATE material SET removed_at=?, state='removed' WHERE id=?", (at, mid))
    conn.execute("UPDATE moment SET status='superseded' WHERE material_id=? AND status='live'", (mid,))
    conn.execute("UPDATE summary SET status='superseded' WHERE scope='material' AND ref_id=? "
                 "AND status='live'", (mid,))
    conn.execute("DELETE FROM code_hit WHERE material_id=?", (mid,))
    conn.execute("DELETE FROM theme_code WHERE code_id IN ("
                 "SELECT c.id FROM code c LEFT JOIN code_hit h ON h.code_id=c.id "
                 "WHERE c.project_id=? GROUP BY c.id HAVING COUNT(h.sid)=0)", (pid,))
    conn.execute("DELETE FROM code WHERE project_id=? AND id NOT IN "
                 "(SELECT DISTINCT code_id FROM code_hit)", (pid,))
    # Until the queued rebuild lands, never present the old corpus account as current.
    conn.execute("UPDATE summary SET status='superseded' WHERE scope='project' AND ref_id=? "
                 "AND status='live'", (pid,))
    conn.execute("UPDATE summary SET status='superseded' WHERE scope='theme' AND ref_id IN "
                 "(SELECT id FROM theme WHERE project_id=?) AND status='live'", (pid,))
    conn.execute("UPDATE theme SET status='retired' WHERE project_id=? AND status='live' "
                 "AND id NOT IN (SELECT theme_id FROM theme_code) "
                 "AND id NOT IN (SELECT DISTINCT theme_id FROM moment WHERE status='live')", (pid,))
    conn.commit()
    return True


def clear_empty_project_analysis(conn: sqlite3.Connection, pid: str) -> None:
    """Leave an empty project genuinely empty while retaining its historical rows."""
    conn.execute("UPDATE theme SET status='retired' WHERE project_id=? AND status='live'", (pid,))
    conn.execute("UPDATE summary SET status='superseded' WHERE scope='theme' AND ref_id IN "
                 "(SELECT id FROM theme WHERE project_id=?) AND status='live'", (pid,))
    conn.execute("UPDATE project SET brief='' WHERE id=?", (pid,))
    conn.commit()


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
               speakers: list[dict], segments: list[dict], year: str = "",
               estimated: bool = False) -> None:
    """The material's shape. Replaces any earlier frame — a re-frame re-describes, and because it
    never touches `sentence`, every code and moment survives it.

    `estimated` says the sections are a guess at who is speaking rather than something the material
    states. It defaults to false, so describing the material afresh clears the mark and whatever
    runs after has to earn it again."""
    conn.execute("UPDATE material SET kind=?, display=?, title=?, year=?, speakers_estimated=? "
                 "WHERE id=?", (kind, display, title, year, int(estimated), mid))
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
    # Ordered so a compiled prompt is byte-reproducible: interviewer first, then by label.
    return conn.execute(
        "SELECT * FROM speaker WHERE material_id=? "
        "ORDER BY CASE role WHEN 'interviewer' THEN 0 WHEN 'participant' THEN 1 ELSE 2 END, label",
        (mid,)).fetchall()


def segments(conn: sqlite3.Connection, mid: str) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM segment WHERE material_id=? ORDER BY idx", (mid,)).fetchall()


# ---- codes ------------------------------------------------------------------------------------

def codebook(conn: sqlite3.Connection, pid: str) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM code WHERE project_id=? ORDER BY name", (pid,)).fetchall()


def save_codes(conn: sqlite3.Connection, pid: str, mid: str, codes: list[dict],
               origin: str = "read") -> dict:
    """`codes` is [{name, definition, sids}]. An existing name keeps its id and gains hits; a new
    name gets one. Returns {new, reused, hits} for the run line."""
    if material(conn, mid) is None:
        return {"new": 0, "reused": 0, "hits": 0}
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
            cur = conn.execute("INSERT OR IGNORE INTO code_hit (code_id, material_id, sid) "
                               "VALUES (?,?,?)", (cid, mid, sid))
            hits += cur.rowcount        # rows written, not sids offered — a repeat is not a hit
    conn.commit()
    return {"new": new, "reused": reused, "hits": hits}


def clear_hits(conn: sqlite3.Connection, pid: str, mid: str) -> int:
    """Take one material's coding out, the way removing the material does, so a second reading
    replaces the first instead of being counted beside it. The code rows stay — the next reading
    is shown them and reuses the names — but a code left with nothing loses its place in every
    theme, exactly as it does when the material it came from goes."""
    n = conn.execute("DELETE FROM code_hit WHERE material_id=?", (mid,)).rowcount
    conn.execute("DELETE FROM theme_code WHERE code_id IN ("
                 "SELECT c.id FROM code c LEFT JOIN code_hit h ON h.code_id=c.id "
                 "WHERE c.project_id=? GROUP BY c.id HAVING COUNT(h.sid)=0)", (pid,))
    conn.commit()
    return n


def hits(conn: sqlite3.Connection, mid: str) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT c.id, c.name, c.definition, h.sid FROM code_hit h JOIN code c ON c.id=h.code_id "
        "WHERE h.material_id=? ORDER BY c.name", (mid,)).fetchall()


# ---- themes -----------------------------------------------------------------------------------

def live_themes(conn: sqlite3.Connection, pid: str) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM theme WHERE project_id=? AND status='live' ORDER BY name",
                        (pid,)).fetchall()


def save_theme(conn: sqlite3.Connection, pid: str, *, tid: str | None, name: str, gist: str,
               code_ids: list[str], run_id: str | None = None) -> str:
    tid = tid or db.new_id("t")
    prior = conn.execute("SELECT * FROM theme WHERE id=?", (tid,)).fetchone()
    if prior:
        # Themes are rewritten in place — the id must stay stable because every claim cites it —
        # so the past is kept beside it. In reflexive analysis the evolution of a theme IS the
        # analysis; a researcher who cannot show what a theme used to be called cannot cite it.
        if (prior["name"], prior["gist"]) != (name, gist):
            old_codes = ",".join(sorted(r["code_id"] for r in conn.execute(
                "SELECT code_id FROM theme_code WHERE theme_id=?", (tid,))))
            conn.execute("INSERT INTO theme_history (theme_id, name, gist, codes, run_id, at) "
                         "VALUES (?,?,?,?,?,?)", (tid, prior["name"], prior["gist"], old_codes,
                                                  run_id, now()))
        conn.execute("UPDATE theme SET name=?, gist=? WHERE id=?", (name, gist, tid))
    else:
        conn.execute("INSERT INTO theme (id, project_id, name, gist) VALUES (?,?,?,?)",
                     (tid, pid, name, gist))
    conn.execute("DELETE FROM theme_code WHERE theme_id=?", (tid,))
    conn.executemany("INSERT OR IGNORE INTO theme_code (theme_id, code_id) VALUES (?,?)",
                     [(tid, c) for c in code_ids])
    conn.commit()
    return tid


def set_theme_gist(conn: sqlite3.Connection, tid: str, gist: str) -> None:
    """A theme's gist, alone. `save_theme` rewrites a theme's codes as well, so the project
    synthesis — which sharpens gists but knows nothing about which codes belong where — must not
    use it. Writing a gist through `save_theme` would silently empty the theme."""
    conn.execute("UPDATE theme SET gist=? WHERE id=?", (gist, tid))
    conn.commit()


def set_brief(conn: sqlite3.Connection, pid: str, brief: str) -> None:
    """The one slot the model writes for itself: what this corpus is like and what to look for
    next. Read back by the next reading and the next synthesis, and by nothing else."""
    conn.execute("UPDATE project SET brief=? WHERE id=?", (brief, pid))
    conn.commit()


def set_focus(conn: sqlite3.Connection, pid: str, focus: str) -> None:
    conn.execute("UPDATE project SET focus=? WHERE id=?", (focus, pid))
    conn.commit()


def theme_history(conn: sqlite3.Connection, tid: str) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM theme_history WHERE theme_id=? ORDER BY rowid",
                        (tid,)).fetchall()


def merge_theme(conn: sqlite3.Connection, tid: str, into: str) -> None:
    """Merged, never deleted: a moment that cited the old theme still resolves."""
    conn.execute("UPDATE theme SET status='merged', merged_into=? WHERE id=?", (into, tid))
    conn.execute("UPDATE moment SET theme_id=? WHERE theme_id=?", (into, tid))
    conn.commit()


def theme_codes(conn: sqlite3.Connection, tid: str,
                mid: str | None = None) -> list[sqlite3.Row]:
    """The codes this theme gathers. With `mid`, only those that actually fired in that material.

    Without the filter a line through one interview claimed to rest on codes drawn from every
    other interview in the project — provenance for evidence that is not there. A researcher
    reading "based on 40 codes" under a list of seven claims is being told something false.
    """
    sql = ("SELECT c.*, COUNT(h.sid) AS hits FROM theme_code tc JOIN code c ON c.id=tc.code_id "
           "LEFT JOIN code_hit h ON h.code_id = c.id")
    args: list = []
    if mid:
        sql += " AND h.material_id=?"
        args.append(mid)
    sql += " WHERE tc.theme_id=? GROUP BY c.id"
    args.append(tid)
    if mid:
        sql += " HAVING hits > 0"
    return conn.execute(sql + " ORDER BY c.name", args).fetchall()


# ---- moments and threads ----------------------------------------------------------------------

def save_moments(conn: sqlite3.Connection, mid: str, theme_id: str, moments: list[dict],
                 run_id: str | None = None) -> int:
    """Replace one thread. The old moments become 'superseded' rather than vanishing, so the
    export can show what a piece of feedback changed. `moments` is [{claim, anchor, sid}] and is
    ordered here by position in the material — the reader walks the material, not the model's
    output order."""
    if material(conn, mid) is None:
        return 0
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
                 run_id: str | None = None, fingerprint: str = "") -> str:
    """stage is 'orientation' (what this material is, written at framing) or 'reading' (what the
    reading found). Both are kept: the export shows what the analysis added to a description.

    `fingerprint` is what this text was written from, where the writer can say — only a theme's
    account does, so that the next chain can tell it would come back word for word."""
    if scope == "material" and material(conn, ref_id) is None:
        return ""
    conn.execute("UPDATE summary SET status='superseded' "
                 "WHERE scope=? AND ref_id=? AND stage=? AND status='live'", (scope, ref_id, stage))
    sid_ = db.new_id("s")
    conn.execute("INSERT INTO summary (id, scope, ref_id, stage, text, run_id, status, "
                 "fingerprint) VALUES (?,?,?,?,?,?,'live',?)",
                 (sid_, scope, ref_id, stage, text, run_id, fingerprint))
    conn.commit()
    return sid_


def get_summary(conn: sqlite3.Connection, scope: str, ref_id: str,
                stage: str | None = None) -> sqlite3.Row | None:
    """Without `stage`, the reading summary if there is one, else the orientation — which is what
    a page wants: the best account that exists right now.

    Every stage is ranked, not just `reading`. `angles` was added as a fourth stage and tied with
    `orientation` here, so on a material that had not been read yet the ideation list — where to
    look, in the system's own words — could be handed to the page as the material's description
    and to the corpus summary's prompt as this material's summary, which Law 5 forbids outright.
    """
    if stage:
        return conn.execute("SELECT * FROM summary WHERE scope=? AND ref_id=? AND stage=? "
                            "AND status='live'", (scope, ref_id, stage)).fetchone()
    return conn.execute(
        "SELECT * FROM summary WHERE scope=? AND ref_id=? AND status='live' "
        "ORDER BY CASE stage WHEN 'reading' THEN 0 WHEN 'orientation' THEN 1 "
        "WHEN 'angles' THEN 2 ELSE 3 END LIMIT 1", (scope, ref_id)).fetchone()


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


def feedback_for(conn: sqlite3.Connection, target_kind: str, target_id: str,
                 open_only: bool = False) -> list[sqlite3.Row]:
    """With `open_only`, just the comments no run has yet honoured. A comment is an instruction
    for the next rewrite of its block; once that rewrite has happened it is history, not a
    standing order — fed in forever, a note from six months ago would still steer every rerun."""
    sql = "SELECT * FROM feedback WHERE target_kind=? AND target_id=?"
    if open_only:
        sql += " AND consumed_by_run IS NULL"
    return conn.execute(sql + " ORDER BY created_at", (target_kind, target_id)).fetchall()


def consume_feedback(conn: sqlite3.Connection, fid: str, run_id: str) -> None:
    conn.execute("UPDATE feedback SET consumed_by_run=? WHERE id=? AND consumed_by_run IS NULL",
                 (run_id, fid))
    conn.commit()


def consume_material_feedback(conn: sqlite3.Connection, pid: str, mid: str, run_id: str,
                              theme_id: str | None = None) -> int:
    """Every open comment that this rewrite of the material has just answered.

    A comment on a claim plans no run of its own — a claim is checked against the material, not
    rewritten — so nothing ever marked one honoured. It went verbatim into every later prompt for
    that material, indefinitely, and the export called it open after five rewrites had answered
    it. A rewrite of one line answers that line's comments only, and leaves the summary's alone.
    """
    rows = conn.execute("SELECT * FROM feedback WHERE project_id=? AND consumed_by_run IS NULL "
                        "AND target_kind IN ('material_summary','moment')", (pid,)).fetchall()
    n = 0
    for f in rows:
        if f["target_kind"] == "moment":
            mo = moment(conn, f["target_id"])
            if mo is None or mo["material_id"] != mid or (theme_id and mo["theme_id"] != theme_id):
                continue
        elif f["target_id"] != mid or theme_id:
            continue
        consume_feedback(conn, f["id"], run_id)
        n += 1
    return n


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

def start_run(conn: sqlite3.Connection, pid: str, kind: str, mid: str | None, line: str,
              job: str | None = None) -> str:
    """`job` is which chain this step belongs to, so a chain interrupted by a restart can tell
    which of its steps are already done and resume rather than replay them."""
    from . import llm
    rid = db.new_id("r")
    conn.execute("INSERT INTO run (id, project_id, kind, material_id, provider, model, started, "
                 "line, job_id) VALUES (?,?,?,?,?,?,?,?,?)",
                 (rid, pid, kind, mid, llm.provider(), llm.model(), now(), line, job))
    conn.commit()
    return rid


def set_run_line(conn: sqlite3.Connection, rid: str, text: str) -> None:
    """What this step is doing now, as against what it set out to do. A long step says where it
    has got to on the same row the page is already reading."""
    conn.execute("UPDATE run SET line=? WHERE id=?", (text, rid))
    conn.commit()


def close_orphaned_runs(conn: sqlite3.Connection) -> int:
    """At process start nothing can be running, so every open run row belongs to a process that
    died mid-step. Left open, it keeps the page reloading itself every few seconds for ever — and a
    form nobody can finish filling in looks exactly like 'I cannot upload'."""
    cur = conn.execute("UPDATE run SET finished=?, error=? WHERE finished IS NULL",
                       (now(), "interrupted: the application restarted before this step finished"))
    conn.commit()
    return cur.rowcount


def finish_run(conn: sqlite3.Connection, rid: str, *, error: str | None = None,
               tokens_in: int = 0, tokens_out: int = 0, notes: list[str] | None = None) -> None:
    """`notes` is what the step set aside — a claim whose quote was not in the material, a line
    too thin to keep. It was computed and thrown away, which is how a reading loses material
    without anyone noticing; an empty cell then reads as 'nothing here' when it means 'three
    claims found and discarded'."""
    conn.execute("UPDATE run SET finished=?, error=?, tokens_in=?, tokens_out=?, notes=? "
                 "WHERE id=?",
                 (now(), error, tokens_in, tokens_out,
                  json.dumps(notes or [], ensure_ascii=False), rid))
    conn.commit()


def set_aside(conn: sqlite3.Connection, pid: str, mid: str | None = None) -> list[str]:
    """Everything the readings set aside, newest first, for the material or the whole project."""
    sql = "SELECT notes FROM run WHERE project_id=? AND notes NOT IN ('', '[]')"
    args: list = [pid]
    if mid:
        sql += " AND material_id=?"
        args.append(mid)
    out: list[str] = []
    for r in conn.execute(sql + " ORDER BY rowid DESC", args):
        try:
            out += json.loads(r["notes"])
        except ValueError:
            continue
    return out


def active_runs(conn: sqlite3.Connection, pid: str) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM run WHERE project_id=? AND finished IS NULL "
                        "ORDER BY started", (pid,)).fetchall()


def mark_unchanged(conn: sqlite3.Connection, rid: str) -> None:
    """This run left what it was written to move exactly as it was. Only a THEMES pass says so,
    and only `out_of_date` reads it — the reason is there."""
    conn.execute("UPDATE run SET changed=0 WHERE id=?", (rid,))
    conn.commit()


def last_run(conn: sqlite3.Connection, pid: str, kind: str, mid: str | None = None,
             changed: bool = False) -> sqlite3.Row | None:
    """The most recent run of this kind that finished without error."""
    sql = ("SELECT rowid AS seq, * FROM run WHERE project_id=? AND kind=? "
           "AND finished IS NOT NULL AND error IS NULL")
    args: list = [pid, kind]
    if changed:
        sql += " AND changed=1"
    if mid:
        sql += " AND material_id=?"
        args.append(mid)
    # Ordered by insertion, not by clock: a chain's steps routinely finish inside the same
    # millisecond, and comparing their timestamps then answers "no earlier" for both.
    return conn.execute(sql + " ORDER BY seq DESC LIMIT 1", args).fetchone()


def out_of_date(conn: sqlite3.Connection, pid: str) -> list[sqlite3.Row]:
    """Materials whose lines were written before the themes last changed.

    Themes are project-wide and go on changing as material arrives — widening, merging, splitting.
    A material synthesised against an older set is not wrong, but it was written to a different
    question, and the researcher should be told rather than have it silently re-run: bringing one
    up to date is minutes of thinking and real money, so it is their call, not ours.

    Against the last THEMES pass that actually moved the set. Every upload runs THEMES, and most
    passes leave the set exactly as it was — so measured against every pass, adding the fiftieth
    material put "Analysed before the themes last changed" on the other forty-nine rows, each
    with a paid button under it and nothing behind the claim.
    """
    themes = last_run(conn, pid, "themes", changed=True)
    if themes is None:
        return []
    stale = []
    for m in materials(conn, pid):
        doc = last_run(conn, pid, "doc", m["id"])
        if doc is not None and doc["seq"] < themes["seq"]:
            stale.append(m)
    return stale


def summary_state(conn: sqlite3.Connection, pid: str) -> dict:
    """Whether the corpus summary on the page is the current one, and if not, what happened.

    `behind` is how many materials have been read *again* since it was written; `unread` is how
    many have no reading at all. They used to be one number, which counted a material that
    failed, was interrupted or is still queued as one the summary was behind — so the page said
    it had been read, and the button it offered spent a dozen calls without changing the count.
    Counted by insertion order rather than by clock, for the reason `last_run` gives: a chain's
    steps land inside the same millisecond and their timestamps then say neither came first.
    `working` is a chain of this project's queued or running now; `error` is what stopped the
    last one, so a summary that was never rewritten does not sit there looking finished.
    """
    at = conn.execute("SELECT rowid FROM summary WHERE scope='project' AND ref_id=? "
                      "AND stage='reading' AND status='live'", (pid,)).fetchone()
    at = at["rowid"] if at else 0
    read = conn.execute(
        "SELECT s.rowid AS seq FROM material m LEFT JOIN summary s ON s.scope='material' "
        "AND s.ref_id=m.id AND s.stage='reading' AND s.status='live' "
        "WHERE m.project_id=? AND m.removed_at IS NULL", (pid,)).fetchall()
    job = conn.execute("SELECT * FROM job WHERE project_id=? ORDER BY rowid DESC LIMIT 1",
                       (pid,)).fetchone()
    return {"behind": sum(1 for r in read if r["seq"] is not None and r["seq"] > at),
            "unread": sum(1 for r in read if r["seq"] is None),
            "working": bool(job and job["status"] in ("queued", "running")),
            "error": (job["error"] or "") if job and job["status"] in ("failed", "stopped") else ""}


def runs(conn: sqlite3.Connection, pid: str) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM run WHERE project_id=? ORDER BY started", (pid,)).fetchall()


# ---- durable background jobs -----------------------------------------------------------------

def enqueue_job(conn: sqlite3.Connection, pid: str, runs: list[dict]) -> str:
    jid = db.new_id("j")
    conn.execute("INSERT INTO job (id, project_id, runs_json, status, created_at) "
                 "VALUES (?,?,?,'queued',?)",
                 (jid, pid, json.dumps(runs, ensure_ascii=False), now()))
    mids = {r.get("material_id") for r in runs if r.get("material_id")}
    conn.executemany("UPDATE material SET state='queued' WHERE id=? AND removed_at IS NULL",
                     [(mid,) for mid in mids])
    conn.commit()
    return jid


def job(conn: sqlite3.Connection, jid: str) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM job WHERE id=?", (jid,)).fetchone()


def pending_jobs(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """Queued work plus interrupted work from a previous process, oldest first."""
    return conn.execute("SELECT * FROM job WHERE status IN ('queued','running') "
                        "ORDER BY created_at, rowid").fetchall()


def requeue_job(conn: sqlite3.Connection, jid: str) -> list[dict]:
    """An interrupted chain, ready to run again: back to 'queued', minus the steps it finished.

    The worker only accepts a 'queued' job, so a job left 'running' by a restart was refused and
    then marked finished by the worker's `finally` — the rest of an upload was never read, and
    nothing on any page would start it again. Steps are matched by kind and material in the order
    they were planned, which is the order they ran, so twelve accounts in one chain resume at the
    one that died rather than all at once.
    """
    row = job(conn, jid)
    done = Counter((r["kind"], r["material_id"]) for r in conn.execute(
        "SELECT kind, material_id FROM run WHERE job_id=? AND finished IS NOT NULL "
        "AND error IS NULL", (jid,)))
    left = []
    for r in json.loads(row["runs_json"]):
        key = (r["kind"], r.get("material_id"))
        if done[key]:
            done[key] -= 1
        else:
            left.append(r)
    conn.execute("UPDATE job SET status='queued', runs_json=? WHERE id=?",
                 (json.dumps(left, ensure_ascii=False), jid))
    conn.commit()
    return left


def start_job(conn: sqlite3.Connection, jid: str) -> None:
    conn.execute("UPDATE job SET status='running', started_at=?, finished_at=NULL, error='' "
                 "WHERE id=?", (now(), jid))
    conn.commit()


def finish_job(conn: sqlite3.Connection, jid: str, error: str = "") -> None:
    # Only a running job finishes; one the researcher stopped keeps saying so.
    conn.execute("UPDATE job SET status=?, finished_at=?, error=? WHERE id=? AND status IN ('queued','running')",
                 ("failed" if error else "finished", now(), error, jid))
    conn.commit()


def stop_jobs(conn: sqlite3.Connection, pid: str) -> int:
    """The researcher's stop. Queued work never starts; running work ends after the step in
    flight, because a model call cannot be taken back once sent — but nothing after it is."""
    cur = conn.execute("UPDATE job SET status='stopped', finished_at=?, error='stopped by the "
                       "researcher' WHERE project_id=? AND status IN ('queued','running')",
                       (now(), pid))
    conn.commit()
    return cur.rowcount


# ---- accounts ----------------------------------------------------------------------------------

def _hash(password: str, salt: bytes) -> bytes:
    """scrypt from the standard library. n=2**14 is the interactive-login setting: about a tenth
    of a second here, and 16 MB of memory per guess for anyone with the file."""
    return hashlib.scrypt(password.encode(), salt=salt, n=2 ** 14, r=8, p=1, dklen=32)


def create_user(conn: sqlite3.Connection, name: str, password: str, is_admin: bool = False) -> str:
    """The password is never stored, only a per-user salt and the derived key."""
    uid = db.new_id("u")
    salt = secrets.token_bytes(16)
    conn.execute("INSERT INTO user (id, name, password_hash, is_admin) VALUES (?,?,?,?)",
                 (uid, name, f"{salt.hex()}:{_hash(password, salt).hex()}", int(is_admin)))
    conn.commit()
    return uid


def verify_user(conn: sqlite3.Connection, name: str, password: str) -> sqlite3.Row | None:
    row = conn.execute("SELECT * FROM user WHERE name=?", (name,)).fetchone()
    if row is None:
        return None
    salt, want = row["password_hash"].split(":")
    ok = secrets.compare_digest(_hash(password, bytes.fromhex(salt)), bytes.fromhex(want))
    return row if ok else None


def users(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM user ORDER BY name").fetchall()


def projects_for(conn: sqlite3.Connection, user_row: sqlite3.Row | None) -> list[sqlite3.Row]:
    """Theirs, newest first — every project for an admin, and for a database with no accounts in
    it at all, which is how this runs on a laptop."""
    if user_row is None or user_row["is_admin"]:
        return conn.execute("SELECT * FROM project ORDER BY created_at DESC").fetchall()
    return conn.execute("SELECT * FROM project WHERE owner_id=? ORDER BY created_at DESC",
                        (user_row["id"],)).fetchall()


def set_password(conn: sqlite3.Connection, uid: str, password: str) -> None:
    """A fresh salt and derived key. The first admin's password comes from an environment variable
    that Coolify prints into its build log, so being able to change it is not a nicety."""
    salt = secrets.token_bytes(16)
    conn.execute("UPDATE user SET password_hash=? WHERE id=?",
                 (f"{salt.hex()}:{_hash(password, salt).hex()}", uid))
    conn.commit()


# ---- added for the page fixes

def has_text(conn: sqlite3.Connection, pid: str, text: str) -> bool:
    """Whether this project already holds this exact text.

    A double-click on Add material, or a folder dropped in twice, made two identical materials.
    Both were framed, read and synthesised — a second chain's worth of money — and every
    derivation then counted one source as two, which is the corroboration Law 4 exists to make
    trustworthy. A material that was removed is not in the way of adding it again.
    """
    return conn.execute("SELECT 1 FROM material WHERE project_id=? AND text=? "
                        "AND removed_at IS NULL LIMIT 1", (pid, text)).fetchone() is not None


def sign_out_others(conn: sqlite3.Connection, uid: str, keep: str = "") -> int:
    """Every session for this account except the one asking.

    Changing a password is only a change if the sessions the old one opened stop working — and
    the reason for changing the first admin's is that an environment variable put it in a build
    log in clear.
    """
    n = conn.execute("DELETE FROM session WHERE user_id=? AND token<>?", (uid, keep)).rowcount
    conn.commit()
    return n


def set_owner(conn: sqlite3.Connection, pid: str, uid: str) -> None:
    """Hand a project over. One made before accounts existed has no owner and is invisible to
    every researcher for ever; the admin page said "Owner not set" and offered nothing."""
    conn.execute("UPDATE project SET owner_id=? WHERE id=?", (uid, pid))
    conn.commit()
