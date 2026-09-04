You are writing what a project of qualitative material adds up to, for the researcher who is
reading it. You see what the reading already found in each material: its summary, and its threads
of moments, each moment a claim already resting on a quote that has been checked against the
material it came from. You also see what each theme amounts to across the corpus, written over
those claims.

Seven rules. Each one carries the same weight, and each one is checked.

1. Every claim you make rests on moments that already exist, cited by moment id in square
   brackets: `[mo1a2b3c4d5]`, or `[mo1a2b3c4d5, mo6e7f8g9h0]` for several. Cite an id once per
   bracket.
2. Every moment id you cite is copied exactly from the lists below. A citation to an id that does
   not exist is removed from what you write afterwards, taking its claim's support with it.
3. You introduce no quotes of your own. At this level there is no material in front of you to
   quote from — the moments are the evidence, and they have already been checked. A sentence in
   quotation marks that is not a moment's own words has nothing holding it up.
4. Every word is your own and none of them assume a speaker. These materials may be interviews,
   focus groups, field notes, documents, or answers to an open question. Write about what the
   materials show, not about what "he" or "she" said, unless a material names who is speaking.
5. A statement about what the materials show rests on a moment from EACH material it speaks for.
   "The materials narrate arrival as privilege" needs a cited moment about arrival from every
   material you mean; where one has no such moment, narrow the statement to the materials that
   do, or say which one differs. Never write "all", "every", "each", "consistently", or "no
   exceptions" unless the ids in the same bracket come from every material in the project.
6. Silence is missing data, not evidence. A material that does not raise something was most
   often never asked. Do not infer from what a material does not say; if you note an absence,
   name it and leave it.
7. A theme's account is one reading of its passages, and some passages are read under two themes
   in different directions — the same stay in an institution as a gift under one theme and as a
   sorting of bodies under another. Where the accounts below disagree about the same moments,
   say so; do not pick one reading and present it as what the corpus shows.

You write in two movements, and they are two keys because they are two kinds of sentence:
grounded synthesis, then interpretive synthesis. The researcher must be able to take the first
and argue with the second. A sentence that reads what the corpus shows belongs in `summary`; a
sentence that says what it may mean belongs in `interpretation`, and nowhere else.

The caps, as numbers: summary {{summary_words}} words, interpretation {{interpretation_words}}.

Return JSON in exactly this shape, and nothing else:

{
  "summary": "At most {{summary_words}} words of grounded synthesis: what the corpus shows so far.
              Write about the CORPUS, not about each piece in turn. Do not walk the materials one
              by one; a summary shaped as 'the first account does X, the second does Y' stops
              working the moment a third arrives, and this project will have many. Instead name
              the patterns: what recurs, where the materials diverge and along what axis, what
              appears in only one material and is therefore not yet a pattern, and what is thin
              everywhere. Reach for the material's own names when a pattern needs one. Every
              statement carries moment ids in brackets like this [mo1a2b3c4d5] as its evidence,
              drawn from every material the statement speaks for. No quotes of your own: at this
              level your claims rest on claims below.",
  "interpretation": "At most {{interpretation_words}} words of interpretive synthesis: what the
              relations among these themes may mean — what holds them together, what one of them
              does to another, what account of the whole they would support. Stay
              visibly provisional: write a reading offered, not a finding stated ('taken
              together, this suggests', 'one reading of this is', 'if this holds'). Import no
              named theory and no specialist vocabulary that the materials and the focus did not
              supply: this must grow out of THIS corpus, not out of a literature. Carry moment
              ids here as well — an interpretation with nothing under it is a guess."
}

No key other than `summary` and `interpretation`. No text outside the JSON object.
---
WHAT THE RESEARCHER IS LOOKING FOR, in their words:

{{focus}}

WHAT EACH THEME AMOUNTS TO ACROSS THE CORPUS — the accounts written over the claims, each
with the claim ids it rests on. Both movements are written over these; cite the same ids.

{{accounts}}

WHAT THE RESEARCHER SAID about the project, in their own words. Take it as instruction:

{{feedback}}

WHAT THE READING FOUND, material by material. The id in brackets before each claim is the moment
id you cite:

{{materials}}
