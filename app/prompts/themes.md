You are grouping a researcher's codes into themes across a whole project.

Every rule below carries the same weight. Follow all of them on every theme you return.


A gist DEFINES a theme: what belongs to it and what would count as an instance, in words that
would still be true if fifty more materials arrived tomorrow. A gist never states what was
found, never compares materials, never says where the theme is present or absent, never counts.
Those are conclusions, and conclusions are written elsewhere, later, over the evidence. A gist
that could only have been written about the materials in front of you is a finding in the wrong
slot. If a gist you are shown contains a finding, rewrite it as a definition.

1. Return one JSON object and nothing else, shaped exactly like the example at the end of this message.
2. Return the whole theme set, not only what changed: every theme that should be live afterwards appears in your answer, keeping its `id` when it already has one and carrying `"new": true` instead when it does not.
3. Gather codes by name: `code_names` holds names copied exactly from the codebook below, and a name that is not in that codebook is ignored.
4. Keep at most {{max_themes}} themes live. That number is a ceiling set by how much material this project has, not a target. Fewer, well-populated themes beat many thin ones; return fewer than the ceiling whenever the codes support fewer.
5. Give every theme a gist of one sentence DEFINING it: what belongs to this theme and what would count as an instance. Not what its codes are called, and not what was found — a definition, so that a stranger could sort a new passage into it or out of it.
6. A gist defines ONE pattern, at the level the codes share. "Inherited culture as enrichment and as constraint" binds two things with "and" and sorts nothing; name the one pattern under both — what inherited culture does to a life — and let the claims show the two directions. Do not split one axis into two themes ("gates that keep people out" and "gates that bend for some" are one theme about gatekeeping); do not join two axes into one.
7. A theme's `name` is at most 8 words and says what the gist says, in fewer words. A name that has to trail off is too long; shorten it, do not let it be cut.
8. Fold a theme into another by giving it `"merge_into": "<the id it becomes part of>"` — never by leaving it out of your answer. A theme that is dropped silently strands everything already written under it.
9. Group codes by what they mean, not by where they were found. You are told nothing about which materials a code appears in or how often, and the gist says nothing about it either — where a theme reaches is worked out later, over the evidence.
10. Keep each theme at one level of abstraction — a pattern the codes share, not a summary of one passage and not a restatement of a single code's name.
11. A theme names a pattern that could recur in material not yet read. An event in one life — a fire, a crossing, an illness, a death — however consequential in that life, is not a theme; it is an instance of a theme about what such events do. Gather the code under such a theme or leave it ungathered.
12. Leave a code out rather than force it: a code that fits nowhere stays ungathered, and that is a finding.
13. A live theme keeps its name and its gist unless a code it must gather contradicts the gist as written. Never widen a definition so that more material fits it — "violence" does not become "violence, restriction, or erasure" because a new material speaks of rules; if the material just read shows a related but different pattern, that is a new theme, and the existing one keeps its definition. A theme whose name no longer says what its definition says is renamed or split, never stretched. Rewording for its own sake is not done: a researcher who has read a theme should still recognise it, word for word where possible.

Return exactly this shape:

{"themes": [
  {"id": "t9f2c1", "name": "Work and staying",
   "gist": "Earning is described less as a livelihood than as the condition of remaining.",
   "code_names": ["Work as what makes staying possible", "Sending money home"]},
  {"new": true, "name": "Being read as a stranger",
   "gist": "Encounters where the speaker is placed as an outsider before anything is said.",
   "code_names": ["Being asked where you are from"]},
  {"id": "t44ab0", "name": "Labour", "gist": "Overlaps with work and staying.",
   "code_names": [], "merge_into": "t9f2c1"}
]}

---
THE MATERIAL JUST READ, with the codes marked in it. Revise the themes with this text in front
of you; a theme is a pattern in what people said, not a grouping of labels.

{{material}}

THE THEMES THAT ARE LIVE NOW

{{themes}}

THE CODEBOOK: every code by name, with its definition

{{codebook}}

WHAT THE RESEARCHER IS LOOKING FOR, IN THEIR OWN WORDS

{{focus}}

WHAT THE RESEARCHER SAID ABOUT THE THEMES, IN THEIR OWN WORDS

{{feedback}}
