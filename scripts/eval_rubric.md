# Reading a record

You are one of two readers marking a reading record produced by an instrument that codes
qualitative material and writes it up. You are given **two records, A and B**, in no particular
order. You are not told which is newer, which came from which version of the instrument, or what
was changed between them. Do not guess, and do not let a guess shape a score. If you find
yourself reasoning about which is the improved one, stop and go back to the text.

Mark **each record separately and completely** before you compare them. Everything you say must
be answerable from the two documents in front of you.

Each record has the same sections: **Across the corpus** (a corpus summary and a provisional
interpretation), **Themes** (each with a definition, an account, the materials where it appears
with its claims and quotes, and the materials where it does not), **Materials** (each with a
description written before the reading and one written after), **Questions checked against the
materials**, **Excluded from the analysis**, **Researcher feedback**, **Processing history**,
**Theme history** (every earlier name and definition of a theme that was rewritten).

A claim is printed as a numbered sentence with the verbatim quote it rests on beneath it and a
passage id in brackets:

```
3. The German state taxed emigrants on new purchases at full price, forcing families to bring …
   > You had to pay for every item that you purchased new  [S053]
```

The quote is the evidence. The claim is what the instrument made of it.

---

## The seven dimensions

Score each **1 to 5**. **5 is clean** — the fault is absent or negligible. **1 is severe** — the
fault is pervasive and would mislead a reader who trusted the record. 3 is "present, and a
careful reader would have to correct for it".

Every score needs **at least one quoted line from the record as evidence**, and a 4 or 5 needs a
sentence saying what you looked at and did not find. Quote the record, do not paraphrase it.

### 1. Theme inflation

Are there more themes than the material can carry? Look at how many themes there are against how
many materials; at themes whose claims all come from one material; and above all at themes that
are **an event rather than a pattern** — a fire, a wedding, one journey — dressed as an analytic
category. A theme should be something fifty more materials could be measured against.

Look at: the theme count against the material count; each theme's "Materials where this theme
appears"; any theme whose definition names a specific incident.

### 2. Concept drift

Has a theme's definition been widened so that a new material could be admitted to it? Compare
each theme's definition with the claims filed under it, and read the **Theme history** section,
which prints every earlier definition. A definition that grows from "a family enterprise of
farming and performance" to "work frames migration in all materials" has been rewritten to fit
what arrived, not sharpened. Also: does the theme's **name** still describe what the definition
now says, and does the definition describe what the claims actually show?

Look at: Theme history; each definition against the claims beneath it; name against definition.

### 3. Recycled passages

Is the same passage doing duty under three or four themes? Track repeated passage ids across
theme sections. One passage supporting two themes can be honest — a sentence can be about both
work and family. The same sentence appearing under four is usually one observation counted four
times, which makes a thin corpus look broad.

Look at: repeated `[Sxxx]` ids across theme sections, within the same material.

### 4. Pattern hunger

Does a claim say more than its quote does? The commonest form is a claim that supplies a
**motive** ("because she feared"), a **manner** ("reluctantly", "with dignity"), or an
**evaluation** ("a humiliating descent") that the quote beneath it does not contain. The second
form is an account or summary asserting that something holds for **all** materials, **every**
speaker, **without exception**, when the claims beneath it do not show that.

Look at: claims against their own quotes; the words *all, every, each, consistently, no
exceptions, across the corpus* in the accounts and the corpus summary.

### 5. Valence contradictions

Is the same passage, or the same episode, read one way under one theme and the opposite way under
another, with neither account acknowledging the other? A mother's refusal to learn English read
as cultural sovereignty under one theme and as failed adaptation under another is a finding only
if the record says so; unmarked, it is two readings that have not met.

Look at: shared passage ids from dimension 3, and what each theme's claim and account makes of
them.

### 6. Overreading absence

Does the record infer meaning from what a material did not say? "Materials where this theme does
not appear" is a legitimate section — it reports that no claims were filed. It becomes a fault
when an account explains the silence: *"the absence of this theme from X suggests a movement
narrated through other frames"*. An interview did not cover a topic; that is a fact about an
interview, not about a life. The same applies to a summary that treats an unmentioned thing as
significant.

Look at: the "Materials where this theme does not appear" sections; the word *absent*,
*silence*, *does not mention*, *never says* in accounts and the corpus summary.

### 7. Housekeeping

Anything a careful reader would call sloppy in a document meant to be handed in: characters from
another script dropped into English prose; a passage id written twice inside one bracket; an
entry under **Excluded from the analysis** that does not say which quote or claim was excluded;
identifiers shown to the reader as opaque strings (`note on md433c285e5`) where a name belongs;
a heading that points at nothing; a count that contradicts the list beneath it.

Look at: Excluded from the analysis; Researcher feedback; every bracketed id; the whole document
at a skim for stray characters.

---

## Spot checks

Answer each **yes** or **no**, and give **one quoted line from the record** as evidence. A "no"
needs evidence too: name what you checked. Answer for each record separately.

1. **Single event as theme.** Does any theme rest on a single event in one life?
2. **Name against definition.** Does any theme's name no longer match its definition?
3. **Totalising account.** Does any account or the corpus summary say *all*, *every*, or *no
   exceptions* about the corpus?
4. **Claim beyond quote.** Sample **five claims** from across the record — different themes,
   different materials — and check each against the quote printed beneath it. Does the claim add
   a motive, a manner or an evaluation the quote does not contain? Report all five with their
   verdicts, then answer yes if any one of them does.
5. **Opposite readings.** Is any passage read in opposite directions under two themes, without
   either account saying so?
6. **Inference from silence.** Does any account infer something from what a material did not
   mention?
7. **Housekeeping defects.** Are there stray non-Latin tokens, a passage id written twice in one
   bracket, or an excluded-quote note that does not name the quote?

---

## What to return

One JSON object, nothing else around it.

```json
{
  "records": {
    "A": {
      "scores": {
        "theme_inflation": {"score": 1, "evidence": "…quoted line…", "note": "…"},
        "concept_drift": {"score": 1, "evidence": "…", "note": "…"},
        "recycled_passages": {"score": 1, "evidence": "…", "note": "…"},
        "pattern_hunger": {"score": 1, "evidence": "…", "note": "…"},
        "valence_contradictions": {"score": 1, "evidence": "…", "note": "…"},
        "overreading_absence": {"score": 1, "evidence": "…", "note": "…"},
        "housekeeping": {"score": 1, "evidence": "…", "note": "…"}
      },
      "spot_checks": {
        "single_event_as_theme": {"answer": "yes", "evidence": "…"},
        "name_against_definition": {"answer": "no", "evidence": "…"},
        "totalising_account": {"answer": "yes", "evidence": "…"},
        "claim_beyond_quote": {
          "answer": "yes",
          "sampled": [
            {"theme": "…", "claim": "…", "quote": "…", "adds": "motive|manner|evaluation|nothing"}
          ]
        },
        "opposite_readings": {"answer": "no", "evidence": "…"},
        "inference_from_silence": {"answer": "yes", "evidence": "…"},
        "housekeeping_defects": {"answer": "yes", "evidence": "…"}
      }
    },
    "B": { "…the same shape…" }
  },
  "which_reads_better": "A|B|neither",
  "why": "two or three sentences, from the text only"
}
```

`which_reads_better` is your judgement of the two documents as documents. It is not a guess at
which came from the newer instrument, and you have not been told.
