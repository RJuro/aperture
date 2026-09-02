"""Fixtures. No test ever reaches a network: `llm.chat_json` is replaced everywhere."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

SEED = Path(__file__).resolve().parent.parent / "seed"

# Captured at import, before any fixture can patch it over.
from app import llm as _llm  # noqa: E402
REAL_CHAT_JSON = _llm.chat_json


@pytest.fixture(autouse=True)
def _isolated(monkeypatch, tmp_path):
    monkeypatch.setenv("APERTURE_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.delenv("APERTURE_PIN", raising=False)
    monkeypatch.setenv("APERTURE_PROVIDER", "minimax")
    monkeypatch.setenv("MINIMAX_API_KEY", "test-key-not-used")
    # A developer's .env is loaded at import; the suite must not read it, or a local model
    # override silently changes what the tests are asserting about.
    for leak in ("APERTURE_RECORD", "APERTURE_REPLAY", "APERTURE_REASONING",
                 "MINIMAX_MODEL", "MISTRAL_MODEL", "MINIMAX_BASE_URL", "MISTRAL_BASE_URL"):
        monkeypatch.delenv(leak, raising=False)


@pytest.fixture
def real_chat_json():
    """The genuine `chat_json`, for the few tests that exercise the client itself (replay,
    parsing) rather than an engine step."""
    return REAL_CHAT_JSON


@pytest.fixture(autouse=True)
def _no_live_model(monkeypatch):
    """Any un-stubbed model call fails loudly rather than quietly costing money."""
    from app import llm

    def boom(*a, **k):
        raise AssertionError("live model call in a test — use the `model` fixture")

    monkeypatch.setattr(llm, "chat_json", boom)
    return boom


@pytest.fixture
def model(monkeypatch):
    """`model.queue(dict, ...)` sets what the next calls return; `model.calls` records
    (label, system, user) so a test can assert what the model was actually shown."""
    from app import llm

    class Fake:
        def __init__(self):
            self.answers, self.calls = [], []

        def queue(self, *answers):
            self.answers.extend(answers)
            return self

        def __call__(self, system, user, *, label="", timeout=None):
            self.calls.append({"label": label, "system": system, "user": user})
            if not self.answers:
                raise AssertionError(f"unexpected model call {label!r}")
            return self.answers.pop(0)

        def shown(self, label=None) -> str:
            """Everything the model saw, for `in` assertions."""
            cs = [c for c in self.calls if label is None or c["label"] == label]
            return "\n".join(c["system"] + "\n" + c["user"] for c in cs)

    fake = Fake()
    monkeypatch.setattr(llm, "chat_json", fake)
    for mod in ("frame", "read", "themes", "synth", "check"):
        try:
            m = __import__(f"app.engine.{mod}", fromlist=["x"])
            if hasattr(m, "llm"):
                monkeypatch.setattr(m.llm, "chat_json", fake)
        except ImportError:
            pass
    return fake


@pytest.fixture
def conn():
    from app import db
    c = db.connect()
    yield c
    c.close()


@pytest.fixture
def project(conn):
    from app import store
    return store.create_project(conn, "Test project", focus="")


@pytest.fixture
def grande(conn, project):
    """A real transcript, ingested. Every phase's tests run against real material — a splitter
    that only works on a toy fixture is a splitter that does not work."""
    from app import ingest, store
    raw = (SEED / "DP-40 GRANDE, M.txt").read_text()
    mid = store.add_material(conn, project, "DP-40 Grande", raw)
    store.save_sentences(conn, mid, ingest.sentences(raw))
    return mid


@pytest.fixture
def rodwin(conn, project):
    from app import ingest, store
    raw = (SEED / "EI-845 RODWIN.txt").read_text()
    mid = store.add_material(conn, project, "EI-845 Rodwin", raw)
    store.save_sentences(conn, mid, ingest.sentences(raw))
    return mid


@pytest.fixture
def quote(conn):
    """A real ≤12-word quote from a material, with its sid — so tests bind against real text
    instead of inventing quotes that happen to satisfy the matcher."""
    from app import store

    def pick(mid: str, at: int = 60) -> tuple[str, str]:
        for sid, text in store.sentences(conn, mid)[at:]:
            words = text.split()
            if 5 <= len(words) <= 12 and not text.endswith(":"):
                return sid, text
        raise AssertionError("no usable quote in this material")

    return pick


@pytest.fixture
def analysed(conn, project, grande, rodwin, quote):
    """A complete project state, built without a model, so the pages phase can be built in
    parallel with the engine phases. Two materials, two themes, threads in both, an orientation
    and a reading summary, a check, and one piece of feedback."""
    from app import store
    store.save_frame(conn, grande, kind="interview", display="turns", title="Grande, M.",
                     speakers=[{"label": "PHILLIPS", "name": "Phillips", "role": "interviewer"},
                               {"label": "GRANDE", "name": "M. Grande", "role": "participant"}],
                     segments=[])
    store.save_frame(conn, rodwin, kind="interview", display="turns", title="Rodwin",
                     speakers=[], segments=[])
    store.save_people(conn, grande, [{"name": "M. Grande", "aliases": ["Grande"],
                                      "role": "participant"}])
    themes = {}
    for name, gist in (("Work and trade", "how a living is made"),
                       ("Leaving and arriving", "the crossing and after")):
        themes[name] = store.save_theme(conn, project, tid=None, name=name, gist=gist,
                                        code_ids=[])
    for mid in (grande, rodwin):
        store.save_summary(conn, "material", mid, "orientation",
                           "An oral-history interview about migration.")
        store.save_summary(conn, "material", mid, "reading",
                           "The reading found work and the crossing braided together.")
        for i, (name, tid) in enumerate(themes.items()):
            ms = []
            for k in range(3):
                sid, text = quote(mid, at=40 + i * 30 + k * 7)
                ms.append({"claim": f"{name}: claim {k}", "anchor": " ".join(text.split()[:8]),
                           "sid": sid})
            store.save_moments(conn, mid, tid, ms)
    store.save_summary(conn, "project", project, "reading",
                       "Across both interviews, work and the crossing are one story.")
    first = store.moments(conn, grande)[0]
    store.add_feedback(conn, project, "moment", first["id"], "agree", "")
    store.save_check(conn, project, "material", grande, "Is religion mentioned?",
                     "not found", [], 302)
    return {"pid": project, "grande": grande, "rodwin": rodwin, "themes": themes,
            "moment": first["id"]}
