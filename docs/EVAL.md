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
