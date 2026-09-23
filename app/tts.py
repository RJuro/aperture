"""Speech, from Roman's Kokoro service (tts.rjuro.com; the GPU behind it runs on RunPod).

Submit the text, poll until the job is done, fetch the MP3 through the service itself — the signed
storage link expires after a fortnight, so the file is kept here and the link never is. English
voices only.

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
POLL = 5.0
# A cold RunPod worker is the long part; a warm one reads a five-minute brief in well under one.
CEILING = 600.0
_sleep = time.sleep


class SpeechError(RuntimeError):
    """One sentence saying what is missing or what the voice answered."""


def configured() -> bool:
    return bool(os.environ.get("TTS_API_KEY"))


def spoken(text: str) -> str:
    """What Kokoro should be handed: dashes read as pauses, asterisks and markup not at all."""
    text = re.sub(r"\s*[—–]\s*", ", ", text.replace("*", ""))
    return re.sub(r"^#+\s*", "", text, flags=re.M).strip()


def speak(text: str, into: Path, title: str = "") -> Path:
    key = os.environ.get("TTS_API_KEY") or ""
    if not key:
        raise SpeechError("no voice is set up here (TTS_API_KEY is not set)")
    base = (os.environ.get("TTS_API_URL") or "https://tts.rjuro.com").rstrip("/")
    auth = {"Authorization": f"Bearer {key}"}
    try:
        with httpx.Client(headers=auth, timeout=httpx.Timeout(30.0, read=120.0)) as c:
            r = c.post(f"{base}/api/generate", json={"text": spoken(text), "title": title or None,
                                                     "voice": os.environ.get("TTS_VOICE") or VOICE})
            if r.status_code != 200:
                raise SpeechError(f"the voice refused the text ({r.status_code})")
            job, waited = r.json()["job_id"], 0.0
            while True:
                s = c.get(f"{base}/api/status/{job}").json()
                if s.get("status") == "completed":
                    break
                if s.get("status") == "failed":
                    raise SpeechError(f"the voice failed: {s.get('error') or 'no reason given'}")
                if waited >= CEILING:
                    raise SpeechError(f"the voice was still working after {int(CEILING)} s")
                _sleep(POLL)
                waited += POLL
            a = c.get(f"{base}/api/audio/{job}", params={"format": "mp3"})
    except httpx.HTTPError as e:
        raise SpeechError(f"the voice could not be reached ({type(e).__name__})") from e
    if a.status_code != 200 or not a.content:
        raise SpeechError(f"the recording could not be fetched ({a.status_code})")
    into.parent.mkdir(parents=True, exist_ok=True)
    into.write_bytes(a.content)
    return into
