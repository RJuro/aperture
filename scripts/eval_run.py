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
the same directory would be a third reading of a project that already has one.
"""
from __future__ import annotations

import argparse
import contextlib
import json
import os
import sys
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
    a = ap.parse_args(argv)

    if (a.data / "aperture.db").exists():
        raise SystemExit(f"{a.data / 'aperture.db'} already exists. Give --data a fresh "
                         f"directory — one reading, one database, so versions stay comparable.")
    # Before `app` is imported: the package reads .env at import with setdefault, and a developer's
    # own APERTURE_DATA_DIR would otherwise decide where this reading lands.
    os.environ["APERTURE_DATA_DIR"] = str(a.data)

    from app import context, db, ingest, intake, jobs, pages, store

    files = sorted(p for p in a.materials.iterdir()
                   if p.suffix.lower() in intake.KINDS and not p.name.startswith("."))
    if not files:
        raise SystemExit(f"no {', '.join(intake.KINDS)} files in {a.materials}")

    conn = db.connect()
    pid = store.create_project(conn, a.name or a.materials.resolve().name, a.focus)
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
    with trace(store):
        jobs.run_now(conn, pid, runs)

    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(pages._render("export.md", context.export(conn, pid)), encoding="utf-8")
    import eval_metrics
    metrics = a.out.with_suffix(".metrics.json")
    metrics.write_text(json.dumps(eval_metrics.from_db(conn, pid), indent=2, ensure_ascii=False),
                       encoding="utf-8")
    print(f"\n{a.out}\n{metrics}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
