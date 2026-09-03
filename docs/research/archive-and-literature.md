# 1. WHAT THIS AREA CONTAINS

| File | Contents and status |
|---|---|
| `DEPLOY.md` | Current Coolify deployment guide for the FastAPI/static-web application: provider credentials, model selection, PIN roles, SQLite persistence, health checks, and demo seeding. Operationally relevant, although its “v4 static frontend” may change under the replacement planned in the current design canon. [DEPLOY.md §Deploying MASSHINE; README.md §Layout] |
| `README.md` | Current repository front door. It defines the present workbench at a high level and points to the newer design canon, engine contract, interaction model, trial plans, and buildout documents. It supersedes the archived files as the implementation index. [README.md §The design canon] |
| `_archive/MASSHINE_v0_SPEC.md` | Historical walking-skeleton specification: synthetic evaluation, JSON/git storage, structure-first segmentation, parallel personas, checkpoints, and gates G1–G4. Superseded first by its own extension map and now by the design canon and P10.2 engine contract named in `README.md`; still useful for the reasons behind early constraints. [_archive/MASSHINE_v0_SPEC.md §§1–2, 9; README.md §The design canon] |
| `_archive/REWORK_PLAN.md` | Audit and repair plan for an earlier static stakeholder preview. It records concrete quote-verification, scope, divergence, accessibility, and presentation defects. Superseded as a build plan by the current `design/BUILDOUT.md`; still highly relevant as a failure record. [_archive/REWORK_PLAN.md §Part 1; README.md §The design canon] |
| `_archive/compass_artifact_wf-02b259de-9e36-5e7e-8879-a35e7c5d9a56_text_markdown.md` | Evidence review separating engineerable chatbot failures from in-principle objections, with requirements R1–R10 and an evaluation strategy. It is an archival research basis, not the current engine contract; its model-specific figures are explicitly perishable. [_archive/compass_artifact_wf-02b259de-9e36-5e7e-8879-a35e7c5d9a56_text_markdown.md §§TL;DR, Caveats] |
| `_archive/research.md` | Earlier architecture study mapping six-phase reflexive thematic analysis onto LLM stages and surveying multi-agent, scaling, provenance, saturation, and evaluation evidence. Superseded as an implementation specification by the later v0 spec and current design canon, but still relevant for methodological rationale and external evidence. [_archive/research.md §§TL;DR, Recommendations; README.md §The design canon] |
| `packs/README.md` | Design and authoring notes for study-specific domain packs and standpoint rosters. It calls the pre-built migration pack the active path, but the root README now calls all panel-mode packs legacy and scheduled for removal; treat it as relevant only to the deprecated panel path. [packs/README.md §§Authoring flow, Status; README.md §Layout] |
| `packs/_brief_template.md` | Parameterized deep-research brief for producing a grounded standpoint reference in a new domain. Explicitly dormant and not wired into the engine; retained as generalization scaffolding. [packs/_brief_template.md heading and PURPOSE; packs/README.md §Status] |
| `packs/migration_oral_history/reference.md` | Scholarship-backed build sheet for five migration/oral-history standpoint coders, their anti-caricature guards, and a friction matrix. It remains the source for the legacy migration pack, but the panel route that consumes it is scheduled for deprecation. [packs/migration_oral_history/reference.md §How to use this document; README.md §Layout] |

# 2. ESTABLISHED FINDINGS

1. The old stakeholder preview failed its own grounding rule. Of 91 quoted passages, 18 failed raw string matching; after normalizing quotation marks and `[PH]` markers, 13 remained genuine paraphrases or splices. One example joined passages approximately 2,000 characters apart and reversed their chronology. [_archive/REWORK_PLAN.md §F1]

2. The old preview also collapsed disagreement despite claiming to preserve it: five of eight conciliator examples merged semantic and latent readings “to keep the codebook lean.” The audit judged those readings substantively distinct and recommended a demonstrative distribution of two creates, three minorities, two genuine near-duplicate merges, and one rejected merge. [_archive/REWORK_PLAN.md §F2; §Task 3]

3. The preview represented roughly 70% of the v0 specification, but its strongest elements were the decision/evidence tabs, pressure tests, grounded Brozinskas illustration, audit limits, and markdown export. Its evidentiary examples, v0 scope claims, and architecture story were not ready for researcher review. [_archive/REWORK_PLAN.md §§What is strong, Verdict]

4. A prominent negative study tested Microsoft Copilot on five open datasets using one zero-shot prompt for a complete thematic analysis. It reported 58% fabricated quotes (SD 45%), versus 79% correct quotes for humans (SD 27%), and drew themes and quotations mainly from the first two or three pages. A subsequent prompt analysis counted 21 analytic tasks requested sequentially without persistent state. This establishes failure of that protocol, not of stateful, verified LLM systems generally. [_archive/compass_artifact_wf-02b259de-9e36-5e7e-8879-a35e7c5d9a56_text_markdown.md §§Key Findings 2, Caveats]

5. Long-context coverage failure has a known mechanism: relevant information is retrieved best near the beginning or end of a context and worse in the middle. The cited “context rot” study found degradation across all 18 frontier models tested. Segment-level passes and corpus retrieval were therefore preferred to putting an entire corpus into one prompt. [_archive/compass_artifact_wf-02b259de-9e36-5e7e-8879-a35e7c5d9a56_text_markdown.md §Key Finding 3]

6. Verbatim-quote fabrication is mechanically testable. A quote can be required to resolve to a source character span before it enters an output. One cited file-assisted study sampled 64 quotations across four sessions covering 16 interviews and found all 64 traceable, although the record flags the single-researcher comparison and possible contamination as caveats. [_archive/compass_artifact_wf-02b259de-9e36-5e7e-8879-a35e7c5d9a56_text_markdown.md §§Key Finding 4, Caveats]

7. Persistent analytic state is a harness responsibility. Stable code, segment, memo, and theme objects can be supplied through a database, external memory, or explicit state machine; chatbot statelessness need not become analytic statelessness. [_archive/compass_artifact_wf-02b259de-9e36-5e7e-8879-a35e7c5d9a56_text_markdown.md §Key Finding 5]

8. LLM performance differs sharply between deductive and inductive work. Reported deductive agreement spans κ = 0.46–1.00. One study found GPT-4 chain-of-thought increased average per-code agreement from 0.59 to 0.68 and full-codebook agreement from 0.46 to 0.60; GPT-3.5’s mean κ was 0.34. Another reached κ ≥ 0.70 on 25 of 34 constructs and up to 0.95. In contrast, one inductive evaluation classified only 31% of generated codes as matching human codes, 26% as reasonable alternatives, and 42% as unreasonable. [_archive/compass_artifact_wf-02b259de-9e36-5e7e-8879-a35e7c5d9a56_text_markdown.md §Key Finding 6]

9. Blind experts in one six-phase study preferred LLM-generated codes 61% of the time, while also finding unnecessary fragmentation, missed latent interpretations, unclear theme boundaries, and broad or generic themes. Useful first-pass coding therefore did not demonstrate autonomous interpretive adequacy. [_archive/research.md §Key Finding 1]

10. Multi-agent specialization improves diversity and sometimes coverage, but not reliably accuracy. A controlled study covered more than 77,000 coding decisions across six open-source models and 18 configurations; persona and temperature changes altered consensus dynamics with minimal accuracy gains, and heterogeneous personas delayed consensus in four of six models. [_archive/research.md §Key Finding 4]

11. Consensus is not the intended optimization target. Reflexive thematic analysis treats positioned interpretation as productive, while majority vote and self-consistency suppress minority readings. Perspectivist work provides a compatible alternative: retain disaggregated labels and rationales and analyze disagreement as signal. [_archive/research.md §§TL;DR, Agentic / Orchestration Patterns; _archive/compass_artifact_wf-02b259de-9e36-5e7e-8879-a35e7c5d9a56_text_markdown.md §Key Finding 9]

12. “Theme as bucket” is a repeated failure. Clustering codes produces categories, whereas a reflexive-TA theme is an argued pattern of shared meaning organized around a central concept. Theme construction requires an explicit central-concept statement, testing against the corpus, and human interpretation. [_archive/research.md §§Key Finding 2, Phase 3, Caveats]

13. Saturation measures are signals, not stopping rules. The ITS unique/total-code ratio and slowing code-creation rate are computable, but independently processed interviews continue producing new codes, so codebook growth may remain quasi-linear. [_archive/research.md §§Key Finding 5, Saturation detection]

14. Provenance is the strongest defensible product claim: every theme should resolve through definitions and codes to excerpts and exact source spans. It supports both auditability and comparison with human work while avoiding unsupported claims that the model “understood” participants’ experience. [_archive/research.md §Key Finding 6; _archive/compass_artifact_wf-02b259de-9e36-5e7e-8879-a35e7c5d9a56_text_markdown.md §Evaluation design]

15. No canonical, public, community-standard benchmark for LLM qualitative coding was identified. Available benchmarks often lack released data or a same-corpus human–human baseline, making isolated LLM–human agreement figures difficult to interpret. [_archive/compass_artifact_wf-02b259de-9e36-5e7e-8879-a35e7c5d9a56_text_markdown.md §§Evaluation design, Open questions]

16. The migration standpoint design distinguishes two kinds of useful disagreement: interpretive friction, where coders select the same material but assign different meanings, and attentional friction, where they disagree about what is worth coding. The latter is considered the higher-value signal because it identifies interpretively dense material. [packs/migration_oral_history/reference.md §Friction Matrix, “Reading the matrix”]

17. A standpoint must direct attention without dictating findings. Each profile consequently includes sensitizing concepts, questions, legitimate low-yield areas, internal heterogeneity, and a worked caricature guard. [packs/_brief_template.md §PURPOSE and deliverables; packs/migration_oral_history/reference.md §§How to use this document, Theoretical foundation]

18. Generalizing standpoint packs was deliberately left dormant. Brief generation is manual/external, the resulting scholarship must be human-reviewed, and prompt distillation is manual; only the pre-built migration pack was active in the pack-era design. [packs/README.md §§Authoring flow, Status]

19. The present implementation has already departed from the v0 file-store decision: current state is held in a registry SQLite database plus one SQLite database per project, with no Postgres or Redis. Persistent deployment requires mounting `/data`; otherwise redeployment erases all projects. [DEPLOY.md §§Deploying MASSHINE, Persistent storage; _archive/MASSHINE_v0_SPEC.md §Locked decision 2]

20. None of the supplied files records the three simulated-researcher rounds, their participant behavior, or round-by-round defect identifiers. The current README merely points to `design/SIM-PLAN.md` and `design/INSIGHT-LOOP.md`; those records were not among the files indexed here. [README.md §The design canon]

# 3. DEFECTS AND FAILURE MODES

No `D0`, `D9`, `D14`, or other `D…` identifiers occur in the supplied files. The recorded identifiers are `F1–F6` for the preview audit and `1–10` for the evidence review’s failure register.

## Preview defects

| ID | Defect | Fix or proposal |
|---|---|---|
| F1 | Thirteen genuine paraphrased, spliced, or chronology-altering “quotes” survived normalization. | Add an automated G2 string-match gate; permit only documented normalization; require one continuous span per speaker turn; split multi-turn dialogue into independently verifiable lines. [_archive/REWORK_PLAN.md §§F1, Quote-matching convention, Tasks 1–2] |
| F2 | Five of eight examples collapsed distinct semantic and latent readings; personas were also incorrectly presented as semantic-versus-latent roles. | Compare each incoming code against the whole codebook; merge only genuine duplicates; preserve distinct and minority readings; show create, merge, minority, and rejected-merge outcomes. Each persona may emit semantic and latent codes. [_archive/REWORK_PLAN.md §§F2, Task 3] |
| F3 | The preview attributed a critic, definition/quote-bank stage, and narrative report drafting to v0 although all were post-v0. | Relabel the single theme pass, human theme checkpoint, gate-table report, and provenance audit accurately; state that critic separation, definition objects, and narrative drafting are extensions. [_archive/REWORK_PLAN.md §§F3, Task 4] |
| F4 | The preview hid disagreements between research recommendations and v0 decisions, especially embeddings versus LLM merging and SQLite versus JSON/git. | Add explicit “Literature disagrees” material and a trigger-based extension map; show synthetic, subset, and corpus-scale stages separately. [_archive/REWORK_PLAN.md §§F4, Tasks 5 and 7] |
| F5 | No full pipeline, checkpoint feed-forward, reconciliation memo, cost ledger, scale story, or disclosure that real-transcript examples were hand-authored illustrations. | Render all 12 nodes, add HumanDecision and advisory memo examples, expose the ledger and extension map, and label the illustrations honestly. [_archive/REWORK_PLAN.md §§F5, Tasks 5–6, 8] |
| F6 | Count drift, misspellings, improper κ shorthand, misleading comparison-table entries, non-clickable copy, incorrect editability, unsafe rendering, weak accessibility, and `file://` failure. | Apply the enumerated factual corrections, inline JSON with a regeneration tool, escape rendered values, and implement keyboard/ARIA behavior. [_archive/REWORK_PLAN.md §§F6, Tasks 8–10] |

## Evidence-review failure register

| ID | Failure | Fix, mitigation, or boundary |
|---|---|---|
| 1 | Results concentrate on the first two or three pages because of long-context position bias. | Code addressed segments separately; retrieve over the full corpus; measure positional coverage rather than relying on one long prompt. [_archive/compass_artifact_wf-…_text_markdown.md §§Failure-mode register, R2–R3] |
| 2 | Fabricated or unsupported quotations. | Exact source-span verification before emission; acceptance criterion: zero unverifiable quotations. [_archive/compass_artifact_wf-…_text_markdown.md §§Failure-mode register, R4] |
| 3 | No persistent codebook or stable analytic objects. | External structured state with retrievable, diffable codes, definitions, exemplars, memos, and source pointers. [_archive/compass_artifact_wf-…_text_markdown.md §§Failure-mode register, R1] |
| 4 | A single prompt cannot reliably execute 21 sequential analytic tasks. | Decompose work into explicit stages and state transitions rather than asking for an entire analysis in one turn. [_archive/compass_artifact_wf-…_text_markdown.md §Failure-mode register] |
| 5 | Outputs vary across unchanged runs. | Use temperature zero where reproducibility is required, fixed seeds where available, checkpoints, and manifests that identify residual variance. This is only partly engineerable. [_archive/compass_artifact_wf-…_text_markdown.md §§Failure-mode register, R9] |
| 6 | Inductive outputs remain shallow, generic, or weak on latent meaning. | Constrain claims, retain human-gated theme construction, test interpretive depth blindly, and fall back to first-pass coding if experts reject latent quality. No established technical fix exists. [_archive/compass_artifact_wf-…_text_markdown.md §§Failure-mode register, Open questions; _archive/research.md §Recommendations] |
| 7 | An LLM has no embodied positionality or reflexive meaning-making capacity. | Capture researcher positionality and decisions and declare a relational/dialogic epistemology if appropriate. This scaffolds human reflexivity but does not answer the orthodox in-principle objection. [_archive/compass_artifact_wf-…_text_markdown.md §§Failure-mode register, Unanswerable residue] |
| 8 | Model internals are opaque. | Make the process inspectable—prompts, outputs, revisions, evidence, models, and parameters—while acknowledging that process auditability does not make model internals interpretable. [_archive/compass_artifact_wf-…_text_markdown.md §§Failure-mode register, R8] |
| 9 | Themes lack participant-spread evidence. | Preserve participant metadata and compute which participants support each theme. [_archive/compass_artifact_wf-…_text_markdown.md §Failure-mode register] |
| 10 | Compute, labor-displacement, and social-justice harms remain. | No architectural fix is claimed; these are normative and explicitly out of scope for the harness architecture. [_archive/compass_artifact_wf-…_text_markdown.md §Failure-mode register] |

Additional named failure modes are:

- **Theme as bucket:** clustering substitutes topical grouping for an argued central concept; add a theorist construction step, corpus-level review, and human authorship. [_archive/research.md §§Key Finding 2, Phase 3]
- **Consensus collapse:** majority vote, self-consistency, or an over-aggressive conciliator deletes productive minority readings; retain disaggregated codes and rationales. [_archive/research.md §Agentic / Orchestration Patterns; _archive/MASSHINE_v0_SPEC.md §Locked decision 5]
- **Judge bias:** LLM judges show approximately 10% position bias and favor their own family—reported as a 10% higher win rate for GPT-4 and 25% for Claude-v1—plus verbosity bias. Randomize ordering, normalize length, and use a different model family. [_archive/research.md §Agentic / Orchestration Patterns]
- **Caricature:** a theoretical persona stamps stock vocabulary onto evidence. Require questions rather than conclusions, explicit low-yield responses, internal heterogeneity, and shallow-versus-sophisticated examples. [packs/_brief_template.md §PURPOSE; packs/migration_oral_history/reference.md §How to use this document]
- **Unprotected deployment state:** without `/data` storage, redeployment destroys all projects; without an editor PIN, a public instance has no access control; LLM JSONL logs are not persisted unless their export path is also mounted. [DEPLOY.md §§Environment variables, Persistent storage]

# 4. DESIGN DECISIONS AND THEIR REASONS

1. **Build an instrument for researcher augmentation, not autonomous interpretation.** Existing systems retain humans as final interpretive authorities, and reflexivity cannot be delegated to a model. Autonomous analysis and autonomous final writing were rejected. [_archive/research.md §§TL;DR, Phase 6, Caveats]

2. **Preserve divergence rather than vote it away.** Independent coders expose positioned interpretations; minority and rejected-merge codes remain visible. Majority vote and “lean codebook” merging were rejected because they erase the phenomenon the panel was created to study. [_archive/MASSHINE_v0_SPEC.md §Locked decision 5; packs/migration_oral_history/reference.md §How to use this document]

3. **Treat a lens as an attention system, not a conclusion generator.** Sensitizing concepts suggest where to look and what to ask; definitive codebooks that prescribe what must be found were rejected as caricature-producing. [packs/migration_oral_history/reference.md §Theoretical foundation; packs/_brief_template.md §PURPOSE]

4. **Use a low-loading calibration anchor.** The pragmatist-interactionist coder stays close to the neutral baseline, allowing the distance to other coders to indicate how much a lens adds or distorts. Maximizing every persona’s distinctiveness was deliberately rejected. [packs/migration_oral_history/reference.md §Standpoint 5]

5. **Structure before segmentation.** Each transcript first receives a descriptive `StructureDoc` with exact tiling boundaries and short gists; local calls then receive the map, position, and segment. Floating excerpts were rejected because they can lose chronology and narrative position. [_archive/MASSHINE_v0_SPEC.md §§Locked decision 10, Pipeline]

6. **Keep structural maps descriptive.** Interpretive or candidate-code language in a `StructureDoc` was prohibited because early framing would propagate into every later decision. A lint and exact-tiling audit were specified. [_archive/MASSHINE_v0_SPEC.md §§Locked decision 10, Audit]

7. **Make grounding deterministic.** Every quotation must match a source span exactly, apart from declared normalization. Trusting generated quotations or citations was rejected. [_archive/MASSHINE_v0_SPEC.md §§Exit gate G2, Audit; _archive/REWORK_PLAN.md §Quote-matching convention]

8. **Make every crossing auditable.** Themes must resolve to codes, excerpts, and character spans; model calls, human edits, and skipped checkpoints must leave records. Final-output-only inspection was rejected. [_archive/MASSHINE_v0_SPEC.md §§Exit gates G3–G4, Locked decisions 7–8]

9. **Use explicit human checkpoints with feed-forward effects.** A codebook edit must affect later theme prompts, and no final theme should exist without a logged human confirmation. Passive human review at the end was rejected. [_archive/MASSHINE_v0_SPEC.md §§Pipeline, Task T5; _archive/compass_artifact_wf-…_text_markdown.md §R6]

10. **Do not headline κ for reflexive thematic analysis.** IRR assumes a correct coding and treats subjectivity as noise. Synthetic recovery measures were labeled `synthetic_only`; agreement remains permissible only in a separately identified codebook/reliability arm and relative to a human–human baseline. [_archive/MASSHINE_v0_SPEC.md §Locked decision 7; _archive/research.md §§Key Finding 3, Evaluation]

11. **Start with a deliberately small synthetic corpus.** The old v0 target was 12 synthetic transcripts, six planted themes, and four exit gates, with ground truth firewalled from all prompts. Real Ellis Island data was explicitly deferred until the skeleton passed. [_archive/MASSHINE_v0_SPEC.md §§Scale, Locked decision 9, Explicitly NOT in v0]

12. **Defer embeddings in v0, but retain them as a scaling fallback.** Natural-language merge decisions were preferred because a human could audit their rationales. The research recommendation—embedding retrieval and map-reduce for 1,343 transcripts—was consciously deferred until the codebook approached the context limit and a digest failed. [_archive/MASSHINE_v0_SPEC.md §§Locked decisions 1 and 4, Extension map; _archive/research.md §§TL;DR, Codebook merging]

13. **The historical JSON/git state decision has been superseded by SQLite.** V0 preferred readable, git-diffable run directories and rejected a database until file counts hurt. The current deployment uses per-project SQLite files, indicating that the persistence requirement eventually outweighed the early minimalism. [_archive/MASSHINE_v0_SPEC.md §Locked decision 2; DEPLOY.md §§Deploying MASSHINE, Persistent storage]

14. **Version prompts and analytic artifacts.** Inline prompts were rejected because the system’s analytic logic must be readable and reviewable independently of code. [_archive/MASSHINE_v0_SPEC.md §Locked decision 3]

15. **Separate bulk coding from stronger synthesis and independent evaluation.** The v0 design assigned distinct coder, strong, and judge models and required the judge to come from a different family; this mitigates cost and self-preference bias. One-model-does-everything was rejected. [_archive/MASSHINE_v0_SPEC.md §Pipeline; _archive/research.md §§LLM-as-judge, Model choice]

16. **Keep reconciliation advisory.** Per-transcript drift checks produce memos but do not block the pipeline; they are surfaced for researcher judgment. Automated drift adjudication was rejected. [_archive/MASSHINE_v0_SPEC.md §§Pipeline, Audit]

17. **Generalization remains outside the active engine.** Producing scholarship is bring-your-own and human-reviewed; automatic brief generation and prompt distillation remain dormant. Baking a research engine into the coding engine was rejected to keep the latter provider-agnostic. [packs/README.md §§Authoring flow, Status]

18. **Current model choice is explicit and recorded.** The server default may be overridden per project or per run using a validated registry; malformed custom registry entries are dropped rather than crashing the application. Hidden or globally hard-coded model selection was rejected. [DEPLOY.md §Selecting a model]

19. **Retain visible residue.** Material that fits no current analytic direction remains present rather than being deleted or forced into a theme. The root README treats this as a system-level guarantee. [README.md opening description]

# 5. OPEN QUESTIONS

1. Where are the actual three simulated-researcher round records, including their observations, measurements, and `D…` defect ledger? The supplied record names simulation planning documents but contains no trial outcomes. [README.md §The design canon]

2. Which decisions from the archived v0 spec survived the lean restart? The current README points to `design/MASSHINE.md`, `P10.2-CONTRACT.md`, `INTERACTION-MODEL.md`, and `BUILDOUT.md`, but those current contracts were not included here. [README.md §The design canon]

3. Were the 13 quotation failures and the other F1–F6 preview defects actually fixed? `_archive/REWORK_PLAN.md` records proposed work with unchecked boxes, not completion evidence. [_archive/REWORK_PLAN.md §Final verification]

4. How should the next version measure interpretive depth or reflexivity? No agreed metric exists for either, although these are the dimensions on which reflexive-TA critics place the greatest weight. [_archive/compass_artifact_wf-…_text_markdown.md §Open questions]

5. Can multi-agent critique improve inductive and latent interpretation enough to justify its cost, or does it merely produce more text and delayed consensus? Existing evidence is mixed and sometimes shows minimal accuracy gains. [_archive/compass_artifact_wf-…_text_markdown.md §Open questions; _archive/research.md §Key Finding 4]

6. What balance should be chosen between determinism and interpretive diversity? Temperature zero improves repeatability but may suppress precisely the variation that perspectivist analysis values. [_archive/compass_artifact_wf-…_text_markdown.md §Open questions]

7. What evaluation corpus will supply released data, at least two human coders, and a human–human baseline? Without one, claims should remain limited to provenance, coverage, and auditability. [_archive/compass_artifact_wf-…_text_markdown.md §§Evaluation design, Open questions]

8. What is the operational scaling trigger in the restarted system? The archived spec proposed a codebook digest before embeddings and batching above roughly 50 transcripts, while the research document argued that 1,343 transcripts require embeddings and map-reduce. No result here resolves that disagreement. [_archive/MASSHINE_v0_SPEC.md §Extension map; _archive/research.md §§TL;DR, Concrete System Architecture]

9. Should stochastic diversity be an exposed researcher control, a fixed methodological setting, or separated into reproducible coding and exploratory perspective runs? The record leaves this undecided. [_archive/compass_artifact_wf-…_text_markdown.md §Open questions]

10. Can the instrument be called reflexive thematic analysis under the intended epistemology? Orthodox Braun-and-Clarke RTA may reject any machine interpretation regardless of engineering; the proposed alternative is an explicit relational-subjectivity or human–LLM-assemblage declaration. Audience acceptance remains unresolved. [_archive/compass_artifact_wf-…_text_markdown.md §The unanswerable residue]

11. Do ATLAS.ti, MAXQDA, or NVivo already guarantee character-offset provenance and complete recode histories? Public documentation did not establish this, preventing a firm competitive claim. [_archive/compass_artifact_wf-…_text_markdown.md §§Key Finding 8, Open questions]

12. Are domain packs still part of the product? `packs/README.md` calls the migration pack active, while the root README calls panel-mode packs legacy and says they leave with deprecated routes in the next release. [packs/README.md §Status; README.md §Layout]

13. Will deployment logs be made durable? `MASSHINE_LLM_LOG=1` writes a useful per-call ledger under `exports/`, but that location is not persisted by the documented `/data` volume unless separately mounted. [DEPLOY.md §§Environment variables, Persistent storage]

14. Terms such as **slot**, **exposure**, **exchange**, and **territories**, named in the indexing request, do not occur in these nine files. Their intended current meanings presumably live in the omitted design/trial record and cannot be reconstructed safely here.

# 6. VOCABULARY

- **Anchor / calibration anchor** — The deliberately low-loading standpoint closest to neutral RTA; distance from it indicates how much another lens adds or distorts. [packs/migration_oral_history/reference.md §Standpoint 5]
- **Attention** — What a theoretical lens directs the coder to notice or question; it must not predetermine the resulting code. [packs/_brief_template.md §PURPOSE]
- **Brief** — A parameterized, study-level request for externally researched scholarship from which a domain reference and standpoint prompts can be produced; currently dormant. [packs/_brief_template.md heading; packs/README.md §Authoring flow]
- **Checkpoint** — An explicit human review gate at which structures, codes, or themes can be accepted or edited, with the decision recorded and fed forward. [_archive/MASSHINE_v0_SPEC.md §§Pipeline, checkpoint.py]
- **Codebook** — Persistent collection of stable code objects and definitions against which incoming codes are considered for creation or merging. [_archive/MASSHINE_v0_SPEC.md §Locked decision 4]
- **Door / evidence door** — The root README’s metaphor for a navigable connection from a paper-surface claim down to its supporting evidence. [README.md opening description]
- **Exchange** — Not used or defined in the supplied files; do not assign it a product meaning without the omitted current interaction record.
- **Exposure** — Not used or defined in the supplied files; do not infer a meaning from ordinary usage.
- **Friction** — Structured disagreement between standpoint coders, either interpretive or attentional, retained as analytic data. [packs/migration_oral_history/reference.md §Friction Matrix]
- **HumanDecision** — Recorded researcher action at a checkpoint whose edit or note becomes input to later stages. [_archive/MASSHINE_v0_SPEC.md §§Repo layout, Task T5]
- **AutoDecision** — Audit record written when `--auto` skips a human checkpoint. [_archive/MASSHINE_v0_SPEC.md §Locked decision 8]
- **Lens / standpoint** — A declared epistemic orientation expressed as sensitizing concepts, analytic questions, blind spots, and guards; it determines where to look, not what must be found. [packs/migration_oral_history/reference.md §§How to use this document, Theoretical foundation]
- **Ledger** — An accounting/audit record. In v0 it meant tokens, calls, wall time, estimated cost, human checkpoint minutes, and per-persona unique-code yield; deployment can also log per-call usage and cache-token data. [_archive/MASSHINE_v0_SPEC.md §Audit; DEPLOY.md §§Environment variables, Alternative provider]
- **Minority** — A divergent, unmerged code preserved and flagged rather than deleted or defeated by voting. [_archive/MASSHINE_v0_SPEC.md §Locked decision 5]
- **Panel** — Multiple standpoint coders reading the same material independently and blindly so their divergences can be analyzed. [packs/migration_oral_history/reference.md §How to use this document]
- **Provenance** — The resolvable trail from a claim or theme through codes and excerpts to exact source character spans, plus the calls and decisions that produced it. [_archive/MASSHINE_v0_SPEC.md §§Exit gates, Audit]
- **Reconcile** — Advisory per-transcript comparison between coding distribution and the descriptive structure map; it emits drift memos but never blocks. [_archive/MASSHINE_v0_SPEC.md §§Repo layout, Pipeline]
- **Register** — Used in two senses: the evidence document’s numbered failure catalogue, and the domain brief’s requested linguistic style or level. [_archive/compass_artifact_wf-…_text_markdown.md §Failure-mode register; packs/_brief_template.md §DOMAIN]
- **Residue** — Evidence or material that fits no current interpretation and is deliberately kept visible rather than discarded or forced into a theme. [README.md opening description]
- **Sensitizing concept** — An initial direction for looking and questioning, not a fixed benchmark or prescribed category. [packs/migration_oral_history/reference.md §Theoretical foundation]
- **Slot** — Not used or defined in the supplied files; its current interaction-model meaning remains unavailable.
- **StructureDoc** — A pre-coding map of transcript sections with exact, gap-free character boundaries and strictly descriptive gists. [_archive/MASSHINE_v0_SPEC.md §§Locked decision 10, Pipeline]
- **Theme** — An argued pattern of shared meaning organized around a central concept, not a topical cluster or bucket. [_archive/research.md §Key Finding 2]
- **Territories** — Not used or defined in the supplied files; it should not be treated as established vocabulary from this record.