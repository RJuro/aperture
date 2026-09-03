# 1. WHAT THIS AREA CONTAINS

- `design/BLUEPRINT.md` — latest conceptual synthesis after three rounds: defines Aperture, the five laws, validated mechanisms, rejected approaches, and intended surfaces. It supersedes earlier conceptual and UI assumptions in `MASSHINE.md`, `P10.2-CONTRACT.md`, and the pre-round plans; its repository-specific build status is historical after the lean restart. [design/BLUEPRINT.md opening; §1–§8]
- `design/BUILDOUT.md` — latest archived file-level implementation plan, rewritten after round 3 and phase A. It supersedes the phase plan in `V2-PLAN.md`; retain its acceptance gates and failure-prevention tests, but re-map its paths and migration steps to the new repository. [design/BUILDOUT.md opening; §Build strategy; §Decision log]
- `design/INSIGHT-LOOP.md` — evaluation protocol for optimizing mediated understanding: roles, blindness, C0/C1/C2 conditions, rubric, Goodhart guards, and stopping rule. Execution results supersede its predictions in `ROUND-LEDGER.md`; the protocol remains reusable. [design/INSIGHT-LOOP.md §1–§9]
- `design/INTERACTION-MODEL.md` — systematic epistemic state ledger, researcher-question catalogue, transition table, and four audits. Its identified UI changes were adopted into `V2-PLAN.md` and `BUILDOUT.md`; its ownership and audit method remain relevant. [design/INTERACTION-MODEL.md §1–§6]
- `design/MASSHINE.md` — foundational post-simplification system specification: evidence/direction loops, three-layer analysis model, reduced pipeline, and methodological positioning. Later superseded on the instrument name, anchor architecture, surface count, coverage claims, and model plan by `BLUEPRINT.md` and `BUILDOUT.md. [design/MASSHINE.md opening; §2–§10]
- `design/P10.2-CONTRACT.md` — pre-round schema and API contract for SYNTHESIZE, focus versioning, check-backs, residue, and needs-judgment. It remains the data-model foundation but is incomplete relative to later anchors, register claims, roster, absence checking, exchange doors, and exposure ledger. [design/P10.2-CONTRACT.md §1–§5; design/BLUEPRINT.md §3–§5]
- `design/RESEARCHER-WALKTHROUGH.md` — action-by-action simulated work week used to test whether surfaces and endpoints fit researcher practice. Its decisions were adopted into `V2-PLAN.md §8`; it is design evidence, not a graded researcher trial. [design/RESEARCHER-WALKTHROUGH.md opening; §The verdict table; §What this changes]
- `design/ROUND-LEDGER.md` — primary empirical record for the three simulated-researcher rounds, including scores, exposure, defects D0–D18, predictions, interventions, and round-4 design. `BLUEPRINT.md` condenses it, but this remains the detailed source of evidence. [design/ROUND-LEDGER.md opening; §Round 1; §Round 2 — results; §Round 3 — result]
- `design/SIM-PLAN.md` — initial plan for the local headless week, steering-diff probe, false-steer test, grounding checks, and UI ledger. Its experiment design was expanded by `INSIGHT-LOOP.md` and its execution is recorded in `ROUND-LEDGER.md`. [design/SIM-PLAN.md §1–§7]
- `design/UI-AUDIT.md` — diagnosis of the abandoned hybrid frontend: nine routed views, legacy fallbacks, conflicting state derivations, and diluted interaction language. Its concrete rewrite target was superseded by `V2-PLAN.md` and then `BUILDOUT.md`; its root-cause findings remain directly relevant. [design/UI-AUDIT.md §The root cause; §What has to happen]
- `design/V2-PLAN.md` — selected the server-rendered FastAPI/Jinja2/htmx architecture and translated the UI audit into invariants and phases. The stack decision remains current in the archive; `BUILDOUT.md` supersedes its phase details and changes several interaction rules. [design/V2-PLAN.md §1–§9; design/BUILDOUT.md opening]
- `design/VIEW-API-MAP.md` — inventory mapping the intended four-screen design to existing endpoints and identifying missing routes, client-side joins, and legacy loads. Its proposed vanilla-SPA rewrite was explicitly rejected in favor of server rendering by `V2-PLAN.md`. [design/VIEW-API-MAP.md §1–§5; design/V2-PLAN.md §1]
- `design/data-session-spec.md` — foundational P10 reframe from codebook curation to a data-session instrument, plus the original two-call design, evidence gates, audio path, history proposal, and open questions. Later contracts and round findings supersede parts of its UI and provenance design. [design/data-session-spec.md opening; §1–§13]

# 2. ESTABLISHED FINDINGS

1. The first-round mediated readers saw about 7% of one 405-sentence, 27,984-character interview. C1 opened 18 passages/7.2%; C2 opened 19/7.0%. The manual baseline used 100%. [design/ROUND-LEDGER.md §Round 1]

2. At 7.2% exposure, passive mediation retained 8/9 of manual depth, 9/9 calibration, and 6.5/7 groundedness, but only 3.5/9 fidelity. The measured cost was breadth rather than depth or calibration. [design/ROUND-LEDGER.md §The round-1 C-condition table; §Reading 1]

3. Interaction did not beat passive reception in the one-document round. C2−C1 was 0 fidelity, −1.0 groundedness, 0 depth, −0.5 calibration, and −1.1 battery; only the battery loss cleared the noise band, in the wrong direction. The stated interpretation was that steering concentrated reading on the researcher’s question and paid in breadth. [design/ROUND-LEDGER.md §Scores, C2]

4. The loop nevertheless changed engine behavior: after steering, codes rose 8→11, findings 4→5, steps 11→13, check-backs 0→11, residue 0→4, and the story 3→5 paragraphs, with zero grounding drops. Guidance was therefore not inert. [design/ROUND-LEDGER.md §Round 1, “Engine behaviour, measured”; §Steering efficacy]

5. All 11 round-1 check-backs returned supports, strains, and could-not-find content, including contradictions of the researcher’s own reframe and qualifications of an agreed step. This established that the check-back mechanism can behave adversarially rather than merely affirming direction. [design/ROUND-LEDGER.md §Round 1, W1]

6. The same round falsified one check-back: it confidently reported no remittance evidence even though relevant sentences were already present under another code. Check-backs cannot safely infer absence from the codebook; they must search the material. [design/ROUND-LEDGER.md §Round 1, D0]

7. Two READ/SYNTHESIZE calls per pass were operationally viable on the local model: approximately 13 minutes for READ and 8 minutes for SYNTHESIZE in round 1. The reduced call architecture worked mechanically, though latency remained minutes rather than interactive. [design/ROUND-LEDGER.md §Round 1, “Engine behaviour, measured”]

8. Changing doors from isolated sentences to question-and-answer exchanges reduced surface-caused entity fabrication. In round 1, zero of two mediated readers reconstructed the sibling sequence correctly; in round 2, three of four did. The remaining error occurred despite the text being available and was graded as a reader error. [design/ROUND-LEDGER.md §Round 2 — results, “Arm 0 worked”]

9. Exchange doors changed the amount of raw text delivered so substantially that round-1 and round-2 scores were not comparable: 18 sentence doors exposed 1,969 characters/7.2%, while round-2 exchange doors exposed 5,595–7,367 characters/20.5–27.0%. Door count is therefore not a valid exposure constant. [design/ROUND-LEDGER.md §Round 2 — results, “The confound”]

10. Exchange doors created duplicate charging unless deduplicated. One reader’s 18 requested IDs resolved to only 12 distinct exchanges; six requests, one-third of the budget, initially bought nothing new. The implemented response was to refund and name duplicates. [design/ROUND-LEDGER.md §Round 2 — results, “The arms found a defect”; §Phase A1]

11. Round 2 tested three reader-facing coverage mechanisms against a context-integrity base. Territory codes changed fidelity +0.5; a coverage map changed it +1.0; a document arc changed it 0.0. None cleared the 1.0 noise band, while the map and document arc each reduced groundedness by 2.0. [design/ROUND-LEDGER.md §Round 2 — results, “The scores”]

12. The focus classified 289 of 405 sentences—about 70%—as set-aside territory. Making that material visible and addressable did not itself produce a credited score improvement. [design/ROUND-LEDGER.md §Round 2 — results, “What the arms produced”; “Round 2 close-out”]

13. The only successful round-2 coverage intervention changed the engine’s representation rather than the reader’s display. An 89-word self-authored reading brief won the blind comparison and caused the next pass to address exactly the three gaps the brief named. This is the empirical basis for “slots, not pipelines.” [design/ROUND-LEDGER.md §Round 2 — results, “Arm 4 is the exception”; design/BLUEPRINT.md §1]

14. A whole-document prose arc increased battery score by 1.45 but reduced groundedness by 2.0 without improving fidelity. The document-arc prose was rejected; only a short anchored divergence note was retained. [design/ROUND-LEDGER.md §Round 2 — results, “The scores”; “Round 2 close-out”; design/BLUEPRINT.md §4]

15. Four round-2 readers independently criticized three system claims, but the oracles overturned two criticisms: one treated unseen kin as absent, and another rejected a true claim whose citations were mis-bound. The resulting finding was that mediated criticism is less reliable than assent because assent is checked against a passage while criticism is often checked against a gap. [design/ROUND-LEDGER.md §Round 2 — results, D14–D15; “The two reversals”]

16. Verbatim anchors proved highly compliant and did not reduce output volume. Three live passes produced 18 bound/0 unfound/0 missing, 37/1/0, and 38/0/0; the first anchored pass had 10 steps versus nine in its unanchored base. [design/ROUND-LEDGER.md §Phase A1; §Round 3 — in progress; design/BLUEPRINT.md §1]

17. Anchors repaired citation binding at the source, exposed previously flattened wording, and surfaced dissent as a tension. They bought auditability and recall without consuming a door. [design/ROUND-LEDGER.md §Phase A1, “The quotes fixed three defects”; design/BLUEPRINT.md §1]

18. Anchors also caught a persistence-layer failure that unit tests missed: a fixed field list silently removed step anchors before database persistence. The exposure counter separately remained at zero because stored IDs and posted IDs used different qualification formats. Both failures survived a green test suite. [design/ROUND-LEDGER.md §Phase A1, “Bug the live check caught”; “Also landed”]

19. The broader lesson was repeated: 453 green tests did not prove trustworthy output. The archive records two anchor-dropping bugs and a counter bug passing tests, leading to the requirement that every acceptance gate inspect at least one real output against its transcript. [design/BUILDOUT.md opening; §Build strategy; design/BLUEPRINT.md §7]

20. The register slot initially returned zero claims because the prompt began with an emphatic prohibition on quoting and described register quotations later as an exception. Making the code and register rules symmetrical changed the same run from 0 claims/0 instances to 2 claims/5 instances and improved the anchor tally from 37 bound/1 unfound to 38/0. [design/ROUND-LEDGER.md §Round 3 — in progress, “The register slot did not fire”; “The register slot fires”]

21. The round-3 absence check worked in both directions. One query searched 363 unread passages and refuted the reader with an anchored passage from a section they had not read; another search of 302 passages supported a different negative claim. This closed the D14 failure mode in live use. [design/ROUND-LEDGER.md §Round 3 — in progress, “D14 closed”; design/BLUEPRINT.md §1]

22. Round 3 scored fidelity 5.0, groundedness 8.5, depth 7.0, calibration 9.0, and battery 7.0 at 28.8% exposure. Only the battery increase, 5.4→7.0 or +1.6, cleared the noise band. Fidelity remained flat within noise. [design/ROUND-LEDGER.md §Round 3 — result]

23. The mediated reader’s groundedness of 8.5 exceeded the unaided full-reader baseline of 7.0, while fidelity remained far below the manual 9.0. The instrument improved honesty about known material but did not reproduce the breadth of full reading. [design/ROUND-LEDGER.md §Round 3 — result, “What the anchors actually bought”]

24. Raising the allowance to 30 doors did not produce the predicted 40% exposure. The reader stopped after 20 doors at 28.8%, having opened 103 sentences and none from the first two sections despite repeated coverage warnings. Reader stopping, not the nominal budget, became the operative constraint. [design/ROUND-LEDGER.md §Round 3 — result, “The prediction fires”]

25. That stopping behavior was consistent with the stated focus: the reader concentrated on migration planning, departure, crossing, arrival, and settlement while declining childhood farm material. The ledger therefore concluded that stopping was not necessarily a failure; the evaluation had compared a focused reading with an unfocused manual ceiling. [design/ROUND-LEDGER.md §Round 4 — design, “The reader stopped because the focus told them to”; “But the instrument scores them as if they had failed”]

26. The frozen battery penalized exactly the material the focus reasonably declined: substance scored 5/8, below texture 6/8, inference 3/4, and limit 3/4. An honest “I do not know because it is outside this focus” could receive calibration credit while losing battery credit. [design/ROUND-LEDGER.md §Round 4 — design]

27. Coverage displays alone did not compel broader reading. A reader can rationally decline an explicitly displayed gap; therefore the product should disclose coverage without representing the focused reading as comprehensive or treating non-use of a budget as failure. [design/ROUND-LEDGER.md §Round 3 — result; §Round 4 — design; design/BUILDOUT.md “What three rounds changed,” item 4]

28. A topic can continue beyond a correctly bounded exchange. In round 3, the first exchange contained a problem and the next contained its resolution; the reader opened only the first and overreached. The implemented fix was to name predecessor and continuation exchanges rather than enlarging the exchange automatically. [design/ROUND-LEDGER.md §Round 3 — result, D18; “Round 3’s change”]

29. The original frontend’s failure was architectural, not attributable to vanilla JavaScript alone: nine fetches populated one state object with both old and new products, derived strings were recomputed in the browser, every change re-rendered the document, and there were no frontend tests. Engine tests could therefore stay green while the UI combined incompatible products. [design/V2-PLAN.md §1; design/VIEW-API-MAP.md §3]

30. The UI audit measured nine routed views against an intended four, approximately 3,340 lines of application JavaScript against an approximately 80-line design shell, and nine load-time data sources against one payload per surface. Five routed views belonged to the abandoned codebook-curation paradigm. [design/UI-AUDIT.md §The root cause; design/VIEW-API-MAP.md §1]

31. The walkthrough used four routed surfaces—Home, Session, Journal, and Text—and did not use the codebook, themes, friction, notes, or overview destinations. The codebook was wanted only twice, for scrutiny, supporting its treatment as a drawer rather than daily workspace. [design/RESEARCHER-WALKTHROUGH.md §The verdict table]

32. These trials are evidence about synthetic LLM readers and the instrument, not human researchers or the validity of reflexive thematic analysis. Human evidence remained reserved for the separate Nirosha validation. [design/INSIGHT-LOOP.md §8; design/SIM-PLAN.md §1 and §7]

# 3. DEFECTS AND FAILURE MODES

1. **D0 — codebook-bounded absence.** A sentence already classified under one code stopped being considered evidence for another question, producing a false could-not-find result. Fix: search the raw unread material through `check-absence`, not the codebook. Later plans avoid pre-verifying every machine negative because that would add one call per check-back; machine negatives remain explicitly unverified until the verb is run. This is mitigation, not full automatic closure. [design/ROUND-LEDGER.md §Round 1, D0; design/BLUEPRINT.md §3; design/BUILDOUT.md §B1.8]

2. **D1 — focus-sycophantic support.** The system used a sentence as emotional support even though its second half retracted the family-wide inference. Proposed fix: inspect immediate neighboring text for retraction, hedge, or reversal and downgrade such evidence to a tension. Round 2 ultimately prioritized D11 instead, so D1 was not separately demonstrated closed. [design/ROUND-LEDGER.md §Round 1, D1; “Change for round 2”]

3. **D2 — category laundering.** Harmful or unequal treatment was rewritten as neutral “repair” performed by an “advocate.” Proposed fix: forbid functional euphemism where the material names harm. No explicit closure is recorded. [design/ROUND-LEDGER.md §Round 1, D2]

4. **D3 — moral silence rendered as data uncertainty.** A narrator’s refusal or hedge around a death was reduced to uncertainty about event detail. Anchor enforcement later placed the speaker’s words directly in the step, materially mitigating the flattening; no separate closure test is recorded. [design/ROUND-LEDGER.md §Round 1, D3; §Phase A1]

5. **D4 — the research frame returned as findings.** Initial codes repeated the vocabulary of the focus rather than discovering a different register. A focus change and later self-brief/register slots diversified the reading, but the general frame-return risk remains open. [design/ROUND-LEDGER.md §Round 1, D4; §Round 2 — results, “Arm 4 is the exception”]

6. **D5 — unmarked silence.** Material entirely outside the mediated layer was invisible even though explicitly declined material was shown. Territories and coverage maps made gaps visible, but neither produced a credited fidelity improvement; the final design discloses unread and declined regions without implying completeness. [design/ROUND-LEDGER.md §Round 1, D5; §Round 2 — results; design/BLUEPRINT.md §3 and §5]

7. **D6 — reactions did not update stance.** Steps had `finding_id: null`, so 11 reactions left every finding at `stance: none`. Proposed fixes: attach finding IDs wherever possible or roll stance up through supporting codes. The later contract includes `finding_id`, but the ledger records no explicit closure test. [design/ROUND-LEDGER.md §Round 1, D6; design/P10.2-CONTRACT.md §3]

8. **D7 — decline memos bloated guidance.** Declines inserted hundreds of sentence IDs into every later prompt. Proposed fix: compile the reason and count, not the ID list. No explicit measured closure is recorded. [design/ROUND-LEDGER.md §Round 1, D7]

9. **D8 — incompatible sentence-ID formats.** Session/journal payloads used document-qualified IDs while document payloads used bare IDs. This broke client resolution and counters. Server-side resolution and normalization at a single write boundary were adopted; the evidence counter was repaired. [design/ROUND-LEDGER.md §Round 1, D8; §Phase A1; design/VIEW-API-MAP.md §3.3]

10. **D9 — register deafness.** The engine indexed what was discussed but not how the participant repeatedly spoke. Fix: a `register_claims` slot with multiple anchored instances. After a prompt-order correction it emitted two claims and five instances. [design/ROUND-LEDGER.md §Round 1, D9; §Round 3 — in progress; design/BLUEPRINT.md §4]

11. **D10 — no sampling against the system’s frame.** Every available door came from an existing claim, so the reader could challenge interpretations but not sample material the system had not claimed. An unclaimed-material map was tested but did not clear noise and reduced groundedness; general “Ask the material” remained deferred. [design/ROUND-LEDGER.md §Round 1, D10; §Round 2 — results; design/BUILDOUT.md §B5]

12. **D11 — sentence-sized doors manufacture facts.** Stripping answers from their questions caused entity and itinerary errors. Fix: exchange-sized doors that always include the question and answer. Three of four round-2 readers then reconstructed the sibling sequence correctly, versus zero of two in round 1. [design/ROUND-LEDGER.md §Round 1, D11; §Round 2 — results, “Arm 0 worked”]

13. **D12 — recurrence ceiling.** A few selected passages cannot by themselves establish that a speaking move is characteristic across a document. Register claims with counts and distributed anchored instances address this for speaking register; general recurrence claims remain bounded by exposure. [design/ROUND-LEDGER.md §Round 1, D12; §Round 3 — in progress, “The register slot fires”]

14. **D13 — weakest-evidence sampling bias.** Readers rationally spent their scarce door allowance on flagged weak passages and failed to test strong load-bearing claims. A proposed strongest-evidence quota was included in the coverage-map arm but did not produce a credited result. Later plans suppress `weakest_sids` entirely. [design/ROUND-LEDGER.md §Round 1, D13; §Round 2 — design, Arm 2; design/BUILDOUT.md §B1.9]

15. **D14 — under-coverage mistaken for absence.** Readers confidently corrected a true kin claim because no relative appeared in the passages they opened. Fix: targeted absence verification over the unread remainder, returning supports/refutes plus anchors and the number searched. Demonstrated closed in round 3 with searches of 363 and 302 unread passages. [design/ROUND-LEDGER.md §Round 2 — results, D14; §Round 3 — in progress, “D14 closed”]

16. **D15 — true claim with wrong evidence pointers.** Readers rejected a correct unequal-treatment claim because its doors pointed to a different episode. Fix: every claim must carry a short verbatim anchor contained in its cited span; the live anchored run bound the claim to the correct words. [design/ROUND-LEDGER.md §Round 2 — results, D15; §Phase A1; design/BLUEPRINT.md §3]

17. **D16 — `weakest_sids` validated only for existence.** Several “weakest evidence” passages were unrelated to their claims, directing scarce attention off-topic. Decision: never render the field; remove it or subject it to the anchor law after round-4 evidence. Its final engine fate is unresolved. [design/ROUND-LEDGER.md §Round 3 — in progress, D16; §Round 3’s change; design/BUILDOUT.md §B1.9 and §B5]

18. **D17 — roster missed an alias.** The same person appeared as both brother and half-brother, but the roster did not reconcile the names. Proposed fix: one person per roster entry with every alias used in the document. No live closure is recorded. [design/ROUND-LEDGER.md §Round 3 — in progress, D17]

19. **D18 — a topic outlives an exchange.** A correctly bounded exchange could contain the setup while the next exchange contained the resolution. Fix: show predecessor and continuation IDs and let the researcher choose whether to follow. This landed in the sim renderer and engine exchange payload with tests. [design/ROUND-LEDGER.md §Round 3 — result, D18; “Round 3’s change”]

20. **Unnumbered — duplicate exchange charging.** Multiple cited sentence IDs can resolve to the same exchange. Fix: use one exposure ledger, refund duplicate openings, and name the refund. [design/ROUND-LEDGER.md §Round 2 — results, “The arms found a defect”; design/BLUEPRINT.md §3]

21. **Unnumbered — stale evidence counters.** Posted bare IDs never intersected stored qualified IDs, leaving “0/N opened” after actual reading. Fix: normalize at one write boundary and derive all counts from the exposure ledger. [design/ROUND-LEDGER.md §Phase A1; design/BUILDOUT.md §B1.2]

22. **Unnumbered — validated fields silently discarded.** Fixed key lists dropped anchors between validation and persistence/rendering. Fix: field-by-field fixture tests plus parity between the measured sim surface and product render. [design/ROUND-LEDGER.md §Phase A1; design/BUILDOUT.md “What three rounds changed,” items 1–2; §B2.5]

23. **Unnumbered — hybrid-product frontend.** Legacy data was loaded into the same client state as the new product, enabling fallback renderers to resurrect old views. Fix: one server-built context per surface, no product-level fallback, and no legacy data available to the template. [design/UI-AUDIT.md §The root cause; design/VIEW-API-MAP.md §3.1; design/V2-PLAN.md §2]

# 4. DESIGN DECISIONS AND THEIR REASONS

1. **The instrument is Aperture; MASSHINE names the funder.** “Aperture” expresses controlled exposure and the trade between focus and breadth. Docent, Sonde, and Ajar were rejected as respectively guide-centered, cold, and too playful. Infrastructure identifiers must not be renamed because a previous rename orphaned a data volume. [design/BLUEPRINT.md §8]

2. **The product is an instrument, not a persona or autonomous analyst.** It reports grounded findings and exposes evidence; interpretation remains researcher-owned. Assistant voice, charm, and claims of autonomous theme generation were rejected as methodologically incongruent. [design/MASSHINE.md §1 and §10; design/data-session-spec.md §1 and §9]

3. **Researcher work is judgment, not taxonomy administration.** The codebook-curation model was rejected because it made the researcher the AI’s librarian. The retained interaction is reaction to claims—agree, challenge, reframe, park—with structural verdicts deferred to a deliberate review sitting. [design/MASSHINE.md §3; design/data-session-spec.md §3–§4]

4. **Use restrained READ plus SYNTHESIZE, approximately two calls per document.** The previous 19–25 calls repeatedly paid thinking costs; fewer larger calls amortize reasoning. Approximately 77 codes per interview were replaced by a hard cap near 20–25, reuse-before-mint, and one default coder with second lenses only on demand. [design/MASSHINE.md §3–§4; design/data-session-spec.md §5]

5. **Slots, not open-ended agent loops.** Python owns contracts, schemas, gates, caps, and call structure; the model and researcher fill named, bounded, validated, exported slots. This was selected because the self-authored brief changed the next engine pass while preserving auditability. [design/ROUND-LEDGER.md §Round 2 — design; §Round 2 — results; design/BLUEPRINT.md §3]

6. **Adopt the anchor law.** Every claim type must contain a short verbatim quote—approximately 12 words or fewer—that Python can locate character-for-character in the cited span. Existence-only sentence-ID validation was rejected because it allowed D15. [design/BLUEPRINT.md §3; design/ROUND-LEDGER.md §Phase A1]

7. **The anchor design supersedes an earlier provenance contract.** `MASSHINE.md` says the model never emits quote text and all quotations are resolved from sentence IDs; the post-round design instead requires the model to emit short verbatim anchors and validates containment. The next version must follow the later anchor law while still resolving full exchanges from immutable offsets. [design/MASSHINE.md §4; design/BLUEPRINT.md §3]

8. **Adopt three explicit absence types:** declined by focus, unread by the researcher, and absent from the document after verification. Conflating them was rejected because it caused D14 and D0. [design/BLUEPRINT.md §3]

9. **Negative claims are verbs, not unverified memo text.** Wherever the researcher can say “never,” the interface should offer a targeted check over unread material and record its verdict, anchors, and searched count. Automatic verification of every machine not-found claim was rejected as incompatible with the two-call economy; until checked, the claim must be visibly marked unverified. [design/BUILDOUT.md §B1.8 and §B3.5]

10. **Use one exposure ledger as the sole source of researcher-visible counts.** Doors write it server-side; share read, per-section coverage, finding gates, and export lines are derived from it. Client bookkeeping and independent counters were rejected because they drifted and destroyed trust. [design/BLUEPRINT.md §3; design/BUILDOUT.md §B1.2 and §Decision log]

11. **Use question-and-answer exchanges as evidence units.** Sentence-level doors were rejected because they hid referents and manufactured facts. Automatically expanding to a whole topical sequence was also avoided; continuations are named so the researcher controls further exposure. [design/BLUEPRINT.md §3; design/ROUND-LEDGER.md D11 and D18]

12. **The product has no door budget.** Budgets were experimental measurement devices. The application instead always shows share read and lets the researcher stop when the focus is satisfied. [design/BUILDOUT.md “What three rounds changed,” item 4; §Decision log]

13. **Coverage disclosure must not imply completeness.** Use a dual strip showing both where the analysis reaches and what the researcher has opened, plus explicit declined territories. Reader-facing arcs and coverage prose were rejected as fidelity mechanisms because they failed to clear noise and could reduce groundedness. [design/BLUEPRINT.md §5 and §7; design/ROUND-LEDGER.md §Round 2 — results]

14. **Retain territory demotions but subordinate them.** They were the only tested mechanism that made the focus-declined 70% addressable, but their score changes were below noise. They are therefore retained as quiet disclosures, not promoted as a proven coverage solution. [design/ROUND-LEDGER.md §Round 2 close-out; design/BLUEPRINT.md §4]

15. **Standardize the reading brief.** The model-authored brief travels to the next pass and is intended eventually to travel across documents. It was adopted because its blind comparison succeeded where three reader-facing coverage interventions did not. [design/BLUEPRINT.md §4; design/ROUND-LEDGER.md §Round 2 — results]

16. **Add register claims and an entity roster.** Register claims are the identified way to communicate recurrence with several anchored instances at less than proportional exposure; the roster addresses cross-door entity reconciliation. [design/BLUEPRINT.md §4]

17. **Do not render `weakest_sids`.** The feature both biased sampling and sometimes pointed to unrelated text. It remains an engine field only until evidence supports removal or anchored redesign. [design/BUILDOUT.md §B1.9; §Decision log]

18. **Use one researcher-facing action: “Read this interview.”** It chains READ and SYNTHESIZE under one job because a read-but-unsynthesized document has no introduction or session and is only an internal checkpoint. The four visible states are not read yet → reading → preparing the session → session ready. [design/RESEARCHER-WALKTHROUGH.md §Scene 4; design/V2-PLAN.md §8]

19. **Use four routed surfaces: Home, Session, Journal, Text.** The older three-surface statement made Journal the home; the later walkthrough and UI architecture add a distinct Home for orientation and outstanding direction. Codebook, themes, friction, notes, and overview routes were rejected as daily destinations. [design/MASSHINE.md §3 and §5; design/UI-AUDIT.md §What has to happen; design/V2-PLAN.md §2]

20. **Text is opened from evidence, not browsed as a generic destination.** Every entry should carry the referring claim and a way back. A top-level arbitrary transcript view was rejected because it detached reading from the analytical reason for opening it. [design/UI-AUDIT.md points 5 and §What has to happen; design/V2-PLAN.md §2]

21. **Server-render the application with FastAPI, Jinja2, and vendored htmx.** This was chosen so actual HTML is pytest-testable, each template receives one server-built context, the design export can be reused directly, and a Python maintainer avoids a second build ecosystem. React/Preact/Vite were rejected as unnecessary tooling; a disciplined vanilla SPA was runner-up but rejected because its safeguards depended on future agents following conventions. [design/V2-PLAN.md §1]

22. **Derived language belongs in Python.** Document state, quotes, job narration, coverage language, and standing directives must have one server-side producer. Browser-side recomputation and multi-payload joins were rejected after producing contradictory state and expensive full-document quote resolution. [design/VIEW-API-MAP.md §3–§4; design/V2-PLAN.md §2]

23. **The measured sim rendering is the product’s content contract.** Template tests should assert that every claim, anchor, roster entry, register instance, and door ID shown in the graded sim also appears in the product, while excluded fields remain excluded. A visually similar but semantically different page would not inherit the evaluation results. [design/BUILDOUT.md “What three rounds changed,” item 2; §B2.5]

24. **No dead controls.** History, compare, ask, second lens, and split remain absent until their engine behavior exists. Disabled placeholders were rejected because they misrepresent capability. [design/V2-PLAN.md §5–§6; design/BUILDOUT.md §Decision log]

25. **The accent color is reserved for researcher-authored language.** Using it for nav, primary actions, and status diluted the ownership distinction. System actions use ink/weight instead. [design/UI-AUDIT.md points 10 and §What has to happen; design/V2-PLAN.md §6]

26. **Standing is computed; stance is derived; verdicts are researcher-authored and evidence-gated.** The model cannot grade its own support, and researchers should not be asked to set evidential facts. Early accept/reject status controls were rejected because the evidence required for a structural verdict does not exist after one document. [design/P10.2-CONTRACT.md §3 and §5; design/data-session-spec.md §4]

27. **Every test gate includes real-output inspection.** Unit tests alone were rejected as sufficient evidence after persistence and counter defects passed green suites. [design/BUILDOUT.md §Build strategy]

28. **Model policy changed and remains internally inconsistent.** `MASSHINE.md` names MiniMax M3 as production default; the later `BUILDOUT.md` selects a current “luna-class” Mistral/GLM generation rather than older M3. However, the same buildout still calls B4 an “M3 gate” and says deployment passes on M3. The next build must resolve this before freezing fixtures or prompts. [design/MASSHINE.md §6; design/BUILDOUT.md “What three rounds changed,” item 6; §B4]

29. **Local Codex/luna output is calibration only.** It may produce fixtures and run simulations locally but must never be registered, deployed, or cited as human evidence. [design/SIM-PLAN.md §1, §6–§7; design/INSIGHT-LOOP.md §8]

# 5. OPEN QUESTIONS

1. **Does interaction add cross-document value?** The one-document C2−C1 result was non-positive. The required Grande→Rodwin two-document test, including whether the travelling brief helps the second document, is planned but no result appears in these files. [design/ROUND-LEDGER.md §Round 1 close-out; design/BUILDOUT.md §The operational track]

2. **What is the correct focused ceiling?** Round 4 proposes C0-F, a full reader carrying the same focus, plus a blind in-focus/out-of-focus battery split. No round-4 result is recorded. [design/ROUND-LEDGER.md §Round 4 — design]

3. **Is the observed fidelity ceiling intrinsic to mediation?** Fidelity remained 4.5–5.5 while exposure rose from about 20% to 28.8%, but the predicted 40% condition was never reached. C0-F is intended to distinguish a real mediation ceiling from a mismatched benchmark. [design/ROUND-LEDGER.md §Round 3 — result; §Round 4 — design]

4. **Do gains transfer beyond the two tuning transcripts?** The protocol requires a third hold-out transcript at declared checkpoints and rollback of non-transferring gains, but no hold-out result is reported. [design/INSIGHT-LOOP.md §6]

5. **Does the instrument help a human qualitative researcher?** The Nirosha/Livicia Antoine validation remains separate and pending in the operational plan. Simulated-reader scores cannot answer this. [design/BUILDOUT.md §The operational track; design/INSIGHT-LOOP.md §8]

6. **Which production model will ship, and does it satisfy the anchor/register/roster contract?** The older M3 default and later luna-class model decision conflict; the paid compliance run is not reported. [design/MASSHINE.md §6; design/BUILDOUT.md §B4]

7. **Should machine-generated could-not-find claims be verified automatically?** The absence law suggests verification against the unread remainder, while `BUILDOUT.md` rejects per-check-back verification on cost grounds and renders them unverified until requested. [design/BLUEPRINT.md §3–§4; design/BUILDOUT.md §B1.8]

8. **What is the final fate of `weakest_sids`?** Evidence supports suppressing it, but the archive defers whether to delete it, anchor it, or redesign it after round 4. [design/ROUND-LEDGER.md D16; design/BUILDOUT.md §B5]

9. **Was the D17 alias fix implemented and validated?** The proposed roster contract requires all names for one person, but no subsequent live run verifies it. [design/ROUND-LEDGER.md D17]

10. **Are D1, D2, D4, D6, and D7 still active in the lean implementation?** Each has a proposed or partial mitigation, but the ledger contains no explicit closure result. [design/ROUND-LEDGER.md §Round 1, D1–D7]

11. **How should researchers sample material no existing claim reaches?** The coverage-map experiment did not solve D10, and general “Ask the material” remains deferred. [design/ROUND-LEDGER.md D10; design/BUILDOUT.md §B5]

12. **Can recurrence beyond speaking register be communicated without proportional exposure?** Anchored register instances address one class, but D12’s broader recurrence ceiling remains. [design/ROUND-LEDGER.md D12; design/BLUEPRINT.md §4]

13. **Should verdicts be checked after application?** Reactions and focus changes receive check-backs, but merge/demote decisions are only evidence-gated before action. The proposed test is whether recomputed standing reliably surfaces a bad merge. [design/INTERACTION-MODEL.md §5; design/V2-PLAN.md §9]

14. **What is the final READ span?** The architecture supports whole-document, halves, section groups, and per-section calibration, but the files do not report a completed held-transcript comparison fixing the default. [design/data-session-spec.md §5]

15. **How long should a walkthrough be before fatigue outweighs value?** No step-count calibration is reported. [design/data-session-spec.md §13]

16. **What should happen to Q&A records?** It remains undecided whether whole Q&A transcripts belong in the Journal or only researcher-promoted excerpts. [design/data-session-spec.md §13]

17. **How should imported human codebooks be adjudicated, and are multi-project cross-corpus sessions needed?** Both remain deliberately deferred. [design/data-session-spec.md §13]

18. **How should project history be made safe?** Git-backed history, restore, and “Mark this moment” are specified but unbuilt and require their own integrity design around active jobs and whole-project restore. [design/data-session-spec.md §7; design/BUILDOUT.md §B5]

19. **Which archived UI invariants transferred into the lean repository?** The files define parity, field-coverage, banned-vocabulary, single-ledger, and one-context tests, but they do not document the restarted repository’s implementation state. [design/BUILDOUT.md §B1–§B3; §Decision log]

20. **When is optimization complete?** The declared stop condition—two consecutive full rounds with no movement beyond noise, all probes green, and hold-out confirmation—has not been met in this record. [design/INSIGHT-LOOP.md §8]

# 6. VOCABULARY

- **Anchor** — a short verbatim quote, approximately 12 words or fewer, that Python can find character-for-character inside the claim’s cited exchange or span. [design/BLUEPRINT.md §3]
- **Door** — a researcher-visible link that opens the full question-and-answer exchange around cited material and records that exposure; duplicate openings are refunded. [design/BLUEPRINT.md §3 and §5]
- **Slot** — a named, bounded, validated, exported field through which the model or researcher supplies words inside a Python-owned scaffold. [design/ROUND-LEDGER.md §Round 2 — design; design/BLUEPRINT.md §3]
- **Exposure** — the raw material actually shown to the researcher, measured from one ledger as passages/sentences, characters, and share of the document. [design/INSIGHT-LOOP.md §2 and §4]
- **Exposure ledger** — the append-only record of every raw passage opened by the researcher, used as the sole source for coverage, gate, and export counts. [design/BLUEPRINT.md §3; design/BUILDOUT.md §B1.2]
- **Round ledger** — the research record containing each experimental configuration, scores, noise band, diagnosis, intervention, and prediction for the next round. [design/INSIGHT-LOOP.md §6–§7]
- **Exchange** — the interviewer question plus its answer; the minimum unit for doors, anchors, and citation context. [design/BLUEPRINT.md §3]
- **Register** — a recurring manner in which a participant answers or narrates, distinct from the topic discussed, represented through a claim plus multiple anchored instances. [design/BLUEPRINT.md §4; design/ROUND-LEDGER.md D9]
- **Territory** — a coarse, addressable description of an out-of-focus region, rendered as a subordinate demotion rather than a foreground code. [design/ROUND-LEDGER.md §Round 2 — design, Arm 1]
- **Residue** — grounded material, codes, or findings that do not fit the current account; retained as a first-class abductive signal with an optional reframe proposal. [design/MASSHINE.md §2; design/P10.2-CONTRACT.md §1]
- **Reading brief / brief** — a model-authored, capped instruction for a subsequent pass naming unrepresented regions, registers, and unresolved questions; the successful test used 89 words against a 120-word cap. [design/ROUND-LEDGER.md §Round 2 — design and results]
- **Focus** — the versioned research question governing what the next reading attends to; researcher-authored or model-proposed and researcher-accepted. [design/MASSHINE.md §2; design/P10.2-CONTRACT.md §2]
- **Steer** — a researcher-authored reaction, challenge, reframe, focus change, or verdict compiled into guidance for a later engine pass. [design/INTERACTION-MODEL.md §1 and §4]
- **Check-back** — the later report testing a standing steer against material through supports, strains, could-not-find content, and possibly a revision proposal. [design/P10.2-CONTRACT.md §1 and §3]
- **Declined** — material explicitly set aside by the active focus; it remains logged, addressable, and eligible for reconsideration after a focus change. [design/BLUEPRINT.md §3]
- **Absence check** — a targeted pass testing a negative claim against unread material and returning supported/refuted status, anchors, and a searched-passage count. [design/BLUEPRINT.md §3 and §5]
- **Standing** — Python-computed evidential strength of a finding, derived from support rather than set by the model or researcher. [design/P10.2-CONTRACT.md §3]
- **Stance** — a lightweight state computed from the researcher’s reactions to related steps. [design/INTERACTION-MODEL.md §2]
- **Verdict** — a researcher-owned structural decision made during a deliberate evidence-gated review sitting: keep-and-name, merge, split, demote, or drop. [design/data-session-spec.md §4]
- **Evidence gate** — the rule preventing keep-and-name until the researcher has opened all required key passages. [design/data-session-spec.md §4]
- **Fact panel** — free, persistent interview metadata and entity roster supplied without consuming exposure. [design/BLUEPRINT.md §5]
- **Dual coverage strip** — per-section display separating passages reached by the analysis from passages actually opened by the researcher. [design/BLUEPRINT.md §5]
- **Reading record / defensible account** — the export containing grounded claims, every filled steering slot, focus history, exposure, declines, and absence checks so every assertion can be defended. [design/BLUEPRINT.md §2 and §5; design/BUILDOUT.md §B1.11]
- **Battery** — the sealed comprehension questions authored before tuning and kept out of prompts, rounds, and selection decisions. [design/INSIGHT-LOOP.md §3]
- **Noise band** — the spread between two independent blind graders; no intervention is credited unless its change exceeds that spread. [design/INSIGHT-LOOP.md §4]
- **C0** — manual full-reading baseline and original ceiling. [design/INSIGHT-LOOP.md §5]
- **C0-F** — proposed full-reading ceiling carrying the same focus as the mediated researcher. [design/ROUND-LEDGER.md §Round 4 — design]
- **C1** — mediated passive condition: the researcher receives surfaces but does not steer. [design/INSIGHT-LOOP.md §5]
- **C2** — mediated interactive condition: reactions, steering, check-backs, residue, and review are active. [design/INSIGHT-LOOP.md §5]
- **Grounding gate** — validation that every cited sentence or anchor resolves to immutable transcript material before persistence. [design/MASSHINE.md §2 and §4]
- **Sitting clock** — immediate, inexpensive interaction with current state: reactions, opened evidence, focus versions, and gates. [design/INTERACTION-MODEL.md §1]
- **Engine clock** — slower, paid READ→SYNTHESIZE work that applies accumulated direction and changes analytical state. [design/INTERACTION-MODEL.md §1]
- **Needs judgment** — a derived queue containing only exceptions that require researcher attention, never routine code-review work. [design/P10.2-CONTRACT.md §1 and §5]