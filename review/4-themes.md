# THEMES — as sent to the model

_1427 words · ≈2204 tokens_

## SYSTEM

```
You are grouping a researcher's codes into themes across a whole project.

Every rule below carries the same weight. Follow all of them on every theme you return.

1. Return one JSON object and nothing else, shaped exactly like the example at the end of this message.
2. Return the whole theme set, not only what changed: every theme that should be live afterwards appears in your answer, keeping its `id` when it already has one and carrying `"new": true` instead when it does not.
3. Gather codes by name: `code_names` holds names copied exactly from the codebook below, and a name that is not in that codebook is ignored.
4. Keep at most 12 themes live. Fewer, well-populated themes beat many thin ones.
5. Give every theme a gist of one sentence saying what the theme claims about the material, not what its codes are called.
6. Fold a theme into another by giving it `"merge_into": "<the id it becomes part of>"` — never by leaving it out of your answer. A theme that is dropped silently strands everything already written under it.
7. Build a theme on codes that recur across more than one material where the codes allow it; say so in the gist when a theme belongs to a single material only.
8. Keep each theme at one level of abstraction — a pattern the codes share, not a summary of one passage and not a restatement of a single code's name.
9. Leave a code out rather than force it: a code that fits nowhere stays ungathered, and that is a finding.
10. Change a live theme's name or gist only when the codes give you a reason to; a researcher who has read a theme should still recognise it.

Return exactly this shape:

{"themes": [
  {"id": "t9f2c1", "name": "Work and staying",
   "gist": "Earning is described less as a livelihood than as the condition of remaining.",
   "code_names": ["Work as what makes staying possible", "Sending money home"]},
  {"new": true, "name": "Being read as a stranger",
   "gist": "Encounters where the speaker is placed as an outsider before anything is said.",
   "code_names": ["Being asked where you are from"]},
  {"id": "t44ab0", "name": "Labour", "gist": "Overlaps with work and staying.",
   "code_names": [], "merge_into": "t9f2c1"}
]}
```

## USER

```
THE THEMES THAT ARE LIVE NOW

- id t322ab0effe · "Administrative and civic labour of becoming" — Administrative labour of emigration is remembered where a mother bore it — repeated trips to courts and offices — and absent where a child was too young to notice.
  gathers: Bureaucratic labour of emigration, Naturalisation as civic belonging
- id t705b49e6a3 · "Family enterprise and the gendering of skill" — A woman's baking skill sustains a family enterprise across three countries, yet the business carries the father's name and the interviewer assumes it was his. Appears in one material only; absent from the farm-and-mine interview.
  gathers: Bakery work as marital connection, Father's trade displaced by family enterprise, Gendered naming of family business, Mother's craft as portable capital
- id te03fdf696d · "Household subsistence and expected labour" — Women's labour and children's routine duty sustain every household — through barter, farm work, or bakery enterprise — framed as ordinary, not hardship. Spans the full corpus; the gendered attribution of that labour diverges sharply between materials.
  gathers: Barter as subsistence exchange, Children's labour as expected routine, Women's farm labour as ordinary
- id tf26da42d35 · "Industrial wage work as livelihood after migration" — Industrial wage work — mining, smelting, butchering — is livelihood after migration in one interview only. Its cost is the body that cannot sustain it. Entirely absent from the bakery-family interview.
  gathers: Packing-house work as long-term livelihood, Wage labour in extractive industry
- id t256893f66d · "The bodily cost of industrial work" — Industrial wage labour disables workers across two generations of one family — father, daughter, granddaughter each driven out by health. Absent from the bakery interview, whose enterprise carries no such bodily cost.
  gathers: Health decline ending wage work, Medical exit from industrial work
- id t70f91d46ab · "What migration narrows and separates" — Migration splits families by distance, death, and prior departure in both materials. A woman's productive range narrows to domestic tasks in one; in the other, separation is felt through sisters left behind and a child lost after the crossing.
  gathers: Family separation across migration, Work narrowing after migration

THE CODEBOOK, AND WHERE EACH CODE WAS FOUND

- Bakery work as marital connection — Passages where a marriage or partnership arises through shared occupation in the same trade or industry.
  found in: Minnie Rodwin oral history interview 3
- Barter as subsistence exchange — Passages where goods or livestock are exchanged directly for other goods rather than for money, as a way of sustaining a household.
  found in: Ellis Island Oral History: Mary Grande 3
- Bureaucratic labour of emigration — Passages describing the offices, courts, approvals, and trips required to secure permission to leave or travel.
  found in: Ellis Island Oral History: Mary Grande 3
- Chain settlement by shared origin — Passages explaining why people from the same region or nationality cluster in one place, citing mutual integration or following earlier settlers.
  found in: Ellis Island Oral History: Mary Grande 3; Minnie Rodwin oral history interview 2
- Children's labour as expected routine — Passages where a child's contribution to household or farm work is presented as a normal part of growing up rather than as hardship.
  found in: Ellis Island Oral History: Mary Grande 3; Minnie Rodwin oral history interview 3
- Conscription as migration push — Passages where a military call-up or draft obligation is cited as the reason a family or individual decides to leave a country.
  found in: Minnie Rodwin oral history interview 3
- Family separation across migration — Passages naming which family members went ahead, which stayed behind, and which died before they could join the migration.
  found in: Ellis Island Oral History: Mary Grande 3; Minnie Rodwin oral history interview 3
- Father's trade displaced by family enterprise — Passages where a man's original occupation is set aside so he can work in a family business built on someone else's skill.
  found in: Minnie Rodwin oral history interview 3
- Gendered naming of family business — Passages where a business is named after or credited to one gender though the operative skill belongs to the other.
  found in: Minnie Rodwin oral history interview 3
- Health decline ending wage work — Passages where a worker's deteriorating health is given as the reason they can no longer hold a job.
  found in: Ellis Island Oral History: Mary Grande 3
- Medical exit from industrial work — Passages where a worker leaves or pauses a job because of surgeries or medical conditions attributable to the work.
  found in: Ellis Island Oral History: Mary Grande 2
- Mother's craft as portable capital — Passages where a woman's skill or trade, learned in one country, becomes the household's livelihood in each subsequent country of settlement.
  found in: Minnie Rodwin oral history interview 3
- Naturalisation as civic belonging — Passages where acquiring citizenship and voting are described as acts that mark belonging in the new country.
  found in: Ellis Island Oral History: Mary Grande 2
- Packing-house work as long-term livelihood — Passages where meatpacking or similar industrial food-processing work is described as a sustained source of income over many years.
  found in: Ellis Island Oral History: Mary Grande 3
- Refusal of performance earnings as labour boundary — Passages where a family member refuses to let children accept money for informal performances, marking a boundary around what counts as acceptable work.
  found in: Minnie Rodwin oral history interview 3
- Wage labour in extractive industry — Passages where earning a living is tied to work in mines, smelters, or similar extraction sites.
  found in: Ellis Island Oral History: Mary Grande 3
- Women's farm labour as ordinary — Passages where women's agricultural or physical work on a farm is described as normal and expected, not exceptional.
  found in: Ellis Island Oral History: Mary Grande 2
- Work narrowing after migration — Passages where a person's range of productive activity shrinks after moving, especially from diverse subsistence work to domestic tasks only.
  found in: Ellis Island Oral History: Mary Grande 1

WHAT THE RESEARCHER IS LOOKING FOR, IN THEIR OWN WORDS

"""
how people make a living after arriving, and what it costs them
"""

WHAT THE RESEARCHER SAID ABOUT THE THEMES, IN THEIR OWN WORDS

The researcher has said nothing about the themes.
```
