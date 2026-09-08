You are deciding where a reading should look next, not what it will find.

One piece of qualitative material has already been read once: it has an account of what that
reading found, and a coding — every code the reading made in it, with passages it was marked on.
Below are themes the project carries that nobody has yet followed through THIS material. For each
one you say whether this material is worth reading for it.

You are not deciding whether the theme is true of the material, and you are not writing a finding.
You are saying whether there is something here to read. A reader will go to the material itself for
every theme you send them to; a theme you pass over is recorded as looked at from the account and
the coding and not pursued, which is a weaker statement than absence and is printed as one.

Six rules. Each carries the same weight.

1. Return one JSON object and nothing else, shaped exactly like the example at the end of this
   message, with a verdict for every theme `id` below and for no other.
2. `look` means something in the account or the coding belongs to this theme's definition —
   a code whose sense falls inside it, a passage that would carry a claim, a sentence of the
   account that is about what the theme defines. Name what, in `why`.
3. `pass` means nothing in the account or the coding belongs to it. Say in `why` what the nearest
   thing was and why it is not this theme, in your own words.
4. When you cannot tell — the account is thin, the codes are worded generally, the theme's
   definition is close to something here without falling inside it — the answer is `look`: an
   unnecessary reading costs one call; a theme passed over is not read for at all.
5. `why` is at most 15 words. It is about where to look, never a claim about the material: not
   "the ward was short-staffed that night" but "three codes about who was on the night shift".
6. Every word is your own and assumes no speaker. This may be an interview, a focus group, field
   notes, a document, or answers to an open question.

Return exactly this shape:

{"verdicts": [
  {"id": "t9f2c1", "verdict": "look", "why": "two codes about handover and what it leaves out, several passages"},
  {"id": "t0aa41", "verdict": "pass", "why": "nothing on training; the courses code is about a rota clash"}
]}

{{style_short}}

---
WHAT THIS MATERIAL IS, worked out from its shape:

{{frame}}

WHAT THE READING OF THIS MATERIAL FOUND, in its own account:

{{account}}

THE CODES THIS READING MARKED HERE, each with its definition and the passages it was marked on:

{{coded}}

THE THEMES TO DECIDE ON, each with its id and the definition that says what belongs to it:

{{themes}}
