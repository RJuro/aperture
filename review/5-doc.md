# DOC — as sent to the model

_7567 words · ≈10481 tokens_

## SYSTEM

```
You are reading one piece of qualitative material for a researcher, and writing what the reading
found in it. You write two things: an account of the material as a whole, and, for each theme, a
thread — that theme's key moments through this material, in the order they occur.

A moment is one specific claim resting on one quote.

The researcher reads your claims down one side of the screen with the material open beside them.
So a claim must say something a person could not have guessed from the theme's name. Name what
actually happens: who does what, what changed, what is at stake, what is refused. A claim that
would fit almost any material in the corpus is a wasted line.

  Good:  "The stall, not the land, is what fed them; the farm is described as a place they left."
  Good:  "He dates the decision to leave from his brother's death, not from any hardship."
  Bad:   "Work shapes what is said here."          (a label, not a finding)
  Bad:   "The speaker discusses employment."       (true of half the material)
  Bad:   "Leaving is an important theme (2)."      (numbering is not content)

Five rules. Each one carries the same weight, and each one is checked.

1. Every claim rests on a quote. A moment without a quote is not a moment.
2. Every quote is copied EXACTLY from the material below, word for word, punctuation and all, at
   most 12 words long. A quote you cannot copy exactly is a claim you must not make: leave it out.
   Every quote is searched for in the material afterwards, character by character, and a moment
   whose quote is not there is thrown away, so an invented quote costs you the claim.
3. Every quote carries the number printed at the start of the line it was copied from. If the
   number is wrong but the quote is real, the quote wins and the number is corrected for you.
4. Every thread holds at least 4 and at most 14 moments, in the order they occur in the material.
   Draw them from across the whole of it — beginning, middle and end — not from one passage.
   A thread that stops a third of the way down has not read the rest.
   Give every theme below a thread if the material carries it at all, and give them comparable
   depth: a corpus where one theme has ten moments and another has four, in the same material,
   usually means the second was not looked for as hard. A theme genuinely absent here gets no
   thread; say so in the summary rather than padding one.
5. Every word outside the quotes is your own, and none of them assume a speaker. This material may
   be an interview, a focus group, field notes, a document, or answers to an open question. Say
   who speaks only where the material itself names them.

The caps, as numbers: summary 320 words. brief 120 words. claim 30 words. quote 12 words. moments
per thread: at least 4, at most 14. One thread per theme, and only for themes listed below.

Return JSON in exactly this shape, and nothing else:

{
  "summary": "The researcher reads this before anything else, so write it as an introduction to
              the material, at most 320 words, in flowing prose and not as a list. Say what this
              material is and whose account it is. Then set out the main narratives running
              through it — the story it tells about itself, and the story it tells without
              meaning to. Name each theme you wrote a thread for and say in a sentence what that
              thread follows and where it goes. End with what is thin, contested or missing: a
              theme you could not find here, a question the material dodges, a claim it makes
              only once. Do not repeat the description you were given above; that one says what
              the material IS, and this one says what reading it FOUND.",
  "threads": [
    {
      "theme_id": "t1a2b3c4d5",
      "moments": [
        {"claim": "The stall, not the land, is what fed them; the farm is a place they left.",
         "anchor": "we had a stall in the market",
         "sid": "S118"},
        {"claim": "Work came through a cousin already in the city, before any paperwork.",
         "anchor": "my cousin got me in at the yard",
         "sid": "S204"},
        {"claim": "He describes the wage as good and the hours as unsurvivable, in one breath.",
         "anchor": "the money was fine but it broke you",
         "sid": "S307"},
        {"claim": "By the end he calls the trade a trap, having called it a rescue earlier.",
         "anchor": "it was a trap, that trade",
         "sid": "S511"}
      ]
    }
  ],
  "brief": "At most 120 words for whoever reads the NEXT piece of material, about the CORPUS and
            not about the piece you have just read. You were shown the brief as it stood; revise
            it, do not replace it. Keep what still holds across everything read so far, drop what
            the newest material has contradicted, and add only what changes how the next piece
            should be approached — a recurring shape to expect, a question that keeps going
            unanswered, a kind of passage that keeps being missed. If this brief could only have
            been written about the material in front of you, it is the wrong brief."
  "people": [{"name": "M. Grande", "aliases": ["Grande"], "role": "participant"}]
}

No keys other than these four. No text outside the JSON object.
```

## USER

```
Write what the reading found in this material: a summary, one thread for every theme that has at least 2 quotable moments here, the people it names, and the brief for whoever reads the next piece.

WHAT THIS CORPUS IS LIKE, written after the last piece was read:

This corpus centres on oral histories of migration to the United States from the Ellis Island project. Two interviews show a shared pattern: subsistence or family-enterprise economies described as ordinary rather than hard, and women's portable skills sustaining households across countries. The first interview's industrial-wage-labour pattern is not universal — the second family runs bakeries, not factories. Watch for enterprises where the woman's skill is credited to the man, and for children's labour framed as routine duty rather than hardship (confirmed twice). Chain settlement by relatives persists. The emotional cost of migration remains refused: both interviewees answer with 'nice.' Bureaucratic labour appears but is dimly remembered.

WHAT THE RESEARCHER IS LOOKING FOR, in their words:

how people make a living after arriving, and what it costs them

WHAT THIS MATERIAL IS, worked out from its shape before anything was read. Your summary re-writes
this into what the reading found; both are kept, so do not simply repeat it:

An oral history interview from the Ellis Island Oral History Project, recorded on August 28, 1989, in Denver, Colorado, with a running time of approximately fifty minutes. The interviewer is Andrew Phillips and the interviewee is Mary Grande, née Marija Yankovik, born in 1910. She recounts her childhood in a peasant home near Novo Mesto in what was then Austria-Hungary and is now Yugoslavia, her 1920 voyage to the United States with her mother, and her subsequent life in America including marriage, work in a packing house, and naturalisation in 1932. A brief interruption occurs midway when Grande's daughter enters the room.

HOW THIS MATERIAL IS LAID OUT:

kind: interview
laid out as: turns
called: Ellis Island Oral History: Mary Grande
people who speak in it: PHILLIPS = Andrew Phillips (interviewer); GRANDE = Mary Grande (participant)

THE THEMES this project is working with. A thread must name one of these ids in `theme_id`:

t322ab0effe  Administrative and civic labour of becoming — Administrative labour of emigration is remembered where a mother bore it — repeated trips to courts and offices — and absent where a child was too young to notice.
t705b49e6a3  Family enterprise and the gendering of skill — A woman's baking skill sustains a family enterprise across three countries, yet the business carries the father's name and the interviewer assumes it was his. Appears in one material only; absent from the farm-and-mine interview.
te03fdf696d  Household subsistence and expected labour — Women's labour and children's routine duty sustain every household — through barter, farm work, or bakery enterprise — framed as ordinary, not hardship. Spans the full corpus; the gendered attribution of that labour diverges sharply between materials.
tf26da42d35  Industrial wage work as livelihood after migration — Industrial wage work — mining, smelting, butchering — is livelihood after migration in one interview only. Its cost is the body that cannot sustain it. Entirely absent from the bakery-family interview.
t256893f66d  The bodily cost of industrial work — Industrial wage labour disables workers across two generations of one family — father, daughter, granddaughter each driven out by health. Absent from the bakery interview, whose enterprise carries no such bodily cost.
t70f91d46ab  What migration narrows and separates — Migration splits families by distance, death, and prior departure in both materials. A woman's productive range narrows to domestic tasks in one; in the other, separation is felt through sisters left behind and a child lost after the crossing.

WHAT THE READING ALREADY MARKED in this material, by passage number:

Barter as subsistence exchange — Passages where goods or livestock are exchanged directly for other goods rather than for money, as a way of sustaining a household. — 3 passages: S042, S141, S240
Bureaucratic labour of emigration — Passages describing the offices, courts, approvals, and trips required to secure permission to leave or travel. — 3 passages: S255, S275, S278
Chain settlement by shared origin — Passages explaining why people from the same region or nationality cluster in one place, citing mutual integration or following earlier settlers. — 3 passages: S318, S401, S402
Children's labour as expected routine — Passages where a child's contribution to household or farm work is presented as a normal part of growing up rather than as hardship. — 3 passages: S080, S118, S167
Family separation across migration — Passages naming which family members went ahead, which stayed behind, and which died before they could join the migration. — 3 passages: S041, S264, S265
Health decline ending wage work — Passages where a worker's deteriorating health is given as the reason they can no longer hold a job. — 3 passages: S335, S377, S378
Medical exit from industrial work — Passages where a worker leaves or pauses a job because of surgeries or medical conditions attributable to the work. — 2 passages: S412, S416
Naturalisation as civic belonging — Passages where acquiring citizenship and voting are described as acts that mark belonging in the new country. — 2 passages: S427, S429
Packing-house work as long-term livelihood — Passages where meatpacking or similar industrial food-processing work is described as a sustained source of income over many years. — 3 passages: S411, S414, S415
Wage labour in extractive industry — Passages where earning a living is tied to work in mines, smelters, or similar extraction sites. — 3 passages: S332, S376, S377
Women's farm labour as ordinary — Passages where women's agricultural or physical work on a farm is described as normal and expected, not exceptional. — 2 passages: S137, S142
Work narrowing after migration — Passages where a person's range of productive activity shrinks after moving, especially from diverse subsistence work to domestic tasks only. — 1 passages: S359

WHAT THE RESEARCHER SAID about this material, in their own words. Take it as instruction:

The researcher has not said anything about this material yet.

THE MATERIAL. Each line starts with the number a quote from that line must cite:

S000  DP-40
S001  MARY YANKOVIK GRANDE
S002  BIRTH DATE:  1910
S003  INTERVIEW DATE:  AUGUST 28, 1989
S004  RUNNING TIME:  50:00
S005  INTERVIEWER:  ANDREW PHILLIPS
S006  RECORDING ENGINEER:  SAME
S007  INTERVIEW LOCATION:  DENVER, CO
S008  TRANSCRIPT ORIGINALLY PREPARED BY:  NANCY VEGA, 1989
S009  TRANSCRIPT RECONCEIVED BY:  CHICK LEMONICK, 2/1996
S010  TRANSCRIPT NOT REVIEWED
S011  YUGOSLAVIA, 1920
S012  AGE 10
S013  SHIP NAME NOT RECALLED

S014  PHILLIPS:	This Andrew Phillips.
S015  It's Monday the 28th of August, 1989.
S016  I'm with Mary Grande, spelled G-R-A-N-D-E.
S017  This is Interview Number 414 [DP-40] of the Ellis Island Oral History Project.
S018  Commencing this interview at a little bit before 12:30.
S019  Mrs.
S020  Grande, could you start by telling me what your name is and where you immigrated from.

S021  GRANDE:	What my maiden name was?

S022  PHILLIPS:	Uh, let me just get the microphone set up.
S023  That's fine.
S024  That's fine.

S025  GRANDE:	My maiden name was, uh, Marija Yankovik.
S026  And we came, my mother and I came from Kandijaright over Novo Mesto, which is in Yugoslavia now.
S027  Originally it was Austria/Hungary.
S028  And we came here, we left there August 12, 1920 and we stayed a few days in Trieste, Italy.

S029  PHILLIPS:	Can you spell that for me, please?

S030  GRANDE:	T-R-I-E-S-T-E, Italy.
S031  And then we got on the ship.
S032  I believe the name of it was America.
S033  And it was right after World War One, so they stopped it in a lot of places.
S034  In London, and I suppose Paris, and all over.
S035  But part of our clothes was stolen in Trieste, so a fellow that my mother knew, he went in, I believe, in London, to buy some clothes for us.
S036  He could speak American.
S037  He came back from the States and who he bought back I don't remember.
S038  But, uh, he bought some clothes so we had something to change in to, to wear.

S039  PHILLIPS:	Before you tell us about travelling from your home country to the United States, could you tell us a little bit about what your home was like.
S040  For instance, start by telling us what your parents did for a living.

S041  GRANDE:	Well, my father was here in the States since 1911.
S042  In 		fact, he was, during World War one here in the United States, and my mother was a farmer, and she raised some cattle and bartered with them.

S043  PHILLIPS:	Tell me what your home was like.
S044  What did it look like?

S045  GRANDE:	It was an average peasant home.
S046  It was three rooms, living room and kitchen in the middle and a small room on the side.
S047  And then facing what would be, I guess, the east side was half, was a barn where the cattle were.

S048  PHILLIPS:	So the cattle were actually, they were part of the 		house.
S049  The barn was part of the house.

S050  GRANDE:	Yes.

S051  PHILLIPS:	Explain that to us, what was that like.

S052  GRANDE:	Well, it was all one building and there were, later on they made that as all one room, but at that time we had a half a room was like for the barn, for the cows, or when my brother had horses it was there.
S053  And then there was a manure pile just to the side of it.
S054  And the majority of people had it similar like that.

S055  PHILLIPS:	Why were the houses and the barns constructed together 		like that?

S056  GRANDE:	It's been historical, as far as I know.
S057  I don't know any different.
S058  They don't do it now any more like that, but they used to.

S059  PHILLIPS:	And what was it like for a little girl to be living so close to the animals?
S060  Did you enjoy that, or were you--

S061  GRANDE:	Oh, yes.
S062  I enjoyed it because they were part of my life.
S063  In fact, I had a pet cow that I loved very much.
S064  And then the pigs were, the pig sty was just across from the kitchen door, just a little ways away.
S065  So all the animals were right close to the house.
S066  It was just a regular home life between the animals.
S067  You wouldn't bring them in the house, but you had them outside.

S068  PHILLIPS:	So you could, when you were sitting down to eat, for instance, you could look out the kitchen door and there were the pigs.

S069  GRANDE:	Right.

S070  PHILLIPS:	And you had names for the pigs?

S071  GRANDE:	Sometimes.

S072  PHILLIPS:	Did you like the pigs?

S073  GRANDE:	Oh, yeah.
S074  They used to slaughter them in winter and save some meat, cured it, for the summer.
S075  And some of it was for right away.
S076  Not too much fresh, but mostly cured.

S077  PHILLIPS:	How did they cure it?

S078  GRANDE:	Uh, salt and water and pack it, put some rocks on it and 		let it stay like that and then they would smoke it.

S079  PHILLIPS:	Did you used to help do that?

S080  GRANDE:	I had to help with, when they killed the pigs I had to catch the blood.
S081  I didn't like it, but that was part of my job.

S082  PHILLIPS:	Can you perhaps remember actually what you did?
S083  Can you 		describe that for us?

S084  GRANDE:	Well, when my mother got the fellow to kill the pig, well, I had to hold the pan there and catch the blood, because they made the blood sausage out of that.
S085  Of course, they worked with it to make it good, and then they made the blood sausage and usually they fried the liver right away, good and fresh.
S086  That was really good.
S087  Then later, out of the other leftover pieces of regular meat they'd make smoked sausage and they'd smoke them and have them for during the summer.
S088  They had for special occasions, or when they had hired help.
S089  They had different pieces for different times.

S090  PHILLIPS:	So you got a lot of different, uh, meats.
S091  You got your money's worth out of those little pigs across the way from the kitchen.

S092  GRANDE:	Oh, yes.
S093  Oh, yes.
S094  Oh, yes.
S095  And then, of course, we had 		the milk from the cows.
S096  We didn't kill the cows at home.
S097  It's very seldom we had beef but, uh, we chickens, so there was chicken meat and eggs and pigs and milk and cheese, whatever.
S098  (Sound of door opening in the background.)
S099  MITZI STACKHOUSE:  Hello.

S100  GRANDE:	Hi.

S101  PHILLIPS:	Just a small interruption there.
S102  Clyde and Mitzi 		Stackhouse.
S103  Mitzi is the daughter--

S104  GRANDE:  Yeah.

S105  PHILLIPS:	--of Mrs.
S106  Grande.
S107  Okay.
S108  We were back, you were telling 		us a little bit about your life on your farm.
S109  Can you tell us, perhaps, how you warmed the place in the wintertime.
S110  What, was it cold for you?

S111  GRANDE:	Well, we, uh, heated it with the wood.
S112  There was times that my mother later on got some coal, but not very much.
S113  It was mostly wood.
S114  And the forest wasn't far from the house, so we used to get the wood there.
S115  And, of course, she had quite a bit hauled in the fall, so we would have wood.

S116  PHILLIPS:	You say hauled in the fall, she got the wood during the 		fall?

S117  GRANDE:	Yeah, so we'd have it all winter long.
S118  But she would cut it up herself, saw and chop it and, of course, later on when I was bigger I tried to help, which I wasn't much good.
S119  But I helped on the farm what little I could, and I had a mile or better to go to school.

S120  PHILLIPS:	Before you tell us about going to school, can you tell 		me what your life was like for your mother.
S121  She was, just one moment.
S122  We need for you to be as quiet as possible (addressing daughter and son-in-law).

S123  GRANDE:	Well, originally she was a widow and she married her husband.
S124  And then she bought this home.
S125  And then when she met--  (Break in tape.)

S126  PHILLIPS:	Okay, Mrs.
S127  Grande, could you continue please?
S128  I think we were just talking about how difficult it was for your mother.
S129  You said she was a widow and married again.

S130  GRANDE:	She was a widow, and she had two boys.
S131  One died before, 		but two of them were living, so she was raising them.
S132  And then I came along after she married with my husband, uh, my father.
S133  And, uh, he came to the States, and there was another sister born after that.

S134  PHILLIPS:	Could you tell me, I mean, is sounds like your mother must have been a tremendously strong and hardy woman to look after a farm and bring up these children and chop the wood.
S135  Was that normal?

S136  GRANDE:	Normal, normal.
S137  Most all the women did similar work, 		worked on the farm and just took care of everything.
S138  There was quite a few men that came to the States to make a livelihood and then probably come back, which a lot of them never did.
S139  A lot of them took their family over here, but a lot of them, some did help.
S140  But during the wartime they couldn't help back and forth at all.
S141  So my mother used to kind of sell milk and eggs and whatever she could, products.
S142  Not too much off the farm because that was our livelihood throughout the year.
S143  And you had to keep some for the seeds for next year.

S144  PHILLIPS:	Did you tell me how ,any were in your family?
S145  Could you 		tell me that?

S146  GRANDE:	Well, there was, actually, uh, four, five, with my mother.
S147  And then my sister died.
S148  Oh, she was about a year old when she died, so there was four of us.
S149  And, uh, we'd done the best we could, just like a lot of others.

S150  PHILLIPS:	Why did your sister die?
S151  What did she die of?

S152  GRANDE:	Childhood problems.

S153  PHILLIPS:	Was that very common in your village?

S154  GRANDE:	Well, there was quite a few children that did die.
S155  I don't know exactly what the cause or what it was, but she died.

S156  PHILLIPS:	Now, could you tell me, please, about going to school.
S157  You said you had to walk to school.
S158  Tell me about your school days.

S159  GRANDE:	Well, it was a good mile, or maybe further, past the cemetery, which I wasn't scared of.
S160  I didn't mind it a bit.
S161  And we crossed the track.
S162  And, of course, one time I didn't pay attention, the weather as bad and I had my head down, the rails were down that the train was going to come,and I bumped in there, which wasn't very good.
S163  But that woke me up to pay attention.
S164  But, uh, we walked back and forth.
S165  We didn't think nothing of it.
S166  That was normal.
S167  Nobody had cars or anything, and they didn't take them with the wagon because there was too much other work to be done.
S168  And then when my brother got older, he was quite a bit older than me, well, uh, he went and stayed with my aunt for a while on a different part of the area.
S169  And so my mother and I were alone for quite a while.
S170  And then she bartered with the cattle, and sometimes I'd stay with the neighbors overnight when she'd go and barter to different places.
S171  And all that she done, all of that walking.
S172  She didn't have no other transportation.
S173  So then after the war, when my dad started writing about coming to the States, naturally we were all enthused about it.
S174  I don't know if my mother was enthused or not, but I was.

S175  PHILLIPS:	Tell me what it was like for you during the war.
S176  Do you 		have any memories of that?

S177  GRANDE:	Well, we had to have refugees from the Italian side, and 		the extra room that we had that was like, it could have been a summer kitchen.
S178  Well, we had to give that to the refugees and everybody had to share their home with the refugees.
S179  And, of course, they spoke quite a bit Italian, but we managed to understand each other pretty good.

S180  PHILLIPS:	Do you know, or do you remember, whether it was the government that forced you to take the refugees, or the people in the community just did it?

S181  GRANDE:	It was more or less a government decision that everybody 		would take some refugees.
S182  And we went down by the river which was about a good half-a-mile or further to wash clothes on the rocks.
S183  I don't know if you ever heard of it or not, but that was, and then my mother would take them sometimes over to the hospital which was the other way.
S184  It wasn't as far.
S185  The only thing, she didn't like to go there because there was too much bloody stuff in there.

S186  PHILLIPS:	Why?

S187  GRANDE:	Uh, to wash clothes in shelter instead of outdoors.

S188  PHILLIPS:	But you said there was some bloody stuff in there.
S189  Why?

S190  GRANDE:	Well. it was a hospital, and they'd let women come there 		and wash clothes but naturally the hospital supplies were going through first.

S191  PHILLIPS:	So the rubbish and the effluent from the hospital was 		thrown into the river.

S192  GRANDE:	Yeah.

S193  PHILLIPS:	And so you probably tried to wash upstream from the 		hospital.

S194  GRANDE:	Oh, yes.
S195  Oh, yes.
S196  Definitely.
S197  And there was two hospitals.
S198  One on one side of the river was for men, and the one on the other side of the river was for women.
S199  They didn't have them all combined together like they have over here now.
S200  They have them like that now too over there.
S201  But at that time there it was each separate.
S202  And there was a castle right across the street from the hospital, which is now tuberculosis sanitarium.
S203  They don't have no castles no more.
S204  So there's quite a bit of changes any more, too.

S205  PHILLIPS:	But in those days who lived in that castle?

S206  GRANDE:	The Austrian people.
S207  They were the higher-ups from the Austrian, not government, but they were well-to-do and all that.
S208  But--

S209  PHILLIPS:	What language did you speak?

S210  GRANDE:	Actually Slovanian, and we had to take German.

S211  PHILLIPS:	Not Hungarian.

S212  GRANDE:	No, no.
S213  German was our main language, like in office or 		different places, you almost had to learn how to speak German to get along with them.

S214  PHILLIPS:	That was the official language.

S215  GRANDE:	Right.

S216  PHILLIPS:	So how many languages were spoken, then, in your 		village?

S217  GRANDE:	The two.
S218  German and Slovanian.

S219  PHILLIPS:	Do you remember much, at that age, about any political 		structures or political problems, or--

S220  GRANDE:	All I kind of remember when, I guess it was about 1918 when they was going to overthrow Austria/Hungary altogether and change it to Yugoslavia.

S221  PHILLIPS:	When who was?

S222  GRANDE:	Well, the government was a changing deal because the--

S223  PHILLIPS:	I'm sorry, which government are you talking about?

S224  GRANDE:	Part of Yugoslavia.
S225  And the First World War started 		down in Sarajevo in what is now Yugoslavia.
S226  It's down more or less in the Serbian section.
S227  That's where Ferdinand got killed and World War One started.  and I kind of remember when they had the meetings around 1918 and '19, '20 and after all that, well, it became Yugoslavia.
S228  So actually I was born in Austria/Hungary and came here from Yugoslavia.

S229  PHILLIPS:	Do you remember what your older relatives, or your mother, or people who came to your house, were talking about during those times?
S230  Were they afraid?
S231  Were they excited?
S232  What was the atmosphere like?

S233  GRANDE:	Well, during the war they were excited and all that but, 		uh, not too much, because you just had to go along.
S234  There were restrictions on certain things you couldn't buy.
S235  And, uh, the people that lived in the city, which was across the river from us, they didn't have food, and we had more food because we were out in the country.
S236  So for any small amount of food, either eggs, or chicken, or no matter what, or milk, they would share clothing because they had plenty of clothes, but they had a hard time getting food.

S237  PHILLIPS:	And so that was, did that become a barter system that 		you, part of the barter system you were describing before, or not?
S238  Or did they pay money for the food?

S239  GRANDE:	Oh, no.
S240  It would be a bartering.
S241  I had, I usually had real nice clothes and, uh, when we were coming here to the States I'd have had beautiful clothes if it wouldn't be stolen in Italy while we were waiting for the ship.
S242  We had to stay there three days and they had us, they had my mother put the suitcases in the storage, and when she went to get them they were gone.
S243  Not only hers, a lot of others too.

S244  PHILLIPS:	Meanwhile, back before that happened, how did the people 		cross that river?
S245  Was there a boat, or a bridge, or--

S246  GRANDE:	Oh, further down there was a big ridge.
S247  There was, uh, or they went with wagons and whatever needed to be.
S248  Of course, you don't see the wagons now any more.
S249  All you see is cars.
S250  But at that time there was wagons.

S251  PHILLIPS:	When was it that you first learned that you were going 		to travel to America?

S252  GRANDE:	Oh, it was, oh, I guess about, not the very first part, 		but about towards the second part of 1920.

S253  PHILLIPS:	And tell me how you learned about that?

S254  GRANDE:	Well, my mother was telling me about the letters she got 		from my father, and then he sent us the tickets.
S255  And she had to go to different places to get it approved and all that.
S256  But, uh, not too many.
S257  Like some of them had to go through more than she did.
S258  And I didn't have to go anywhere because I was a minor.
S259  So, but on the passport, uh, her and my pictures were together, so everything went, whatever she got, it was for me, too.

S260  PHILLIPS:	And how about the other children?

S261  GRANDE:	Well, my oldest brother, he had to go in the army.
S262  See, 		they have to serve three years all the time.
S263  But, uh, he had to go in.
S264  And then the other one, they was going to bring him here.
S265  And in the spring, when he was supposed to go kind of like to report for the army, he was on the wagon and he fell or jumped or whatever, and he got killed.
S266  So then this one got to come from the army earlier to take over the farm.

S267  PHILLIPS:	Because his brother had been killed.

S268  GRANDE:	Yeah.

S269  PHILLIPS:	And so did your brother accompany you to the United 		States?

S270  GRANDE:	No.
S271  He would have to come after it.
S272  It was just my 		mother and I that came then.

S273  PHILLIPS:	All right.
S274  Now, tell me what you actually had to, to do 		to get your papers.

S275  GRANDE:	Well, I wasn't with my mother too much, but she had to go through quite a bit of different courts and different offices and get approvals of, oh, different higher-ups that were in line with the travelling and all.
S276  So she had to make quite a few different trips.

S277  PHILLIPS:	Do you know how long it took her to get the approval?

S278  GRANDE:	Oh, it was about, the last month before we left it seemed like she was always coming or going to different places.

S279  PHILLIPS:	And meanwhile your father was in America?

S280  GRANDE:	Yeah.

S281  PHILLIPS:	So tell me about finally leaving.
S282  How did you feel?

S283  GRANDE:	Oh, I was anxious just to get here to meet my dad.

S284  PHILLIPS:	Weren't you going to miss your friends?

S285  GRANDE:	I didn't think about it then.

S286  PHILLIPS:	How old were you when you were leaving?

S287  GRANDE: 	Ten.
S288  I was just anxious to meet my dad.

S289  PHILLIPS:	And how had your school life been?
S290  Had you enjoyed 		school back in--

S291  GRANDE:	Well, I like school.
S292  I had average grades.
S293  I wouldn't say they were exceptional, but I had them average, and I had to take German for two years in third and fourth grade.
S294  Of course, Later on when I came here there was no German people around, so I just kind of forgot it.
S295  But, uh, it would be nice if I had remembered it.

S296  PHILLIPS:	So how did you, you got to Trieste, think you described.

S297  GRANDE:	We went by train.
S298  We went by train, and then we got to 		where we had, where my mother checked in the suitcases and, uh, we just had like a barn place.
S299  It wasn't a hotel or anything, where we stayed for, till 15th.
S300  And then we went on the ship.
S301  And, uh, my dad paid for first class but they put us down on the bottom and then this one fellow spoke up that was, uh, here before, and he seen my mother's card, and he said, "You don't belong down here.
S302  You should go up higher.
S303  And we had mostly fish and macaroni on the ship, which I didn't like very well, but you had to eat something.

S304  PHILLIPS:	So did you manage to get up to first class?

S305  GRANDE:	Not first.
S306  But we got up to second.
S307  We got up to second class.
S308  It was better, but nothing to brag about compared to what the ships are now.

S309  PHILLIPS:	Did you still have to eat fish and macaroni?

S310  GRANDE:	Oh, yes.
S311  I guess that was the basic, it was an Italian ship, so I guess that's what it was.
S312  And they stopped it in London, they stopped it in different places until finally I guess they got a call from the United States where the people are that were supposed to be in by a certain time and they weren't, and so the ship started going real fast, and finally got to New York.

S313  PHILLIPS:	Do you remember that?

S314  GRANDE:	Well, I do some, not too much.
S315  I suppose I was too excited about getting to my dad's place.
S316  I know there was quite a few that had eye disease and they had them there for a few days, and then a lot of them were sent back from where they were coming from, either Italy, Germany or Yugoslavia.
S317  And then uh, well, we were there, and they vaccinated us again and checked us through and all, and finally we got to go and I think we changed trains in Chicago, from New York to Chicago, and then changed trains.
S318  And there were some people that went here to Denver that were from more or less the same area as we were.
S319  But, uh, we got on a different train in Chicago.
S320  The train they got was different than the one we had.
S321  And that's the first time I got to see bananas, on the train.
S322  And, of course, there was a fellow that, he went over there to get his two children, and he didn't buy them very much.
S323  Whatever, the rest of them, like my mother and this other lady bought, we shared with his kids.
S324  They didn't like it very much, but what can you do.
S325  So we all went, there was a lady with her two daughters, and this man with his two children, and my mother and me, we all went to the same town in Utah.
S326  We got off in Price, and we, of course, that's where my dad met us, and then we had to take the bus twenty-eight miles to Sunnyside.

S327  PHILLIPS:	Why was it that you decided to move up to, you were on 		your way to Denver, I take it?

S328  GRANDE:	No, no.
S329  We were on the way to Utah to begin with.
S330  That's where my dad lived.

S331  PHILLIPS:	Why had he chosen to live in Utah?

S332  GRANDE:	Well, he was working in coal mines.
S333  He worked in different mines in Utah, around.
S334  He worked part-time years before that in  Aspen, Colorado, but he went back to Utah around Tooele.
S335  And at that time he was in Sunnyside, and so we lived there about six and a half years, and then his health went bad, and so we came to Colorado.

S336  PHILLIPS:	I see.
S337  Can you tell me how you felt when you arrived in 		the United States and how eventually you must have started school, what was that like for you?

S338  GRANDE:	Well, we lived, my dad rented a company four room house that was a double, and the other family was similar in nationality as we were.
S339  And so, uh, the kids could talk broken Slovanian, so we kind of got started getting along, and I'd pick up words from them little by little.
S340  And we came on a Thursday, and the following Monday I went to school.
S341  And being that these were going to the same grades, so they put me in the fourth grade instead of the first.
S342  And I struggle along pretty good because as far as figures you didn't have to talk.
S343  You could just write, and it was good.
S344  And, uh, so I was in a county contest the first and second year for arithmetic to where we went from Sunnyside to Price, we stayed overnight.
S345  And it was good.
S346  And then I skipped the sixth grade and in seventh grade I was in a running contest.
S347  I wouldn't go now, but I did go then.

S348  PHILLIPS:	Okay.
S349  Let me just turn my tape over.
S350  END OF SIDE ONE
S351  BEGINNING OF SIDE TWO

S352  PHILLIPS:	This is side two, Interview Number 414 [DP-40], with Mary Grande.
S353  Um, so, uh, you did fairly well at school?

S354  GRANDE:	Yeah, I done, I'd say I wasn't the best, but I was with 		the top ones.

S355  PHILLIPS:	Now, tell me what life was like now for your mother.
S356  She no longer had all of those animals to look after.
S357  It must have been very different.
S358  What did she do?

S359  GRANDE:	All we could do was housework and laundry, cleaning and cooking, and that.
S360  So she got adjusted pretty well.
S361  She always hoped to go back, but she never did because they started talking about the war and she didn't want to be in another war over there, which they had it worse right in our area in the second one than they did in the first.
S362  And my brother, half-brother, of course, he lived there until the '70s when he died.
S363  She gave the property over to him.
S364  And they had pretty rough deals there during the second war.
S365  In fact, one of his daughters got deaf and dumb on account of the noise of the cannons that they were shooting on their farm.
S366  We were right close to where they had the battles and everything, my brother was, so.
S367  But, uh, I got pretty well with the kids in school.
S368  Of course, I couldn't speak, but I started learning very fast the best way I could and I enjoyed the school.

S369  PHILLIPS:	And where were you living at this point?

S370  GRANDE:	In Sunnyside, Utah.

S371  PHILLIPS:	When did you, well, before I ask you that question, uh, can you tell me a little bit about the Depression years for your family.
S372  What was that like?

S373  GRANDE:	Well, the Depression really hit us after I came here to Colorado.
S374  Right after I got married, that's when we had the worst Depression.
S375  But, uh, dad was kind of, his health was going down great, so he couldn't, uh, work and he figured, well, between my mother and him, they figured maybe he could do some outside work over here, and we had, my mother's sister lived up on northeast of Greeley on what they call the dry land, so we were there for a week, and then we came to Denver.
S376  So he got a job finally over at the smelter, and he worked there for a while, but couldn't work too long.
S377  And then little by little he tried to work, he went finally back into the mine, and he couldn't work too long there.
S378  Finally the doctor said he couldn't work no more.

S379  PHILLIPS:	What was, uh, how did you feel, at this point, or how did your family feel about being so far away from home?
S380  Did they miss--

S381  GRANDE:	My mother missed it a lot.
S382  But, uh, I'm sorry to say, I 		didn't		.

S383  PHILLIPS:	So you got married.
S384  When did you get married?

S385  GRANDE:	In 1927, here in Denver.
S386  And I've been here ever since.

S387  PHILLIPS:	And, uh, you moved to Denver when, from Sunnyside?
S388  GRANDE;	In 1926, in October.
S389  We drove a Model T.
S390  In fact, I drove it most of the way, and we stopped in Aspen.
S391  I had an uncle, my mother's brother, there.
S392  We stopped there for a month, and then we came on to Colorado.
S393  And, uh, after a while we both got jobs, and it worked out.
S394  And I met my husband on New Year's and married him in May.
S395  He was from the same area as I was, and years later we went back there.
S396  He liked the area where I was raised much better than where he was because it was close to the city.
S397  And him and I went back there three times, one by car and twice with the plane.
S398  And, of course, I've been there since a few times.

S399  PHILLIPS:	Why was it that there were so many people from your, 		from that area that you came from in Europe, living in this area around Denver?
S400  Do you know?

S401  GRANDE:	Well, it's a settlement.
S402  When a group gets settled and then somebody else tries to come in, and they just like to integrate together.

S403  PHILLIPS:	Okay.
S404  Is there anything else that you'd like to, think 		we might be interested to hear about?

S405  GRANDE:	Well, I worked later on.
S406  During the Depression it was kind of rough.
S407  My husband wasn't making much.
S408  Worked every other week and the girls were getting to the point, being in school, we sent them to parochial school.
S409  And naturally we had to pay.
S410  It wasn't like now that somebody else pays for them a lot.
S411  And then, uh, U finally got a job in a packing house, which I worked close to thirty years in it.
S412  And in between every so often I had to have different surgeries and I'd be home.

S413  PHILLIPS:	What kind of work, excuse me, what kind of work 		particularly were you doing?

S414  GRANDE:	Cutting up meat, pork and beef.
S415  Cut it for scraps for 		sausage and stuff.
S416  And then later on she came into the packing house and she worked with me for a while, and then she went down in the smokehouse where they have to smoke bacon and ham, and she worked there until she had to give up medically on account of it.

S417  PHILLIPS:	Let me explain for identification who she is.

S418  GRANDE:	My daughter, Mitzi.

S419  PHILLIPS:	M-I-T-Z-I.
S420  Mitzi Stackhouse.

S421  GRANDE:	Yeah.
S422  I have another daughter, Jenny Musk.
S423  She's a 		nurse.
S424  She lives way up in Northglen.

S425  PHILLIPS:	Okay.
S426  Unless there's something else you think you'd 		like to us all.

S427  GRANDE:	Well, we became, my husband and I became American citizens in 1932 and we tried to vote every time ever since.
S428  Maybe not right, but we try our best.
S429  And every time I go back to Europe I'm happy to come back.
S430  This is my country.

S431  PHILLIPS:	Okay.
S432  That finishes Interview Number 414 [DP-40] with 		Mary Grande,  It's five after one.
```
