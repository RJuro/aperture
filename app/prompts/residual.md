You are reading what a coding of one piece of qualitative material did NOT mark: the passages no
code touched. Lines have already been written through the marked passages under the project's
themes. Your question is whether the unmarked passages hold anything those lines missed — and if
they do not, to say so plainly.

Six rules, equal weight, each checked.

1. Return `additions`: each is one moment the lines missed, under ONE existing theme named by its
   `id` below — a `claim` in your own words, an `anchor` copied EXACTLY from the passages below, at
   most 12 words, and the `sid` printed at the start of its line. A quote you cannot copy exactly
   is a claim you must not make; every quote is searched for afterwards and a moment whose quote is
   not there is thrown away.
2. A claim says no more than its passage says: no motive, manner, feeling, cause, frequency,
   evaluation or comparison the passage does not contain; a hedge stays a hedge. Every claim is
   checked against its passage afterwards.
3. Add a moment only where the passage plainly carries the theme's definition. A passage that
   would need the definition bent to fit is not an addition. Nothing here rewards finding things;
   an empty list is a finding.
4. Return `none_for`: the ids of the themes below for which the unmarked passages hold nothing —
   every theme you did not add to appears here, so the researcher can read the absence as searched.
5. `note` is at most 40 words on what the unmarked passages are mostly about, if they are about
   anything the themes do not cover. Your own words; no quotes; or empty.
6. Every word outside the quotes is your own and assumes no speaker. Interview, focus group,
   field notes, document or open answers — all ordinary here.

Return JSON in exactly this shape and nothing else:

{
  "additions": [
    {"theme": "t9f2c1", "claim": "The stall, not the land, is what fed them.",
     "anchor": "we had a stall in the market", "sid": "S118"}
  ],
  "none_for": ["t44ab0", "t0aa41"],
  "note": "Mostly the interviewer's questions about dates, and a passage on the weather at sea."
}
---
THE THEMES, each with its id and definition:

{{themes}}

WHAT THE READING ALREADY FOUND in this material — its account in brief, so you do not repeat it:

{{memo}}

THE UNMARKED PASSAGES. Each line starts with the id a quote from that line must cite:

{{unmarked}}
