# Aperture — build plan

*Written 2026-09-02, after three rounds of simulation in `MASSHINE_Qual_LLM`. That repo stays as
the record of what was learned; this one is the product, built from the ground up, lean.*

## 0. What it is

A reading companion for qualitative material. **Any material**: interviews, focus groups, field
notes, documents, open-ended survey text. It takes each piece in, works out what shape it has and
how to display it, reads it, codes it, groups codes into themes, and then presents each theme as a
**thread through that material**: a stack of key moments, each a short claim resting on a verbatim
quote highlighted in the text next to it. The researcher reacts to moments, threads and summaries;
doubt is checked against the material; feedback re-runs one layer down, never the whole reading.
Every number on a page is a derivation over rows the page links to. Every claim shows the words it
rests on.

Interviews are the first shape, never the only one. Nothing in the engine may assume a speaker.

Not in v1: audio (Voxtral), a designed UI, htmx, multi-user, the simulation harness.

## 1. Layers, and which way things run

| Layer | Artifact | Made by | Scope |
|---|---|---|---|
| L0 | material — sentences with ids | ingest (Python) | material |
| L1 | **frame** — kind, display, speakers, segments, title, orientation | FRAME | material |
| L2 | codes — name, definition, the sentence ids they apply to | READ | material |
| L3 | themes — name, gist, the codes they gather | THEMES | project |
| L4 | material synthesis — summary + threads (moments: claim + quote + sid) | DOC | material |
| L5 | project synthesis — summary + theme gists, citing moments | PROJECT | project |

**Up** (material arrives): ingest → FRAME → READ → THEMES → DOC → PROJECT, one background job,
one line a person can read (*"Working out how this is laid out"*, *"Reading Grande"*, *"Finding
themes"*, *"Writing what stands out in Grande"*, *"Updating the project summary"*).

**Down** (feedback): a rerun re-makes one layer and treats the layer below as input it may amend
but never rebuild. READ never reruns on feedback; material is read once. FRAME is about the
material's *form*, so no analytic feedback touches it — it has its own verb (§4).

| Feedback on | Runs | Sees, in addition to its normal inputs | May change |
|---|---|---|---|
| a moment — *doubt* | **CHECK**, not a rerun | the doubt verbatim; passages of this material no moment cites | nothing; records a verdict with quotes |
| a moment — *agree / note* | nothing now | — | stance stored, shown, exported; enters the next DOC rerun as a directive |
| a thread in one material | DOC for that material, that theme only | all feedback on this thread, verbatim | the thread's moments; may cite new sentences; may *propose* a theme gist change (flagged, not applied) |
| a material's summary | DOC for that material | all feedback on this material | its summary and every thread; may add codes, marked `origin=rerun` |
| a theme (project level) | THEMES, then DOC for each material where the theme has moments | the feedback verbatim | the theme set (rename, merge, split); affected threads |
| the project summary | DOC for every material with the feedback as directive, then PROJECT | per material as above | summaries, threads, project summary — **never codes' original hits, never READ, never FRAME** |
| focus (what you are looking for) | nothing now | — | the next READ and every later DOC carry it |
| *"check this against the material"* anywhere | CHECK | the question; uncited passages in scope | nothing; records verdict, quotes, searched count |
| *"this is laid out wrong"* + a hint | FRAME for that material | the hint verbatim; the current frame | frame only; codes, themes and moments are untouched (sentence ids never change) |

`rerun.plan(feedback) -> [Run]` is a table-driven Python function, and its test is this table.

## 2. What each prompt shows the model

Prompts are files in `app/prompts/*.md` with named slots. Python fills them; a test snapshots the
compiled prompt for the fixture, so a change to what the model sees is a visible diff.

| Prompt | Sees | Returns (JSON) | Python validates |
|---|---|---|---|
| **FRAME** | the first ~6000 and last ~1500 characters of the raw text; the mechanical speaker scan's result (labels and how often each recurs, or *none found*); the researcher's hint if this is a re-frame | `kind` · `display` · `title` ≤10 words · `speakers: [{label, name, role}]` · `segments: [{anchor, label}]` ≤12 · `orientation` ≤150 words | `kind` ∈ {interview, focus_group, fieldnotes, document, open_text, other}; `display` ∈ {turns, segments, plain}; **every speaker `label` must occur ≥2 times at a line start in the raw text**, unverified ones dropped; if none survive, `display` falls back to plain; every segment `anchor` bound by `anchor.bind`, unbound dropped |
| READ | the brief; the focus verbatim; the live codebook; **the frame** (kind, speakers and roles, segment labels); the material as ids + text, laid out per `display` | `codes: [{code: <existing name> \| {name, definition}, sids}]` | sids exist here; ≤ 40 codes, ≤ 12 new; names unique |
| THEMES | live themes; the codebook with per-material hit counts; the focus; theme feedback verbatim | `themes: [{id \| new, name, gist, code_names, merge_into?}]` | codes exist; ≤ 12 live themes; merges recorded as `merged_into`, never deleted |
| DOC | the brief; the focus; the frame; **the orientation** (FRAME's summary of what this material is); the material laid out; its codes and hits; live themes; feedback on this material verbatim, dated, by target | `summary` ≤180 words · `threads: [{theme_id, moments: [{claim ≤30 words, anchor ≤12 words, sid}]}]` · `brief` ≤120 words · `people: [{name, aliases, role}]` | **every anchor bound**: unfound → moment dropped, wrong sid → repaired; 2–8 moments per thread else the thread is dropped and noted; moments ordered by position |
| PROJECT | the focus; every material's kind, summary and threads (claims, anchors, moment ids); live themes; project feedback verbatim | `summary` ≤250 words citing moment ids · `theme_gists: [{theme_id, gist ≤40 words, moment_ids}]` | cited moment ids exist and are live; **no new quotes at this level** — a project claim rests on moments |
| CHECK | the question verbatim; the uncited passages in scope, chunked | `found: [{anchor, sid}]` | anchors bound; the verdict is Python's: bound quotes → *found*, none → *not found in N passages*; the model's opinion can only lower confidence |

**The orientation is written once and re-synthesized, never replaced.** FRAME writes *what this
material is* before anything is coded, so a freshly uploaded piece already reads as something. DOC
sees it and writes *what the reading found*. Both are kept (`summary.stage` = `orientation` |
`reading`); the page shows the reading one when it exists, the orientation before that; the export
shows both, which is how a researcher sees what the analysis added to a plain description.

**Self-prompting is exactly one slot: the brief.** DOC rewrites it after each material (*what this
corpus is like; what to look for next*); READ and DOC read it. Round 2 tested five mechanisms; the
self-written brief was the only one that cleared the noise band. Researcher feedback enters prompts
as **quoted text assembled by Python**, never paraphrased by a model — the export shows the
researcher exactly the block the model saw.

**Mechanical first, model second.** FRAME never parses. Python's speaker scan runs first and its
result goes *into* the prompt; the model's job is to name and role what the scan found, and to
propose labels only when the scan found nothing. Every label the model proposes must be found in
the text before it is used. Same law as anchors, applied to structure.

## 3. Four laws

1. **Anchor.** No claim without a verbatim quote of ≤12 words that Python can find. The quote, not
   the citation, is authoritative: a wrong sentence id is repaired, a quote that is not there drops
   the claim. Applies to moments and to frame segments alike. (`anchor.py`, ported unchanged.)
2. **Absence.** A negative claim is a verb the researcher runs, never a sentence the model writes.
   CHECK searches; Python rules.
3. **Slot.** The scaffold is Python and frozen; the model fills named, bounded, validated slots. A
   slot with no real-output check is a slot you do not have — each phase ends with one.
4. **Derivation.** Every number on a page is printed as its derivation over rows the page links to:
   *"cites 87 of 302 passages"*, *"4 of 5 moments agreed"*. No counter is stored; all are views.

5. **Slot.** *(the discipline, stated separately because breaking it produced six bugs at once)*
   A prompt template is universal: the same file for every corpus, every material, every project.
   What varies is what fills its slots, and a slot may hold only three kinds of thing — **the
   material itself**, **validated structure** (codes with their sentence ids, themes with their
   code lists, claims with their quotes), or **the researcher's own words verbatim**. It may never
   hold prose the system wrote about the corpus. The single exception is the one self-prompting
   slot, and that slot carries *questions the corpus has raised and not answered* — never what
   it found. Conclusions flow up the layers; only questions flow forward into the next reading.
   A gist *defines* a theme; an account *concludes* about it; the two are different objects and
   the first is never allowed to become the second.

## 4. Nouns, verbs, pages

- **Nouns:** material · moment (claim + quote, highlighted in place) · thread (one theme's moments
  through one material, in order) · summary (per material; per project).
- **Verbs:** react (agree / doubt / note) on a moment, thread or summary · check ("check this
  against the material") · focus · add material · **re-frame** ("this is laid out wrong" + a hint).
- **Pages:** home · project · material. Plus `export.md`. Codes have no page; a thread shows
  *"based on 4 codes"* in a native `<details>`.

## 5. Stack

FastAPI · Jinja2 · sqlite (stdlib) · httpx · pydantic · python-multipart · uvicorn. Dev: pytest.
No JS. No spaCy. Tests replay recorded model output from `tests/recorded/`.

**Two providers, both OpenAI-compatible, selected by `APERTURE_PROVIDER`:**

| Provider | Base | Key | Default model | Use |
|---|---|---|---|---|
| `minimax` (default) | `https://api.minimaxi.com/v1` | `MINIMAX_API_KEY` | `MiniMax-M3` | development, testing, cost |
| `mistral` | `https://api.mistral.ai/v1` | `MISTRAL_API_KEY` | `glm-5-2` | EU deployment under the university contract |

Each is overridable (`APERTURE_BASE_URL`, `APERTURE_MODEL`). Calls are **streamed**, so the timeout
is an idle timeout — a long think does not trip a cap but a real hang still dies. `<think>…</think>`
is stripped before parsing. Every run row records provider, model and tokens; the export prints
them. A provider must never be inferred from a key being present.

```
aperture/
  app/
    main.py        # FastAPI app, routers, /health
    db.py          # sqlite per project under $APERTURE_DATA_DIR, schema + migrate
    store.py       # persistence helpers: moments, summaries, supersede, queries
    auth.py        # PIN gate (ported)
    anchor.py      # the anchor law (ported unchanged)
    turns.py       # mechanical speaker scan + turns (ported from store.py)
    ingest.py      # text → sentences with ids
    llm.py         # chat_json(system, user) → dict; providers; streaming; usage
    prompts/       # frame.md read.md themes.md doc.md project.md check.md
    engine/        # one module per prompt: frame read themes synth check
    rerun.py       # feedback → [Run]   (the table in §1)
    jobs.py        # background run chains; progress line; run rows
    context.py     # one function per page; APP_AUTHORED; the banned list
    pages.py       # GET routes        verbs.py  # POST routes
    templates/     # base home project material export.md
    static/aperture.css   # ≤ 80 lines
  seed/  tests/  Dockerfile  pyproject.toml  PLAN.md  DEPLOY.md
```

## 6. Data model

```sql
project (id, name, focus, brief, created_at)
material (id, project_id, name, text, kind, display, title, state, created_at)
sentence (material_id, idx, sid, turn_idx, speaker, text)          -- sid "S014"
speaker  (material_id, label, name, role)                          -- role: interviewer|participant|other
segment  (material_id, idx, sid, label)                            -- anchored section starts
code (id, project_id, name, definition, origin)                    -- origin: read|rerun
code_hit (code_id, material_id, sid)
theme (id, project_id, name, gist, status, merged_into)            -- status: live|merged
moment (id, material_id, theme_id, sid, position, claim, anchor, run_id, status)
summary (id, scope, ref_id, stage, text, run_id, status)           -- scope: material|project ; stage: orientation|reading
person (material_id, name, aliases, role)
feedback (id, target_kind, target_id, kind, text, created_at, consumed_by_run)
check_ (id, scope, ref_id, question, verdict, anchors_json, searched_n, run_id, created_at)
run (id, project_id, kind, material_id, provider, model, tokens_in, tokens_out,
     started, finished, error, line)
```

A **thread** is a query: live moments where `(material_id, theme_id)`, ordered by `position`.
Reruns supersede rows; nothing is deleted, so the export can show what changed. **Sentence ids are
stable** — a re-frame never re-ingests, so codes and moments survive it.

## 7. Pages

**Home `/`** — projects; new project. PIN gate when `APERTURE_PIN` is set.

**Project `/p/{pid}`** — the project summary (moment citations link into materials). The brief, one
line. Focus with history and a form. **Themes as rows**: name, gist, one column per material
holding that material's thread as a compact list of claims, each linking to
`/p/{pid}/m/{mid}?thread={theme}#S014`. Material list with kind, state line, add form. React and
check forms at the summary. While a run is active the page carries `<meta http-equiv="refresh"
content="5">` and the run's line; idle pages carry neither.

**Material `/p/{pid}/m/{mid}?thread={theme}`** — header: title, kind, people, *"moments cite 87 of
302 passages"*. The summary (reading, or orientation before it exists). Then the **stack**: one
card per theme with moments here — name · n moments · gist. The selected card (default: the first)
expands into two columns: left, its moments — claim, then the quote set as a quotation, linking to
`#S014`; right, the text, laid out per the frame (`turns` → numbered speaker turns; `segments` →
labelled sections; `plain` → paragraphs), this thread's quotes wrapped in `<mark>`. The sentence at
`:target` is tinted. Unmarked text is what the reading did not claim on. Under the card: react
form, check form, `<details>` with the codes. Re-frame link in the header. Two typographic
registers: the material in a monospace face, everything the app or model says in the reading face;
a quote and a claim never look alike.

**Export `/p/{pid}/export.md`** — project summary; per material the orientation *and* the reading
summary, people, every thread with claims and quotes; every check with verdict, quotes, searched
count; focus history; every reaction; the derivation line per material; per run provider, model,
tokens; the brief; the verbatim feedback blocks as the model saw them.

**Words.** Our vocabulary stays in the code. `context._BANNED` is checked against `APP_AUTHORED`
strings and against rendered template text with quotes and model prose stripped. On the page:
*material · what this is · what the reading found · Check this against the material · Reading
record*. Never: anchor, door, slot, ledger, exposure, residue, territory, register, roster, gate,
delta, frame. Say *interview* only where the frame says the material is one.

## 8. Build phases

The lead writes the contract tests before an agent starts. Each phase ends with a **real-output
check** against MiniMax-M3 on the public seeds, recorded into `tests/recorded/` so the suite
replays it offline. Agents build against tests and recordings, never against a live model.

| # | Builds | Who | Depends on |
|---|---|---|---|
| P0 | repo, pyproject, `main.py`, `db.py`, `store.py`, `auth.py`, `anchor.py`, `turns.py`, `llm.py` (two providers + replay double), `ingest.py`, Dockerfile, seeds, conftest, **all contract tests** | lead | — |
| P1 | `engine/frame.py` + `prompts/frame.md`; speaker verification; segments bound; orientation stored | agent | P0 |
| P2 | `engine/read.py`, `engine/themes.py` + prompts | agent | P0 |
| P3 | `engine/synth.py` (DOC + PROJECT), `engine/check.py` + prompts | agent | P0 |
| P4 | `rerun.py` + `jobs.py` — the §1 table, run chains, progress lines | agent | P0 |
| P5 | `context.py`, `templates/`, `static/`, `pages.py`, export | agent | P0 fixture |
| P6 | `verbs.py` — add material, react, check, focus, re-frame; wiring | lead | P1–P5 |
| P7 | real-output pass on Grande + Rodwin, recordings, walkthrough | lead | P6 |
| P8 | GitHub remote, new Coolify app, volume, env, tag `v0.1` | lead + user | P7 |

P1–P5 run in parallel; each owns files no other touches.

Lessons the tests exist to hold (each happened once): an explicit field list dropped a validated
quote on the way to the page, three times, under a green suite — hence field-coverage tests, not
key lists; a summary line said "nothing is carried" while a comment was carried — hence the
compiled prompt and the page read the same rows; a slot that felt optional in the prompt returned
empty — hence symmetrical, top-of-prompt rules and a real-output check per slot; a validator never
checked against real output is not a validator.

## 9. Deploy

New Coolify application from this repo; persistent storage at `/data`; env: `APERTURE_DATA_DIR`,
`APERTURE_PIN`, `APERTURE_PROVIDER`, `MINIMAX_API_KEY`, `MISTRAL_API_KEY`, `PORT`. Health at
`/health`. **Never rename the application after creation** — a rename orphaned the previous app's
volume. Secrets live only in Coolify's env and a gitignored `.env`.

## 10. Carried over, and knowledge only

Verbatim or near: `anchor.py` · `absence.py` → `engine/check.py` · `store.py`'s speaker/turn scan →
`turns.py` · `auth.py` · Dockerfile shape · seeds Grande and Rodwin · `_BANNED` · streaming client
and the idle-timeout finding · the two-provider config.

Knowledge, not code: `design/ROUND-LEDGER.md` and `BLUEPRINT.md §1` in the old repo; the defect
catalogue D0–D18; that a mediated researcher's criticism is less reliable than their assent (why
doubt routes to CHECK); that reader-facing coverage mechanisms did not move fidelity (why there is
no coverage strip — unmarked text is the coverage display). The simulation harness stays in the old
repo; measuring this instrument is a later round.

## 11. Standing constraints

Only the two public seed transcripts enter this repo; `pairing_nirosha/` and `transcripts_sample/`
never do. codex-cli / luna is not a provider here and never deploys. Simulation output never mixes
into validation against a human coder. The deployed model is M3 or GLM-5.2 via Mistral; P7's
recorded checks are the compliance gate for any later model change.
