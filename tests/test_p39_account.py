"""P39 — what the account is shown about a material that sits at the edge of a definition, and
the prose rules the three prompts of this level now carry.

WP-3 of the human-gap plan. THREAD writes a note where a material carries a theme in a way its
definition did not foresee — a different kind of case, actor, setting or time — and until now
nothing above the theme page read it. The account is where it matters: the evaluation's Batta
case is a theme defined around children applied to a participant who arrived at twenty-four, and
an account that is not shown the note writes her up as an ordinary instance and the exception
disappears into the pattern.

Two things hold that here. The note is printed under the material it was written from, so the
account cannot place it against the wrong claims; and only a `fit` note is printed, because a
`tension` note is THEMES's case for unfreezing a frozen definition and is addressed to the
researcher, not to this level.

The rest of the file is the prose block and its counter across the three prompts this level owns
— ACCOUNT, MEMO and RESIDUAL. What it asserts is that the block reaches the model and that what
came back is counted on the run row; never that a count is zero, which would be the gate
`docs/EVAL.md` forbids.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from app import prose, store
from app.engine import account, memo, residual

PROMPT = Path(__file__).resolve().parent.parent / "app" / "prompts" / "account.md"

# A note in the shape THREAD writes them, on a material whose kind the definition does not name.
NOTE = "this material is a policy document; the definition names a shift"
OTHER_NOTE = "the ward is named as an organisation, not as the people on it"

# Prose of exactly the kind the rules name, so the counter has something to count. It cites a real
# claim id where a test needs it to survive the citation rules on the way out.
SMELL = "The corpus shows a pattern of refusal"


@pytest.fixture
def corpus(conn, analysed):
    """`analysed` — two framed materials, two themes, three claims each — under one theme."""
    return {**analysed, "tid": analysed["themes"]["Work and trade"],
            "other": analysed["themes"]["Leaving and arriving"]}


def written(conn, corpus, model, answer="An account."):
    """Run the account and give back what the model was shown."""
    model.queue({"account": answer})
    out = account.run(conn, corpus["pid"], corpus["tid"])
    return model.shown("account"), out


def blocks(shown: str) -> str:
    """What was shown from the first material heading on. The rules and the heading that explains
    what a note is both say the words a block would otherwise be searched for, so a test that
    searched the whole prompt would pass on the template alone."""
    return shown.split("\n## ", 1)[1]


# ---- the note from the reading -----------------------------------------------------------------

def test_a_note_from_the_reading_is_printed_under_the_material_it_was_written_from(
        conn, corpus, model):
    """Under the heading, above that material's claims. A note in a list of its own is a second
    finding about the theme; under the heading it is a fact about this material's claims."""
    store.add_theme_note(conn, corpus["tid"], corpus["grande"], None, NOTE, kind="fit")
    shown, _ = written(conn, corpus, model)

    assert f"## Grande, M. — interview — 3 claims\nnote from the reading: {NOTE}" in shown
    assert shown.index(NOTE) < shown.index("## Rodwin"), "it belongs to the block above it"


def test_a_tension_note_is_not_shown_to_this_level(conn, corpus, model):
    """A tension is THEMES's: this material pulls against a definition the researcher froze, and
    the answer to it is to unfreeze the definition or leave it frozen. Neither is the account's,
    and an account shown one writes about a decision nobody has made."""
    store.add_theme_note(conn, corpus["tid"], corpus["grande"], None,
                         "the frozen definition excludes this", kind="tension")
    shown, _ = written(conn, corpus, model)

    assert "note from the reading" not in blocks(shown)
    assert "the frozen definition excludes this" not in shown


def test_a_note_written_from_another_material_stays_under_that_material(conn, corpus, model):
    """The whole point of the note is which material it is about. Printed under the wrong heading
    it would say the exception is where it is not."""
    store.add_theme_note(conn, corpus["tid"], corpus["grande"], None, NOTE, kind="fit")
    store.add_theme_note(conn, corpus["tid"], corpus["rodwin"], None, OTHER_NOTE, kind="fit")
    shown, _ = written(conn, corpus, model)

    grande, rodwin = shown.split("## Rodwin")
    assert NOTE in grande and OTHER_NOTE not in grande
    assert OTHER_NOTE in rodwin and NOTE not in rodwin


def test_a_note_on_another_theme_is_not_this_theme_s_to_read(conn, corpus, model):
    store.add_theme_note(conn, corpus["other"], corpus["grande"], None, NOTE, kind="fit")
    shown, _ = written(conn, corpus, model)
    assert NOTE not in shown


def test_a_material_the_reading_left_no_note_on_prints_no_label(conn, corpus, model):
    """An empty "note from the reading:" reads as a reading that looked and had nothing to say,
    and no such reading was ever made."""
    store.add_theme_note(conn, corpus["tid"], corpus["grande"], None, NOTE, kind="fit")
    shown, _ = written(conn, corpus, model)

    assert blocks(shown).count("note from the reading:") == 1
    assert "note from the reading:\n" not in shown


def test_a_note_left_after_an_account_makes_it_worth_writing_again(conn, corpus, model):
    """The fingerprint is everything the prompt is built from. A note the fingerprint cannot see
    is a note a cached account was written without, and the page would call that account current.
    """
    was = account.fingerprint(conn, corpus["pid"], corpus["tid"])
    store.add_theme_note(conn, corpus["tid"], corpus["grande"], None, NOTE, kind="fit")
    assert account.fingerprint(conn, corpus["pid"], corpus["tid"]) != was


# ---- the three rules that read it ---------------------------------------------------------------

def test_the_prompt_carries_the_three_rules_this_level_gained(conn, corpus, model):
    """Placing a noted material, checking the mechanism a definition names, and keeping what a
    material describes apart from how it weighs it. Numbered on from the eight that were there."""
    shown, _ = written(conn, corpus, model)
    said = " ".join(shown.split())

    assert "Eleven rules" in said
    assert "Where a material's block carries a note from the reading" in said
    assert "names a cause, a consequence or a mechanism" in said
    assert "carry that link itself or only its two ends" in said
    assert "the material's own evaluation of what it describes" in said


def test_each_of_the_three_says_nothing_where_the_corpus_lacks_what_it_names():
    """Aperture reads documents, field notes and open answers as ordinarily as interviews. A rule
    that presupposes its own subject produces one: an evaluation where nothing evaluates, a
    mechanism where the definition names none."""
    text = " ".join(PROMPT.read_text().split())
    assert text.count("this rule says nothing") == 3
    for word in ("narrator", "her life", "life course", "journey"):
        assert word not in text.lower()


# ---- the prose block, in all three prompts ------------------------------------------------------

def test_the_prose_rules_reach_the_model(conn, corpus, model):
    shown, _ = written(conn, corpus, model)
    assert "HOW TO WRITE" in shown
    assert "Subject: a person, a group, a material, or the claims" in shown
    assert "{{style}}" not in shown, "the loader fills it; nothing ships the literal slot"


def test_the_worked_example_obeys_the_rules_it_now_sits_beside():
    """The strongest teacher in the prompt is the example, not the rule. While it was written in
    the register the rules ban, every account came back in that register."""
    example = re.search(r'Worked, on a theme called.*?\{\s*"account": "(.*?)"\s*\}',
                        PROMPT.read_text(), re.S)
    assert example, "the worked example must still be findable"
    assert prose.count(" ".join(example.group(1).split())) == {}


def test_what_the_account_came_back_in_is_counted_on_the_run_row(conn, corpus, model):
    """Counted, never rejected: a retry is a whole call, and the sentence this points at may be
    the sentence the claims earn. The researcher reads the count beside the account."""
    real = store.thread(conn, corpus["grande"], corpus["tid"])[0]["id"]
    _, out = written(conn, corpus, model, f"{SMELL} [{real}].")

    said = [d for d in out["dropped"] if d.startswith("style: ")]
    assert said and "unscoped" in said[0]
    assert SMELL in out["text"], "the account itself is untouched by the count"


def test_a_plain_account_is_counted_and_says_so_by_saying_nothing(conn, corpus, model):
    real = store.thread(conn, corpus["grande"], corpus["tid"])[0]["id"]
    _, out = written(conn, corpus, model,
                     f"Two of the materials describe a stall in the market [{real}].")
    assert not [d for d in out["dropped"] if d.startswith("style: ")]


def test_what_a_memo_came_back_in_is_counted_too(conn, analysed, model):
    mid = analysed["grande"]
    sid = store.sentences(conn, mid)[5][0]
    model.queue({"memo": f"{SMELL} [{sid}].", "questions": "It was not merely the roster.",
                 "people": []})
    model.queue({"verdicts": []})

    out = memo.run(conn, mid)

    said = [d for d in out["dropped"] if d.startswith("style: ")]
    assert said and "unscoped" in said[0] and "contrast" in said[0], \
        "the memo and its questions are both prose a researcher reads"


def test_what_the_remainder_came_back_in_is_counted_too(conn, analysed, model):
    """RESIDUAL writes a claim and a note. Nothing here marked a passage, so every passage of the
    material is the remainder — which is what this step is shown."""
    mid = analysed["grande"]
    model.queue({"additions": [], "none_for": [], "note": f"{SMELL} about dates."})

    out = residual.run(conn, mid)

    said = [d for d in out["dropped"] if d.startswith("style: ")]
    assert said and "unscoped" in said[0]
    assert out["note"] == f"{SMELL} about dates.", "the note itself is stored as it came back"
