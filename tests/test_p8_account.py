"""P8 — the theme account. `app/engine/account.py`, `app/prompts/account.md`.

    account.run(conn, pid, theme_id)     -> {"text","gist","dropped","coverage"}
    account.coverage(conn, pid, theme_id) -> {"materials_with","materials_total","claims",
                                              "per_material"}

The layer that gathers one theme's claims ACROSS materials. Everything below the reading is
per-material; everything above it, until now, had to read every claim there was. These tests are
the two laws it inherits from `synth.project` — no quotes of its own, and a citation to nothing is
removed and said so — plus the one thing only this level can see: where the theme is not.
"""
from __future__ import annotations

import pytest

from app import db, store

account = pytest.importorskip("app.engine.account")

DESIGN_WORDS = ("moment", "thread", "anchor", "frame", "slot")

# A claim and a quote at the length the reading actually produces them, for measuring a prompt.
CLAIM = ("The stall and not the land is what fed them, and the farm is described throughout as a "
         "place that was left rather than lost, even where the leaving cost everything")
QUOTE = "we had a stall in the market before any of that"


@pytest.fixture
def corpus(conn, analysed):
    """`analysed` — two materials, two themes, three claims each — plus one material the reading
    made no claim in at all. Without that third material there is no absence to ask about."""
    quiet = store.add_material(conn, analysed["pid"], "EI-900 Vaughn", "A short field note.\n")
    store.save_frame(conn, quiet, kind="fieldnotes", display="plain", title="Vaughn, field notes",
                     speakers=[], segments=[])
    return {**analysed, "quiet": quiet,
            "tid": analysed["themes"]["Work and trade"],
            "other": analysed["themes"]["Leaving and arriving"]}


def ids(conn, mid, tid) -> list[str]:
    return [m["id"] for m in store.thread(conn, mid, tid)]


def test_a_cited_claim_that_does_not_exist_is_stripped_and_reported(conn, corpus, model):
    real = ids(conn, corpus["grande"], corpus["tid"])[0]
    model.queue({"account": f"It holds where trade is small [{real}], and elsewhere "
                            f"[mo-does-not-exist] it does not.", "gist": "a living, made small"})
    out = account.run(conn, corpus["pid"], corpus["tid"])

    assert real in out["text"], "a citation that resolves must survive"
    assert "mo-does-not-exist" not in out["text"]
    said = " ".join(out["dropped"])
    assert "mo-does-not-exist" in said, "a silent strip is how a reading loses support unnoticed"
    assert store.get_summary(conn, "theme", corpus["tid"], "reading")["text"] == out["text"]
    assert not [w for w in DESIGN_WORDS if w in said], "our vocabulary must not reach a researcher"


def test_a_claim_id_from_another_theme_is_rejected_too(conn, corpus, model):
    """Live, real, and citable one theme over — and still not evidence for this one."""
    mine = ids(conn, corpus["grande"], corpus["tid"])[0]
    theirs = ids(conn, corpus["grande"], corpus["other"])[0]
    model.queue({"account": f"Trade recurs [{mine}] and so does the crossing [{theirs}].",
                 "gist": "g"})
    out = account.run(conn, corpus["pid"], corpus["tid"])

    assert mine in out["text"] and theirs not in out["text"]
    assert theirs in " ".join(out["dropped"])


def test_a_superseded_claim_is_not_citable_either(conn, corpus, model, quote):
    """A rerun supersedes rather than deletes, so a stale id still resolves in the table."""
    stale = ids(conn, corpus["grande"], corpus["tid"])[0]
    sid, text = quote(corpus["grande"], at=140)
    store.save_moments(conn, corpus["grande"], corpus["tid"],
                       [{"claim": "rewritten", "anchor": " ".join(text.split()[:8]), "sid": sid}])
    assert store.moment(conn, stale)["status"] == "superseded"

    model.queue({"account": f"It rests here [{stale}].", "gist": "g"})
    out = account.run(conn, corpus["pid"], corpus["tid"])
    assert stale not in out["text"] and stale in " ".join(out["dropped"])


def test_the_account_is_stored_against_the_theme_and_the_gist_revised_without_emptying_it(
        conn, corpus, model):
    """`save_theme` also rewrites which codes a theme gathers; this level knows nothing about
    codes, so a gist written through it would empty the theme. Same trap as at project level."""
    cid = db.new_id("c")
    conn.execute("INSERT INTO code (id, project_id, name) VALUES (?,?,'Work')",
                 (cid, corpus["pid"]))
    store.save_theme(conn, corpus["pid"], tid=corpus["tid"], name="Work and trade",
                     gist="how a living is made", code_ids=[cid])

    model.queue({"account": "Small trades pay for everything here.",
                 "gist": "Small trades, not land, are what a living is made of in two of three."})
    out = account.run(conn, corpus["pid"], corpus["tid"])

    stored = store.get_summary(conn, "theme", corpus["tid"], "reading")
    assert stored["text"] == out["text"] == "Small trades pay for everything here."
    assert stored["stage"] == "reading" and stored["scope"] == "theme"
    row = conn.execute("SELECT * FROM theme WHERE id=?", (corpus["tid"],)).fetchone()
    assert row["gist"] == out["gist"] and row["gist"].startswith("Small trades")
    assert [c["id"] for c in store.theme_codes(conn, corpus["tid"])] == [cid]
    # The material's own summaries are a different scope and must be untouched by this.
    assert store.get_summary(conn, "material", corpus["grande"], "reading") is not None


def test_coverage_returns_parts_that_reconcile_with_the_database(conn, corpus):
    cov = account.coverage(conn, corpus["pid"], corpus["tid"])
    per = {r["material_id"]: r["claims"] for r in cov["per_material"]}

    assert cov["materials_total"] == len(store.materials(conn, corpus["pid"])) == 3
    assert cov["materials_with"] == 2
    assert per[corpus["quiet"]] == 0
    for mid in (corpus["grande"], corpus["rodwin"]):
        assert per[mid] == len(store.thread(conn, mid, corpus["tid"])) == 3
    assert cov["claims"] == sum(per.values()) == 6
    assert all("%" not in str(v) for v in cov.values()), "the parts, not a percentage"


def test_coverage_is_one_query_not_a_loop_over_materials(conn, corpus):
    seen = []
    conn.set_trace_callback(seen.append)
    try:
        account.coverage(conn, corpus["pid"], corpus["tid"])
    finally:
        conn.set_trace_callback(None)
    assert len(seen) == 1, f"coverage ran {len(seen)} statements: {seen}"


def test_the_materials_this_theme_is_missing_from_are_named_in_the_prompt(conn, corpus, model):
    """The absence is half the finding, and the model cannot ask about a name it was not given."""
    model.queue({"account": "It holds in the interviews.", "gist": "g"})
    account.run(conn, corpus["pid"], corpus["tid"])
    shown = model.shown("account")

    assert "EI-900 Vaughn" in shown or "Vaughn, field notes" in shown
    assert "Grande" in shown and "Rodwin" in shown
    assert "2 of the 3 materials" in shown, "the reach is a derivation, printed as its parts"
    # This theme's claims and no other's.
    for i in ids(conn, corpus["grande"], corpus["tid"]):
        assert i in shown
    for i in ids(conn, corpus["grande"], corpus["other"]):
        assert i not in shown


def test_the_prompt_states_its_caps_as_numbers(conn, corpus, model):
    model.queue({"account": "a", "gist": "g"})
    account.run(conn, corpus["pid"], corpus["tid"])
    shown = model.shown("account")
    for cap in ("250", "350", "40"):
        assert cap in shown, f"the cap {cap} is enforced in Python and must be stated as a number"
    assert "no quotes of your own" in shown.lower()


def test_a_theme_that_is_no_longer_live_is_not_written_about(conn, corpus, model):
    """The model fixture raises on an unexpected call, so this asserts no call was made."""
    store.merge_theme(conn, corpus["tid"], corpus["other"])
    out = account.run(conn, corpus["pid"], corpus["tid"])
    assert out["text"] == "" and out["dropped"]
    assert model.calls == []


def test_a_theme_nothing_rests_on_yet_costs_no_call(conn, corpus, model):
    tid = store.save_theme(conn, corpus["pid"], tid=None, name="Faith", gist="", code_ids=[])
    out = account.run(conn, corpus["pid"], tid)
    assert out["text"] == "" and out["dropped"] and model.calls == []
    assert out["coverage"]["materials_with"] == 0


def test_the_prompt_stays_flat_as_the_corpus_grows(conn, project, model):
    """Fifty materials, nine claims each: the whole reason this layer exists. The budget is spread
    over the materials that carry the theme, so what the model reads stops growing while the
    corpus does not — and every material is still named and counted."""
    tid = store.save_theme(conn, project, tid=None, name="Work", gist="a living", code_ids=[])
    for n in range(50):
        mid = store.add_material(conn, project, f"Material {n:02d}", "text")
        store.save_moments(conn, mid, tid, [{"claim": CLAIM, "anchor": QUOTE, "sid": f"S{i:03d}"}
                                            for i in range(9)])

    model.queue({"account": "x", "gist": "g"})
    out = account.run(conn, project, tid)
    call = model.calls[-1]
    size = len(call["system"]) + len(call["user"])

    assert out["coverage"]["claims"] == 450 and out["coverage"]["materials_with"] == 50
    assert call["user"].count("] ") <= account.CLAIMS_SHOWN, "the claim budget is a hard cap"
    assert size < 70_000, f"the prompt is {size} characters at 50 materials — not flat"
    assert "Material 49" in call["user"], "every material is named, whatever the budget"
    assert "3 of 9 claims shown" in call["user"], "a partial view says so, in its own numbers"
    assert str(450 - account.CLAIMS_SHOWN) in " ".join(out["dropped"])


def test_laying_out_no_materials_is_empty_rather_than_a_crash():
    """`run` guards this case before it gets here, but a helper that divides by the number of
    materials must not be one refactor away from a ZeroDivisionError."""
    assert account._blocks([], []) == ("", 0)
