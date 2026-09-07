"""TRANSCRIBE — a recording becomes the transcript everything above it reads.

The first step of the chain for a material that arrived as a recording, and the only one in this
engine that does not talk to a chat model. Voxtral takes a multipart POST at a different endpoint
with a different model, so this module speaks `httpx` itself rather than going through `llm.chat_json`
— and it **always** uses the Mistral credentials whatever `APERTURE_PROVIDER` says, because
Voxtral is the only transcriber here and there is no profile to switch. The two optional passes
over what comes back ARE ordinary structured calls and do go through `llm.chat_json`, so the
suite's offline guard covers them.

What it produces is not a special kind of material. It is Aperture's own turn format —
`NAME:\ttext`, blank line between turns — so `turns.scan` reads it back, FRAME describes it from
the text the way it describes an uploaded transcript, and nothing downstream knows or cares that
a machine heard it. That is the whole design: the recording path ends here.

**Chunks.** A long recording is cut before it is sent (`app/audio.py`), and diarization numbering
is only stable inside one request. So every segment carries the index of the chunk it came from,
the optional naming pass runs once per chunk, and rendering stitches turns by the RESOLVED
name — which is what makes a chunk boundary invisible: two chunks whose differently-numbered
voices both resolve to the same person are one turn, not two.

**Who disposes.** The model proposes, Python disposes, exactly as everywhere else in this engine.
A voice the naming pass omits is `other` with no name; a voice it invents is dropped; a role
outside the three is `other`. A tidied line is measured against the line it replaces and put back
where the change is larger than tidying — the researcher is reading the marks of talk on purpose,
and a model that quietly improves a stammer into a sentence has edited the evidence.
"""
from __future__ import annotations

import difflib
import os
import re
import shutil
import sqlite3
import tempfile
import time
from pathlib import Path

import httpx

from .. import audio, db, ingest, llm, store

# Voxtral Mini Transcribe 2. Overridable per host the way the chat models are, and named here
# rather than in `llm.PROVIDERS` because it is not a chat model and cannot be chosen instead of one.
DEFAULT_MODEL = "voxtral-mini-latest"
TIMEOUT = 1800.0            # a 150-minute chunk is a long upload before it is a long transcription

HEAD_LINES = 20             # how much of a chunk's opening the naming pass is shown
BIAS_MAX = 100              # the API's own ceiling on context_bias terms
ROLES = ("interviewer", "participant", "other")

# The gate on a tidied line, in the predecessor's numbers and for the predecessor's reason: past
# either of these the model is no longer repunctuating, it is rewriting.
MAX_CHANGE = 0.25           # share of words that may differ, ignoring case and outer punctuation
MAX_LENGTH_DELTA = 0.15     # how far the word COUNT may move — the add-or-drop guard

# Words a sentence starts with, which look like proper nouns at a full stop and are not. Only
# single words are tested against this, so "The Hague" survives it.
_OPENERS = {"the", "a", "an", "i", "we", "it", "this", "that", "they", "he", "she", "there",
            "but", "and", "in", "on", "at", "if", "so", "my", "our", "his", "her", "their",
            "when", "what", "who", "how", "why", "she's", "it's", "there's", "one", "two"}
_QUOTED = re.compile(r"[\"“]([^\"”\n]{2,60})[\"”]")
# A capital, then a word or a full stop — so an initial ("L. Byrne") is one term and not half of
# one — and any run of those, so a full name arrives whole.
_PROPER = re.compile(r"[A-Z](?:[\w’'\-]+|\.)(?:\s+[A-Z](?:[\w’'\-]+|\.))*")

# What a display name may be, so `turns.CUE` reads the line back: a capital, then letters, spaces,
# apostrophes, dots and hyphens, and not longer than the cue pattern allows.
_NAMEABLE = re.compile(r"[^A-Za-z'.\- ]+")
NAME_MAX = 28


class ASRError(RuntimeError):
    """One sentence. The researcher chose the file and is the one who can choose another."""


# ---- the file, the terms, the call ------------------------------------------------------------

def _key() -> str:
    key = (os.environ.get("MISTRAL_API_KEY") or "").strip()
    if not key:
        raise ASRError("set MISTRAL_API_KEY to transcribe a recording — transcription always uses "
                       "the Mistral credentials whatever APERTURE_PROVIDER says, because Voxtral "
                       "is the only transcriber this app has.")
    return key


def model() -> str:
    return os.environ.get("APERTURE_ASR_MODEL") or DEFAULT_MODEL


def context_bias(note: str) -> list[str]:
    """The terms the transcriber is told to expect, built in Python from the researcher's note.

    Names and places are what an ASR model mis-hears, and the researcher has just written the ones
    that matter into the box beside the upload — "Two people, R. Okafor and the interviewer
    L. Byrne, about the move to the coast". Quoted phrases first, because a researcher who quotes a term
    means it; then anything that looks like a proper noun. No model call: this is a regular
    expression over one paragraph, and paying for a call to find capital letters would be absurd.
    """
    out: list[str] = []
    seen: set[str] = set()

    def add(term: str) -> bool:
        """One word, or nothing. A phrase is added by its caller word by word.

        The API takes these as repeated form fields and reads them as a comma-separated list, so
        it refuses a term with a space in it — `Context bias item 'Paul Sigrist' must not contain
        commas or whitespace`, a 400 that fails the whole recording. Found by transcribing a real
        recording, not by a stub. Biasing towards *Sigrist* and *Rockaway* separately is the half
        of a name that was ever at risk of being mis-heard anyway.
        """
        term = (term or "").strip().strip(",;:")
        if " " in term or "," in term or not (2 <= len(term) <= 60) or term.lower() in seen:
            return False
        seen.add(term.lower())
        out.append(term)
        return True

    def add_all(phrase: str) -> None:
        for word in (phrase or "").split():
            add(word)

    for m in _QUOTED.finditer(note or ""):
        add_all(m.group(1))
    for m in _PROPER.finditer(note or ""):
        term = m.group(0)
        if len(term.split()) == 1 and term.lower() in _OPENERS:
            continue
        add_all(term)
    return out[:BIAS_MAX]


def _post(path: Path, bias: list[str]) -> dict:
    """One transcription request. The parameters are the documented ones (docs.mistral.ai →
    /v1/audio/transcriptions): `model`, `file`, `diarize`, `timestamp_granularities` and
    `context_bias`, the last two repeated form fields because both are arrays. `language` is
    deliberately not sent — the model detects it, and a researcher's corpus is not always in the
    language the host's locale would guess.

    The `call` row and the step's token counter are `llm`'s, through `record_audio`: a
    transcription is a paid call inside a step like any other, and the record of what a reading
    cost has to include it.
    """
    base = (os.environ.get("MISTRAL_BASE_URL") or "https://api.mistral.ai/v1").rstrip("/")
    name = model()
    began, t0 = store.now(), time.monotonic()
    try:
        with path.open("rb") as fh:
            r = httpx.post(f"{base}/audio/transcriptions",
                           headers={"Authorization": f"Bearer {_key()}"},
                           files={"file": (path.name, fh, "application/octet-stream")},
                           data={"model": name, "diarize": "true",
                                 "timestamp_granularities": ["segment"],
                                 "context_bias": bias},
                           timeout=TIMEOUT)
    except Exception as e:
        llm.record_audio("asr", {}, name, began, time.monotonic() - t0, "failed",
                         f"{type(e).__name__}: {e}"[:200])
        raise
    if r.status_code >= 400:
        # The provider's own words, truncated. What was SENT is a researcher's recording and never
        # goes anywhere near a log or a run row.
        why = f"{r.status_code} from {base}: {r.text[:300]}"
        llm.record_audio("asr", {}, name, began, time.monotonic() - t0, "failed", why[:200])
        raise ASRError(f"the transcriber refused this recording — {why}")
    payload = r.json()
    u = payload.get("usage") or {}
    llm.record_audio("asr", {"tokens_in": int(u.get("prompt_tokens") or 0),
                             "tokens_out": int(u.get("completion_tokens") or 0)},
                     name, began, time.monotonic() - t0)
    return payload


# ---- the segments ------------------------------------------------------------------------------

def _label(n: int) -> str:
    """SPEAKER A, SPEAKER B, … — letters rather than the numbers the API uses.

    `turns.CUE`, which is what reads a transcript back into turns, does not admit a digit in a
    speaker label: `SPEAKER 1:` at the start of a line is not a cue and the whole transcript would
    read as one unbroken block. Letters cost nothing and the text stays legible.
    """
    letters = ""
    n += 1
    while n:
        n, r = divmod(n - 1, 26)
        letters = chr(65 + r) + letters
    return f"SPEAKER {letters}"


def _tag(payload: dict, chunk: int, base: float) -> list[dict]:
    """One chunk's answer → segments in the whole recording's time, each stamped with its chunk.

    Speaker ids are renumbered per chunk in order of first appearance, so what the naming pass is
    shown is stable and readable however the API labels its voices.
    """
    out: list[dict] = []
    numbering: dict[str, str] = {}
    for s in payload.get("segments") or []:
        if not isinstance(s, dict):
            continue
        text = " ".join(str(s.get("text") or "").split())
        if not text:
            continue
        raw = str(s.get("speaker", s.get("speaker_id", 0)))
        if raw not in numbering:
            numbering[raw] = _label(len(numbering))
        out.append({"chunk": chunk, "speaker": numbering[raw], "text": text,
                    "start": float(s.get("start") or 0) + base,
                    "end": float(s.get("end") or 0) + base})
    if not out and (payload.get("text") or "").strip():
        # A recording with one voice throughout, or an answer with no segment breakdown at all:
        # the text is still the transcript and losing it because the shape was unexpected would be
        # the worst failure this module could have.
        out.append({"chunk": chunk, "speaker": _label(0), "start": base, "end": base,
                    "text": " ".join(str(payload["text"]).split())})
    return out


def _audio_seconds(payload: dict) -> float:
    u = payload.get("usage") or {}
    for k in ("prompt_audio_seconds", "audio_seconds", "seconds"):
        try:
            return float(u[k])
        except (KeyError, TypeError, ValueError):
            continue
    return 0.0


# ---- naming the voices (one call per chunk, only where the researcher asked) --------------------

def _display(name: str) -> str:
    """A name as a speaker cue, or empty where nothing usable survives."""
    clean = " ".join(_NAMEABLE.sub(" ", name or "").split()).upper()[:NAME_MAX].strip()
    return clean if len(clean) >= 2 and clean[0].isalpha() else ""


def voices(segments: list[dict], note: str, dropped: list[str]) -> dict[str, dict]:
    """{"<chunk>:<SPEAKER X>": {"role", "name"}} for every voice actually present.

    One call per chunk, because the numbering only means anything inside one. Python disposes: a
    voice the model leaves out is `other` with no name, a voice it invents is dropped and said so,
    and a role it makes up becomes `other`.
    """
    by_chunk: dict[int, list[dict]] = {}
    for s in segments:
        by_chunk.setdefault(int(s["chunk"]), []).append(s)

    resolved: dict[str, dict] = {}
    for chunk, mine in sorted(by_chunk.items()):
        present = list(dict.fromkeys(s["speaker"] for s in mine))
        system, user = llm.prompt(
            "voices", note=note.strip() or "(they said nothing about this recording)",
            speakers=", ".join(present),
            lines="\n".join(f"[{s['speaker']}] {s['text']}" for s in mine[:HEAD_LINES]))
        said = llm.chat_json(system, user, label="voices")
        proposed: dict[str, dict] = {}
        for e in said.get("voices") or []:
            if not isinstance(e, dict):
                continue
            who = str(e.get("speaker") or "").strip().upper()
            if who not in present:
                dropped.append(f"a voice called {who or '(unnamed)'} in piece {chunk + 1}: the "
                               "transcriber heard no such voice there")
                continue
            proposed[who] = e
        for who in present:
            e = proposed.get(who) or {}
            role = str(e.get("role") or "").strip().lower()
            if who not in proposed:
                dropped.append(f"{who} in piece {chunk + 1} was not placed, so it is shown as "
                               "another voice")
            elif role not in ROLES:
                dropped.append(f"{who} in piece {chunk + 1}: {role!r} is not one of "
                               f"{', '.join(ROLES)}, so it is shown as another voice")
            resolved[f"{chunk}:{who}"] = {"role": role if role in ROLES else "other",
                                          "name": _display(e.get("name"))}
    return resolved


def name_of(segment: dict, resolved: dict[str, dict]) -> str:
    """What this segment's line is headed with: the mapped name, else the mapped role, else the
    chunk's own numbering. This is the key turns are stitched on — never the raw speaker id, which
    is why a chunk boundary between two of one person's sentences is invisible."""
    r = resolved.get(f"{segment['chunk']}:{segment['speaker']}")
    if not r:
        return segment["speaker"]
    return r["name"] or r["role"].upper()


# ---- tidying (one call per chunk, gated line by line) -------------------------------------------

def _norm(word: str) -> str:
    """Case and outer punctuation stripped — those are exactly what tidying is FOR, so they must
    not count as changed words. A substituted word, which is a real correction, still differs."""
    return re.sub(r"^\W+|\W+$", "", word, flags=re.UNICODE).lower()


def within_gate(before: str, after: str) -> bool:
    """Whether a proposed line is a tidy or a rewrite. Measured, never argued with."""
    old, new = before.split(), after.split()
    if not old or not new:
        return False
    changed = 1.0 - difflib.SequenceMatcher(None, [_norm(w) for w in old],
                                            [_norm(w) for w in new]).ratio()
    return (changed <= MAX_CHANGE
            and abs(len(new) - len(old)) / len(old) <= MAX_LENGTH_DELTA)


def _who_block(chunk: int, mine: list[tuple[int, dict]], resolved: dict[str, dict]) -> str:
    """The voices of one chunk as the naming pass settled them. Tidying is shown this because a
    mis-heard word is most often a name, and the name is right here."""
    said = []
    for who in dict.fromkeys(s["speaker"] for _i, s in mine):
        r = resolved.get(f"{chunk}:{who}") or {}
        name = r.get("name") or ""
        said.append(f"  {who} — {name.title() if name else 'not named'}"
                    f" ({r.get('role', 'not placed')})")
    return "\n".join(said)


def tidy(segments: list[dict], note: str, resolved: dict[str, dict]) -> dict[str, int]:
    """Repunctuate in place. Returns {"accepted", "rejected", "untouched"} for the run's notes.

    One call per chunk. Every proposed line is measured against the line it replaces before it is
    accepted; a line past the gate is left exactly as the transcriber heard it.
    """
    by_chunk: dict[int, list[tuple[int, dict]]] = {}
    for i, s in enumerate(segments):
        by_chunk.setdefault(int(s["chunk"]), []).append((i, s))

    counted = {"accepted": 0, "rejected": 0, "untouched": 0}
    for chunk, mine in sorted(by_chunk.items()):
        system, user = llm.prompt(
            "tidy", note=note.strip() or "(they said nothing about this recording)",
            speakers=_who_block(chunk, mine, resolved),
            lines="\n".join(f"{i}. {s['text']}" for i, s in mine))
        said = llm.chat_json(system, user, label="tidy")
        proposed: dict[int, str] = {}
        for e in said.get("lines") or []:
            if not isinstance(e, dict):
                continue
            try:
                proposed[int(e.get("n"))] = " ".join(str(e.get("text") or "").split())
            except (TypeError, ValueError):
                continue
        for i, s in mine:
            fixed = proposed.get(i)
            if not fixed or fixed == s["text"]:
                counted["untouched"] += 1
            elif within_gate(s["text"], fixed):
                s["text"] = fixed
                counted["accepted"] += 1
            else:
                counted["rejected"] += 1
    return counted


# ---- the transcript ------------------------------------------------------------------------------

def render(segments: list[dict], resolved: dict[str, dict]) -> str:
    """Aperture's own turn format. Consecutive segments under the same name are one turn, turns are
    separated by a blank line, and `turns.scan` reads the result back exactly as it reads an
    uploaded transcript — which is the point: nothing above this step is told a machine heard it."""
    turns: list[tuple[str, list[str]]] = []
    for s in segments:
        who = name_of(s, resolved)
        if turns and turns[-1][0] == who:
            turns[-1][1].append(s["text"])
        else:
            turns.append((who, [s["text"]]))
    return "".join(f"{who}:\t{' '.join(said)}\n\n" for who, said in turns).rstrip("\n") + \
        ("\n" if turns else "")


def _voice_rows(rows: list[dict], resolved: dict[str, dict]) -> tuple[list[dict], list[dict]]:
    """(speakers, segments) for `store.save_voices`, from the sentences as they were just cut.

    A segment is where a turn starts, which is what the `segment` table already means, and the
    speaker rows carry the role the naming pass settled — so the reading above never has to guess
    at who is speaking in a material whose voices were separated from the recording itself.
    """
    known = {(r["name"] or r["role"].upper()): r for r in resolved.values()}
    segments, speakers, at = [], [], None
    for r in rows:
        who = r.get("speaker") or ""
        if who and r["turn_idx"] != at:
            segments.append({"sid": r["sid"], "label": who})
            at = r["turn_idx"]
    for who in dict.fromkeys(s["label"] for s in segments):
        r = known.get(who)
        speakers.append({"label": who, "role": r["role"] if r else "other",
                         "name": r["name"].title() if r and r["name"] else ""})
    return speakers, segments


# ---- the step ------------------------------------------------------------------------------------

def run(conn: sqlite3.Connection, mid: str, *, run_id: str | None = None) -> dict:
    """Transcribe one material's recording and write the transcript it became.

    Everything that can fail — the file, ffmpeg, the API, the two optional passes — fails before
    anything is written, so a failed transcription leaves the material with its placeholder and a
    run row saying why, and the researcher can upload a different file or run it again.

    `run_id` is taken for the same reason MEMO and RESIDUAL take it — so a caller can say which
    step this is — but nothing here needs it: the calls record themselves under the row `jobs`
    already put in this context (`llm.new_usage`), the transcription included.
    """
    row = store.material(conn, mid)
    if row is None:
        raise ASRError("that material is not here any more")
    if not row["audio_file"]:
        raise ASRError(f"{row['name']} did not come from a recording, so there is nothing to "
                       "transcribe")
    source = db.data_dir() / row["audio_file"]
    if not source.exists():
        raise ASRError(f"the recording for {row['name']} is no longer on the volume; upload it "
                       "again")

    note, clean = row["audio_note"] or "", bool(row["audio_clean"])
    dropped: list[str] = []
    work = Path(tempfile.mkdtemp(prefix="aperture-asr-"))
    try:
        was = source.stat().st_size
        llm.report("preparing the recording")
        prepared = audio.prepare(source, work)
        if prepared != source:
            dropped.append(f"converted to mono 16 kHz FLAC before sending: "
                           f"{was / 1e6:.0f} MB became {prepared.stat().st_size / 1e6:.0f} MB")
        per = audio.chunking(prepared)
        pieces = audio.split(prepared, per, work) if per else [(prepared, 0.0)]
        if per:
            dropped.append(f"the recording runs {audio.spoken(audio.seconds(prepared))} and was "
                           f"sent in {len(pieces)} pieces of about {audio.spoken(per)}")

        bias = context_bias(note)
        segments: list[dict] = []
        heard = 0.0
        for i, (piece, base) in enumerate(pieces):
            llm.report(f"transcribing piece {i + 1} of {len(pieces)}")
            payload = _post(piece, bias)
            heard += _audio_seconds(payload)
            segments.extend(_tag(payload, i, base))
        if not segments:
            raise ASRError(f"the transcriber returned nothing for {row['name']} — no speech was "
                           "heard in it")

        resolved: dict[str, dict] = {}
        if clean:
            llm.report("working out whose voice is whose")
            resolved = voices(segments, note, dropped)
            llm.report("tidying what was heard")
            counted = tidy(segments, note, resolved)
            dropped.append(f"tidying: {counted['accepted']} line(s) accepted, "
                           f"{counted['rejected']} rejected as more than tidying, "
                           f"{counted['untouched']} left as they were")

        text = render(segments, resolved)
        rows = ingest.sentences(text)
        speakers, spans = _voice_rows(rows, resolved)
        total = heard or audio.seconds(prepared)
        with store.atomic(conn) as c:
            store.update_text(c, mid, text, audio_seconds=total)
            store.save_sentences(c, mid, rows)
            store.save_voices(c, mid, speakers, spans)

        # The original goes; the mono 16 kHz FLAC it was transcribed from stays. Keeping the
        # recording is what makes "run again from the recording" more than a menu entry — a
        # researcher who wants the naming pass they did not ask for the first time should not have
        # to upload an hour of audio again — and keeping the prepared copy costs a twentieth of
        # keeping the original, with nothing lost that a transcript would ever show.
        if prepared != source:
            kept = db.data_dir() / f"audio/{mid}.flac"
            shutil.move(str(prepared), str(kept))
            source.unlink(missing_ok=True)
            store.set_audio_file(conn, mid, f"audio/{mid}.flac")
            dropped.append("the uploaded file was replaced by the mono 16 kHz FLAC it was "
                           "transcribed from, which is what a rerun from the recording will use")
    finally:
        shutil.rmtree(work, ignore_errors=True)

    return {"text": text, "segments": segments, "speakers": speakers, "seconds": total,
            "dropped": dropped}
