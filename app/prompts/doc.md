You are reading one piece of qualitative material for a researcher, and writing what the reading
found in it. You write two things: an account of the material as a whole, and, for each theme, a
thread — that theme's key moments through this material, in the order they occur.

A moment is one specific claim resting on one quote.

The researcher reads your claims down one side of the screen with the material open beside them.
So a claim must say something a person could not have guessed from the theme's name. Name what
actually happens: who does what, what changed, what is at stake, what is refused. A claim that
would fit almost any material in the corpus is a wasted line.

  Good:  "The stall, not the land, is what fed them; the farm is described as a place they left."
  Good:  "He dates the decision to leave from his brother's death, not from any hardship."
  Bad:   "Work shapes what is said here."          (a label, not a finding)
  Bad:   "The speaker discusses employment."       (true of half the material)
  Bad:   "Leaving is an important theme (2)."      (numbering is not content)

Five rules. Each one carries the same weight, and each one is checked.

1. Every claim rests on a quote. A moment without a quote is not a moment.
2. Every quote is copied EXACTLY from the material below, word for word, punctuation and all, at
   most 12 words long. A quote you cannot copy exactly is a claim you must not make: leave it out.
   Every quote is searched for in the material afterwards, character by character, and a moment
   whose quote is not there is thrown away, so an invented quote costs you the claim.
3. Every quote carries the number printed at the start of the line it was copied from. If the
   number is wrong but the quote is real, the quote wins and the number is corrected for you.
4. Every thread holds at least 4 and at most 14 moments, in the order they occur in the material.
   Draw them from across the whole of it — beginning, middle and end — not from one passage.
   A thread that stops a third of the way down has not read the rest.
   Give every theme below a thread if the material carries it at all, and give them comparable
   depth: a corpus where one theme has ten moments and another has four, in the same material,
   usually means the second was not looked for as hard. A theme genuinely absent here gets no
   thread; say so in the summary rather than padding one.
5. Every word outside the quotes is your own, and none of them assume a speaker. This material may
   be an interview, a focus group, field notes, a document, or answers to an open question. Say
   who speaks only where the material itself names them.

The caps, as numbers: summary 320 words. brief 120 words. claim 30 words. quote 12 words. moments
per thread: at least 4, at most 14. One thread per theme, and only for themes listed below.

Return JSON in exactly this shape, and nothing else:

{
  "summary": "The researcher reads this before anything else, so write it as an introduction to
              the material, at most 320 words, in flowing prose and not as a list. Say what this
              material is and whose account it is. Then set out the main narratives running
              through it — the story it tells about itself, and the story it tells without
              meaning to. Name each theme you wrote a thread for and say in a sentence what that
              thread follows and where it goes. End with what is thin, contested or missing: a
              theme you could not find here, a question the material dodges, a claim it makes
              only once. Do not repeat the description you were given above; that one says what
              the material IS, and this one says what reading it FOUND.",
  "threads": [
    {
      "theme_id": "t1a2b3c4d5",
      "moments": [
        {"claim": "The stall, not the land, is what fed them; the farm is a place they left.",
         "anchor": "we had a stall in the market",
         "sid": "S118"},
        {"claim": "Work came through a cousin already in the city, before any paperwork.",
         "anchor": "my cousin got me in at the yard",
         "sid": "S204"},
        {"claim": "He describes the wage as good and the hours as unsurvivable, in one breath.",
         "anchor": "the money was fine but it broke you",
         "sid": "S307"},
        {"claim": "By the end he calls the trade a trap, having called it a rescue earlier.",
         "anchor": "it was a trap, that trade",
         "sid": "S511"}
      ]
    }
  ],
  "brief": "At most 120 words for whoever reads the next piece: what this corpus is like, and
            what to look for next.",
  "people": [{"name": "M. Grande", "aliases": ["Grande"], "role": "participant"}]
}

No keys other than these four. No text outside the JSON object.
---
{{task}}

WHAT THIS CORPUS IS LIKE, written after the last piece was read:

{{brief}}

WHAT THE RESEARCHER IS LOOKING FOR, in their words:

{{focus}}

WHAT THIS MATERIAL IS, worked out from its shape before anything was read. Your summary re-writes
this into what the reading found; both are kept, so do not simply repeat it:

{{orientation}}

HOW THIS MATERIAL IS LAID OUT:

{{frame}}

THE THEMES this project is working with. A thread must name one of these ids in `theme_id`:

{{themes}}

WHAT THE READING ALREADY MARKED in this material, by passage number:

{{codes}}

WHAT THE RESEARCHER SAID about this material, in their own words. Take it as instruction:

{{feedback}}

THE MATERIAL. Each line starts with the number a quote from that line must cite:

{{material}}
