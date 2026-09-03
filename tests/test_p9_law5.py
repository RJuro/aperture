"""Law 5, mechanically. A prompt template is universal; a slot holds the material, validated
structure, or the researcher's words. Prose the system wrote about the corpus reaches no prompt —
except the one self-prompting slot, which carries questions and is read by exactly one step.

The test plants sentinels where such prose lives and compiles every prompt, with the model
stubbed to answer nothing. Wherever a sentinel surfaces, a conclusion is being fed back in as an
instruction. This is the check that would have caught six bugs at once.
"""
from __future__ import annotations

import pytest

from app import store
from app.engine import account, angles, check, frame, read, synth, themes

SELF_PROMPT = "SENTINEL-QUESTIONS the corpus left open"
ACCOUNT_PROSE = "SENTINEL-ACCOUNT conclusion about the whole corpus"
SUMMARY_PROSE = "SENTINEL-SUMMARY what the reading found in this piece"
PROJECT_PROSE = "SENTINEL-PROJECT what the corpus shows"
ANGLES_PROSE = "SENTINEL-ANGLES where to look next"


@pytest.fixture
def compiled(conn, analysed, model):
    """Every prompt the engine can compile, keyed by label, against a project seeded with
    sentinels in each place the system stores its own prose."""
    pid, mid = analysed["pid"], analysed["grande"]
    tid = list(analysed["themes"].values())[0]
    store.set_brief(conn, pid, SELF_PROMPT)
    store.save_summary(conn, "theme", tid, "reading", ACCOUNT_PROSE)
    store.save_summary(conn, "material", mid, "reading", SUMMARY_PROSE)
    store.save_summary(conn, "project", pid, "reading", PROJECT_PROSE)
    # A second material that has been ideated and re-framed but not yet read. Its summary is the
    # one the corpus summary is shown, and the stageless lookup used to hand it the angles.
    other = analysed["rodwin"]
    conn.execute("UPDATE summary SET status='superseded' WHERE scope='material' AND ref_id=? "
                 "AND stage='reading'", (other,))
    store.save_summary(conn, "material", other, "angles", ANGLES_PROSE)
    store.save_summary(conn, "material", other, "orientation", "An interview, described.")

    seen: dict[str, str] = {}
    empty = {"frame": {"kind": "interview", "display": "turns", "title": "t", "speakers": [],
                       "segments": [], "orientation": "o"},
             "angles": {"field": ANGLES_PROSE, "subareas": [], "angles": []},
             "read": {"codes": []}, "themes": {"themes": []},
             "thread": {"moments": []},
             "doc": {"summary": "", "questions": "", "people": []},
             "account": {"text": "", "gist": ""}, "project": {"summary": ""},
             "check": {"found": []}}

    def fake(system, user, *, label="", timeout=None):
        seen[label] = seen.get(label, "") + "\n" + system + "\n" + user
        return empty[label]

    for mod in (frame, angles, read, themes, synth, check, account):
        mod.llm.chat_json = fake

    frame.run(conn, mid)
    angles.run(conn, mid)
    read.run(conn, mid)
    themes.run(conn, pid, material_id=mid)
    synth.doc(conn, mid)
    account.run(conn, pid, tid)
    synth.project(conn, pid)
    check.run(conn, pid, "material", mid, "anything?")
    return seen


def test_every_step_compiles(compiled):
    assert set(compiled) >= {"frame", "angles", "read", "themes", "thread", "doc", "account",
                             "project", "check"}


def test_the_self_prompting_slot_reaches_exactly_one_step(compiled):
    """The brief used to reach READ, DOC and ACCOUNT as 'what this corpus is like' and became a
    finding carried forward as an instruction. It carries questions now, to ideation only."""
    where = sorted(label for label, text in compiled.items() if SELF_PROMPT in text)
    assert where == ["angles"], f"the self-prompting slot leaked into {where}"


def test_the_places_to_look_reach_only_the_reading(compiled):
    """Angles say where to look, and the reading is the one step allowed to be pointed. Anywhere
    else they are the system's own prose about the corpus standing in a slot Law 5 reserves for
    the material, validated structure, or the researcher's words — and the stageless summary
    lookup handed them to the corpus summary as a material's summary until it was ordered."""
    where = sorted(label for label, text in compiled.items() if ANGLES_PROSE in text)
    assert where == ["read"], f"the places to look leaked into {where}"


def test_a_theme_account_reaches_only_the_layer_above_it(compiled):
    """An account concludes about a theme. It is read by the corpus summary, which is written over
    it, and by nothing that reads material — or the conclusion would steer the next reading."""
    where = sorted(label for label, text in compiled.items() if ACCOUNT_PROSE in text)
    assert where == ["project"], f"an account leaked into {where}"


def test_a_material_summary_reaches_only_the_layers_above_it(compiled):
    where = sorted(label for label, text in compiled.items() if SUMMARY_PROSE in text)
    assert set(where) <= {"project"}, f"a material summary leaked into {where}"


def test_the_corpus_summary_reaches_no_prompt_at_all(compiled):
    """Nothing is written over the corpus summary; it is the top. If it appears in any prompt, a
    conclusion is being fed back into its own evidence."""
    where = sorted(label for label, text in compiled.items() if PROJECT_PROSE in text)
    assert where == [], f"the corpus summary leaked into {where}"


def test_a_prompt_template_carries_no_corpus_specific_text():
    """The template files are the same for every project. Nothing from any corpus we have run
    may be written into them."""
    import re
    from pathlib import Path
    prompts = Path(__file__).resolve().parent.parent / "app" / "prompts"
    for f in prompts.glob("*.md"):
        text = f.read_text()
        for word in ("Grande", "Rodwin", "Trieste", "Ellis Island", "packing house", "Denver"):
            assert word not in text, f"{f.name} carries corpus text: {word!r}"
        # a slot the engine does not fill would be caught at compile time; a slot-free block of
        # prose longer than a worked example is the shape a leaked finding takes
        assert len(re.findall(r"\{\{\w+\}\}", text)) >= 3, f"{f.name} has too few slots to be a scaffold"
