You are checking the sentences of a summary against the evidence it was written over. The summary
introduces one piece of qualitative material after it was read; below it are every claim the
reading made in that material, each with the quote it rests on. Your question for each sentence is
whether the claims and quotes CARRY it.

You do not judge whether the summary is well written, complete, or fair. You judge whether each
sentence rests on the evidence shown: could a careful reader, given only these claims and quotes,
agree that the sentence is what they amount to?

Three verdicts, and every sentence gets exactly one:

  `supported`  The claims and quotes carry this, in substance. A summary may compress many claims
               into one sentence, name a pattern across them, and say what is thin or missing among
               them; that is still supported.
  `partly`     Part of the sentence rests on the claims and part is added — a detail no claim or
               quote contains (a place, a name, a number, an institution, a date), a motive, an
               evaluation, or a hedge hardened into a fact. Say in `why` which words are added.
  `not`        Nothing in the claims and quotes carries this sentence, or they say otherwise.

Rules. Each one carries the same weight.

1. Judge each sentence against the claims and quotes below only. The material itself is not in
   front of you; a fact the material may well contain but no claim carries is still added here,
   because the summary is written over the claims.
2. Sentences that say what the material IS — its kind, who speaks, when it was recorded — are
   judged against the description of the material given below, not against the claims.
3. Sentences that name what is thin, contested, missing or unresolved are `supported` when the
   claims show the thinness — one claim where a pattern would need several, or none on a matter
   the sentence names — and `partly` when they assert a specific absence the evidence does not
   show.
4. `why` is at most 12 words, in your own words. For `supported` it may be empty.
5. Copy every `n` exactly as printed. A sentence you return no verdict for is treated as
   `supported`, so return every one.
6. Every word is your own and assumes no speaker. This may be an interview, a focus group, field
   notes, a document, or answers to an open question.

Return JSON in exactly this shape and nothing else:

{
  "verdicts": [
    {"n": 1, "verdict": "supported", "why": ""},
    {"n": 2, "verdict": "partly", "why": "'Ivy League' appears in no claim or quote"},
    {"n": 3, "verdict": "not", "why": "no claim concerns the brother's schooling"}
  ]
}
---
WHAT THIS MATERIAL IS, worked out from its shape:

{{frame}}

THE SUMMARY, sentence by sentence, each numbered:

{{sentences}}

THE CLAIMS THE SUMMARY WAS WRITTEN OVER, each with the quote it rests on and its passage id:

{{claims}}
