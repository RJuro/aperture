"""P42 — rendering what the new analytical objects say: the overarching tier, the notes a reading
left beside a definition, what a theme is nearest to, and the pairs that may be one theme.

Every row here is written by the test, not by a model. The steps that produce them (PROJECT's
tier, THREAD's fit note, THEMES' nearest) are other packages; what this file holds is that a page
renders whatever they wrote — including the three shapes a model's JSON arrives in when something
has gone wrong, none of which may take the project page down.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import eval_metrics  # noqa: E402

from app import context, store  # noqa: E402


@pytest.fixture
def client(conn, monkeypatch):
    from fastapi.testclient import TestClient
    from app import main, pages
    monkeypatch.setattr(pages, "connection", lambda: conn, raising=False)
    return TestClient(main.app)


def _tier(conn, pid, tier, ungathered=()):
    """The row PROJECT writes: the whole tier as one JSON summary beside the reading."""
    store.save_summary(conn, "project", pid, "overarching",
                       json.dumps({"overarching": tier, "ungathered": list(ungathered)}), None)


def _one(analysed, **over):
    """One overarching entry gathering both of the fixture's themes."""
    return {"name": "Making a living across a move", "gathers": list(analysed["themes"].values()),
            "organising_idea": "Both themes describe how a household kept its income.",
            "boundary": "This one sorts claims about income; the other sorts claims about arrival.",
            "exceptions": "none in the claims shown",
            "argument": "In both interviews the trade is described before the crossing is.",
            **over}


# ---- WP-6a: the overarching tier -------------------------------------------------------------

def test_the_tier_reaches_the_project_page_with_its_themes_linked(client, conn, analysed):
    pid = analysed["pid"]
    _tier(conn, pid, [_one(analysed)])
    html = client.get(f"/p/{pid}").text
    assert "Overarching themes" in html
    assert "Making a living across a move" in html
    assert "Both themes describe how a household kept its income." in html
    assert "This one sorts claims about income" in html
    assert "In both interviews the trade is described before the crossing is." in html
    for name, tid in analysed["themes"].items():
        assert f'/p/{pid}/t/{tid}">{name}' in html, f"{name} is not a link to its theme"


def test_a_theme_the_summary_did_not_place_is_shown_with_its_reason(client, conn, analysed):
    """The gap is the finding: a theme no overarching theme gathers is a fact about the summary,
    and hiding it would leave a researcher unable to ask why."""
    pid, themes = analysed["pid"], analysed["themes"]
    work, leaving = themes["Work and trade"], themes["Leaving and arriving"]
    _tier(conn, pid, [_one(analysed, gathers=[work])],
          [{"id": leaving, "why": "the two materials describe the crossing differently"}])
    html = client.get(f"/p/{pid}").text
    assert "Themes no overarching theme gathers" in html
    assert "the two materials describe the crossing differently" in html
    assert f'/p/{pid}/t/{leaving}">Leaving and arriving' in html


def test_no_row_an_empty_list_and_unreadable_json_each_render_nothing(client, conn, analysed):
    """Three states, none of them an error and all of them ordinary: a project written before the
    tier existed, a set of themes that would not group, and the model's JSON arriving broken."""
    pid = analysed["pid"]
    assert context.project_page(conn, pid)["overarching"] == [], "no row at all"
    assert client.get(f"/p/{pid}").status_code == 200

    for text in ('{"overarching": [], "ungathered": []}', "{not json at all", '"a string"',
                 '{"overarching": 7, "ungathered": null}'):
        store.save_summary(conn, "project", pid, "overarching", text, None)
        got = context.project_page(conn, pid)
        assert got["overarching"] == [] and got["ungathered"] == [], text
        assert client.get(f"/p/{pid}").status_code == 200, text
        assert "Overarching themes" not in client.get(f"/p/{pid}").text, text


def test_an_id_no_live_theme_answers_to_is_dropped_rather_than_linked(client, conn, analysed):
    """A theme merged away after the summary was written would otherwise be a link to nothing."""
    pid, work = analysed["pid"], analysed["themes"]["Work and trade"]
    _tier(conn, pid, [_one(analysed, gathers=[work, "t-gone"])],
          [{"id": "t-also-gone", "why": "not placed by the summary"}])
    got = context.project_page(conn, pid)
    assert [g["id"] for g in got["overarching"][0]["gathers"]] == [work]
    assert got["ungathered"] == []
    assert "t-gone" not in client.get(f"/p/{pid}").text


def test_a_dangling_citation_in_the_argument_is_taken_out_and_a_live_one_becomes_a_link(
        client, conn, analysed):
    """The tier's prose cites claims as the summary does, so it goes through the same filter: an
    id whose claim is no longer live is not a citation, and the brackets go with it."""
    pid = analysed["pid"]
    mo = store.moments(conn, analysed["grande"])[0]
    _tier(conn, pid, [_one(analysed,
                           argument=f"The trade is described first [{mo['id']}].",
                           exceptions="One interview does not [mo0000deadbeef].")])
    html = client.get(f"/p/{pid}").text
    assert f'?theme={mo["theme_id"]}#{mo["sid"]}' in html
    assert f'>{mo["sid"]}<' in html
    assert "mo0000deadbeef" not in html and "[]" not in html


def test_the_tier_reaches_the_record_and_the_markdown_export(client, conn, analysed):
    pid = analysed["pid"]
    mo = store.moments(conn, analysed["grande"])[0]
    _tier(conn, pid, [_one(analysed, argument=f"The trade is described first [{mo['id']}].")],
          [{"id": analysed["themes"]["Leaving and arriving"], "why": "not placed by the summary"}])
    record = client.get(f"/p/{pid}/record").text
    assert "Overarching themes" in record and "Making a living across a move" in record
    assert "not placed by the summary" in record
    assert f'>{mo["sid"]}<' in record, "the record links a citation as the project page does"

    md = client.get(f"/p/{pid}/export.md").text
    assert "### Overarching themes" in md and "#### Making a living across a move" in md
    assert "not placed by the summary" in md
    # A document has no links, so a claim id is printed as the passage a reader can find.
    assert f'[{mo["sid"]}]' in md and mo["id"] not in md


def test_the_theme_page_says_which_overarching_themes_gather_it(client, conn, analysed):
    pid, work = analysed["pid"], analysed["themes"]["Work and trade"]
    assert "Gathered under" not in client.get(f"/p/{pid}/t/{work}").text
    _tier(conn, pid, [_one(analysed, gathers=[work])])
    assert context.theme_page(conn, pid, work)["gathered_under"] == \
        ["Making a living across a move"]
    assert "Gathered under: Making a living across a move" in client.get(f"/p/{pid}/t/{work}").text


# ---- WP-6b: notes, told apart by where they came from -----------------------------------------

def test_a_fit_note_and_a_tension_note_are_told_apart_on_an_open_theme(client, conn, analysed):
    """Both kinds show on an open theme. The section used to be gated on the definition being
    locked, which is exactly when a fit note cannot be written — so nothing printed them."""
    pid, work, grande = analysed["pid"], analysed["themes"]["Work and trade"], analysed["grande"]
    store.add_theme_note(conn, work, grande, None,
                         "the participant sells nothing; she is paid a wage", kind="fit")
    store.add_theme_note(conn, work, analysed["rodwin"], None,
                         "the definition names a trade and this material names an employer",
                         kind="tension")
    assert store.themes_for_material(conn, pid, grande)[0]["hold"] != "frozen"

    html = client.get(f"/p/{pid}/t/{work}").text
    assert "Evidence that challenges this definition" in html
    assert "Materials this definition did not foresee" in html
    assert "From the reading of Grande, M.: the participant sells nothing" in html
    assert "the definition names a trade and this material names an employer" in html

    record = client.get(f"/p/{pid}/record").text
    assert "From the reading of Grande, M.: the participant sells nothing" in record
    assert "Evidence that challenges this definition" in record


def test_a_theme_with_only_tension_notes_does_not_grow_an_empty_fit_heading(client, conn,
                                                                           analysed):
    pid, work = analysed["pid"], analysed["themes"]["Work and trade"]
    store.add_theme_note(conn, work, analysed["grande"], None, "the wage is not a trade")
    html = client.get(f"/p/{pid}/t/{work}").text
    assert "Evidence that challenges this definition" in html
    assert "Materials this definition did not foresee" not in html


# ---- WP-6c: what a theme is nearest to --------------------------------------------------------

def test_nearest_renders_only_once_it_is_set(client, conn, analysed):
    pid, themes = analysed["pid"], analysed["themes"]
    work, leaving = themes["Work and trade"], themes["Leaving and arriving"]
    assert context.theme_page(conn, pid, work)["nearest"] is None
    assert "Most easily confused with" not in client.get(f"/p/{pid}/t/{work}").text

    store.set_nearest(conn, work, leaving,
                      "a passage about pay sorts here, one about the ship there")
    assert context.theme_page(conn, pid, work)["nearest"]["name"] == "Leaving and arriving"
    html = client.get(f"/p/{pid}/t/{work}").text
    assert "Most easily confused with" in html
    assert "a passage about pay sorts here, one about the ship there" in html
    assert f'/p/{pid}/t/{leaving}' in html

    record = client.get(f"/p/{pid}/record").text
    assert "a passage about pay sorts here, one about the ship there" in record
    assert "a passage about pay sorts here" in client.get(f"/p/{pid}/export.md").text


# ---- WP-6d: pairs that may be one theme -------------------------------------------------------

def test_two_themes_that_name_each_other_are_proposed_as_a_possible_duplicate(client, conn,
                                                                             analysed):
    pid, themes = analysed["pid"], analysed["themes"]
    work, leaving = themes["Work and trade"], themes["Leaving and arriving"]
    assert context._duplicates(conn, pid) == []

    store.set_nearest(conn, work, leaving, "pay sorts here")
    assert context._duplicates(conn, pid) == [], "one pointing at the other is not a pair"
    store.set_nearest(conn, leaving, work, "the ship sorts here")
    pairs = context._duplicates(conn, pid)
    assert len(pairs) == 1
    assert {pairs[0]["a"]["id"], pairs[0]["b"]["id"]} == {work, leaving}
    assert "each names the other" in pairs[0]["why"]

    html = client.get(f"/p/{pid}").text
    assert "Possible duplicates" in html
    assert "pay sorts here" in html and "the ship sorts here" in html
    # It proposes and nothing else, and the page says which control does the merging.
    assert "This list changes nothing and starts" in html
    assert "merged only when you run Compare and update themes" in html


def test_two_themes_that_gather_half_the_same_codes_are_proposed_too(conn, analysed, quote):
    """Jaccard at exactly the threshold: two codes each, one of them shared, is 1 of 3 — under it;
    a second shared code is 2 of 2 — over it."""
    pid, themes, grande = analysed["pid"], analysed["themes"], analysed["grande"]
    work, leaving = themes["Work and trade"], themes["Leaving and arriving"]
    sids = [quote(grande, at=40 + i * 7)[0] for i in range(4)]
    names = ("paying to cross", "the stall", "the ship", "the wage")
    store.save_codes(conn, pid, grande, [{"name": n, "definition": "", "sids": [s]}
                                         for n, s in zip(names, sids)])
    by_name = {c["name"]: c["id"] for c in store.codebook(conn, pid)}
    ids = [by_name[n] for n in names]
    store.save_theme(conn, pid, tid=work, name="Work and trade", gist="how a living is made",
                     code_ids=ids[:2])
    store.save_theme(conn, pid, tid=leaving, name="Leaving and arriving", gist="the crossing",
                     code_ids=[ids[0], ids[2], ids[3]])
    assert context._duplicates(conn, pid) == [], "1 of 3 codes shared is under the threshold"

    store.save_theme(conn, pid, tid=leaving, name="Leaving and arriving", gist="the crossing",
                     code_ids=ids[:2])
    pairs = context._duplicates(conn, pid)
    assert len(pairs) == 1 and "2 of the 2 codes" in pairs[0]["why"]


# ---- WP-6e: the prose counts, summed per record -----------------------------------------------

def test_the_prose_counts_are_summed_beside_the_totalising_words(conn, analysed):
    pid = analysed["pid"]
    store.save_summary(conn, "theme", analysed["themes"]["Work and trade"], "reading",
                       "The work is not merely work: the trade survives as a habit.")
    m = eval_metrics.from_db(conn, pid)
    assert m["prose_style"]["contrast"] == 1
    assert m["prose_style"]["abstract_agent"] == 1
    assert m["prose_style"]["total"] == sum(
        v for k, v in m["prose_style"].items() if k != "total")
    # Every kind is emitted, so two records with different faults still line up in `--compare`.
    assert m["prose_style"]["unscoped"] == 0


def test_a_record_and_its_database_count_the_same_prose(conn, analysed, tmp_path):
    from app import context as ctx, pages
    pid = analysed["pid"]
    store.save_summary(conn, "theme", analysed["themes"]["Work and trade"], "reading",
                       "The work is not merely work: the trade survives as a habit.")
    record = tmp_path / "record.md"
    record.write_text(pages._render("export.md", ctx.export(conn, pid)), encoding="utf-8")
    assert eval_metrics.from_record(record)["prose_style"] == \
        eval_metrics.from_db(conn, pid)["prose_style"]


def test_plain_prose_counts_nothing_and_says_so_as_a_nought(conn, analysed):
    m = eval_metrics.from_db(conn, analysed["pid"])
    assert m["prose_style"]["total"] == 0
    assert "prose_style.total" in eval_metrics.compare(m, m)
