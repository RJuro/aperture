"""Speech, from Roman's Kokoro service (tts.rjuro.com; the GPU behind it runs on RunPod).

One job per brief: the service splits the text into model-sized pieces itself and returns one MP3.
Submit, poll, fetch the MP3 through the service — the signed storage link expires after a
fortnight, so the file is kept here and the link never is. English voices only.

A voice that cannot be reached is a sentence, never a traceback: the brief's text is written
before this is called, and it stands whatever happens here.
"""
from __future__ import annotations

import os
import re
import time
from pathlib import Path

import httpx

VOICE = "af_heart"
# The service's own limit per request. A brief is capped at 800 words, about 5,000 characters, so
# this is a guard and never a reason to split.
MAX_CHARS = 25_000
POLL = 5.0
# A cold RunPod worker is the long part.
CEILING = 1200.0
SUBMIT_WAIT = 600.0
_sleep = time.sleep


class SpeechError(RuntimeError):
    """One sentence saying what is missing or what the voice answered."""


def configured() -> bool:
    return bool(os.environ.get("TTS_API_KEY"))


def spoken(text: str) -> str:
    """What Kokoro should be handed. It reads a heading's `#` as "hashtag", a URL aloud and a
    bracketed code letter by letter, so those go; dashes become pauses. Blank lines stay: they
    carry through as pauses between paragraphs."""
    text = re.sub(r"^[ \t]*#+[ \t]*", "", text.replace("*", ""), flags=re.M)
    text = re.sub(r"\[([^\]]+)\]\((?:https?://)?[^)]+\)", r"\1", text)      # [words](link)
    text = re.sub(r"[ \t]*\[[^\]]*\]", "", text)                             # [LA S012]
    text = re.sub(r"\s*(?:https?://|www\.)\S+?(?=[.,;:!?)]*(?:\s|$))", "", text)
    text = re.sub(r"[ \t]*[—–][ \t]*", ", ", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def speak(text: str, into: Path, title: str = "") -> Path:
    key = os.environ.get("TTS_API_KEY") or ""
    if not key:
        raise SpeechError("no voice is set up here (TTS_API_KEY is not set)")
    body = spoken(text)
    if len(body) > MAX_CHARS:
        raise SpeechError(f"the text is {len(body)} characters and the voice takes {MAX_CHARS}")
    base = (os.environ.get("TTS_API_URL") or "https://tts.rjuro.com").rstrip("/")
    try:
        with httpx.Client(headers={"Authorization": f"Bearer {key}"},
                          timeout=httpx.Timeout(30.0, read=120.0)) as c:
            # Accepting a job is slow too when the service is busy: live, a submit took over 120 s
            # and one came back 502 after 102. A submit abandoned early may still have been queued,
            # and trying again would record the brief twice, so it is given long enough to answer.
            r = c.post(f"{base}/api/generate", json={
                "text": body, "title": title or None,
                "voice": os.environ.get("TTS_VOICE") or VOICE},
                timeout=httpx.Timeout(30.0, read=SUBMIT_WAIT))
            if r.status_code != 200:
                raise SpeechError(f"the voice refused the text ({r.status_code})")
            job, waited = r.json()["job_id"], 0.0
            while True:
                # A busy service can sit on a status request past the read timeout, or answer it
                # with a proxy's error page. That is the job still running, not the voice gone;
                # the ceiling still holds. (Live, 2026-09-23: a page that was not JSON failed a
                # recording 219 s in.)
                try:
                    r = c.get(f"{base}/api/status/{job}")
                    s = r.json() if r.status_code == 200 else {}
                except (httpx.TransportError, ValueError):
                    s = {}
                if s.get("status") == "completed":
                    break
                if s.get("status") == "failed":
                    raise SpeechError(f"the voice failed: {s.get('error') or 'no reason given'}")
                if waited >= CEILING:
                    raise SpeechError(f"the voice was still working after {int(CEILING)} s")
                _sleep(POLL)
                waited += POLL
            a = c.get(f"{base}/api/audio/{job}", params={"format": "mp3"},
                      timeout=httpx.Timeout(30.0, read=300.0))
    except httpx.HTTPError as e:
        raise SpeechError(f"the voice could not be reached ({type(e).__name__})") from e
    if a.status_code != 200 or not a.content:
        raise SpeechError(f"the recording could not be fetched ({a.status_code})")
    into.parent.mkdir(parents=True, exist_ok=True)
    into.write_bytes(a.content)
    return into
