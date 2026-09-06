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
    """Every guide section a page's links ask for. `?from=` is optional and comes before the
    fragment — home.html and project.html do not carry it yet, but the pattern has to keep
    matching once they do."""
    return set(re.findall(r'href="/guide(?:\?from=[^"#]*)?#([a-z-]+)"', html))


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
    assert 'href="/guide"' in client.get("/").text, "no way to the guide from the home page"
    # From inside a project, the top bar's Help control carries `?from=` so the Guide can offer
    # an in-app way back — the bare, parameter-free link only appears where there is no project.
    assert f'href="/guide?from=/p/{project}"' in client.get(f"/p/{project}").text, \
        "no way to the guide from a project, or it lost its return path"


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


def test_help_reaches_the_top_bar_on_every_kind_of_page(client, conn, project, grande):
    """F2: Help must stand in the top bar on every page, not only where the rail also carries it
    — the rail disappears below 920px and on pages with no project at all."""
    for url in ("/", f"/p/{project}", f"/p/{project}/m/{grande}"):
        html = client.get(url).text
        assert '<a class="guide-link" href="/guide' in html, f"no top-bar Help control on {url}"


def test_a_skip_link_is_the_first_focusable_thing_on_the_page(client, project):
    """F10: the first thing a keyboard user meets, so they are not made to tab through the whole
    top bar before reaching the workspace."""
    html = client.get(f"/p/{project}").text
    assert html.index('class="skip-link"') < html.index("<header"), \
        "the skip link is not the first focusable element"
    assert 'href="#content"' in html
    assert 'id="content"' in html


def test_a_compact_project_menu_stands_in_for_the_hidden_rail(client, project):
    """F2: below 920px CSS hides `.project-rail` entirely, so Materials, Themes and the record
    need another way to be reached — a `<details>` in the top bar, with no script."""
    html = client.get(f"/p/{project}").text
    assert '<details class="project-menu">' in html
    for target in (f"/p/{project}#materials", f"/p/{project}#themes", f"/p/{project}/record"):
        assert target in html


def test_opening_help_from_a_project_offers_an_in_app_way_back(client, conn, project, grande):
    """F2 acceptance: Help from a project names that project, not just 'the guide'."""
    from app import store

    name = store.project(conn, project)["name"]
    html = client.get(f"/guide?from=/p/{project}").text
    assert f'<a href="/p/{project}">Back to {name}' in html


def test_opening_help_from_a_material_names_the_material(client, conn, project, grande):
    from app import context, store

    title = context._material_title(store.material(conn, grande))
    html = client.get(f"/guide?from=/p/{project}/m/{grande}").text
    assert f'<a href="/p/{project}/m/{grande}">Back to {title}' in html


def test_help_with_no_return_path_offers_all_projects(client):
    """A bookmarked or directly typed `/guide` has nowhere to return to. The Guide must still
    render, and must not claim a project it was never told about."""
    html = client.get("/guide").text
    assert '<a href="/">All projects</a>' in html


@pytest.mark.parametrize("bad_from", [
    "//evil.example/",           # protocol-relative — a browser reads this as another host
    "https://evil.example/p/x",  # another site outright
    "/account",                  # a real local path, but not one of the app's project routes
    "/p/doesnotexist0000",       # shaped like a project route, but not a project that exists
])
def test_an_unsafe_or_unmatched_return_path_falls_back_to_all_projects(client, bad_from):
    html = client.get("/guide", params={"from": bad_from}).text
    assert '<a href="/">All projects</a>' in html
    assert bad_from not in html


def test_the_return_path_checks_access_before_naming_a_project(conn, monkeypatch):
    """A visitor who cannot see a project must not be told its name by the Guide — the same rule
    `store.access` already enforces for every page and every verb."""
    from fastapi.testclient import TestClient

    from app import accounts, main, pages, store

    for mod in (pages, accounts):
        monkeypatch.setattr(mod, "connection", lambda: conn, raising=False)
    client = TestClient(main.app, follow_redirects=False)

    ann = store.create_user(conn, "ann", "battery staple")
    store.create_user(conn, "bob", "purple monkey")
    pid = store.create_project(conn, "Ann's project", focus="", owner_id=ann, method="iterative")

    r = client.post("/login", data={"name": "bob", "password": "purple monkey"})
    assert r.status_code == 303
    html = client.get(f"/guide?from=/p/{pid}").text
    assert '<a href="/">All projects</a>' in html
    assert "Ann's project" not in html


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
