# The prompts, compiled on real data — after the fifth law

Files `1-frame.md` … `9-check.md` are the exact system and user messages the redesigned engine
sends, slot-filled from the live database, in run order. `5-thread` is new: one theme's line
through one material is now its own call, and `6-doc` is the summary written afterwards over
those lines.

## What the review found, and what was done

| Finding | Done |
|---|---|
| The brief carried findings into READ, DOC and ACCOUNT as "what this corpus is like" | Removed from all three. DOC now writes *questions the material raised and did not answer*; only the ideation step reads them |
| Theme gists were 40-word findings about two interviews, handed to DOC as definitions | THEMES' gist rule is definitional — true if fifty more materials arrived, never a comparison or a location. PROJECT no longer rewrites gists |
| Angles were shaped by the focus, READ by the angles | Angles no longer see the focus. They are the counter-focus: where to look, from the material alone |
| THEMES saw code labels only, never the material | THEMES sees the material it has just been handed with its codes marked by passage |
| DOC wrote six lines + summary + brief + people in one answer | One call per line (`thread.md`); the summary (`doc.md`) is written over lines that exist |
| PROJECT read every claim in every material, ignoring the accounts | PROJECT reads the accounts and material summaries, cites the claims they rest on |
| Twelve new codes per material, whatever its length | One new code per dozen passages, fifteen to fifty |
| Themes rewritten in place, no history | `theme_history` keeps every prior name, gist and code set |

## The law, as written into PLAN.md §3

A prompt template is universal. A slot may hold only the material, validated structure, or the
researcher's verbatim words — never prose the system wrote about the corpus. The one
self-prompting slot carries questions, not findings. Conclusions flow up; only questions flow
forward. A gist defines; an account concludes.

## Postscript: the gist that would not stop concluding

The definitional rule alone did not hold. Shown material titles, THEMES wrote *"absent from the
bakery interview"*; shown counts instead, it wrote *"found in one of two materials"*. Three rules
at the top of the prompt did not stop it — and one rule lower down, inherited from the first draft,
actually instructed it. The fix that held was not a fourth rule: THEMES is now shown names and
definitions only, nothing about where or how often. Re-run at two materials, 0 of 9 gists located
themselves.

The lesson generalises and is worth more than the fix: **when a slot keeps leaking a conclusion,
remove the information rather than add a rule.** A fact the model never sees cannot leak; a rule
it must obey can.
