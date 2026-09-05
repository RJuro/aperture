"""P32 — the guide at `/guide`, and the `?` links that reach it.

The guide's whole risk is that it goes stale in a way nobody notices: a section id renamed and
every `?` beside a control lands at the top of the page instead of at the answer. So the test that
matters is the link test — every `?` on a page a researcher meets first must point at a section
that exists.
"""
from __future__ import annotations

import re

import pytest

pytest.importorskip("app.pages")
pytest.importorskip("app.context")

# The ids `docs/GUIDE.md` promises and the templates link to.
SECTIONS = ("what-happens", "method", "focus", "themes", "reach", "lines", "absence", "comments",
            "rerun", "check", "cases", "record", "sharing", "method-notes")


@pytest.fixture
def client(conn, monkeypatch):
    from fastapi.testclient import TestClient
    from app import main, pages
    monkeypatch.setattr(main, "conn", conn, raising=False)
    monkeypatch.setattr(pages, "connection", lambda: conn, raising=False)
    return TestClient(main.app)


def helps(html: str) -> set[str]:
    """Every guide section a page's links ask for."""
    return set(re.findall(r'href="/guide#([a-z-]+)"', html))


def test_the_guide_renders_with_every_section(client):
    html = client.get("/guide").text
    for sid in SECTIONS:
        assert f'id="{sid}"' in html, f"no section {sid!r} in the guide"


def test_the_guide_renders_without_a_project(client, project):
    """It is reached from inside a project and from outside one, and it has no project of its own
    — so it must not touch the rail's context. A 500 here is the shell asking for one."""
    r = client.get("/guide")
    assert r.status_code == 200
    assert "project-rail" not in r.text


def test_the_rail_and_the_home_page_offer_the_guide(client, conn, project, grande):
    assert '/guide"' in client.get("/").text, "no way to the guide from the home page"
    assert '/guide"' in client.get(f"/p/{project}").text, "no way to the guide from a project"


def test_every_help_link_on_home_and_project_points_at_a_real_section(client, conn, project,
                                                                     grande):
    asked = helps(client.get("/").text) | helps(client.get(f"/p/{project}").text)
    assert asked, "no help links at all"
    assert asked <= set(SECTIONS), f"help links at nothing: {sorted(asked - set(SECTIONS))}"


def test_the_long_choices_are_stacked_labels(client, conn, project):
    """The two-sentence choices overflowed their column: a radio inherits `width: 100%` from the
    field rule, and in a centred flex row it shrank to a sliver with its sentence hanging off the
    middle. `.choice` is the grid that gives the control a column of its own."""
    for url in ("/", f"/p/{project}"):
        html = client.get(url).text
        labels = re.findall(r"<label[^>]*>\s*<input type=\"radio\"", html)
        assert labels, f"no choice at all on {url} — this test would pass on an empty page"
        for label in labels:
            assert 'class="choice"' in label, f"an unstacked radio label on {url}"


def test_the_guide_does_not_speak_our_vocabulary(client):
    """`_BANNED` is our design language and would be jargon on a page. Module paths are exempt and
    are the reason `<code>` is stripped first: `app/anchor.py` is a filename a maintainer needs,
    not the app calling a quote an anchor."""
    from app import context
    from tests.test_p5_pages import strip_material

    said = strip_material(re.sub(r"<code>.*?</code>", " ", client.get("/guide").text,
                                 flags=re.S)).lower()
    for word in context._BANNED:
        assert not re.search(rf"\b{re.escape(word)}s?\b", said), f"{word!r} in the guide"
