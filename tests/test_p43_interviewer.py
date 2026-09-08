"""The interviewer speaks; the interviewer is not evidence.

    store.asked_sids(conn, mid) -> {sid, ...}    the passages an interviewer spoke
    synth.layout(conn, mid)                      marks every one of them, not just turn heads
    synth._thread_kept                           drops a moment whose quote is one of them

A researcher reading her own interviews back found the instrument citing HER words as the evidence
for a claim about the participant, and made the point that decides the shape of this: it happened
where she had summarised the participant correctly. So accuracy is not the test. A quote from the
interviewer is the researcher's own framing handed back as a finding about the material, and the
rule is absolute rather than a matter of how good the paraphrase was.

The anchor law cannot catch it. The quote is verbatim, the sid is right, and it binds perfectly:
in one project twelve live claims rested on the interviewer and every one had passed every check
the chain had. Eight of the twelve quoted a line carrying no speaker cue at all — the cue is
written once at the head of a turn — which is why the layout has to mark the lines before the
prompt can ask for anything, and why Python has to rule regardless (PLAN.md §3, laws 1 and 3).

The estimated case is the one that must NOT fire: where DIARIZE guessed at who was speaking, a
wrong guess would delete a participant's words in silence. There the reading is left alone.
"""
from __future__ import annotations

import pytest

from app import store

synth = pytest.importorskip("app.engine.synth")

SPEAKERS = [{"label": "PHILLIPS", "name": "A. Phillips", "role": "interviewer"},
            {"label": "GRANDE", "name": "M. Grande", "role": "participant"}]


def _framed(conn, mid, *, estimated=False):
    store.save_frame(conn, mid, kind="interview", display="turns", title="Grande, M.",
                     speakers=SPEAKERS, segments=[], estimated=estimated)


def _line(conn, mid, label):
    """A real line of this material spoken by `label`, long enough to quote and not a bare cue."""
    for r in store.sentence_rows(conn, mid):
        text = r["text"].split(":", 1)[-1].strip() if ":" in r["text"][:14] else r["text"]
        if r["speaker"] == label and 5 <= len(text.split()) <= 12:
            return r["sid"], " ".join(text.split()[:8])
    raise AssertionError(f"no usable {label} line in this material")


def _thread(conn, mid, tid, moments):
    """One THREAD answer through the keeper, exactly as a wave delivers it."""
    theme = dict(conn.execute("SELECT * FROM theme WHERE id=?", (tid,)).fetchone())
    return synth._thread_kept(conn, mid, tid, {"moments": moments, "summary": "s", "fit": ""},
                              store.sentences(conn, mid), theme,
                              store.material(conn, mid)["project_id"], run_id=None)


@pytest.fixture
def ready(conn, project, grande):
    _framed(conn, grande)
    tid = store.save_theme(conn, project, tid=None, name="Work", gist="a living", code_ids=[])
    return {"pid": project, "mid": grande, "tid": tid}


# ---- who is marked ------------------------------------------------------------------------------

def test_asked_sids_are_the_interviewers_and_only_those(conn, ready):
    asked = store.asked_sids(conn, ready["mid"])
    assert asked, "the interviewer speaks in this transcript"
    speaker = {r["sid"]: r["speaker"] for r in store.sentence_rows(conn, ready["mid"])}
    assert {speaker[s] for s in asked} == {"PHILLIPS"}


def test_an_estimated_frame_marks_nobody(conn, project, grande):
    """A guess at who is talking must never be able to delete evidence."""
    _framed(conn, grande, estimated=True)
    assert store.asked_sids(conn, grande) == set()


# ---- what the model is shown --------------------------------------------------------------------

def test_layout_marks_every_interviewer_line_not_just_the_turn_head(conn, ready):
    """The failure this exists for: the cue is written once, so most quoted interviewer lines
    carried nothing to see. A rule the model cannot see is one it cannot follow."""
    laid = synth.layout(conn, ready["mid"])
    asked = store.asked_sids(conn, ready["mid"])
    marked = {ln.split()[0] for ln in laid.splitlines() if "[interviewer]" in ln}
    assert marked == asked
    # Not merely the lines whose text still carries the cue.
    plain = {r["sid"] for r in store.sentence_rows(conn, ready["mid"])
             if r["sid"] in asked and not r["text"].lstrip().startswith("PHILLIPS")}
    assert plain and plain <= marked


def test_the_participants_lines_are_not_marked(conn, ready):
    laid = synth.layout(conn, ready["mid"])
    sid, _ = _line(conn, ready["mid"], "GRANDE")
    line = next(ln for ln in laid.splitlines() if ln.startswith(sid + " "))
    assert "[interviewer]" not in line


# ---- what Python rules --------------------------------------------------------------------------

def test_a_moment_quoting_the_interviewer_is_dropped(conn, ready):
    sid, quote = _line(conn, ready["mid"], "PHILLIPS")
    kept, dropped, stats = _thread(conn, ready["mid"], ready["tid"],
                                   [{"claim": "the border moved often", "anchor": quote,
                                     "sid": sid}])
    assert kept == []
    assert stats["asked"] == 1
    assert any("interviewer speaking" in d for d in dropped), dropped
    assert not store.thread(conn, ready["mid"], ready["tid"])


def test_the_note_does_not_claim_the_quote_is_missing(conn, ready):
    """It IS in the material. A note saying otherwise sends a researcher hunting a fault that is
    not there — the two outcomes are different findings and are said differently."""
    sid, quote = _line(conn, ready["mid"], "PHILLIPS")
    _, dropped, _ = _thread(conn, ready["mid"], ready["tid"],
                            [{"claim": "c", "anchor": quote, "sid": sid}])
    assert not any("not in this material" in d for d in dropped), dropped


def test_a_moment_quoting_the_participant_still_stands(conn, ready):
    sid, quote = _line(conn, ready["mid"], "GRANDE")
    kept, _, stats = _thread(conn, ready["mid"], ready["tid"],
                             [{"claim": "she sold milk and eggs", "anchor": quote, "sid": sid}])
    assert [m["sid"] for m in kept] == [sid]
    assert stats["asked"] == 0


def test_the_rest_of_a_line_survives_one_bad_moment(conn, ready):
    """The interviewer's moment goes; the participant's, written in the same answer, stays."""
    bad_sid, bad = _line(conn, ready["mid"], "PHILLIPS")
    good_sid, good = _line(conn, ready["mid"], "GRANDE")
    kept, dropped, _ = _thread(conn, ready["mid"], ready["tid"],
                               [{"claim": "asked", "anchor": bad, "sid": bad_sid},
                                {"claim": "answered", "anchor": good, "sid": good_sid}])
    assert [m["sid"] for m in kept] == [good_sid]
    assert len(dropped) == 1


def test_an_estimated_frame_keeps_the_moment(conn, project, grande):
    """Where the speakers were guessed, the reading is left exactly as it was."""
    _framed(conn, grande, estimated=True)
    tid = store.save_theme(conn, project, tid=None, name="Work", gist="a living", code_ids=[])
    for r in store.sentence_rows(conn, grande):
        text = r["text"].split(":", 1)[-1].strip() if ":" in r["text"][:14] else r["text"]
        if r["speaker"] == "PHILLIPS" and 5 <= len(text.split()) <= 12:
            sid, quote = r["sid"], " ".join(text.split()[:8])
            break
    kept, _, stats = _thread(conn, grande, tid, [{"claim": "c", "anchor": quote, "sid": sid}])
    assert [m["sid"] for m in kept] == [sid]
    assert stats["asked"] == 0


# ---- the remainder ------------------------------------------------------------------------------

def test_residual_never_reads_the_interviewers_passages(conn, ready, model):
    """An unmarked question is not something the coding missed — there was nothing to code. Left
    out of the remainder rather than dropped after, so no call is spent producing a note."""
    residual = pytest.importorskip("app.engine.residual")
    model.queue({"additions": [], "none_for": [], "note": ""})
    residual.run(conn, ready["mid"], run_id=None)
    shown = model.shown("residual")
    assert shown, "the residual pass ran"
    for sid in store.asked_sids(conn, ready["mid"]):
        assert f"\n{sid}  " not in shown, f"{sid} is the interviewer and was offered as remainder"
