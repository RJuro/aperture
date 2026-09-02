You are writing the account of one piece of qualitative material for a researcher who reads it
before anything else on the page. The lines through it have already been written and are shown to
you below; your summary introduces them.

Four rules, equal weight, each checked.

1. `summary` is at most {{summary_words}} words of flowing prose, not a list. Say what this
   material is and whose account it is. Then set out the main narratives running through it — the
   story it tells about itself and the story it tells without meaning to. Name each line below and
   say in a sentence what it follows and where it goes. End with what is thin, contested or
   missing. Do not repeat the description you are given of what the material IS; you are saying
   what reading it FOUND.
2. `questions` is at most {{question_words}} words: the questions this material raises that it
   does not answer, and the questions the corpus so far has left open that this piece bears on.
   QUESTIONS, not findings. They are handed to whoever works out what to look for in the next
   piece. If a sentence here states what the corpus shows, it is in the wrong place — delete it.
3. `people` lists who is named in this material, with aliases and a role where the text gives one.
4. Every word is your own and assumes no speaker. Interview, focus group, field notes, document,
   or open answers — all ordinary here.

Return JSON in exactly this shape and nothing else:

{
  "summary": "...",
  "questions": "Why does the family choose Trieste rather than Genoa? What happened to the brother
                who stayed? Whether the wage was ever enough is asked and never answered.",
  "people": [{"name": "M. Grande", "aliases": ["Grande"], "role": "participant"}]
}
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

THE MATERIAL:

{{material}}
