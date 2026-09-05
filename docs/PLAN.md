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
| L4 | material synthesis — one line per theme (moments: claim + quote + sid), then a summary over the lines | THREAD ×n, DOC | material |
| L4½ | theme account — what one theme amounts to across the corpus, citing moments | ACCOUNT ×themes | project |
| L5 | project synthesis — summary over the accounts and material summaries, citing moments | PROJECT | project |

**Up** (material arrives): ingest → FRAME → ANGLES → READ → THEMES → THREAD per theme → DOC → ACCOUNT per theme → PROJECT, one background job,
one line a person can read (*"Working out how this is laid out"*, *"Reading Grande"*, *"Finding
themes"*, *"Writing what stands out in Grande"*, *"Updating the project summary"*).

**Down** (feedback): a rerun re-makes one layer and treats the layer below as input it may amend
but never rebuild. READ never reruns on feedback; material is read once. FRAME is about the
material's *form*, so no analytic feedback touches it — it has its own verb (§4).

| Feedback on | Runs | Sees, in addition to its normal inputs | May change |
|---|---|---|---|
| a comment on a moment | nothing now | — | stored, shown, exported; enters the next DOC rerun as a directive, and that rerun consumes it |
| a thread in one material | DOC for that material, that theme only | all feedback on this thread, verbatim | the thread's moments; may cite new sentences; may *propose* a theme gist change (flagged, not applied) |
| a material's summary | DOC for that material | all feedback on this material | its summary and every thread; may add codes, marked `origin=rerun` |
| a theme (project level) | **ACCOUNT** for that theme | that theme's claims across the corpus; which materials carry it and which do not | that theme's account, and its gist if the account sharpens one |
| the project summary | **ACCOUNT** for every live theme, then PROJECT | PROJECT sees the feedback verbatim; each ACCOUNT as the theme row | every account and the project summary — **never a material's threads, never codes' original hits, never READ, never FRAME** |
| focus (what you are looking for) | nothing now | — | the next READ and every later DOC carry it |
| *"check this against the material"* anywhere | CHECK | the question; uncited passages in scope | nothing; records verdict, quotes, searched count |
| *"this is laid out wrong"* + a hint | FRAME for that material | the hint verbatim; the current frame | frame only; codes, themes and moments are untouched (sentence ids never change) |

`rerun.plan(feedback) -> [Run]` is a table-driven Python function, and its test is this table.

**And the researcher may simply ask for it again.** One verb, on one material, from a step they
pick: `rerun.from_step(mid, step)` plans everything that happens to that material from there on,
in the order the upward chain uses. It is not feedback — they said *do that again*, and re-reading
is the point of it — so it is the one thing that may run READ a second time. An optional note is
stored once as a comment on the material and rides on every run in the chain.

| Run again from | Runs | Where the note goes |
|---|---|---|
| Structure | FRAME → ANGLES → READ → THEMES → DOC → ACCOUNT ×themes → PROJECT | FRAME as its hint, then ANGLES, READ, THEMES, and DOC as an open comment |
| Angles | ANGLES → READ → THEMES → DOC → ACCOUNT ×themes → PROJECT | ANGLES, READ, THEMES, DOC |
| Coding | READ → THEMES → DOC → ACCOUNT ×themes → PROJECT | READ, THEMES, DOC |
| Themes | THEMES → DOC → ACCOUNT ×themes → PROJECT | THEMES, DOC |
| Synthesis | DOC → ACCOUNT ×themes → PROJECT | DOC |

A second READ **replaces** the first: that material's code hits go before it runs, and a code left
with nothing loses its place in every theme, exactly as when the material itself is removed.
Themes and moments already supersede, FRAME already replaces. A note is honoured by the last run
that was shown it, so one that rides a whole chain is still open when the synthesis at its end is
written.

Three rows read differently from how they were first written. A comment on a theme planned
*THEMES, then DOC for each material where the theme has moments*, and one on the corpus planned a
DOC per material; a scaling review measured the second at fifty syntheses, seventeen hours, for
one sentence. The theme account exists precisely so a corpus-level correction can be answered at
corpus level, and a comment that genuinely needs one material re-read belongs on that material,
where it is one run. **Known gap: the ACCOUNT prompt has no feedback slot, so a comment on a theme
is consumed by a run that was never shown it.** And doubt about a claim reaches this table as
*check this against the material*: the page offers one free-text comment per block and sends no
`doubt`, so the row that matched one could never fire.

## 2. What each prompt shows the model

Prompts are files in `app/prompts/*.md` with named slots. Python fills them; a test snapshots the
compiled prompt for the fixture, so a change to what the model sees is a visible diff.

| Prompt | Sees | Returns (JSON) | Python validates |
|---|---|---|---|
| **FRAME** | the first ~6000 and last ~1500 characters of the raw text; the mechanical speaker scan's result (labels and how often each recurs, or *none found*); the researcher's hint if this is a re-frame | `kind` · `display` · `title` ≤10 words · `speakers: [{label, name, role}]` · `segments: [{anchor, label}]` ≤12 · `orientation` ≤150 words | `kind` ∈ {interview, focus_group, fieldnotes, document, open_text, other}; `display` ∈ {turns, segments, plain}; **every speaker `label` must occur ≥2 times at a line start in the raw text**, unverified ones dropped; if none survive, `display` falls back to plain; every segment `anchor` bound by `anchor.bind`, unbound dropped |
| ANGLES | the frame; the orientation; **the open questions** from earlier material; the researcher's words about what to look for here, verbatim, when they asked for this again; a larger slice of the text than FRAME. **Never the focus** — angles are the counter-focus, an independent source of where to look | `field` · `subareas` · `angles: [{name, why, questions}]` | 5–8 angles, 2–4 questions each; stored as prose a researcher reads; fed to READ under *an angle decides where to look, never what is found* |
| READ | the focus verbatim; **the researcher's words about this reading, verbatim**, when they asked for it to be read again; the live codebook; **the frame**; **the angles** (places to look, never things to find); the material as ids + text, laid out per `display` | `codes: [{code: <existing name> \| {name, definition}, sids}]` | sids exist here; ≤ 60 codes; new codes ≤ one per dozen passages, 15–50; names unique. **No brief.** |
| THEMES | **the material just read, with its codes marked by passage**; live themes; the codebook with spread as *counts* (never material names); the focus; theme feedback verbatim | `themes: [{id \| new, name, gist, code_names, merge_into?}]` | codes exist; ≤ 12 live; merges before creates so a full set can turn over; **a gist defines — true if fifty more materials arrived — never locates or compares**; every rewrite kept in `theme_history` |
| THREAD | one theme's definition and its codes marked here; the focus; the frame; open comments on this line verbatim; the material laid out | `moments: [{claim ≤30 words, anchor ≤12 words, sid}]` | **every anchor bound**: unfound → dropped, wrong sid → repaired; 4–14 moments else the line is set aside *and the set-aside is kept on the run*; ordered by position |
| VERIFY | every live claim of the material just written: claim, quote, and the passage with its neighbours; the frame; the count | `verdicts: [{id, verdict ∈ supported\|partly\|not, why ≤12 words}]` | **Python owns the outcome**: `not` → the claim is set aside with the reason on the run; `partly` → kept and marked "the passage carries part of this" wherever it is read; a missing verdict counts as supported; runs once per material, between the lines and the summary, so the summary is written over verified claims |
| VERIFY-SUMMARY | the summary just written, split into numbered sentences; every live claim of that material with its quote and its passage id; the frame | `verdicts: [{n, verdict ∈ supported\|partly\|not, why ≤12 words}]` | **Python owns the outcome**: `not` → the sentence is removed from the summary and quoted on the run, *the claims do not carry it*; `partly` → kept, and the run says it goes past the claims; a missing verdict counts as supported; runs once per material, after the summary is written and before it is stored, so the summary a researcher reads first is the verified one, and with no live claim to check against it does not run |
| DOC | the orientation; the frame; the focus; **the lines just written** (claims + quotes); open comments verbatim; the material | `summary` ≤320 words · `questions` ≤120 words · `people` | summary introduces the lines by name; **`questions` are questions the material raised and did not answer — never findings**; read by ANGLES only |
| PROJECT | the focus; **each theme's account** and definition; each material's kind and summary; project feedback verbatim | `summary` ≤300 words citing moment ids · `interpretation` ≤150 words, provisional, no imported named theory, citing moment ids | cited ids exist and are live; **no new quotes and no gist rewriting** — a gist defines, an account concludes, the summary is written over the accounts. **Two movements, two rows** (`stage` = `reading` \| `interpretation`): what the corpus shows is cited, what it may mean is argued with, and the page must not run them together |
| CHECK | the question verbatim; the uncited passages in scope, chunked | `found: [{anchor, sid}]` | anchors bound; the verdict is Python's: bound quotes → *found*, none → *not found in N passages*; the model's opinion can only lower confidence |

**The orientation is written once and re-synthesized, never replaced.** FRAME writes *what this
material is* before anything is coded, so a freshly uploaded piece already reads as something. DOC
sees it and writes *what the reading found*. Both are kept (`summary.stage` = `orientation` |
`reading`); the page shows the reading one when it exists, the orientation before that; the export
shows both, which is how a researcher sees what the analysis added to a plain description.

**Self-prompting is exactly one slot, and it carries questions.** DOC writes the questions this material raised and did not answer; ANGLES reads them for the next piece; nothing else does. Round 2 found the self-written brief was the one mechanism that cleared the noise band — and the hand review of compiled prompts found the same brief, fed to READ and DOC as *what this corpus is like*, had become a finding carried forward as an instruction. Law 5 (§3) is the rule that keeps it a question.

**Mechanical first, model second.** FRAME never parses. Python's speaker scan runs first and its
result goes *into* the prompt; the model's job is to name and role what the scan found, and to
propose labels only when the scan found nothing. Every label the model proposes must be found in
the text before it is used. Same law as anchors, applied to structure.

## 3. Five laws

1. **Anchor.** No claim without a verbatim quote of ≤12 words that Python can find. The quote, not
   the citation, is authoritative: a wrong sentence id is repaired, a quote that is not there drops
   the claim. Applies to moments and to frame segments alike. (`anchor.py`, ported unchanged.)
2. **Absence.** A negative claim is a verb the researcher runs, never a sentence the model writes.
   CHECK searches; Python rules.

   *Three states, not two.* Where a theme has no claim in a material, one of three things
   happened: a line holds and this is not that case; the theme was **looked for** and what came
   back was set aside as too thin; or it was **not looked for**, because none of the codes the
   theme gathers marked that material at all. The third is not absence. It is a fact about where
   the reading went, and reading it as absence is how a corpus comes to say that eleven themes run
   through every one of four interviews. So DOC follows a theme through a material only where that
   material marked something the theme gathers, writes down which of the three it was (`follow`,
   keyed by theme id so a rename cannot break it), and every level that states an absence — the
   theme page, the record, the account prompt — states which kind it is. A researcher who asks for
   a line anyway gets it: `only_theme` is a person asking, and the answer to a person is not
   silence.
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
- **Verbs:** react (one free-text comment) on a moment, thread or summary · check ("check this
  against the material") · focus · add material · **re-frame** ("this is laid out wrong" + a hint)
  **run again** on one material, from a step the researcher picks, with an optional note.
- **Pages:** home · project · material. Plus `export.md`. Codes have no page; a thread shows
  *"based on 4 codes"* in a native `<details>`.

## 5. Stack

FastAPI · Jinja2 · sqlite (stdlib) · httpx · pydantic · python-multipart · uvicorn. Dev: pytest.
One poller for the progress line, nothing else. No spaCy. Tests replay recorded model output from
`tests/recorded/`.

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
material (id, project_id, name, text, kind, display, title, state, created_at, case_id)
case     (id, project_id, name, note, created_at)                  -- a file is not a case
sentence (material_id, idx, sid, turn_idx, speaker, text)          -- sid "S014"
speaker  (material_id, label, name, role)                          -- role: interviewer|participant|other
segment  (material_id, idx, sid, label)                            -- anchored section starts
code (id, project_id, name, definition, origin)                    -- origin: read|rerun
code_hit (code_id, material_id, sid)
theme (id, project_id, name, gist, status, merged_into)            -- status: live|merged
moment (id, material_id, theme_id, sid, position, claim, anchor, run_id, status)
summary (id, scope, ref_id, stage, text, run_id, status)           -- scope: material|project ; stage: orientation|reading|interpretation
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

**Home `/`** — the signed-in user's projects and the ones shared with them; new project. Sign-in with an account an admin made; `/admin` creates users and lists every project by name and owner, and nothing of what is in them: administering the instance is not a way into anyone's material, so an administrator opens only what they own or were invited to, and can hand over only a project whose owner account is gone. A project is shared by its owner from `/p/{pid}/share`, as a standing link (`/join/{token}`, collaborate or read only) that anyone signed in can take up until it is revoked.

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
`APERTURE_ADMIN` (`name:password`, first boot only), `APERTURE_PROVIDER`, `MINIMAX_API_KEY`, `MISTRAL_API_KEY`, `PORT`. Health at
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

## 12. Theme lifecycle: candidate, open, frozen

*Added 2026-09-04, after a four-interview project came back with twelve themes, eleven of them
"in 4 of 4", and a ceiling change left the set unable to move.*

The method this follows is template analysis with a constant-comparison loop, read through
reflexive TA's rule that a theme need not appear in every item and that prevalence is not
importance. Three consequences, each violated by the chain as it stood: a pattern seen in one case
is a candidate, not a category; saturation is judged per theme, not for the set; and the analyst —
not the instrument — declares a theme final, after which new material is *applied* to it and
deviations are logged, not written in.

**Three holds on a theme.** `theme.hold` is `candidate`, `open` or `frozen`; `status` stays
`live | merged` as before.

- **Candidate** — a pattern found in one material so far. It lives on that material's page and
  in the "in one material so far" group, never counts against the ceiling, and gets no account.
  THREAD follows a candidate through a new material only where its codes fired there (always,
  whatever `APERTURE_FOLLOW` says: a candidate needs confirmation from coding, not a reader sent to
  find it). It becomes **open** when the researcher promotes it, and
  where a second *case* holds a line under it Python only **proposes** that — a count of
  cases is a question, not a confirmation. The one exception is a consolidation (§14), where
  the count has been asked of a reading that went and looked everywhere: half the cases,
  rounded up and never fewer than two, opens it. A theme THEMES coins is born a candidate.
- **Open** — a project theme still developing. THEMES may reword, rescope, gather, merge. This is
  the behaviour the chain has always had, now confined to this group.
- **Frozen** — the researcher has declared it final. Name and gist are fixed in Python, not by
  asking nicely: a changed name or gist returned for a frozen id is ignored, and a frozen theme
  cannot be merged away (an open theme may be merged *into* it). New material is applied to it —
  codes gathered, lines written, absence recorded — and what pulls against the definition comes
  back as a **tension note** (`theme_note`: theme, material, run, ≤ 25 words) shown to the
  researcher on the theme page, never written into the gist. Unfreeze is one click; the notes
  are the case for it.

**A saturation signal, bookkeeping only.** `theme.stable_passes` counts the consecutive THEMES
passes over new material in which the theme's name, gist and gathered codes did not change (a
fingerprint compared per pass; reset to 0 on any change). At three or more the page says
*stable for N materials* beside a Freeze control. The researcher freezes; the instrument only
counts.

**The ceiling counts open + frozen.** Candidates are unbounded but THEMES may coin at most
`MAX_NEW` (4) per pass. When open + frozen exceed the ceiling — a project that reached twelve
under the old `4 + 2n` — THEMES is told so in its own slot and asked to merge down to it, folding
the theme that gathers fewest codes into its nearest; nothing is dropped, merges carry their lines.

**THEMES sees the set partitioned** — frozen (assign codes; report tensions; do not touch), open
(revise), candidates from other materials (this material may confirm one by gathering its codes
into it; a candidate left out of the answer simply stays a candidate) — in one call per material
as before. Accounts are written for open and frozen only; a frozen theme's account is still
rewritten when its claims change, since the fingerprint includes them.

**Pages.** Overview: frozen first, then open by reach, candidates folded per material with a
Promote control. Theme page: hold, stable-for count, Freeze/Unfreeze, tension notes with the
material each came from. Material page: this material's candidates marked as such. Record:
the hold printed with each theme; tension notes under the theme. Controls are the owner's and
an invited editor's.

## 13. Evidence first: the explore workflow after reading (R4)

*Added 2026-09-05 after the audit (Astra-review §5, AR-10/11) and pass 5 of docs/EVAL.md, which
showed that exploratory reading does not converge by itself: two materials coded on their own
terms produced eight candidates and nothing across them.*

Applies to projects whose `method` is `explore`; `iterative` projects keep the chain of §1–2.

**The unit of expensive work becomes a reading of one material, and a question asked of the
corpus** — not every theme × every material.

Per material: FRAME → (DIARIZE) → ANGLES → READ → RECONCILE → **MEMO**. The memo (`memo.md`) is
the material's account on its own terms, written over the passages the reading coded — never over
theme lines, so it does not go stale when themes move. Every sentence cites passage ids; Python
drops a sentence that cites nothing, and VERIFY-SUMMARY checks each sentence against the passages
it cites. The memo also carries the material's questions and people (what DOC's summary carried).
In an explore project the material page shows the memo as "what the reading found"; DOC writes
no summary for it (its lines still get written, below).

Per batch, once: **CROSS-CASE THEMES** (`themes_cross.md`) over an evidence packet instead of one
material's text — for each code in the reconciled codebook, its definition and up to two verbatim
passages from *different* materials, labelled by material; the batch's memos; the theme set
partitioned frozen/open/candidates as in §12. Same answer shape as THEMES v4, same Python
enforcement; no counts are shown (law 5 withholds spread on purpose — the passages are the
evidence). One call per batch, not one per material, so the serial tail of §1 disappears here.

Per material, after the themes: **targeted lines**. THREAD runs only for themes whose reconciled
codes fired in the material — the gate of §3 law 2 is on for explore projects, because after
RECONCILE "marked" means something across materials. Then **RESIDUAL** (`residual.md`), one call:
the passages no code touched, the theme set and the memo; the reader says what the coding missed
— an addition under a theme (a quote, a passage id, a claim; anchored and verified like any
moment) — or that the unmarked passages hold nothing further. A theme the gate passed over whose
residual pass found nothing gets the follow outcome **`residual`**: looked for in the unmarked
passages and not found — a verified absence, cheaper than a THREAD call and stronger than
"not looked for". The three silences of §3 become four, each printed as what it is.

Then ACCOUNT and PROJECT as now. Per material this is FRAME + ANGLES + READ + RECONCILE + MEMO +
VERIFY-SUMMARY + THREAD × marked + VERIFY + RESIDUAL, with THEMES once per batch, against the
iterative chain's THREAD × every theme + THEMES per material + DOC + VERIFY-SUMMARY.

**Evaluation before adoption** (Astra §8; docs/EVAL.md): four conditions on the same corpus and
model — iterative (corrected) · iterative with the code-hit gate · explore-R4 without RESIDUAL ·
explore-R4 with RESIDUAL — records judged blind on the seven faults plus coverage (what stayed
unexamined), with `call` rows giving calls, cached and reasoning tokens and seconds per material.
Thresholds fixed before unblinding. `explore` stays opt-in until that pass is written up.

## 14. Consolidate: comparing the themes against the whole corpus

*Added 2026-09-05, after an eight-material record came back with 28 themes and 748 claims: three
open, twenty-five candidates, fourteen of them resting on one material, three of them about
language. The corpus summary was written over the three.*

The chain revises the theme set one material — or one batch — at a time, and it never goes back.
A theme named at the fifth material is *not assessed yet* for the four before it, and wherever the
code gate passed it over it is *not looked for here*; a near-duplicate is folded only when THEMES
volunteers a `merge_into` in the pass that happens to see both; and since promotion became the
researcher's alone (§12), a candidate seen in seven of eight materials stays a candidate that no
account speaks for and PROJECT never reads. Every one of those is the same missing verb: nothing
in the instrument ever asks how the set stands **as a set, against the whole corpus**.

**Consolidate is that verb**, on the project page, with what it would cost printed before it is
pressed — *N themes to compare · M cells to read* — and an optional note that goes verbatim into
the THEMES call and nowhere else. It plans four movements (`rerun.consolidate_plan`):

1. **`consolidate`** — `themes.run_cross` over every live material at once, its ceiling slot
   carrying one extra sentence: this is a consolidation, fold two themes that define one pattern
   with `merge_into`, and a candidate seen in several materials is still a candidate here. Merges
   carry their lines, as they always have. Both methods consolidate through this call: what it
   reads is the codebook's own passages, so an iterative project needs no memo for it.
2. **The back-fill** — one `doc(mid, only_theme=tid)` per cell where a theme **two cases already
   carry** was never assessed, or was skipped by the gate. `only_theme` is a person asking, so the
   gate is off (§3, law 2) and the cell ends as a line, a sparse line, or thin: *looked for and
   found too thin* is a finding; *not assessed yet* was never one. These run side by side like any
   DOC step, and no memo or material summary is rewritten by them — an iterative project's summary
   is written over its lines, so it is rerun once per touched material afterwards; an exploratory
   project's memo is written over passages and does not move.
3. **The count rule** (`store.settle_holds`, `OPEN_AT = 0.5`) — now that every cell has been read,
   a candidate carried by half the cases (rounded up, never fewer than two) becomes **open**;
   below that but carried by two it stays a candidate with a proposal against it; frozen and open
   themes are untouched. This is the only place a count promotes, and it is allowed to because the
   looking is finished.
4. **The accounts and the corpus summary**, over the set as it now stands.

And PROJECT is widened to match: besides the accounts, it reads the claims of every **proposed**
candidate, not only those of materials no account carries. A candidate's claims enter as claims,
cited by id, never as an account's conclusions.

What this does not do: it does not re-read, re-code or re-frame anything (§1's rule holds — only
the researcher's own *run again* may re-read), it never promotes a theme one case carries, and it
never unfreezes. It is a paid verb — one THEMES call plus one line call per cell — which is why
the page prints the count first.
