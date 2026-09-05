"""P26 — a failed step changes nothing, a completed one replaces everything it touched.

The audit of 5 September 2026 (findings 5, 9 and 11; Astra-review AR-02, AR-05, AR-06) found four
ways this instrument could end up holding half an old analysis beside half a new one, or a record
saying one thing while the database said another:

    READ cleared a material's code hits BEFORE the call went out, so a 429 took the previous
    coding with it and every theme left holding an empty code lost the link as well

    a THREAD answer under the four-claim floor was thrown away without superseding anything, so
    the follow row said `thin` while the claims it was about were still live on the page — and a
    valid answer of one to three sound observations disappeared as a group

    VERIFY wrote a verdict for every claim it had asked about, so an answer that ruled on nothing
    read as a clean bill of health and could lift a standing `partly` off a claim

    a candidate theme that gathered no code at all passed the gate and was followed into every
    material in the corpus, where a reader sent to find a theme finds it

Each test here asserts the repaired behaviour. No test reaches a model.
"""
from __future__ import annotations

import pytest

from app import llm, store

read = pytest.importorskip("app.engine.read")
synth = pytest.importorskip("app.engine.synth")
verify = pytest.importorskip("app.engine.verify")


@pytest.fixture
def ready(conn, project, grande):
    store.save_frame(conn, grande, kind="interview", display="turns", title="Grande",
                     speakers=[{"label": "GRANDE", "name": "M. Grande", "role": "participant"}],
                     segments=[])
    store.save_summary(conn, "material", grande, "orientation", "A 1978 oral history.")
    tid = store.save_theme(conn, project, tid=None, name="Work", gist="a living", code_ids=[])
    return {"pid": project, "mid": grande, "tid": tid}


def _moments(quote, mid, n=5, at=40):
    return [{"claim": f"claim {i}", "anchor": " ".join(quote(mid, at=at + i * 9)[1].split()[:8]),
             "sid": quote(mid, at=at + i * 9)[0]} for i in range(n)]


def _doc(model, conn, pid, moments, summary="an account of this line"):
    """The answers one full DOC asks for: the line, the check of its claims, the summary, the
    check of that summary."""
    model.queue({"moments": moments, "summary": summary},
                {"verdicts": []},
                {"summary": "what the reading found", "questions": "", "people": []},
                {"verdicts": []})


# ---- READ: the coding survives a provider failure ---------------------------------------------

def _outage(*a, **k):
    raise llm.LLMError("synthetic outage")


def test_a_read_that_fails_leaves_the_coding_and_its_theme_links_alone(ready, conn, model,
                                                                       monkeypatch):
    """The hits were cleared before the model was even asked. A timeout then left the material
    uncoded, and every code the clearing emptied lost its place in every theme with it."""
    sids = [s for s, _ in store.sentences(conn, ready["mid"])[:3]]
    model.queue({"codes": [{"code": {"name": "Making a living", "definition": "work"},
                            "sids": sids}]})
    read.run(conn, ready["mid"])
    before = {(h["name"], h["sid"]) for h in store.hits(conn, ready["mid"])}
    cid = [c["id"] for c in store.codebook(conn, ready["pid"])][0]
    store.save_theme(conn, ready["pid"], tid=ready["tid"], name="Work", gist="a living",
                     code_ids=[cid])
    assert before and store.theme_codes(conn, ready["tid"])

    monkeypatch.setattr(llm, "chat_json", _outage)
    with pytest.raises(llm.LLMError):
        read.run(conn, ready["mid"])
    assert {(h["name"], h["sid"]) for h in store.hits(conn, ready["mid"])} == before
    assert store.theme_codes(conn, ready["tid"]), "the theme kept the code it gathered"


def test_a_read_that_answers_replaces_the_whole_coding_at_once(ready, conn, model):
    sids = [s for s, _ in store.sentences(conn, ready["mid"])[:3]]
    model.queue({"codes": [{"code": {"name": "Making a living", "definition": "work"},
                            "sids": sids[:1]}]},
                {"codes": [{"code": {"name": "The crossing", "definition": "leaving"},
                            "sids": sids[1:]}]})
    read.run(conn, ready["mid"])
    read.run(conn, ready["mid"])
    assert {h["name"] for h in store.hits(conn, ready["mid"])} == {"The crossing"}


# ---- THREAD: a completed empty answer supersedes, a malformed one does not --------------------

def test_a_completed_empty_line_supersedes_the_claims_that_were_there(ready, conn, model, quote):
    """The floor returned before `save_moments`, so the run recorded `thin` while every claim of
    the reading it replaced was still live under the theme."""
    _doc(model, conn, ready["pid"], _moments(quote, ready["mid"], 5))
    synth.doc(conn, ready["mid"])
    assert len(store.thread(conn, ready["mid"], ready["tid"])) == 5

    model.queue({"moments": [], "summary": "nothing held here"},
                {"summary": "what the reading found", "questions": "", "people": []})
    synth.doc(conn, ready["mid"])
    assert store.thread(conn, ready["mid"], ready["tid"]) == []
    assert store.followed(conn, ready["pid"])[(ready["tid"], ready["mid"])] == "thin"


def test_an_answer_with_no_moments_field_changes_nothing_at_all(ready, conn, model, quote):
    """A malformed answer is a failed attempt, not a reassessment that found nothing. The claims
    stand and so does the follow row that was written about them."""
    _doc(model, conn, ready["pid"], _moments(quote, ready["mid"], 5))
    synth.doc(conn, ready["mid"])
    before = [dict(m) for m in store.thread(conn, ready["mid"], ready["tid"])]
    follow = store.followed(conn, ready["pid"])[(ready["tid"], ready["mid"])]

    model.queue({"summary": "an answer that forgot its moments"})
    out = synth.doc(conn, ready["mid"], only_theme=ready["tid"])
    assert [dict(m) for m in store.thread(conn, ready["mid"], ready["tid"])] == before
    assert store.followed(conn, ready["pid"])[(ready["tid"], ready["mid"])] == follow
    assert any("carried no moments" in d for d in out["dropped"])


def test_a_thread_call_that_raises_leaves_the_claims_and_the_summary_alone(ready, conn, model,
                                                                           quote, monkeypatch):
    _doc(model, conn, ready["pid"], _moments(quote, ready["mid"], 5))
    synth.doc(conn, ready["mid"])
    before = [dict(m) for m in store.thread(conn, ready["mid"], ready["tid"])]
    account = store.get_summary(conn, "thread", f'{ready["mid"]}:{ready["tid"]}', "reading")["text"]

    monkeypatch.setattr(llm, "chat_json", _outage)
    with pytest.raises(llm.LLMError):
        synth.doc(conn, ready["mid"], only_theme=ready["tid"])
    assert [dict(m) for m in store.thread(conn, ready["mid"], ready["tid"])] == before
    assert store.get_summary(conn, "thread", f'{ready["mid"]}:{ready["tid"]}',
                             "reading")["text"] == account


# ---- the four-claim floor is a label, not a rule about evidence -------------------------------

def test_a_line_of_two_claims_is_kept_live_and_reads_as_sparse(ready, conn, model, quote):
    """One to three sound observations used to go as a group, while a line cut below four by the
    check that runs afterwards stayed. The count is what the page marks it with, nothing more."""
    _doc(model, conn, ready["pid"], _moments(quote, ready["mid"], 2))
    out = synth.doc(conn, ready["mid"])

    kept = store.thread(conn, ready["mid"], ready["tid"])
    assert len(kept) == 2 < synth.MIN_MOMENTS, "the page reads `sparse` off exactly this"
    assert store.followed(conn, ready["pid"])[(ready["tid"], ready["mid"])] == "line"
    assert not any("set aside" in d for d in out["dropped"]), "sparse is not an exclusion"
    assert store.get_summary(conn, "thread", f'{ready["mid"]}:{ready["tid"]}',
                             "reading")["text"] == "an account of this line"


def test_the_thread_prompt_asks_for_a_ceiling_and_no_floor(ready, conn, model, quote):
    """The floor was in the prompt as well as in Python. `llm.prompt` refuses a slot the template
    does not use, so the two cannot drift apart again."""
    _doc(model, conn, ready["pid"], _moments(quote, ready["mid"], 5))
    synth.doc(conn, ready["mid"])
    shown = model.shown("thread")
    assert f"At most {synth.MAX_MOMENTS} moments" in shown
    assert "is kept and marked sparse, and it is a finding." in shown
    with pytest.raises(llm.LLMError):
        llm.prompt("thread", theme="", codes="", claimed="", focus="", frame="", feedback="",
                   material="", min_moments=4, max_moments=14, summary_words=90)


# ---- VERIFY: only the verdicts that came back are written ------------------------------------

def test_a_verdict_that_never_came_back_cannot_clear_a_standing_qualification(ready, conn, model,
                                                                              quote):
    """An empty answer read as a clean bill of health for the whole batch, and lifted the mark a
    researcher had already been warned by."""
    _doc(model, conn, ready["pid"], _moments(quote, ready["mid"], 5))
    synth.doc(conn, ready["mid"])
    marked = store.thread(conn, ready["mid"], ready["tid"])[0]
    store.mark_support(conn, [(marked["id"], "partly", "'steady' is not in the passage")])

    model.queue({"verdicts": []})
    verify.run(conn, ready["mid"])
    row = store.moment(conn, marked["id"])
    assert (row["support"], row["support_note"]) == ("partly", "'steady' is not in the passage")


def test_a_claim_nobody_ruled_on_is_recorded_unchecked(ready, conn, model, quote):
    _doc(model, conn, ready["pid"], _moments(quote, ready["mid"], 5))
    synth.doc(conn, ready["mid"])          # its check answered nothing
    assert {m["support"] for m in store.thread(conn, ready["mid"], ready["tid"])} == {"unchecked"}


def test_only_the_subset_the_check_left_out_is_asked_about_again(ready, conn, model, quote):
    """A reply cut off part way is worth asking again — for what it missed, once, and no more."""
    _doc(model, conn, ready["pid"], _moments(quote, ready["mid"], 5))
    synth.doc(conn, ready["mid"])
    rows = store.thread(conn, ready["mid"], ready["tid"])
    judged, missed = rows[:2], rows[2:]

    model.queue({"verdicts": [{"id": m["id"], "verdict": "supported", "why": ""} for m in judged]},
                {"verdicts": [{"id": missed[0]["id"], "verdict": "partly", "why": "'often'"}]})
    verify.run(conn, ready["mid"])

    asked = [c["user"] for c in model.calls if c["label"] == "verify"][-1]
    assert all(m["id"] in asked for m in missed)
    assert not any(m["id"] in asked for m in judged), "what was judged is not paid for twice"
    assert store.moment(conn, missed[0]["id"])["support"] == "partly"
    assert store.moment(conn, missed[1]["id"])["support"] == "unchecked", "one retry, then it rests"


def test_an_answer_that_ruled_on_nothing_is_not_asked_again(ready, conn, model, quote):
    """The identical prompt gets the identical nothing. The claims are recorded unchecked, where
    a researcher can see them, rather than paid for twice."""
    _doc(model, conn, ready["pid"], _moments(quote, ready["mid"], 5))
    synth.doc(conn, ready["mid"])
    before = len([c for c in model.calls if c["label"] == "verify"])
    model.queue({"verdicts": []})
    verify.run(conn, ready["mid"])
    assert len([c for c in model.calls if c["label"] == "verify"]) == before + 1


def test_the_check_names_the_lines_it_took_a_claim_from(ready, conn, model, quote):
    """The line's account is written over its claims and stored before any of them is checked.
    Take one away and the paragraph stands over evidence that is no longer there — so the check
    NAMES the line, and its caller writes the summary again (test_p34). It cannot do that itself:
    a model call has no business inside the transaction that sets the claim aside."""
    _doc(model, conn, ready["pid"], _moments(quote, ready["mid"], 5))
    synth.doc(conn, ready["mid"])
    doomed = store.thread(conn, ready["mid"], ready["tid"])[0]

    model.queue({"verdicts": [{"id": doomed["id"], "verdict": "not", "why": "not said here"}]},
                {"verdicts": []})
    out = verify.run(conn, ready["mid"])
    assert out["lost"] == [ready["tid"]]
    said = store.get_summary(conn, "thread", f'{ready["mid"]}:{ready["tid"]}', "reading")["text"]
    assert said == "an account of this line", "no note appended to it, and none needed"


def test_the_doc_prompt_carries_the_partly_note_beside_the_claim(ready, conn, quote, monkeypatch):
    """DOC used to be shown the claim bare, and a summary written over a bare claim hardens back
    into prose exactly the manner or the motive the passage never carried."""
    seen: dict[str, str] = {}

    def fake(system, user, *, label="", timeout=None):
        seen[label] = seen.get(label, "") + user
        if label == "thread":
            return {"moments": _moments(quote, ready["mid"], 5), "summary": "an account"}
        if label == "verify":
            return {"verdicts": [{"id": m["id"], "verdict": "partly", "why": "'often' is added"}
                                 for m in store.thread(conn, ready["mid"], ready["tid"])]}
        if label == "verify_summary":
            return {"verdicts": []}
        return {"summary": "what the reading found", "questions": "", "people": []}

    monkeypatch.setattr(llm, "chat_json", fake)
    synth.doc(conn, ready["mid"])
    assert seen["doc"].count("— partly: 'often' is added") == 5


# ---- the gate: a candidate with no codes is not followed --------------------------------------

def test_a_candidate_that_gathers_no_code_is_not_followed(conn, project, grande):
    """An empty code mapping is missing indexing, not evidence that every material carries the
    candidate. Followed anyway, it is looked for everywhere and confirms itself out of looking."""
    tid = store.save_theme(conn, project, tid=None, name="A hunch", gist="one material's shape",
                           code_ids=[])
    assert synth._marked_here(conn, grande, tid), "an open theme with no codes is still followed"
    store.set_hold(conn, tid, "candidate")
    assert not synth._marked_here(conn, grande, tid)


def test_a_candidate_with_a_code_that_fired_here_is_followed(conn, project, grande):
    store.save_codes(conn, project, grande, [{"name": "Work", "definition": "a living",
                                              "sids": [store.sentences(conn, grande)[5][0]]}])
    cid = [c["id"] for c in store.codebook(conn, project) if c["name"] == "Work"][0]
    tid = store.save_theme(conn, project, tid=None, name="Work", gist="a living", code_ids=[cid])
    store.set_hold(conn, tid, "candidate")
    assert synth._marked_here(conn, grande, tid)


def test_a_person_asking_for_a_line_is_answered_whatever_the_gate_says(conn, project, grande,
                                                                       model, quote):
    """`only_theme` is a person's own request. The gate is about where a reading goes on its own."""
    store.save_frame(conn, grande, kind="interview", display="turns", title="G", speakers=[],
                     segments=[])
    tid = store.save_theme(conn, project, tid=None, name="A hunch", gist="a shape", code_ids=[])
    store.set_hold(conn, tid, "candidate")
    model.queue({"moments": _moments(quote, grande, 5), "summary": "a"}, {"verdicts": []})
    synth.doc(conn, grande, only_theme=tid)
    assert len(store.thread(conn, grande, tid)) == 5
