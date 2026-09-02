# PROJECT — as sent to the model

_2677 words · ≈4221 tokens_

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
              your claims rest on claims below.",
  "theme_gists": [
    {"theme_id": "t1a2b3c4d5",
     "gist": "At most 40 words saying what this theme amounts to across the corpus — including how
              much of it the theme actually reaches.",
     "moment_ids": ["mo1a2b3c4d5", "mo6e7f8g9h0"]}
  ]
}

No keys other than these two. No text outside the JSON object.
```

## USER

```
WHAT THE RESEARCHER IS LOOKING FOR, in their words:

how people make a living after arriving, and what it costs them

THE THEMES this project is working with. A gist must name one of these ids in `theme_id`:

t322ab0effe  Administrative and civic labour of becoming — Administrative labour of emigration is remembered where a mother bore it — repeated trips to courts and offices — and absent where a child was too young to notice.
t705b49e6a3  Family enterprise and the gendering of skill — A woman's baking skill sustains a family enterprise across three countries, yet the business carries the father's name and the interviewer assumes it was his. Appears in one material only; absent from the farm-and-mine interview.
te03fdf696d  Household subsistence and expected labour — Women's labour and children's routine duty sustain every household — through barter, farm work, or bakery enterprise — framed as ordinary, not hardship. Spans the full corpus; the gendered attribution of that labour diverges sharply between materials.
tf26da42d35  Industrial wage work as livelihood after migration — Industrial wage work — mining, smelting, butchering — is livelihood after migration in one interview only. Its cost is the body that cannot sustain it. Entirely absent from the bakery-family interview.
t256893f66d  The bodily cost of industrial work — Industrial wage labour disables workers across two generations of one family — father, daughter, granddaughter each driven out by health. Absent from the bakery interview, whose enterprise carries no such bodily cost.
t70f91d46ab  What migration narrows and separates — Migration splits families by distance, death, and prior departure in both materials. A woman's productive range narrows to domestic tasks in one; in the other, separation is felt through sisters left behind and a child lost after the crossing.

WHAT THE RESEARCHER SAID about the project, in their own words. Take it as instruction:

The researcher has not said anything about the project yet.

WHAT THE READING FOUND, material by material. The id in brackets before each claim is the moment
id you cite:

## Ellis Island Oral History: Mary Grande — interview
what the reading found: This oral history interview, recorded in Denver in 1989, is Mary Grande's account of her life from a peasant childhood near Novo Mesto — then Austria-Hungary, later Yugoslavia — through her 1920 migration to the United States at age ten, to decades of work and settlement in Utah and Colorado. Andrew Phillips conducts; Grande's daughter Mitzi Stackhouse enters midway.

The interview traces a passage through distinct economies. In Yugoslavia, Grande's mother sustained the household through livestock, barter, and children's labour — cattle traded for goods, pigs slaughtered and cured, a ten-year-old catching blood for sausage. This subsistence world is presented as ordinary. Migration was organised by a father already in Utah's coal mines since 1911: tickets sent by post, approvals navigated by the mother across courts and offices. A brother meant to follow died in a wagon accident before he could emigrate.

After arrival, the father's mining and smelter work collapsed under failing health. The mother's world narrowed from running a farm to housework and laundry. Grande spent nearly thirty years in a packing house, her employment interrupted by surgeries; her daughter Mitzi left the same industry for medical reasons. Citizenship in 1932 and voting thereafter are framed as acts of belonging, and Grande closes by declaring the United States her country.

The thread on administrative and civic labour follows the mother's bureaucratic ordeal to emigrate and then Mary's naturalisation decades later. Household subsistence tracks barter, children's duties, and women's farm labour as unremarkable routine. Industrial wage work follows the family through coal mines, smelters, and packing houses. Bodily cost traces health ending each generation's work. What migration narrows follows the shrinking of the mother's productive life and the family split by distance and death. What is thin: the emotional life of migration is largely refused — Grande says she did not miss home, and the interview does not press. The mother's interior world is almost entirely absent.
thread — Administrative and civic labour of becoming (t322ab0effe):
  [mo8548819c2e] The father sent tickets, but the mother still had to secure approvals from multiple offices before they could leave. — quoted: "she had to go to different places to get it approved"
  [mo88c12565f4] As a minor, Mary was folded into her mother's passport, skipping the bureaucratic labour her mother bore alone. — quoted: "I didn't have to go anywhere because I was a minor"
  [mofb907f7b91] Emigration required trips through courts and offices, with approvals from higher-ups overseeing travel. — quoted: "she had to go through quite a bit of different courts"
  [mo3c47d806b0] In the final month before departure, the mother was constantly travelling to bureaucratic appointments. — quoted: "she was always coming or going to different places"
  [mod5993e0c16] Citizenship arrived twelve years after migration, framed as a joint act with her husband. — quoted: "my husband and I became American citizens in 1932"
  [mo007a3003db] The interview closes with a declaration that ties belonging to the new country, not the old. — quoted: "This is my country."
thread — Household subsistence and expected labour (te03fdf696d):
  [moef6ccae400] The mother kept the household going by raising cattle and bartering them, not by farming for market. — quoted: "she raised some cattle and bartered with them"
  [mo8c61c539ea] A child's expected role at slaughter was catching blood for sausage, disliked but treated as duty. — quoted: "I had to catch the blood"
  [mob856c93b37] The mother cut, sawed, and chopped firewood herself, with the child helping when she was older. — quoted: "she would cut it up herself, saw and chop it"
  [moc018e2eebb] Women running farms alone while men went to America is described as normal, not exceptional. — quoted: "Most all the women did similar work"
  [mobfc2ae2bcc] The farm's produce was held back from sale because it was the household's year-round food supply. — quoted: "Not too much off the farm because that was our livelihood"
  [moc5b05d950f] Exchange with city dwellers during wartime was barter, not cash: food traded for clothing. — quoted: "It would be a bartering"
thread — Industrial wage work as livelihood after migration (tf26da42d35):
  [moa9a8f4dbf7] The father's livelihood in Utah was coal mining, the reason the family settled there. — quoted: "he was working in coal mines"
  [mo9c05216fa1] Before Utah, he had worked mines in Aspen, Colorado, then returned to Utah. — quoted: "He worked part-time years before that in Aspen, Colorado"
  [moab32428112] After health decline ended mining, he found a job at a smelter, but could not sustain it. — quoted: "he got a job finally over at the smelter"
  [mof1678b7f27] He returned to the mine again, but the body still could not last there either. — quoted: "he went finally back into the mine"
  [moab408aec16] The work was butchering pork and beef, cutting scraps for sausage. — quoted: "Cutting up meat, pork and beef"
thread — The bodily cost of industrial work (t256893f66d):
  [moad1bfe1e81] After six and a half years in Sunnyside, the father's health deteriorated, forcing the family to relocate. — quoted: "his health went bad"
  [moe3380e7980] The smelter job lasted only a while; his body could not sustain the work. — quoted: "he worked there for a while, but couldn't work too long"
  [mo1ab2399682] A return to mining also failed; the body gave out again. — quoted: "he couldn't work too long there"
  [mo5da421ae26] A doctor's verdict finally ended the father's working life. — quoted: "the doctor said he couldn't work no more"
  [mo8fcbb216d9] Mary's own packing-house employment was interrupted by repeated surgeries across the years. — quoted: "I had to have different surgeries"
  [mo872e1a0eb1] Her daughter Mitzi also had to leave packing-house work for medical reasons. — quoted: "she had to give up medically on account of it"
thread — What migration narrows and separates (t70f91d46ab):
  [mofeda679037] The father had been in America since 1911, nine years before mother and child joined him. — quoted: "my father was here in the States since 1911"
  [mo58f2096509] A second brother was meant to follow them to America. — quoted: "they was going to bring him here"
  [mo1df6f2ed5e] That brother died in a wagon accident before he could emigrate, ending the plan. — quoted: "he fell or jumped or whatever, and he got killed"
  [mo0b350d6296] After migration, the mother's productive range collapsed to housework and laundry alone. — quoted: "All we could do was housework and laundry"
  [mo6ee2705382] The family property in Yugoslavia was transferred to the half-brother who stayed behind. — quoted: "She gave the property over to him"
  [mo418c7e4897] The mother grieved the lost homeland, while Mary did not share the feeling. — quoted: "My mother missed it a lot"

## Minnie Rodwin oral history interview — interview
what the reading found: This is an oral history interview with Minnie Rodwin, née Mary Floun, conducted by Janet Levine for the National Park Service in 1997 at Rodwin's home in Sunrise, Florida. Rodwin, ninety years old, recounts her early childhood in London, her parents' Polish origins, and the family's immigration to New York's Lower East Side in 1910, when she was three and a half. The interview is brief and fragmented; Rodwin's memories are patchy, often uncertain, and she interrupts herself to eat before the final questions. The central narrative is a family-enterprise story: the mother's bakery skill, practiced in Poland, London, and New York, sustains the household across three countries. Yet this skill is consistently attributed to the father. The interviewer assumes the bakery was his business; the New York shop is named Floun's after the father's surname; and Rodwin states plainly that her mother was the baker while her father was a tailor who became a baker through her. A second narrative follows what migration separates: two sisters left in Poland with a grandmother, a father who goes ahead a year before, a younger sister who dies after the crossing, and a mother who follows her husband rather than her own wish. Children's labour appears as expected routine: the school tells the mother to keep older children home to help, and Rodwin describes decorating macaroons and helping out as ordinary. On the ship, children danced for thrown money, but the mother refused to let them keep it. The thread on administrative labour follows the gap between Rodwin's actual and registered birth dates, her father's securing of tickets, and her complete non-memory of Ellis Island. What is thin or missing: industrial wage work and its bodily cost are entirely absent — this is a bakery family, not a factory one. Civic acts like voting are never mentioned.
thread — Administrative and civic labour of becoming (t322ab0effe):
  [mo228dc3a5e1] Rodwin gives Christmas morning as her actual birth date, not the registered one. — quoted: "December—December 25th."
  [mo2434164aeb] The official registered date is six weeks later than the actual birth. — quoted: "your official birth date is February 9th, 1907"
  [mof9fa185df5] The father secures tickets and goes ahead to the United States alone. — quoted: "So my father got tickets, went to the United States."
  [mo2941456e12] She has no memory of Ellis Island processing at all. — quoted: "No"
thread — Family enterprise and the gendering of skill (t705b49e6a3):
  [mo55bb92952e] The mother's bakery business is the first trade mentioned, before the father's. — quoted: "She's—bakery business."
  [mo055e8158c3] The interviewer assumes the bakery was the father's enterprise, not the mother's. — quoted: "That was his business, uh-huh."
  [mod0de02cde9] The father was explicitly not a baker by trade but a tailor. — quoted: "My father was not—my father was not a baker."
  [mofb8c8685d7] The mother is identified as the baker; the father became one through her. — quoted: "My mother was the b—the baker."
  [mobb78fd3f61] The mother's baking skill predates both migrations, rooted in Poland before London. — quoted: "had your mother been a baker in Poland before she ever got to—"
  [mo744bfbe4f5] The New York bakery is named after the father's surname, not the mother's skill. — quoted: "Floun's."
thread — Household subsistence and expected labour (te03fdf696d):
  [mo83e3b6af93] Children performed for money in steerage, dancing and singing while passengers threw coins. — quoted: "used to dance and sing and they used to throw money down"
  [moe263a2557a] The mother refused to let children accept the thrown money, marking a labour boundary. — quoted: "My mother wouldn't let—let us."
  [mof706e0df3a] The school released children from attendance so they could help in the household. — quoted: "And they says, "Let them stay home and help you.""
  [moa1a6c68818] Holiday bakery work for children involved decorating macaroons with almonds and cherries. — quoted: "we used to you put almonds and cherries on the macaroons"
  [mo8f36ad134b] Children's bakery help is described as casual, routine, and expected. — quoted: "Yeah, we—we helped out."
thread — What migration narrows and separates (t70f91d46ab):
  [mo3a237a8517] Two sisters were left behind in Poland when the family emigrated to America. — quoted: "we had two sisters in Poland we left there—"
  [moabb3898bf2] The mother left them because she feared she could not care for them. — quoted: "my mother was afraid she wouldn't be—be able to take care"
  [mo61b7b34479] The younger sister who made the crossing to America died. — quoted: "She died."
  [mo3e22687253] The father went to America a full year before the rest of the family. — quoted: "The year before."
  [mo2035ea1cb6] The mother followed because the father went, not from her own desire to emigrate. — quoted: "as long as my father went, she wanted to come too"
```
