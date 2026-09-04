"""P20 — the shell. The rail says where each material stands without opening it."""
from __future__ import annotations

import pytest

from app import store

pytest.importorskip("app.context")


def state(conn, pid: str, mid: str) -> tuple[str, str]:
    from app import context
    m = next(x for x in context._shell(conn, pid)["nav_materials"] if x["id"] == mid)
    return m["reading_state"], m["reading_said"]


def test_the_rail_says_where_each_material_stands(conn, project, grande):
    assert state(conn, project, grande) == ("waiting", "Not read yet")

    rid = store.start_run(conn, project, "frame", grande, "Reading the shape of it")
    assert state(conn, project, grande) == ("active", "Being read")

    store.finish_run(conn, rid, error="LLMError: the model returned no JSON")
    assert state(conn, project, grande) == ("failed",
                                            "Stopped: LLMError: the model returned no JSON")


def test_a_material_is_marked_read_only_once_every_step_has_landed(conn, project, grande):
    for kind in ("frame", "angles", "read", "doc"):
        assert state(conn, project, grande)[0] != "done"
        store.finish_run(conn, store.start_run(conn, project, kind, grande, "x"))
    assert state(conn, project, grande) == ("done", "Read")
