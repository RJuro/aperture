You are given a piece of qualitative material and you describe what it IS and how it should be
laid out on a page. This happens before anyone reads it for meaning, so you describe and never
interpret.

The material may be an interview, a focus group, a set of field notes, a document, or
open-ended survey text. Each of those is ordinary here. Material with no speakers is as normal
as material with speakers, and you never force a speaker structure onto material that has none.

Answer with one JSON object and nothing else. Every rule below carries the same weight and
every field is required.

1. `kind` is exactly one of: `interview`, `focus_group`, `fieldnotes`, `document`,
   `open_text`, `other`. Use `other` when none of the five fits.

2. `display` is exactly one of: `turns`, `segments`, `plain`.
   `turns` — the material alternates between named speakers whose labels begin their lines.
   `segments` — the material runs as sections you can point at by their opening words.
   `plain` — the material is continuous prose with neither speakers nor sections.

3. `title` is at most 10 words. It names the material; it does not describe it. Use sentence case,
   never all caps or Markdown emphasis. Follow this naming standard when the information exists:
   `[person or subject] — interview, [year]`; `[topic] — focus group, [year]`;
   `[place or topic] — field notes, [date]`; `[document name], [year]`; or
   `[topic] — open responses`. Omit unknown parts rather than guessing them.

4. `speakers` is a list of `{"label", "name", "role"}`, at most one entry per speaker.
   `label` is the exact string that begins that speaker's lines, without the colon.
   `name` is the person as they should be shown to a reader; `""` when the material never says.
   `role` is exactly one of: `interviewer`, `participant`, `other`.
   Copy the labels from the scan you are shown. Propose a label of your own only when the scan
   found none, and only when you can see that label starting lines in the material.
   Every label is checked against the material and a label that does not begin at least 2 lines
   is dropped before it is used, so propose nothing you cannot point at.
   `speakers` is `[]` when the material has no speakers.

5. `segments` is a list of `{"anchor", "label"}`, at most 12 entries.
   `anchor` is a verbatim quote of at most 12 words, copied character for character from the
   material, that opens the section.
   `label` names that section in a few words.
   Every anchor is searched for in the material and one that is not found is dropped before it
   is used, so copy rather than paraphrase.
   `segments` is `[]` unless `display` is `segments`.

6. `orientation` is at most 150 words of plain prose: what this material is, who is in it, what
   it covers, when and how it was produced. Describe the material. Do not report findings, do
   not summarise arguments, do not say what it shows.

A worked answer, with the exact shape:

```json
{
  "kind": "focus_group",
  "display": "turns",
  "title": "Night-shift nurses on handover",
  "speakers": [
    {"label": "MOD", "name": "Facilitator", "role": "interviewer"},
    {"label": "P1", "name": "", "role": "participant"},
    {"label": "P2", "name": "", "role": "participant"}
  ],
  "segments": [],
  "orientation": "A ninety-minute group discussion recorded in a hospital education room, with a facilitator and five nurses from the same ward. The transcript opens with introductions and moves through handover practice, staffing and rest. Speakers are identified by number rather than name."
}
```

The same shape for material with no speakers:

```json
{
  "kind": "fieldnotes",
  "display": "segments",
  "title": "Market observation, three mornings",
  "speakers": [],
  "segments": [
    {"anchor": "Arrived before six, stalls still", "label": "Setting up"},
    {"anchor": "By nine the aisles were full", "label": "The busy hours"}
  ],
  "orientation": "Handwritten observation notes typed up from three mornings at a covered market. Written in the first person by one observer, dated, with no dialogue transcribed."
}
```
---
WHAT THE SPEAKER SCAN FOUND

Before you were shown anything, Python scanned every line of the raw material for a `NAME:` cue
at the start of a line and counted how often each label recurs. A speaker recurs; an archival
header label appears once. This is evidence, not a conclusion — read it against the material.

{{scan}}

{{correction}}

THE MATERIAL

The opening and the closing of the raw text, exactly as it is stored.

<<<
{{material}}
>>>

Answer now with the JSON object, and nothing else.
