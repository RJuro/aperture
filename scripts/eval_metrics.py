#!/usr/bin/env python3
"""Bookkeeping over a finished reading. Counting only — nothing here judges anything.

    python scripts/eval_metrics.py --data runs/v2                 # from the database
    python scripts/eval_metrics.py --record runs/v1/record.md     # from a record, when there is no database
    python scripts/eval_metrics.py --compare v1.metrics.json v2.metrics.json

The seven dimensions the outside reader marked the record against are read by people, not by
regular expressions: a theme that rests on one life, a definition widened to admit a material, a
claim that adds a motive the quote does not carry. Those go to blind judges (`docs/EVAL.md`).

What *is* mechanical is how much of each there is room for, and that is what this counts: themes
per material, how many rest on one material, how many distinct passages each theme cites and how
often two themes cite the same one, how much of the corpus is cited at all, how many claims a
verify step set aside, how many times the prose says *all* or *every*, stray non-Latin characters,
an id written twice inside one bracket, and the tokens each step spent.

From a database it also counts what the four-condition comparison needs and a record cannot say:
the model calls under those steps with their attempts, cached and reasoning tokens and seconds;
what became of every theme × material pair, including the pairs nothing ever looked at; the lines
too short to be full; how much of each material no code touched; and the theme holds.

A count is not a score. 12 themes over 3 materials is a number; whether it is inflation is a
reading. These numbers sit *beside* the judges' scores, never in place of them.
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path

# Words that assert a pattern holds without exception. Counted where the model generalises — the
# theme accounts and the corpus summary — never in the material's own words.
HEDGES = ("all", "every", "each", "consistently", "no exceptions", "across the corpus")

# The claim count below which the record prints a line as "sparse". A copy of
# `synth.MIN_MOMENTS` rather than an import: counting a finished reading must not have to load the
# engine, and this number changes about once a year.
SPARSE_BELOW = 4

_SID = re.compile(r"\bS\d{2,5}\b")
_BRACKET = re.compile(r"\[([^\[\]\n]{0,300})\]")


# ---- the small mechanical checks -----------------------------------------------------------------

def hedges(texts: list[str]) -> dict[str, int]:
    """How often each totalising word appears. Counted, not judged: a corpus really can be
    unanimous, and the word is only worth a look when the account cannot show it."""
    joined = "\n".join(texts).lower()
    return {w: len(re.findall(rf"\b{re.escape(w)}\b", joined)) for w in HEDGES}


def non_latin(text: str) -> list[str]:
    """Alphabetic characters from another script. `M-3` slips a Chinese particle into English
    prose now and then, and nobody reading a finished record expects to find one."""
    return [c for c in text
            if c.isalpha() and not unicodedata.name(c, "").startswith("LATIN")]


def doubled_ids(text: str) -> list[str]:
    """Brackets citing the same passage twice — `[S034, S038, S034]`. Two claims resting on one
    sentence, written as though they were two sentences."""
    out = []
    for m in _BRACKET.finditer(text):
        ids = _SID.findall(m.group(1))
        if len(ids) != len(set(ids)):
            out.append(m.group(0))
    return out


def _overlap(passages: dict[str, set]) -> tuple[dict[str, float], float]:
    """Per theme, the share of its distinct passages that another theme also cites; and the same
    over every cited passage. The recycled-passage dimension, as a count."""
    per, shared_any = {}, set()
    for name, mine in passages.items():
        others = set().union(*(p for k, p in passages.items() if k != name)) if len(passages) > 1 \
            else set()
        also = mine & others
        shared_any |= also
        per[name] = round(len(also) / len(mine), 3) if mine else 0.0
    every = set().union(*passages.values()) if passages else set()
    return per, (round(len(shared_any) / len(every), 3) if every else 0.0)


def _blank(source: str) -> dict:
    """Every key both paths emit, so `--compare` lines up whatever it is given."""
    return {"source": source, "materials": 0, "themes_live": 0, "themes_per_material": None,
            "themes_in_one_material": 0, "themes_in_two_or_more": 0, "claims_total": 0,
            "claims_per_theme": {}, "materials_per_theme": {}, "passages_per_theme": {},
            "shared_passage_share_per_theme": {}, "shared_passage_share": 0.0,
            "cited_passages": 0, "total_passages": None, "cited_share": None,
            "set_aside": {}, "hedge_words": {}, "non_latin": {}, "doubled_ids": [],
            "tokens_per_step": {},
            # Only the database knows these. A record prints neither the calls under a step nor
            # the pairs nothing was written for, so off a record they stay null — "not measured",
            # which is what `--compare` prints them as, and never a nought.
            "calls": None, "cells": None, "sparse_lines": None, "unmarked_share": None,
            "candidates": None, "proposed": None, "frozen": None}


# ---- from the database ---------------------------------------------------------------------------

def from_db(conn: sqlite3.Connection, pid: str) -> dict:
    """Everything countable about one project's reading as it stands in the database."""
    out = _blank("db")
    mats = conn.execute("SELECT id, name, title FROM material WHERE project_id=? "
                        "AND removed_at IS NULL", (pid,)).fetchall()
    mids = [m[0] for m in mats]
    themes = conn.execute("SELECT id, name, gist FROM theme WHERE project_id=? AND status='live'",
                          (pid,)).fetchall()
    out["materials"] = len(mats)
    out["themes_live"] = len(themes)
    out["themes_per_material"] = round(len(themes) / len(mats), 2) if mats else None

    passages: dict[str, set] = {}
    for tid, name, _gist in themes:
        rows = conn.execute("SELECT material_id, sid FROM moment WHERE theme_id=? AND "
                            "status='live'", (tid,)).fetchall()
        rows = [r for r in rows if r[0] in mids]
        out["claims_per_theme"][name] = len(rows)
        carrying = {r[0] for r in rows}
        out["materials_per_theme"][name] = len(carrying)
        passages[name] = {tuple(r) for r in rows}
        out["passages_per_theme"][name] = len(passages[name])
        if len(carrying) == 1:
            out["themes_in_one_material"] += 1
        elif len(carrying) > 1:
            out["themes_in_two_or_more"] += 1
    out["claims_total"] = sum(out["claims_per_theme"].values())
    out["shared_passage_share_per_theme"], out["shared_passage_share"] = _overlap(passages)

    cited = set().union(*passages.values()) if passages else set()
    total = conn.execute("SELECT COUNT(*) FROM sentence WHERE material_id IN "
                         f"({','.join('?' * len(mids)) or 'NULL'})", mids).fetchone()[0]
    out["cited_passages"] = len(cited)
    out["total_passages"] = total
    out["cited_share"] = round(len(cited) / total, 3) if total else None

    out["set_aside"] = _set_aside(conn, pid)

    accounts = [r[0] for r in conn.execute(
        "SELECT text FROM summary WHERE scope='theme' AND status='live' AND ref_id IN "
        "(SELECT id FROM theme WHERE project_id=?)", (pid,))]
    corpus = [r[0] for r in conn.execute(
        "SELECT text FROM summary WHERE scope='project' AND ref_id=? AND status='live'", (pid,))]
    out["hedge_words"] = hedges(accounts + corpus)

    prose = accounts + corpus + [t[2] or "" for t in themes] + [
        r[0] for r in conn.execute(
            "SELECT text FROM summary WHERE scope='material' AND status='live' AND ref_id IN "
            f"({','.join('?' * len(mids)) or 'NULL'})", mids)] + [
        r[0] for r in conn.execute(
            "SELECT claim FROM moment WHERE status='live' AND material_id IN "
            f"({','.join('?' * len(mids)) or 'NULL'})", mids)]
    material_text = "".join(r[0] for r in conn.execute(
        "SELECT text FROM material WHERE project_id=? AND removed_at IS NULL", (pid,)))
    out["non_latin"] = _non_latin_report(prose, material_text)
    out["doubled_ids"] = doubled_ids("\n".join(prose))

    for kind, n, ti, to in conn.execute(
            "SELECT kind, COUNT(*), SUM(tokens_in), SUM(tokens_out) FROM run WHERE project_id=? "
            "GROUP BY kind ORDER BY kind", (pid,)):
        out["tokens_per_step"][kind] = {"runs": n, "in": ti or 0, "out": to or 0}

    out["calls"] = _calls(conn, pid)
    out["cells"] = _cells(conn, pid)
    out["sparse_lines"] = conn.execute(
        "SELECT COUNT(*) FROM (SELECT 1 FROM moment WHERE status='live' AND theme_id IN "
        "(SELECT id FROM theme WHERE project_id=? AND status='live') AND material_id IN "
        f"({','.join('?' * len(mids)) or 'NULL'}) "
        "GROUP BY material_id, theme_id HAVING COUNT(*) < ?)",
        [pid, *mids, SPARSE_BELOW]).fetchone()[0]
    out["unmarked_share"] = _unmarked_share(conn, pid)
    holds = dict(conn.execute("SELECT hold, COUNT(*) FROM theme WHERE project_id=? AND "
                              "status='live' GROUP BY hold", (pid,)))
    out["candidates"] = holds.get("candidate", 0)
    out["frozen"] = holds.get("frozen", 0)
    # A proposal is a count Python made, not a promotion anybody accepted (`store.propose`), so it
    # is a share of the candidates and not a fourth hold.
    out["proposed"] = conn.execute(
        "SELECT COUNT(*) FROM theme WHERE project_id=? AND status='live' AND hold='candidate' "
        "AND proposed_at IS NOT NULL", (pid,)).fetchone()[0]
    return out


# ---- what the model actually did, and what the reading left alone --------------------------------

_CALL_COLUMNS = ("calls", "attempts", "tokens_in", "tokens_out", "tokens_cached",
                 "tokens_reasoning", "seconds_total")
_CALL_SELECT = ("COUNT(*) AS calls, SUM(c.attempt) AS attempts, SUM(c.tokens_in) AS tokens_in, "
                "SUM(c.tokens_out) AS tokens_out, SUM(c.tokens_cached) AS tokens_cached, "
                "SUM(c.tokens_reasoning) AS tokens_reasoning, SUM(c.seconds) AS seconds_total")
_CALL_FROM = "FROM call c JOIN run r ON r.id = c.run_id WHERE r.project_id=?"


def _share(part, whole) -> float | None:
    """None where the provider reported nothing. A share of an unreported total is not 0.0 — the
    `call` table keeps 'not reported' and 'none' apart on purpose (AR-09), and so does this."""
    if part is None or not whole:
        return None
    return round(part / whole, 3)


def _calls(conn: sqlite3.Connection, pid: str) -> dict:
    """One row per attempt at one model call, totalled. `run.tokens_in/out` are a step's totals and
    a step is a dozen calls; only these rows carry cached and reasoning tokens, seconds, and the
    retries — and on the first live M-3 run four output tokens in five were reasoning.

    `attempts` sums the attempt NUMBERS, so it equals `calls` exactly where every call was
    answered first time; the gap between them is what would not parse and had to be asked again.
    """
    total = conn.execute(f"SELECT {_CALL_SELECT} {_CALL_FROM}", (pid,)).fetchone()
    out = {k: total[k] for k in _CALL_COLUMNS}
    if out["seconds_total"] is not None:
        out["seconds_total"] = round(out["seconds_total"], 1)
    out["reasoning_share"] = _share(total["tokens_reasoning"], total["tokens_out"])
    out["cached_share"] = _share(total["tokens_cached"], total["tokens_in"])
    out["per_kind"] = {
        r["kind"]: {k: (round(r[k], 1) if k == "seconds_total" and r[k] is not None else r[k])
                    for k in _CALL_COLUMNS}
        for r in conn.execute(f"SELECT r.kind AS kind, {_CALL_SELECT} {_CALL_FROM} "
                              "GROUP BY r.kind ORDER BY r.kind", (pid,))}
    return out


def _cells(conn: sqlite3.Connection, pid: str) -> dict:
    """Theme × material: what became of every pair. Three outcomes today and a fourth, `residual`,
    where R4's omission pass looked through the unmarked passages and found nothing.

    A pair with no row at all is `not_assessed`, counted separately for the reason
    `store.followed` exists: a theme developed after a material was read was never looked for in
    it, and reading that silence as "looked for and too thin" asserts a reading that never ran.
    """
    out = {k: 0 for k in ("line", "thin", "skipped", "residual")}
    rows = conn.execute(
        "SELECT f.outcome, COUNT(*) FROM follow f "
        "JOIN material m ON m.id = f.material_id AND m.removed_at IS NULL "
        "JOIN theme t ON t.id = f.theme_id AND t.status='live' "
        "WHERE m.project_id=? AND t.project_id=? AND f.status='live' "
        "GROUP BY f.outcome", (pid, pid)).fetchall()
    for outcome, n in rows:
        out[outcome] = out.get(outcome, 0) + n
    pairs = conn.execute(
        "SELECT (SELECT COUNT(*) FROM theme WHERE project_id=? AND status='live') * "
        "(SELECT COUNT(*) FROM material WHERE project_id=? AND removed_at IS NULL)",
        (pid, pid)).fetchone()[0]
    out["not_assessed"] = pairs - sum(n for _, n in rows)
    return out


def _unmarked_share(conn: sqlite3.Connection, pid: str) -> dict:
    """Per material, the share of its passages no code hit — how much of it the reading walked
    past. The denominator for coverage, and the pool RESIDUAL reads."""
    return {r["name"]: _share(r["total"] - r["marked"], r["total"])
            for r in conn.execute(
                "SELECT m.name AS name, "
                "(SELECT COUNT(*) FROM sentence s WHERE s.material_id=m.id) AS total, "
                "(SELECT COUNT(DISTINCT h.sid) FROM code_hit h WHERE h.material_id=m.id) AS marked "
                "FROM material m WHERE m.project_id=? AND m.removed_at IS NULL "
                "ORDER BY m.created_at", (pid,))}


def _set_aside(conn: sqlite3.Connection, pid: str) -> dict:
    """What the reading threw away. Three counters, because they arrive from three places and the
    verify step is still being built — a missing column is 'not measured', not zero."""
    notes = [n for (raw,) in conn.execute(
        "SELECT notes FROM run WHERE project_id=? AND notes NOT IN ('', '[]')", (pid,))
        for n in json.loads(raw or "[]")]
    have = {r[1] for r in conn.execute("PRAGMA table_info(moment)")}
    verified = None
    if "support_note" in have:
        verified = conn.execute(
            "SELECT COUNT(*) FROM moment WHERE status='superseded' AND COALESCE(support_note,'')"
            "<>'' AND material_id IN (SELECT id FROM material WHERE project_id=?)",
            (pid,)).fetchone()[0]
    return {"verify_superseded_claims": verified,
            "runs_saying_does_not_carry_it": sum("does not carry it" in n for n in notes),
            "notes_total": len(notes)}


def _non_latin_report(prose: list[str], material_text: str) -> dict:
    """Stray script in the model's prose — but only where the material itself is Latin. A Danish
    corpus with a Greek quotation in it would otherwise be reported as a defect for ever."""
    in_material = non_latin(material_text)
    letters = sum(c.isalpha() for c in material_text)
    if letters and len(in_material) / letters > 0.02:
        return {"checked": False, "why": "the material is not Latin-script", "chars": None}
    found = [c for t in prose for c in non_latin(t)]
    return {"checked": True, "chars": len(found), "characters": sorted(set(found))}


# ---- from a record, where there is no database -----------------------------------------------------

_THEME_CLAIMS = re.compile(r"^\*\*(?P<title>.+?)\*\* — .*? · (?P<claims>\d+) claims?\s*$", re.M)
_CLAIMS_LINE = re.compile(r"^(?P<claims>\d+) claims?\s*$", re.M)
_QUOTE = re.compile(r"^\s+> .*?\[(?P<sid>S\d+)\]\s*$", re.M)
_TOKENS = re.compile(r"^- \*\*(?P<step>.+?)\*\* — (?P<runs>\d+) runs? · (?P<in>\d+) input "
                     r"tokens? · (?P<out>\d+) output tokens?", re.M)

# A material's own sections, which sit at the same heading level as the themes read in it.
_NOT_A_THEME = ("Before reading", "After reading", "What to look for")


def _sections(md: str, level: str) -> list[tuple[str, str]]:
    """[(heading, body)] for one heading level, in order."""
    parts = re.split(rf"^{level} (.+)$", md, flags=re.M)[1:]
    return list(zip(parts[0::2], parts[1::2]))


def _under_the_materials(mats_md: str) -> dict[str, list[tuple[str, int, set]]]:
    """Theme name → one (material, claims, passages) block per material carrying it.

    The record prints each claim under the material it was read in, so a theme's claims are
    gathered back up from the material sections — the same direction the analysis runs in.
    """
    out: dict[str, list[tuple[str, int, set]]] = {}
    for title, body in _sections(mats_md, "###"):
        for name, block in _sections(body, "####"):
            if name.strip() in _NOT_A_THEME:
                continue
            n = _CLAIMS_LINE.search(block)
            out.setdefault(name.strip(), []).append(
                (title.strip(), int(n["claims"]) if n else 0,
                 {q["sid"] for q in _QUOTE.finditer(block)}))
    return out


def _under_the_theme(body: str, sub_level: str) -> list[tuple[str, int, set]]:
    """The same blocks off a record written before the claims moved under their material."""
    here = next((b for h, b in _sections(body, sub_level)
                 if h.startswith("Materials where this theme appears")), "")
    found = list(_THEME_CLAIMS.finditer(here))
    cut = [m.start() for m in found] + [len(here)]
    return [(m["title"], int(m["claims"]),
             {q["sid"] for q in _QUOTE.finditer(here[cut[i]:cut[i + 1]])})
            for i, m in enumerate(found)]


def from_record(path: Path | str) -> dict:
    """The same counts, read back off a finished record. Less than the database knows — the corpus
    has no passage count in it and the runs are already totalled — so those keys stay null."""
    md = Path(path).read_text(encoding="utf-8")
    out = _blank("record")
    top = dict(_sections(md, "##"))

    passages: dict[str, set] = {}
    accounts: list[str] = []
    themes_md, mats_md = top.get("Themes", ""), top.get("Materials", "")
    # Two record shapes: the older one lists themes at ### with #### sub-sections; since the
    # corpus/single-material split, ### is the group heading, #### the theme, ##### the sub-section.
    theme_level, sub_level = ("####", "#####") if re.search(r"^##### ", themes_md, re.M) else ("###", "####")
    # And two places the claims can be: under their material since the record was flipped, under
    # their theme before it. A quoted passage in the material sections is what tells them apart.
    gathered = _under_the_materials(mats_md) if _QUOTE.search(mats_md) else {}
    for name, body in _sections(themes_md, theme_level):
        name = name.strip()
        accounts.append(body.split(sub_level)[0])
        blocks = gathered.get(name) or _under_the_theme(body, sub_level)
        out["claims_per_theme"][name] = sum(c for _, c, _ in blocks)
        out["materials_per_theme"][name] = len(blocks)
        passages[name] = {(title, sid) for title, _, sids in blocks for sid in sids}
        out["passages_per_theme"][name] = len(passages[name])
        if len(blocks) == 1:
            out["themes_in_one_material"] += 1
        elif len(blocks) > 1:
            out["themes_in_two_or_more"] += 1

    out["themes_live"] = len(passages)
    out["materials"] = len(_sections(mats_md, "###"))
    out["themes_per_material"] = (round(out["themes_live"] / out["materials"], 2)
                                  if out["materials"] else None)
    out["claims_total"] = sum(out["claims_per_theme"].values())
    out["shared_passage_share_per_theme"], out["shared_passage_share"] = _overlap(passages)
    out["cited_passages"] = len(set().union(*passages.values())) if passages else 0

    excluded = [ln[2:] for ln in top.get("Excluded from the analysis", "").splitlines()
                if ln.startswith("- ")]
    out["set_aside"] = {"verify_superseded_claims": None,
                        "runs_saying_does_not_carry_it": sum("does not carry it" in n
                                                             for n in excluded),
                        "notes_total": len(excluded)}
    out["hedge_words"] = hedges(accounts + [top.get("Across the corpus", "")])
    out["non_latin"] = _non_latin_report([md], md)
    out["doubled_ids"] = doubled_ids(md)
    for m in _TOKENS.finditer(top.get("Processing history", "")):
        out["tokens_per_step"][m["step"]] = {"runs": int(m["runs"]), "in": int(m["in"]),
                                             "out": int(m["out"])}
    return out


# ---- comparing two of them -------------------------------------------------------------------------

def _flat(d, prefix="") -> dict[str, str]:
    out = {}
    for k, v in d.items():
        key = f"{prefix}{k}"
        if isinstance(v, dict):
            out.update(_flat(v, f"{key}."))
        elif isinstance(v, list):
            out[key] = f"{len(v)} — {', '.join(map(str, v[:3]))}" if v else "0"
        else:
            out[key] = "—" if v is None else str(v)
    return out


def compare(a: dict, b: dict) -> str:
    """Two readings side by side. Every key either has, in the order they were given."""
    fa, fb = _flat(a), _flat(b)
    keys = list(fa) + [k for k in fb if k not in fa]
    w = max([len(k) for k in keys] + [6])
    lines = [f"{'metric'.ljust(w)}  {'a':>12}  {'b':>12}", f"{'-' * w}  {'-' * 12}  {'-' * 12}"]
    for k in keys:
        lines.append(f"{k.ljust(w)}  {fa.get(k, '—'):>12}  {fb.get(k, '—'):>12}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Count what a reading contains. Nothing is judged.")
    ap.add_argument("--data", type=Path, help="a data directory holding aperture.db")
    ap.add_argument("--project", default="", help="project id, when the database holds several")
    ap.add_argument("--record", type=Path, help="a record.md, when the database is gone")
    ap.add_argument("--compare", nargs=2, metavar=("A.json", "B.json"))
    a = ap.parse_args(argv)

    if a.compare:
        print(compare(*(json.loads(Path(p).read_text()) for p in a.compare)))
        return 0
    if a.record:
        print(json.dumps(from_record(a.record), indent=2, ensure_ascii=False))
        return 0
    if not a.data:
        ap.error("give --data, --record or --compare")

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import os
    os.environ["APERTURE_DATA_DIR"] = str(a.data)
    from app import db

    conn = db.connect()
    pid = a.project
    if not pid:
        rows = conn.execute("SELECT id FROM project ORDER BY created_at").fetchall()
        if len(rows) != 1:
            raise SystemExit(f"{len(rows)} projects in {a.data}; name one with --project")
        pid = rows[0][0]
    print(json.dumps(from_db(conn, pid), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
