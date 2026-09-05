"""P22 — what an operator can see. The `aperture` log on stdout, and `/admin/runs`.

The instrument wrote nothing of its own: when a model call stalled for an hour, the only trace
anywhere was a grey line under one project's summary, and the host's Logs held uvicorn's access
lines and nothing else. One line per model call, one per job and one per step — and a page that
reads the `run` table across every project, which until now only each project's owner could see.

The rule these tests exist to hold: **ids, counts and times, never the material.** A log leaves the
researcher's machine; a title is usually somebody's name.
"""
from __future__ import annotations

import logging
import re

import pytest

from app import db, jobs, store

accounts = pytest.importorskip("app.accounts")


@pytest.fixture
def said(caplog):
    """Everything the app logged, as one string."""
    class Log:
        def __str__(self):
            return "\n".join(r.getMessage() for r in caplog.records)

        def __contains__(self, needle):
            return needle in str(self)

    with caplog.at_level(logging.INFO, logger="aperture"):
        yield Log()


# ---- the log ------------------------------------------------------------------------------------

def test_a_model_call_leaves_one_line_with_its_tokens_and_its_seconds(
        said, real_chat_json, monkeypatch):
    from app import llm

    def answer(system, user, timeout, effort="", label=""):
        llm.usage["tokens_in"] += 7692
        llm.usage["tokens_out"] += 1681
        return '{"ok": true}'

    monkeypatch.setattr(llm, "_ask", answer)
    llm.new_usage()
    assert real_chat_json("a system message", "the material", label="thread") == {"ok": True}
    assert re.fullmatch(r"llm label=thread provider=minimax model=MiniMax-M3 "
                        r"in=7692 out=1681 s=\d+\.\d", str(said)), str(said)


def test_a_busy_provider_says_which_wait_it_is_on(said, real_chat_json, monkeypatch):
    """The line the researcher greps for when a chain has gone quiet: 429, and how long."""
    from app import llm

    tries = []

    def send(body, timeout):
        tries.append(1)
        if len(tries) == 1:
            raise llm._Busy("429 from somewhere", "", 429)
        return '{"ok": true}'

    monkeypatch.setattr(llm, "_send", send)
    monkeypatch.setattr(llm, "_sleep", lambda s: None)
    real_chat_json("s", "u", label="read")
    assert "llm label=read busy=429 wait=15s try=1/5" in said


def test_a_job_and_its_steps_are_on_the_log_and_the_material_is_not(
        said, conn, project, grande, monkeypatch):
    monkeypatch.setitem(jobs.STEPS, "read", ("Reading {name}", lambda c, p, r: None))

    jid = jobs.start(db.connect, project, [{"kind": "read", "material_id": grande}])
    assert jobs.wait(jid, 10)

    assert f"job id={jid} project={project} started steps=1" in said
    assert f"step kind=read project={project} material={grande} started" in said
    assert re.search(rf"step kind=read project={project} material={grande} "
                     rf"finished s=\d+\.\d in=0 out=0", str(said)), str(said)
    assert re.search(rf"job id={jid} project={project} finished s=\d+\.\d", str(said))

    # The whole point. A log line is read by whoever runs the host, not by the material's owner:
    # the progress line "Reading DP-40 Grande" stays on the run row, where its owner reads it.
    for private in (store.material(conn, grande)["name"], store.sentences(conn, grande)[0][1]):
        assert private not in said, f"{private!r} reached the log"


def test_a_step_that_fails_says_so_without_quoting_the_model_back(
        said, conn, project, grande, monkeypatch):
    """`parse` puts up to 200 characters of an answer it could not read into its message, and that
    message is the run row's error. Eighty characters is short of where the answer starts."""
    from app import llm

    def boom(c, p, r):
        raise llm.LLMError("the model's answer was not JSON, twice: no JSON object in model "
                           "output: 'M. Grande said she crossed in the winter of 1952'")

    monkeypatch.setitem(jobs.STEPS, "read", ("Reading {name}", boom))
    jobs.run_now(conn, project, [{"kind": "read", "material_id": grande}])

    assert f"step kind=read project={project} material={grande} failed: LLMError" in said
    assert "crossed in the winter" not in said
    assert "crossed in the winter" in store.runs(conn, project)[0]["error"], \
        "the reason in full still belongs on the row its owner reads"


# ---- the page -----------------------------------------------------------------------------------

@pytest.fixture
def client(conn, monkeypatch):
    from fastapi.testclient import TestClient
    from app import main, pages, verbs
    for mod in (pages, verbs, accounts):
        monkeypatch.setattr(mod, "connection", lambda: conn, raising=False)
    return TestClient(main.app, follow_redirects=False)


@pytest.fixture
def ran(conn, project, grande):
    """One finished run, one failed, one still going."""
    ok = store.start_run(conn, project, "read", grande, "Reading DP-40 Grande")
    store.finish_run(conn, ok, tokens_in=7692, tokens_out=1681, notes=["a claim without a quote"])
    bad = store.start_run(conn, project, "doc", grande, "Writing what stands out")
    store.finish_run(conn, bad, error="ReadTimeout: the model went quiet")
    store.start_run(conn, project, "frame", grande, "Working out how this is laid out")
    return project


def test_the_runs_page_is_not_there_for_anyone_but_an_administrator(client, conn, ran):
    store.create_user(conn, "ada", "correct horse", is_admin=True)
    store.create_user(conn, "ann", "battery staple")

    assert client.get("/admin/runs").status_code == 303        # signed out, as /admin is
    client.post("/login", data={"name": "ann", "password": "battery staple"})
    assert client.get("/admin/runs").status_code == 404        # not yours to know it exists
    client.post("/logout")
    client.post("/login", data={"name": "ada", "password": "correct horse"})
    assert client.get("/admin/runs").status_code == 200


def test_an_administrator_sees_every_projects_runs_and_no_material(client, conn, ran, grande):
    from app import context
    store.create_user(conn, "ada", "correct horse", is_admin=True)
    client.post("/login", data={"name": "ada", "password": "correct horse"})
    page = client.get("/admin/runs").text

    assert "Test project" in page and grande in page             # the project's name, the id
    assert "Coding" in page and "Synthesis" in page              # the words the pages already use
    assert "7,692" in page and "1,681" in page                   # today's totals, and the run's
    assert "ReadTimeout: the model went quiet" in page
    assert "<td>running</td>" in page and "<td>ok</td>" in page

    material = store.material(conn, grande)
    assert material["name"] not in page, "a title is usually somebody's name"
    assert store.sentences(conn, grande)[0][1] not in page
    for word in context._BANNED:                                # 'frame' is ours, not the page's
        assert not re.search(rf"\b{re.escape(word)}s?\b", page, re.I), word


def test_the_daily_table_totals_what_the_instrument_did(conn, ran):
    day, = store.runs_by_day(conn)
    assert (day["runs"], day["failed"], day["tokens_in"], day["tokens_out"],
            day["set_aside"]) == (3, 1, 7692, 1681, 1)
    assert day["minutes"] >= 0        # two rows finished; the third is still going and adds none
    assert day["day"] == store.now()[:10]


def test_the_last_runs_come_back_newest_first_with_their_project(conn, ran):
    rows = store.recent_runs(conn)
    assert [r["kind"] for r in rows] == ["frame", "doc", "read"]
    assert {r["project"] for r in rows} == {"Test project"}
    assert rows[0]["seconds"] is None and rows[-1]["seconds"] >= 0
    assert store.recent_runs(conn, limit=1) == rows[:1]


def test_a_run_says_how_many_tries_it_took_and_what_the_provider_served_cached(client, conn, ran):
    """A step is many calls, and until the `call` table the page could only say what they cost
    together. `not reported` where the provider mentioned no cached count — never nought, which
    would claim the call cached nothing."""
    store.create_user(conn, "ada", "correct horse", is_admin=True)
    client.post("/login", data={"name": "ada", "password": "correct horse"})
    rid = store.start_run(conn, ran, "doc", None, "Writing what stands out")
    store.save_call(conn, rid, "thread", 1, "minimax", "MiniMax-M3", "medium",
                    {"tokens_in": 9000, "tokens_out": 400}, store.now(), 61.0, "invalid_json")
    store.save_call(conn, rid, "thread", 2, "minimax", "MiniMax-M3", "medium",
                    {"tokens_in": 9000, "tokens_out": 400, "tokens_cached": 7800},
                    store.now(), 58.0, "ok")
    store.finish_run(conn, rid, tokens_in=18000, tokens_out=800)

    row = next(r for r in store.recent_runs(conn) if r["id"] == rid)
    assert (row["attempts"], row["cached"]) == (2, 7800)
    assert store.runs_by_day(conn)[0]["cached"] == 7800

    page = client.get("/admin/runs").text
    assert "Tries" in page and "7,800" in page and "not reported" in page
