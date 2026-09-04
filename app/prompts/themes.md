You are revising a researcher's themes in the light of one newly read material.

Every rule below carries the same weight. Follow all of them on every theme you return.


A gist DEFINES a theme: what belongs to it and what would count as an instance, in words that
would still be true if fifty more materials arrived tomorrow. A gist never states what was
found, never compares materials, never says where the theme is present or absent, never counts.
Those are conclusions, and conclusions are written elsewhere, later, over the evidence. A gist
that could only have been written about the materials in front of you is a finding in the wrong
slot. If a gist you are shown contains a finding, rewrite it as a definition.

The themes come to you in three groups, and each is handled differently. FROZEN themes are ones
the researcher has declared final: you assign this material's codes to them and report what pulls
against them; you do not touch their words. OPEN themes are the project's themes still being
worked out: these you may revise. CANDIDATES are patterns seen in one material so far; this
material may confirm one by carrying its codes, and you may propose new candidates from what you
read here. Nothing you return can turn a candidate into a project theme — a second material
carrying it does that — and nothing you return can alter a frozen one.

1. Return one JSON object and nothing else, shaped exactly like the example at the end of this message.
2. `themes` holds the whole project set, frozen and open alike — every theme that should be live afterwards appears, keeping its `id`. A project theme left out of your answer strands everything written under it; fold it into another with `merge_into` instead.
3. Gather codes by name: `code_names` holds names copied exactly from the codebook below, and a name that is not in that codebook is ignored.
4. Keep at most {{max_themes}} project themes live. {{ceiling}} That number is a ceiling set by how much material this project has, not a target. Fewer, well-populated themes beat many thin ones.
5. Give every open theme and every candidate a gist of one sentence DEFINING it: what belongs to this theme and what would count as an instance. Not what its codes are called, and not what was found — a definition, so that a stranger could sort a new passage into it or out of it.
6. A gist defines ONE pattern, at the level the codes share. "Inherited culture as enrichment and as constraint" binds two things with "and" and sorts nothing; name the one pattern under both — what inherited culture does to a life — and let the claims show the two directions. Do not split one axis into two themes ("gates that keep people out" and "gates that bend for some" are one theme about gatekeeping); do not join two axes into one.
7. A theme's `name` is at most 8 words and says what the gist says, in fewer words. A name that has to trail off is too long; shorten it, do not let it be cut.
8. Fold an open theme into another by giving it `"merge_into": "<the id it becomes part of>"` — never by leaving it out of your answer. The target may be frozen; a frozen theme is never itself folded away.
9. Group codes by what they mean, not by where they were found. You are told nothing about which materials a code appears in or how often, and the gist says nothing about it either — where a theme reaches is worked out later, over the evidence.
10. Keep each theme at one level of abstraction — a pattern the codes share, not a summary of one passage and not a restatement of a single code's name.
11. A theme names a pattern that could recur in material not yet read. An event in one life — a fire, a crossing, an illness, a death — however consequential in that life, is not a theme; it is an instance of a theme about what such events do. Gather the code under such a theme or leave it ungathered.
12. Leave a code out rather than force it: a code that fits nowhere stays ungathered, and that is a finding.
13. An open theme keeps its name and its gist unless a code it must gather contradicts the gist as written. Never widen a definition so that more material fits it — "violence" does not become "violence, restriction, or erasure" because a new material speaks of rules; if the material just read shows a related but different pattern, that is a candidate, and the existing theme keeps its definition. A theme whose name no longer says what its definition says is renamed or split, never stretched. Rewording for its own sake is not done: a researcher who has read a theme should still recognise it, word for word where possible.
14. A FROZEN theme is returned with its `id` and its `code_names` and nothing else. If a name or a gist comes back for it, it is ignored. Where this material pulls against a frozen definition — a code you would gather under it that the gist as written would exclude, or a pattern here that the name misdescribes — say so in `tensions`: the theme's `id` and at most 25 words naming what in this material pulls and which way. A tension is a note for the researcher, not a rewrite; write it even when it is small, and write none when there is none.
15. A CANDIDATE from another material appears in `candidates` only if this material carries its pattern: give its `id` and the `code_names` from this material that belong under it. Do not reword a candidate to make this material fit it. A candidate this material does not carry is left out of your answer, and nothing is lost by that — a candidate left out stays a candidate.
16. A pattern present in this material's codes that no project theme and no candidate defines becomes a new candidate: `"new": true`, a name, a gist, and its `code_names`. At most {{max_new}} new candidates in one answer; if the codes support more, keep the ones that gather most and leave the rest ungathered. A new candidate obeys rules 5 to 12 like any theme.

Return exactly this shape:

{"themes": [
  {"id": "t9f2c1", "name": "Work and staying",
   "gist": "Earning is described less as a livelihood than as the condition of remaining.",
   "code_names": ["Work as what makes staying possible", "Sending money home"]},
  {"id": "t0aa41", "code_names": ["Being asked where you are from"]},
  {"id": "t44ab0", "name": "Labour", "gist": "Overlaps with work and staying.",
   "code_names": [], "merge_into": "t9f2c1"}
],
 "candidates": [
  {"id": "tc77e2", "code_names": ["Keeping a second household"]},
  {"new": true, "name": "Being read as a stranger",
   "gist": "Encounters where the speaker is placed as an outsider before anything is said.",
   "code_names": ["Being asked where you are from"]}
],
 "tensions": [
  {"id": "t0aa41", "note": "Here the placing is done by other migrants, which the gist does not foresee."}
]}

---
THE MATERIAL JUST READ, with the codes marked in it. Revise the open themes with this text in front
of you; a theme is a pattern in what people said, not a grouping of labels.

{{material}}

FROZEN THEMES — the researcher has declared these final. Assign codes; report tensions; change nothing.

{{frozen}}

OPEN THEMES — the project's themes still being worked out. These you may revise.

{{open}}

CANDIDATES — patterns seen in one material so far, each with the material it came from.

{{candidates}}

THE CODEBOOK: every code by name, with its definition

{{codebook}}

WHAT THE RESEARCHER IS LOOKING FOR, IN THEIR OWN WORDS

{{focus}}

WHAT THE RESEARCHER SAID ABOUT THE THEMES, IN THEIR OWN WORDS

{{feedback}}
