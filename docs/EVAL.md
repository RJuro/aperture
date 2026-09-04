# The evaluation loop

*How a change to the instrument is shown to have improved a reading, rather than asserted to have.*

An outside reader marked the first Ellis Island record against seven faults: theme inflation,
concept drift, recycled passages, pattern hunger, valence contradictions, overreading absence,
and housekeeping. That critique is the rubric. Every change to a prompt or to a mechanic is
measured by producing the record again on the same corpus with the same focus, and having two
readers who do not know which record is which mark them both.

**The rule that decides the shape of this loop:** quality is judged by readers, never by Python.
`scripts/eval_metrics.py` counts — themes, claims, passages, tokens, totalising words, stray
characters. It never scores. A count sits beside a judgement to explain it; it never stands in
for one. Twelve themes over three materials is a number. Whether that is inflation is a reading.

---

**Pin the provider.** The local `.env` defaults to `minimax` for cheap testing; the live instance and the v1 record used GLM on Mistral. A comparison across models measures the model, not the prompts, so every eval run sets it explicitly: `APERTURE_PROVIDER=mistral python scripts/eval_run.py …`. The runner prints provider and model before its first call.

## The corpus is fixed

Three interviews, one focus, unchanged between versions. The researcher supplies the three files;
until they land, the two interviews in `seed/` stand in — the loop works the same on two.

Put the corpus in one folder and leave it alone. A record produced on different material is not a
version of anything.

## Version 1

For the Ellis Island corpus, v1 already exists: `Ellis Island.md`, produced by the running
instrument on 2026-09-03, three materials, twelve themes, and the record the outside reader
marked. It has no database beside it any more, so its counts come from the record itself:

```
python scripts/eval_metrics.py --record "path/to/Ellis Island.md" > eval/v1.metrics.json
```

For any corpus without a v1 record, produce one with the runner exactly as v2 is produced below,
before the change is made.

## Change the instrument

A prompt in `app/prompts/`, a validator in `app/engine/`, a step in the chain. One change, or one
coherent set of them — a version whose diff cannot be described in a sentence cannot be judged
either, because a mixed result has nothing to attach to.

## Version 2

Same files, same focus, a fresh data directory:

```
python scripts/eval_run.py \
  --materials corpus/ellis-island \
  --focus "experience of migration, economic outcomes, integration" \
  --data eval/v2 --out eval/v2/record.md
```

The runner creates a project, adds every `.txt/.md/.docx/.pdf/.csv` in the folder, and runs
**exactly the chain the application runs** — it takes the plan from `jobs.ingest_chain` rather
than restating it — synchronously, printing each step's line and its tokens as it goes. It writes
`record.md` and `record.metrics.json` beside it. It refuses a `--data` directory that already
holds a database: one reading, one database.

It calls the live model and it costs real money. It respects the same environment the server
does: `APERTURE_PROVIDER`, the provider's key, `APERTURE_MODEL`, `APERTURE_RECORD`.

## The counts, side by side

```
python scripts/eval_metrics.py --compare eval/v1.metrics.json eval/v2/record.metrics.json
```

What it counts, and which dimension each number belongs beside:

| Count | Beside |
|---|---|
| materials · live themes · themes per material · themes with claims in one material / in two or more | theme inflation |
| claims per theme | theme inflation |
| distinct passages per theme; the share of them another theme also cites | recycled passages |
| distinct cited passages over total passages | how much of the corpus was used at all |
| claims set aside by the verify step; run notes saying a quote does not carry a claim | pattern hunger |
| *all · every · each · consistently · no exceptions · across the corpus* in the accounts and the corpus summary | pattern hunger |
| non-Latin characters in the model's prose, where the material is Latin-script | housekeeping |
| a passage id written twice inside one bracket | housekeeping |
| tokens per step | cost |

Nothing in that table is a target. A version that halves the theme count and loses the reading is
worse, and only a reader can say so.

## Blind judging

This is where the verdict comes from.

The coordinator — the person or agent running the loop, who knows which record is which —
prepares two files, **A** and **B**, **in random order**, with every trace of provenance removed:
no version number, no date in the filename, no "v2" in the project name. The corpus summary
already carries the project's name, which is the same in both, so nothing there gives it away.

Two Opus judges, each in a fresh session with no knowledge of this loop, are given both records
and `scripts/eval_rubric.md`. **Neither judge is told which record is newer, which came from the
changed instrument, or what was changed.** A judge who knows which one is supposed to be better
will find that it is.

Each returns one JSON object: a 1–5 score per dimension per record, each with a quoted line from
the record as evidence, plus the seven spot checks answered yes or no with evidence — including
five claims sampled and checked against their own quotes.

Two judges, because one judge's 3 and another's 4 on the same document is information about the
rubric. Where they diverge by two points or more on a dimension, read both their evidence lines
before believing either.

## Reading the result

Put the two judgements and the two metrics files beside each other. The judgement decides whether
the change helped; the counts say what moved underneath it and are how a surprising judgement is
investigated. A version that scores better on theme inflation while the theme count is unchanged
is worth understanding before it is believed.

Keep every version's record, metrics and judge output. The loop is only worth running if v3 can
be measured against v2 the same way.

---

## Files

| | |
|---|---|
| `scripts/eval_run.py` | produce a record from a folder of material, synchronously |
| `scripts/eval_metrics.py` | count a finished reading — from its database, or from its record |
| `scripts/eval_rubric.md` | what the blind judges are given |
| `tests/test_eval_metrics.py` | the counting, and that the runner runs the application's chain |

## Results

### Pass 1 — 2026-09-04, three Ellis Island interviews, GLM-5.2 on Mistral, same focus

v1 = the record the outside reader critiqued (old prompts). v2 = prompts v2 (ACCOUNT no longer
rewrites gists; no inference from silence; no count-words; `claimed`/`shared` slots; theme ceiling
4 + 2n) plus the VERIFY step. Bookkeeping, v1 → v2: themes 12 → 10; single-material themes 4 → 0;
shared-passage share 0.12 → 0.077; "all" 20 → 5, "every" 13 → 1, "no exceptions" 1 → 0; non-Latin
characters 2 → 0; doubled ids 2 → 0; VERIFY set aside 2 claims. Wall 50 min.

Two blind Opus judges, records shuffled (A = v2, B = v1), scores 1–5 (5 = clean):

| dimension | judge 1 v2 / v1 | judge 2 v2 / v1 |
|---|---|---|
| theme inflation | 5 / 2 | 4 / 2 |
| concept drift | 4 / 2 | 4 / 2 |
| recycled passages | 5 / 2 | 5 / 2 |
| pattern hunger | 4 / 2 | 4 / 2 |
| valence contradictions | 5 / 2 | 4 / 2 |
| overreading absence | 5 / 1 | 5 / 1 |
| housekeeping | 4 / 1 | 4 / 2 |

Both judges: "which reads better: A" (v2). Full reports: `bench/judge-1.md`, `bench/judge-2.md`
(the `bench/` folder is local, not in git).

What the judges still hold against v2 — the v3 list: claims that add an evaluative shade or
harden a hedge into a fact (3/5 and 2/5 sampled) and one added motive — VERIFY passed them;
material summaries adding details the claims do not carry (the DOC summary is not verified);
compound theme definitions ("binds two things") and a claim filed under a theme its definition
does not cover; one episode-level tension across themes on different passage ids, unmarked; a
theme name cut off by the word cap ("… and as discipline to"); mixed quote marks; a
self-contradicting count in a summary; exclusion notes cut mid-word (fixed in 524a076).

### Pass 2 — 2026-09-04, same corpus and model, v2 vs v3

v3 = prompts v3 (THEMES: one pattern per gist, names ≤ 8 words, "if two patterns are present,
return two themes"; THREAD: claim inside the definition, hedges stay hedges; VERIFY: sharpened
`partly`; DOC: no facts beyond the claims) plus VERIFY-SUMMARY. Bookkeeping, v2 → v3: claims
225 → 209; cited passages 208 → 191; shared-passage share 0.077 → 0.084; VERIFY set aside 2 → 1;
summary sentences flagged or removed 0 → 8; theme rewrites in the history 2 → 4. Wall 25 min.

Two blind judges (A = v3, B = v2), scores 1–5:

| dimension | judge 3 v3 / v2 | judge 4 v3 / v2 |
|---|---|---|
| theme inflation | 3 / 3 | 3 / 4 |
| concept drift | 2 / 4 | 2 / 4 |
| recycled passages | 4 / 3 | 3 / 3 |
| pattern hunger | 2 / 3 | 3 / 4 |
| valence contradictions | 5 / 5 | 5 / 5 |
| overreading absence | 2 / 3 | 4 / 4 |
| housekeeping | 2 / 3 | 2 / 3 |

Both judges: "which reads better: B" (v2). **v3 is a regression on drift**, and the mechanism is
visible in the record: four theme definitions were rewritten, all widenings ("anti-Jewish violence
and war" → "violence, restriction, or erasure", which then files a complaint about Austrian rules
beside a pogrom), and one bureaucratic axis was split into two counted themes — the THEMES rule
"if two patterns are genuinely present, return two themes" invited exactly that. v3's corpus
summary also stated one material's position backwards. What the judges kept from v3: the summary
self-audit (six sentences caught going past the claims, where v2 lets "Russia and Japan", "Ivy
League college", "the 1980 fire" into summaries no claim carries); distinct second readings of a
shared passage rather than restatements. Costs both judges name: v3's additions are causes and
motives where v2's are evaluations; the more careful record reads more mechanically.

Decisions: v3.1 THEMES installed (9127683) — one pattern per gist without the split clause; a
theme keeps its words unless a gathered code contradicts them, with the forbidden widening named.
THREAD/VERIFY/DOC/VERIFY-SUMMARY v3 kept. Live stays on v2 until v3.1 is judged. Open: an
entailment check of the PROJECT summary against the accounts (the inverted sentence); VERIFY at
`medium` still passes hardened hedges in both versions. Caveat that stands over every pass: one
run per version — some of each difference is run-to-run variation, which is why every pass has
two judges and why no prompt change is kept on one pass alone.
