You are following ONE theme through ONE piece of qualitative material and writing its line: the
key moments where this theme is present, in the order they occur, each a specific claim resting on
a quote copied exactly from the text.

The researcher reads your claims down one side of the screen with the material open beside them.
A claim must say something a person could not have guessed from the theme's name: who does what,
what changed, what is at stake, what is refused.

  Good:  "The stall, not the land, is what fed them; the farm is described as a place they left."
  Bad:   "Work shapes what is said here."          (a label, not a finding)
  Bad:   "The speaker discusses employment."       (true of half the material)

Eight rules. Each carries the same weight, and each is checked.

1. Every claim rests on a quote. A moment without a quote is not a moment.
2. Every quote is copied EXACTLY from the material below, word for word, at most 12 words. A quote
   you cannot copy exactly is a claim you must not make. Every quote is searched for afterwards and
   a moment whose quote is not there is thrown away.
3. Every quote carries the id printed at the start of its line. If the id is wrong but the quote is
   real, the quote wins and the id is corrected for you.
4. Between {{min_moments}} and {{max_moments}} moments, drawn from across the whole material —
   beginning, middle and end. If this theme is genuinely present fewer than {{min_moments}} times
   here, return fewer and the line will be set aside with that reason; never pad.
5. Every word outside the quotes is your own and assumes no speaker. This may be an interview, a
   focus group, field notes, a document, or answers to an open question.
6. A claim says no more than its passage says. It may compress and it may name what the words
   amount to, but it may not add a motive, a manner, a feeling, a cause, a frequency, or a
   comparison that the passage does not contain. "He took factory work without complaint" when the
   passage says only that he got a job in a factory is an invention, and so is "she adapted well"
   when the passage says she made others adapt. Every claim is checked against its passage
   afterwards and a claim the passage does not carry is set aside.
7. Prefer passages no other theme has claimed in this material. The passages already carrying a
   claim under another theme are listed below with that theme's claim. Such a passage may carry a
   claim here only if this theme reads something in it that the other did not, and your claim says
   what; a passage that would carry the same finding under a second name is left to the theme that
   has it.
8. `summary` is at most {{summary_words}} words: what THIS material says on THIS theme, taken
   across the moments you have just listed and read as one. Say what the line amounts to — the
   shape of it, what holds and what pulls against it — not that a line exists. Your own words: no
   new quotes, and rules 5 and 6 hold here too. If the moments are too few to make a line, write it
   anyway of what you found; it is thrown away with them.

Return JSON in exactly this shape and nothing else:

{
  "moments": [
    {"claim": "The stall, not the land, is what fed them; the farm is a place they left.",
     "anchor": "we had a stall in the market",
     "sid": "S118"}
  ],
  "summary": "Making a living here is trade rather than land. The farm is named twice and both
              times as somewhere already left; the stall is where the family's days, and the
              children's labour, are placed."
}
---
THE THEME you are following. Its definition says what belongs to it; you decide where, in THIS
material, it is present:

{{theme}}

WHERE THE READING ALREADY MARKED this theme's codes in this material, by passage id:

{{codes}}

PASSAGES IN THIS MATERIAL ALREADY CARRYING A CLAIM UNDER ANOTHER THEME. Each line: passage id,
the other theme's name, and its claim:

{{claimed}}

WHAT THE RESEARCHER IS LOOKING FOR, in their words:

{{focus}}

HOW THIS MATERIAL IS LAID OUT:

{{frame}}

WHAT THE RESEARCHER SAID about this line, in their own words. Take it as instruction:

{{feedback}}

THE MATERIAL. Each line starts with the id a quote from that line must cite:

{{material}}
