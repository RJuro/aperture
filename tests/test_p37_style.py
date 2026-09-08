"""The prose rules, the counter that watches for their absence, and the two columns beside them.

The style block is one file included by every prompt that writes prose a researcher reads. What
these tests hold: the file supplies it and no caller can, a fragment carries no corpus of ours,
the counter counts what the material said separately from what the reading wrote, and a database
made before either column comes up with both.
"""
from __future__ import annotations

import sqlite3

import pytest

from app import db, llm, prose, store

FRAGMENTS = ("_style", "_style_short")


# ---- the block itself ---------------------------------------------------------------------

def test_both_fragments_exist_and_say_how_to_write():
    for name in FRAGMENTS:
        text = (llm.Path(llm.__file__).parent / "prompts" / f"{name}.md").read_text()
        assert text.strip(), f"{name} is empty"
        assert "HOW TO WRITE" in text
        # The rules that do the work in every domain: a subject, a scope, and no manufactured
        # contrast. `_style` adds verbs, fragments, hedges and figures on top of these.
        assert "Subject:" in text and "Scope," in text and "No contrast for effect" in text


def test_a_fragment_names_no_corpus_the_instrument_is_judged_on():
    """A fragment reaches every prompt that includes it, so a domain word here would teach the
    reading a vocabulary before it opened the material. `test_p9_law5` holds the same rule over
    every template; this says it of the block specifically, because it travels furthest."""
    for name in FRAGMENTS:
        text = (llm.Path(llm.__file__).parent / "prompts" / f"{name}.md").read_text().lower()
        for word in ("ellis island", "migrat", "emigrat", "immigrant", "grande", "rodwin"):
            assert word not in text, f"{name}.md carries {word!r}"


# ---- the reserved slot --------------------------------------------------------------------

@pytest.fixture
def prompts(tmp_path, monkeypatch):
    """A prompts directory of this test's own, so nothing it writes lands in `app/prompts`."""
    d = tmp_path / "app" / "prompts"
    d.mkdir(parents=True)
    for name in FRAGMENTS:
        real = (llm.Path(llm.__file__).parent / "prompts" / f"{name}.md").read_text()
        (d / f"{name}.md").write_text(real)
    monkeypatch.setattr(llm, "__file__", str(tmp_path / "app" / "llm.py"))
    return d


def test_the_file_supplies_the_block_and_the_caller_never_passes_it(prompts):
    (prompts / "p.md").write_text("Write it up.\n\n{{style}}\n---\nTHE MATERIAL\n\n{{material}}")
    system, user = llm.prompt("p", material="S001 a line")
    assert "HOW TO WRITE" in system
    assert "Subject: a person, a group, a material, or the claims" in system
    assert "{{style}}" not in system
    assert user == "THE MATERIAL\n\na line" or "a line" in user


def test_the_short_block_is_the_shorter_one(prompts):
    (prompts / "p.md").write_text("Name it.\n\n{{style_short}}\n---\n{{themes}}")
    system, _ = llm.prompt("p", themes="t1")
    assert "HOW TO WRITE" in system
    # the four rules that bear on a name or a note, and not the worked examples
    assert "Not this:" not in system
    assert len(system.split()) < 160


def test_a_caller_that_passes_the_block_is_the_drift_this_catches(prompts):
    (prompts / "p.md").write_text("Write it up.\n\n{{style}}\n---\n{{material}}")
    with pytest.raises(llm.LLMError) as e:
        llm.prompt("p", material="x", style="be terse")
    assert "filled from its own file" in str(e.value)


def test_a_prompt_without_the_slot_is_untouched(prompts):
    (prompts / "p.md").write_text("Do the thing.\n---\n{{material}}")
    system, _ = llm.prompt("p", material="x")
    assert "HOW TO WRITE" not in system


def test_a_missing_ordinary_slot_still_fails(prompts):
    """The block is the exception to the loader's law, not a hole in it."""
    (prompts / "p.md").write_text("x\n\n{{style}}\n---\n{{material}} {{focus}}")
    with pytest.raises(llm.LLMError) as e:
        llm.prompt("p", material="x")
    assert "unfilled slots ['focus']" in str(e.value)


# ---- the counter --------------------------------------------------------------------------

def test_it_counts_the_shapes_the_rules_name():
    assert prose.count("Violence is a backdrop, not an event.")["contrast"] >= 1
    assert prose.count("It was not merely work.")["contrast"] >= 1
    assert prose.count("The crossing survives as fragments.")["abstract_agent"] >= 1
    assert prose.count("What one theme does to another matters.")["announce"] >= 1
    assert prose.count("The corpus shows a pattern of refusal.")["unscoped"] >= 1


def test_it_counts_a_claim_made_of_every_case():
    """PROJECT rule 5's negative half. A researcher reading her own corpus back found the summary
    saying outputs were "never accepted at face value" where one participant accepted most of one
    and estimated its error himself — the positive quantifiers were named in the rule and the
    negative was not, so nothing on the page had anything to say about it."""
    assert prose.count("The outputs are never accepted at face value.")["universal"] >= 1
    assert prose.count("No participant queries the figure.")["universal"] >= 1
    assert prose.count("None of the interviews raise cost.")["universal"] >= 1
    assert prose.count("In every case the tool is checked first.")["universal"] >= 1


def test_a_universal_the_material_itself_said_is_not_counted():
    """The rules govern the words the reading writes, never the words the material said."""
    assert "universal" not in prose.count('She said "I never trust it" and moved on.')


def test_plain_prose_counts_nothing():
    """The ordinary answer, and it reads as one."""
    clean = ("Four of the six nurses describe handover as a checklist read aloud. Two say it "
             "leaves out what they most need to know. The claims do not say why.")
    assert prose.count(clean) == {}
    assert prose.note(clean) is None


def test_what_the_material_said_is_not_what_the_reading_wrote():
    """A quotation is the material talking. The rules govern the prose around it."""
    quoted = 'The speaker says "it was not work but duty" and the claims do not say why.'
    assert prose.count(quoted) == {}


def test_the_note_says_what_it_counted_and_never_that_the_prose_is_wrong():
    note = prose.note("Violence is a backdrop, not an event. The corpus shows this.")
    assert note and note.startswith("style: ")
    assert "contrast" in note and "unscoped" in note
    for verdict in ("bad", "wrong", "rewrite", "must"):
        assert verdict not in note.lower()


def test_it_counts_across_several_pieces_of_prose_at_once():
    a, b = "It was not merely work.", "The corpus shows a pattern."
    assert prose.count(a, b) == {**prose.count(a), **prose.count(b)}


# ---- the two columns ----------------------------------------------------------------------

def test_a_database_made_before_the_columns_comes_up_with_them(tmp_path):
    """A theme_note written before there were kinds was a tension: nothing else could write one."""
    path = tmp_path / "old.db"
    old = sqlite3.connect(path)
    old.execute("CREATE TABLE theme (id TEXT PRIMARY KEY, project_id TEXT NOT NULL, "
                "name TEXT NOT NULL, gist TEXT DEFAULT '', status TEXT NOT NULL DEFAULT 'live', "
                "merged_into TEXT)")
    old.execute("CREATE TABLE theme_note (id TEXT PRIMARY KEY, theme_id TEXT NOT NULL, "
                "material_id TEXT, run_id TEXT, text TEXT NOT NULL, created_at TEXT NOT NULL)")
    old.execute("INSERT INTO theme (id, project_id, name) VALUES ('t1','p1','One')")
    old.execute("INSERT INTO theme_note (id, theme_id, text, created_at) "
                "VALUES ('tn1','t1','the definition did not foresee this','2026-01-01')")
    old.commit()
    old.close()

    conn = db.connect(path)
    try:
        assert conn.execute("SELECT kind FROM theme_note WHERE id='tn1'").fetchone()[0] == "tension"
        cols = {r[1] for r in conn.execute("PRAGMA table_info(theme)")}
        assert {"nearest_id", "nearest_note"} <= cols
        row = conn.execute("SELECT nearest_id, nearest_note FROM theme WHERE id='t1'").fetchone()
        # Nobody had said what it was nearest to, and the migration does not invent an answer.
        assert tuple(row) == (None, "")
    finally:
        conn.close()


def test_a_fit_note_and_a_tension_note_are_told_apart(conn, project):
    tid = store.save_theme(conn, project, tid=None, name="Handover",
                           gist="How a shift hands over.", code_ids=[])
    store.add_theme_note(conn, tid, None, None, "pulls against the definition")
    store.add_theme_note(conn, tid, None, None, "carried by an organisation, not a shift",
                         kind="fit")
    kinds = sorted(r["kind"] for r in store.theme_notes(conn, tid))
    assert kinds == ["fit", "tension"]


def test_what_a_theme_is_nearest_to_is_written_and_read_back(conn, project):
    a = store.save_theme(conn, project, tid=None, name="Handover",
                         gist="How a shift hands over.", code_ids=[])
    b = store.save_theme(conn, project, tid=None, name="Rostering",
                         gist="How shifts are assigned.", code_ids=[])
    store.set_nearest(conn, a, b, "this is the handing over; that is who is on")
    row = conn.execute("SELECT nearest_id, nearest_note FROM theme WHERE id=?", (a,)).fetchone()
    assert row["nearest_id"] == b
    assert "who is on" in row["nearest_note"]


def test_a_theme_nothing_is_close_to_keeps_none(conn, project):
    """Not every theme has a neighbour, and `None` is an answer rather than a gap."""
    a = store.save_theme(conn, project, tid=None, name="Handover",
                         gist="How a shift hands over.", code_ids=[])
    store.set_nearest(conn, a, None, "")
    row = conn.execute("SELECT nearest_id FROM theme WHERE id=?", (a,)).fetchone()
    assert row["nearest_id"] is None
