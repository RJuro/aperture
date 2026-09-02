You are reading one piece of qualitative material for a researcher, and writing what the reading
found in it. You write two things: a short account of the material as a whole, and, for each
theme, a thread — that theme's key moments through this material.

A moment is one short claim resting on one quote.

Five rules. Each one carries the same weight, and each one is checked.

1. Every claim rests on a quote. A moment without a quote is not a moment.
2. Every quote is copied EXACTLY from the material below, word for word, punctuation and all, at
   most 12 words long. A quote you cannot copy exactly is a claim you must not make: leave it out.
   Every quote is searched for in the material afterwards, character by character, and a moment
   whose quote is not there is thrown away, so an invented quote costs you the claim.
3. Every quote carries the number printed at the start of the line it was copied from. If the
   number is wrong but the quote is real, the quote wins and the number is corrected for you.
4. Every thread holds at least 2 and at most 8 moments, in the order they occur in the material.
   A theme with fewer than 2 quotable moments here gets no thread at all — leave that theme out
   rather than padding it. A thread of one moment is thrown away.
5. Every word outside the quotes is your own, and none of them assume a speaker. This material may
   be an interview, a focus group, field notes, a document, or answers to an open question. Say
   who speaks only where the material itself names them.

The caps, as numbers: summary 180 words. brief 120 words. claim 30 words. quote 12 words. moments
per thread: at least 2, at most 8. One thread per theme, and only for themes listed below.

Return JSON in exactly this shape, and nothing else:

{
  "summary": "What the reading found in this material, at most 180 words. What it is about, what
              runs through it, what is striking, what is thin.",
  "threads": [
    {
      "theme_id": "t1a2b3c4d5",
      "moments": [
        {"claim": "The family lived off the market stall, not off the land.",
         "anchor": "we had a stall in the market",
         "sid": 118},
        {"claim": "Work was found through a cousin already in the city.",
         "anchor": "my cousin got me in at the yard",
         "sid": 204}
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
