"""The evaluation loop: the runner that produces a record, and the bookkeeping over one.

Nothing here judges a reading — that is `scripts/eval_rubric.md` and two blind readers. These
tests only pin the counting, and the one thing the runner must get right: that the chain it runs
is the chain the application runs, so v2 is comparable with v1.

No model is called. The runner is exercised with every engine step stubbed, exactly as
`test_p4_unit.py` exercises `jobs.py` — this file is about the harness, not about what it runs.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import eval_metrics  # noqa: E402
import eval_run  # noqa: E402

from app import context, jobs, pages, store  # noqa: E402


# ---- counting a reading -------------------------------------------------------------------------

def test_the_counts_over_a_finished_reading(conn, analysed):
    m = eval_metrics.from_db(conn, analysed["pid"])
    assert m["materials"] == 2
    assert m["themes_live"] == 2
    assert m["themes_per_material"] == 1.0
    assert m["claims_total"] == 12, "two themes × two materials × three claims"
    assert m["claims_per_theme"] == {"Work and trade": 6, "Leaving and arriving": 6}
    assert m["materials_per_theme"] == {"Work and trade": 2, "Leaving and arriving": 2}
    assert m["themes_in_one_material"] == 0 and m["themes_in_two_or_more"] == 2
    assert 0 < m["cited_passages"] <= m["total_passages"]
    assert m["cited_share"] == round(m["cited_passages"] / m["total_passages"], 3)


def test_a_passage_two_themes_both_cite_is_reported_as_shared(conn, analysed, quote):
    """Recycling, as a count: the same words carrying a claim under one theme and another."""
    before = eval_metrics.from_db(conn, analysed["pid"])["shared_passage_share"]
    assert before == 0.0
    work, leaving = analysed["themes"]["Work and trade"], analysed["themes"]["Leaving and arriving"]
    shared = store.thread(conn, analysed["grande"], work)[0]
    store.save_moments(conn, analysed["grande"], leaving,
                       [{"claim": "the same words, read again", "anchor": shared["anchor"],
                         "sid": shared["sid"]}])
    m = eval_metrics.from_db(conn, analysed["pid"])
    assert m["passages_per_theme"] == {"Work and trade": 6, "Leaving and arriving": 4}
    assert m["shared_passage_share_per_theme"] == {"Work and trade": round(1 / 6, 3),
                                                   "Leaving and arriving": 0.25}
    assert m["shared_passage_share"] == round(1 / 9, 3), "one of nine passages carries two themes"


def test_totalising_words_doubled_ids_and_stray_script_are_counted(conn, analysed):
    pid = analysed["pid"]
    store.save_summary(conn, "project", pid, "reading",
                       "All three, every one, with no exceptions [S001, S004, S001] 数据.")
    m = eval_metrics.from_db(conn, pid)
    assert m["hedge_words"]["all"] == 1 and m["hedge_words"]["every"] == 1
    assert m["hedge_words"]["no exceptions"] == 1
    assert m["hedge_words"]["consistently"] == 0
    assert m["doubled_ids"] == ["[S001, S004, S001]"]
    assert m["non_latin"] == {"checked": True, "chars": 2, "characters": ["据", "数"]}


def test_stray_script_is_not_reported_when_the_material_is_not_latin(conn, project):
    store.add_material(conn, project, "北京", "数据数据数据数据数据数据数据数据数据数据")
    store.save_summary(conn, "project", project, "reading", "数据")
    assert eval_metrics.from_db(conn, project)["non_latin"]["checked"] is False


def test_what_a_verify_step_set_aside_is_zero_when_it_ran_and_kept_everything(conn, analysed):
    """The column exists (schema 11), so the count is measured: nothing set aside reads as 0, and
    the run notes are counted from their own source."""
    pid = analysed["pid"]
    rid = store.start_run(conn, pid, "doc", analysed["grande"], "x")
    store.finish_run(conn, rid, notes=['the quote does not carry it: "we sailed in March"',
                                       "1 quote(s) ran past the 12-word cap and were kept"])
    aside = eval_metrics.from_db(conn, pid)["set_aside"]
    assert aside["verify_superseded_claims"] == 0
    assert aside["runs_saying_does_not_carry_it"] == 1
    assert aside["notes_total"] == 2


def test_a_claim_the_verify_step_set_aside_is_counted(conn, analysed):
    live = store.moments(conn, analysed["grande"])[0]
    conn.execute("UPDATE moment SET status='superseded', support_note='the quote does not carry "
                 "it' WHERE id=?", (live["id"],))
    conn.commit()
    assert eval_metrics.from_db(conn, analysed["pid"])["set_aside"]["verify_superseded_claims"] == 1


def test_the_calls_under_the_steps_are_totalled(conn, analysed):
    """A step is a dozen calls, and only the call rows carry cached and reasoning tokens, seconds
    and retries. A counter no provider reported stays null — never a nought."""
    pid = analysed["pid"]
    rid = store.start_run(conn, pid, "doc", analysed["grande"], "x")
    store.save_call(conn, rid, "thread", 1, "mistral", "glm", "medium",
                    {"tokens_in": 1000, "tokens_out": 400, "tokens_cached": 250,
                     "tokens_reasoning": 320}, "2026-09-05T10:00:00", 12.5, "ok")
    store.save_call(conn, rid, "thread", 2, "mistral", "glm", "medium",
                    {"tokens_in": 1000, "tokens_out": 100}, "2026-09-05T10:01:00", 7.5, "ok")
    other = store.start_run(conn, pid, "read", analysed["rodwin"], "x")
    store.save_call(conn, other, "read", 1, "mistral", "glm", "", {"tokens_in": 500},
                    "2026-09-05T10:02:00", 5.0, "ok")

    c = eval_metrics.from_db(conn, pid)["calls"]
    assert c["calls"] == 3
    assert c["attempts"] == 4, "1 + 2 + 1 — the gap from 3 is the answer that would not parse"
    assert c["tokens_in"] == 2500 and c["tokens_out"] == 500
    assert c["tokens_cached"] == 250 and c["tokens_reasoning"] == 320
    assert c["reasoning_share"] == 0.64 and c["cached_share"] == 0.1
    assert c["seconds_total"] == 25.0
    assert c["per_kind"]["doc"]["calls"] == 2 and c["per_kind"]["read"]["calls"] == 1
    assert c["per_kind"]["read"]["tokens_out"] is None, "the provider reported no output tokens"


def test_a_provider_that_reports_no_cache_is_not_reported_as_caching_nothing(conn, analysed):
    rid = store.start_run(conn, analysed["pid"], "read", None, "x")
    store.save_call(conn, rid, "read", 1, "minimax", "M3", "", {"tokens_in": 10, "tokens_out": 5},
                    "2026-09-05T10:00:00", 1.0, "ok")
    c = eval_metrics.from_db(conn, analysed["pid"])["calls"]
    assert c["tokens_cached"] is None and c["cached_share"] is None


def test_every_theme_by_material_pair_is_one_of_five_things(conn, analysed):
    """Two themes over two materials is four cells. A cell with no follow row was never assessed,
    which is the distinction `store.followed` exists to keep — not a zero."""
    pid, work = analysed["pid"], analysed["themes"]["Work and trade"]
    leaving = analysed["themes"]["Leaving and arriving"]
    assert eval_metrics.from_db(conn, pid)["cells"] == {
        "line": 0, "thin": 0, "skipped": 0, "residual": 0, "not_assessed": 4}
    store.save_follow(conn, analysed["grande"], work, "line")
    store.save_follow(conn, analysed["rodwin"], work, "thin")
    store.save_follow(conn, analysed["grande"], leaving, "skipped")
    assert eval_metrics.from_db(conn, pid)["cells"] == {
        "line": 1, "thin": 1, "skipped": 1, "residual": 0, "not_assessed": 1}
    # `residual` is a key here and 0 for now: the follow table's CHECK constraint still refuses
    # the word, and R4's omission pass is what widens it. The counter is ready for the day it does.


def test_short_lines_uncoded_passages_and_the_holds_are_counted(conn, analysed, quote):
    """Three counts a record cannot give back: lines under the four-claim floor, how much of each
    material no code marked, and where the themes stand in the lifecycle."""
    pid = analysed["pid"]
    assert eval_metrics.from_db(conn, pid)["sparse_lines"] == 4, "four lines of three claims"
    third = store.save_theme(conn, pid, tid=None, name="A candidate", gist="one life", code_ids=[])
    store.set_hold(conn, third, "candidate")
    sid, text = quote(analysed["grande"], at=200)
    store.save_moments(conn, analysed["grande"], third,
                       [{"claim": "one claim only", "anchor": " ".join(text.split()[:8]),
                         "sid": sid}])
    m = eval_metrics.from_db(conn, pid)
    assert m["sparse_lines"] == 5, "and the new line of one"
    assert m["candidates"] == 1 and m["proposed"] == 0 and m["frozen"] == 0
    # Nothing was coded, so every passage in both materials is unmarked.
    assert set(m["unmarked_share"].values()) == {1.0}
    store.save_codes(conn, pid, analysed["grande"],
                     [{"name": "work", "definition": "a living", "sids": [sid]}])
    assert eval_metrics.from_db(conn, pid)["unmarked_share"]["DP-40 Grande"] < 1.0


def test_tokens_come_back_per_step(conn, analysed):
    pid = analysed["pid"]
    for kind, ti, to in (("read", 100, 20), ("read", 300, 40), ("themes", 50, 10)):
        rid = store.start_run(conn, pid, kind, None, "x")
        store.finish_run(conn, rid, tokens_in=ti, tokens_out=to)
    steps = eval_metrics.from_db(conn, pid)["tokens_per_step"]
    assert steps["read"] == {"runs": 2, "in": 400, "out": 60}
    assert steps["themes"] == {"runs": 1, "in": 50, "out": 10}


# ---- the same counts off a record, where the database is gone ------------------------------------

def test_a_record_gives_back_the_counts_the_database_gave(conn, analysed, tmp_path):
    """v1 of the Ellis Island record exists as a markdown file and nothing else. The .md path is
    the poorer of the two — a record does not say how many passages were never cited — but what
    it does carry has to agree."""
    pid = analysed["pid"]
    store.save_summary(conn, "theme", analysed["themes"]["Work and trade"], "reading",
                       "Every material carries this, across the corpus, with no exceptions.")
    record = tmp_path / "record.md"
    record.write_text(pages._render("export.md", context.export(conn, pid)), encoding="utf-8")

    a, b = eval_metrics.from_db(conn, pid), eval_metrics.from_record(record)
    for key in ("materials", "themes_live", "themes_per_material", "claims_total",
                "claims_per_theme", "materials_per_theme", "passages_per_theme",
                "themes_in_one_material", "themes_in_two_or_more", "cited_passages"):
        assert a[key] == b[key], key
    assert b["hedge_words"]["every"] and b["hedge_words"]["no exceptions"]
    assert b["total_passages"] is None, "a record does not say what was never cited"


_BEFORE_THE_FLIP = """# A reading

## Themes

### Across materials

#### Work and trade

how a living is made

in 2 of 2 materials · 4 claims on 4 passages

Every material carries this, across the corpus.

##### Materials where this theme appears

**Grande, M.** — interview · 2 claims

1. He worked the boats
   > we worked the boats in March  [S010]
2. And was paid by the day
   > paid by the day, never the week  [S011]

**Rodwin** — interview · 2 claims

1. The trade was learned at home
   > my father taught me the trade  [S020]
2. And kept after the crossing
   > I kept at it here too  [S021]

##### Materials where this theme does not appear

Every material contains claims for this theme.

## Materials

### Grande, M.

interview · claims rest on 2 of 400 passages

#### Before reading

An oral-history interview about migration.

#### Work and trade

2 claims

Printed in full under [Work and trade](#work-and-trade) above.

### Rodwin

interview · claims rest on 2 of 500 passages

#### Work and trade

2 claims

Printed in full under [Work and trade](#work-and-trade) above.

## Excluded from the analysis

Nothing was excluded from the analysis.
"""


def test_a_record_written_before_the_claims_moved_under_their_material_still_counts(tmp_path):
    """v1 of the Ellis Island record printed every claim under its theme, and the material
    sections only pointed back at it. It exists as a markdown file and nothing else, and every
    later version is compared against it, so that shape has to keep counting the same."""
    record = tmp_path / "v1.md"
    record.write_text(_BEFORE_THE_FLIP, encoding="utf-8")
    m = eval_metrics.from_record(record)
    assert m["materials"] == 2 and m["themes_live"] == 1
    assert m["claims_per_theme"] == {"Work and trade": 4}
    assert m["materials_per_theme"] == {"Work and trade": 2}
    assert m["passages_per_theme"] == {"Work and trade": 4}
    assert m["themes_in_two_or_more"] == 1 and m["themes_in_one_material"] == 0
    assert m["hedge_words"]["every"] == 1 and m["hedge_words"]["across the corpus"] == 1


def test_two_readings_side_by_side(tmp_path):
    a = {"themes_live": 12, "hedge_words": {"all": 9}, "doubled_ids": ["[S1, S1]"]}
    b = {"themes_live": 7, "hedge_words": {"all": 2}, "doubled_ids": []}
    table = eval_metrics.compare(a, b)
    assert "themes_live" in table and "12" in table and "7" in table
    assert "hedge_words.all" in table
    for p, d in ((tmp_path / "a.json", a), (tmp_path / "b.json", b)):
        p.write_text(json.dumps(d))
    assert eval_metrics.main(["--compare", str(tmp_path / "a.json"), str(tmp_path / "b.json")]) == 0


def test_a_database_and_a_record_line_up_across_the_new_counts_too(conn, analysed, tmp_path):
    """Two conditions are compared through this table, and one of the four may only ever exist as
    a record. What only the database knows prints as '—' on that side, never as a nought."""
    store.save_follow(conn, analysed["grande"], analysed["themes"]["Work and trade"], "line")
    record = tmp_path / "record.md"
    record.write_text(pages._render("export.md", context.export(conn, analysed["pid"])),
                      encoding="utf-8")
    table = eval_metrics.compare(eval_metrics.from_db(conn, analysed["pid"]),
                                 eval_metrics.from_record(record))
    row = next(ln for ln in table.splitlines() if ln.startswith("cells.line"))
    assert row.split() == ["cells.line", "1", "—"]
    for key in ("calls.calls", "calls.reasoning_share", "cells.not_assessed", "sparse_lines",
                "candidates", "proposed", "frozen"):
        assert any(ln.startswith(key + " ") for ln in table.splitlines()), key


# ---- the runner ----------------------------------------------------------------------------------

@pytest.fixture
def corpus(tmp_path):
    """Two tiny materials on disk, and a .DS_Store to be ignored."""
    d = tmp_path / "materials"
    d.mkdir()
    (d / "one.txt").write_text("A: We left in March. It was cold.\nB: And after that?\n")
    (d / "two.md").write_text("A: The work was steady. Nobody complained.\n")
    (d / ".hidden.txt").write_text("not material")
    (d / "notes.rtf").write_text("not a kind this reads")
    return d


def the_applications_chain(pid, mids) -> list[str]:
    """The step kinds `jobs.ingest_chain` queues, taken from that function by standing in for
    `jobs.start` — the application's own planner, called directly.

    The expectation is computed and not written down: the chain differs by the project's `method`
    and grows as the workflow does, and a list copied into a test only ever pins the day it was
    copied. What is being asserted is that the runner runs *that* plan, not a particular plan.
    """
    queued: list[dict] = []
    real = jobs.start
    jobs.start = lambda conn_factory, project, runs: queued.extend(runs)
    try:
        jobs.ingest_chain(pid, mids)
    finally:
        jobs.start = real
    return [r["kind"] for r in queued]


def test_the_runner_runs_exactly_the_chain_the_application_runs(corpus, tmp_path, monkeypatch,
                                                                capsys):
    from app import db

    ran = []
    for kind, (line, _) in list(jobs.STEPS.items()):
        monkeypatch.setitem(jobs.STEPS, kind, (line, lambda c, p, r, _k=kind: ran.append(_k)))
    out = tmp_path / "v2" / "record.md"
    assert eval_run.main(["--materials", str(corpus), "--focus", "why people left",
                          "--data", str(tmp_path / "v2data"), "--out", str(out)]) == 0

    printed = capsys.readouterr().out
    conn = db.connect(tmp_path / "v2data" / "aperture.db")
    pid = conn.execute("SELECT id FROM project").fetchone()[0]
    mids = [r[0] for r in conn.execute("SELECT id FROM material ORDER BY created_at")]
    plan = the_applications_chain(pid, mids)
    assert f"{len(plan)} steps: {' → '.join(plan)}" in printed, \
        "the same chain as jobs.ingest_chain, planned in the same order"
    # What it RUNS is that plan in stages: the materials side by side, THEMES one at a time, the
    # corpus level last (`jobs._stages`). So the order is a multiset, with two things fixed —
    # every material is read before anything moves the theme set, and the tail is last.
    assert sorted(ran) == sorted(plan)
    assert ran[-2:] == plan[-2:] == ["accounts", "project"]
    assert ran.index("themes") > max(i for i, k in enumerate(ran) if k == "read")
    assert out.exists() and out.with_suffix(".metrics.json").exists()
    metrics = json.loads(out.with_suffix(".metrics.json").read_text())
    assert metrics["materials"] == 2, "the .rtf and the dotfile were not material"
    assert metrics["source"] == "db"
    assert "Reading one.txt" in printed and "Finding themes" in printed
    assert "0 in / 0 out" in printed, "every step prints what it spent"


def test_the_runner_leaves_the_store_as_it_found_it(corpus, tmp_path, monkeypatch):
    """The trace prints by standing in front of two store functions; it puts them back."""
    before = (store.start_run, store.finish_run)
    for kind, (line, _) in list(jobs.STEPS.items()):
        monkeypatch.setitem(jobs.STEPS, kind, (line, lambda c, p, r: None))
    eval_run.main(["--materials", str(corpus), "--data", str(tmp_path / "d"),
                   "--out", str(tmp_path / "r.md")])
    assert (store.start_run, store.finish_run) == before


def test_the_runner_refuses_a_data_directory_that_already_holds_a_reading(corpus, tmp_path):
    data = tmp_path / "used"
    data.mkdir()
    (data / "aperture.db").write_text("")
    with pytest.raises(SystemExit, match="already exists"):
        eval_run.main(["--materials", str(corpus), "--data", str(data),
                       "--out", str(tmp_path / "r.md")])


def test_the_runner_says_so_when_there_is_nothing_to_read(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(SystemExit, match="no .*files"):
        eval_run.main(["--materials", str(empty), "--data", str(tmp_path / "d"),
                       "--out", str(tmp_path / "r.md")])
