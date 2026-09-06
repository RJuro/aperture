# Aperture frontend review: language, navigation, and user help

**Date:** 6 September 2026  
**For:** The system and people building Aperture  
**Purpose:** An implementation brief for making the interface understandable and removing formulaic AI writing.  
**Scope:** Review only. No application behavior, analysis results, or production data changed.

## 1. Main finding

Aperture asks researchers to learn the application's private vocabulary before they can use ordinary controls. Short labels conceal what an action changes; the surrounding explanation often adds metaphors instead of resolving the ambiguity. Repeated uppercase subtitles, literary phrasing, and small muted text make practical instructions feel like an essay about the software.

The user's example is an exact match in the live interface:

> Every theme two materials carry:

This means **themes with claims in at least two materials**. The control selects which themes to check in materials where they were previously unassessed or skipped. Neither the threshold nor the missing-assessment scope is adequately explained by the label. “Carry” also means different things elsewhere: a source supports a claim, a material contains evidence of a theme, and a prompt includes an instruction. Readers have to reconstruct the intended relationship each time.

The first revision should address three things together:

1. Replace indirect language with the action, object, scope, and consequence.
2. Make Help consistently available and preserve the user's place when they open it.
3. Correct misleading statements about assessment, candidate promotion, and processing estimates.

Keep the useful foundation: restrained colors, readable source/analysis separation, linked quotations, visible processing status, and a project navigation rail. A new visual theme is not required to address these problems.

## 2. What was inspected

**Live inspection:** Safari, the existing signed-in “Ellis Island v3” project: project overview, theme matrix and comparison controls, the Guide, and a material page with claims beside source text. Opening Guide removed the project rail and breadcrumb. Browser Back returned to the project at the previous scroll position; the Guide itself offered no explicit return-to-project control.

**Source inspection:** Local checkout `29c4bf9`; shared layout, project, material, theme, home, reading-record, and Guide templates; relevant CSS; context-generated labels; comparison planning and promotion logic; the project-summary prompt; README and documentation organization. Live copy matched the cited comparison and Guide text. Deployment commit identity was not independently verified.

**Limits:** No analysis jobs, sharing changes, or destructive actions were run. Mobile findings below come from source inspection, not a mobile-device test. Contrast and assistive-technology behavior need dedicated verification. Generated analysis was reviewed for presentation and wording, not revalidated against the whole interview corpus.

## 3. Brief research: “Claude-isms” and common AI design habits

“Claude-ism” is an informal description of recurring writing habits, not a reliable test of authorship. The relevant question for Aperture is whether users understand the page and can predict its actions.

### Writing patterns worth checking

| Pattern | Why readers object | Application to Aperture |
|---|---|---|
| Repeated “not X, but Y” constructions | The sentence manufactures a correction before stating the useful information. Repetition becomes a recognizable voice. | Keep contrasts that distinguish real research states. Remove rhetorical ones such as “not by asking the model nicely.” |
| Punchy fragments and synthetic profundity | Rhythm gives an impression of insight without explaining a mechanism. | “Recurrence proposes; you promote” should become an explicit account of who changes theme status and when. |
| Metaphors substituting for relationships | Words sound polished while leaving the reader to infer what is being done to what. | Audit “carry,” “rest on,” “hold,” “open,” “fold,” “written over,” and “what the reading arrived at.” |
| Reassurance or certainty beyond the evidence | Confidence in tone can obscure limitations or exceptions. | Replace universal promises with specific behavior and visible qualifications. |
| Repeated explanations and ceremonial introductions | The reader works through setup before reaching the action or answer. | Remove introductions that explain the structure of the Guide instead of helping someone use Aperture. |

Two first-person critiques describe the fatigue caused by Claude's recognizable cadence, rhetorical reversals, and polished but semantically weak prose. These are useful accounts of reader frustration, not controlled comparisons between models. [Jerod Santo, “Claude's writing style has me on edge”](https://jerodsanto.net/2026/06/claudes-writing-style-has-me-on-edge/); [cmart, “Why is Anthropic's public writing style so unlike Claude's?”](https://cmart.blog/claude-writing/).

The stronger basis for changing UI copy is usability research: even domain experts prefer concise, scannable language, and expertise in a subject does not imply familiarity with an application's terminology. Explain necessary concepts at the point of use and put specialist detail in a secondary layer. [Nielsen Norman Group, “Plain Language Is for Everyone, Even Experts”](https://www.nngroup.com/articles/plain-language-experts/).

### Visual patterns worth checking

Anthropic itself describes recurring generated-design defaults: familiar font choices, purple gradients, predictable layouts, and components with little connection to the particular product. It also notes that prompts to avoid one default can produce another default. This supports reviewing design against actual tasks rather than just requesting a more “distinctive” appearance. [Anthropic, “Improving frontend design through Skills”](https://claude.com/blog/improving-frontend-design-through-skills).

The following is this review's application of that concern, not a claim that every item is uniquely caused by AI:

| Common design problem | Present in Aperture? | Direction |
|---|---|---|
| Gradient hero, generic feature cards, decorative animation | Not the dominant issue in the inspected workspace. | Avoid a cosmetic redesign aimed at these absent problems. |
| An eyebrow, large heading, and explanatory paragraph for every section | Yes. Particularly in the record, Guide, and home templates. | Give each section one useful heading. Keep extra text only when it changes understanding. |
| Marketing language occupying a returning user's workspace | Yes in the home template: a large slogan precedes projects. | Lead with projects and a clear creation action; reserve the introduction for first use. |
| “Quiet” styling making important controls hard to see | Yes: small gray labels, tiny help links, deeply folded actions. | Give task instructions and state explanations sufficient size, contrast, and prominence. |
| A polished default view with weak navigation and edge states | Yes: lost Help context, disappearing narrow-screen navigation, unexplained disabled choice. | Review real task sequences and incomplete states as part of design acceptance. |
| Decorative data displays without a clear measurement | Partly: theme bars compare claim counts, but require prose to decode. | Label the measure and sort; do not imply importance or confidence. |

Help should be easy to find, focused on the current task, and available in context. Consistent terms, visible state, and control over navigation are established usability principles. [Nielsen Norman Group, “10 Usability Heuristics for User Interface Design”](https://www.nngroup.com/articles/ten-usability-heuristics/).

## 4. Priority findings and required changes

**P1:** Misleads a consequential choice, hides important evidence state, or interrupts a core task.  
**P2:** Adds substantial reading effort, inconsistency, or visual noise.

### F1 — P1: The comparison control conceals both scope and changes

**Evidence:** `app/templates/project.html:142–148`; `app/store.py`, `opening_need()` and `backfill_cells()`; `app/rerun.py`, `consolidate_plan()`.

The control mixes four ideas in a paragraph and two radio labels: comparing theme definitions, merging overlapping themes, filling gaps in assessment, and changing candidate status. “Fold” elsewhere means collapse a visible section, but here means merge themes. “Compare every theme” sounds like a read-only comparison even though it can change the analysis.

The two scopes use **at least** a threshold, not exactly two materials. The default threshold is half of the counting units, rounded up, with a minimum of two. Where files are grouped into cases, the threshold counts cases while the work still happens on individual materials. Themes with evidence in only one counting unit are excluded from the additional source checks.

**Required change:** Name the operation and disclose its effects immediately above the button. Separate the threshold choice from the processing estimate. Show the actual threshold, unit, and number of theme/material pairs to assess. A “pair” means one theme checked in one material; a user should not have to understand a database cell.

**Proposed replacement, preserving current behavior:**

> **Compare and update themes**
>
> Compare the project's theme definitions and merge overlapping themes where appropriate. Also check selected themes in materials where they were previously unassessed or skipped. This updates the analysis and summaries.
>
> **Which themes should receive these additional checks?**
>
> ○ Themes with claims in at least **4 of 8 materials**
>
> ○ Themes with claims in at least **2 materials**
>
> **Additional checks:** 5 theme/material pairs. Each pair is one theme checked in one material. A preliminary review may skip a source check; the result will say why.
>
> **Theme status:** After comparison, candidate themes with claims in at least 4 of 8 materials become project themes automatically.
>
> **Instructions for comparing themes (optional)**
>
> Example: Consider merging the three themes about language.
>
> **Compare and update themes**

The numbers above illustrate the inspected eight-material project; generate them from current state. Keep a processing estimate nearby once F5 is addressed. If both scopes produce the same work, show one effective option and “Both scopes currently select the same 5 checks.” The live second radio was disabled without this explanation.

**Acceptance:** A new user can explain what will change, what will be checked, and why a choice is disabled before pressing the button. The wider option never implies every theme will be searched in every material.

### F2 — P1: Help removes the user's working context

**Evidence:** Live Guide navigation; `app/templates/base.html:25,53`; `app/pages.py:116–123`; narrow-screen rules in `app/static/aperture.css`.

Guide is in the project rail when a project is open and in the top bar otherwise. Opening it removes the project breadcrumb and rail. Users can use browser Back, but there is no application-level return path. Reading several help sections also adds fragment navigation to browser history, making Back a poor substitute for “return to my work.”

At viewport widths of 920px or less, CSS hides the project rail. The top-bar Guide link is still omitted on project pages. Contextual question marks remain in some places, but the global Help entry and project-section navigation disappear.

**Required design:** Put a consistently named **Help** control in the top bar on every page and at every supported width. Keep the project rail focused on project content. Contextual help should open a short answer beside the task, with a link to the full Guide.

For full documentation, retain the project context and show **Back to [project or material name]**. Preserve the selected theme, passage anchor, scroll positions, expanded sections, and unsent form values. A same-page help drawer is a good option for short answers because it can preserve the form in place; a contextual full-page route is also acceptable if restoration works. Do not depend solely on browser history or force a new tab.

On a direct or bookmarked Guide visit without project context, provide **All projects** as the fallback. Validate any return destination as a local application route and check access before showing project details. Provide a compact project menu when the rail is hidden.

**Acceptance:** Open Help from a selected theme with a draft comment, read two topics, and return with the draft and selection intact. Repeat on a narrow screen, with keyboard navigation, and from a direct Guide link. Closing inline help returns focus to its trigger.

### F3 — P1: An empty matrix cell is described as absence

**Evidence:** `app/templates/project.html:94,122`; `app/context.py`, `ASSESSED_SAID`; `app/templates/guide.html`, `#absence`.

The table says “A dash means none.” Its dash actually stands for five different states: no retained claims after assessment; preliminary review declined a source check; no matching codes triggered a check; no finding in the uncoded passages searched; or no assessment yet. Only a hover title distinguishes them in the table. The Guide describes four states and omits the preliminary-review state now present in code.

**Required change:** Replace the legend with **“Numbers count claims. Cells without a count show the assessment status.”** Expose each status in visible text or a keyboard- and touch-accessible detail control. Suggested labels:

| Stored state | Label | Explanation |
|---|---|---|
| `thin` | No retained claims | The theme was assessed, but no claims were retained. Review exclusions before interpreting this as absence. |
| `screened` | Source check skipped | A preliminary review of the summary and codes did not select this theme for a source check. Show its reason. |
| `skipped` | No matching codes | The initial coding did not trigger assessment for this theme. |
| `residual` | No match in uncoded passages | A search of passages without codes found nothing to add for this theme. This was a limited search. |
| No outcome | Not assessed | This material has not been assessed for this theme. |

Do not collapse these states into “Absent,” “None,” or zero. Keep search scope visible wherever a negative result is shown.

### F4 — P1: Candidate status and promotion explanations contradict behavior

**Evidence:** `app/store.py`, `settle_holds()`; `app/jobs.py`, `_settle()`; Guide `#themes`; `app/templates/project.html:99`; `app/templates/theme.html:10`; `app/context.py`, `_single_group()` and `_proposal()`.

The Guide says “Recurrence proposes; you promote.” Comparison can instead change candidates to open project themes automatically. This is an important methodological choice hidden behind ambiguous wording.

Separately, the project groups all candidates under “In one material so far” (or one case), and the theme page hardcodes the one-material explanation. Candidates can have claims in more than one material or case while awaiting promotion. Candidate status is not an evidence count.

**Required change:** Use **Project themes** and **Candidate themes** as group headings. Print actual coverage independently. Define candidate as **“Not yet included as a project theme.”** Disclose automatic promotion in the comparison control and Guide if it remains. If researcher-only promotion is the intended policy, change the behavior explicitly and test it. A wording patch must not silently choose between these policies.

The `OPEN_AT` code comment also attributes the half-of-cases threshold to reflexive thematic analysis. No source for that numerical rule is given there. Treat it as a product rule unless a specific methodological source substantiates it; review the attribution separately. This brief does not establish a methodological justification for the threshold.

### F5 — P1: The displayed call estimate omits later work

**Evidence:** `app/context.py:605–616`, `_cost()` inside project context; `app/rerun.py`, `consolidate_plan()`; `app/jobs.py`, `_accounts()`.

The estimate counts the comparison, preliminary reviews, verification, and possible per-pair checks. The planned operation also includes material summaries for iterative projects, theme summaries where required, and the project summary. Those later calls are not included in the displayed formula. The “up to” value is therefore not a demonstrated upper bound for the whole operation. This is a source-confirmed omission, not a measured billing result.

**Required change:** Estimate the entire planned operation, including conditional stages, or explicitly label the existing number as a partial estimate and state what is additional. A count of model calls does not establish elapsed time or monetary cost. Use current measured timing only when available, and date any illustrative benchmark. Move the historical “24 calls” example out of routine upload instructions.

### F6 — P2: Eyebrows add a second, less useful vocabulary

**Evidence:** Project, record, home, Guide, and sharing templates; `.eyebrow` in CSS.

Examples include “Your work” above “Projects,” “Begin a reading” above “New project,” “The corpus” above “Across the corpus,” “Doubt” above “Questions checked against the materials,” and “What the reading dropped” above “Excluded from the analysis.” These add atmosphere or repeat the heading. Several actual section labels, such as “What the material shows,” are paragraphs styled as eyebrows rather than semantic headings.

**Required change:** Delete redundant eyebrows. Give substantive sections normal, sentence-case headings in the heading hierarchy. Keep a separate label only when it supplies useful metadata that the title cannot convey, such as “Interview · 1989.” Do not replace deleted eyebrows with new slogans.

### F7 — P2: The Guide mixes instructions, rationale, history, and code

**Evidence:** Live Guide and `app/templates/guide.html`; `docs/GUIDE.md`; `docs/INDEX.md`; README.

The opening answer is a dense tour of the processing pipeline. It makes users learn codes, claims, lines, memos, accounts, and two methods before telling them how to add a file. Every section ends with source module names, presented as ordinary help. “Read that sentence exactly as it is written” and “not by asking the model nicely” add an admonishing tone. “Fourteen questions, in the order you meet them” is a promise about an imagined user journey.

**Required organization:**

| Layer | Contents | Where it belongs |
|---|---|---|
| Contextual help | What this control does, scope, consequences, a short example | At the control |
| User Guide | Getting started; adding sources; methods; themes and evidence; revising and reanalysing; sharing; exports; troubleshooting | Global Help, task-based contents, searchable topics |
| Method and limitations | Meaning of counts, search limits, human judgment, distinctions between analysis methods | Linked from relevant help and a dedicated Guide section |
| Developer documentation | Modules, prompts, configuration, deployment, evaluations, historical design decisions | Repository docs or a clearly labeled developer reference |

Keep one maintained source for each explanation. `docs/GUIDE.md` correctly points to the rendered Guide as its canonical source; preserve that principle when restructuring. `docs/INDEX.md` currently indexes predecessor-repository records, so it should not become the user-help landing page merely because it is called INDEX. Mark historical records clearly and add a current developer-doc entry point if needed.

Suggested opening answer:

> **Add materials**
>
> Open a project and select **Add material**. Choose one or more files, or paste text and give it a name. Select **Add material** to start the analysis.
>
> Each file becomes one material. Aperture identifies its structure, assigns codes, and produces themes and summaries with links to the source text. Processing continues if you leave the page. Check the progress message to see which step is running.
>
> Supported files: TXT, Markdown, Word (.docx), PDF, and CSV.
>
> **How analysis works** · **Understand the two analysis methods**

The two links are proposed destinations, not existing link labels. Put import limitations and error recovery in this topic once verified against ingestion behavior.

### F8 — P2: The workspace makes users scroll through generated prose to reach work

**Evidence:** Live overview and material page; `home.html`, `project.html`, and `material.html`.

The project overview puts a long synthesis and interpretation before its theme matrix and materials. A material page repeats themes in a summary list and a horizontal selector before the detailed claims. The source view is valuable, but several layers compete to introduce it. The home template uses a large promotional headline above the returning user's projects.

**Required change:** Make primary tasks available near the project title: **Add material**, **Materials**, **Themes**, and **Analysis record**. Show a concise project summary with an explicit way to read the full text. Keep interpretation separately labeled. Use one compact theme selector with counts, offering longer theme summaries on demand. Keep selected claims and the source text easy to reach. Preserve the matrix as a comparison tool, with clear horizontal-scroll affordance and a usable narrow-screen alternative.

The active navigation state should follow the current section or use a clearly page-level indication. The live page highlighted Overview while the comparison controls and Materials section were in view.

### F9 — P1: A claim's partial-support qualification disappears on the theme page

**Evidence:** `material.html:111` and `record.html:145` render the `partly` support note. The claim loop in `theme.html:60–69` renders the same claim and quote without that qualification; theme context passes through the stored claim fields.

**Required change:** Show **“Partially supported: [reason]”** wherever the qualified claim is displayed, including the theme page. Verify all relevant exports as well. This is a source-confirmed presentation inconsistency; the inspected live material was not used to demonstrate a specific partially supported claim. A claim must not appear more certain because the user opened another view.

### F10 — P2: Important text and controls are too visually quiet

**Evidence:** Live desktop screenshots; CSS uses 11px eyebrows and metadata, 10px material sublabels, 13px helper text, and 15×15px Help controls. Negative-status explanations are hover titles on noninteractive spans.

**Required change:** Increase the prominence of instructions that affect decisions. Use approximately 14–16px for ordinary control descriptions and readable sentence-case labels; reserve very small text for genuinely secondary metadata. Use descriptive accessible names for Help controls and an adequate hit area. Provide keyboard and touch access to cell explanations and code definitions. Add a skip-to-content link for the repeated navigation.

Measure text/background contrast and focus visibility on actual rendered colors. WCAG's normal-text contrast criterion is 4.5:1, with a 3:1 threshold for qualifying large text. Its minimum pointer-target criterion is 24×24 CSS pixels with specified exceptions, including spacing and inline content; a 15px icon alone does not establish nonconformance. Aim for comfortably sized controls and verify the complete target. [W3C contrast guidance](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html); [W3C target-size guidance](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html).

## 5. Copy inventory for the first revision

These are proposed product strings. Check dynamic state before using any example number. The terminology changes should apply consistently to the UI, Guide, progress messages, and exports.

| Current text | Proposed text or treatment | Location / reason |
|---|---|---|
| What the material shows | Project summary | Project and record; normal heading |
| What this may mean, so far | Possible interpretation | Keep separate from summary and retain substantive uncertainty |
| What the project adds up to | Project summary | Stable heading in empty and populated states |
| What the reading found | Material summary | Material page; identify the object |
| What this is | Material overview | Label the provisional structural description separately |
| Interpretive account | Theme summary | Theme page; explain its interpretive nature where useful |
| What has pulled against this definition | Evidence that challenges this definition | Frozen-theme notes |
| Every theme two materials carry | Themes with claims in at least 2 materials | Scope label; see F1 for the complete control |
| The themes that could open | Themes with claims in at least {threshold} of {total} {units} | Explain automatic status changes separately |
| Fold themes that define one pattern | Merge overlapping themes | Distinguish merging data from collapsing a section |
| Written over all 8 materials | Based on the analysis of all 8 materials | Distinguish analysis inputs from every claim occurring everywhere |
| claims rest on 106 of 532 passages | Claims cite 106 of 532 passages | Coverage is citation use, not percent of material understood |
| 3 set aside as not carried by their passages | 3 claims excluded because their cited passages did not support them | Name what was excluded |
| The passage carries part of this | Partially supported: [reason] | All claim views |
| Only passages no claim rests on yet | Passages not cited by any claim | Distinguish uncited passages from uncoded passages |
| Promote | Add to project themes | State the result; update help consistently |
| Freeze / Unfreeze | Lock definition / Unlock definition | Explain that new material is still analysed against it |
| Open | Definition can change | Theme status; “open” is already a navigation verb |
| sparse · 2 claims | 2 claims | If the threshold matters, explain it explicitly; do not equate count with quality |
| Reading record | Analysis record | Reserve “Source text” for the original material |
| Open full record / Verbatim record | View source text / Source text | On material page; avoid confusing this with the project record |
| Begin a reading / Your work / Doubt | Delete | Decorative eyebrows |
| Fold / Show | Collapse / Expand | If explicit disclosure labels are needed |
| Research actions | Use specific actions: Check a claim; Revise theme analysis; Analysis details | Avoid hiding useful actions behind a category users must decode |
| Read exploratively | Analyse each material independently | Explain that codes are compared with the project afterwards |
| Built iteratively | Analyse using existing project codes | Explain that the framework can develop; it is not necessarily fixed |
| Structure · Angles · Coding · Synthesis | Identify structure · Plan analysis · Assign codes · Generate analysis | Proposed step labels; expand the last step's contents in details |
| Nothing brings it back | You cannot restore this material in Aperture | Use only where verified; state what removal affects and whether recovery exists |

The research focus appears optional in the creation form, while the empty state says “Begin with a research question.” Label it **Research question or focus (optional)** if that is the intended behavior, and explain the default when it is blank.

## 6. Vocabulary and editorial rules

Assume the user may know qualitative research but has never used Aperture. Keep useful research terms and define their application here:

| Term | First-use explanation |
|---|---|
| Material | One uploaded file or one pasted text item. It may contain multiple speakers or respondents. |
| Case | A grouping chosen by the researcher, such as a participant or organization. Ungrouped materials count separately. |
| Code | A label assigned to a passage during analysis. |
| Theme | A named pattern used to group related codes and claims. Candidate/project status is separate from how many materials contain claims. |
| Claim | A statement generated from a source passage, shown with a quotation and any support qualification. |
| Passage | A numbered segment of source text that can be opened from a citation. |

Use **all materials in this project** when “corpus” adds no precision. Choose **summary** consistently in controls rather than alternating between account, synthesis, reading, and write-up. Do not rename stored fields merely to change the interface vocabulary.

For every control, answer: **What happens? To which item? Does it start now? What else changes?** Put consequences beside the action. For example, feedback on a material summary can also update theme summaries and the project summary; “Your words guide the next revision” is insufficient.

Delete text that only announces the text to come. Replace abstract verbs with concrete relationships. Use ordinary complete sentences, without manufactured drama, flattery, or a persistent “not X, but Y” rhythm. Preserve comparisons that prevent a real error, particularly searched versus unsearched material and evidence versus interpretation.

Keep uncertainty specific: what was checked, which evidence is partial, what has not been assessed. Removing every hedge would make this research tool worse. Similarly, familiar fonts, em dashes, and serif headings are not defects by themselves.

The current `_BANNED` vocabulary in `app/context.py` and related tests blocks some internal jargon, but permits the confusing metaphors quoted throughout this review. Some bans even reach markup strings rather than just visible copy. **Inference:** this may encourage indirect substitutes instead of understandable explanations. Replace this as the primary quality gate with a positive vocabulary and task-comprehension checks. Retain narrow checks for genuinely unsuitable visible strings. Leave source quotations, researcher text, and identifiers untouched.

## 7. Generated analysis needs a separate editing pass

Changing template labels will not change already-generated summaries or future model prose. The live overview contains phrases such as “The corpus narrates,” “the crossing survives as fragments,” and “What one theme does to another matters.” These may conceal the specific observation behind an abstract subject or a sentence that adds no information.

`app/prompts/project.md` uses the same metaphors as the UI and explicitly asks what themes “do to another” and what “holds them together.” This is a plausible source of stylistic imitation, not a proven causal attribution.

Revise the relevant generation instructions to request named actors or materials, concrete relationships, readable paragraphs, and bounded statements about evidence. Keep the summary/interpretation distinction, source coverage rules, and citation validation. Give the model examples of good analytical prose rather than only a list of banned words.

Illustrative style change:

> “The crossing survives as fragments — rough water, mattresses — while stretches vanish.”
>
> “Some interviewees recall details of the crossing, such as rough water and mattresses, but cannot recall other parts of the journey.”

This demonstrates clearer syntax, not a verified replacement finding. Check the cited passages and preserve their coverage before accepting a rewrite. Never use a cosmetic “humanizing” pass that invents specificity, deletes qualifications, alters quotations, or detaches citations from the statements they support. Do not regenerate existing project analyses silently as part of a frontend change.

## 8. Implementation sequence and acceptance

1. **Correct meaning first:** comparison scope and consequences, assessment states, promotion policy, candidate labels, full-operation estimates, and partial-support notes.
2. **Fix Help navigation:** one stable entry point, contextual answers, return path, retained state, narrow-screen project navigation, and stable links to existing topics.
3. **Revise authored copy:** use the inventory above, remove redundant eyebrows, align terminology across templates, context-generated strings, progress messages, Guide, and exports.
4. **Adjust hierarchy:** make primary actions and materials accessible near the top; shorten default summaries; reduce repeated theme introductions; improve helper-text legibility and interaction targets.
5. **Revise generation style separately:** preserve evidence contracts and evaluate fresh outputs before applying the new instructions broadly.

Use a small set of meaningful checks rather than snapshot tests that merely freeze the new prose:

- A first-time user can explain both comparison scopes, automatic promotion if retained, and the affected summaries without opening developer documentation.
- Candidate themes appearing in one and several materials have correct labels. Repeat with multiple files grouped into one case and with an odd number of counting units.
- All five no-count states can be understood without hovering. The same partially supported claim retains its warning in every view and applicable export.
- Every existing Guide anchor remains valid or has a deliberate compatible destination. Test Help → two topics → return, including an unsent comment and selected source passage.
- At 390px, 768px, and desktop widths, users can find Help, Materials, Themes, and the analysis record. Test 200% zoom, keyboard focus, matrix scrolling, and readable descriptions.
- Empty, queued, running, failed, stopped, stale, and read-only states explain what happened and offer only appropriate actions. “Fully read” must not imply exhaustive analysis when processing completion is the fact being reported.
- A generated summary still has valid supporting citations and preserves partial support, limited search scope, and differences between materials after the style revision.

For a quick human review, ask a researcher unfamiliar with Aperture to add a material, explain a candidate theme, inspect a no-count cell, and open Help and return. Record where they hesitate or mispredict an action. Treat observed misunderstandings as defects even if a vocabulary check passes.

**Requested builder deliverable:** An updated interface and Guide with a short before/after copy inventory, screenshots of desktop and narrow-screen task flows, and results for the checks above. Identify any behavior-policy decisions explicitly. Keep the first pass focused on comprehension, navigation, and accurate state presentation.
