#!/usr/bin/env python3
"""One reading of one corpus, start to finish, without a server.

    python scripts/eval_run.py --materials seed --focus "..." --data runs/v2 --out runs/v2/record.md

The researcher runs this to produce the next version of a record: same files, same focus, changed
prompts. It creates a project, adds every readable file in `--materials`, and runs **exactly the
chain `jobs.ingest_chain` plans** — not a copy of it. The plan is taken from that function by
standing in for `jobs.start`, so the day the chain grows a step this runner grows it too.

Synchronous on purpose. `jobs.start` puts the chain in a thread so a browser is not left waiting;
here nobody is waiting and a thread only makes a failure harder to read.

**This calls the live model.** It respects the environment the app respects — `APERTURE_PROVIDER`,
the provider key, `APERTURE_RECORD` — and a full corpus costs real money, which is why it refuses
a `--data` directory that already holds a database: v1 and v2 are two readings, and a rerun into
the same directory would be a third reading of a project that already has one. `--dry-run` prints
the condition and the steps that would run, and stops before the first call.

**The four conditions of the pass-6 comparison** (docs/EVAL.md) are four invocations of this, not
a fifth script. One of them is a column on the project; the other two are environment the engine
reads, set here so that a condition is one command line and not a shell prologue somebody forgets:

    --method iterative|explore   the new project's `method`   read by jobs.ingest_chain
    --gate                       APERTURE_FOLLOW=marked       read by synth._marked_here
    --no-residual                APERTURE_RESIDUAL=off        read by R4's residual pass

`APERTURE_RESIDUAL` is named here first, for the residual pass to adopt. Until it reads that name
the flag is inert, and the run says so rather than reporting a condition it did not apply.
"""
from __future__ import annotations

import argparse
import contextlib
import json
import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent)]      # eval_metrics, then the app package


def plan(pid: str, mids: list[str]) -> list[dict]:
    """The steps `jobs.ingest_chain` would have queued, without the job row or the thread.

    Standing in for `jobs.start` rather than restating the list: the chain is one of the things
    the eval loop is measuring changes to, and a second copy of it here would be wrong the first
    time somebody edited the real one.
    """
    from app import jobs

    got: list[dict] = []
    real = jobs.start
    jobs.start = lambda conn_factory, project, runs: got.extend(runs)
    try:
        jobs.ingest_chain(pid, mids)
    finally:
        jobs.start = real
    return got


def _reads_residual() -> bool:
    """Whether the engine has adopted `APERTURE_RESIDUAL` yet. Grepping the source rather than
    asserting the condition held: `--no-residual` was named here before the pass that obeys it
    existed, and a report that says a condition was applied when nothing read it is worse than no
    condition at all."""
    return any("APERTURE_RESIDUAL" in p.read_text(encoding="utf-8", errors="ignore")
               for p in (HERE.parent / "app").rglob("*.py"))


@contextlib.contextmanager
def trace(store):
    """Print each step's line as it starts and its tokens as it ends.

    Around `store`, not inside `jobs`: every step already writes its sentence on a run row for the
    page to poll, and a terminal is just another reader of the same rows.
    """
    start_run, finish_run = store.start_run, store.finish_run

    def started(conn, pid, kind, mid, line, job=None):
        print(f"  {line}", flush=True)
        return start_run(conn, pid, kind, mid, line, job)

    def finished(conn, rid, **kw):
        print(f"    {kw.get('tokens_in', 0)} in / {kw.get('tokens_out', 0)} out"
              + (f" — {kw['error']}" if kw.get("error") else ""), flush=True)
        for note in kw.get("notes") or []:
            print(f"    set aside: {note}", flush=True)
        return finish_run(conn, rid, **kw)

    store.start_run, store.finish_run = started, finished
    try:
        yield
    finally:
        store.start_run, store.finish_run = start_run, finish_run


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Read a folder of material and write the record.")
    ap.add_argument("--materials", required=True, type=Path,
                    help="folder of .txt/.md/.docx/.pdf/.csv material")
    ap.add_argument("--focus", default="", help="what the researcher is looking for")
    ap.add_argument("--data", required=True, type=Path,
                    help="a fresh data directory for this reading's database")
    ap.add_argument("--out", required=True, type=Path, help="where to write the record markdown")
    ap.add_argument("--name", default="", help="project name (default: the materials folder's)")
    ap.add_argument("--method", choices=("iterative", "explore"), default=None,
                    help="how this project reads material (default: what a new project does)")
    ap.add_argument("--gate", action="store_true", help="follow a theme only into material its "
                                                        "codes marked (APERTURE_FOLLOW=marked)")
    ap.add_argument("--no-residual", dest="residual", action="store_false", default=True,
                    help="skip the pass over the unmarked passages (APERTURE_RESIDUAL=off)")
    ap.add_argument("--record-calls", action=argparse.BooleanOptionalAction, default=True,
                    help="write the per-call rows to <out>.calls.json (on: they are the only "
                         "record of attempts, cached tokens and seconds, and they die with --data)")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the condition and the steps that would run; call nothing")
    a = ap.parse_args(argv)

    # Set before `app` is imported and before any step reads them. The engine looks the
    # environment up at the moment it needs it, so later would work too — but a condition applied
    # halfway because an import got in first is exactly the confound this pass exists to avoid.
    if a.gate:
        os.environ["APERTURE_FOLLOW"] = "marked"
    if not a.residual:
        os.environ["APERTURE_RESIDUAL"] = "off"

    if (a.data / "aperture.db").exists():
        raise SystemExit(f"{a.data / 'aperture.db'} already exists. Give --data a fresh "
                         f"directory — one reading, one database, so versions stay comparable.")
    # Before `app` is imported: the package reads .env at import with setdefault, and a developer's
    # own APERTURE_DATA_DIR would otherwise decide where this reading lands. A dry run goes to a
    # temporary directory instead — it ingests and plans for real, and leaving its database behind
    # in `--data` would make the run it was rehearsing refuse to start.
    scratch = tempfile.TemporaryDirectory() if a.dry_run else None
    os.environ["APERTURE_DATA_DIR"] = scratch.name if scratch else str(a.data)

    from app import context, db, ingest, intake, jobs, llm, pages, store

    # Said before the first call: a developer's .env may point at the cheap testing provider, and a
    # record made on a different model than its predecessor compares models, not prompts.
    print(f"provider {llm.provider()} · model {llm.model()} — set APERTURE_PROVIDER to change it", flush=True)

    files = sorted(p for p in a.materials.iterdir()
                   if p.suffix.lower() in intake.KINDS and not p.name.startswith("."))
    if not files:
        raise SystemExit(f"no {', '.join(intake.KINDS)} files in {a.materials}")

    conn = db.connect()
    # No `method=` unless one was asked for: the default belongs to `store.create_project`, and a
    # runner with an opinion of its own would read a corpus differently from the application.
    pid = store.create_project(conn, a.name or a.materials.resolve().name, a.focus,
                               **({"method": a.method} if a.method else {}))
    print(f"condition: method={store.project(conn, pid)['method']}"
          f" · gate={'marked' if a.gate else 'off'}"
          f" · residual={'on' if a.residual else 'off' + ('' if _reads_residual() else ' (inert — nothing in app/ reads APERTURE_RESIDUAL yet)')}",
          flush=True)
    mids = []
    for f in files:
        text = intake.extract(f.name, f.read_bytes())
        mid = store.add_material(conn, pid, f.name, text)
        rows = ingest.sentences(text)
        store.save_sentences(conn, mid, rows)
        mids.append(mid)
        print(f"{f.name}: {len(rows)} passages", flush=True)

    runs = plan(pid, mids)
    print(f"{len(runs)} steps: {' → '.join(r['kind'] for r in runs)}", flush=True)
    if a.dry_run:
        print(f"dry run — nothing was called and {a.data} is untouched", flush=True)
        return 0
    with trace(store):
        jobs.run_now(conn, pid, runs)

    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(pages._render("export.md", context.export(conn, pid)), encoding="utf-8")
    import eval_metrics
    metrics = a.out.with_suffix(".metrics.json")
    metrics.write_text(json.dumps(eval_metrics.from_db(conn, pid), indent=2, ensure_ascii=False),
                       encoding="utf-8")
    print(f"\n{a.out}\n{metrics}", flush=True)
    if a.record_calls:
        print(_dump_calls(conn, pid, a.out), flush=True)
    return 0


def _dump_calls(conn, pid: str, out: Path) -> Path:
    """Every attempt at every model call, beside the record. The `run` row keeps a step's totals;
    only these rows say how many calls it took, what was retried, how long each took and how much
    of it the provider served from its own cache — which is half of what a condition costs and is
    gone the moment the data directory is deleted."""
    rows = [dict(r) for r in conn.execute(
        "SELECT c.*, r.kind AS kind, r.material_id AS material_id FROM call c "
        "JOIN run r ON r.id = c.run_id WHERE r.project_id=? "
        "ORDER BY c.started, c.rowid", (pid,))]
    path = out.with_suffix(".calls.json")
    path.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


if __name__ == "__main__":
    raise SystemExit(main())
