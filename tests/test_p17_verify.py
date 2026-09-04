"""VERIFY — every claim read once more against its own passage. `app/engine/verify.py`,
`app/prompts/verify.md`.

    verify.run(conn, mid, *, theme_id=None) -> {"dropped", "set_aside", "marked"}

The anchor law rules that the quote is really there; it cannot rule on what was built on top of
it. A real run produced "he took factory work without complaint" over a passage that said only
that he got a job in a factory. The quote was verbatim and the citation was right.

Python owns the outcome: `not` sets the claim aside and says so, `partly` marks it where it is
read, `supported` and a missing verdict change nothing at all.
"""
from __future__ import annotations

import pytest

from app import context, store

synth = pytest.importorskip("app.engine.synth")
verify = pytest.importorskip("app.engine.verify")


@pytest.fixture
def client(conn, monkeypatch):
    from fastapi.testclient import TestClient
    from app import main
    monkeypatch.setattr(main, "conn", conn, raising=False)
    from app import pages
    monkeypatch.setattr(pages, "connection", lambda: conn, raising=False)
    return TestClient(main.app)


@pytest.fixture
def ready(conn, project, grande):
    store.save_frame(conn, grande, kind="interview", display="turns", title="Grande",
                     speakers=[{"label": "GRANDE", "name": "M. Grande", "role": "participant"}],
                     segments=[])
    store.save_summary(conn, "material", grande, "orientation", "A 1978 oral history.")
    tid = store.save_theme(conn, project, tid=None, name="Work", gist="a living", code_ids=[])
    return {"pid": project, "mid": grande, "tid": tid}


def _moments(quote, mid, n=5, at=40):
    return [{"claim": f"claim {i}", "anchor": " ".join(quote(mid, at=at + i * 9)[1].split()[:8]),
             "sid": quote(mid, at=at + i * 9)[0]} for i in range(n)]


def run_doc(model, conn, ready, quote, verdicts=None, n=5, summary="what the reading found"):
    """One full DOC: the line, the check, the summary."""
    model.queue({"moments": _moments(quote, ready["mid"], n)},
                {"verdicts": verdicts or []},
                {"summary": summary, "questions": "", "people": []})
    return synth.doc(conn, ready["mid"])


def claims(conn, ready):
    return store.thread(conn, ready["mid"], ready["tid"])


# ---- what each verdict does ------------------------------------------------------------------

def test_a_claim_its_passage_does_not_carry_is_set_aside_and_named(ready, conn, model, quote):
    run_doc(model, conn, ready, quote)
    doomed = claims(conn, ready)[0]
    model.queue({"verdicts": [{"id": doomed["id"], "verdict": "not",
                               "why": "the passage says the mother chose it"}]})
    out = verify.run(conn, ready["mid"])

    assert store.moment(conn, doomed["id"])["status"] == "superseded"
    assert doomed["id"] not in [m["id"] for m in claims(conn, ready)]
    assert out["set_aside"] == [doomed["id"]]
    said = out["dropped"][0]
    assert said.startswith("a claim was set aside — its passage does not carry it:")
    assert doomed["claim"][:60] in said and "the mother chose it" in said


def test_a_claim_the_passage_only_partly_carries_stays_live_and_is_marked(ready, conn, model,
                                                                          quote):
    run_doc(model, conn, ready, quote)
    marked = claims(conn, ready)[0]
    model.queue({"verdicts": [{"id": marked["id"], "verdict": "partly",
                               "why": "'without complaint' is not in the passage"}]})
    out = verify.run(conn, ready["mid"])

    row = store.moment(conn, marked["id"])
    assert row["status"] == "live", "a claim worth reading with the addition named beside it"
    assert row["support"] == "partly"
    assert row["support_note"] == "'without complaint' is not in the passage"
    assert out["marked"] == [marked["id"]] and out["dropped"] == []


def test_a_reading_every_claim_of_which_holds_is_left_exactly_as_it_was(ready, conn, model,
                                                                        quote):
    run_doc(model, conn, ready, quote)
    before = [dict(m) for m in claims(conn, ready)]
    model.queue({"verdicts": [{"id": m["id"], "verdict": "supported", "why": ""} for m in before]})
    out = verify.run(conn, ready["mid"])

    assert [dict(m) for m in claims(conn, ready)] == before
    assert out == {"dropped": [], "set_aside": [], "marked": []}


def test_an_id_from_nowhere_is_ignored_and_a_claim_with_no_verdict_stands(ready, conn, model,
                                                                          quote):
    """A missing verdict must not be able to delete a claim; the prompt says as much."""
    run_doc(model, conn, ready, quote)
    before = [dict(m) for m in claims(conn, ready)]
    model.queue({"verdicts": [{"id": "mo-does-not-exist", "verdict": "not", "why": "invented"}]})
    out = verify.run(conn, ready["mid"])
    assert [dict(m) for m in claims(conn, ready)] == before and out["set_aside"] == []


# ---- where it runs, and what it protects -----------------------------------------------------

def test_the_summary_is_written_over_the_claims_that_survived_the_check(ready, conn, quote,
                                                                        monkeypatch):
    """A summary written over a claim the passage does not carry introduces that claim by name,
    and the claim is gone by the time anyone reads the summary."""
    from app import llm
    seen: dict[str, str] = {}

    def fake(system, user, *, label="", timeout=None):
        seen[label] = user
        if label == "thread":
            return {"moments": _moments(quote, ready["mid"], 5)}
        if label == "verify":
            gone = [m for m in claims(conn, ready) if m["claim"] == "claim 0"][0]
            return {"verdicts": [{"id": gone["id"], "verdict": "not", "why": "not said here"}]}
        return {"summary": "s", "questions": "", "people": []}

    monkeypatch.setattr(llm, "chat_json", fake)
    out = synth.doc(conn, ready["mid"])

    assert "claim 0" not in seen["doc"], "the summary was shown a claim that had been set aside"
    assert "claim 1" in seen["doc"]
    assert [m["claim"] for m in claims(conn, ready)] == ["claim %d" % i for i in range(1, 5)]
    assert any("claim 0" in d for d in out["dropped"])
    assert [t["theme_id"] for t in out["threads"]] == [ready["tid"]]
    assert len(out["threads"][0]["moments"]) == 4, "what it hands back survived the check too"


def test_a_full_reading_checks_after_every_line_and_before_the_summary(ready, conn, project,
                                                                       model, quote):
    store.save_theme(conn, project, tid=None, name="Leaving", gist="the crossing", code_ids=[])
    model.queue({"moments": _moments(quote, ready["mid"], 5)},
                {"moments": _moments(quote, ready["mid"], 4, at=140)},
                {"verdicts": []},
                {"summary": "s", "questions": "", "people": []})
    synth.doc(conn, ready["mid"])
    assert [c["label"] for c in model.calls] == ["thread", "thread", "verify", "doc"]


def test_the_check_is_shown_the_claim_its_quote_and_the_passage_around_it(ready, conn, model,
                                                                          quote):
    run_doc(model, conn, ready, quote)
    kept = claims(conn, ready)
    shown = model.shown("verify")
    sents = store.sentences(conn, ready["mid"])
    where = {sid: i for i, (sid, _) in enumerate(sents)}
    for m in kept:
        assert f'[{m["id"]}] {m["claim"]}' in shown
        assert m["anchor"] in shown
        i = where[m["sid"]]
        assert sents[i - 1][1] in shown and sents[i + 1][1] in shown, "the neighbours too"
    assert f"{len(kept)} CLAIMS TO CHECK" in shown
    assert "kind: interview" in shown, "the frame"


def test_the_claims_are_checked_in_batches_the_model_can_hold(ready, conn, model, quote,
                                                              monkeypatch):
    """Sixty claims with three sentences of passage each is a prompt a model can hold in one
    judgement; a whole corpus in one call is not."""
    run_doc(model, conn, ready, quote)
    monkeypatch.setattr(verify, "BATCH", 2)
    model.queue({"verdicts": []}, {"verdicts": []}, {"verdicts": []})
    verify.run(conn, ready["mid"])

    users = [c["user"] for c in model.calls if c["label"] == "verify"][-3:]
    assert [u.count("quoted:") for u in users] == [2, 2, 1], "five claims, batched at two"
    assert "2 CLAIMS TO CHECK" in users[0] and "1 CLAIMS TO CHECK" in users[2]


def test_a_one_line_rerun_checks_that_line_only(ready, conn, project, model, quote):
    other = store.save_theme(conn, project, tid=None, name="Leaving", gist="the crossing",
                             code_ids=[])
    model.queue({"moments": _moments(quote, ready["mid"], 5)},
                {"moments": _moments(quote, ready["mid"], 4, at=140)},
                {"verdicts": []},
                {"summary": "s", "questions": "", "people": []})
    synth.doc(conn, ready["mid"])
    theirs = [m["id"] for m in store.thread(conn, ready["mid"], other)]

    model.queue({"moments": _moments(quote, ready["mid"], 5, at=60)}, {"verdicts": []})
    synth.doc(conn, ready["mid"], only_theme=ready["tid"])
    shown = [c["user"] for c in model.calls if c["label"] == "verify"][-1]
    assert not any(i in shown for i in theirs), "the other line was not read again"


# ---- what a researcher sees ------------------------------------------------------------------

def test_the_mark_is_shown_where_the_claim_is_read(ready, conn, model, quote, client):
    run_doc(model, conn, ready, quote)
    marked = claims(conn, ready)[0]
    model.queue({"verdicts": [{"id": marked["id"], "verdict": "partly",
                               "why": "the passage does not say it was steady"}]})
    verify.run(conn, ready["mid"])

    page = client.get(f'/p/{ready["pid"]}/m/{ready["mid"]}?theme={ready["tid"]}').text
    record = client.get(f'/p/{ready["pid"]}/record').text
    for html in (page, record):
        assert ("The passage carries part of this: the passage does not say it was steady"
                in html)


def test_the_derivation_says_how_many_claims_were_set_aside(ready, conn, model, quote):
    run_doc(model, conn, ready, quote)
    assert "set aside" not in context.derivation(conn, ready["mid"])

    doomed = claims(conn, ready)[0]
    model.queue({"verdicts": [{"id": doomed["id"], "verdict": "not", "why": "not said here"}]})
    verify.run(conn, ready["mid"])
    said = context.derivation(conn, ready["mid"])
    assert said.endswith(", 1 set aside as not carried by their passages")
    assert "claims rest on" in said
    assert not [w for w in context._BANNED if w in said.lower()]


def test_a_mark_is_lifted_when_a_later_check_reads_the_claim_as_supported(ready, conn, model,
                                                                          quote):
    """A page that keeps warning about words no longer in question teaches a researcher to
    ignore the warning."""
    run_doc(model, conn, ready, quote)
    marked = claims(conn, ready)[0]
    model.queue({"verdicts": [{"id": marked["id"], "verdict": "partly", "why": "'steady' added"}]})
    verify.run(conn, ready["mid"])
    assert store.moment(conn, marked["id"])["support"] == "partly"

    model.queue({"verdicts": [{"id": marked["id"], "verdict": "supported", "why": ""}]})
    verify.run(conn, ready["mid"])
    row = store.moment(conn, marked["id"])
    assert (row["support"], row["support_note"], row["status"]) == ("", "", "live")


def test_a_database_made_before_the_check_gains_the_two_columns(tmp_path):
    """`moment` exists in every deployment already and CREATE TABLE IF NOT EXISTS leaves it
    alone, so the columns have to be added explicitly, and an old claim reads as unchecked."""
    import sqlite3

    from app import db
    path = tmp_path / "old.db"
    old = sqlite3.connect(path)
    old.execute("CREATE TABLE moment (id TEXT PRIMARY KEY, material_id TEXT NOT NULL, "
                "theme_id TEXT NOT NULL, sid TEXT NOT NULL, position INTEGER NOT NULL, "
                "claim TEXT NOT NULL, anchor TEXT NOT NULL, run_id TEXT, "
                "status TEXT NOT NULL DEFAULT 'live')")
    old.execute("INSERT INTO moment VALUES ('mo1','m1','t1','S001',0,'c','a',NULL,'live')")
    old.commit()
    old.close()

    conn = db.connect(path)
    try:
        assert {"support", "support_note"} <= {r[1] for r in
                                               conn.execute("PRAGMA table_info(moment)")}
        row = conn.execute("SELECT support, support_note FROM moment WHERE id='mo1'").fetchone()
        assert tuple(row) == ("", "")
        assert conn.execute("PRAGMA user_version").fetchone()[0] == db.SCHEMA_VERSION == 11
    finally:
        conn.close()
