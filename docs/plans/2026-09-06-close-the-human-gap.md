# Plan: take what the human analysis did better, without adding a model call

**Date:** 6 September 2026
**Baseline:** the Ellis Island v3 export (`Ellis Island v3-3.md`, GLM-5.2 on Mistral, iterative chain + one consolidate) and the close-reading evaluation of it against three coders, their consolidated book and the calibration session (`output/pdf/ellis_island_evaluation/evaluation.pdf`).
**Constraint:** no new step in any chain. Every change lands inside a call that already runs, or in Python. Output-token growth is bounded and stated per package.
**Not in scope:** the Astra work packages (AR-01…AR-11) already specified in `Astra-review.md`. This plan assumes R1/R2 land first and does not restate them.

## 0. Generality

Aperture reads any qualitative material — interviews, focus groups, field notes, documents, open-ended survey answers — and its prompts are universal templates (PLAN.md law 5). The Ellis Island corpus is the evidence for this plan because it is the only corpus with a human benchmark; it is not the subject of it. Three rules hold throughout:

1. **A rule names a kind of thing, never a domain's thing.** "A standing condition", "an evaluation made after the fact", "a case the definition did not foresee" — not "a legal status", "regret", "an adult migrant". Every rule below is written so that it says nothing on a corpus that does not have the thing it names.
2. **Nothing assumes a speaker.** Where a rule concerns judgment or evaluation, it is the material's — an author's, a note-taker's, a respondent's — as much as a narrator's.
3. **Examples in a prompt come from a domain other than any evaluation corpus.** The repo's existing examples (a nurses' focus group, a market observation, "R. Okafor") set that convention; nothing migration-shaped is added to a template.

Each gap is also anchored in qualitative method rather than in this corpus: boundary work is Braun and Clarke's phase 4 (reviewing themes); an overarching tier with a rationale is phase 5 (defining and naming, the thematic map); keeping description apart from the material's own evaluation is the semantic/latent distinction; coding an extract under every pattern it carries is their phase-2 guidance. The Ellis instances are fixtures for those general capabilities, and §5 adds a second-domain check so a rule that only works on oral history is caught before it ships.

## 1. What the evaluation established

Where the machine already carries or beats the human work — do not touch:

- Evidence discipline: every claim quoted, 371 caveated, four self-flagged overreaches.
- Counterexamples retained (relatives who could not help; comfortable sending households; disavowed regret).
- Three organising lenses the humans did not have: memory as mediated; property and relative class position; the social limits of the enclave.
- The Batta religion case: the machine's cross-ethnic reading was right, the adjudicated human reading was wrong.

Where the human work is genuinely stronger — the targets of this plan. The first column is the general capability; the second is the Ellis instance that showed it.

| # | General capability the humans had | Ellis instance (fixture) | Why the machine lacks it (root cause in the chain) |
|---|---|---|---|
| G1 | A named overarching tier: 2–4 higher-order themes, each with a rationale for what it gathers and what separates it from its neighbour | Pattern 9; overarching dimensions 3–4; "artifact-level absence is real" | PROJECT returns free prose `summary` + `interpretation`. Nothing asks it to gather themes into a higher-order set, name what each gathers, or defend the grouping. Single-material candidates (18 here) have nowhere to go but a list. |
| G2 | The material's own evaluation of what it describes — judgment made after the fact about what something cost, achieved or meant — organised as its own layer rather than scattered as incidental claims | Pattern 9; dimension 4; "how later lives change the meaning of earlier sacrifice"; T6 "loss of childhood" | The evidence exists as claims across six themes. No prompt distinguishes *what is described* from *how the material weighs it*, so the second is never organised. In a policy document this is the evaluation section read as if it were description; in field notes, the observer's assessment read as observation. |
| G3 | Explicit analytical boundaries: what separates two neighbouring themes; whether a material's instance fits the definition or sits at its edge | Overall finding; family versus community (calibration 908–1042); "similarity does not license merging" (1752–1790); Batta-at-24 | THEMES defines but never has to say what a theme is *not*. THREAD must fit claims inside a definition but has no field to say "this material carries it differently". Tension notes exist for frozen themes only. VERIFY excludes theme fit by design. |
| G4 | Several concrete, distinct patterns consolidated under one account without merging them | Pattern 8; dimension 3: six work/economy candidates | Same cause as G1: candidates with no tier above them. Merging would flatten real distinctions; aggregating is what the humans did. |
| G5 | A passage that carries two meanings coded under both | Pattern 7: discrimination and identity pressure lost beside language | READ pushes toward one code per passage and "say less". The calibration explicitly decided the opposite: allow multiple meanings within one extract. |
| G6 | Standing conditions — a status, a constraint, a resource, a state of a body, a place or an organisation — coded as codes rather than read past as events | T1/T8 close-reading cases (derivative citizenship, journey illness, housing); 59 uncovered segments, T1 lowest at 66% | READ rule 6 pitches every code at "what a passage is about"; a condition reads as an event and is not coded. ANGLES for T1 produced findings dressed as angles and no angle on the body or on legal status. |
| G7 | A cause, consequence or mechanism named in a definition is checked against the evidence for the link, not just its two ends | Friedman volunteerism ("absence *prompting* volunteerism"); enclave "employment breaks the enclave" | Nothing verifies a gist. ACCOUNT is asked what varies with what, not whether the causal word in the definition is carried. |

Two things the humans did that are **not** adopted, on purpose: importing named theory (Berry, Portes) — the evaluation shows it outrunning evidence, and PLAN.md forbids it at project level; and a second independent reader — that is a second chain, and this plan adds no call.

## 2. The levers, one per call

Each gap maps to an existing call and a bounded change to its output contract. The cost column is the only new spend.

| Gap | Call | Change | Extra output per call |
|---|---|---|---|
| G1, G4 | PROJECT | structured `overarching` list replaces most of free `interpretation` | ~400 words, once per chain |
| G2 | ACCOUNT, PROJECT | one rule each: keep what the material describes apart from the material's own evaluation of it; say where that evaluation is read | ~40 words per account |
| G3 | THREAD | `fit` field (≤25 words) → stored as a theme note for open themes too | ≤25 words per line |
| G3 | THEMES, THEMES-CROSS | `nearest` {id, differs} per open theme and candidate | ~20 words per theme |
| G3 | ACCOUNT | reads the notes; must place a noted material rather than fold it in | ~0 (input +1 line per note) |
| G5, G6 | READ, ANGLES | two rule changes, one negative example | ~0; possibly more codes within the existing cap |
| G7 | ACCOUNT | one rule: a cause/consequence/mechanism in the definition is checked for the link | ~30 words per account |
| — | Python | duplicate-theme heuristic at consolidate; rendering; export | 0 |

Per material the call count is unchanged in both chains. Across the Ellis run (2.4M input / 1.7M output) the additions total well under 2% of output.

## 3. Work packages

### WP-1 — PROJECT writes the overarching tier (G1, G4, G2)

**Change the contract** in `app/prompts/project.md` and `engine/synth.py::project`:

```json
{
  "summary": "…as now, ≤{{summary_words}} words, cited…",
  "overarching": [
    {"name": "≤8 words",
     "gathers": ["t9f2c1", "t0aa41", "tc77e2"],
     "organising_idea": "one sentence: what every theme in `gathers` is an instance of",
     "boundary": "one clause: what separates this from the nearest other overarching theme",
     "exceptions": "the materials or claims that pull against it, cited [mo…]; or 'none in the claims shown'",
     "argument": "≤{{overarching_words}} words, cited [mo…], drawing on at least two gathered themes"}
  ],
  "ungathered": [{"id": "t44ab0", "why": "≤15 words"}],
  "interpretation": "≤{{interpretation_words}} words, provisional, as now but shorter"
}
```

Rules added to the prompt (numbered on from 7):

8. Between two and four overarching themes. Every open and frozen theme appears in exactly one `gathers` or in `ungathered` with a reason. A candidate may be gathered: a pattern seen in one material can still be an instance of something several materials carry.
9. An overarching theme is not a theme renamed. Its `argument` cites claims from at least two of the themes it gathers, and its `organising_idea` says what those themes have in common that none of them says alone.
10. `boundary` names the nearest other overarching theme and what sorts a theme into this one rather than that. Two overarching themes that cannot be told apart in one clause are one.
11. Where claims carry the material's own evaluation of what it describes — a judgment made after the fact about what something cost, achieved, failed at or meant, whether by a person speaking, an author, or whoever wrote the notes — say under which overarching theme that evaluation is read and how it stands to what it evaluates. It is a different kind of claim from the description, and it is not left scattered across the set. Where the materials carry no such evaluation, this rule says nothing.
12. `interpretation` says what the overarching set may mean and what evidence would settle it. It introduces no fifth overarching theme.

**Inputs:** PROJECT already sees accounts (open/frozen) and candidate claims per material. Add a `candidates` block — id, name, gist, and the claim ids already in the material blocks — so `gathers` can name candidates. Under 2k tokens on Ellis.

**Python:** validate every `gathers`/`ungathered` id against live themes (drop unknown, note on the run); a live theme in neither list is appended to `ungathered` with "not placed by the summary"; `_strip_dangling` over every cited id as now; word caps per field; store as `summary(scope='project', stage='overarching')` holding the JSON, alongside `reading` and `interpretation`. `OVERARCHING_WORDS = 120` per argument.

**Pages and export:** project page shows the overarching set between the summary and the interpretation — name, organising idea, the themes it gathers as links, boundary, exceptions, argument with citations. Theme page shows "gathered under: …". Record and `export.md` print the tier. Section heading, per the frontend audit's vocabulary: **Overarching themes**.

**Acceptance (Ellis fixture):** the six work/economy candidates (class descent, displaced craft, women's wage work, children's household labour, lodging economy, workplace mobility) land under one overarching theme with a cited argument; evaluative claims (regret in *Emotional weight*, descendants in *Class descent*, later service in *Volunteerism*) are placed by rule 11; no dangling ids; every live theme placed or ungathered with a reason. Judged blind against the v3-3 record (see §5).

**Acceptance (second domain, mechanics only):** on a non-narrative fixture — documents or open-text survey answers — the output validates, every live theme is placed or ungathered, and no `organising_idea`, `boundary` or `argument` refers to a speaker, a life, or a chronology the materials do not contain. Rule 11 produces nothing where the materials contain no evaluation.

### WP-2 — THREAD says where a material does not fit the definition (G3)

**Change:** `thread.md` gains one field and one rule:

```json
{"moments": [...], "summary": "...", "fit": ""}
```

10. `fit` is empty, or at most 25 words naming where THIS material carries the theme in a way its definition does not foresee: a different kind of case, actor, setting, time or direction than the definition names. Not a finding about the material, and not a rewrite of the definition — a note to the researcher that this material sits at the edge of it. Write it when it is small; write nothing when there is nothing. It assumes no speaker: the case may be an organisation, a site, a document's subject.

**Python:** in `_thread_kept`, when `kept` is non-empty and `fit` is non-empty, `store.add_theme_note(tx, tid, mid, run_id, fit)` in the same transaction. `theme_note` already exists and already renders on the theme page (`context._tension_notes`); today only THEMES writes to it, for frozen themes. Distinguish origin with a `kind` column (`tension` | `fit`) so the page can label them ("From the reading of Batta: …").

**Acceptance fixture (Ellis):** T7. The definition of *Ellis Island as a child's threshold* names children; Batta arrived at 24 (source header, lines 8–21). A `fit` note of the form "the participant arrived as an adult; the definition names children" must appear, and WP-3's account must then place Batta as an adult case rather than fold her in. Second fixture: T2 Larsen under *Household authority in sending family* (the evaluation's "summary goes past the claims" flag). The general class of error is *a theme applied to a case its definition excludes* — the kind of actor, setting or time — and it occurs in any corpus where a definition written from the first materials meets a later one of a different kind: a definition written from clinics applied to a pharmacy; one written from managers applied to a union document.

### WP-3 — ACCOUNT places noted materials, checks the mechanism, keeps the event apart from its later weighing (G2, G3, G7)

**Inputs:** the `{{materials}}` block gains, under a material's heading, any `fit` note from WP-2: `note from the reading: <text>`.

**Rules added** to `account.md`:

9. Where a material's block carries a note from the reading, say in one sentence how that material stands to the definition — the exception it is, or the edge it sits at. Do not fold it in as if it were an ordinary instance.
10. Where the theme's definition names a cause, a consequence or a mechanism — one thing prompting, producing, enabling or breaking another — say whether the cited claims carry that link itself or only its two ends. If only the ends, say so in one sentence, and say which claims would be needed.
11. Where claims carry the material's own evaluation of what it describes — a judgment made after the fact about what something cost, achieved, failed at or meant, by whoever speaks or writes in it — keep it apart from the description: say what is described, then how the material weighs it, and cite each separately. An evaluation made in one material is not read into another, and a description is not read as an evaluation.

**Acceptance fixtures (Ellis):** T5 Friedman under *Absence of arrival support prompting later volunteerism* — the account must state that the claims carry the service and the lack of support but not her identifying one as the cause of the other (source lines 218–236: bereavement is the stated trigger). *Ethnic enclave as bounded social world* — the account must state the enclave→employment sequence with the materials where it does not hold in the same sentence (Larsen's rapid English; mixed neighbourhoods). The general class: any definition of the form *X producing / enabling / preventing Y* — "understaffing causing handover errors", "funding cuts closing services" — where the claims show X and show Y but no claim shows one leading to the other.

### WP-4 — THEMES says what each theme is nearest to and how it differs (G3)

**Change** to `themes.md` and `themes_cross.md`, for every open theme and candidate returned:

```json
{"id": "t9f2c1", "name": "…", "gist": "…", "code_names": [...],
 "nearest": {"id": "t0aa41", "differs": "≤20 words: what sorts a passage into this one and not that"}}
```

17. `nearest` names the live theme or candidate this one is most easily confused with, and `differs` says what sorts a passage into this one rather than that. If you cannot say what differs, the two are one: return `merge_into` instead. `nearest` may be `null` only when no other theme is close.

**Consolidate** (`themes_cross.md`, the `{{ceiling}}` slot when `consolidating=True`) adds the calibration session's own criterion: *Two themes are folded only when one definition would sort every passage of the other. A shared subject is not a shared pattern, and similar wording is not a reason to fold.*

**Python:** validate `nearest.id`; store `theme.nearest_id`, `theme.nearest_note` (schema +2 columns); render under the definition on the theme page and in the record. Zero-call duplicate heuristic at consolidate time and on the project page: two live themes whose `nearest` point at each other, or whose gathered code sets have Jaccard ≥ 0.5, are listed as **possible duplicates** beside the consolidate control, with the two `differs` texts side by side. Python proposes; the researcher decides.

**Acceptance:** on Ellis the two language themes and the two Ellis-Island themes each carry a `differs` a reader can apply to a new passage; the "three about language" state of §14 is visible as a proposal before anyone presses consolidate.

### WP-5 — READ and ANGLES: two meanings per passage, conditions as codes, no verdicts as angles (G5, G6)

**READ** (`read.md`):

- Rule 10 becomes: *Cite the sentences that carry the meaning, not the whole passage around them. A passage that carries two meanings carries two codes; do not choose between them, and do not code one passage twice under synonyms.*
- Rule 11 becomes: *Fewer codes that each earn their sentences beat a long list that restates the material — but a meaning the researcher could ask about is coded, not left because it appears once.*
- Rule 6 gains one sentence: *A standing condition — a status, a constraint, a resource, a rule, a state of a body, a place or an organisation — is a code where the passage treats it as a condition that holds, and not a code where the passage only reports it as one event among others.*

**ANGLES** (`angles.md`), rule 2 gains a negative pair in the prompt's own example domain, because the Ellis angles broke the rule as written ("Economic descent across migration" and "The absent father's return" are verdicts): *Name the ground, not the verdict: "How staffing is spoken of on nights" is an angle; "Understaffing on the night shift" is a finding.*

**Cost:** more codes per passage, within `max_codes`. In the iterative chain THREAD follows every open theme regardless, so no new calls. In the explore chain THREAD is gated on codes fired, so a passage carrying two codes can fire one more theme per material; bounded by the theme set, and measured in §5.

**Acceptance (Ellis):** re-run the passage alignment in `eval_package/crosswalk/segment_alignment.json` against the new record. Of the 59 human segments the v3-3 run did not touch, count how many now carry a claim on the same passage. This is retrieval, not correctness — pair it with the blind read. The T1 derivative-citizenship and journey-illness passages are the named checks.

**Acceptance (second domain):** on the non-narrative fixture, code count stays within the cap, the share of passages carrying two codes rises, and no code name presupposes a person ("the participant's…") where the material has none.

### WP-6 — Rendering, record, export (Python only)

- Overarching themes on the project page, record, export (WP-1).
- Theme notes labelled by origin and shown for open themes (WP-2).
- `nearest` / `differs` under each definition; possible-duplicate list at consolidate (WP-4).
- `docs/prompts/` regenerated from the live templates — it holds nine stale snapshots against twenty live prompts, and a reviewer of these changes needs to read what the model sees.

## 4. What this plan deliberately does not do

| Considered | Why not |
|---|---|
| A theme-fit verifier pass after THREAD | A new call per material. WP-2 gets the fit judgment from the call that already read the material under the theme. |
| An account verifier (entailment of ACCOUNT against its claims) | A new call per theme. ACCOUNT cites ids and Python strips dangling ones; WP-3's rules narrow what it may assert. Revisit only if the blind read shows accounts overreaching after WP-3. |
| A second, independent reading to imitate three coders | A second chain. The union of three human vocabularies was richer, but the cost is a whole reading; WP-5's two-meanings rule recovers part of it inside one. |
| RESIDUAL in the iterative chain | +1 call per material. The explore chain already has it; whether explore + residual beats iterative on this corpus is pass 6 of `docs/EVAL.md`, not this plan. |
| Theory import (Berry, Portes) at ACCOUNT/PROJECT | The evaluation shows the humans' theoretical labels outrunning evidence; PLAN.md law 5 keeps imported vocabulary out. A researcher who wants it writes it as feedback, verbatim, into the slot that exists. |
| Automatic promotion by "importance" | The calibration's rule (importance + frequency) puts importance with the analyst. Python already counts; WP-4 makes the boundary visible so the analyst can judge. |

## 5. Sequence, measurement, and what changes in the repo

**Three change sets, three blind passes**, each described in one sentence (per `docs/EVAL.md`):

| Set | Packages | Sentence |
|---|---|---|
| A | WP-2, WP-3 | "Lines say where a material sits at the edge of a definition, and accounts place it." |
| B | WP-1, WP-6 | "The project summary gathers themes into an overarching tier with a cited argument." |
| C | WP-4, WP-5 | "Themes say what they are nearest to; reading codes two meanings and conditions." |

**Corpus and model, benchmark:** the eight Ellis Island transcripts, focus "Ellis Island migration", GLM-5.2 on Mistral, iterative chain plus one consolidate — the exact conditions of v3-3, so the v3-3 record is the A side of set A. This is the judged comparison, because it is the only corpus with a human reading beside it.

**Second domain, every set:** one fixture that is neither an interview nor about migration — a handful of documents, or open-text survey answers, in the shape the frame examples already describe. Run the same chain; counts and a short read only, no blind panel. Its purpose is to catch a rule that silently presupposes a narrator, a life course or a journey. A rule that produces a speaker where there is none, or an overarching theme built on chronology the materials lack, fails the set regardless of the Ellis result. The repo does not yet hold such a fixture; adding one is the first task of set A.

**Judging:** the seven-fault rubric unchanged, plus three spot checks appended to `scripts/eval_rubric.md`, written for any material:

8. **Overarching coherence.** Does each overarching theme's argument cite claims from at least two of the themes it gathers, and name an exception or say there is none?
9. **Definition fit.** Is any theme applied to a material its definition excludes — a different kind of case, actor, setting or time — without a printed note saying so?
10. **Mechanism carried.** Where a definition names a cause, consequence or mechanism, does the account say whether the claims carry the link or only its ends?

**Thresholds, fixed now:** no dimension of the seven drops by more than one point on either reader; spot checks 8–10 answer as intended on the named Ellis fixtures (T7 Batta; T5 volunteerism; the six work/economy candidates); the second-domain fixture validates and shows no presupposed speaker or chronology; dangling citations zero; output tokens for the chain within +5% of v3-3. Retrieval on the 59 uncovered segments is reported, not thresholded.

**Repo consequences:** every changed prompt invalidates its recordings — `tests/recorded/` is keyed on the hash of system + user text — so each set re-records its labels (`APERTURE_RECORD`) against the seeds before the suite is green. Schema: `theme_note.kind`, `theme.nearest_id`, `theme.nearest_note`; `summary.stage='overarching'` needs no migration. PLAN.md §2 (the prompt table) and §12 (theme notes for open themes) get one-paragraph amendments; the frontend audit's copy inventory supplies the page labels.
