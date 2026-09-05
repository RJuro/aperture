#!/usr/bin/env python3
"""Blind judging material for a comparison of two or more conditions.

    python scripts/eval_dossiers.py --pass pass6 --transcripts bench/ellis3 \
        --conditions iterative=bench/p6-iterative explore-r4=bench/p6-explore ...

Each condition is that run's `--data` directory (the record is rendered from its database) or a
`record.md` written earlier, for a condition whose database is gone.

One dossier per condition, lettered and shuffled, in `bench/<pass>/dossiers/`, with the key
sealed in `bench/<pass>/KEY.json` and instructions generated from `scripts/eval_rubric.md`.
`unseal.py` is written beside them and tabulates the judges' reports against the key afterwards.

A dossier is the record's **Themes** and **Materials** sections and nothing else. Not the whole
record: *Processing history* prints the steps that ran, and `reconcile` in that list would tell a
judge which condition they were holding — which is the one thing the shuffle exists to prevent.
Claims are carried over in full, because the claim against its own quote is what dimension 4 is.

Python does the bookkeeping — slicing, lettering, shuffling, sealing. The judgement is two Opus
readers who do not know which record is which (docs/EVAL.md).
"""
from __future__ import annotations

import argparse
import json
import random
import re
import string
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import eval_metrics  # noqa: E402  — `_sections`, so a record is sliced the same way it is counted

RUBRIC = HERE / "eval_rubric.md"

# The two dimensions the four-condition comparison adds to the seven the outside reader marked.
# Coverage is the question the explore workflow exists to answer and the seven do not ask: they
# all mark what the record SAYS, and none of them asks what it walked past.
EXTRA_DIMENSIONS = """### 8. Coverage

What remained unexamined? Take each material's section and ask what a careful reader of the
transcript would have marked that this record does not. Then look at how the record states its
absences: an absence that was **searched for and not found** is a finding, and an absence that
was **never looked for** is a fact about the reading. A record that prints the two in the same
words is claiming the first while doing the second.

Also: does each material's own account stand on its own — could a reader who never saw the theme
list learn what this interview is about from it?

5: the record says what it looked at and what it did not, and the material's own account carries
what the transcript carries. 3: the reading is partial in ways the record does not admit.
1: silences are presented as findings, or whole regions of the material are absent unremarked.

Look at: each material's section against the transcript named for it; the wording of every
"does not appear" and "not assessed"; anything the record calls absent.

### 9. Within-case integrity

Does the material's account read as an **account of that interview**, or as a set of theme labels
with quotations filled in underneath them? A record can score well on every one of the seven
faults and still have dissolved each life into the categories, so that the order in which things
happened, what caused what, and what the participant themselves made of it have gone.

5: each material reads as a reading of that material, and its narrative survives. 3: the account
is a list of themes with the connective tissue removed. 1: the material exists only as evidence
for categories.

Look at: each material's section read end to end, without reading the theme sections first.
"""

_SCORE_KEYS = ("theme_inflation", "concept_drift", "recycled_passages", "pattern_hunger",
               "valence_contradictions", "overreading_absence", "housekeeping", "coverage",
               "within_case_integrity")

# The rubric's own return block, which is cut off with its two-record preamble. Kept verbatim so
# the seven spot checks come back in the shape `eval_rubric.md` asks for.
SPOT_CHECKS = """        "spot_checks": {
          "single_event_as_theme": {"answer": "yes", "evidence": "…"},
          "name_against_definition": {"answer": "no", "evidence": "…"},
          "totalising_account": {"answer": "yes", "evidence": "…"},
          "claim_beyond_quote": {"answer": "yes", "sampled": [
            {"theme": "…", "claim": "…", "quote": "…", "adds": "motive|manner|evaluation|nothing"}
          ]},
          "opposite_readings": {"answer": "no", "evidence": "…"},
          "inference_from_silence": {"answer": "yes", "evidence": "…"},
          "housekeeping_defects": {"answer": "yes", "evidence": "…"}
        }"""

UNSEAL = '''"""Unseal the comparison: the judges' scores against the key. Bookkeeping only."""
import json, re, statistics as st
from pathlib import Path
G = Path(__file__).parent
key = json.loads((G / "KEY.json").read_text())
KEYS = %(keys)r


def scores(path):
    txt = Path(path).read_text()
    # To the LAST brace in the file: `ranking` sits after `records`, and a regex that stops at the
    # first balanced-looking pair drops it.
    m = re.search(r'\\{\\s*"records".*\\}', txt, re.S)
    return json.loads(m.group(0))


judges = {p.stem: scores(p) for p in sorted(G.glob("judge-*.md"))}
letters = sorted(key)
w = max(len(d) for d in KEYS) + 2
print("condition".ljust(w) + "  ".join(f'{key[l]["condition"][:14]:>14s}' for l in letters))
print("letter".ljust(w) + "  ".join(f"{l:>14s}" for l in letters))
for d in KEYS:
    cells = []
    for l in letters:
        got = [j["records"].get(l, {}).get("scores", {}).get(d, {}).get("score")
               for j in judges.values()]
        got = [g for g in got if g is not None]
        cells.append("/".join(str(g) for g in got) + f" ({st.mean(got):.1f})" if got else "—")
    print(f"{d.ljust(w)}" + "  ".join(f"{c:>14s}" for c in cells))
for name, j in judges.items():
    if j.get("ranking"):
        print(f"{name} ranks: " + " > ".join(f'{l}={key[l]["condition"]}' for l in j["ranking"]))
'''


def record_md(path: Path) -> str:
    """One condition's record. A data directory is rendered from its database with the template
    `eval_run.py` uses; a `record.md` is read as it stands.

    Rendered rather than only read, because a condition is a *reading*, not a file: a run that was
    re-read, or given a piece of feedback, has moved on from the markdown it wrote at the end of
    its chain, and judging the stale file would judge a state nothing is in any more.
    """
    if path.is_dir() and (path / "aperture.db").exists():
        sys.path.insert(0, str(HERE.parent))
        from app import context, db, pages

        conn = db.connect(path / "aperture.db")
        pids = [r[0] for r in conn.execute(
            "SELECT id FROM project WHERE removed_at IS NULL ORDER BY created_at")]
        if len(pids) != 1:
            raise SystemExit(f"{len(pids)} projects in {path}; one condition is one reading")
        return pages._render("export.md", context.export(conn, pids[0]))
    md = path / "record.md" if path.is_dir() else path
    if not md.exists():
        raise SystemExit(f"no record and no aperture.db at {path}")
    return md.read_text(encoding="utf-8")


def dossier(md: str, letter: str, names: dict[str, str]) -> str:
    """One record's Themes and Materials sections, with every condition's name replaced by its
    letter. Names are scrubbed across all conditions, not just this one: a record that mentions a
    sibling condition would name it as plainly as it names its own."""
    top = dict(eval_metrics._sections(md, "##"))
    out = f"# Record {letter}\n\n## Themes\n{top.get('Themes', '')}\n## Materials\n" \
          f"{top.get('Materials', '')}"
    # Longest name first, so scrubbing "explore" does not leave "-r4" behind out of "explore-r4",
    # and case-insensitively, because a name written into a project title gets capitalised.
    for name in sorted(names, key=len, reverse=True):
        out = re.sub(re.escape(name), f"Record {names[name]}", out, flags=re.I)
    return out


def instructions(letters: list[str], transcripts: Path) -> str:
    """The rubric's seven dimensions and spot checks verbatim, plus the two dimensions this
    comparison adds, plus a return block shaped for however many records there are.

    Generated rather than kept as a second file: the seven dimensions are the standing rubric and
    a copy of them would drift away from it the first time either was edited.
    """
    body = RUBRIC.read_text(encoding="utf-8")
    body = body[body.index("## The seven dimensions"):body.index("## What to return")]
    body = body.replace("## The seven dimensions", "## The nine dimensions", 1)
    body = body.replace("\n---\n\n## Spot checks", "\n" + EXTRA_DIMENSIONS + "\n---\n\n## Spot checks")
    body = body.rstrip().removesuffix("---").rstrip()          # the rule before "What to return"
    scores = ",\n".join(f'          "{k}": {{"score": 1, "evidence": "…quoted line…", '
                        f'"note": "…"}}' for k in _SCORE_KEYS)
    records = ",\n".join(
        f'      "{l}": {{"scores": {{\n{scores}\n        }},\n{SPOT_CHECKS}}}'
        if l == letters[0] else f'      "{l}": {{ "…the same shape…" }}' for l in letters)
    named = ", ".join(f"`{l}.md`" for l in letters)
    return f"""# Marking {len(letters)} records of the same corpus

The files in `dossiers/` — {named} — are {len(letters)} readings of the **same** interviews,
produced by the same instrument configured {len(letters)} different ways. You are not told which
is which, which is newer, or what was changed between them, and the letters are in random order.
Do not guess, and do not let a guess shape a score: a reader who decides which one is meant to be
better will find that it is.

Each dossier is one record's **Themes** and **Materials** sections. A claim is printed as a
numbered sentence with the verbatim quote it rests on and a passage id in brackets; the quote is
the evidence and the claim is what the instrument made of it.

The transcripts these were read from are in `{transcripts}`. **Open them.** Dimensions 8 and 9
cannot be answered from the record alone — they ask what the reading missed and whether the
material survived it, and both need the material.

Mark **each record separately and completely** before comparing any of them.

Rules: read only the dossiers and the transcripts. Do not open `KEY.json`, any database, any
`record.md`, `docs/EVAL.md`, or any other file in the repository, and do not try to work out how
the conditions differ — that is the thing being tested.

---

{body}

---

## What to return

Write your report to the path you were given: a paragraph on what separated the records, then one
JSON object and nothing after it.

```json
{{
  "records": {{
{records}
  }},
  "ranking": ["{'", "'.join(letters)}"],
  "why": "three or four sentences, from the text only"
}}
```

`ranking` is best first, as documents. It is not a guess at which instrument made which.
"""


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Blind dossiers for a comparison of conditions.")
    ap.add_argument("--conditions", nargs="+", required=True, metavar="NAME=PATH",
                    help="per condition: the run's --data directory, or a record.md")
    ap.add_argument("--transcripts", required=True, type=Path,
                    help="the corpus folder the judges may open")
    ap.add_argument("--pass", dest="pass_name", required=True,
                    help="which pass this is; the folder under --bench")
    ap.add_argument("--bench", type=Path, default=Path("bench"))
    ap.add_argument("--seed", type=int, default=7, help="the shuffle, so a build is repeatable")
    a = ap.parse_args(argv)

    conditions = {}
    for spec in a.conditions:
        if "=" not in spec:
            raise SystemExit(f"{spec!r} is not NAME=PATH")
        name, path = spec.split("=", 1)
        if not Path(path).exists():
            raise SystemExit(f"no record at {path}")
        conditions[name] = Path(path)
    if len(conditions) < 2:
        raise SystemExit("a blind comparison needs at least two conditions")

    # Sorted before shuffled, so the same seed gives the same letters however the flags were
    # typed: a coordinator who rebuilds the dossiers halfway through the judging must not
    # renumber them under the judges because they retyped the conditions in another order.
    order = sorted(conditions)
    random.Random(a.seed).shuffle(order)
    letters = list(string.ascii_uppercase[:len(order)])
    names = dict(zip(order, letters))

    out = a.bench / a.pass_name
    (out / "dossiers").mkdir(parents=True, exist_ok=True)
    for name, letter in names.items():
        (out / "dossiers" / f"{letter}.md").write_text(
            dossier(record_md(conditions[name]), letter, names), encoding="utf-8")
    (out / "KEY.json").write_text(json.dumps(
        {letter: {"condition": name, "record": str(conditions[name].resolve())}
         for name, letter in names.items()}, indent=1), encoding="utf-8")
    (out / "INSTRUCTIONS.md").write_text(
        instructions(letters, a.transcripts.resolve()), encoding="utf-8")
    (out / "unseal.py").write_text(UNSEAL % {"keys": list(_SCORE_KEYS)}, encoding="utf-8")

    print(f"{len(names)} dossiers in {out / 'dossiers'} (seed {a.seed})")
    for letter in letters:
        print(f"  {letter} ← {[n for n, l in names.items() if l == letter][0]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
