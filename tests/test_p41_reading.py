"""P41 — what the reading is told to code, and which prompts are told how to write.

Two changes to the reading, both from the close reading of the Ellis Island run against three
human coders, and both about material the machine walked past:

    a passage carrying two meanings   the run coded one of them. The calibration session had
                                      already decided the opposite — an extract carries every
                                      pattern it carries — and READ was pushing the other way
                                      with "say less rather than more"
    a standing condition              a status, a constraint, a resource, a state of a body: the
                                      reading saw an event and moved on, and a whole theme came
                                      out at 66% coverage because of it

The second change is one sentence of licence, and the danger in it is a passage coded twice under
two names for the same thing — a fault the rubric already scores. Rule 10 permits the second
meaning and forbids the synonym in the same breath, and this file holds both halves.

Beside them, the style block: the prompts whose prose a researcher reads carry it, and the
prompts that emit codes, ids and twelve-word verdicts do not. `docs/plans/2026-09-06-prose-style.md`
§3 is the table; a slot this file finds where the table gives none is drift.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from app import ingest, llm, store
from app.engine import angles

reconcile = pytest.importorskip("app.engine.reconcile")
screen = pytest.importorskip("app.engine.screen")
tighten = pytest.importorskip("app.engine.tighten")

PROMPTS = Path(llm.__file__).resolve().parent / "prompts"

MINE = ("read", "angles", "screen", "reconcile", "verify", "verify_summary", "tighten")


def flat(text: str) -> str:
    """One line. Every rule here is wrapped at eighty columns in the file, and a test that
    asserted on the wrapping would fail the next time a word was added to a sentence."""
    return " ".join(text.split())


def compiled(name: str) -> str:
    """The prompt as the model gets it, on one line, with every caller-filled slot marked. The
    reserved slots are left out on purpose: passing one raises, which is the loader's point."""
    text = (PROMPTS / f"{name}.md").read_text()
    slots = set(re.findall(r"\{\{(\w+)\}\}", text)) - set(llm.RESERVED)
    system, user = llm.prompt(name, **{s: f"<<{s}>>" for s in slots})
    return flat(system + "\n" + user)


# ---- what READ is now allowed, and what it is still not ---------------------------------------

def test_a_passage_with_two_meanings_carries_two_codes():
    system = compiled("read")
    assert "A passage that carries two meanings carries two codes" in system
    assert "do not choose between them" in system


def test_the_same_licence_does_not_let_one_passage_be_coded_twice_under_two_names():
    """The recycled-passage fault. Permission for a second meaning is not permission for a second
    name for the first one, and the two sit in the same rule so neither is read without the
    other."""
    system = compiled("read")
    assert "do not code one passage twice under synonyms" in system
    assert "no code repeats the codebook's wording with a synonym" in system


def test_a_meaning_that_appears_once_is_still_coded():
    """The old rule 11 said "say less rather than more", which is what dropped the second
    meaning."""
    system = compiled("read")
    assert "say less rather than more" not in system.lower()
    assert "not left because it appears once" in system


def test_a_standing_condition_is_named_as_a_kind_of_thing_and_not_as_a_domain_s_thing():
    """A status, a constraint, a resource — a list that says nothing at all on a corpus that has
    none of them, and everything on one that does. A rule naming legal status or illness would
    have taught the reading this corpus before it opened the material."""
    system = compiled("read")
    assert ("A standing condition — a status, a constraint, a resource, a rule, a state of a "
            "body, a place or an organisation —") in system
    assert "is a code where the passage treats it as a condition that holds" in system
    assert "not a code where the passage only reports it as one event among others" in system


# ---- what an angle may name -------------------------------------------------------------------

def test_an_angle_names_the_ground_and_the_prompt_shows_the_verdict_it_would_be():
    """Rule 2 already said an angle never says what is found, and the run produced "Economic
    descent across migration" anyway — a noun phrase that reads like a place to look and is a
    conclusion. The rule now carries an instance of itself in its own example domain."""
    system = compiled("angles")
    assert '"How staffing is spoken of on nights" is an angle' in system
    assert '"Understaffing on the night shift" is a finding' in system
    assert "Name the ground, not the verdict" in system


# ---- who is told how to write, and who is not -------------------------------------------------

@pytest.fixture
def read_material(conn, project):
    text = ("NURSE: The night shift was two of us. Whatever the day missed we found late. "
            "The handover sheet is read out and then nobody looks at it again.")
    mid = store.add_material(conn, project, "Ward notes", text)
    store.save_sentences(conn, mid, ingest.sentences(text))
    return mid


def test_the_short_block_reaches_the_angles(conn, grande, model):
    store.save_frame(conn, grande, kind="interview", display="turns", title="G",
                     speakers=[], segments=[])
    model.queue({"field": "f", "subareas": [], "angles": []})
    angles.run(conn, grande)
    assert "HOW TO WRITE" in model.shown("angles")


def test_the_short_block_reaches_the_look(conn, project, read_material, model):
    tid = store.save_theme(conn, project, tid=None, name="Handover",
                           gist="How a shift hands over.", code_ids=[])
    model.queue({"verdicts": [{"id": tid, "verdict": "look", "why": "two codes about handover"}]})
    screen.run(conn, read_material, [tid])
    assert "HOW TO WRITE" in model.shown("screen")


def test_the_short_block_reaches_the_comparison(conn, project, grande, rodwin, model):
    for mid, name in ((rodwin, "Handover"), (grande, "Rostering")):
        sid, _ = store.sentences(conn, mid)[1]
        store.save_codes(conn, project, mid,
                         [{"name": name, "definition": f"Passages about {name.lower()}.",
                           "sids": [sid]}])
    model.queue({"relations": []})
    reconcile.run(conn, grande)
    assert "HOW TO WRITE" in model.shown("reconcile")


def test_the_whole_block_reaches_the_rewrite_of_a_claim(conn, project, grande, model, quote):
    """TIGHTEN writes the sentence a researcher reads in place of the one the check marked, so it
    gets the whole block and not the four rules that bear on a name."""
    store.save_frame(conn, grande, kind="interview", display="turns", title="G",
                     speakers=[], segments=[])
    tid = store.save_theme(conn, project, tid=None, name="Work", gist="a living", code_ids=[])
    sid, text = quote(grande)
    store.save_moments(conn, grande, tid,
                       [{"claim": "He took the work without complaint.",
                         "anchor": " ".join(text.split()[:8]), "sid": sid}])
    rows = store.thread(conn, grande, tid)
    store.mark_support(conn, [(rows[0]["id"], "partly", "'without complaint' adds a manner")])

    model.queue({"claims": []})
    tighten.run(conn, grande)
    shown = model.shown("tighten")
    assert "HOW TO WRITE" in shown
    assert "Not this:" in shown, "the whole block, worked pairs included"


def test_the_reading_and_the_two_checks_are_told_nothing_about_prose():
    """READ emits code names and sentence ids; VERIFY and its summary emit a verdict and at most
    twelve words of why. None of that is prose a researcher reads as prose, and 250 tokens of
    style beside the evidence rules would only crowd them."""
    for name in ("read", "verify", "verify_summary"):
        assert "HOW TO WRITE" not in compiled(name), f"{name} carries a style block"


def test_no_prompt_here_declares_a_slot_the_table_does_not_give():
    table = {"read": set(), "verify": set(), "verify_summary": set(), "tighten": {"style"},
             "angles": {"style_short"}, "screen": {"style_short"},
             "reconcile": {"style_short"}}
    for name in MINE:
        text = (PROMPTS / f"{name}.md").read_text()
        assert set(re.findall(r"\{\{(\w+)\}\}", text)) & set(llm.RESERVED) == table[name], name


def test_the_block_is_the_last_thing_before_the_material():
    """Placement is the rule, not decoration: the task rules stay numbered first and the style
    block sits between them and the material, where the model reads it last."""
    for name in ("angles", "screen", "reconcile", "tighten"):
        head = (PROMPTS / f"{name}.md").read_text().partition("\n---\n")[0]
        assert head.rstrip().endswith("}}"), f"{name}: the block is not last in the system message"


# ---- the register the prompts used to teach ---------------------------------------------------

def test_none_of_these_prompts_teaches_the_voice_the_style_block_bans():
    """A model imitates an example more faithfully than a rule. "A hedge hardened into a fact" is
    a figure, and "Reading costs a call; a missed theme costs a finding" is an aphorism; both
    named the right thing in the wrong register, and both came back in the record's prose."""
    for name in MINE:
        text = flat((PROMPTS / f"{name}.md").read_text())
        assert "hardened into a fact" not in text, f"{name} still writes the figure"
        assert "costs a finding" not in text, f"{name} still writes the aphorism"


def test_the_hedge_is_named_by_an_instance_instead():
    for name in ("verify", "verify_summary", "tighten"):
        text = flat((PROMPTS / f"{name}.md").read_text())
        assert "a hedge written as a fact" in text
        assert '"I think she adapted"' in text, f"{name} names the figure without showing one"


def test_no_worked_example_here_comes_from_the_corpus_the_instrument_is_judged_on():
    """`test_p9_law5` holds the corpus out of the slots; this holds it out of the examples. A
    prompt that teaches the reading a migration vocabulary and is then judged on migration
    material cannot be told apart from one that learned the domain from the prompt."""
    for name in MINE:
        text = flat((PROMPTS / f"{name}.md").read_text()).lower()
        for word in ("migrat", "emigrat", "immigrant", "ellis island", "the crossing",
                     "leaving home", "waiting for papers"):
            assert word not in text, f"{name}.md carries {word!r}"
