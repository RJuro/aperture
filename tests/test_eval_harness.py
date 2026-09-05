"""The eval harness around a comparison of conditions: the runner's flags, and the blind dossiers.

The four conditions of the pass-6 comparison (docs/EVAL.md) are four invocations of
`scripts/eval_run.py`, and the verdict comes from readers who do not know which record is which.
This file pins the two things Python is responsible for there: that a condition is planned as
asked, and that the letters hide which condition a dossier came from while the key gets it back.

No model is called and nothing is judged. `--dry-run` is how a condition is checked before it is
paid for, so most of this file uses it.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import eval_dossiers  # noqa: E402
import eval_run  # noqa: E402


@pytest.fixture
def corpus(tmp_path):
    d = tmp_path / "materials"
    d.mkdir()
    (d / "one.txt").write_text("A: We left in March. It was cold.\nB: And after that?\n")
    (d / "two.md").write_text("A: The work was steady. Nobody complained.\n")
    return d


@pytest.fixture(autouse=True)
def _condition_env(monkeypatch):
    """The runner puts a condition on the process environment, the way a shell prologue would.
    Recorded here so monkeypatch takes it back off again: a leaked `APERTURE_FOLLOW=marked` would
    quietly gate every later test in the session."""
    for name in ("APERTURE_FOLLOW", "APERTURE_RESIDUAL"):
        monkeypatch.setenv(name, "")
        monkeypatch.delenv(name)


@pytest.fixture
def dry(corpus, tmp_path, capsys):
    """Plan one condition and give back what the runner said about it."""
    def run(*flags, data="d"):
        assert eval_run.main(["--materials", str(corpus), "--data", str(tmp_path / data),
                              "--out", str(tmp_path / "r.md"), "--dry-run", *flags]) == 0
        return capsys.readouterr().out

    return run


# ---- the four conditions -------------------------------------------------------------------------

def test_a_dry_run_plans_the_iterative_chain_and_leaves_the_data_directory_alone(dry, tmp_path):
    """What `--dry-run` is for: the plan, the provider and the condition, before any of it is paid
    for — and no database in `--data`, or the real run would refuse to start.

    The iterative chain is written out here because §1-2 is the chain that does not move; the
    explore one is checked by what distinguishes it, so R4 can grow it without editing a test.
    """
    printed = dry("--method", "iterative")
    assert "condition: method=iterative · gate=off · residual=on" in printed
    assert "provider minimax" in printed
    assert "one.txt: 3 passages" in printed and "two.md: 2 passages" in printed
    assert ("frame → angles → read → frame → angles → read → themes → themes → "
            "doc → tighten → doc → tighten") in printed, \
        "no reconcile: an iterative project is shown the codebook"
    assert not (tmp_path / "d" / "aperture.db").exists()


def test_a_dry_run_plans_the_explore_chain_with_its_reconciling_step(dry):
    """What separates the two conditions, not the whole list: a reading shown no codebook has its
    vocabulary compared with the project's in a step of its own, after every material."""
    printed = dry("--method", "explore")
    assert "condition: method=explore" in printed
    steps = printed.split("steps: ")[1].splitlines()[0].split(" → ")
    assert steps.count("reconcile") == 2, "one per material"
    assert steps[:4] == ["frame", "angles", "read", "reconcile"]
    assert steps != dry("--method", "iterative", data="e").split("steps: ")[1].splitlines()[0]


def test_without_a_method_the_runner_plans_what_a_new_project_would_do(dry):
    """The default belongs to `store.create_project`, not to the runner: a harness with an opinion
    of its own would read a corpus differently from the application it is measuring."""
    import inspect

    from app import store

    default = inspect.signature(store.create_project).parameters["method"].default
    assert f"condition: method={default}" in dry()


def test_the_gate_flag_sets_the_environment_the_engine_reads(dry):
    """`--gate` is the second condition. `synth._marked_here` reads APERTURE_FOLLOW, so the flag
    has to arrive as that name and not as an argument the engine never sees."""
    import os

    printed = dry("--method", "iterative", "--gate")
    assert os.environ["APERTURE_FOLLOW"] == "marked"
    assert "gate=marked" in printed


def test_no_residual_names_its_environment_and_admits_when_nothing_reads_it(dry):
    """The fourth condition turns R4's omission pass off. The name is agreed here first, so the
    run reports the flag as inert until the engine adopts it — a condition reported as applied
    when nothing read it is worse than no condition at all."""
    import os

    printed = dry("--method", "explore", "--no-residual")
    assert os.environ["APERTURE_RESIDUAL"] == "off"
    assert "residual=off" in printed
    assert ("inert" in printed) is not eval_run._reads_residual()


def test_a_dry_run_still_refuses_a_data_directory_that_holds_a_reading(corpus, tmp_path):
    used = tmp_path / "used"
    used.mkdir()
    (used / "aperture.db").write_text("")
    with pytest.raises(SystemExit, match="already exists"):
        eval_run.main(["--materials", str(corpus), "--data", str(used),
                       "--out", str(tmp_path / "r.md"), "--dry-run"])


def test_the_calls_under_every_step_are_written_beside_the_record(corpus, tmp_path, monkeypatch,
                                                                  capsys):
    """`--record-calls` is on by default: the data directory is what gets deleted, and the call
    rows are the only record of cached tokens, reasoning tokens and retries."""
    from app import jobs, store

    def one_call(conn, project, run):
        store.save_call(conn, run["run_id"], "read", 1, "minimax", "M3", "",
                        {"tokens_in": 90, "tokens_out": 12, "tokens_reasoning": 9},
                        "2026-09-05T10:00:00", 1.5, "ok")

    for kind, (line, _) in list(jobs.STEPS.items()):
        monkeypatch.setitem(jobs.STEPS, kind, (line, one_call))
    out = tmp_path / "v" / "record.md"
    assert eval_run.main(["--materials", str(corpus), "--data", str(tmp_path / "vdata"),
                          "--out", str(out)]) == 0

    steps = capsys.readouterr().out.split("steps: ")[1].splitlines()[0].split(" → ")
    calls = json.loads(out.with_suffix(".calls.json").read_text())
    assert len(calls) == len(steps), "one call per step of the chain, whatever the chain is"
    assert {c["kind"] for c in calls} == set(steps)
    assert calls[0]["tokens_reasoning"] == 9 and calls[0]["tokens_cached"] is None
    totals = json.loads(out.with_suffix(".metrics.json").read_text())["calls"]
    assert totals["calls"] == len(steps) and totals["attempts"] == len(steps)


def test_the_calls_file_can_be_turned_off(corpus, tmp_path, monkeypatch):
    from app import jobs

    for kind, (line, _) in list(jobs.STEPS.items()):
        monkeypatch.setitem(jobs.STEPS, kind, (line, lambda c, p, r: None))
    out = tmp_path / "v" / "record.md"
    eval_run.main(["--materials", str(corpus), "--data", str(tmp_path / "vdata"),
                   "--out", str(out), "--no-record-calls"])
    assert not out.with_suffix(".calls.json").exists()


# ---- the blind dossiers --------------------------------------------------------------------------

RECORD = """# A reading of ellis3

## Across the corpus

Written by the {name} condition.

## Themes

### Across materials

#### Work and trade

how a living is made

1. He worked the boats
   > we worked the boats in March  [S010]

## Materials

### Grande, M.

#### Work and trade

The {name} reading found work.

## Processing history

- **reconcile** — 3 runs · 10 input tokens · 2 output tokens
"""


@pytest.fixture
def records(tmp_path):
    """One record per condition, each naming its own condition in the text — which is what the
    lettering has to remove."""
    for name in ("iterative", "iterative-gated", "explore", "explore-residual"):
        (tmp_path / f"{name}.md").write_text(RECORD.format(name=name), encoding="utf-8")
    return {n: str(tmp_path / f"{n}.md")
            for n in ("iterative", "iterative-gated", "explore", "explore-residual")}


def build(records, out, *flags, seed=7):
    assert eval_dossiers.main(
        ["--bench", str(out), "--pass", "pass6", "--seed", str(seed),
         "--transcripts", str(out / "corpus"), "--conditions",
         *(f"{n}={p}" for n, p in records.items()), *flags]) == 0
    return out / "pass6"


def test_each_condition_becomes_a_letter_and_the_key_maps_it_back(records, tmp_path):
    d = build(records, tmp_path / "bench")
    key = json.loads((d / "KEY.json").read_text())
    assert sorted(key) == ["A", "B", "C", "D"]
    assert sorted(k["condition"] for k in key.values()) == sorted(records)
    assert sorted(p.name for p in (d / "dossiers").iterdir()) == ["A.md", "B.md", "C.md", "D.md"]
    assert [k["condition"] for k in key.values()] != sorted(records), "the letters are shuffled"


def test_the_same_seed_letters_them_the_same_way_and_another_seed_does_not(records, tmp_path):
    """A build has to be repeatable — a coordinator who rebuilds the dossiers halfway through the
    judging must not silently renumber them under the judges."""
    one = json.loads((build(records, tmp_path / "a") / "KEY.json").read_text())
    same = json.loads((build(records, tmp_path / "b") / "KEY.json").read_text())
    other = json.loads((build(records, tmp_path / "c", seed=99) / "KEY.json").read_text())
    assert one == {k: {**v, "record": same[k]["record"]} for k, v in same.items()}
    shuffled_flags = build({k: records[k] for k in reversed(list(records))}, tmp_path / "d")
    assert {k: v["condition"] for k, v in one.items()} == \
           {k: v["condition"] for k, v in
            json.loads((shuffled_flags / "KEY.json").read_text()).items()}, \
        "and the order the flags were typed in does not renumber them either"
    assert {k: v["condition"] for k, v in one.items()} != \
           {k: v["condition"] for k, v in other.items()}


def test_a_dossier_is_the_themes_and_materials_and_nothing_that_names_its_condition(records,
                                                                                    tmp_path):
    """The record's own name for the condition, and the step list that would give it away, both
    go: `reconcile` in a processing history says which chain ran, which is the whole secret."""
    d = build(records, tmp_path / "bench")
    key = json.loads((d / "KEY.json").read_text())
    for letter, k in key.items():
        text = (d / "dossiers" / f"{letter}.md").read_text()
        assert text.startswith(f"# Record {letter}")
        assert "## Themes" in text and "## Materials" in text
        assert "Processing history" not in text and "reconcile" not in text
        assert "Across the corpus" not in text
        for name in key.values():
            assert name["condition"] not in text
        assert f"The Record {letter} reading found work." in text


def test_a_condition_whose_name_contains_another_is_not_half_scrubbed(records, tmp_path):
    """'explore' is a prefix of 'explore-residual'. Scrubbed shortest-first, the longer record
    would keep a '-residual' nobody removed."""
    d = build(records, tmp_path / "bench")
    for p in (d / "dossiers").iterdir():
        assert "-residual" not in p.read_text() and "-gated" not in p.read_text()


def test_the_instructions_carry_the_rubric_plus_coverage_and_within_case_integrity(records,
                                                                                   tmp_path):
    d = build(records, tmp_path / "bench")
    text = (d / "INSTRUCTIONS.md").read_text()
    assert "## The nine dimensions" in text
    for heading in ("### 1. Theme inflation", "### 7. Housekeeping", "### 8. Coverage",
                    "### 9. Within-case integrity", "## Spot checks", "## What to return"):
        assert heading in text, heading
    assert "what remained unexamined" in text.lower()
    assert str((tmp_path / "bench" / "corpus").resolve()) in text, "the transcripts are named"
    assert "Do not open `KEY.json`" in text
    block = json.loads(text.split("```json")[1].split("```")[0]
                       .replace('{ "…the same shape…" }', "{}").replace("…as above…", ""))
    assert list(block["records"]["A"]["scores"]) == list(eval_dossiers._SCORE_KEYS)
    assert block["ranking"] == ["A", "B", "C", "D"]


def test_a_condition_can_be_given_as_the_runs_data_directory(conn, analysed, records, tmp_path):
    """A condition is a reading, not a file. Given the directory `--data` pointed at, the record
    is rendered from the database with the template `eval_run.py` uses — so a run that has since
    been re-read, or given a piece of feedback, is judged as it now stands."""
    d = build({"explore": str(tmp_path / "data"), "iterative": records["iterative"]},
              tmp_path / "bench")
    key = json.loads((d / "KEY.json").read_text())
    letter = next(l for l, k in key.items() if k["condition"] == "explore")
    text = (d / "dossiers" / f"{letter}.md").read_text()
    assert "## Themes" in text and "## Materials" in text
    assert "Work and trade" in text and "### Grande, M." in text
    assert "Work and trade: claim 0" in text, "the claims are carried over in full"


def test_a_condition_that_is_neither_a_record_nor_a_reading_is_refused(records, tmp_path):
    (tmp_path / "nothing").mkdir()
    with pytest.raises(SystemExit, match="no record and no aperture.db"):
        build({"gone": str(tmp_path / "nothing"), "here": records["explore"]}, tmp_path / "bench")


def test_two_conditions_are_the_fewest_that_can_be_judged_blind(records, tmp_path):
    with pytest.raises(SystemExit, match="at least two"):
        build({"only": records["explore"]}, tmp_path / "bench")


def test_unseal_puts_the_judges_scores_back_against_the_conditions(records, tmp_path, capsys):
    """The last step of the loop: two reports keyed by letter, tabulated by condition."""
    d = build(records, tmp_path / "bench")
    key = json.loads((d / "KEY.json").read_text())
    for judge, base in (("judge-1", 2), ("judge-2", 3)):
        scored = {letter: {"scores": {k: {"score": base, "evidence": "x"}
                                      for k in eval_dossiers._SCORE_KEYS}}
                  for letter in key}
        (d / f"{judge}.md").write_text(
            "prose\n\n" + json.dumps({"records": scored, "ranking": sorted(key)[::-1]}))

    code = compile((d / "unseal.py").read_text(), str(d / "unseal.py"), "exec")
    exec(code, {"__file__": str(d / "unseal.py"), "__name__": "__main__"})
    out = capsys.readouterr().out
    for k in key.values():
        assert k["condition"][:14] in out
    assert "coverage" in out and "within_case_integrity" in out
    assert "2/3 (2.5)" in out, "both judges, then their mean"
    assert "D=" in out and "ranks:" in out
