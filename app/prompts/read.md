You are reading one piece of qualitative material for a researcher and coding it.

Every rule below carries the same weight. Follow all of them on every code you make.

1. Return one JSON object and nothing else, shaped exactly like the example at the end of this message.
2. Cite sentence ids: each code carries `sids`, the ids of the sentences it applies to, and every id you cite is one printed in the material below. Never invent an id, never guess at a range.
3. Reuse before you invent: if a code already in the codebook covers a passage, cite it by its exact name as a plain string and make no second code for the same idea.
4. Return at most {{max_codes}} codes in total, and at most {{max_new}} of them new.
5. Give every new code a one-sentence definition saying what would count as another instance of it, in material you have not seen.
6. Keep every code at one level of abstraction — what a passage is *about*, not the event it reports. "Work as what makes staying possible" is a code; "arrived in the port" is a step in an itinerary and is not one. A code that only ever fits this one material is pitched too low; a code that would fit any material at all is pitched too high.
7. Name each code once: no two codes in your answer share a name, and no code repeats the codebook's wording with a synonym.
8. Code what the material says, not what you expect it to say. Material comes as interviews, focus groups, field notes, documents and open-ended survey answers alike; some of it has speakers and some has none, and a code never assumes there is someone talking.
9. An angle decides WHERE TO LOOK, never WHAT IS FOUND. The angles below were written before anyone read this material; they are places to look, and they are neither codes nor findings. Make a code only where this material says it, and never because an angle suggested it — an angle that this material turns out to have nothing to say to earns no code at all.
10. Cite the sentences that carry the meaning, not the whole passage around them: two or three ids per code is usual, and a code resting on one clear sentence is better than a code smeared across twenty.
11. Say less rather than more: fewer codes that each earn their sentences beat a long list that restates the material.

Return exactly this shape — `code` is a plain string when the codebook already has that name, and an object when the code is new:

{"codes": [
  {"code": {"name": "Work as what makes staying possible",
            "definition": "Passages where earning is described as the condition of remaining somewhere."},
   "sids": ["S012", "S013", "S045"]},
  {"code": "Leaving home", "sids": ["S004", "S007"]}
]}

---

WHAT THE RESEARCHER IS LOOKING FOR, IN THEIR OWN WORDS

{{focus}}

THE CODEBOOK AS IT STANDS — reuse these names exactly, as plain strings

{{codebook}}

WHAT THIS MATERIAL IS

{{frame}}

WHERE IT COULD BE WORTH LOOKING — written before this material was read, so treat every line of it
as a place to look and none of it as something found. Code what the material says here; leave an
angle uncoded when this material has nothing to say to it.

{{angles}}

THE MATERIAL — each line is one sentence id and its text; cite only these ids

{{material}}
