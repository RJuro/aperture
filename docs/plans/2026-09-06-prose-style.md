# Plan: plain analytic prose from the prompts, whatever model runs them

**Date:** 6 September 2026
**Prompted by:** `docs/audits/2026-09-06-frontend-language-and-help-review.md` §3 and §7, and a read of the Ellis Island v3 record.
**Constraint:** no new model call. No rejection-and-retry on style — a retry is a round. The fix is what the model is shown, plus a counter that makes drift visible.
**Companion:** the audit's copy inventory (§5) fixes the *interface* strings. This plan fixes the *generated* prose and the prompts that produce it. They are the same voice and should ship together, but the interface copy needs no model run to check.

## 0. Generality

The style rules are about sentence construction — who is the subject, what is the verb, where is the scope — and apply to prose about a hospital ward, a planning document or a survey answer as much as to prose about a migrant's childhood. Three consequences for how this plan is written:

1. **The style block contains no example from any evaluation corpus.** Its examples use the repo's established example domains (a nurses' focus group, a market observation, a document), so a model cannot learn the Ellis Island vocabulary from the style block itself.
2. **The rules assume no speaker.** "The subject of a sentence is a person, a group, a material, or the claims" covers a document with no one speaking; "which speaker, where the material names one" is conditional.
3. **The smell counter's word lists are seeded from one record and treated as incomplete.** They grow from each evaluation's record, they never reject output, and a count is read beside a judgment — never in place of one.

The Ellis record is the evidence in §1 because it is the record that was read closely; it is the benchmark in §6 because a blind panel already exists for it. A second-domain run in §6 shows the block does not trade one register for a narrative-shaped one.

## 1. Where the voice comes from

The recognisable habits are not model-specific. GLM-5.2 wrote the Ellis record, and it reproduces them because the prompts model them. Three sources, each with evidence.

**(a) The instructions ask for the voice in so many words.** The phrase in the prompt reappears in the output as a template.

| Prompt text | What the record wrote |
|---|---|
| `doc.md` rule 1: "the story it tells about itself and the story it tells without meaning to" | Thome after-reading: "The story she tells without meaning to is about how thin a child's memory of migration is" |
| `doc.md` rule 1: "say in a sentence what it follows and where it goes" | every material: "'Family separation…' follows the father's two-year departure … and goes toward the disorienting arrival" |
| `account.md`: "Say what is thin — claimed once and nowhere else" | every account: "What is thin: confusion of arrival blocking memory [S381] is claimed once." |
| `project.md`: "what holds them together, what one of them does to another" | interpretation: "What one theme does to another matters." |
| `project.md`: "'taken together, this suggests', 'one reading of this is'" | interpretation: "One reading: this corpus tells a single story in two registers" |
| `thread.md` rule 9: "the shape of it, what holds and what pulls against it" | line summaries built on "holds" / "pulls against" |

**(b) The prompts' own register teaches it.** Rules and worked examples are written in the cadence the audit describes — rhetorical reversal, dash-fragment, abstract agent, aphorism:

- "a hedge hardened into a fact" (`verify.md`, `doc.md`, `memo.md`, `tighten.md`, `line_summary.md`)
- "Reading costs a call; a missed theme costs a finding." (`screen.md`)
- "an interpretation with nothing under it is a guess" (`project.md`)
- "Leaving is given as a matter of work, and the trade that paid was a small one — a stall, a yard, a cousin's shop" (`account.md` worked example)
- "The stall, not the land, is what fed them; the farm is a place they left." (`thread.md`, `residual.md` example claim — the *not X, Y* shape as the model's example of a good claim)

A model imitates the example more faithfully than the rule. The record's corpus summary is the examples' register at scale:

> The crossing survives as fragments — rough water, mattresses — while stretches vanish.
> Violence is a habitual backdrop, not an event: pogroms became everyday, fear dulled by repetition.
> Reunion demands improvisation — or is refused.
> Ellis Island enters as a threshold where wonder and vulnerability coexist.
> Childhood memory of migration is defined by what is missing.

Each of these has an abstraction as its agent, a verb the data cannot perform, and a scope it does not state. None is false; each hides who said what, in how many materials.

**(c) There is no positive model of plain analytic prose anywhere in the prompts.** Every prose rule is a prohibition (no motive, no evaluation, no "all"). Nothing shows what a good sentence looks like when it is boring.

The audit's own `_BANNED` finding applies here too: a word list produces substitutes, not clarity. The rules below are about sentence construction, not vocabulary.

## 2. The style block

One fragment, `app/prompts/_style.md`, included verbatim into every prompt that produces prose a researcher reads.

**As built it is 331 words, not the 180 this plan first budgeted** (`_style_short.md` is 92). The seven rules each do distinct work, and the two worked pairs are the part a model imitates most faithfully, so trimming to the budget meant dropping a rule. The plan's own risk row already fixes what to do if the block crowds the evidence rules — cut 5, then 7, never 1–4 — and the blind read is what decides that, so the rules stay whole until it does. At roughly 430 tokens against a 30k-token prompt the cost is not the issue; attention is, and that is what the eval measures.

```
HOW TO WRITE. Every sentence outside a quotation follows these; each is checked.

1. The subject of a sentence is a person, a group, a material, or the claims. Not an
   abstraction acting on its own. "Four of the six nurses describe handover as a checklist
   read aloud", not "Handover survives as ritual". "The claims do not say why", not
   "Trust is defined by what is withheld".
2. Use an ordinary verb for what was said, written or done: says, describes, reports,
   records, lists, decided, was refused. Data does not narrate, survive, vanish, haunt,
   enter, demand or coexist.
3. State the scope inside the sentence: which material, how many of them, which speaker or
   author where the material names one. "In the two ward notes", "in five of the eight
   materials", "in the 2019 policy" — not "the corpus", "the material", "these accounts".
4. No contrast for effect. Do not write "not X but Y", "X, not Y", "less X than Y",
   "not merely", "at once", "as much as". Say Y. Say X only where the material says both,
   and then say who says which. A distinction the reader needs — what was searched and what
   was not; what was said and what it may mean — is written out in full.
5. No fragment after a dash or a colon in place of a clause. No sentence that only announces
   or evaluates ("this matters", "one reading:", "at the heart of"). No list of three for
   rhythm.
6. Qualify with a fact, not a tone: name the claim that stands alone, the material that
   differs, the word the passage does not contain. Keep every hedge the material makes —
   a speaker's "I think", a document's "may". Add none of your own.
7. Prefer a plain relation to a figure of speech: "is supported by" not "rests on",
   "is about" not "carries", "differs from" not "pulls against".
```

Three pairs follow the rules in the fragment, so the model sees the target as well as the ban. They stay in the repo's example domains — a focus group, field notes, a document — and none comes from a corpus the instrument is evaluated on:

```
Not this: "Handover is a ritual, not a safeguard: the checklist is read, the substance
          vanishes."
This:     "Four of the six nurses describe handover as a checklist read aloud. Two say the
          checklist leaves out what they most need to know about a patient."

Not this: "Trust demands time — or is refused."
This:     "In three of the five sets of notes the new supervisor is described as trusted
          only after several months; in one, the team is described as never accepting her."

Not this: "The policy speaks of access while enacting closure."
This:     "The 2019 policy lists wider access as its first aim [..]. Its annex closes two of
          the four sites [..]. The document does not say how the two relate."
```

Rule 7 conflicts with the prompts' own vocabulary ("every claim rests on a quote", "a material carries a theme") — the same conflict the frontend audit found in the interface. Phase it: the block ships with rule 7 as *prefer*; the vocabulary alignment across prompts and pages (§4) follows.

## 3. Where the block goes, and how

**Mechanism.** `llm.prompt()` treats `{{style}}` as a reserved slot: if the template contains it, the loader fills it from `_style.md` itself; callers never pass it. This keeps the loader's law — an unfilled or unknown slot is an error — and makes inclusion visible in the template file, not in Python. A second reserved slot, `{{style_short}}`, carries rules 1, 3, 4 and 7 only, for prompts whose prose is a name, a gist or a 15-word note.

**Placement.** At the end of the system message, after the task rules and before `---`. The last thing before the material.

| Prompt | Slot | Prose it produces |
|---|---|---|
| thread | `style` | claims, line summary, (WP-2) fit note |
| line_summary, tighten | `style` | rewritten claims, summaries |
| doc, memo | `style` | material summary, questions |
| account | `style` | theme account |
| project | `style` | summary, overarching arguments, interpretation |
| themes, themes_cross | `style_short` | names, gists, tensions, (WP-4) differs |
| angles | `style_short` | angle names, why, questions — read by the researcher |
| residual | `style_short` | added claims, note |
| screen, reconcile | `style_short` | 15–20-word `why` fields |
| frame, diarize, read, check, verify, verify_summary | none | no prose, or prose no researcher reads |

**Cost.** ~250 input tokens per included call; zero output; zero calls. On the Ellis run that is under 0.5% of input.

## 4. Rewrite the prompts that teach the voice

Rules keep their meaning; their wording and their examples change. The worst first.

| File | Now | Becomes |
|---|---|---|
| `doc.md` r.1 | "the story it tells about itself and the story it tells without meaning to. Name each line below and say in a sentence what it follows and where it goes." | "what the material sets out to say — through whoever speaks or writes in it — and what it shows without remarking on it. Name each line and say in a sentence what it covers, from where to where in the material." |
| `memo.md` r.1 | same phrase | same replacement |
| `account.md` worked example | "Leaving is given as a matter of work, and the trade that paid was a small one — a stall, a yard, a cousin's shop [..]. The claims divide on whether that trade was chosen or fallen into…" | Re-worked on a theme outside any evaluation corpus, e.g. *Handover as where errors are caught*: "In four of the six materials handover is described as the point at which a mistake from the previous shift is noticed [..]. Two of those describe the catch as luck — one nurse happened to read the chart [..]; two describe it as the checklist working as intended [..]. The two field-note materials describe handover but contain no claim about errors [..]. The chart passage is also read under *Paperwork as protection* as a record kept for the ward's sake; here it is read as the moment of noticing, and the two readings concern different sentences of the same turn [..]. One material contains no claim under this theme; its claims concern rostering and do not mention handover." |
| `account.md` schema text | "Say what is thin — claimed once and nowhere else." | "Say which claims stand alone: made in one material and in no other." (and drop the label "What is thin:" from the record template) |
| `project.md` interpretation slot | "what holds them together, what one of them does to another … 'taken together, this suggests', 'one reading of this is', 'if this holds'" | "how the overarching themes relate — which depends on which, which contradicts which — and what evidence would settle it. Mark it provisional in plain words: 'This may mean', 'It is possible that'." |
| `thread.md`, `residual.md` example claim | "The stall, not the land, is what fed them; the farm is a place they left." | "The family lived from the market stall; the farm is mentioned twice, both times as somewhere they had already left." |
| `thread.md` r.9 | "the shape of it, what holds and what pulls against it" | "what the claims have in common, and which claim differs from the rest" |
| `screen.md` r.4 | "Reading costs a call; a missed theme costs a finding." | "When in doubt, answer `look`: an unnecessary reading costs one call; a theme passed over is not read for at all." |
| `verify.md`, `doc.md`, `memo.md`, `tighten.md`, `line_summary.md` | "a hedge hardened into a fact" | "a hedge written as a fact ('I think she adapted' written as 'she adapted')" |
| `project.md` r.1 caps text | "an interpretation with nothing under it is a guess" | "an interpretation cites claims like the summary does" |

Then the vocabulary alignment the frontend audit lists for the interface, applied to prompt text where the model reads it: *rests on* → *is supported by*; *carries* (a theme) → *contains claims under*; *pulls against* → *differs from* / *contradicts*; *written over* → *based on*; *fold* → *merge*. The stored field names do not change.

One standing rule for the prompts after this pass: **worked examples come from a domain other than any corpus the instrument is evaluated on.** The repo's current examples ("Work and staying", "Sending money home", "Leaving home", "Being asked where you are from") are migration-shaped while the seeds and the benchmark are Ellis Island oral histories — a model shown those examples and that corpus cannot be told apart from one that learned the domain from the prompt. Move them to the focus-group, field-note and document examples that `frame.md` already uses, one pass, while the prose rewrite is open.

`docs/prompts/` is regenerated from the live templates as part of the same change so the review reads the compiled text.

## 5. A counter, not a gate (Python, zero calls)

`app/prose.py`: a small set of regexes over generated prose, returning counts by kind. Logged, printed, never used to reject.

| Kind | Pattern (illustrative) | Catches |
|---|---|---|
| contrast | `\bnot\s+(merely|simply|just|only)\b` · `\bnot\s+\w+( \w+){0,3},\s+but\b` · `,\s*not\s+(a|an|the)?\s*\w+[.;]` · `\bless\s+\w+\s+than\b` · `\bat once\b` | rule 4 |
| dash_fragment | `\s—\s[^—.]{1,25}[.;]` · `:\s+[a-z][^.]{0,40}\.$` | rule 5 |
| abstract_agent | `\b(narrates|survives as|vanish(es)?|haunts|enters as|demands|coexists?)\b` | rule 2 |
| announce | `\bmatters\.$` · `^one reading:` · `\bthe heart of\b` · `\bin two registers\b` | rule 5 |
| unscoped | `\b(the corpus|the material|these accounts)\s+(shows?|tells?|narrates?)\b` | rule 3 |

Where it runs: on every prose field after the existing `words()`/`foreign()` pass, in THREAD, DOC/MEMO, ACCOUNT, PROJECT. It writes one note on the run row — `style: 4 (contrast 2, dash 1, announce 1)` — and `scripts/eval_metrics.py` sums them per record beside the existing totalising-word count. The record's processing history prints the total.

False positives are expected (a legitimate "not X but Y" the material itself states). That is why it counts and does not reject: the number is read beside a judgment, per `docs/EVAL.md`'s rule that Python never scores.

The `abstract_agent` and `announce` lists are seeded from one record about one corpus. They are a starting point, not a definition of the fault: after each evaluation, the sentences the readers flagged under spot check 11 are the source of new entries, and an entry that fires mostly on legitimate sentences in a new domain is dropped. The `contrast` and `dash_fragment` patterns are structural and should carry across domains unchanged.

## 6. Measurement

Same loop as every prompt change (`docs/EVAL.md`): the Ellis eight, GLM-5.2, iterative chain, one sentence per version. This is its own version — **not** bundled with the human-gap sets, because a mixed result has nothing to attach to.

- **Version sentence:** "Prose rules added to every reader-facing prompt; the prompts' own examples rewritten in them."
- **Counts:** `prose.py` totals per record, v3-3 against new; expected to fall by more than half on contrast, dash_fragment and announce. Claim count, passage coverage and dangling citations unchanged within noise — the block must not cost evidence.
- **Blind read:** the seven faults plus one spot check appended to `scripts/eval_rubric.md`:
  11. **Plain statement.** Sample five sentences from the corpus summary and five from accounts. For each: is the grammatical subject a person, group, material or the claims? Does it state its scope? Report all ten, answer *yes* if three or more fail.
- **Second provider:** one MiniMax-M3 run of the same version on the two seeds, counts only, to show the block is not tuned to GLM.
- **Second domain:** one run on the non-narrative fixture from the human-gap plan (documents or open-text survey answers), counts plus a short read of the material summaries and one account. What it must show: the prose names the document, the author or the respondents as its subjects; it does not manufacture a narrator, a chronology or a "story" where the material has none (the `doc.md` phrase this plan removes was doing exactly that); the smell counts are as low as on Ellis. A block that produces plain prose about lives and mannered prose about organisations has only moved the problem.
- **Thresholds, fixed now:** no rubric dimension drops more than one point; pattern hunger and overreading absence do not worsen (rule 6 keeps hedges — the audit's warning that removing every hedge makes the tool worse); `prose.py` contrast + dash_fragment + announce total falls by ≥50% on both the Ellis and the second-domain records; tokens within +2%.

## 7. Risks and how each is held

| Risk | Hold |
|---|---|
| Over-correction to flat, list-like prose | Rule 1–3 demand subjects and scope, not shortness; the "This:" examples are full sentences. Judged by spot check 11 and `which_reads_better`. |
| The block trades one register for a narrative-shaped one — every material becomes someone's "account", every document a "story" | The examples are a focus group, field notes and a document, not an interview; rule 3 names authors and documents as subjects; the second-domain run in §6 is the check. |
| The block crowds out the evidence rules | ≤180 words, placed last in the system message; the evidence rules stay numbered first. If the eval shows dangling citations or pattern hunger rising, cut rules 5 and 7 before touching 1–4. |
| Hedges deleted as "tone" | Rule 6 forbids exactly that; pattern hunger and overreading absence are the thresholds. |
| Every recording invalidated | True for every prompt that gains the slot. Re-record per label against the seeds; the suite stays offline. Budget one recording pass. |
| Interface copy stays in the old voice while generated prose changes | Ship the audit's §5 inventory in the same release; it needs no model run. |
| Existing project analyses keep the old prose | They are not regenerated silently (audit §7). A researcher who wants the new prose re-runs synthesis from the step they choose. |
