# Plan: fewer model calls, the same reading

**Date:** 6 September 2026
**Prompted by:** an adversarial read of every `llm.chat_json` call site, against the `call` rows in `bench/minidata2/aperture.db` (24 calls, two materials, eight themes, MiniMax-M3) and the two-provider DOC comparison in `data/aperture.db`.
**Constraint:** no loss of reading quality. The five laws hold (PLAN.md §3). Every change that alters what a model is shown or asked is an evaluation condition under the pass-6 protocol (docs/EVAL.md), judged blind on the seven faults, before it becomes the default. Changes that alter nothing a model sees ship on the replay suite alone.
**Companion:** `docs/audits/2026-09-05-llm-and-method-audit.md` §"Efficiency", whose ordering this follows — *reduce redundant work, make retries resumable, then tune concurrency and effort* — and Astra-review AR-11.

## 0. The chain as it runs

One material through an iterative project with T live themes. Every row is one `llm.chat_json` label; "sent" is what fills the slots.

| Step | Unit | Calls | Sent | Where |
|---|---|---|---|---|
| FRAME | material | 1, +1 DIARIZE when speech has no speaker cue | first 6000 + last 1500 chars, the speaker scan | `frame.py:138`, `jobs.py:54–80` |
| ANGLES | material | 1 | first 18000 + last 6000 chars, frame, orientation, every material's open questions | `angles.py:171` |
| READ | material | 1, **one at a time across materials** | the whole material, the codebook, frame, angles | `read.py:162`, `jobs.py:483` |
| THEMES | material | 1, its own stage, so a barrier | the whole material with its code marks, the codebook, the theme set | `themes.py:267` |
| THREAD | theme × material | T (+ candidates marked here), **waves of 3** | the whole material, frame, focus, one theme, its codes, the claims of earlier waves | `synth.py:635–661` |
| VERIFY | material | ⌈claims/60⌉, +1 per partly-answered batch | claim, quote, passage window | `verify.py:143–154` |
| line_summary | line that lost a claim | 0…T | theme, standing claims | `synth.py:439`, `:672` |
| DOC | material | 1, +1 rewrite on any flag | the whole material, the lines, orientation, frame | `synth.py:703–727` |
| VERIFY-SUMMARY | material | 1, +1 after a rewrite | numbered sentences, claims | `verify_summary.py:67` |
| TIGHTEN | material | 0…⌈partly/60⌉, then VERIFY over the rewrites, then line_summary per touched line | as VERIFY, plus the check's note | `tighten.py:56–116` |
| ACCOUNT | theme, at every chain's tail | ≤T, fingerprint-gated, **one after another** | ≤150 claims, shared passages, absences | `jobs.py:322–345`, `account.py:301` |
| PROJECT | project, at every chain's tail | 1 | the accounts, the summaries, candidate claims | `synth.py:869` |

Explore projects add RECONCILE (one, in turn with READ), MEMO (one, plus VERIFY-SUMMARY, plus one rewrite and re-check when flagged), RESIDUAL (one per chunk, plus VERIFY over its additions); THEMES runs once per batch and DOC writes no summary. The researcher's verbs add CHECK (materials × chunks, one after another), SCREEN (one per material before a back-fill) and consolidate (one cross THEMES, one THREAD per cell, one VERIFY per touched material, then the tail).

Two structural facts follow. **The whole material goes out T + 3 times per material** — READ, THEMES, T THREADs, DOC. **THREAD is the only step that scales as themes × materials**; everything else is once per material or once per project.

## 1. Where the cost is

Measured, `bench/minidata2/aperture.db`, MiniMax-M3, two materials, eight themes, 24 calls:

| Label | Calls | Output tokens | Share of output | Reasoning share | Seconds per call |
|---|---|---|---|---|---|
| thread | 8 | 156,664 | 44% | 97% | 218 |
| read | 2 | 69,463 | 20% | — | 366 |
| themes | 2 | 44,530 | 13% | 98% | 208 |
| doc | 2 | 32,605 | 9% | 95% | 200 |
| verify | 2 | 14,899 | 4% | 88% | 52 |
| angles | 2 | 13,815 | 4% | 85% | 89 |
| verify_summary | 2 | 13,099 | 4% | 95% | 82 |
| project, reconcile, frame | 4 | 7,959 | 2% | — | 9–34 |
| **all** | **24** | **353,034** | | **82%** | |

The same DOC step, same material, nine themes, two providers (`data/aperture.db`, the run `llm.py:54` cites):

| Provider | Output tokens | Seconds |
|---|---|---|
| mistral / glm-5-2, effort high | 10,765 | 120 |
| minimax / MiniMax-M3 | 151,768 | 1,351 |

Three things carry the plan.

1. **THREAD is the cost, and it is the cost because of its count.** Eight calls, 44% of output, 46% of model seconds. It is also 37% cache-served on input — the material-first prompt order works — so the tokens that cost are the ~20k of reasoning each call spends, not the 7k of input.
2. **On M3 a call has a floor, whatever it is asked.** VERIFY-SUMMARY spends 6,500 output tokens to rule on six sentences. Four output tokens in five are reasoning nobody reads. So on the default provider **the number of calls is the bill**, more than the size of any one of them, and merging small calls is worth more than trimming large ones.
3. **The effort table does nothing on the default provider.** `llm.reasoning()` consults `EFFORT` only when the provider's own default is non-empty (`llm.py:243`); M3 takes no parameter. The comment at `llm.py:50–59` that THREAD and ACCOUNT run at *medium* describes Mistral only. Every M3 number above is at the provider's unbounded default, and there is no knob.

One gap: **no `call` rows exist for any GLM run**, so the cached and reasoning split on the EU provider is unmeasured. Phase 0 fills it.

## 2. Findings, ranked

Each: what, the evidence, what it saves, what it risks, and the law it must not bend.

### F1. THREAD's waves exist for one rule, and the rule can be served after the fact

The waves are sequential so that each line sees the claims of earlier waves (`thread.md` rule 8, `_claimed_block` at `synth.py:301`) — what stops one passage coming back under three themes. Wave-mates already do not see each other (`synth.py:629`). So the sequence buys the rule for two-thirds of pairs and costs three rounds of the slowest call in the system.

- **(a) One round, overlap resolved afterwards.** Fire every THREAD of a material at once, bounded by the rate limit as now; then, where a passage carries claims under two or more themes, either keep both and mark it on the page (law 4: the reader sees the derivation) or ask one small call over only the overlapping passages — claims listed, no material — which stays. DOC's wall clock falls from three rounds to one. Tokens are about even. Keep the cache warm-up of F9 or lose the 37% of THREAD input the cache now serves.
- **(b) Two or three themes per call.** T calls become ⌈T/3⌉, and on M3 each call removed is a reasoning floor removed. One call for *every* theme at once was measured thin (`synth.py:495–502`: the model rations attention across six lines); two or three is untested. **An evaluation condition, not a default.**

Law 1 is untouched — every moment still binds. Law 2 is untouched — a passage under two themes is a fact the page states, not an absence.

### F2. Line summaries are written before the check and rewritten after it — once per line

THREAD writes a 90-word summary with the line (`thread.md` rule 9); VERIFY may take a claim away; `line_summary` is then called **once per lost line** (`synth.py:672`, `jobs.py:273`), and TIGHTEN calls it again per touched line (`tighten.py:116`). The summary reaches no other prompt: it is page-only. So a material can pay for T summaries inside the THREAD answers and up to T more calls to write them again.

Write them **once, after VERIFY, all lines of the material in one call** — theme, standing claims, quote each, exactly what `line_summary.md` is shown today. Rule 9 leaves `thread.md`, which also shortens every THREAD answer. What is lost is a summary written with the material in view; what stands is what `line_summary.md` already does for every line the check touched, which the design accepted. Law 5 holds: the slot carries claims with their quotes, validated structure.

### F3. VERIFY, TIGHTEN, VERIFY again: three passes over one set of passages

`tighten.py:42` rebuilds VERIFY's claims block almost verbatim — same frame, same passage window, same batch size — and then VERIFY runs a third time over the rewrites (`tighten.py:109`), then line summaries again. A material with claims marked *partly* pays three calls for one judgement.

Let VERIFY return, beside a *partly* verdict, **the part the passage carries** as a rewritten claim; Python applies it, anchors it as any moment, and the line summary of F2 sees the result. The judge that found the gap writes the fix over the same window it judged. TIGHTEN and its re-check go. Risk: the same call proposes and blesses; the blind judge on the overclaim fault is the check.

### F4. The DOC rewrite re-sends the material to change one sentence, and fires on *partly*

`verify_summary.run` calls `again` on any `not` **or** `partly` verdict (`verify_summary.py:118`), and `again` is the full DOC prompt with the whole material (`synth.py:714–727`), of which only `summary` is kept — questions and people come from the first answer. Two cuts, both Python and prompt-only:

- fire the rewrite on `not` only. A *partly* sentence is kept and marked, which is what PLAN.md §2 already specifies for it;
- give the rewrite a prompt of its own: the flagged sentences, the lines, the orientation — no material. It rewrites over claims, and the claims are in front of it.

Then one VERIFY-SUMMARY over the rewrite, as now.

### F5. Accounts: one after another, and rewritten for one new claim

`_accounts` loops (`jobs.py:335`); the calls are independent by construction — each sees its own theme. Run them side by side, as THREAD waves do. Zero risk.

Then the count. Every chain ends here, and the fingerprint (`account.py:88–114`) changes on any change to a theme's claims, so one uploaded material rewrites nearly every account, and PROJECT after it. Over a project's life that is themes × materials again. Rewrite when a theme's live claims changed by at least *k* (three, say) or a fifth, or a comment is open, or the researcher asks; otherwise the theme page prints **"written over 41 of 43 claims"** — a derivation, which is what law 4 asks for, and truer than a fresh account that says the same thing. `_another_chain` (`jobs.py:434`) already leaves the tail to the last queued chain; this extends the same idea to a chain that is alone.

### F6. Four loops that are sequential and need not be

| Loop | Where | Independent because |
|---|---|---|
| VERIFY batches | `verify.py:143` | disjoint claims |
| CHECK materials × chunks | `check.py:55–67` | disjoint passages; verdict is Python's after |
| TIGHTEN batches | `tighten.py` | disjoint claims |
| ACCOUNT per theme | `jobs.py:335` | one theme each |

`ThreadPoolExecutor` with `contextvars.copy_context().run`, exactly `synth.py:635–646`, so tokens and progress still land on the step's row. The provider's rate limit bounds it as it bounds the waves; `_ask` waits out the 429s. Wall clock only; no prompt changes; the replay suite is the test.

### F7. Iterative THEMES is M near-identical calls when a batch arrives

Each sends the codebook and the whole theme set again with a different material block, one after another, each its own stage. `themes.run_cross` already does one call per batch for explore projects and is what consolidate uses for iterative projects too (PLAN.md §14: "both methods consolidate through this call"). A multi-file upload to an iterative project could take the cross call once. It is also exactly the comparison pass 6 is running, so: **after pass 6 reports, not before.**

### F8. The provider is the 10× lever, and the docs say the quality question is open

Same step, same material: GLM at *high* spent 14× fewer output tokens in 11× less time than M3 at its default. `docs/MODELS.md:51–53` already concludes GLM for development and the EU deployment. What stops the switch is `MODELS.md:40–43`: two identical M3 runs produced 37 claims and 22 claims, so any richness comparison at one run each is noise.

Two moves, in order:

- **Per-label routing.** `PROVIDERS`, `EFFORT` and `reasoning()` are already keyed by label; a `{label: provider}` table beside `EFFORT` is a small change to `llm.py`. Start where a verdict is short and binary — `verify`, `verify_summary`, `check`, the line summaries of F2 — on GLM at *low*: cheapest to judge, least to lose.
- **Then the reading labels**, `read`, `thread`, `themes`, `doc`, each as a pass-6 condition at n ≥ 3, because there the model's deliberation is the reading.

Do not pick the cheaper provider for producing fewer claims (Astra §8). Report the invoice beside the estimate.

### F9. The first wave misses the cache

37% of THREAD input is cache-served because waves two and three hit what wave one wrote. Wave one's three calls go out together and all miss. Send the first THREAD alone and the rest once it has started answering — one line in the wave loop. Under F1(a) this is the line that keeps the cache.

### F10. Not worth a change

- **FRAME + ANGLES in one call.** Both cheap; DIARIZE sits between them and changes what ANGLES is shown. Skip.
- **A targeted "fix this JSON" call instead of a full re-send.** Zero `invalid_json` rows in 24 recorded calls; `_repair` catches the stray quote. Add when a log shows one.
- **Caching CHECK by question.** The same question is rarely re-asked and any edit invalidates it.
- **Raising `PARALLEL` or `WAVE`.** They are the rate limit (`jobs.py:453–462`). More in flight is more 429s.

## 3. What this plan refuses

- **One THREAD call for all themes.** Measured thin; that is why the split exists.
- **The code-hit gate as default.** EVAL pass 3: a third of DOC's cost for a third of the good lines. SCREEN is the accepted cheap look, and only before a back-fill.
- **ANGLES folded into READ.** Angles are the counter-focus and must never see the focus (PLAN.md §2).
- **The material out of DOC's first call.** Questions and people are read from it.
- **Any slot that carries the system's own prose about the corpus** (law 5). F4's flags are the instrument's own labelled paragraph, already allowed; F3's rewritten claim is a claim with its quote; F2's summaries are written over claims with their quotes.

## 4. Phases

**Phase 0 — the baseline (half a day).** Run `bench/mini` on both providers with `call` rows; extend `scripts/eval_metrics.py`'s per-step table to per-label calls, attempts, input, cached, output, reasoning, seconds. This is the number every later phase is judged against, and it is the first GLM measurement at call granularity.

**Phase 1 — nothing a model sees changes (a day).** F6, F9, F5's parallel loop. Replay suite green; DOC and accounts wall clock from Phase 0 against after.

**Phase 2 — fewer calls, each an evaluation condition (a week).** In this order, each a snapshot-visible prompt diff, blind-judged on the seven faults, counted from `call` rows:

1. F2 — line summaries once per material, after the check.
2. F4 — the DOC rewrite on `not` only, without the material.
3. F3 — VERIFY carries the tightened claim; TIGHTEN goes.
4. F5 — accounts rewritten on a claim delta, with the derivation on the page.
5. F1(a) — one THREAD round, overlap after.

**Phase 3 — the multipliers, gated on measurement.** F8 routing, judging labels first; F1(b) and F7 as pass-6-style conditions.

## 5. What it should buy

Calls per material, iterative, T = 9, no candidates:

| | Today | After Phase 2 |
|---|---|---|
| fixed (FRAME, ANGLES, READ, THEMES, T THREADs) | 13 | 13 |
| variable (VERIFY, line summaries, DOC, its rewrite, VERIFY-SUMMARY, TIGHTEN and its re-check) | 4–18 | 3–5 |
| tail per chain (accounts, PROJECT) | ≤10, one at a time | ≤10, side by side, most skipped |
| DOC rounds of the slowest call | 3 | 1 |

The structural work removes the variable tail and the serial rounds; it does not touch the thirteen. Those are the reading, and the only levers on them are F1(b) and F8 — which is why both are gated on the blind judge and not on a savings figure (Astra §8: some cases should justifiably cost more).

## 6. Risks and how each is held

| Risk | Held by |
|---|---|
| A summary written over claims alone reads thinner than one written with the material in view (F2) | it is what every checked line already gets; the judge on the *thin* fault |
| The verdict that writes its own fix is lenient with it (F3) | the anchor still binds; the judge on the overclaim fault |
| A *partly* sentence left standing in a summary (F4) | it is marked on the page and on the run, as PLAN.md §2 already specifies |
| A stale account (F5) | the page prints the derivation; a comment or a click rewrites it |
| Two themes claim one passage in one round (F1a) | kept and shown, or one small arbitration call over the overlaps only |
| Run-to-run variance larger than any condition's effect (all of Phase 2, F8) | n ≥ 3 per condition; thresholds fixed before unblinding |
| A faster provider found "better" for finding less (F8) | Astra §8's rule; coverage judged beside cost |
