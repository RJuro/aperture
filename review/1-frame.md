# FRAME — as sent to the model

_2105 words · ≈3044 tokens_

## SYSTEM

```
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

3. `title` is at most 10 words. It names the material; it does not describe it.

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
```

## USER

```
WHAT THE SPEAKER SCAN FOUND

Before you were shown anything, Python scanned every line of the raw material for a `NAME:` cue
at the start of a line and counted how often each label recurs. A speaker recurs; an archival
header label appears once. This is evidence, not a conclusion — read it against the material.

  PHILLIPS: 77 lines
  GRANDE: 75 lines
  BIRTH DATE: 1 line
  INTERVIEW DATE: 1 line
  INTERVIEW LOCATION: 1 line
  INTERVIEWER: 1 line
  MITZI STACKHOUSE: 1 line
  RECORDING ENGINEER: 1 line
  RUNNING TIME: 1 line
  TRANSCRIPT RECONCEIVED BY: 1 line

Recurring 3 times or more: PHILLIPS, GRANDE

THIS IS THE FIRST DESCRIPTION OF THIS MATERIAL

Nobody has described it before, so there is nothing to correct.

THE MATERIAL

The opening and the closing of the raw text, exactly as it is stored.

<<<
﻿


	DP-40
	MARY YANKOVIK GRANDE
	BIRTH DATE:  1910
	INTERVIEW DATE:  AUGUST 28, 1989
	RUNNING TIME:  50:00
	INTERVIEWER:  ANDREW PHILLIPS
	RECORDING ENGINEER:  SAME
	INTERVIEW LOCATION:  DENVER, CO
	TRANSCRIPT ORIGINALLY PREPARED BY:  NANCY VEGA, 1989
	TRANSCRIPT RECONCEIVED BY:  CHICK LEMONICK, 2/1996
	TRANSCRIPT NOT REVIEWED


	YUGOSLAVIA, 1920
	AGE 10
	SHIP NAME NOT RECALLED


	PHILLIPS:	This Andrew Phillips.  It's Monday the 28th of August, 1989.  I'm with Mary Grande, spelled G-R-A-N-D-E.  This is Interview Number 414 [DP-40] of the Ellis Island Oral History Project.  Commencing this interview at a little bit before 12:30.  Mrs. Grande, could you start by telling me what your name is and where you immigrated from.

	GRANDE:	What my maiden name was?

	PHILLIPS:	Uh, let me just get the microphone set up.  That's fine.  		That's fine.

	GRANDE:	My maiden name was, uh, Marija Yankovik.  And we came, my mother and I came from Kandijaright over Novo Mesto, which is in Yugoslavia now.  Originally it was Austria/Hungary.  And we came here, we left there August 12, 1920 and we stayed a few days in Trieste, Italy.

	PHILLIPS:	Can you spell that for me, please?

	GRANDE:	T-R-I-E-S-T-E, Italy.  And then we got on the ship.  I believe the name of it was America.  And it was right after World War One, so they stopped it in a lot of places.  In London, and I suppose Paris, and all over.  But part of our clothes was stolen in Trieste, so a fellow that my mother knew, he went in, I believe, in London, to buy some clothes for us.  He could speak American.  He came back from the States and who he bought back I don't remember.  But, uh, he bought some clothes so we had something to change in to, to wear.

	PHILLIPS:	Before you tell us about travelling from your home country to the United States, could you tell us a little bit about what your home was like.  For instance, start by telling us what your parents did for a living.

	GRANDE:	Well, my father was here in the States since 1911.  In 		fact, he was, during World War one here in the United States, and my mother was a farmer, and she raised some cattle and bartered with them.

	PHILLIPS:	Tell me what your home was like.  What did it look like?

	GRANDE:	It was an average peasant home.  It was three rooms, living room and kitchen in the middle and a small room on the side.  And then facing what would be, I guess, the east side was half, was a barn where the cattle were.

	PHILLIPS:	So the cattle were actually, they were part of the 		house.  The barn was part of the house.

	GRANDE:	Yes.

	PHILLIPS:	Explain that to us, what was that like.

	GRANDE:	Well, it was all one building and there were, later on they made that as all one room, but at that time we had a half a room was like for the barn, for the cows, or when my brother had horses it was there.  And then there was a manure pile just to the side of it.  And the majority of people had it similar like that.

	PHILLIPS:	Why were the houses and the barns constructed together 		like that?

	GRANDE:	It's been historical, as far as I know.  I don't know any different.  They don't do it now any more like that, but they used to.

	PHILLIPS:	And what was it like for a little girl to be living so close to the animals?  Did you enjoy that, or were you--

	GRANDE:	Oh, yes.  I enjoyed it because they were part of my life.  In fact, I had a pet cow that I loved very much.  And then the pigs were, the pig sty was just across from the kitchen door, just a little ways away.  So all the animals were right close to the house.  It was just a regular home life between the animals.  You wouldn't bring them in the house, but you had them outside.

	PHILLIPS:	So you could, when you were sitting down to eat, for instance, you could look out the kitchen door and there were the pigs.

	GRANDE:	Right.

	PHILLIPS:	And you had names for the pigs?

	GRANDE:	Sometimes.

	PHILLIPS:	Did you like the pigs?

	GRANDE:	Oh, yeah.  They used to slaughter them in winter and save some meat, cured it, for the summer.  And some of it was for right away.  Not too much fresh, but mostly cured.

	PHILLIPS:	How did they cure it?

	GRANDE:	Uh, salt and water and pack it, put some rocks on it and 		let it stay like that and then they would smoke it.

	PHILLIPS:	Did you used to help do that?

	GRANDE:	I had to help with, when they killed the pigs I had to catch the blood.  I didn't like it, but that was part of my job.

	PHILLIPS:	Can you perhaps remember actually what you did?  Can you 		describe that for us?

	GRANDE:	Well, when my mother got the fellow to kill the pig, well, I had to hold the pan there and catch the blood, because they made the blood sausage out of that.  Of course, they worked with it to make it good, and then they made the blood sausage and usually they fried the liver right away, good and fresh.  That was really good.  Then later, out of the other leftover pieces of regular meat they'd make smoked sausage and they'd smoke them and have them for during the summer.  They had for special occasions, or when they had hired help.  They had different pieces for different times.

	PHILLIPS:	So you got a lot of different, uh, meats.  You got your money's worth out of those little pigs across the way from the kitchen.

	GRANDE:	Oh, yes.  Oh, yes. Oh, yes.  And then, of course, we had 		the milk from the cows.  We didn't kill the cows at home.  It's very seldom we had beef but, uh, we chickens, so there was chicken meat and eggs and pigs and milk and cheese, whatever.  (Sound of door opening in the background.)

	MITZI STACKHOUSE:  Hello.

	GRANDE:	Hi.

	PHILLIPS:	Just a small interruption there.  Clyde and Mitzi 		Stackhouse.  Mitzi is the daughter--

	GRANDE:  Yeah.

	PHILLIPS:	--of Mrs. Grande.  Okay.  We were back, you were telling 		us a little bit about your life on your farm.  Can you tell us, perhaps, how you warmed the place in the wintertime.  What, was it cold for you?

	GRANDE:	Well, we, uh, heated it with the wood.  The

[... 20482 characters not shown ...]

My husband wasn't making much.  Worked every other week and the girls were getting to the point, being in school, we sent them to parochial school.  And naturally we had to pay.  It wasn't like now that somebody else pays for them a lot.  And then, uh, U finally got a job in a packing house, which I worked close to thirty years in it.  And in between every so often I had to have different surgeries and I'd be home.

	PHILLIPS:	What kind of work, excuse me, what kind of work 		particularly were you doing?

	GRANDE:	Cutting up meat, pork and beef.  Cut it for scraps for 		sausage and stuff.  And then later on she came into the packing house and she worked with me for a while, and then she went down in the smokehouse where they have to smoke bacon and ham, and she worked there until she had to give up medically on account of it.

	PHILLIPS:	Let me explain for identification who she is.

	GRANDE:	My daughter, Mitzi.

	PHILLIPS:	M-I-T-Z-I.  Mitzi Stackhouse.

	GRANDE:	Yeah.  I have another daughter, Jenny Musk.  She's a 		nurse.  She lives way up in Northglen.

	PHILLIPS:	Okay.  Unless there's something else you think you'd 		like to us all.

	GRANDE:	Well, we became, my husband and I became American citizens in 1932 and we tried to vote every time ever since.  Maybe not right, but we try our best.  And every time I go back to Europe I'm happy to come back.  This is my country.

	PHILLIPS:	Okay.  That finishes Interview Number 414 [DP-40] with 		Mary Grande,  It's five after one.

>>>

Answer now with the JSON object, and nothing else.
```
