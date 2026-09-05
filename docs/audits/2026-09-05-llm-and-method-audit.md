# Aperture: model use, analytical state, and qualitative method

Audit date: 5 September 2026. Repository revision: `92ed7960577754cb07baa56fe97bbbb9a2761e5e`.

## Assessment

The efficiency hypothesis is substantially supported by the implementation and the historical benchmarks. The main opportunity is architectural: build a reusable, source-grounded reading of each document, then develop and review cross-case themes over that evidence. Shortening the prompts or changing the model alone would leave the main source of repeated work intact.

The recent candidate/open/frozen lifecycle is a useful improvement. It does **not** remove the default practice of reading an entire document separately for every established project theme. Initial coding is also influenced by earlier project analysis through the shared codebook and the angles step. This can be an intentional iterative method, but the product should identify that choice and let a researcher conduct an exploratory reading without that conditioning.

Several concrete defects should be fixed before optimizing the workflow. They affect whether a researcher’s correction reaches the model, whether revised evidence actually replaces old evidence, and whether an unexamined case is represented as examined. These are more consequential than spending too many tokens.

## Scope and evidence limits

- GitHub’s remote HEAD and the local checkout both resolved to the revision above. The original untracked `Aperture-UI-Exploration.zip` was left alone.
- The deployed service at [Aperture](https://aperture.automate.business.aau.dk) returned `{"ok":true}` from `/health`; its home page redirected to a working sign-in page. Authenticated project pages, production run logs, runtime configuration, and the deployed container’s commit were unavailable. A healthy endpoint does not establish which revision is deployed.
- Reviewed all **12 active prompt templates** in `app/prompts`, all engine stages, the LLM client, storage, scheduling, feedback/rerun planning, relevant page rendering, and the repository’s design and evaluation record.
- Historical benchmark files are local evidence, not current production measurements. The local databases inspected read-only were at schema version 12; current code uses version 15. They must not be mistaken for a fresh evaluation of the theme lifecycle change.
- The existing offline suite returned **425 passed, 1 failed**. The failure is an empty `hold` form returning HTTP 422 where the test expects 404, in `tests/test_p24_hold_pages.py:73`. It does not explain the model-use concerns.
- Additional [offline diagnostic probes](/Users/roman/Desktop/20_Research-Projects/aperture/docs/audits/2026-09-05-probes.py) reproduced the defects identified as “reproduced” below. They use synthetic data, in-memory databases, and mocked model replies. They establish control-flow behavior, not real-model quality.
- No application behavior was edited, no production data was changed, and no paid model calls were made for this audit.

## What happens now

Each HTTP model request contains one system message and one user message. There is no persistent model conversation per document or project. The application reconstructs context from its database for every call. That is a sound starting point: analytical memory should reside in inspectable records, rather than depend on a model remembering a chat. The issue is the content, dependencies, and versioning of those records. See [the request builder](/Users/roman/Desktop/20_Research-Projects/aperture/app/llm.py:302).

An upload batch follows this sequence:

1. Extract text and assign stable sentence IDs locally.
2. FRAME → optional DIARIZE → ANGLES → READ for each document. Framing and angles overlap across documents; READ takes turns because it reads and updates the shared codebook.
3. THEMES once per newly read document, serially. Every document in the batch has already contributed codes before the first theme pass.
4. Document synthesis in parallel across up to four documents. Each synthesis launches theme-specific THREAD calls in waves of three, then verifies claims, writes the document summary, and verifies that summary.
5. Write changed project-theme accounts, then the project summary.

The scheduler can therefore have up to 12 THREAD requests in flight. Parallel execution changes elapsed time; it does not reduce the number of model judgments or tokens. See [upload planning](/Users/roman/Desktop/20_Research-Projects/aperture/app/jobs.py:511) and [document synthesis](/Users/roman/Desktop/20_Research-Projects/aperture/app/engine/synth.py:379).

### All active prompts and their inputs

“Default” below means the configured provider’s reasoning default, not necessarily the provider’s external API default. In the code, Mistral defaults to `high`; selected stages override this. MiniMax normally receives no effort parameter. A global environment override can change this behavior. There is one configured model for all stages, not a model selected independently for each task.

| Stage | Actual context sent | Output and stored state | Audit judgment |
|---|---|---|---|
| [FRAME](/Users/roman/Desktop/20_Research-Projects/aperture/app/engine/frame.py:135) | Mechanical speaker counts; first 6,000 and last 1,500 characters; optional correction plus earlier structure | Kind, layout, title, year, speakers, sections, orientation | Appropriately bounded. Structure validation is useful. Head/tail cannot discover interior structure reliably; orientation is not a verified reading of the whole document. No effort parameter under normal stage settings. |
| [DIARIZE](/Users/roman/Desktop/20_Research-Projects/aperture/app/engine/diarize.py:35) | Frame plus **entire document**, if speech has no accepted speaker labels | Estimated voice-change boundaries, stored as sections | Keep conditional. Use explicit uncertainty downstream: the page marks estimation, but analysis prompts do not consistently carry that qualification. Default reasoning. |
| [ANGLES](/Users/roman/Desktop/20_Research-Projects/aperture/app/engine/angles.py:157) | Frame, orientation, previous project questions, existing open/frozen themes, first 18,000 and last 6,000 characters, optional researcher note | Research field, subareas, 5–8 proposed angles with questions; stored as prose | A sensitizing pass, already informed by project themes. It deliberately does **not** receive research focus. Move this after initial exploratory reading or make it an explicit mode. Its worked example contains findings despite its rules prohibiting them. Low reasoning. |
| [READ](/Users/roman/Desktop/20_Research-Projects/aperture/app/engine/read.py:121) | Focus, current **whole-project codebook**, frame, angles, optional note, **entire document** with sentence IDs | Project-level code definitions and document-specific code hits; at most 60 codes, with 15–50 new codes allowed according to document length | “Reuse before inventing,” fixed abstraction, and sparse citation instructions favor an established vocabulary and illustrative passages. No coverage ledger, local code version, or explicit residual findings. Default reasoning. |
| [THEMES](/Users/roman/Desktop/20_Research-Projects/aperture/app/engine/themes.py:162) | **Entire current document**, its code hits, global codebook, all frozen/open/candidate themes, focus, optional note | Revisions/merges of themes, new candidates, code membership, frozen-theme tension notes, stability counter | One document’s text is asked to revise a corpus-level structure whose other source texts are absent. Code labels from all cases help, but do not replace cross-case evidence. The prompt asks for the whole theme set repeatedly. Default reasoning. |
| [THREAD](/Users/roman/Desktop/20_Research-Projects/aperture/app/engine/synth.py:297) | One theme definition, this document’s matching code IDs, claims already written under other themes, focus, frame, open comments, **entire document** | 4–14 claim/quote items and a short theme-within-document summary | Dominant repetition. Established themes are followed even without matching codes by default; candidates are generally gated. The four-claim floor loses sparse but meaningful evidence. Medium reasoning. |
| [VERIFY](/Users/roman/Desktop/20_Research-Projects/aperture/app/engine/verify.py:52) | Frame and batches of 60 claims, quotes, cited sentence plus one neighbor each side | Unsupported claims removed; partly supported claims marked | Useful factual guard. Explicitly does not assess theme fit. Missing verdicts count as supported; limited context can misjudge case-level interpretations. Medium reasoning. |
| [DOC](/Users/roman/Desktop/20_Research-Projects/aperture/app/engine/synth.py:495) | Orientation, frame, focus, surviving thread claims/quotes, open comments, **entire document again** | Material summary, people, and questions that overwrite project brief | It sees source details that its summary is forbidden to use unless already selected into claims. Split case description/people from evidence-based synthesis. Questions are a document output being stored as project memory. Default reasoning. |
| [VERIFY-SUMMARY](/Users/roman/Desktop/20_Research-Projects/aperture/app/engine/verify_summary.py:58) | Frame, proposed summary sentences, all live material claims and quotes | Summary sentences removed or flagged | Does not receive the theme definitions whose names DOC must introduce, or the complete metadata context DOC sees. Missing verdicts pass; with no claims, verification is skipped and summary survives. Medium reasoning. |
| [ACCOUNT](/Users/roman/Desktop/20_Research-Projects/aperture/app/engine/account.py:182) | One theme, focus, up to 150 sampled claims/quotes across cases, other-theme readings of shared passages, cases without claims | 250–350-word theme account | Good intermediate layer, but sampling is positional, not designed to preserve contradictory cases. No feedback slot, no support qualifications, incomplete reuse fingerprint, unbounded shared-passages block. Medium reasoning. |
| [PROJECT](/Users/roman/Desktop/20_Research-Projects/aperture/app/engine/synth.py:528) | Open/frozen theme accounts, every material summary or orientation fallback, focus, all project-summary comments | Up to 300 words of synthesis and 150 words of interpretation | The prompt says it receives claim lists; actual material blocks contain prose summaries. Candidate-only evidence can supply no claim IDs at all. No entailment check at this level. Default reasoning. |
| [CHECK](/Users/roman/Desktop/20_Research-Projects/aperture/app/engine/check.py:25) | Researcher’s question and **only currently uncited passages**, in chunks of about 40,000 characters | Matching quotes and “found/not found” within searched passages | Useful as a residual search, inadequate as the general “check this” action. It can exclude the very evidence being questioned. Default reasoning. |

There are also source/documentation inconsistencies: `docs/prompts` has nine historical compiled snapshots rather than the 12 current templates; comments in several engines describe earlier inputs; deployment documentation advertises `APERTURE_MODEL` while the client reads provider-specific model variables. Audit the live builders, not those snapshots.

## Efficiency findings

### 1. Repeated full-document synthesis dominates historical token use

The local [v3 benchmark](/Users/roman/Desktop/20_Research-Projects/aperture/bench/v3-glm.metrics.json) records:

| Measure | Entire three-interview run | Document synthesis portion | Share |
|---|---:|---:|---:|
| Input tokens | 559,684 | 417,956 | 74.7% |
| Output tokens | 400,130 | 294,142 | 73.5% |

That synthesis portion includes THREAD, VERIFY, DOC, and VERIFY-SUMMARY; it is not a measurement of THREAD alone. v2 has a similar concentration: 74.1% of input and 76.9% of output. These are historical token counts, not verified current invoice costs or a benchmark of the latest revision. Cached input and model-specific rates matter for billing.

For a document with `T` attempted threads and `C` claims to verify, the normal pipeline makes approximately:

`5 + T + ceil(C / 60) + 1` calls,

where 5 is FRAME, ANGLES, READ, THEMES, and DOC, and the final 1 is summary verification. Add optional diarization, retries, and project-level work. With ten attempted threads and 70 pre-verification claims, that is 18 calls per document. Fifty such documents would be roughly 900 document-level calls plus accounts and project synthesis. This is an illustrative calculation, not an observed 50-document run.

The full source text is sent about `T + 3` times: READ, THEMES, every THREAD, and DOC, before counting the partial framing/angles inputs or optional diarization. A context window that accepts a whole document does not make repeated processing of it free.

### 2. Turning on the code-hit gate alone is not a sound solution

The default `APERTURE_FOLLOW` behavior follows every established theme. The existing [evaluation, pass 3](/Users/roman/Desktop/20_Research-Projects/aperture/docs/EVAL.md:209) found weaker lines where no code had fired, but also several strong ones the gate would discard. This is evidence that initial coding is an incomplete index of useful material, not evidence that every extra reading is waste.

Use a document evidence index plus targeted source retrieval and a deliberate residual/contradiction pass. Test recall before making the index a hard gate. Periodically revisit full source context, especially when a concept changes. Do not optimize by treating “not indexed” as “not present.”

### 3. Execution and transport leave avoidable costs

- All projects share one process-wide runner lock. A long project blocks unrelated projects even though their analytical state is independent. Use per-project serialization plus a shared provider concurrency budget. [Scheduler](/Users/roman/Desktop/20_Research-Projects/aperture/app/jobs.py:418).
- A document synthesis is one persisted step containing many model calls. An interruption can repeat successful work within that step; stopping is checked between planned steps, not between its thread waves and verification calls. Persist substep completion and check cancellation there.
- HTTP retries may resend a complete prompt six times; a JSON failure can repeat that cycle for the same task. The second parse attempt receives the same messages, without targeted correction. There is no requested output-token limit, context-budget preflight, structured response format, or call-level response-schema validation. [Client](/Users/roman/Desktop/20_Research-Projects/aperture/app/llm.py:302).
- The client stores aggregated input/output counts, but not cached input, reasoning versus visible output, individual attempt IDs, prompt/schema versions, or per-thread durable call records. Concurrent calls share a usage counter, so the per-call log’s before/after differences can include overlapping sibling consumption even where the aggregate step total is correct.
- Stable source context appears **after** theme-specific content in THREAD. This limits reuse of a long common prefix. Mistral documents prefix caching and cached-token usage fields; move stable context before changing questions where compatible, and measure the actual hit rate. Confirm availability for the deployed model/contract rather than assuming the documented Mistral examples establish GLM support. [Mistral caching documentation](https://docs.mistral.ai/studio/conversations/advanced/prompt-caching).
- Prefer provider-supported schema-constrained output, with application validation regardless. This avoids spending a second complete analytical call solely on broken JSON. Model-specific support needs verification. [Mistral structured outputs](https://docs.mistral.ai/studio/conversations/structured-output/custom).

Increasing parallelism is not the first optimization. Reduce redundant work, make retries resumable, then tune concurrency and effort against measured quality.

## Analytical state and correctness findings

### 4. Researcher feedback is consumed without reaching ACCOUNT — reproduced

A theme comment plans an account rewrite. `jobs._account` calls `account.run`, which has neither a feedback argument nor a feedback prompt slot. A successful run still consumes the feedback. A project-level comment also schedules all theme accounts, but none sees that correction; PROJECT alone receives it.

This spends money while creating the impression that the researcher’s instruction was considered. Add scoped, versioned directives to the affected prompt and consume them only after a validated result records that they were supplied. A lasting analytical decision should remain active until superseded, rather than disappear after one rewrite.

Evidence: [account dispatch](/Users/roman/Desktop/20_Research-Projects/aperture/app/jobs.py:147), [consumption](/Users/roman/Desktop/20_Research-Projects/aperture/app/jobs.py:317), [actual account inputs](/Users/roman/Desktop/20_Research-Projects/aperture/app/engine/account.py:213).

### 5. Reruns can leave contradictory or damaged state — reproduced

If a THREAD rerun produces fewer than four anchored claims, `_thread_kept` returns before `save_moments` supersedes the old claims. The application can record “thin” while all the old claims remain live. Conversely, READ commits removal of existing hits before asking the model: a provider failure loses the previous coding and can remove theme-code links.

Build new results as a separate attempt. Validate them and atomically activate the new version, including an explicitly empty result when a completed reassessment finds no support. Keep the previous version as history; retain it as current on a failed attempt.

Evidence: [early return](/Users/roman/Desktop/20_Research-Projects/aperture/app/engine/synth.py:351), [replacement](/Users/roman/Desktop/20_Research-Projects/aperture/app/store.py:390), [READ](/Users/roman/Desktop/20_Research-Projects/aperture/app/engine/read.py:131), [destructive clearing](/Users/roman/Desktop/20_Research-Projects/aperture/app/store.py:217).

### 6. Missing examination history becomes “looked for and too thin” — reproduced

The account builder and theme page treat anything except an explicit `skipped` outcome as examined. That includes a newly added unread document and an older document never revisited for a newly developed theme. This is not merely a migration edge case.

Missing history must mean **not assessed**, with the theme and document versions attached. “Some relevant evidence,” “no supporting evidence located,” “contradictory evidence,” and “not assessed” need separate states. A sparse finding is not an absence.

Evidence: [account absence context](/Users/roman/Desktop/20_Research-Projects/aperture/app/engine/account.py:161), [page behavior](/Users/roman/Desktop/20_Research-Projects/aperture/app/context.py:540).

### 7. Cached accounts and upstream summaries miss dependencies

The account fingerprint contains the theme’s name/gist and its claim IDs. It omits corpus membership, examination outcomes, focus, support qualifications, shared interpretations from other themes, model configuration, and prompt version. The diagnostic probes confirm that adding a document, changing focus, or changing a claim’s support qualification leaves the fingerprint identical.

Removal currently supersedes all theme accounts, so removal takes a different path; the fingerprint defect is especially visible on additions and other changed inputs.

Update propagation is also inconsistent. Thread feedback rewrites a thread but leaves the material summary and project summaries unchanged. Theme feedback does not update PROJECT. The stale-material refresh route runs DOC → PROJECT, omitting ACCOUNT, so PROJECT can read old accounts referencing superseded claims. Rendering removes unresolved citations while leaving the old prose.

Use an explicit dependency graph or equivalent version keys for each analytical artifact. An affected upstream artifact should become stale immediately, with a targeted rebuild. The researcher should see what changed and why a refresh is needed.

Evidence: [fingerprint](/Users/roman/Desktop/20_Research-Projects/aperture/app/engine/account.py:83), [feedback planning](/Users/roman/Desktop/20_Research-Projects/aperture/app/rerun.py:83), [refresh](/Users/roman/Desktop/20_Research-Projects/aperture/app/verbs.py:177), [citation removal](/Users/roman/Desktop/20_Research-Projects/aperture/app/context.py:86).

### 8. “Check this” can omit the answer already in the document — reproduced

The diagnostic document says “We joined a union.” Once that sentence supports an existing claim, asking “Did they join a union?” sends only other, uncited sentences to CHECK. The action can return “not found” without examining the answer.

Separate **verify this claim**, **search for this question**, and **inspect material not yet used**. Verify a claim against its actual evidence and necessary context. Search all relevant source passages regardless of prior citation. Keep residual search as a separately named operation. Quotes that merely bear on a question should also be distinguished from quotes supporting or contradicting the proposition.

Evidence: [CHECK scope](/Users/roman/Desktop/20_Research-Projects/aperture/app/engine/check.py:25), [uncited filter](/Users/roman/Desktop/20_Research-Projects/aperture/app/store.py:491).

### 9. Verification is narrower than the product’s apparent evidential assurance

The anchor matcher establishes that words can be located, not that the claim is warranted or belongs under a theme. VERIFY adds a useful entailment judgment, but explicitly excludes theme fit. An empty verifier answer is treated as support and can erase a previous “partly supported” warning; the probe reproduced that behavior.

Partly supported claims remain in later synthesis inputs without their qualification. THREAD summaries are saved before verification removes claims and are not regenerated afterward. ACCOUNT and PROJECT have citation-existence checks, but no equivalent semantic check. Removing an invalid citation does not repair the unsupported statement left behind.

Persist explicit `unchecked`, `supported`, `partly`, `contradicted`, and `needs_context` states. Require a valid verdict for every requested item, retry only missing judgments, propagate qualifications, and separately evaluate theme fit. Use factual checking for descriptive claims; retain researcher-labeled interpretation with a rationale rather than forcing every qualitative inference into sentence-level entailment.

Evidence: [verifier](/Users/roman/Desktop/20_Research-Projects/aperture/app/engine/verify.py:52), [verifier prompt](/Users/roman/Desktop/20_Research-Projects/aperture/app/prompts/verify.md:1), [thread storage](/Users/roman/Desktop/20_Research-Projects/aperture/app/engine/synth.py:357), [summary verifier](/Users/roman/Desktop/20_Research-Projects/aperture/app/engine/verify_summary.py:58).

### 10. Project memory is the last document’s questions

Each completed DOC overwrites `project.brief`. DOC does not receive the previous questions or a full project evidence packet, despite being asked to consider what the corpus has left open. With parallel document synthesis, the last successful writer determines which questions survive. ANGLES for a batch runs before any of that batch’s DOC outputs, so within-batch questions do not inform later files in that batch.

Store questions on their originating documents with IDs and provenance. Reconcile the project’s open questions once per batch, retaining, answering, or superseding individual questions. This makes project memory cumulative and removes completion-order dependence.

Evidence: [question overwrite](/Users/roman/Desktop/20_Research-Projects/aperture/app/engine/synth.py:515), [brief storage](/Users/roman/Desktop/20_Research-Projects/aperture/app/store.py:343), [ANGLES inputs](/Users/roman/Desktop/20_Research-Projects/aperture/app/engine/angles.py:165).

### 11. Candidate lifecycle improves restraint but remains an unreliable research judgment

The code creates new themes as candidates and generally gates them on matching codes. However:

- A candidate with no accepted codes passes `_marked_here`, so it can be followed in every document. Reproduced.
- Promotion counts live claims in two **materials**, not independently reviewed instances of a concept in two cases. These claims are themselves generated by theme-directed THREAD calls. During parallel synthesis, another document’s live claims can still await verification. Promotion is not proof of independent confirmation.
- A one-material project normally has only candidates; candidates receive no ACCOUNT. PROJECT then receives prose material summaries without the candidate claim IDs its instructions require. Reproduced.
- The four-claim minimum applies before semantic verification. One to three sound observations disappear as a group; a line reduced below four by verification can remain. Quantity is neither a consistent quality rule nor a method-neutral one.
- Stability counts unchanged THEMES **passes**, including reruns of the same document, but the page labels this “stable for N materials.” Code-membership-only changes are not consistently represented in theme history or stale-document detection; promotion happens during DOC and is outside the THEMES change comparison.

The numerical theme ceiling (`min(12, 4 + number of materials)`) and four-new-candidate allowance are product heuristics, not methodological warrants. They can pressure merging or omission for reasons unrelated to interpretive importance.

Keep candidates, but represent support as evidence for researcher review. Preserve rare observations without requiring promotion. Give single-case work a full evidence path into synthesis. Keep workflow stability separate from methodological saturation.

Evidence: [gate](/Users/roman/Desktop/20_Research-Projects/aperture/app/engine/synth.py:264), [promotion](/Users/roman/Desktop/20_Research-Projects/aperture/app/store.py:292), [stability](/Users/roman/Desktop/20_Research-Projects/aperture/app/engine/themes.py:258), [display](/Users/roman/Desktop/20_Research-Projects/aperture/app/templates/theme.html:10), [theme change comparison](/Users/roman/Desktop/20_Research-Projects/aperture/app/jobs.py:92).

### 12. File-level state is not sufficient case-level state

The application treats each uploaded file as one material; a CSV of many respondents remains one material. Two files from one participant can count as two materials, while hundreds of respondents in one CSV count as one. Those are valid file counts but cannot ground claims about recurrence across independent cases.

Introduce researcher-defined cases and links among sources, participants, interviews, time points, and survey responses. Keep file identity and case identity distinct. A long transcript, a one-paragraph field note, and a short survey answer should not inherit identical evidence-density requirements.

Evidence: [data model](/Users/roman/Desktop/20_Research-Projects/aperture/app/db.py:43), [CSV intake](/Users/roman/Desktop/20_Research-Projects/aperture/app/intake.py:1).

### 13. Compression needs to preserve exceptions, not only distribute examples

ACCOUNT samples up to 150 claims evenly by position within each carrying material. It does not deliberately preserve rare mechanisms, negative cases, context, or partial-support warnings. Its opening instructions still claim it sees every claim. Its shared-passages block is not included in the 150-item cap, so total prompt size remains unbounded. Beyond 150 carrying materials, some receive a zero-item allocation and `_spread` divides by zero; reproduced at 151.

Use evidence packets that explicitly retain representative support, strongest counterexamples, alternative interpretations, uncertainty, and links to the complete source set. Allocate a real total token budget across all fields. Retrieve additional context when a cross-case claim needs it. Do not imply full coverage from a sample.

Evidence: [sampling](/Users/roman/Desktop/20_Research-Projects/aperture/app/engine/account.py:111), [shared context](/Users/roman/Desktop/20_Research-Projects/aperture/app/engine/account.py:143), [account prompt](/Users/roman/Desktop/20_Research-Projects/aperture/app/prompts/account.md:1).

## Fit with qualitative research

There is no single “typical qualitative analysis” to encode. The current [design record](/Users/roman/Desktop/20_Research-Projects/aperture/docs/PLAN.md:311) explicitly describes template analysis with a constant-comparison loop. Reusing codes and comparing later cases with a developing framework can be legitimate. Induction does not require forgetting earlier cases. The problem is making that procedure the implicit universal method while also promising that each document is read on its own terms.

For reflexive thematic analysis, themes are developed through interpretation; they are not automatically certified by appearing in two documents. Codes can evolve, themes are analytical outputs, and reflexivity includes the researcher’s standpoint and decisions. A theme’s organizing concept is more than an inclusion rule. These distinctions support making the method explicit rather than treating a codebook workflow as interchangeable with reflexive TA. [Braun and Clarke’s methodological FAQ](https://cdn.auckland.ac.nz/assets/psych/about/our-research/documents/Answers%20to%20frequently%20asked%20questions%20about%20thematic%20analysis%20April%202019.pdf).

For framework analysis, a case-by-code matrix and iterative refinement of a working framework are a good fit. The matrix retains within-case and across-case comparison; qualitative judgment remains necessary. This is a useful model for Aperture’s comparison view, provided its cells show the status and context of evidence rather than reducing interpretation to a claim count. [Gale et al., Framework Method](https://doi.org/10.1186/1471-2288-13-117).

An unchanged definition is operational stability, not evidence that interpretive possibilities are exhausted. Braun and Clarke explicitly question transferring saturation assumptions into reflexive TA. Show “definition unchanged in these reviewed cases,” if accurate; do not present a counter as methodological saturation. [To saturate or not to saturate?](https://www.tandfonline.com/doi/abs/10.1080/2159676X.2019.1704846?journalCode=rqrs21).

My recommendation is an **exploratory document reading by default**, with an explicit option to apply a researcher-approved framework. Let researchers combine the two deliberately. Avoid naming the software’s output “grounded theory” or “reflexive thematic analysis” merely because it groups codes and writes themes.

## Recommended target design

### Document state: a reading that survives changes to themes

Every document should retain its immutable extracted text and source mapping, a source/version identifier, its relation to cases, verified or uncertain structure, a case memo, local observations and codes linked to full evidence spans, contradictory or exceptional observations, open questions, researcher notes, and the coverage of each analytical pass.

Separate **source observations**, **interpretations**, and **researcher decisions**. Store who or what produced each item and which prompt/model/source version produced it. A concise quote can be the display anchor; it should not be the only stored context. Preserve interview questions and complete turns where needed to interpret an answer.

First-pass exploratory coding should receive the source, necessary structure, researcher-authored question and methodological choices. It should not automatically receive generated project themes or conclusions. Reconcile local codes with the project vocabulary in a later, explicit operation. This reduces first-file vocabulary lock-in while still allowing cumulative comparison.

The document memo must stand on the document’s own evidence, including important material not yet assigned to a project theme. A new theme should not require regenerating the case memo.

### Project state: a versioned argument across cases

Keep the research question and methodological choices; case/source registry; approved vocabulary and code mappings; provisional and approved theme versions; central organizing concepts and supporting arguments; counterexamples; a case-by-theme evidence matrix; a cumulative question register; researcher decisions with rationales; and the synthesis’s dependency versions.

A matrix cell should say what is actually known: unassessed, partly assessed, supporting evidence, contradictory evidence, mixed evidence, or no support located within a stated search. Record coverage and the versions assessed. “Not applicable” is a separate contextual judgment, not a synonym for no matching code.

Researcher approval should determine when a proposed conceptual change becomes the active theme definition. Routine new evidence can be attached automatically without asking for approval on every action. The interface can offer a concise batch review: what changed, evidence for it, contrary cases, and affected earlier readings.

### Model workflow: source reading, then focused comparison

| Operation | Minimal useful input | Durable output |
|---|---|---|
| Describe source | Mechanical extraction and enough source context | Structure and uncertainties |
| Read document | Full source when bounded; otherwise context-preserving chunks with coverage tracking; researcher’s question | Local evidence items, provisional interpretations, case memo, questions |
| Inspect omissions | Residual/ambiguous passages and what the first pass covered | Additional evidence or explicit unresolved coverage |
| Reconcile vocabulary | New local codes and excerpts; relevant existing definitions/examples | Mapping proposals, distinctions, splits, unresolved differences |
| Develop/review themes | Evidence from relevant cases, case memos, contrary examples, researcher choices | Proposed themes/changes with provenance and rationale |
| Revisit earlier cases | Specific changed concept plus retrieved evidence/context; expand to full source when needed | Versioned case–theme assessment |
| Write synthesis | Current, qualified evidence packets and approved analytical structure | Claims with direct resolvable support and explicit scope |

The ordinary unit of expensive work becomes a document reading or a defined analytical question. It should not be every possible theme–document combination. Retain full-text revisits when the question warrants them and scheduled comprehensive review points chosen by the researcher.

### Update rules

| Researcher action | Necessary recomputation |
|---|---|
| Add a document | Analyze that document; reconcile its evidence; update affected themes/accounts; update project synthesis |
| Correct a claim | Reassess the claim with context; invalidate only summaries/accounts that depend on it |
| Rename a theme without changing meaning | Update display references; no source reread |
| Change theme meaning | New theme version; mark affected case assessments stale; targeted review of earlier evidence with source expansion as needed |
| Correct a theme account | Rewrite that account using the correction; update dependent project synthesis |
| Change research focus | New focus version; show which readings used the old focus and plan the desired reassessment |
| Freeze a framework | Record the approved version; apply it in an explicitly deductive pass, retaining exceptions and provisional new concepts |

A persistent chat per document would not solve these problems. It would tend to accumulate obsolete assumptions and repeatedly transmit history. Versioned analytical records with deliberately assembled context are the better form of memory.

## Implementation order and evaluation

1. **Repair analytical trust:** wire feedback; make replacement atomic; preserve explicit unassessed states; fix CHECK scope; propagate qualifications; repair missing dependencies and the candidate-only evidence path. Address the 151-material failure while changing account budgeting.
2. **Measure actual calls:** record call/attempt IDs, input versions, model and effort, token breakdown where supplied, timing, completion/validation outcome, and relevant artifact IDs. Show what each call was intended to resolve. Persist sensitive prompt snapshots only in the project’s protected audit store, not infrastructure logs.
3. **Introduce durable local evidence and case memos:** retain existing exports and interfaces while separating document evidence from project themes. Add coverage accounting and researcher-defined case identity.
4. **Compare alternative workflows:** current default; current code-hit gate; local-first evidence plus targeted thematic retrieval; and the same targeted workflow with an omission/contradiction pass. Keep source corpus and model fixed initially so model choice does not confound architecture.
5. **Then tune models, reasoning, caching, and batching:** use a small/non-reasoning path for mechanical structure when adequate; concentrate stronger reasoning on difficult interpretations and cross-case synthesis. Do not infer quality from longer reasoning traces or more generated claims.

Evaluation should include repeated runs and shuffled document/upload order; long interviews; short answers; multiple files per case; one CSV with many cases; a concept introduced late; and decisive negative cases. Preserve full raw evidence for review. Existing evaluation uses model judges; qualified human researchers should assess the final methodological fit.

Measure unsupported factual additions, loss of important passages, missing counterexamples, inappropriate theme assignments, quality of within-case interpretation, response to researcher correction, and the ability to explain a theme’s evolution. Measure actual input/output/cache usage, wall time, and researcher review time alongside those judgments. Do not use more codes, greater theme prevalence, or agreement alone as a proxy for qualitative quality.

The first decision to test is whether a reusable document evidence layer can preserve the worthwhile discoveries from theme-directed rereading while avoiding most repeated full-document calls. The current code and benchmarks make that the strongest next experiment; they do not yet establish a particular savings percentage or a best model.
