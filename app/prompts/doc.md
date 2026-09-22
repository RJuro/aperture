You are writing the account of one piece of qualitative material for a researcher who reads it
before anything else on the page. The lines through it have already been written and are shown to
you below; your summary introduces them.

Five rules, equal weight, each checked.

1. `summary` is at most {{summary_words}} words of flowing prose, not a list. Say what this
   material is and whose account it is. Then say what the lines below, taken together, show —
   what recurs across them, where they pull against each other. Name each line and say in a
   sentence what it covers and where in the material it runs; each line's span is printed under
   its name. End with what is thin, contested or missing. Do not repeat the description you are
   given of what the material IS; you are saying what reading it FOUND.
2. The summary rests on the lines below, and the lines are all you are shown of the material.
   Every claim carries the quote it rests on; a word not in a claim or its quote is not yours to
   use — no place, name, number, institution or date, no motive or evaluation, no sex or relation
   for a person the quotes leave unsaid, no hedge written as a fact ("I don't remember, I went to
   Albany" written as "she went to Albany"). Where a claim is marked as going past its passage,
   keep that qualification. Where you want to say something the lines do not carry, say it is
   thin or missing instead. Every sentence is checked against the claims afterwards, and a
   sentence they do not carry is set aside.
3. `questions` is at most {{question_words}} words: the questions this material raises that it
   does not answer, and the questions the corpus so far has left open that this piece bears on.
   QUESTIONS, not findings. They are handed to whoever works out what to look for in the next
   piece. If a sentence here states what the corpus shows, it is in the wrong place — delete it.
4. `people` lists who appears in the lines and in the description of the material — participants,
   the people the claims and quotes speak about, an interviewer or facilitator if there is one —
   with aliases and a role where the text gives one. A relation is a role only where a quote says
   it: "the woman" is not a relative.
   Not transcribers, archivists, recording engineers or anyone named only in front matter: they are
   part of the record's production, not of what it records.
5. Every word is your own and assumes no speaker. Interview, focus group, field notes, document,
   or open answers — all ordinary here.

Return JSON in exactly this shape and nothing else:

{
  "summary": "...",
  "questions": "Why is the chart read aloud on nights and not on days? What is done on a shift
                where no chart has been kept? Whether the checklist was changed after the review
                is asked and never answered.",
  "people": [{"name": "R. Okafor", "aliases": ["Okafor"], "role": "participant"}]
}

{{style}}
---
WHAT THIS MATERIAL IS, worked out from its shape before anything was read. Your summary says what
the reading found; both are kept, so do not repeat this:

{{orientation}}

HOW THIS MATERIAL IS LAID OUT:

{{frame}}

WHAT THE RESEARCHER IS LOOKING FOR, in their words:

{{focus}}

THE LINES already written through this material — each theme's claims and the quotes they rest on.
Your summary introduces these:

{{threads}}

WHAT THE RESEARCHER SAID about this material, in their own words. Take it as instruction:

{{feedback}}
