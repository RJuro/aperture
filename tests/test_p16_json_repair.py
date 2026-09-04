"""One stray quote must not throw away twenty minutes of model time.

Twice on the deployed instance the PROJECT step — `{"summary": <300 words>, "interpretation":
<150 words>}` — came back with an unescaped `"` inside one of those long strings, `json.loads`
died at column 420, the one-more-try got the same kind of answer, and nine THREAD calls and a DOC
call were discarded so the researcher's corpus summary was never written. `llm._repair` escapes
the inner quote and the raw newline instead; these tests hold the rule it uses.
"""
from __future__ import annotations

import json

import pytest

from app import llm


def test_the_live_failure_an_inner_quote_and_a_raw_line_break_in_a_long_value():
    """The exact shape that broke the run, both faults in the same answer."""
    broken = ('{"summary": "The shop stood on the corner: she called it "the shop" and left\n'
              'it at that.", "interpretation": "A living made in plain sight."}')
    with pytest.raises(json.JSONDecodeError):
        json.loads(broken)
    out = llm.parse(broken)
    assert out["summary"] == ('The shop stood on the corner: she called it "the shop" and left\n'
                              'it at that.')
    assert out["interpretation"] == "A living made in plain sight."


def test_a_value_that_ends_at_a_comma_is_left_alone():
    """A closing quote followed by `,` is a close and nothing else. Two values, both intact."""
    good = '{"a": "she left", "b": "he stayed"}'
    assert llm.parse(good) == {"a": "she left", "b": "he stayed"}
    assert llm._repair(good) == good


def test_an_escape_the_model_got_right_is_not_escaped_twice():
    already = '{"summary": "she called it \\"the shop\\" and left", "n": 2}'
    assert llm._repair(already) == already
    assert llm.parse(already) == {"summary": 'she called it "the shop" and left', "n": 2}


def test_a_quoted_term_followed_by_a_colon_is_inner_not_closing():
    """The case a greedy rule cannot do: `:` is in the follow set for a KEY, not for a value, so
    the quote before it is inner here and the key's own quote a paragraph earlier still closes."""
    broken = '{"summary": "the sign said "closed": nobody came", "interpretation": "shut"}'
    assert llm.parse(broken) == {"summary": 'the sign said "closed": nobody came',
                                 "interpretation": "shut"}


def test_a_quote_inside_a_nested_value_is_repaired_too():
    """Threads arrive as a list of objects; the stack is what keeps key position right in there."""
    broken = '{"moments": [{"claim": "he called it "the crossing"", "sid": "s7"}]}'
    assert llm.parse(broken) == {"moments": [{"claim": 'he called it "the crossing"',
                                              "sid": "s7"}]}


def test_garbage_with_no_object_is_still_a_loud_error():
    with pytest.raises(llm.LLMError, match="no JSON object"):
        llm.parse("I am afraid I cannot help with that.")
    with pytest.raises(llm.LLMError, match="no JSON object"):
        llm.parse("")


def test_a_repair_that_does_not_help_still_raises_so_the_one_more_try_runs():
    with pytest.raises(json.JSONDecodeError):
        llm.parse('{"summary": "she said "no", then left"}')


def test_a_repaired_answer_costs_no_second_call(monkeypatch, real_chat_json):
    """The point of the whole thing: chat_json returns the dict off the FIRST answer."""
    calls = []

    def ask(system, user, timeout, effort="", label=""):
        calls.append(1)
        return '{"summary": "she called it "the shop" and left", "interpretation": "a living"}'

    monkeypatch.setattr(llm, "_ask", ask)
    assert real_chat_json("s", "u", label="project") == {
        "summary": 'she called it "the shop" and left', "interpretation": "a living"}
    assert len(calls) == 1
