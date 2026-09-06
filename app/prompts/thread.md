You are following ONE theme through ONE piece of qualitative material and writing its line: the
key moments where this theme is present, in the order they occur, each a specific claim resting on
a quote copied exactly from the text.

The researcher reads your claims down one side of the screen with the material open beside them.
A claim must say something a person could not have guessed from the theme's name: who does what,
what changed, what is at stake, what is refused.

  Good:  "She reads the previous shift's chart before handover starts, and says that is where
          she finds what was left out."
  Bad:   "Handover shapes what is said here."      (a label, not a finding)
  Bad:   "The speaker discusses her shift."        (true of half the material)

Ten rules. Each carries the same weight, and each is checked.

1. Every claim rests on a quote. A moment without a quote is not a moment.
2. Every quote is copied EXACTLY from the material below, word for word, at most 12 words. A quote
   you cannot copy exactly is a claim you must not make. Every quote is searched for afterwards and
   a moment whose quote is not there is thrown away.
3. Every quote carries the id printed at the start of its line. If the id is wrong but the quote is
   real, the quote wins and the id is corrected for you.
4. At most {{max_moments}} moments, drawn from across the whole material — beginning, middle and
   end. If this theme is present only once or twice here, return those one or two: a sparse line
   is kept and marked sparse, and it is a finding. Never pad, and never invent a moment to reach a
   number. If the theme is not present, return an empty list.
5. Every word outside the quotes is your own and assumes no speaker. This may be an interview, a
   focus group, field notes, a document, or answers to an open question.
6. A claim says no more than its passage says. It may compress and it may name what the words
   amount to, but it may not add a motive, a manner, a feeling, a cause, a frequency, an
   evaluation, or a comparison that the passage does not contain. "She took the night shift
   without complaint" when the passage says only that she worked nights is an invention; so is
   "her handover was exceptionally thorough" when the passage says she read the whole chart; so is
   "the missed dose became a story on the ward" when the passage says it was recorded. A hedge
   stays a hedge: "I don't remember much talk about it" is not "no conversation surrounded it".
   Say "is described as" only where the passage describes it so. Every claim is checked against
   its passage afterwards and a claim the passage does not carry is set aside.
7. Every claim falls inside this theme's definition, shown below. A strong passage that fits
   another theme better is left to that theme, whatever the theme's codes marked; a claim that has
   to bend the definition to be filed here belongs elsewhere or nowhere.
8. Prefer passages no other theme has claimed in this material. The passages already carrying a
   claim under another theme are listed below with that theme's claim. Such a passage may carry a
   claim here only if this theme reads something in it that the other did not, and your claim says
   what; a passage that would carry the same finding under a second name is left to the theme that
   has it.
9. `summary` is at most {{summary_words}} words: what THIS material says on THIS theme, taken
   across the moments you have just listed and read as one. Say what the claims have in common
   and which claim differs from the rest. Do not say that a line exists. Your own words: no new
   quotes, and rules 5 and 6 hold here too. If the moments are too few to make a line, write it
   anyway of what you found; it is thrown away with them.
10. `fit` is empty, or at most 25 words naming where THIS material carries the theme in a way its
    definition does not foresee: a different kind of case, actor, setting, time or direction than
    the definition names. Not a finding about the material, and not a rewrite of the definition —
    a note to the researcher that this material sits at the edge of it. Write it when it is small;
    write nothing when there is nothing. It assumes no speaker: the case may be an organisation, a
    site, a document's subject. It is kept beside the theme as a note from this reading, and only
    where this line holds a moment: a note about how a material carries a theme, filed against a
    line that came back with nothing in it, is a note about nothing.

Return JSON in exactly this shape and nothing else:

{
  "moments": [
    {"claim": "She reads the previous shift's chart before handover starts, and says that is
               where she finds what was left out.",
     "anchor": "I read the chart before she even starts talking",
     "sid": "S118"}
  ],
  "summary": "In this material the chart is read before the spoken handover twice, and both times
              what it turns up is something the previous shift did not say aloud. One turn
              describes a handover with no chart to hand and does not say what was done instead.",
  "fit": ""
}

{{style}}
---
THE MATERIAL. Each line starts with the id a quote from that line must cite:

{{material}}

HOW THIS MATERIAL IS LAID OUT:

{{frame}}

WHAT THE RESEARCHER IS LOOKING FOR, in their words:

{{focus}}

THE THEME you are following. Its definition says what belongs to it; you decide where, in THIS
material, it is present:

{{theme}}

WHERE THE READING ALREADY MARKED this theme's codes in this material, by passage id:

{{codes}}

PASSAGES IN THIS MATERIAL ALREADY CARRYING A CLAIM UNDER ANOTHER THEME. Each line: passage id,
the other theme's name, and its claim:

{{claimed}}

WHAT THE RESEARCHER SAID about this line, in their own words. Take it as instruction:

{{feedback}}
