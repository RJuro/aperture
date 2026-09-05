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
  `partly`     The passage supports part of the claim and the rest is added. Added means any of:
               a motive ("out of pity"); a manner ("without complaint", "casually"); a feeling;
               a cause; a frequency ("always", "repeatedly", "routinely"); a comparison ("more
               than", "unlike", "exceptional for a woman"); an evaluation or an intensifier
               ("immediate", "explicitly", "deliberately", "a standard that became a family
               anecdote"); a consequence the passage does not state; or a hedge hardened into a
               fact — "I don't remember much talk" read as "there was no conversation", "I think
               she adapted well" read as "she adapted well". Say in `why` which words are added.
  `not`        The passage does not say this, or says otherwise. A claim that reverses what the
               passage says, or rests on a reading of one word against the sense of the sentence,
               is `not`.

Rules. Each one carries the same weight.

1. Judge each claim against its own passage only. What other passages in the material say is not
   in front of you and does not count for or against a claim.
2. `why` is at most 12 words, in your own words, naming what is added or contradicted. For
   `supported` it may be empty.
3. Copy every `id` exactly as printed. An id not in the list below is ignored, and a claim you do
   not return a verdict for is recorded as UNCHECKED — not as supported — and the researcher is
   shown it as a claim nobody ruled on. Return every one.
4. Be exact, not severe. Compression is not addition; naming what the words amount to is not
   addition. "The family ran a bakery" is supported by a passage about the mother baking and
   selling bread from the front room; "the family prospered from a bakery" is `partly` unless the
   passage speaks of prospering. "Finding the town is described as an immediate belonging" is
   supported by "they just felt very much at home" only if the passage carries the immediacy;
   otherwise `partly`, with "immediate" in `why`.
5. Every word is your own and assumes no speaker. This may be an interview, a focus group, field
   notes, a document, or answers to an open question.

Return JSON in exactly this shape and nothing else:

{
  "verdicts": [
    {"id": "mo1a2b3c4d5", "verdict": "supported", "why": ""},
    {"id": "mo6e7f8g9h0", "verdict": "partly", "why": "'without complaint' is not in the passage"},
    {"id": "mo9c8d7e6f5", "verdict": "partly", "why": "'exceptional for a woman' is a comparison the passage does not make"},
    {"id": "mo2e3f4g5h6", "verdict": "not", "why": "the passage says the mother chose it"}
  ]
}
---
HOW THIS MATERIAL IS LAID OUT:

{{frame}}

{{count}} CLAIMS TO CHECK. Each shows the claim, the quote it rests on, and the passage the quote
was found in, with the passage before and after it:

{{claims}}
