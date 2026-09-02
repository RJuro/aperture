"""The anchor law's rules (masshine/anchor.py) — the trust core, so tested as pure functions."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import anchor  # noqa: E402

# Shaped like a real transcript: tab-separated speaker cues, doubled spaces, a quote that runs
# across a sentence boundary, and the D15 pair — a theft passage and a class passage far apart.
SENTS = [
    ("S1.019", "\tGRANDE:\tBut part of our clothes was stolen in Trieste, so a fellow that my "
               "mother knew, he went in, I believe, in London, to buy some clothes for us."),
    ("S1.022", " He could speak American."),
    ("S4.014", "\tGRANDE:\tAnd in the spring, when he was supposed to go kind of like to report "
               "for the army, he was on the wagon and he fell or jumped or whatever, and he got "
               "killed."),
    ("S4.015", " So then this one got to come from the army earlier to take over the farm."),
    ("S5.012", "\tGRANDE:\tAnd, uh, my dad paid for first class but they put us down on the "
               "bottom and then this one fellow spoke up that was, uh, here before."),
    ("S5.013", " And he seen my mother's card, and he said, “You don't belong down here.”"),
]


def test_norm_ignores_typesetting_and_quote_style():
    assert anchor.norm("\tHe  said,\t“don’t”") == anchor.norm('He said, "don\'t"')


def test_anchor_inside_its_own_citation_is_bound():
    v = anchor.bind("he fell or jumped or whatever", ["S4.014"], SENTS)
    assert v["verdict"] == "bound"
    assert v["sids"] == ["S4.014"]


def test_d15_a_true_claim_with_wrong_citations_is_rebound_not_dropped():
    """The round-2 defect: the claim about the paid-for class was real, and pointed at the
    Trieste theft. The anchor is authoritative, so the citation is repaired."""
    v = anchor.bind("my dad paid for first class", ["S1.019", "S1.022"], SENTS)
    assert v["verdict"] == "rebound"
    assert v["sids"] == ["S5.012"]


def test_invented_quote_is_unfound():
    v = anchor.bind("she wept for the old country", ["S4.014"], SENTS)
    assert v["verdict"] == "unfound"
    assert v["sids"] == []


def test_anchor_may_cross_a_sentence_boundary_and_binds_where_it_starts():
    v = anchor.bind("he got killed. So then this one got to come from the army earlier",
                    ["S4.014"], SENTS)
    assert v["verdict"] == "bound"
    assert v["found_in"] == ["S4.014"]


def test_curly_apostrophe_retyped_straight_still_matches():
    v = anchor.bind("You don't belong down here", ["S5.013"], SENTS)
    assert v["verdict"] == "bound"


def test_apply_drops_a_claim_with_no_anchor_and_tallies_missing():
    st = anchor.new_stats()
    assert anchor.apply({"statement": "x"}, ["S4.014"], SENTS, st) is None
    assert st["missing"] == 1 and st["unfound"] == 0


def test_apply_returns_repaired_sids_on_rebind():
    st = anchor.new_stats()
    kept = anchor.apply({"anchor": "put us down on the bottom"}, ["S1.019"], SENTS, st)
    assert kept == ("put us down on the bottom", ["S5.012"])
    assert st["rebound"] == 1


def test_over_cap_is_counted_but_never_rejected():
    long = ("And in the spring, when he was supposed to go kind of like to report for the army, "
            "he was on the wagon")
    st = anchor.new_stats()
    kept = anchor.apply({"anchor": long}, ["S4.014"], SENTS, st)
    assert kept is not None                       # truth, not style, decides
    assert st["over_cap"] == 1 and st["bound"] == 1


def test_locate_binds_to_the_starting_sentence_not_an_earlier_window():
    assert anchor.locate("He could speak American", SENTS) == ["S1.022"]
