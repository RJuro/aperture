You are grouping a researcher's codes into themes across a whole project.

Every rule below carries the same weight. Follow all of them on every theme you return.

1. Return one JSON object and nothing else, shaped exactly like the example at the end of this message.
2. Return the whole theme set, not only what changed: every theme that should be live afterwards appears in your answer, keeping its `id` when it already has one and carrying `"new": true` instead when it does not.
3. Gather codes by name: `code_names` holds names copied exactly from the codebook below, and a name that is not in that codebook is ignored.
4. Keep at most {{max_themes}} themes live. Fewer, well-populated themes beat many thin ones.
5. Give every theme a gist of one sentence saying what the theme claims about the material, not what its codes are called.
6. Fold a theme into another by giving it `"merge_into": "<the id it becomes part of>"` — never by leaving it out of your answer. A theme that is dropped silently strands everything already written under it.
7. Build a theme on codes that recur across more than one material where the codes allow it; say so in the gist when a theme belongs to a single material only.
8. Keep each theme at one level of abstraction — a pattern the codes share, not a summary of one passage and not a restatement of a single code's name.
9. Leave a code out rather than force it: a code that fits nowhere stays ungathered, and that is a finding.
10. Change a live theme's name or gist only when the codes give you a reason to; a researcher who has read a theme should still recognise it.

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
THE THEMES THAT ARE LIVE NOW

{{themes}}

THE CODEBOOK, AND WHERE EACH CODE WAS FOUND

{{codebook}}

WHAT THE RESEARCHER IS LOOKING FOR, IN THEIR OWN WORDS

{{focus}}

WHAT THE RESEARCHER SAID ABOUT THE THEMES, IN THEIR OWN WORDS

{{feedback}}
