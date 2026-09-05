"""RECONCILE — the codes an exploratory reading made, set beside the project's vocabulary.

Where a project explores, READ is shown no codebook: each material is coded on its own terms. That
is the whole point of the method, and it leaves a job behind — two readings can name one thing
twice. This step is where the two vocabularies meet, after the reading and before THEMES, once per
material.

Two things it is careful about.

**Exact names never reach the model.** `store.save_codes` reuses a code by name, so a reading that
happened to write a name the project already had wrote onto that code, and it now has hits in two
materials. `store.codes_only_in` therefore sees only what is genuinely this material's, and where
that list is empty — or where no other material has been read yet — nothing is asked of anyone.

**Python applies one relation of the four.** `same` is a merge: the local code's hits move to the
project's code and the row that carried them goes. `narrower`, `wider` and `distinct` change
nothing at all — they are written beside the code as a note, because deciding that two codes are
related is not the same as deciding they are one, and the second is the researcher's to make.
"""
from __future__ import annotations

import sqlite3

from .. import llm, store

RELATIONS = ("same", "narrower", "wider", "distinct")
WHY_WORDS = 20


def _verbatim(text: str, empty: str) -> str:
    """The researcher's own words, delimited rather than reworded."""
    text = (text or "").strip()
    return f'"""\n{text}\n"""' if text else empty


def _local_block(rows: list[sqlite3.Row]) -> str:
    return "\n".join(f"- {r['name']} — {r['definition'] or 'no definition recorded'}\n"
                     f"  for example: {r['example'] or 'no example recorded'}" for r in rows)


def _codebook_block(rows: list[sqlite3.Row]) -> str:
    return "\n".join(f"- {r['name']} — {r['definition'] or 'no definition recorded'}"
                     for r in rows)


def note(relation: str, project: str, why: str) -> str:
    """What is written beside a code the comparison did not merge. It names the relation and the
    code it is a relation to, so a researcher reading it later needs nothing else on the page."""
    head = (f'{relation} than "{project}"' if relation in ("narrower", "wider") and project
            else "distinct from the project's vocabulary" if relation == "distinct"
            else relation)
    return f"{head} — {why}" if why else head


def run(conn: sqlite3.Connection, mid: str) -> dict:
    """Compare this material's own codes with the project's. Returns
    {considered, merged, noted, dropped}.

    Nothing is asked of the model where there is nothing to ask: a material that founded no code
    of its own, or a project with no other material read yet, returns having spent nothing.
    """
    m = store.material(conn, mid)
    pid = m["project_id"]
    local = store.codes_only_in(conn, pid, mid)
    known = {r["name"]: r for r in store.codes_elsewhere(conn, pid, mid)}
    if not local or not known:
        return {"considered": len(local), "merged": 0, "noted": 0, "dropped": []}

    proj = store.project(conn, pid)
    system, user = llm.prompt(
        "reconcile",
        focus=_verbatim(proj["focus"], "The researcher has not said what they are looking for."),
        local=_local_block(local),
        codebook=_codebook_block(list(known.values())))
    out = llm.chat_json(system, user, label="reconcile")

    # Popped as they are answered, so a name answered twice is dropped the second time and a code
    # nobody said anything about simply keeps standing as it is.
    waiting = {r["name"]: r for r in local}
    dropped: list[str] = []
    merged = noted = 0
    with store.atomic(conn) as tx:
        for entry in out.get("relations") or []:
            if not isinstance(entry, dict):
                continue
            row = waiting.pop(str(entry.get("local") or "").strip(), None)
            if row is None:
                dropped.append(f"a relation for {str(entry.get('local') or '')!r}, "
                               f"which is not one of this reading's codes")
                continue
            relation = str(entry.get("relation") or "").strip().lower()
            if relation not in RELATIONS:
                dropped.append(f"code {row['name']!r}: {relation!r} is not a relation")
                continue
            other = known.get(str(entry.get("project") or "").strip())
            why = " ".join(str(entry.get("why") or "").split()[:WHY_WORDS])
            if relation == "same":
                if other is None:
                    dropped.append(f"code {row['name']!r}: said to be the same as a code the "
                                   f"project does not have")
                    continue
                store.merge_code(tx, row["id"], other["id"])
                merged += 1
                continue
            store.note_code(tx, row["id"], note(relation, other["name"] if other else "", why))
            noted += 1
    return {"considered": len(local), "merged": merged, "noted": noted, "dropped": dropped}
