"""P36 — the compare control is a visible field under the theme table, not a fold in the heading.

Folded into the section heading, the one action that reads the whole corpus at once was a summary
line nobody opened. It now stands under the table, where a researcher meets it after reading the
themes it would change, with both scopes and their prices printed before it is pressed.
"""
from __future__ import annotations

import re

import pytest

from app import context, store
from tests.test_p33_consolidate import _line, _login, _material, client  # noqa: F401
from tests.test_p5_pages import strip_material


@pytest.fixture
def study(conn):                                                    # noqa: F811
    """Five materials; one candidate carried by two of them, and three never read for it.

    Two of five is below the opening threshold (three, half of five rounded up) but still meets
    the wider scope's fixed two — so the two scopes select different pairs, and both radios in
    the control actually mean something different to press.
    """
    ann = store.create_user(conn, "ann", "battery staple")
    pid = store.create_project(conn, "Ann's study", owner_id=ann, method="iterative")
    wide = store.save_theme(conn, pid, tid=None, name="Wide", gist="g", code_ids=[])
    store.set_hold(conn, wide, "candidate")
    _line(conn, _material(conn, pid, 0), wide)
    _line(conn, _material(conn, pid, 1), wide)
    for n in (2, 3, 4):
        _material(conn, pid, n)                 # never read for this theme: cells to fill
    return {"pid": pid, "ann": ann}


def _field(html: str) -> str:
    """The compare form itself, so a test cannot pass on markup elsewhere on the page."""
    found = re.search(r'<form class="compare".*?</form>', html, re.S)
    assert found, "no compare form on the project page"
    return found.group(0)


def test_an_editor_meets_it_open_under_the_table_with_both_prices(client, conn, study):  # noqa: F811
    """Visible markup, not a `<details>`: the point of the change is that it is read without
    being opened. Both scopes are there, each in its own words, with the additional checks and
    the whole operation's model-call estimate printed before it is pressed (F1, F5)."""
    _login(client, "ann", "battery staple")

    html = client.get(f"/p/{study['pid']}").text
    said = context.project_page(conn, study["pid"])["consolidate"]
    field = _field(html)

    assert "<details" not in field, "the control is open, not folded"
    assert f'action="/p/{study["pid"]}/compare"' in field and 'method="post"' in field
    assert not said["same"], "the fixture is built so the two scopes select different pairs"
    assert 'value="opening"' in field
    assert f"Themes with claims in at least {said['need']} of {said['total']} materials" in field
    assert 'value="all"' in field
    assert "Themes with claims in at least 2 materials" in field
    # Each scope prices itself: without a script the page cannot recompute when the choice
    # changes, so a count may only stand beside the option that produces it.
    assert said["opening_said"] in field and said["all_said"] in field
    assert "Each pair is one theme checked in one material." in field
    assert 'name="note"' in field
    assert "btn-primary" in field, "the button carries primary weight"
    # Under the table, not in the section head: the themes it would change are read first.
    assert html.index('<table class="themes"') < html.index('<form class="compare"')


def test_a_member_who_may_only_read_is_not_offered_it(client, conn, study):   # noqa: F811
    """It spends money and rewrites the theme set. A reader sees the themes and no control."""
    bob = store.create_user(conn, "bob", "purple monkey")
    token = store.add_invite(conn, study["pid"], "read", study["ann"])
    _login(client, "bob", "purple monkey")
    store.join(conn, token, bob)

    html = client.get(f"/p/{study['pid']}").text
    assert "Wide" in html and 'class="compare"' not in html


def test_with_nothing_to_compare_the_page_says_nothing(client, conn):        # noqa: F811
    """One candidate and no holes: `consolidate` is None and the whole field is skipped rather
    than standing there priced at nothing."""
    ann = store.create_user(conn, "ann", "battery staple")
    pid = store.create_project(conn, "Ann's study", owner_id=ann, method="iterative")
    tid = store.save_theme(conn, pid, tid=None, name="Only", gist="g", code_ids=[])
    store.set_hold(conn, tid, "candidate")
    _line(conn, _material(conn, pid, 0), tid)
    _login(client, "ann", "battery staple")

    assert context.project_page(conn, pid)["consolidate"] is None
    assert 'class="compare"' not in client.get(f"/p/{pid}").text


def test_the_field_speaks_the_researchers_language(client, conn, study):      # noqa: F811
    """Our design words would be jargon here, and a class name is on the page like any other
    text. The paragraph says what the action does, in plain, complete sentences (F1)."""
    _login(client, "ann", "battery staple")

    field = _field(client.get(f"/p/{study['pid']}").text)
    assert ("Compare the project's theme definitions and merge overlapping themes where "
            "appropriate.") in " ".join(field.split())
    said = strip_material(field).lower()
    for word in context._BANNED:
        assert not re.search(rf"\b{re.escape(word)}s?\b", said), f"{word!r} in the compare field"
