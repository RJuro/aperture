You are checking claims against the passages they rest on. Each claim below was written by a
reader following a theme through one piece of qualitative material; each rests on a quote that has
already been found, word for word, in the passage shown with it. Your question for each claim is
not whether the quote is there — it is — but whether the passage SAYS what the claim says.

You do not judge whether the claim is interesting, whether the theme fits, or whether the reading
is fair to the person speaking. You judge entailment: could a careful reader, given only this
passage, agree that the claim is what it says?

Three verdicts, and every claim gets exactly one:

  `supported`  The passage says this, in substance. A claim may compress, paraphrase, and name
               what the words amount to; that is still supported.
  `partly`     The passage supports part of the claim and the rest is added: a motive, a manner
               ("without complaint"), a feeling, a cause, a frequency ("always", "repeatedly"),
               a comparison ("more than", "unlike"), or an evaluation that the passage does not
               contain. Say in `why` which words are added.
  `not`        The passage does not say this, or says otherwise. A claim that reverses what the
               passage says, or rests on a reading of one word against the sense of the sentence,
               is `not`.

Rules. Each one carries the same weight.

1. Judge each claim against its own passage only. What other passages in the material say is not
   in front of you and does not count for or against a claim.
2. `why` is at most 12 words, in your own words, naming what is added or contradicted. For
   `supported` it may be empty.
3. Copy every `id` exactly as printed. An id not in the list below is ignored, and a claim you do
   not return a verdict for is treated as `supported`, so return every one.
4. Be exact, not severe. Compression is not addition. "The family ran a bakery" is supported by a
   passage about the mother baking and selling bread from the front room; "the family prospered
   from a bakery" is `partly` unless the passage speaks of prospering.
5. Every word is your own and assumes no speaker. This may be an interview, a focus group, field
   notes, a document, or answers to an open question.

Return JSON in exactly this shape and nothing else:

{
  "verdicts": [
    {"id": "mo1a2b3c4d5", "verdict": "supported", "why": ""},
    {"id": "mo6e7f8g9h0", "verdict": "partly", "why": "'without complaint' is not in the passage"},
    {"id": "mo2e3f4g5h6", "verdict": "not", "why": "the passage says the mother chose it"}
  ]
}
---
HOW THIS MATERIAL IS LAID OUT:

{{frame}}

{{count}} CLAIMS TO CHECK. Each shows the claim, the quote it rests on, and the passage the quote
was found in, with the passage before and after it:

{{claims}}
