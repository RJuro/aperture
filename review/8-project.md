# PROJECT — as sent to the model

_3056 words · ≈4846 tokens_

## SYSTEM

```
You are writing what a project of qualitative material adds up to, for the researcher who is
reading it. You see what the reading already found in each material: its summary, and its threads
of moments, each moment a claim already resting on a quote that has been checked against the
material it came from.

Four rules. Each one carries the same weight, and each one is checked.

1. Every claim you make rests on moments that already exist, cited by moment id in square
   brackets: `[mo1a2b3c4d5]`, or `[mo1a2b3c4d5, mo6e7f8g9h0]` for several.
2. Every moment id you cite is copied exactly from the lists below. A citation to an id that does
   not exist is removed from your summary afterwards, taking its claim's support with it.
3. You introduce no quotes of your own. At this level there is no material in front of you to
   quote from — the moments are the evidence, and they have already been checked. A sentence in
   quotation marks that is not a moment's own words has nothing holding it up.
4. Every word is your own and none of them assume a speaker. These materials may be interviews,
   focus groups, field notes, documents, or answers to an open question. Write about what the
   materials show, not about what "he" or "she" said, unless a material names who is speaking.

The caps, as numbers: summary 250 words. Each theme gist 40 words. One gist per theme, and only
for the themes listed below.

Return JSON in exactly this shape, and nothing else:

{
  "summary": "At most 400 words on what the corpus shows so far. Write about the CORPUS, not
              about each piece in turn. Do not walk the materials one by one; a summary shaped as
              'the first account does X, the second does Y' stops working the moment a third
              arrives, and this project will have many. Instead name the patterns: what recurs
              across materials and how widely, where they diverge and along what axis, what
              appears in only one and is therefore not yet a pattern, and what is thin everywhere.
              Reach for the material's own names when a pattern needs one. Every statement carries
              moment ids in brackets like this [mo1a2b3c4d5] as its evidence, drawn from more than
              one material wherever the pattern spans them. No quotes of your own: at this level
              your claims rest on claims below."
}

No key other than `summary`. No text outside the JSON object.
```

## USER

```
WHAT THE RESEARCHER IS LOOKING FOR, in their words:

how people make a living after arriving, and what it costs them

WHAT EACH THEME AMOUNTS TO ACROSS THE CORPUS — the accounts written over the claims, each
with the claim ids it rests on. Your summary is written over these; cite the same ids.

## Administrative and civic labour of becoming (t322ab0effe)
definition: Administrative labour of emigration is remembered where a mother bore it — repeated trips to courts and offices — and absent where a child was too young to notice.
The theme runs through both materials but diverges along the axis of who bore the administrative labour and whether the narrator was conscious of it. In Mary Grande's interview, bureaucratic labour is vivid, sustained, and gendered: the mother navigated courts, offices, and higher-ups before departure, constantly travelling to appointments in the final month [mo8548819c2e, mofb907f7b91, mo3c47d806b0]. Mary herself was folded into her mother's passport as a minor, exempted from this labour [mo88c12565f4]. The civic culmination arrives twelve years later — citizenship as a joint act with her husband — and closes with a declaration of belonging to the new country, not the old [mod5993e0c16, mo007a3003db]. In Minnie Rodwin's interview, the bureaucratic labour is dimly present and partly erased from memory. Her father secured tickets and went ahead alone, removing the labour from her view [mof9fa185df5]; she has no memory of Ellis Island processing at all [mo2941456e12]. What survives instead is a discrepancy between actual and registered birth dates — six weeks apart — carried as fact rather than grievance [mo228dc3a5e1, mo2434164aeb]. The civic dimension appears only in Mary's material [mod5993e0c16, mo007a3003db], making it thin: claimed in one interview and not echoed in the other. Minnie's silence on citizenship may reflect the same dimness that obscures her Ellis Island memory, or it may mean the interview did not reach that chapter. The administrative labour of becoming, in short, is remembered where a parent performed it within the narrator's sight and forgotten where a parent went ahead alone.

## Family enterprise and the gendering of skill (t705b49e6a3)
definition: A woman's baking skill sustains a family enterprise across three countries, yet the business carries the father's name and the interviewer assumes it was his. Appears in one material only; absent from the farm-and-mine interview.
Across this corpus, the theme appears in a single material — the Minnie Rodwin interview — but the pattern it exposes is sharp enough to stand as a finding about how livelihoods are remembered and attributed. A woman's portable craft, baking, is the skill that builds a family enterprise across two migrations, from Poland to London to New York [mobb78fd3f61, mofb8c8685d7]. The mother is identified as the baker; the father was a tailor by trade, not a baker, and became one through her [mod0de02cde9, mofb8c8685d7]. Her bakery business is the first trade mentioned in the interview, preceding any reference to the father's work [mo55bb92952e]. Yet this authorship is obscured twice over. The New York bakery carries the father's surname — "Floun's" — rather than the mother's name or skill [mo744bfbe4f5]. And the interviewer, hearing of the bakery, assumes it was the father's enterprise: the question itself presumes male ownership [mo055e8158c3]. The gendering of skill thus operates at two levels: the business is named after the man, and the record itself defaults to crediting him. What is thin here is everything — six claims, one material, nowhere corroborated. The absence from the Mary Grande interview means this pattern cannot be tested against a second case. Mary Grande's silence might indicate a different household economy where women's skills were not commercially deployed, or where the interview's framing did not surface the question of attribution. Without a second instance, the theme stands as a single, vivid example of a woman's craft sustaining a transatlantic livelihood while the name and the assumption of ownership settle on the man.

## Household subsistence and expected labour (te03fdf696d)
definition: Women's labour and children's routine duty sustain every household — through barter, farm work, or bakery enterprise — framed as ordinary, not hardship. Spans the full corpus; the gendered attribution of that labour diverges sharply between materials.
Across both materials, household subsistence rests on women's labour and children's routine participation, framed as ordinary duty rather than as hardship or exceptional burden. The materials diverge along an urban-rural axis: in the Grande interview, the mother sustains the household through cattle-raising and barter in a wartime rural economy [moef6ccae400, moc5b05d950f], while in the Rodwin interview the family enterprise is a bakery where children's help is casual and expected [mo8f36ad134b, moa1a6c68818]. Despite the different settings, the structure holds: a woman's skill or labour is what keeps the household fed, and children's contributions are woven into the daily round without being marked as exploitation. Women running farms alone while men went to America is described as normal, not exceptional [moc018e2eebb], and the mother's physical labour — cutting, sawing, and chopping firewood herself — is presented matter-of-factly [mob856c93b37]. What appears beside this theme in both materials is a boundary set by maternal authority around labour: the Grande household held farm produce back from sale because it was the year's food supply [mobfc2ae2bcc], and the Rodwin mother refused to let her children accept coins thrown by steerage passengers after they performed [moe263a2557a]. In both cases the boundary protects the household's dignity or survival over immediate cash. Children's labour is the most consistent strand: catching blood at slaughter [mo8c61c539ea], being released from school to help at home [mof706e0df3a], decorating macaroons [moa1a6c68818], and performing in steerage [mo83e3b6af93] are all recounted as routine. The steerage performance is the thinnest claim — a single instance unique to one material — but the pattern of children's expected labour is confirmed across both. The theme is absent from no material in this project; it reaches the entire corpus, suggesting that household subsistence through gendered and juvenile labour is a defining feature of these migration accounts rather than a sidelight.

## Industrial wage work as livelihood after migration (tf26da42d35)
definition: Industrial wage work — mining, smelting, butchering — is livelihood after migration in one interview only. Its cost is the body that cannot sustain it. Entirely absent from the bakery-family interview.
Industrial wage work appears in only one of the two materials, but within it the pattern is clear and carries a cost. Coal mining is the reason the family settled in Utah [moa9a8f4dbf7], and it was not a first instance — the father had already worked mines in Aspen, Colorado, before returning to Utah [mo9c05216fa1]. Mining, smelting, and packing-house butchering form a sequence of industrial employments, but the sequence is driven by physical decline rather than choice. When health ended mining, the father found work at a smelter but could not sustain it [moab32428112]; he returned to the mine, but the body could not last there either [mof1678b7f27]. The final claim names butchering — cutting pork and beef, scraps for sausage [moab408aec16] — suggesting a move from extraction to processing, from underground to the killing floor, as the body gave out. What the theme shows is industrial wage labour as both livelihood and attrition: the work sustains the household, but it consumes the worker, each job ending because the body cannot continue and the next found in its wake. The cost here is corporeal, not emotional or bureaucratic. The theme is absent from the Minnie Rodwin oral history interview. That silence is structural rather than incidental: the Rodwin family's livelihood ran on bakeries — family enterprise, not factories — so industrial wage labour never arose as a route. The divergence between the two materials runs along the axis of economic form: wage labour in extraction and processing on one side, family enterprise on the other. Industrial work is not the universal post-migration livelihood in this corpus; it is one path, and where it appears, what appears beside it is bodily breakdown.

## The bodily cost of industrial work (t256893f66d)
definition: Industrial wage labour disables workers across two generations of one family — father, daughter, granddaughter each driven out by health. Absent from the bakery interview, whose enterprise carries no such bodily cost.
The bodily cost of industrial work is documented entirely within a single family's experience, spanning two generations and three workers. The father's trajectory establishes the pattern: a smelter job ended when his body could not sustain the labour [moe3380e7980], a subsequent return to mining failed the same way [mo1ab2399682], and after six and a half years in Sunnyside his health deteriorated badly enough to force a family relocation [moad1bfe1e81]. A doctor's verdict finally ended his working life altogether [mo5da421ae26]. The same cost then recurs in the next generation. Mary Grande's own packing-house employment was interrupted by repeated surgeries over the years [mo8fcbb216d9], and her daughter Mitzi likewise had to leave packing-house work for medical reasons [mo872e1a0eb1]. What varies across these claims is not the outcome but the site — smelter, mine, packing house — and the generation: the father is disabled across multiple extractive jobs, while the mother and daughter are both disabled by the same packing-house labour. The theme is thin in one sense: every claim rests on a single interview, so the pattern cannot be tested against other accounts in this corpus. Its absence from the Minnie Rodwin oral history interview is meaningful rather than accidental. The Rodwin family ran bakeries, not factories, and the corpus note flags that the industrial-wage-labour pattern is not universal. Where the livelihood is a family enterprise rather than industrial wage labour, the bodily cost simply does not arise in the record — suggesting the theme belongs specifically to the industrial sector, not to migration or labour in general.

## What migration narrows and separates (t70f91d46ab)
definition: Migration splits families by distance, death, and prior departure in both materials. A woman's productive range narrows to domestic tasks in one; in the other, separation is felt through sisters left behind and a child lost after the crossing.
Across both materials, migration is defined by what it breaks apart. Separation runs on two axes: temporal and spatial. Fathers depart first and the rest follow — in one case by nine years [mofeda679037], in another by a full year [mo3e22687253] — so the family unit is lived in two countries at once for long stretches. The trailing mother's motive is given as following the man rather than choosing the move herself [mo2035ea1cb6]. Spatial separation is permanent: siblings are left behind in Poland because the mother fears she cannot provide for them [mo3a237a8517, moabb3898bf2], and the property in Yugoslavia is signed over to a relative who stays [mo6ee2705382]. Death sharpens the severance: a brother who was meant to emigrate dies in an accident before he can [mo58f2096509, mo1df6f2ed5e], and a younger sister who does make the crossing dies in America [mo61b7b34479]. Migration thus narrows the family not only by distance but by attrition — planned reunions that never happen, and arrivals that end in death. The second strand, narrowing of productive life, appears only in one material: the mother's work collapses from whatever it had been to housework and laundry alone [mo0b350d6296]. The homeland itself is surrendered materially, through the property transfer [mo6ee2705382], and emotionally: one mother grieves the loss while her daughter does not share it [mo418c7e4897]. This last claim is thin — a single observation in a single material — but it marks how the cost of narrowing falls unevenly within a household, borne more heavily by the generation that left than by the one that grew up after. The theme reaches the entire corpus, and its two strands — separation and narrowing — are inseparable: the same act of leaving that splits families also strips the woman's world to domestic labour and the memory of what was given away.

WHAT THE RESEARCHER SAID about the project, in their own words. Take it as instruction:

The researcher has not said anything about the project yet.

WHAT THE READING FOUND, material by material. The id in brackets before each claim is the moment
id you cite:

## Ellis Island Oral History: Mary Grande — interview
This oral history interview, recorded in Denver in 1989, is Mary Grande's account of her life from a peasant childhood near Novo Mesto — then Austria-Hungary, later Yugoslavia — through her 1920 migration to the United States at age ten, to decades of work and settlement in Utah and Colorado. Andrew Phillips conducts; Grande's daughter Mitzi Stackhouse enters midway.

The interview traces a passage through distinct economies. In Yugoslavia, Grande's mother sustained the household through livestock, barter, and children's labour — cattle traded for goods, pigs slaughtered and cured, a ten-year-old catching blood for sausage. This subsistence world is presented as ordinary. Migration was organised by a father already in Utah's coal mines since 1911: tickets sent by post, approvals navigated by the mother across courts and offices. A brother meant to follow died in a wagon accident before he could emigrate.

After arrival, the father's mining and smelter work collapsed under failing health. The mother's world narrowed from running a farm to housework and laundry. Grande spent nearly thirty years in a packing house, her employment interrupted by surgeries; her daughter Mitzi left the same industry for medical reasons. Citizenship in 1932 and voting thereafter are framed as acts of belonging, and Grande closes by declaring the United States her country.

The thread on administrative and civic labour follows the mother's bureaucratic ordeal to emigrate and then Mary's naturalisation decades later. Household subsistence tracks barter, children's duties, and women's farm labour as unremarkable routine. Industrial wage work follows the family through coal mines, smelters, and packing houses. Bodily cost traces health ending each generation's work. What migration narrows follows the shrinking of the mother's productive life and the family split by distance and death. What is thin: the emotional life of migration is largely refused — Grande says she did not miss home, and the interview does not press. The mother's interior world is almost entirely absent.

## Minnie Rodwin oral history interview — interview
This is an oral history interview with Minnie Rodwin, née Mary Floun, conducted by Janet Levine for the National Park Service in 1997 at Rodwin's home in Sunrise, Florida. Rodwin, ninety years old, recounts her early childhood in London, her parents' Polish origins, and the family's immigration to New York's Lower East Side in 1910, when she was three and a half. The interview is brief and fragmented; Rodwin's memories are patchy, often uncertain, and she interrupts herself to eat before the final questions. The central narrative is a family-enterprise story: the mother's bakery skill, practiced in Poland, London, and New York, sustains the household across three countries. Yet this skill is consistently attributed to the father. The interviewer assumes the bakery was his business; the New York shop is named Floun's after the father's surname; and Rodwin states plainly that her mother was the baker while her father was a tailor who became a baker through her. A second narrative follows what migration separates: two sisters left in Poland with a grandmother, a father who goes ahead a year before, a younger sister who dies after the crossing, and a mother who follows her husband rather than her own wish. Children's labour appears as expected routine: the school tells the mother to keep older children home to help, and Rodwin describes decorating macaroons and helping out as ordinary. On the ship, children danced for thrown money, but the mother refused to let them keep it. The thread on administrative labour follows the gap between Rodwin's actual and registered birth dates, her father's securing of tickets, and her complete non-memory of Ellis Island. What is thin or missing: industrial wage work and its bodily cost are entirely absent — this is a bakery family, not a factory one. Civic acts like voting are never mentioned.
```
