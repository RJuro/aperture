# What was learned before this repository existed

*A condensed record of the design documents, three rounds of simulated-researcher trials, and the
literature review that preceded Aperture's lean restart. Each finding cites its source in the
predecessor repository (`MASSHINE_Qual_LLM`, now archived). The long form, sectioned by area, is in
`docs/research/`. Written 2026-09-03 from an indexing pass by gpt-5.6-sol (local), read and edited
by hand.*

The point of this document is that nobody re-learns any of it. Where a finding changed the design,
the current mechanism is named in **bold**.

## 1. What the trials established

The trials used simulated researchers — LLM readers driven turn by turn with a fixed reading budget
— graded blind by oracle models against a frozen rubric and a sealed twelve-question battery. They
are evidence about the *instrument*, not about human researchers. [design/INSIGHT-LOOP.md §8;
design/SIM-PLAN.md §1]

1. **Quotes the model emits can be checked, and checking them is free.** Three live passes bound
   18/0/0, 37/1/0 and 38/0/0 quotes (bound / not in the material / missing). Requiring a ≤12-word
   verbatim quote per claim did not reduce output and repaired three defects at once: a claim
   citing the wrong sentence (D15), a claim whose evidence had been flattened, and dissent hidden
   inside a step. → **The anchor law. Every claim carries a quote Python finds; a wrong pointer is
   repaired; a missing quote drops the claim.** [design/ROUND-LEDGER.md §Phase A1; §Round 3]

2. **A mediated reader's criticism is less reliable than their assent.** Four readers independently
   objected to three system claims; oracles overturned two objections — one treated unseen kin as
   absent, one rejected a true claim whose citation was mis-bound. Assent is checked against a
   passage; criticism is often checked against a gap. → **Doubt is routed to a search of the
   material (CHECK), never to a rewrite.** [design/ROUND-LEDGER.md §Round 2, D14–D15]

3. **Absence must be searched, not inferred.** A confident "could not find" was false because the
   sentences existed under another code (D0); three readers rejected a true kin claim because no
   relative appeared in the quarter they had opened (D14). In round 3 a search of 363 unread
   passages refuted a negative and a search of 302 supported one. → **CHECK searches the passages
   no claim rests on; the verdict is Python's — a quote must bind or the answer is "not found in
   N".** [design/ROUND-LEDGER.md §Round 1 D0; §Round 3 "D14 closed"]

4. **Reader-facing coverage devices did not move fidelity.** Territory lists, a coverage map and a
   whole-document arc changed fidelity by +0.5, +1.0 and 0.0 against a noise band of 1.0; the map
   and the arc each cost 2.0 in groundedness. → **No coverage strip. With the material on the page,
   unmarked text is the coverage display.** [design/ROUND-LEDGER.md §Round 2 "The scores"]

5. **The one mechanism that worked changed the engine's own representation, not the reader's.** An
   89-word brief the model wrote to itself won a blind comparison and made the next pass address
   exactly the three gaps it named (codes 8→11, steps 9→17). → **Self-prompting exists, in exactly
   one slot** — and see law 5 below for what it may carry. [design/ROUND-LEDGER.md §Round 2 "Arm 4";
   engine/sim_runs/round2/screen-arm4-verdict.md]

6. **A sentence is the wrong unit; an answer without its question manufactures facts.** Zero of two
   readers reconstructed a sibling sequence from sentence-sized excerpts; three of four did from
   question-and-answer exchanges. → **Material is laid out as turns; a quote is shown inside its
   turn.** [design/ROUND-LEDGER.md §Round 2 "Arm 0 worked", D11]

7. **Budget was never the binding constraint.** Given 30 doors, a reader stopped at 20 (28.8%
   exposure), having read nothing of the first two sections — consistent with the focus they were
   given. The trials had been scoring a focused reading against an unfocused ceiling. → **No
   reading budget in the product, and no pressure to "finish".** [design/ROUND-LEDGER.md §Round 3;
   §Round 4 design]

8. **Green tests proved nothing about output.** 453 passing tests coexisted with two bugs that
   dropped validated quotes on the way to the page and one that left a counter at zero. → **Every
   phase ends with a real-output check; field-coverage tests walk real rows, never key lists.**
   [design/BUILDOUT.md §Build strategy; design/ROUND-LEDGER.md §Phase A1]

9. **A slot that feels optional in a prompt returns empty.** A register slot yielded 0 claims while
   the prompt opened with a capitalised prohibition and described the exception later; making the
   rules symmetrical yielded 2 claims / 5 instances in the same run. → **Rules that must fire sit
   at the top of a prompt, in parallel form, equal weight.** [design/ROUND-LEDGER.md §Round 3]

10. **Synthesis, not retrieval, is where euphemism is minted.** Both blind analyses in the arm-4
    comparison turned an unresolved death into a tidy determinant of family movement; more doors
    and a self-brief did not fix it. Still open (§6). [engine/sim_runs/round2/screen-arm4-verdict.md]

11. **A blind theorist over-generalises.** Themes built from code labels alone produced over-stuffed,
    single-case-to-universal themes; showing the theorist the transcript fixed it. The lean restart
    rebuilt the blind version and had to re-learn this (see §3, law 5). [design/MASSHINE.md;
    docs/prompts/README.md postscript]

12. **Run-to-run variance is large.** Two identical runs of one model on one interview produced 37
    claims across 5 themes and then 22 across 3. Nothing about richness can be read from one run.
    → **Model comparisons need repeated runs graded blind; counts at n=1 are noise.** [docs/MODELS.md]

## 2. The defect catalogue

| Id | Defect | Status in Aperture |
|---|---|---|
| D0 | Absence inferred from the codebook, not the material | closed — CHECK searches uncited passages |
| D1 | A passage used as support though its second half retracts it | open — no neighbour-retraction check |
| D2 | Harm rewritten as neutral "repair" | open — a prompt rule only |
| D3 | A moral refusal flattened into data uncertainty | mitigated — the speaker's words sit in the claim |
| D4 | The research frame returned as findings | **partly closed — law 5**: focus never shapes ideation; conclusions never re-enter prompts |
| D5 | Material outside the mediated layer invisible | closed — the whole material is on the page |
| D6 | Reactions did not update stance | superseded — no stances; one comment per block |
| D7 | Decline memos bloated later prompts | superseded — no decline memos |
| D8 | Two sentence-id formats | closed — one id space, one writer |
| D9 | Register (how people speak) unindexed | dropped from v1 |
| D10 | No way to sample against the system's frame | partly — CHECK asks the uncited material any question |
| D11 | Sentence-sized doors manufacture facts | closed — turns |
| D12 | Recurrence cannot be shown from a few passages | open |
| D13 | "Weakest evidence" flags bias what readers check | closed — no such field |
| D14 | Under-coverage mistaken for absence | closed — CHECK |
| D15 | True claim, wrong pointer | closed — the anchor law repairs the pointer |
| D16 | `weakest_sids` unvalidated | closed — removed |
| D17 | Roster missed an alias | open — `people` carries aliases; unverified live |
| D18 | A topic outlives its exchange | moot — the whole material is shown |
| — | Duplicate charging of one exchange | moot — no doors |
| — | Validated fields silently dropped by fixed key lists | closed — field-coverage tests, `dict(row)` |
| — | Frontend loaded two products into one state | closed — one server-built context per page, no JS |

[design/ROUND-LEDGER.md throughout; engine/sim_runs/*/memo-*.md]

## 3. Decisions that carried forward, and the one the restart added

- **Instrument, not persona.** It reports grounded claims and exposes evidence; interpretation is
  the researcher's. [design/MASSHINE.md §1]
- **The researcher's work is judgment, not taxonomy administration.** Codebook curation was
  rejected as making the researcher the model's librarian. Codes have no page. [design/MASSHINE.md §3]
- **Slots, not pipelines.** Python owns structure, caps and validation; the model fills named slots.
  [design/BLUEPRINT.md §3]
- **Every number is a derivation over rows the page links to; no counter is stored.** After
  counters drifted and destroyed trust. [design/BUILDOUT.md §B1.2]
- **Server-rendered, one context per page, no client state.** After a 3,340-line SPA combined
  incompatible products while its engine tests stayed green. [design/V2-PLAN.md §1; design/UI-AUDIT.md]
- **Our vocabulary stays out of the page.** Anchor, door, slot, ledger, exposure, thread, moment,
  frame are design words; the page says quote, claim, line, material. Enforced by test.
- **Law 5 — slot discipline (added 2026-09-02).** A prompt template is universal; a slot may hold
  the material, validated structure, or the researcher's verbatim words — never prose the system
  wrote about the corpus. Conclusions flow up; only *questions* flow forward into the next reading.
  Found by reading the compiled prompts on real data: the brief carried findings into READ, theme
  gists carried findings into DOC as definitions, THEMES was blind, and one prompt rule contradicted
  another. Enforced by `tests/test_p9_law5.py` with sentinels. **Corollary learned three times: when
  a slot keeps leaking a conclusion, remove the information rather than add a rule.**
  [docs/prompts/README.md]

## 4. Rejected, with reasons

- Coverage maps, territory lists, document arcs as reader aids — below noise, cost groundedness (§1.4).
- Door budgets — a measurement device mistaken for a product feature (§1.7).
- Automatic verification of every machine negative — one call per claim; negatives are a verb the
  researcher runs, marked unverified until then. [design/BUILDOUT.md §B1.8]
- Majority vote and self-consistency across coders — they erase the minority readings reflexive
  analysis exists to keep. [_archive/MASSHINE_v0_SPEC.md §Locked decision 5; _archive/research.md]
- κ as a headline — it assumes a correct coding and treats subjectivity as noise. [_archive/research.md §KF3]
- Embeddings for merging — deferred; a natural-language merge a human can audit was preferred.
  [_archive/MASSHINE_v0_SPEC.md §Locked decisions 1, 4]
- Buttons on individual claims — a claim needs no affordance when its quote is beside it; what
  wants correcting is how the synthesis was made. [this repository, 2026-09-02]

## 5. From the literature, the parts that shaped the laws

- A one-shot Copilot thematic analysis fabricated **58%** of its quotes (humans: 79% correct) and
  drew themes from the first two or three pages. The failure is of that protocol — stateless,
  twenty-one tasks in one turn — not of verified, stateful systems. → the anchor law; one bounded
  step per call. [_archive/compass_artifact_…md §KF2]
- Long contexts retrieve well at the edges and poorly in the middle across all frontier models
  tested. → per-material passes; a theme account layer so the corpus step never reads every claim.
  [ibid. §KF3]
- Provenance — theme → codes → quote → exact span — is the strongest defensible claim an
  instrument can make; it avoids claiming the model "understood". [_archive/research.md §KF6]
- "Theme as bucket": clustering yields categories; a reflexive theme is an argued pattern around a
  central concept. → a gist *defines*, an account *concludes*, and the theorist sees the text.
  [_archive/research.md §KF2]
- A standpoint directs attention without dictating findings — sensitizing concepts, questions,
  legitimate low-yield areas, a caricature guard. → the ideation step: *an angle decides where to
  look, never what is found.* [packs/migration_oral_history/reference.md]

## 6. Still open

1. Whether interaction adds value across documents (the two-document test was designed, never scored).
2. The focused ceiling: a full reader carrying the same focus (C0-F) was designed for round 4, never run.
3. Whether any of this helps a human researcher — the Nirosha validation remains pending and is the
   only evidence that would count.
4. Synthesis-stage euphemism and causal smoothing (§1.10) — no mechanical guard exists.
5. Which model ships, on evidence rather than one run each (§1.12).
6. D1, D2, D12, D17.
7. How to sample material no claim reaches beyond a single question to CHECK.

## 7. Vocabulary, old to current

| The record says | Aperture says (in code) | The page says |
|---|---|---|
| anchor | anchor | the quote |
| door, exchange | — (the whole material is shown) / turn | passage, turn |
| step, moment | moment | claim |
| thread | thread | line |
| finding, theme | theme | theme |
| brief | `project.brief` — now *questions* | open questions the readings carry forward |
| exposure, ledger | — (derived counts) | "claims rest on 45 of 433 passages" |
| register, territories, residue, declines | dropped from v1 | — |
| check-back, absence check | CHECK | check this against the material |
| roster | people | who appears in it |
