"""P20 — the theme overview stops spreading.

`store.live_themes` orders by name, which the record and the export depend on. On the project
page that meant a theme every material carries, with twenty claims behind it, printed the same
size and in the same place as one a single reading mentioned twice: the reader did the ranking.
"""
from __future__ import annotations

import pytest

from app import context, store


@pytest.fixture
def client(conn, monkeypatch):
    from fastapi.testclient import TestClient
    from app import main, pages
    monkeypatch.setattr(pages, "connection", lambda: conn, raising=False)
    return TestClient(main.app)


def _claims(conn, quote, mid, tid, n, at):
    ms = [{"claim": f"claim {k}", "anchor": " ".join(quote(mid, at=at + k * 7)[1].split()[:8]),
           "sid": quote(mid, at=at + k * 7)[0]} for k in range(n)]
    store.save_moments(conn, mid, tid, ms)


def test_themes_are_ordered_by_reach_then_claims_then_name(conn, quote, analysed):
    """Two materials each with three claims under both of the fixture's themes, plus one theme
    carried by both with more claims and one motif carried by a single material."""
    pid, grande, rodwin = analysed["pid"], analysed["grande"], analysed["rodwin"]
    wide = store.save_theme(conn, pid, tid=None, name="Zebra crossing", gist="last by name",
                            code_ids=[])
    for mid in (grande, rodwin):
        _claims(conn, quote, mid, wide, 4, at=200)
    motif = store.save_theme(conn, pid, tid=None, name="Alpha motif", gist="first by name",
                             code_ids=[])
    _claims(conn, quote, grande, motif, 5, at=300)

    rows = context.project_page(conn, pid)["themes"]
    assert [r["name"] for r in rows] == ["Zebra crossing", "Leaving and arriving",
                                         "Work and trade", "Alpha motif"], (
        "widest reach first, then claims, then name — and a one-material motif last however "
        "many claims it has")
    assert [(r["reach"], r["claims"]) for r in rows] == [(2, 8), (2, 6), (2, 6), (1, 5)]
    # Three steps only, and carried-by-every-material is the largest.
    assert [r["tier"] for r in rows] == [1, 1, 1, 3]
    assert [r["single"] for r in rows] == [False, False, False, True]


def test_a_theme_with_no_claims_yet_does_not_take_the_page_down(client, conn, project):
    """Themes are named before a single claim is read, so every bar is measured against nought."""
    store.save_theme(conn, project, tid=None, name="Named, not yet read", gist="no claims",
                     code_ids=[])
    assert client.get(f"/p/{project}").status_code == 200


def test_the_head_says_how_far_the_reading_has_got(conn, quote, analysed):
    """One material taken through all four steps, one part-way, one added and not read at all."""
    pid, grande = analysed["pid"], analysed["grande"]
    store.save_summary(conn, "material", grande, "angles", "Three angles on the crossing.")
    store.save_codes(conn, pid, grande, [{"name": "paying to cross", "definition": "",
                                          "sids": [quote(grande, at=40)[0]]}])
    store.add_material(conn, pid, "Waiting", "A short unread material. It has two sentences.")
    assert context.project_page(conn, pid)["reading"] == {"done": 1, "active": 0, "failed": 0,
                                                          "waiting": 2}
