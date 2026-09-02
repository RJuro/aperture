# Aperture — build plan

*Written 2026-09-02, after three rounds of simulation in `MASSHINE_Qual_LLM`. That repo stays as
the record of what was learned; this one is the product, built from the ground up, lean.*

## 0. What it is

A reading companion for interview transcripts. It reads each transcript once, codes it, groups
codes into themes, and then presents each theme as a **thread through the interview**: a stack of
key moments, each one a short claim resting on a verbatim quote highlighted in the transcript next
to it. The researcher reacts to moments, threads and summaries; doubt is checked against the
material; feedback re-runs one layer down, never the whole reading. Every number on a page is a
derivation over rows the page links to. Every claim shows the words it rests on.

Not in v1: audio (Voxtral), a designed UI, htmx, speech-register claims, typed declines,
"set aside" lists, review dialogs, stories, model picker, multi-user, the simulation harness.

## 1. Layers, and which way things run

| Layer | Artifact | Made by | Scope |
|---|---|---|---|
| L0 | material — sentences with ids, grouped into speaker turns | ingest (Python) | document |
| L1 | codes — name, definition, the sentence ids they apply to | READ | document |
| L2 | themes — name, gist, the codes they gather | THEMES | project |
| L3 | doc synthesis — summary + threads (moments: claim + quote + sid), per theme | DOC | document |
| L4 | project synthesis — summary + theme gists, citing moments | PROJECT | project |

**Up** (a document arrives): READ → THEMES → DOC → PROJECT, one background job, one line of
progress a person can read (*"Reading Grande"*, *"Finding themes"*, *"Writing Grande's threads"*,
*"Updating the project summary"*).

**Down** (feedback): a rerun re-makes one layer and treats the layer below as input it may amend
but never rebuild. READ never reruns on feedback; a document is read once.

| Feedback on | Runs | Sees, in addition to its normal inputs | May change |
|---|---|---|---|
| a moment — *doubt* | **CHECK**, not a rerun | the doubt verbatim; passages of the document no moment cites | nothing; records a verdict with quotes |
| a moment — *agree / note* | nothing now | — | stance stored, shown, exported; enters the next DOC rerun as a directive |
| a thread in one interview | DOC for that document, that theme only | all feedback on this thread, verbatim | the thread's moments; may cite new sentences (new code hits); may *propose* a theme gist change (flagged, not applied) |
| an interview summary | DOC for that document | all feedback on this document | summary and every thread of this document; may add codes, marked `from_rerun` |
| a theme (project level) | THEMES, then DOC for each document where the theme has moments | the feedback verbatim | the theme set (rename, merge, split); affected threads |
| the project summary | DOC for every document with the feedback as directive, then PROJECT | per document as above | summaries, threads, project summary — **never codes' original hits, never READ** |
| focus (what you are looking for) | nothing now | — | the next READ and every later DOC carry it |
| *"check this against the material"* anywhere | CHECK | the question; uncited passages of the document(s) in scope | nothing; records verdict, quotes, searched count |

`rerun.plan(feedback) -> [Run]` is a table-driven Python function, and its test is this table.

## 2. What each prompt shows the model

Prompts are files in `app/prompts/*.md` with named slots. Python fills them; a test snapshots the
compiled prompt for the fixture, so a change to what the model sees is a visible diff.

| Prompt | Sees | Returns (JSON) | Python validates |
|---|---|---|---|
| READ | the brief (model's own, ≤120 words); the focus (researcher's words, verbatim); the live codebook (name, definition); the document as numbered turns with sentence ids | `codes: [{code: <existing name> \| {name, definition}, sids}]` | sids exist in this document; ≤ 40 codes, ≤ 12 new; names unique |
| THEMES | live themes (name, gist, codes); the codebook with per-document hit counts; the focus; theme feedback verbatim | `themes: [{id \| new, name, gist, code_names, merge_into?}]` | codes exist; ≤ 12 live themes; merges recorded as `merged_into`, never deleted |
| DOC | the brief; the focus; the document as turns with ids; this document's codes and hits; live themes; feedback on this document verbatim, dated, by target | `summary` (≤180 words) · `threads: [{theme_id, moments: [{claim ≤30 words, anchor ≤12 words, sid}]}]` · `brief` (≤120 words, rewritten) · `people: [{name, aliases, role}]` | **every anchor is bound** (`anchor.bind`): unfound → moment dropped, wrong sid → repaired; 2–8 moments per thread, else the thread is dropped and noted; moments ordered by position |
| PROJECT | the focus; every document's summary and threads (claims, anchors, moment ids); live themes; project feedback verbatim | `summary` (≤250 words, citing moment ids in brackets) · `theme_gists: [{theme_id, gist ≤40 words, moment_ids}]` | cited moment ids exist and are live; **no new quotes at this level** — a project claim rests on moments |
| CHECK | the question or doubt verbatim; the uncited passages in scope as turns with ids (chunked) | `found: [{anchor, sid}]` | anchors bound; verdict is Python's: bound quotes → *found*, none → *not found in N passages*; the model's opinion can only lower confidence |

**Self-prompting is exactly one slot: the brief.** DOC rewrites it after each document (*what this
corpus is like; what to look for next*), and READ and DOC read it. Nothing else the model writes
enters a prompt. Round 2 tested five mechanisms; the self-written brief was the only one that
cleared the noise band. Researcher feedback enters prompts as **quoted text assembled by Python**,
never paraphrased by a model — the export shows the researcher exactly the block the model saw.

## 3. Four laws

1. **Anchor.** No claim without a verbatim quote of ≤12 words that Python can find in the
   document. The quote, not the citation, is authoritative: a wrong sentence id is repaired, a
   quote that is not there drops the claim. (`anchor.py`, ported unchanged.)
2. **Absence.** A negative claim (*"the material does not say…"*) is a verb the researcher runs,
   never a sentence the model writes. CHECK searches; Python rules.
3. **Slot.** The scaffold is Python and frozen; the model fills named, bounded, validated slots.
   A slot with no real-output check is a slot you do not have — each phase ends with one.
4. **Derivation.** Every number on a page is printed as its derivation over rows the page links
   to: *"cites 87 of 302 passages"*, *"4 of 5 moments agreed"*. No counter is stored; all are
   views over `moment`, `feedback`, `check`.

## 4. Nouns, verbs, pages

- **Nouns:** moment (claim + quote, highlighted in place) · thread (one theme's moments through
  one interview, in order) · summary (per interview; per project).
- **Verbs:** react (agree / doubt / note) on a moment, thread or summary · check ("check this
  against the material") · focus · upload.
- **Pages:** home · project · interview. Plus `export.md`. Codes have no page; a thread shows
  *"based on 4 codes"* in a native `<details>`.

## 5. Stack and layout

FastAPI · Jinja2 · sqlite (stdlib) · httpx · pydantic · python-multipart · uvicorn. Dev: pytest.
No JS. No spaCy. One LLM provider: any OpenAI-compatible chat endpoint (Mistral in production),
configured by env. Tests replay recorded model outputs from `tests/recorded/`.

```
aperture/
  app/
    main.py        # FastAPI app, routers, /health
    db.py          # sqlite per project under $APERTURE_DATA_DIR, schema + migrate
    auth.py        # PIN gate (ported)
    anchor.py      # the anchor law (ported unchanged)
    turns.py       # speakers, turns (ported from store.py)
    ingest.py      # text → sentences with ids → turns
    llm.py         # chat_json(system, user, schema) → dict; usage on the run row
    prompts/       # read.md themes.md doc.md project.md check.md
    engine.py      # READ, THEMES, DOC, PROJECT, CHECK: fill → call → validate → persist
    rerun.py       # feedback → [Run]   (the table in §1)
    jobs.py        # background thread per run chain; progress line; run rows
    context.py     # one function per page; APP_AUTHORED fields; the banned list
    pages.py       # GET routes (home, project, interview, export)
    verbs.py       # POST routes (upload, feedback, check, focus)
    templates/     # base.html home.html project.html interview.html export.md
    static/aperture.css   # ≤ 80 lines
  seed/            # Grande, Rodwin (public)
  tests/
  Dockerfile  pyproject.toml  PLAN.md  DEPLOY.md
```

## 6. Data model

```sql
project (id, name, focus, brief, created_at)
document (id, project_id, name, text, state, created_at)         -- state: uploaded|reading|ready|failed
sentence (doc_id, idx, sid, turn_idx, speaker, text)             -- sid "S014"
code (id, project_id, name, definition, origin)                  -- origin: read|rerun
code_hit (code_id, doc_id, sid)
theme (id, project_id, name, gist, status, merged_into)          -- status: live|merged
moment (id, doc_id, theme_id, sid, position, claim, anchor, run_id, status)   -- status: live|superseded
summary (id, scope, ref_id, text, run_id, status)                -- scope: doc|project
person (doc_id, name, aliases, role)
feedback (id, target_kind, target_id, kind, text, created_at, consumed_by_run)
        -- target_kind: moment|thread|doc_summary|theme|project_summary ; kind: agree|doubt|note
check_ (id, scope, ref_id, question, verdict, anchors_json, searched_n, run_id, created_at)
run (id, project_id, kind, doc_id, model, prompt_sha, tokens_in, tokens_out, started, finished, error, line)
```

A **thread** is a query: live moments where `(doc_id, theme_id)`, ordered by `position`. Reruns
supersede rows; nothing is deleted, so the export can show what changed.

## 7. Pages, minimal

**Home `/`** — projects; new project. PIN gate when `APERTURE_PIN` is set.

**Project `/p/{pid}`** — the project summary (moment citations are links). *"The reading is
attending to: …"* (the brief, one line). Focus with its history and a form. Then **themes as
rows**: name, gist, and one column per interview holding that interview's thread as a compact
list of claims, each a link to `/p/{pid}/i/{doc}?thread={theme}#S014`. Material list with state
lines and the upload form. React and check forms at the summary. While a run is active the page
carries `<meta http-equiv="refresh" content="5">` and the run's line; idle pages carry neither.

**Interview `/p/{pid}/i/{doc}?thread={theme}`** — header: name, people mentioned, *"moments
cite 87 of 302 passages"*. The summary. Then the **stack**: one card per theme with moments here,
showing name · n moments · gist. The selected card (default: the first) is expanded into two
columns — left, its moments: the claim, then the quote set as a quotation, linking to `#S014`;
right, the transcript as numbered speaker turns, this thread's quotes wrapped in `<mark>`. The
sentence at `:target` is tinted. Unmarked text is what the reading did not claim on. Under the
card: react form, check form, `<details>` with the codes. Two typographic registers: the
transcript in a monospace face, everything the app or model says in the reading face; a quote
and a claim never look alike.

**Export `/p/{pid}/export.md`** — the project summary; per interview the summary, people, every
thread with claims and quotes; every check with verdict, quotes, searched count; the focus history;
every reaction; the derivation line per interview; per run the model and tokens; the brief; the
verbatim feedback blocks as the model saw them.

**Words.** Our vocabulary stays in the code. `context._BANNED` (ported and extended) is checked
against `APP_AUTHORED` strings and against rendered template text with quotes and model prose
stripped. On the page: *Read the passage · What did not fit · How they said it · You have read /
moments cite · Check this against the material · Reading record.* Never: anchor, door, slot,
ledger, exposure, residue, territory, register, roster, gate, delta.

## 8. Build phases

Tests are written by the lead before an agent starts; each phase ends with a real-output check
against the production model on the public seeds, and the outputs are recorded into
`tests/recorded/` so the suite replays them. Agents build against the tests and the recordings.

| # | Builds | Who | Tests first | Real-output check |
|---|---|---|---|---|
| P0 | repo, pyproject, `main.py`, `db.py` v1, `auth.py`, `anchor.py`, `turns.py`, `llm.py` with a replay double, Dockerfile, `/health`, seeds | lead | ported tests for anchor/turns/auth; `chat_json` replay | — |
| P1 | `ingest.py`, `prompts/read.md`, READ in `engine.py`, `jobs.py` with run rows and lines | agent A | splitter table; READ rejects unknown sids and caps new codes; run row written with tokens | READ on Grande: ≥ 15 codes, every sid valid; recorded |
| P2 | THEMES, DOC, PROJECT, CHECK, the brief slot, `rerun.py` | agent B | unfound anchor drops the moment; thread < 2 dropped and noted; PROJECT cites live moment ids only; `rerun.plan` matches §1's table row by row; feedback appears verbatim in the compiled prompt; compiled-prompt snapshots | DOC on Grande: ≥ 3 threads × ≥ 3 bound moments, summary ≤ 180 words; PROJECT over Grande + Rodwin cites moments only; CHECK finds a planted assertion and reports *not found in N* for an absent one; recorded |
| P3 | templates, CSS, `context.py`, `pages.py`, export | agent C, **parallel with P2** against a lead-written fixture db | field coverage: every live moment's claim and quote appear on its interview page, every theme on the project page; banned words absent from app-authored text; every quote is inside a `<mark>` whose sentence has the moment's sid; export contains every section of §7 | the Grande fixture renders with its first thread expanded and the quotes highlighted, by eye, once |
| P4 | `verbs.py`: upload → job; feedback → row → `rerun.plan` → jobs; check → result; focus; refresh only while running | agent D, after P2 + P3 | POST → redirect → stance visible; doubt on a moment creates a check and no run; feedback on the project summary schedules DOC for every document then PROJECT and no READ; idle page has no refresh tag | upload Rodwin on the deployed model, react, check, export — all four verbs, once |
| P5 | Coolify app from the repo, volume at `/data`, env, walkthrough, tag `v0.1` | lead | — | the deployed instance passes P4's walkthrough; screenshots kept |

Estimate: P0 ½ day · P1 ½ · P2 1 · P3 1 (in parallel) · P4 ½–1 · P5 ½ → **about 3 days**.

Lessons the tests exist to hold (each happened once): an explicit field list dropped a validated
quote on the way to the page, three times, under a green suite — hence field-coverage tests, not
key lists; a summary line said "nothing is carried" while a comment was carried — hence the
compiled prompt and the page read the same rows; a slot that felt optional in the prompt returned
empty — hence symmetrical, top-of-prompt rules and a real-output check per slot; a validator
never checked against real output is not a validator.

## 9. Deploy

New Coolify application from this repo; persistent storage mounted at `/data`; env:
`APERTURE_DATA_DIR=/data`, `APERTURE_PIN`, `APERTURE_LLM_BASE`, `APERTURE_LLM_KEY`,
`APERTURE_LLM_MODEL`, `PORT`. Health at `/health`. **Never rename the application after
creation** — a rename orphaned the previous app's volume. Secrets live only in Coolify's env and a
gitignored `.env`.

## 10. Carried over, and knowledge only

Verbatim or near: `anchor.py` (130 lines, with tests) · `absence.py` → `check.py` · `store.py`
`_speakers/_turns/_exchange` → `turns.py` · `auth.py` · Dockerfile shape · seeds Grande and Rodwin
· `_BANNED` and the page-words table · the lessons above.

Knowledge, not code: `design/ROUND-LEDGER.md` and `BLUEPRINT.md §1` in the old repo — the
rounds' evidence; the defect catalogue D0–D18; the finding that a mediated researcher's criticism
is less reliable than their assent (why doubt routes to CHECK); the finding that reader-facing
coverage mechanisms did not move fidelity (why there is no coverage strip — unmarked transcript is
the coverage display). The simulation harness stays in the old repo; measuring this instrument is a
later round with an adapter.

## 11. Standing constraints

Only the two public seed interviews enter this repo; `pairing_nirosha/` and `transcripts_sample/`
never do. codex-cli / luna is not a provider here and never deploys. Simulation output never mixes
into validation against a human coder. The deployed model is luna-class (Mistral / GLM-5.2
generation); P1 and P2's recorded checks are the compliance gate for any later model change.
