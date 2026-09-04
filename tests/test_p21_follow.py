"""P21 — following a theme only where the reading found it. `synth._marked_here`, `store.follow`,
the two absences on the theme page, and the two wordings in the account prompt.

A four-interview record came back with twelve themes, eleven of them claimed in all four
materials. Half of that was the ceiling; the other half was here — after the first material every
live theme was followed through every later one whether its codes had fired there or not, and a
reader sent to find a theme finds it. On the benchmark twelve theme-and-material pairs had no code
hit at all and nine of them still produced claims: a quarter of the whole record.

So a theme is followed through a material only where the reading of that material marked something
the theme gathers, and the skip is written down. Three states per theme and material, and the
researcher must be able to tell them apart (PLAN.md §3, law 2):

    line       a line holds here
    thin       it was looked for and what came back was set aside
    skipped    it was never looked for — none of this theme's codes marked this material
"""
from __future__ import annotations

import pytest

from app import llm, store

synth = pytest.importorskip("app.engine.synth")
account = pytest.importorskip("app.engine.account")


@pytest.fixture(autouse=True)
def _gate_on(monkeypatch):
    """The skip is opt-in (docs/EVAL.md pass 3): these tests are about what it does when it is on.
    The one test of the default turns it back off itself."""
    monkeypatch.setenv("APERTURE_FOLLOW", "marked")


@pytest.fixture
def client(conn, monkeypatch):
    from fastapi.testclient import TestClient

    from app import main, pages
    monkeypatch.setattr(main, "conn", conn, raising=False)
    monkeypatch.setattr(pages, "connection", lambda: conn, raising=False)
    return TestClient(main.app)


@pytest.fixture
def split(conn, project, grande, rodwin, quote):
    """Two materials, two themes, and one code each — the Grande code marked only in Grande, the
    Rodwin code only in Rodwin. So each theme has exactly one material it may be followed through
    and exactly one it may not."""
    for mid in (grande, rodwin):
        store.save_frame(conn, mid, kind="interview", display="turns", title=f"M{mid[-4:]}",
                         speakers=[], segments=[])
        store.save_summary(conn, "material", mid, "orientation", "A 1978 oral history.")
    ids = {}
    for name, mid in (("Grande work", grande), ("Rodwin work", rodwin)):
        store.save_codes(conn, project, mid, [{"name": name, "definition": "making a living",
                                               "sids": [store.sentences(conn, mid)[5][0]]}])
        cid = [c["id"] for c in store.codebook(conn, project) if c["name"] == name][0]
        ids[mid] = store.save_theme(conn, project, tid=None, name=name, gist="a living",
                                    code_ids=[cid])
    return {"pid": project, "grande": grande, "rodwin": rodwin,
            "here": ids[grande], "elsewhere": ids[rodwin]}


def _moments(quote, mid, n=5, at=40):
    return [{"claim": f"claim {i}", "anchor": " ".join(quote(mid, at=at + i * 9)[1].split()[:8]),
             "sid": quote(mid, at=at + i * 9)[0]} for i in range(n)]


def test_a_theme_whose_codes_did_not_fire_here_is_not_followed_through_this_material(
        split, conn, model, quote):
    """The whole point. One call goes out, for the theme this material actually marked; the other
    theme is not asked about at all, and the run says so in the words a researcher reads."""
    model.queue({"moments": _moments(quote, split["grande"], 5)})     # the one line that is asked
    model.queue({"verdicts": []})
    model.queue({"summary": "what the reading found", "questions": "what remains?", "people": []})
    model.queue({"verdicts": []})

    said: list[str] = []
    with llm.reporting(said.append):
        synth.doc(conn, split["grande"])

    assert len([c for c in model.calls if c["label"] == "thread"]) == 1
    assert split["elsewhere"] not in model.shown("thread")
    outcomes = store.followed(conn, split["pid"])
    assert outcomes[(split["elsewhere"], split["grande"])] == "skipped"
    assert outcomes[(split["here"], split["grande"])] == "line", "the followed theme held a line"
    assert store.thread(conn, split["grande"], split["here"]), "and its claims were written"
    assert store.thread(conn, split["grande"], split["elsewhere"]) == []
    assert "1 of 1 lines written · 1 not looked for" in said


def test_a_theme_with_no_codes_at_all_is_still_followed(conn, project, grande, model, quote):
    """No evidence either way. A theme that gathers nothing says nothing about this material, and
    a theme named by a researcher before any code was grouped under it would otherwise never be
    looked for anywhere."""
    store.save_frame(conn, grande, kind="interview", display="turns", title="G", speakers=[],
                     segments=[])
    tid = store.save_theme(conn, project, tid=None, name="Work", gist="a living", code_ids=[])
    model.queue({"moments": _moments(quote, grande, 5)})
    model.queue({"verdicts": []})
    model.queue({"summary": "s", "questions": "q", "people": []})
    model.queue({"verdicts": []})
    synth.doc(conn, grande)
    assert store.followed(conn, project)[(tid, grande)] == "line"


def test_a_line_asked_for_by_a_person_is_written_wherever_they_ask(split, conn, model, quote):
    """`only_theme` is a rerun of one line or a reaction to one, and the answer to a person is not
    silence. The theme's codes never fired in this material and it is followed all the same."""
    model.queue({"moments": _moments(quote, split["rodwin"], 5)})
    model.queue({"verdicts": []})
    synth.doc(conn, split["rodwin"], only_theme=split["here"])
    assert [c["label"] for c in model.calls] == ["thread", "verify"]
    assert store.followed(conn, split["pid"])[(split["here"], split["rodwin"])] == "line"
    assert store.thread(conn, split["rodwin"], split["here"])


def test_a_line_that_was_looked_for_and_set_aside_is_told_apart_from_one_never_looked_for(
        split, conn, model, quote):
    """Both leave no claim behind, and until this was recorded the record called both of them
    absence. Three claims is under the floor, so the line is looked for and set aside."""
    model.queue({"moments": _moments(quote, split["grande"], 3)})
    model.queue({"summary": "s", "questions": "q", "people": []})
    synth.doc(conn, split["grande"])
    outcomes = store.followed(conn, split["pid"])
    assert outcomes[(split["here"], split["grande"])] == "thin"
    assert outcomes[(split["elsewhere"], split["grande"])] == "skipped"


def test_the_theme_page_puts_the_two_absences_under_their_own_headings(split, client, conn, model,
                                                                      quote):
    model.queue({"moments": _moments(quote, split["grande"], 5)})
    model.queue({"verdicts": []})
    model.queue({"summary": "s", "questions": "q", "people": []})
    model.queue({"verdicts": []})
    synth.doc(conn, split["grande"])

    html = client.get(f'/p/{split["pid"]}/t/{split["elsewhere"]}').text
    grande, rodwin = store.material(conn, split["grande"]), store.material(conn, split["rodwin"])
    section = html.split("Materials with no claims under this theme")[-1]
    under = section.split("Not looked for here — none of this theme's codes marked these")
    assert len(under) == 2, "the heading a skip is named under"
    assert grande["title"] in under[1] and grande["title"] not in under[0]
    # Rodwin has not been read at all, and reads as looked-for: a material with no row is a
    # material read before any of this was recorded, and that is what the page used to say.
    assert "Looked for and found too thin" in under[0] and rodwin["title"] in under[0]

    from app import context
    absent = context.theme_page(conn, split["pid"], split["elsewhere"])["absent"]
    assert {m["material_id"]: m["looked_for"] for m in absent} == {split["grande"]: False,
                                                                   split["rodwin"]: True}


def test_the_record_says_looked_for_beside_every_absence_it_names(split, conn, model, quote):
    """The contract the reading record reads: every entry of a theme's `absent` carries
    `looked_for`, so the record can name the two silences apart without asking again."""
    from app import context
    model.queue({"moments": _moments(quote, split["grande"], 5)})
    model.queue({"verdicts": []})
    model.queue({"summary": "s", "questions": "q", "people": []})
    model.queue({"verdicts": []})
    synth.doc(conn, split["grande"])

    themes = context.export(conn, split["pid"])["themes"]
    mine = [t for t in themes if t["id"] == split["elsewhere"]][0]
    assert all("looked_for" in m for m in mine["absent"])
    assert {m["material_id"]: m["looked_for"] for m in mine["absent"]} == {split["grande"]: False,
                                                                          split["rodwin"]: True}


def test_the_account_is_told_which_kind_of_nothing_each_material_is(split, conn, model, quote):
    """Rule 5 of the account prompt only works if the block under it says which is which. Told
    only 'this theme does not appear here', the model writes the silence up as absence — and one
    of the two silences is a fact about where the reading went."""
    for mid, tid in ((split["grande"], split["here"]), (split["rodwin"], split["elsewhere"])):
        model.queue({"moments": _moments(quote, mid, 5)})
        model.queue({"verdicts": []})
        model.queue({"summary": "s", "questions": "q", "people": []})
        model.queue({"verdicts": []})
        synth.doc(conn, mid)
        assert store.thread(conn, mid, tid)
    # A person then asks for the Grande theme's line through Rodwin, and it comes back too thin:
    # the same material, now looked for and set aside rather than never looked for.
    model.queue({"moments": _moments(quote, split["rodwin"], 3)})
    synth.doc(conn, split["rodwin"], only_theme=split["here"])

    def block(tid) -> str:
        model.queue({"account": "The claims say what they say."})
        account.run(conn, split["pid"], tid)
        return model.shown("account").rsplit("WHERE THIS THEME DOES NOT APPEAR", 1)[1]

    assert "LOOKED FOR AND TOO THIN" in block(split["here"])
    assert "NOT LOOKED FOR HERE — none of this theme's codes marked this material" \
        in block(split["elsewhere"])


def test_a_theme_renamed_after_the_skip_still_reads_as_not_looked_for(split, conn, model, quote):
    """Why this is a row and not a note in the run's own words: the note names the theme, and the
    researcher renames the theme."""
    model.queue({"moments": _moments(quote, split["grande"], 5)})
    model.queue({"verdicts": []})
    model.queue({"summary": "s", "questions": "q", "people": []})
    model.queue({"verdicts": []})
    synth.doc(conn, split["grande"])

    store.save_theme(conn, split["pid"], tid=split["elsewhere"], name="Something else entirely",
                     gist="a living", code_ids=[])
    assert store.followed(conn, split["pid"])[(split["elsewhere"], split["grande"])] == "skipped"


def test_by_default_every_live_theme_is_followed_whatever_its_codes_did(split, conn, model,
                                                                        quote, monkeypatch):
    """The skip is opt-in. Twenty-four lines judged blind (docs/EVAL.md pass 3) found the unmarked
    ones weaker as a group and four of twelve among the best in the set; a default that deletes a
    third of the good lines is not a default. Unset, both themes are asked about."""
    monkeypatch.delenv("APERTURE_FOLLOW", raising=False)
    model.queue({"moments": _moments(quote, split["grande"], 5)})
    model.queue({"moments": _moments(quote, split["grande"], 5, at=120)})
    model.queue({"verdicts": []})
    model.queue({"summary": "what the reading found", "questions": "what remains?", "people": []})
    model.queue({"verdicts": []})

    said: list[str] = []
    with llm.reporting(said.append):
        synth.doc(conn, split["grande"])

    assert len([c for c in model.calls if c["label"] == "thread"]) == 2
    outcomes = store.followed(conn, split["pid"])
    assert "skipped" not in outcomes.values()
    assert outcomes[(split["elsewhere"], split["grande"])] in ("line", "thin")
    assert not any("not looked for" in s for s in said)
