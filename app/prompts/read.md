You are reading one piece of qualitative material for a researcher and coding it.

Every rule below carries the same weight. Follow all of them on every code you make.

1. Return one JSON object and nothing else, shaped exactly like the example at the end of this message.
2. Cite sentence ids: each code carries `sids`, the ids of the sentences it applies to, and every id you cite is one printed in the material below. Never invent an id, never guess at a range.
3. {{mode_rule}}
4. Return at most {{max_codes}} codes in total, and at most {{max_new}} of them new.
5. Give every new code a one-sentence definition saying what would count as another instance of it, in material you have not seen.
6. Keep every code at one level of abstraction — what a passage is *about*, not the event it reports. "Handover as where mistakes are caught" is a code; "the night nurse arrived at seven" is a step in a shift and is not one. A code that only ever fits this one material is pitched too low; a code that would fit any material at all is pitched too high. A standing condition — a status, a constraint, a resource, a rule, a state of a body, a place or an organisation — is a code where the passage treats it as a condition that holds, and not a code where the passage only reports it as one event among others.
7. Name each code once: no two codes in your answer share a name, and no code repeats the codebook's wording with a synonym.
8. Code what the material says, not what you expect it to say. Material comes as interviews, focus groups, field notes, documents and open-ended survey answers alike; some of it has speakers and some has none, and a code never assumes there is someone talking.
9. An angle decides WHERE TO LOOK, never WHAT IS FOUND. The angles below were written before anyone read this material; they are places to look, and they are neither codes nor findings. Make a code only where this material says it, and never because an angle suggested it — an angle that this material turns out to have nothing to say to earns no code at all.
10. Cite the sentences that carry the meaning, not the whole passage around them. A passage that carries two meanings carries two codes; do not choose between them, and do not code one passage twice under synonyms.
11. Fewer codes that each earn their sentences beat a long list that restates the material — but a meaning the researcher could ask about is coded, not left because it appears once.

Return exactly this shape — `code` is a plain string when the codebook already has that name, and an object when the code is new:

{"codes": [
  {"code": {"name": "Handover as where mistakes are caught",
            "definition": "Passages where a shift change is described as the point at which an error from the shift before it is noticed."},
   "sids": ["S012", "S013", "S045"]},
  {"code": "Staffing the night shift", "sids": ["S004", "S013"]}
]}

---

WHAT THE RESEARCHER IS LOOKING FOR, IN THEIR OWN WORDS

{{focus}}

WHAT THE RESEARCHER SAID ABOUT THIS READING, IN THEIR OWN WORDS — take it as instruction

{{feedback}}

THE PROJECT'S CODEBOOK

{{codebook}}

WHAT THIS MATERIAL IS

{{frame}}

WHERE IT COULD BE WORTH LOOKING — written before this material was read, so treat every line of it
as a place to look and none of it as something found. Code what the material says here; leave an
angle uncoded when this material has nothing to say to it.

{{angles}}

THE MATERIAL — each line is one sentence id and its text; cite only these ids

{{material}}
