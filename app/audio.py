"""A recording becomes a file the transcriber can take. The standard library and one subprocess.

Nothing here talks to a model, a database or the network. It answers three questions about a file
on disk — how long is it, is it small enough to send, and where do I cut it — and it answers them
the same way for a researcher's phone recording as for a studio WAV.

**Why the conversion is the point.** The API takes a gigabyte and three hours, and an hour of
stereo 48 kHz 16-bit WAV is already 691 MB before anyone has done anything wrong. Speech does
not need that: mono 16 kHz FLAC is what every ASR model actually listens to, and the same hour
comes out around a tenth of that with nothing lost that a transcript would show. So a recording is re-encoded before
it is measured against any limit, and chunking is the exception rather than the rule.

Video containers are in `KINDS` because a researcher's recording is very often a video file — a
Teams call, a phone held on a table — and ffmpeg takes the audio out of one exactly as it takes it
out of a sound file.

ffmpeg missing is a sentence, not a traceback. The one path that does not need it is the one a
laptop most often has: a WAV, read by stdlib `wave`.
"""
from __future__ import annotations

import json
import math
import os
import shutil
import subprocess
import tempfile
import wave
from pathlib import Path

# What may be uploaded as a recording. The video containers are here on purpose (see the module
# docstring); ffmpeg reduces every one of them to the same mono 16 kHz FLAC.
KINDS = (".mp3", ".wav", ".m4a", ".flac", ".ogg", ".mp4", ".m4v", ".mov", ".aac", ".opus",
         ".webm")

# What a material's text says between the upload and the transcription. Transcribing takes
# minutes, so it cannot happen in the request; the material exists from the moment the file lands
# and says so in words rather than sitting empty.
NOT_YET = "(this recording has not been transcribed yet)"

# The API takes three hours and a gigabyte per request. Both of these sit comfortably under that:
# a chunk boundary costs a little accuracy at the seam, so it is worth having room rather than
# discovering the limit on a researcher's longest interview.
MAX_SECONDS = 150 * 60
MAX_BYTES = 800 * 1024 * 1024
RATE = 16000                    # what speech recognition listens at, whatever was recorded


class AudioError(RuntimeError):
    """One sentence naming the file and what is needed. Never a traceback."""


def is_audio(filename: str) -> bool:
    return os.path.splitext(filename or "")[1].lower() in KINDS


def _tool(name: str) -> str:
    if shutil.which(name) is None:
        raise AudioError(
            f"{name} is not installed here, and a recording that is not already a mono "
            f"{RATE // 1000} kHz WAV cannot be prepared without it. The deployed image carries "
            f"ffmpeg; on a laptop, `brew install ffmpeg` or `apt install ffmpeg`.")
    return name


def _run(args: list[str]) -> str:
    """One subprocess. Its last line of stderr is the reason, because ffmpeg's first fifty are
    a banner nobody needs."""
    args = [_tool(args[0]), *args[1:]]
    done = subprocess.run(args, capture_output=True, text=True)
    if done.returncode != 0:
        why = [ln for ln in (done.stderr or "").splitlines() if ln.strip()]
        raise AudioError(f"{args[0]} could not handle this recording: "
                         f"{why[-1].strip() if why else 'it gave no reason'}")
    return done.stdout


def _wav(path: Path) -> tuple[float, int, int]:
    """(seconds, channels, rate) for a WAV, without ffmpeg. The common case on a laptop."""
    with wave.open(str(path), "rb") as w:
        rate = w.getframerate()
        return (w.getnframes() / rate if rate else 0.0), w.getnchannels(), rate


def _probe(path: Path, entries: str) -> dict:
    out = _run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", entries,
                "-of", "json", str(path)])
    try:
        return json.loads(out or "{}")
    except json.JSONDecodeError:
        return {}


def seconds(path: str | Path) -> float:
    """How long the recording runs. stdlib for a WAV so the common case needs no ffmpeg."""
    path = Path(path)
    if path.suffix.lower() == ".wav":
        try:
            return _wav(path)[0]
        except (wave.Error, EOFError):
            pass            # a .wav stdlib cannot read is still one ffprobe knows the length of
    got = _probe(path, "format=duration:stream=duration")
    for value in ((got.get("format") or {}).get("duration"),
                  *(s.get("duration") for s in got.get("streams") or [])):
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return 0.0


def _already_prepared(path: Path) -> bool:
    """Mono, 16 kHz and small enough — nothing to gain by re-encoding it."""
    if path.stat().st_size > MAX_BYTES:
        return False
    if path.suffix.lower() == ".wav":
        try:
            _, channels, rate = _wav(path)
        except (wave.Error, EOFError):
            return False
        return channels == 1 and rate == RATE
    if path.suffix.lower() == ".flac":
        # Costs one ffprobe, and saves re-encoding a file this module itself produced — which is
        # what a rerun from the recording would otherwise do every time.
        stream = ((_probe(path, "stream=channels,sample_rate").get("streams") or [{}])[0])
        return str(stream.get("channels")) == "1" and str(stream.get("sample_rate")) == str(RATE)
    return False


def prepare(path: str | Path, into: str | Path | None = None) -> Path:
    """The recording as the transcriber wants it: mono 16 kHz FLAC, in `into`.

    Returns the original path unchanged when it is already that and already small enough, so a
    file this module produced is never re-encoded.
    """
    path = Path(path)
    if _already_prepared(path):
        return path
    into = Path(into or tempfile.mkdtemp(prefix="aperture-audio-"))
    into.mkdir(parents=True, exist_ok=True)
    out = into / f"{path.stem}.flac"
    _run(["ffmpeg", "-y", "-i", str(path), "-ac", "1", "-ar", str(RATE), "-c:a", "flac",
          str(out)])
    return out


def chunking(path: str | Path) -> float | None:
    """Seconds per chunk, or None where the whole recording goes in one request.

    Both limits are the same question — how many pieces does this have to be — so they are asked
    together and the pieces come out even. Ten equal chunks read better at the seams than nine of
    two and a half hours and one of four minutes.
    """
    path = Path(path)
    total = seconds(path)
    parts = max(math.ceil(path.stat().st_size / MAX_BYTES),
                math.ceil(total / MAX_SECONDS) if total else 1, 1)
    return None if parts < 2 else total / parts


def split(path: str | Path, seconds_per_chunk: float,
          into: str | Path | None = None) -> list[tuple[Path, float]]:
    """[(chunk, its start in the original recording)]. The offset is what makes a timestamp from
    the third chunk mean something in the whole interview."""
    path = Path(path)
    into = Path(into or tempfile.mkdtemp(prefix="aperture-audio-"))
    into.mkdir(parents=True, exist_ok=True)
    total = seconds(path)
    # WAV and FLAC cut without decoding; anything else is re-encoded, which is also the moment to
    # bring it down to mono 16 kHz if it somehow arrived here without being prepared.
    copyable = path.suffix.lower() in (".wav", ".flac")
    codec = ["-c:a", "copy"] if copyable else ["-ac", "1", "-ar", str(RATE), "-c:a", "flac"]
    ext = path.suffix if copyable else ".flac"
    out: list[tuple[Path, float]] = []
    for i in range(max(1, math.ceil(total / seconds_per_chunk))):
        base = i * seconds_per_chunk
        dest = into / f"{path.stem}.{i:03d}{ext}"
        _run(["ffmpeg", "-y", "-ss", f"{base:.3f}", "-t", f"{seconds_per_chunk:.3f}",
              "-i", str(path), *codec, str(dest)])
        out.append((dest, base))
    return out


def spoken(total: float) -> str:
    """A duration a researcher reads rather than counts: "1 h 12 min", "48 min", "40 s"."""
    total = max(0.0, float(total or 0))
    if total < 60:
        return f"{total:.0f} s"
    if total < 3600:
        return f"{total / 60:.0f} min"
    return f"{int(total // 3600)} h {int((total % 3600) // 60):02d} min"
