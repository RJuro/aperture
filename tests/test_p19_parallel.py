"""What runs beside what. `jobs._stages`, `jobs._together`, `llm.usage` per context.

Measured on a real three-interview run the chain was strictly sequential — one thread, one global
lock, one module-level token counter — so three readings that touch nothing of each other's ran
one after another. These tests hold the shape that replaced it:

    a material's own steps keep their own order
    materials run beside each other, capped at `jobs.PARALLEL`
    everything that touches what the PROJECT shares still runs alone — THEMES because it revises
      one theme set, READ because it is shown the codebook the last reading left behind
    every run row still carries its own line, its own tokens and its own error

Overlap is asserted with a `threading.Barrier`, never with a stopwatch: a barrier of three that
does not time out is three steps that genuinely ran at the same moment, on any machine under any
load. The clock is read only to say by how much they overlapped.
"""
from __future__ import annotations

import re
import threading
import time

import pytest

from app import db, ingest, jobs, llm, store

SEED = {"grande": "DP-40 GRANDE, M.txt", "rodwin": "EI-845 RODWIN.txt"}


# ---- what a step does while the test watches ----------------------------------------------------

class Watch:
    """Every step that ran: when it started, when it stopped, and on which thread."""

    def __init__(self, monkeypatch, hold=None, wait=0.0, boom=()):
        """`wait` is how long a step takes — a number for all of them, or per kind, so a test can
        give READ the length it really has against FRAME and ANGLES."""
        self.spans: list[dict] = []
        self.lock = threading.Lock()
        self.hold, self.wait, self.boom = hold, wait, boom
        for kind, (text, _) in list(jobs.STEPS.items()):
            monkeypatch.setitem(jobs.STEPS, kind, (text, self._make(kind)))

    def _make(self, kind):
        def step(conn, pid, run):
            mid = run.get("material_id")
            started = time.monotonic()
            try:
                if self.hold and kind in self.hold:
                    self.hold[kind].wait(timeout=5)     # BrokenBarrier if they never met
                time.sleep(self.wait.get(kind, 0) if isinstance(self.wait, dict)
                           else self.wait)
                if (kind, mid) in self.boom or kind in self.boom:
                    raise RuntimeError(f"the model said no to {kind}")
            finally:
                with self.lock:
                    self.spans.append({"kind": kind, "mid": mid, "at": started,
                                       "until": time.monotonic(),
                                       "thread": threading.get_ident()})
        return step

    def of(self, kind: str) -> list[dict]:
        return [s for s in self.spans if s["kind"] == kind]

    def kinds(self) -> list[str]:
        return [s["kind"] for s in self.spans]

    def overlap(self, a: dict, b: dict) -> float:
        """Seconds these two steps were running at the same time."""
        return min(a["until"], b["until"]) - max(a["at"], b["at"])

    def alone(self, kind: str) -> bool:
        """Nothing else was running while any step of this kind was."""
        return all(self.overlap(mine, other) <= 0
                   for mine in self.of(kind) for other in self.spans if other is not mine)


@pytest.fixture
def three(conn, project):
    """Three materials in one project. Real sentences, no model within a mile of them."""
    mids = []
    for i in range(3):
        text = (f"This is material {i}. It has a first sentence and a second one. "
                f"Nobody in it says anything about the weather. It ends here.")
        mid = store.add_material(conn, project, f"material-{i}.txt", text)
        store.save_sentences(conn, mid, ingest.sentences(text))
        mids.append(mid)
    return mids


def plan(mids: list[str]) -> list[dict]:
    """Exactly what `jobs.ingest_chain` queues, without the job row or the thread."""
    got: list[dict] = []
    real = jobs.start
    jobs.start = lambda factory, pid, runs: got.extend(runs)
    try:
        jobs.ingest_chain("p", mids)
    finally:
        jobs.start = real
    return got


# ---- one counter per call, not one per process --------------------------------------------------

def test_two_calls_at_once_do_not_mix_their_token_counts():
    """`llm.usage` was one module-level dict, which is why nothing could run in parallel: the
    second step's first token landed on the first step's row."""
    import contextvars
    counted, ready = {}, threading.Barrier(2, timeout=5)

    def spend(name, tokens):
        llm.new_usage()
        llm.usage["tokens_in"] += tokens
        ready.wait()                          # both counters are open at the same moment
        llm.usage["tokens_out"] += tokens * 2
        counted[name] = dict(llm.usage)

    threads = [threading.Thread(target=contextvars.copy_context().run, args=(spend, n, t))
               for n, t in (("a", 100), ("b", 7))]
    for t in threads:
        t.start()
    for t in threads:
        t.join(5)
    assert counted == {"a": {"tokens_in": 100, "tokens_out": 200},
                       "b": {"tokens_in": 7, "tokens_out": 14}}


def test_a_progress_line_lands_on_the_row_of_the_step_that_wrote_it():
    """`llm.report` was one module-level hook. Two steps at once and the second one's 'the model
    is busy' was written onto the first one's run row."""
    import contextvars
    said, ready = {}, threading.Barrier(2, timeout=5)

    def step(name):
        with llm.reporting(lambda msg, n=name: said.setdefault(n, []).append(msg)):
            ready.wait()
            llm.report(f"halfway through {name}")

    threads = [threading.Thread(target=contextvars.copy_context().run, args=(step, n))
               for n in ("a", "b")]
    for t in threads:
        t.start()
    for t in threads:
        t.join(5)
    assert said == {"a": ["halfway through a"], "b": ["halfway through b"]}
    llm.report("and nobody is listening out here")
    assert said == {"a": ["halfway through a"], "b": ["halfway through b"]}


# ---- materials beside each other ----------------------------------------------------------------

def test_three_materials_are_framed_and_ideated_side_by_side(conn, project, three, monkeypatch):
    """Three materials, three threads. The barrier is the assertion: it releases only when all
    three FRAME steps are inside it at the same time."""
    watch = Watch(monkeypatch, hold={"frame": threading.Barrier(3, timeout=5),
                                     "angles": threading.Barrier(3, timeout=5)})
    jobs.run_now(conn, project, plan(three))

    assert len(watch.of("frame")) == 3 and len({s["thread"] for s in watch.of("frame")}) == 3
    a, b, c = watch.of("frame")
    assert watch.overlap(a, b) > 0 and watch.overlap(b, c) > 0
    for mid in three:
        assert [s["kind"] for s in watch.spans if s["mid"] == mid] == \
            ["frame", "angles", "read", "themes", "doc"], "one material's own order is kept"


def test_the_readings_themselves_still_queue_behind_each_other(conn, project, three, monkeypatch):
    """READ is shown the project codebook and `store.save_codes` reuses a code by name. Two
    readings at once would each be shown a codebook without the other's codes and would coin two
    rows for one name — so a reading waits for the reading before it, in the planned order, while
    the NEXT material's framing and ideation overlap it."""
    watch = Watch(monkeypatch, wait={"frame": 0.01, "angles": 0.01, "read": 0.15})
    jobs.run_now(conn, project, plan(three))

    reads = watch.of("read")
    assert [s["mid"] for s in reads] == three, "in the order the chain planned them"
    assert all(watch.overlap(reads[i], reads[i + 1]) <= 0 for i in range(2)), "never at once"
    # And the queue costs nothing: every material was framed and worked out while the first one
    # was being read, so each reading starts the moment the one before it ends.
    assert max(s["until"] for s in watch.of("angles")) <= reads[0]["until"]
    assert all(0 <= reads[i + 1]["at"] - reads[i]["until"] < 0.1 for i in range(2))


def test_themes_runs_beside_nothing_at_all(conn, project, three, monkeypatch):
    """It revises one set shared by the whole project, and every material is read before any of
    them moves it."""
    watch = Watch(monkeypatch, wait=0.01)
    jobs.run_now(conn, project, plan(three))

    assert len(watch.of("themes")) == 3 and watch.alone("themes")
    assert [s["mid"] for s in watch.of("themes")] == three
    last_read = max(s["until"] for s in watch.of("read"))
    assert min(s["at"] for s in watch.of("themes")) >= last_read
    assert watch.alone("accounts") and watch.alone("project")


def test_what_stands_out_in_each_material_is_written_side_by_side(conn, project, three,
                                                                  monkeypatch):
    """DOC is the dominant cost of the chain — one nine-theme material measured 1351 s — and it
    writes only its own material's rows."""
    watch = Watch(monkeypatch, hold={"doc": threading.Barrier(3, timeout=5)})
    jobs.run_now(conn, project, plan(three))

    docs = watch.of("doc")
    assert len(docs) == 3 and len({s["thread"] for s in docs}) == 3
    assert watch.overlap(docs[0], docs[1]) > 0 and watch.overlap(docs[1], docs[2]) > 0
    assert min(s["at"] for s in docs) >= max(s["until"] for s in watch.of("themes"))


def test_no_more_than_four_materials_are_worked_on_at_once(conn, project, monkeypatch):
    """The cap is the provider's rate limit, not the machine's."""
    from app import ingest as _ing
    mids = []
    for i in range(6):
        text = f"Material {i}. It has two sentences."
        mid = store.add_material(conn, project, f"m{i}.txt", text)
        store.save_sentences(conn, mid, _ing.sentences(text))
        mids.append(mid)
    watch = Watch(monkeypatch, wait=0.02)
    jobs.run_now(conn, project, plan(mids))

    frames = watch.of("frame")
    assert len(frames) == 6
    at_once = max(sum(1 for b in frames if watch.overlap(a, b) > 0) for a in frames)
    assert 2 <= at_once <= jobs.PARALLEL, "four in flight, no more"


# ---- what lands on the rows ---------------------------------------------------------------------

def test_every_run_row_still_carries_its_own_tokens_and_its_own_line(conn, project, three,
                                                                     monkeypatch):
    ready = threading.Barrier(3, timeout=5)

    def spend(conn_, pid, run):
        mid = run["material_id"]
        n = three.index(mid) + 1
        llm.usage["tokens_in"] += 100 * n
        ready.wait()                                    # all three counters open at once
        llm.usage["tokens_out"] += n
        llm.report(f"working on {n}")

    for kind, (text, _) in list(jobs.STEPS.items()):
        monkeypatch.setitem(jobs.STEPS, kind, (text, lambda c, p, r: None))
    monkeypatch.setitem(jobs.STEPS, "frame", (jobs.STEPS["frame"][0], spend))
    jobs.run_now(conn, project, plan(three))

    rows = {r["material_id"]: r for r in store.runs(conn, project) if r["kind"] == "frame"}
    for n, mid in enumerate(three, 1):
        assert (rows[mid]["tokens_in"], rows[mid]["tokens_out"]) == (100 * n, n)
        assert rows[mid]["line"].endswith(f"— working on {n}")
    assert all(r["tokens_in"] == 0 for r in store.runs(conn, project) if r["kind"] != "frame"), \
        "and no other step is billed for them"


def test_a_material_that_fails_stops_its_own_sequence_and_the_chain_before_themes(
        conn, project, three, monkeypatch):
    """The other materials finish what they were doing — a failure is one material's, not the
    upload's — and then the chain stops rather than finding themes over a half-read corpus."""
    watch = Watch(monkeypatch, boom=[("read", three[1])])
    jobs.run_now(conn, project, plan(three))

    assert [s["mid"] for s in watch.of("read")] == three, "each material still tried to read"
    assert [s["kind"] for s in watch.spans if s["mid"] == three[1]] == ["frame", "angles", "read"]
    assert "themes" not in watch.kinds() and "doc" not in watch.kinds()

    rows = store.runs(conn, project)
    failed = next(r for r in rows if r["kind"] == "read" and r["material_id"] == three[1])
    assert "the model said no to read" in failed["error"]
    assert [r["error"] for r in rows if r["kind"] == "read" and r["material_id"] != three[1]] == \
        [None, None], "one material's failure is not another's"
    stopped = next(r for r in rows if r["kind"] == "themes")
    assert "not run" in stopped["error"] and "material-1.txt" in stopped["error"]
    assert "the model said no to read" in stopped["error"], "the page says why it stopped"
    assert store.material(conn, three[1])["state"] == "failed"
    assert [store.material(conn, m)["state"] for m in (three[0], three[2])] == ["ready", "ready"]


def test_two_threads_writing_run_rows_through_separate_connections_both_succeed(conn, project):
    """WAL plus `PRAGMA busy_timeout`: the second writer waits for the lock instead of raising
    'database is locked'."""
    problems, ready = [], threading.Barrier(2, timeout=5)

    def write(tag):
        c = db.connect()
        try:
            ready.wait()
            for i in range(40):
                rid = store.start_run(c, project, "read", None, f"{tag} {i}")
                store.finish_run(c, rid, tokens_in=i)
        except Exception as e:                                  # noqa: BLE001 — the point
            problems.append(f"{type(e).__name__}: {e}")
        finally:
            c.close()

    threads = [threading.Thread(target=write, args=(t,)) for t in ("a", "b")]
    for t in threads:
        t.start()
    for t in threads:
        t.join(20)
    assert problems == []
    assert len(store.runs(conn, project)) == 80


# ---- and the same reading comes out ------------------------------------------------------------

def _answer(system: str, user: str, *, label: str = "", timeout=None) -> dict:
    """A model that answers from the prompt in front of it rather than from a queue, so the same
    chain run in a different order is shown the same things and answers the same way."""
    passages = re.findall(r"^(S\d+)  (.+)$", user, re.M)
    usable = [(sid, " ".join(t.split()[:8])) for sid, t in passages
              if 6 <= len(t.split()) <= 20 and not t.endswith(":")]
    picked = usable[10::9][:5]
    if label == "frame":
        return {"kind": "other", "display": "plain", "title": "A piece of material",
                "orientation": "What this material is, in one line."}
    if label == "angles":
        return {"field": "migration", "subareas": ["work", "family"],
                "angles": [{"name": "Work", "why": "the material keeps returning to it",
                            "questions": ["what work is named?", "who names it?"]}]}
    if label == "read":
        return {"codes": [{"code": {"name": "Work", "definition": "how a living is made"},
                           "sids": [sid for sid, _ in usable[:6]]},
                          {"code": {"name": "Leaving", "definition": "the crossing"},
                           "sids": [sid for sid, _ in usable[6:12]]}]}
    if label == "themes":
        known = re.findall(r"- id (\S+) ·", user)
        return {"themes": [{"id": known[0] if known else None, "name": "Work and trade",
                            "gist": "how a living is made", "code_names": ["Work"]}]}
    if label == "thread":
        return {"summary": "what this theme comes to here",
                "moments": [{"claim": f"claim {i}", "anchor": text, "sid": sid}
                            for i, (sid, text) in enumerate(picked)]}
    if label in ("verify", "verify_summary"):
        return {"verdicts": []}
    if label == "doc":
        return {"summary": "what the reading found", "questions": "what is still open?",
                "people": []}
    if label == "account":
        return {"account": "What this theme amounts to across the corpus."}
    if label == "project":
        return {"summary": "what the corpus shows", "interpretation": "what it may mean"}
    raise AssertionError(f"no canned answer for {label!r}")


def _snapshot(conn, pid: str) -> dict:
    """The reading, with every id replaced by the name it stands for — so two projects that read
    the same material the same way compare equal."""
    mats = {m["id"]: m["name"] for m in store.materials(conn, pid)}
    themes = {t["id"]: t["name"] for t in conn.execute("SELECT * FROM theme WHERE project_id=?",
                                                       (pid,))}
    moments = sorted(
        (mats[r["material_id"]], themes[r["theme_id"]], r["sid"], r["position"], r["claim"],
         r["anchor"], r["status"])
        for r in conn.execute("SELECT m.* FROM moment m JOIN material x ON x.id=m.material_id "
                              "WHERE x.project_id=?", (pid,)))
    codes = sorted(
        (r["name"], r["definition"], r["origin"],
         tuple(sorted(f'{mats[h["material_id"]]}:{h["sid"]}' for h in conn.execute(
             "SELECT * FROM code_hit WHERE code_id=?", (r["id"],)))))
        for r in store.codebook(conn, pid))
    named = {**mats, **themes, pid: "the project"}
    summaries = sorted(
        (r["scope"], named.get(r["ref_id"], r["ref_id"]), r["stage"], r["text"], r["status"])
        for r in conn.execute(
            "SELECT * FROM summary WHERE ref_id IN "
            "(SELECT id FROM material WHERE project_id=?) OR ref_id IN "
            "(SELECT id FROM theme WHERE project_id=?) OR ref_id=?", (pid, pid, pid)))
    return {"moments": moments, "codes": codes, "summaries": summaries}


def test_the_same_answers_land_the_same_reading_side_by_side_as_one_at_a_time(conn, monkeypatch):
    """The point of the whole change: the chain gets faster and the reading does not move."""
    from pathlib import Path
    seed = Path(__file__).resolve().parent.parent / "seed"
    monkeypatch.setattr(llm, "chat_json", _answer)

    def read_a_corpus(name: str) -> str:
        pid = store.create_project(conn, name, focus="why people left")
        mids = []
        for f in sorted(SEED.values()):
            raw = (seed / f).read_text()
            mid = store.add_material(conn, pid, f, raw)
            store.save_sentences(conn, mid, ingest.sentences(raw))
            mids.append(mid)
        jobs.run_now(conn, pid, plan(mids))
        return pid

    one_at_a_time = jobs._stages
    monkeypatch.setattr(jobs, "_stages", lambda runs: [[[r]] for r in runs])
    before = _snapshot(conn, read_a_corpus("one step at a time"))
    monkeypatch.setattr(jobs, "_stages", one_at_a_time)
    after = _snapshot(conn, read_a_corpus("side by side"))

    assert before["moments"] and before["codes"] and before["summaries"], "it really read"
    assert after == before
