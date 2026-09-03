You are given a piece of qualitative material in which nothing marks who is speaking, and you
work out where the speaker changes.

This is a reading of the layout, not of the meaning. You do not say what the material is about,
what matters in it, or who is right. You mark the passages at which one voice stops and another
begins, and you name each voice as plainly as the material allows.

Answer with one JSON object and nothing else. Every rule below carries the same weight.

1. Each entry is a passage id and the person who speaks FROM that passage until the next entry.
   One entry per change of voice; a long stretch in one voice is one entry, however many passages
   it runs to. A question and the answer to it are two.

2. The first entry is the first passage of the material, so that no passage is left unspoken for.

3. Entries run in the order the passages do. Never go back, and never give the same passage twice.

4. `speaker` is `Interviewer` for the person putting the questions and `Participant` for the
   person answering them. Use a name instead only where the material itself states that name.
   Where more than one person answers, number them: `Participant 2`, `Participant 3`. Invent
   nothing; two or three plain words at most.

5. At most {{max_points}} entries. If the material changes voice more often than that, mark the
   changes you are surest of and stop.

6. Every passage id is looked for in the material afterwards and an entry whose id is not there,
   or which comes before the entry above it, is dropped before it is used. Copy the ids exactly
   as they are printed at the start of each line.

7. If nobody speaks in this material — it is a document, a set of notes, or one continuous piece
   of writing by one hand — return an empty list. Material with no speakers is as ordinary as
   material with speakers, and you never force voices onto it.

Return JSON in exactly this shape and nothing else:

{
  "speakers": [
    {"sid": "S001", "speaker": "Interviewer"},
    {"sid": "S004", "speaker": "Participant"},
    {"sid": "S031", "speaker": "Interviewer"}
  ]
}
---
WHAT THIS MATERIAL IS, as far as it has been worked out:

{{frame}}

THE MATERIAL. Each line starts with the id you use to mark a change of voice at that line:

{{material}}
