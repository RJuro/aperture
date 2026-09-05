"""P25 — what the account is written from. `app/engine/account.py`, `app/prompts/account.md`.

An external audit ran ACCOUNT against its own claims and found four of them false. A comment on a
theme was marked honoured by a run that had no slot to put it in. A cached account was reused
after a material had been added, the focus rewritten, or a claim marked half-supported, none of
which the fingerprint could see. A material nobody had ever read for the theme was described to
the model as looked for and found wanting. And the prompt said it saw every claim while showing a
sample of them — up to 150 carrying materials, and dividing by zero past that.

These are those four, turned the right way round: each one asserts what the level is supposed to
do. The audit's own probes assert the defects and should fail against this file's behaviour.
"""
from __future__ import annotations

import pytest

from app import jobs, rerun, store

account = pytest.importorskip("app.engine.account")

SAID = "Say what this theme costs the people in it, not only what it gathers."


@pytest.fixture
def corpus(conn, analysed):
    """`analysed` — two materials, two themes, three claims each — plus one material the reading
    has never been through, which is the only kind of absence that has no history at all."""
    quiet = store.add_material(conn, analysed["pid"], "EI-900 Vaughn", "A short field note.\n")
    store.save_frame(conn, quiet, kind="fieldnotes", display="plain", title="Vaughn, field notes",
                     speakers=[], segments=[])
    return {**analysed, "quiet": quiet, "tid": analysed["themes"]["Work and trade"],
            "other": analysed["themes"]["Leaving and arriving"]}


def comment(conn, pid, tid, text=SAID) -> str:
    return store.add_feedback(conn, pid, "theme", tid, "note", text)


def account_step(conn, pid, fid) -> list[str]:
    """The account the comment plans, and only that: the corpus summary after it is the next
    step's business and has its own tests."""
    return jobs.run_now(conn, pid, rerun.plan(conn, fid)[:1])


def still_open(conn, fid) -> bool:
    return rerun.feedback(conn, fid)["consumed_by_run"] is None


# ---- what the researcher said reaches the run their words planned -------------------------------

def test_a_comment_on_a_theme_is_in_the_prompt_of_the_account_it_plans(conn, corpus, model):
    """The comment planned an account rewrite, the rewrite had no feedback slot, and a successful
    run marked the comment honoured — money spent to leave the impression that an instruction had
    been considered."""
    fid = comment(conn, corpus["pid"], corpus["tid"])
    model.queue({"account": "Written again, with the cost of it named."})
    account_step(conn, corpus["pid"], fid)

    shown = model.shown("account")
    assert SAID in shown, "the researcher's words, verbatim, in the prompt they planned"
    assert "WHAT THE RESEARCHER SAID ABOUT THIS THEME" in shown
    assert not still_open(conn, fid), "an account written with it in front of the model answers it"


def test_a_theme_nobody_has_commented_on_says_so_rather_than_nothing(conn, corpus, model):
    model.queue({"account": "The first pass."})
    account.run(conn, corpus["pid"], corpus["tid"])
    assert "The researcher has said nothing about this theme." in model.shown("account")


def test_a_comment_on_another_theme_stays_where_it_was_made(conn, corpus, model):
    fid = comment(conn, corpus["pid"], corpus["other"])
    model.queue({"account": "The first pass."})
    account.run(conn, corpus["pid"], corpus["tid"])
    assert SAID not in model.shown("account")
    assert still_open(conn, fid), "no run of another theme's account answers it"


# ---- honoured by a result, not by a step ------------------------------------------------------

def test_a_failed_account_leaves_the_comment_open_and_the_next_one_is_shown_it(conn, corpus,
                                                                               model):
    """Consumed on the way past, a comment is lost by every failure between the researcher and
    the model: the run row says it failed, the comment says it was answered."""
    pid, fid = corpus["pid"], comment(conn, corpus["pid"], corpus["tid"])
    account_step(conn, pid, fid)                    # nothing queued: the call itself fails
    assert SAID in model.shown("account"), "it failed at the call, not before the prompt"
    assert still_open(conn, fid)

    model.queue({"account": "Written again, with the cost of it named."})
    account_step(conn, pid, fid)
    assert not still_open(conn, fid)


def test_an_account_that_comes_back_empty_answers_nothing(conn, corpus, model):
    pid, fid = corpus["pid"], comment(conn, corpus["pid"], corpus["tid"])
    model.queue({"account": ""})
    account_step(conn, pid, fid)
    assert store.get_summary(conn, "theme", corpus["tid"], "reading") is None
    assert still_open(conn, fid), "nothing was stored, so nothing answered the researcher"


def test_a_theme_left_as_it_stood_is_written_again_when_a_comment_is_waiting(conn, corpus, model):
    """The chain's accounts step skips a theme whose evidence has not moved. The researcher's
    words are not in that evidence, so the skip would answer the comment with silence."""
    pid = corpus["pid"]
    model.queue({"account": "The first pass."}, {"account": "The first pass."})
    jobs.run_now(conn, pid, [{"kind": "accounts"}])
    assert len(model.calls) == 2

    jobs.run_now(conn, pid, [{"kind": "accounts"}])
    assert model.calls[2:] == [], "nothing moved and nobody said anything: nothing to pay for"

    fid = comment(conn, pid, corpus["tid"])
    model.queue({"account": "Written again, with the cost of it named."})
    jobs.run_now(conn, pid, [{"kind": "accounts"}])
    assert len(model.calls) == 3 and SAID in model.calls[-1]["user"]
    assert not still_open(conn, fid)


# ---- the fingerprint covers what the prompt is built from ---------------------------------------

def test_a_material_added_to_the_project_moves_the_fingerprint(conn, corpus):
    """It is named in the absence block, so an account written before it arrived is an account
    that has not been asked about it."""
    was = account.fingerprint(conn, corpus["pid"], corpus["tid"])
    store.add_material(conn, corpus["pid"], "EI-901 Nowak", "One more interview.\n")
    assert account.fingerprint(conn, corpus["pid"], corpus["tid"]) != was


def test_a_new_focus_moves_the_fingerprint(conn, corpus):
    was = account.fingerprint(conn, corpus["pid"], corpus["tid"])
    store.set_focus(conn, corpus["pid"], "What the work costs, rather than what it pays")
    assert account.fingerprint(conn, corpus["pid"], corpus["tid"]) != was


def test_a_claim_marked_half_supported_moves_the_fingerprint(conn, corpus):
    """`partly` leaves the claim live and its id unchanged, so the ids alone cannot see it — and
    what the account may rest on that claim has changed."""
    was = account.fingerprint(conn, corpus["pid"], corpus["tid"])
    claim = store.thread(conn, corpus["grande"], corpus["tid"])[0]
    store.mark_support(conn, [(claim["id"], "partly", "the quote is about one year only")])
    assert account.fingerprint(conn, corpus["pid"], corpus["tid"]) != was


# ---- a budget over the whole context ------------------------------------------------------------

def test_more_carrying_materials_than_the_budget_is_a_thin_prompt_not_a_crash():
    """151 materials each carrying one claim. Past the budget a material gets no example, and it
    is still named and counted: this level exists to say where a theme runs, and a material it
    cannot afford an example from is not a material it may leave out."""
    carrying = [{"material_id": str(i), "title": f"Material {i}", "name": str(i),
                 "kind": "interview", "claims": 1} for i in range(151)]
    rows = [{"material_id": str(i), "id": f"mo{i}", "claim": "c", "anchor": "a"}
            for i in range(151)]
    text, held_back = account._blocks(rows, carrying)

    assert text.count("[mo") == account.CLAIMS_SHOWN, "the budget is a hard cap, not a division"
    assert held_back == 151 - account.CLAIMS_SHOWN
    assert "Material 150 — interview — 0 of 1 claims shown" in text, "named, counted, unshown"


def test_the_shared_passages_are_bounded_too(conn, corpus, model):
    """The claim budget bounded the blocks and nothing else, so on a corpus where every passage
    is read twice the prompt grew with the corpus underneath it."""
    pid, mid = corpus["pid"], corpus["grande"]
    many = [{"claim": f"claim {i}", "anchor": f"anchor {i}", "sid": f"S{i:03d}"}
            for i in range(account.SHARED_SHOWN + 5)]
    store.save_moments(conn, mid, corpus["tid"], many)
    store.save_moments(conn, mid, corpus["other"], many)

    block = account._shared_block(conn, pid, corpus["tid"])
    assert len(block.splitlines()) == account.SHARED_SHOWN + 1
    assert block.splitlines()[-1].startswith("… and 5 more")


# ---- a material nobody has read for this theme --------------------------------------------------

def test_a_material_never_read_for_this_theme_is_not_reported_as_an_absence(conn, corpus, model):
    """The strongest of the three statements used to be made from the weakest of the three
    histories: no row at all read as looked for and found wanting."""
    model.queue({"account": "The first pass."})
    account.run(conn, corpus["pid"], corpus["tid"])
    absent = model.shown("account").rsplit("WHERE THIS THEME DOES NOT APPEAR", 1)[1]

    assert "Vaughn, field notes — fieldnotes — NOT ASSESSED — this material has not been read " \
           "for this theme yet (no reading exists)" in absent
    assert "LOOKED FOR AND TOO THIN" not in absent


def test_the_three_kinds_of_nothing_stay_apart(conn, corpus):
    """Each of the three says a different thing about the reading, and rule 5 of the prompt only
    works if the block under it keeps them apart."""
    quiet = [m for m in account.coverage(conn, corpus["pid"], corpus["tid"])["per_material"]
             if not m["claims"]]
    assert "NOT ASSESSED" in account._absent_block(conn, corpus["pid"], corpus["tid"], quiet)

    store.save_follow(conn, corpus["quiet"], corpus["tid"], "thin")
    assert "LOOKED FOR AND TOO THIN" in account._absent_block(conn, corpus["pid"],
                                                              corpus["tid"], quiet)
    store.save_follow(conn, corpus["quiet"], corpus["tid"], "skipped")
    assert "NOT LOOKED FOR HERE" in account._absent_block(conn, corpus["pid"],
                                                          corpus["tid"], quiet)


def test_the_prompt_no_longer_claims_to_see_every_claim(conn, corpus, model):
    """A model told it sees everything weighs a sample as if it were everything."""
    model.queue({"account": "The first pass."})
    account.run(conn, corpus["pid"], corpus["tid"])
    shown = model.shown("account")
    assert "You see every claim" not in shown
    assert "examples selected" in shown
    assert "NOT ASSESSED means this material has never been read for this theme at all" in shown
