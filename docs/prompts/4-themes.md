# THEMES — as sent to the model

_6670 words_

## SYSTEM

```
You are grouping a researcher's codes into themes across a whole project.

Every rule below carries the same weight. Follow all of them on every theme you return.


A gist DEFINES a theme: what belongs to it and what would count as an instance, in words that
would still be true if fifty more materials arrived tomorrow. A gist never states what was
found, never compares materials, never says where the theme is present or absent. Those are
conclusions, and conclusions are written elsewhere, later, over the evidence. A gist that could
only have been written about the materials in front of you is a finding in the wrong slot.

1. Return one JSON object and nothing else, shaped exactly like the example at the end of this message.
2. Return the whole theme set, not only what changed: every theme that should be live afterwards appears in your answer, keeping its `id` when it already has one and carrying `"new": true` instead when it does not.
3. Gather codes by name: `code_names` holds names copied exactly from the codebook below, and a name that is not in that codebook is ignored.
4. Keep at most 12 themes live. Fewer, well-populated themes beat many thin ones.
5. Give every theme a gist of one sentence DEFINING it: what belongs to this theme and what would count as an instance. Not what its codes are called, and not what was found — a definition, so that a stranger could sort a new passage into it or out of it.
6. Fold a theme into another by giving it `"merge_into": "<the id it becomes part of>"` — never by leaving it out of your answer. A theme that is dropped silently strands everything already written under it.
7. Group codes by what they mean, not by where they were found. You are told nothing about which materials a code appears in or how often, and the gist says nothing about it either — where a theme reaches is worked out later, over the evidence.
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
THE MATERIAL JUST READ, with the codes marked in it. Revise the themes with this text in front
of you; a theme is a pattern in what people said, not a grouping of labels.

## Minnie Rodwin oral history interview (interview)

CODES MARKED IN THIS MATERIAL, by passage:
- Absent parent's letters and tickets as migration mechanism: S256, S281
- Birth name superseded by everyday name: S021, S022, S025
- Children left behind with grandparent due to care concerns: S181, S183, S185
- Children's unpaid labor in family enterprise: S482, S484, S486
- Conscription recall as emigration trigger: S238, S254, S271
- Dual birth date as official versus lived identity: S037, S038, S053
- Early school start abroad as pre-migration education: S457, S459, S463
- Family business as weekly relative gathering point: S546, S547
- Family business re-established at each migration stop: S158, S265, S514
- Family business relocation driving residential move: S511, S514, S539
- Horse-drawn delivery as business transport: S387, S389
- Icebox as marker of relative household comfort: S070, S072, S075, S076
- Jewish section on ship as ordinary travel arrangement: S285, S290
- Kosher food sent by acquaintance during transit: S288, S326
- Living above or adjacent to family business: S086, S435
- Marriage through shared trade workplace: S490, S491, S495, S497
- Mother as bakery skill source across borders: S397, S403, S406, S408
- Mother-in-law conflict as migration cause: S147, S154, S155, S158
- Nationality shifting under one's birthplace: S248, S251
- Parent refusing children's earned money in transit: S308, S313, S315
- Prior emigration of parent as precondition for family relocation: S261, S280, S281
- School releasing children for family business labor: S446, S447
- Spouse's presence as condition for migration willingness: S556
- Spouse's trade skill converting partner's occupation: S393, S395, S401, S403
- Tenement hall bathrooms and coin-fed gas meters: S422, S425, S428, S431

THE MATERIAL:
S000  EI-845RODWIN
S001  MINNIE RODWIN
S002  BIRTHDATE:  FEBRUARY 9, 1907
S003  INTERVIEW DATE: FEBRUARY 12, 1997
S004  AGE AT TIME OF INTERVIEW:  90
S005  RUNNING TIME:  27:12
S006  INTERVIEWER:  JANET LEVINE, PH.D.
S007  RECORDING ENGINEER:  JANET LEVINE, PH.D.
S008  INTERVIEW LOCATION:  SUNRISE, FLORIDA
S009  TRANSCRIPT PREPARED BY: TAPESCRIBE
S010  TRANSCRIPT REVIEWED BY: HELEN HENWOOD
S011  ENGLAND, 1910
S012  AGE:  3
S013  SHIP:  PHILADELPHIA
S014  PORT:
S015  RESIDENCES:
S016  ●  ENGLAND, LONDON, COMMERCIAL ROAD
S017  ●  U.S, NEW YORK, LOWER EAST SIDE, 141 ESSEX STREET,
S018  ROCKAWAY BEACH, SUNRISE FLORIDA.

S019  LEVINE:	Today—today is February the—the 12th and I’m here in Sunrise, Florida at the home of Minnie Rodwin.
S020  Minnie came from England in 1910 when she was three and a half years of age.

S021  RODWIN:	I—at that time I was Mary.

S022  LEVINE:	You were Mary Floun .
S023  Mary Floun, her—that was her maiden name.

S024  RODWIN:	Yeah.

S025  LEVINE:	And that was her name when she came to this country.

S026  RODWIN:	Right.

S027  LEVINE:	Okay.
S028  And let’s see.
S029  At the time of this—of this interview you’re 90 years of age.
S030  You just had a birthday.

S031  RODWIN:	Right.

S032  LEVINE:	(chuckles)  Okay, so you’re 90 years old.
S033  And this is Janet Levine for the National Park Service.
S034  If you would state for the tape again your birth date and where you were born.

S035  RODWIN:	My—the regular [unclear]?

S036  LEVINE:	What you—whatever birth date.
S037  You—you have two, right?
S038  When you were born and when you were registered.

S039  RODWIN:	December—December 25th.

S040  LEVINE:	Was that when you were actually born?

S041  RODWIN:	Yeah, six o’clock in the morning.
S042  My—my—my—my mother used to say the—the times [unclear].

S043  LEVINE:	Really?
S044  And what else did your mother tell you about when you were born?

S045  RODWIN:	Well, my mother was—business.
S046  She’s—bakery business.

S047  LEVINE:	In London?

S048  RODWIN:	Yeah.

S049  LEVINE:	Uh-huh, uh-huh.
S050  So you were really born on Christmas—

S051  RODWIN:	Morning.

S052  LEVINE:	—morning.
S053  And—but you were registered and so your official birth date is February 9th, 1907.

S054  RODWIN:	That’s right.

S055  LEVINE:	Okay.
S056  Now, you were only three and a half when you came to this country.
S057  But what recollections do you have of England?

S058  RODWIN:	Well, first of all, we—we—we—we—we had—they were building—the building they had built—and they were building houses.
S059  So there was a lady right—right—right opposite us.
S060  She was Irish.
S061  And she used to call me “Mary, Mary.”  So I said, “What do you want?”  “I just want to tell you not to make so—so—noise.”  I [unclear] I was quiet.

S062  LEVINE:	Yeah, uh-huh.

S063  RODWIN:	But—

S064  LEVINE:	Do you remember the house you lived in in London?

S065  RODWIN:	I have the birth—birth certif—

S066  LEVINE:	Certificate.
S067  Uh-huh, uh-huh.
S068  But do you remember the house?
S069  Do you remember anything in particular that you could describe?

S070  RODWIN:	Well, I know we had—we had a—oh, what do you call it?
S071  Where none—lo—lot of people didn’t have.
S072  We had—outside, we had a—an icebox with ice.
S073  And we used to keep our cold things in there.

S074  LEVINE:	Uh-huh, uh-huh.
S075  And a lot of people didn’t have an icebox at that time.

S076  RODWIN:	No.

S077  LEVINE:	Uh-huh, uh-huh.
S078  And is there anything else you can think of that you recall?
S079  Do you recall your mo—where your mother had the bakery?

S080  RODWIN:	Yeah, in Commercial Road.

S081  LEVINE:	Wow!
S082  Uh-huh.
S083  Did you go to the bakery?
S084  Could you say anything about—

S085  RODWIN:	Yeah.
S086  We lived—we lived up where—where the bakery was.

S087  LEVINE:	I see.
S088  And what was your mother’s name?

S089  RODWIN:	Sophie.

S090  LEVINE:	Sophie.
S091  And her maiden name, do you know that?

S092  RODWIN:	It’s a funny name.
S093  Vivyeika.
S094  That means, oh, a squirrel.

S095  LEVINE:	Oh.  (chuckles)  Uh-huh.
S096  And could you spell it?

S097  RODWIN:	Vivyeika—V-I-V-Y-E-I-K-A.

S098  LEVINE:	Was your mother born in England?

S099  RODWIN:	No.

S100  LEVINE:	Where was she born?

S101  RODWIN:	[unclear], Warsaw.

S102  LEVINE:	Oh, Warsaw.
S103  Uh-huh.
S104  So do you know when she came to England?
S105  Do you know—had she been—

S106  RODWIN:	When we—when we were born.

S107  LEVINE:	Well, I mean, had she been living—she had a bakery there so she must have been there for a while before you were born.

S108  RODWIN:	No.

S109  LEVINE:	No?

S110  RODWIN:	When—er--my father was married and he was in—what do you call it’s—

S111  LEVINE:	The military?

S112  RODWIN:	No—yeah.

S113  LEVINE:	In the—in the army.

S114  RODWIN:	Yeah.

S115  LEVINE:	Uh-huh.

S116  RODWIN:	But he wasn’t [unclear].
S117  He was in—see, I forget all this.

S118  LEVINE:	That’s okay.
S119  Whatever you remember you can say.

S120  RODWIN:	Ah—

S121  LEVINE:	Was—was he in Warsaw?

S122  RODWIN:	No.

S123  LEVINE:	No.

S124  RODWIN:	In—I forget.
S125  I—I knew all these things but the—

S126  LEVINE:	Yeah.
S127  Well, in other words, when he was in the army is when he met your mother.

S128  RODWIN:	No.

S129  LEVINE:	No.

S130  RODWIN:	They lived togeth—they lived in the same town.

S131  LEVINE:	Oh, so he also came from Poland?

S132  RODWIN:	Yeah.

S133  LEVINE:	Your father?

S134  RODWIN:	Yeah.

S135  LEVINE:	Now, his last name was Floun?

S136  RODWIN:	Right.

S137  LEVINE:	Uh-huh.
S138  So—so they had met in Poland.

S139  RODWIN:	Right.

S140  LEVINE:	And they married and came to England?

S141  RODWIN:	Well, he went to—they sent him some—I forget the name.
S142  Anyway, he was there sometime.
S143  My mother was married and her husband died.

S144  LEVINE:	Oh.

S145  RODWIN:	So when he come back he married my mother.

S146  LEVINE:	I see.

S147  RODWIN:	And he had a mother-in-law that was very—she wasn’t very nice.
S148  So she—

S149  LEVINE:	This is your mother’s mother?

S150  RODWIN:	My mother’s mother—m—m—m—m—my mother’s mother-in-law.

S151  LEVINE:	Oh, okay.

S152  RODWIN:	So she—she—she always used to talk about—she said that’s why her son died, because my mother was waiting for a—him to come back.

S153  LEVINE:	Oh.

S154  RODWIN:	Anyway, they got married but she was always after her.
S155  So she—she got a [unclear] so crazy that she went to L—London.

S156  LEVINE:	Oh, uh-huh.
S157  I see.

S158  RODWIN:	She went to London and then they opened up another bakery.

S159  LEVINE:	Uh-huh.

S160  RODWIN:	That’s all.

S161  LEVINE:	Uh-huh.
S162  Now, did you have brothers and sisters?

S163  RODWIN:	Yeah, we were nine.

S164  LEVINE:	In England?

S165  RODWIN:	No—yeah.
S166  We had two sisters in Poland—

S167  LEVINE:	Oh, that were born in Poland.

S168  RODWIN:	—[unclear]—were born there.
S169  My grandmother—that’s [unclear].

S170  LEVINE:	Wow.

S171  RODWIN:	My [unclear] grandmother.
S172  She—she—she—no, no.
S173  She was very good.

S174  LEVINE:	You remember her?

S175  RODWIN:	No, just from—

S176  LEVINE:	No.

S177  RODWIN:	Just from pictures.

S178  LEVINE:	Right, uh-huh.
S179  Uh-huh.

S180  RODWIN:	She was in London but I was too—I wasn’t even born.
S181  So—er--anyway, we had two sisters in Poland we left there—

S182  LEVINE:	Oh.

S183  RODWIN:	—because my mother was afraid she wouldn’t be—be able to take care of them.

S184  LEVINE:	So the two sisters were left with your grandmother?

S185  RODWIN:	Yeah, just till one was seven years old.

S186  LEVINE:	So then who went to London?
S187  Your mother—

S188  RODWIN:	My father.

S189  LEVINE:	—and your father.
S190  Just the two of them?

S191  RODWIN:	Yeah.

S192  LEVINE:	And then you were born in London.
S193  And were other children born in London too?

S194  RODWIN:	Yeah, all—all the rest of them.

S195  LEVINE:	I see.
S196  So you must have been among the youngest.

S197  RODWIN:	Yeah, next to the youngest.

S198  LEVINE:	Do you have any idea of when your mother came to London?
S199  When she left Poland and went to London?

S200  RODWIN:	When my—my—I have two brothers that were twins.
S201  And—er--wh—she was pregnant with them when she went to London.

S202  LEVINE:	I see.
S203  And then after the two twins—the two twin brothers, who comes next in the—in the line of children?

S204  RODWIN:	It’s a—a—a—a daughter.

S205  LEVINE:	Okay.

S206  RODWIN:	Esther.

S207  LEVINE:	Esther.
S208  And then who?

S209  RODWIN:	Esther—Jackie.

S210  LEVINE:	Jackie’s a girl or boy?

S211  RODWIN:	No, boy.

S212  LEVINE:	A boy, uh-huh.
S213  Jackie, and then?

S214  RODWIN:	Annie.

S215  LEVINE:	Annie.

S216  RODWIN:	Me.

S217  LEVINE:	Okay, Mary.

S218  RODWIN:	And then kid sister, Yettie.

S219  LEVINE:	Yettie.

S220  RODWIN:	She died.

S221  LEVINE:	Uh-hmm.

S222  RODWIN:	She was two years younger than me.
S223  That’s all.

S224  LEVINE:	So was Yettie born—Yettie was born in London and Yettie came to the United States—

S225  RODWIN:	With us.

S226  LEVINE:	With you.
S227  Uh-huh, okay.
S228  So what—let’s see.
S229  What was your father’s first name?

S230  RODWIN:	Morris.

S231  LEVINE:	Morris, okay.
S232  And so your mother had the bakery business.
S233  And did your fath—was your father part of that bakery business in London?

S234  RODWIN:	Oh, he was—yeah.

S235  LEVINE:	That was his business, uh-huh.
S236  I see.
S237  Did—did anybody ever tell you why your mother and father decided to come to the United States?

S238  RODWIN:	Well, my father was called in—into—back to the army when the boys were just—just thirteen, the twins.

S239  LEVINE:	The Polish Army?

S240  RODWIN:	No—yeah.
S241  No.

S242  LEVINE:	In England?
S243  In—in—

S244  RODWIN:	It wasn’t England.
S245  It was—I forget the name of it.

S246  LEVINE:	Maybe it was the Russian Army.

S247  RODWIN:	Yeah.

S248  LEVINE:	Because those borders changed a lot.

S249  RODWIN:	Yeah.

S250  LEVINE:	Uh-huh, uh-huh.

S251  RODWIN:	This is the Russian Army.
S252  It was underground.
S253  I don’t know what the—and anyway, that’s where—

S254  LEVINE:	He was called back into the army.
S255  And so, instead, the family moved to the United States.

S256  RODWIN:	So my father got tickets, went to the United States.
S257  He had some rel—relatives in the—in New--New York.

S258  LEVINE:	So he went first.

S259  RODWIN:	Yeah.

S260  LEVINE:	And then—

S261  RODWIN:	The year before.

S262  LEVINE:	The year before.
S263  And what did he do when he got to the United States for work?
S264  Do you know?

S265  RODWIN:	He opened up a bakery.

S266  LEVINE:	A bakery.
S267  I see. (telephone rings)

S268  RODWIN:	All right.
S269  I get it.

S270  LEVINE:	Okay, we’ll just turn this off.  [tape off/on]  Resume here after a telephone call from Minnie’s daughter.
S271  Okay, why don’t we say—so the reason was to avoid going back in the army.
S272  That was the reason that your father left first.

S273  RODWIN:	That’s right.

S274  LEVINE:	And he opened a bakery in New York?
S275  Was it in New York?

S276  RODWIN:	Downtown.

S277  LEVINE:	Downtown in Manhattan?

S278  RODWIN:	Yeah.

S279  LEVINE:	Uh-hmm.
S280  And then in a year or so he sent for the children.

S281  RODWIN:	He had the tickets, yeah.

S282  LEVINE:	He—okay.
S283  And when you left, you left with your mother and all of your brothers and sisters.
S284  Do you remember anything about the journey?

S285  RODWIN:	We—we had—we were in—in—in—in a Jewish—

S286  LEVINE:	Section of London?
S287  Uh-huh.

S288  RODWIN:	And the—er--the—er-- chef knew us from London.

S289  LEVINE:	Oh.
S290  You were in the Jewish section on the ship?

S291  RODWIN:	On the ship, yeah.

S292  LEVINE:	Wow, I never h—have heard that before.

S293  RODWIN:	Yeah.
S294  So they had, um--like, you know—

S295  LEVINE:	Bunk beds?

S296  RODWIN:	Bunk beds.
S297  And I was on the top [unclear].
S298  Anyway, I—I wanted to go to the bathroom so I just went in—I went into the—into the water.
S299  And th—the—the lady took me—took me and took—took all my things off.
S300  And she changed me.
S301  And then she gave me something and put me back [unclear].

S302  LEVINE:	Now, were you in steerage?
S303  Were you in the bottom of the ship with a lot of people all around?

S304  RODWIN:	Oh, we were in the bottom.
S305  And we used to dance and—

S306  LEVINE:	Used to dance?

S307  RODWIN:	Oh, yes.
S308  We used to dance and sing and they used to throw money down.

S309  LEVINE:	Really?

S310  RODWIN:	But we couldn’t put—we couldn’t put—put—put it up.
S311  My mother wouldn’t let—let us.

S312  LEVINE:	Oh.
S313  You mean—you mean your sisters and brothers—you would dance and sing and people would throw money, but your mother wouldn’t let you take it.
S314  Uh-huh.

S315  RODWIN:	No.

S316  LEVINE:	And this was in steerage—

S317  RODWIN:	Yeah.

S318  LEVINE:	—that you did that.
S319  Uh-huh.

S320  RODWIN:	Yeah.

S321  LEVINE:	And you said that the name of the ship—

S322  RODWIN:	The Philadelphia.

S323  LEVINE:	The Philadelphia.
S324  And do you remember anything else about the voyage?

S325  RODWIN:	They were very nice.
S326  This--er--this chef used to send us up all kind of kosher things we could eat, like pickle herring or the—the—the—the things that we—we could eat.

S327  LEVINE:	Well, now, did the chef send these things—did you go up to a dining area where there were tables?
S328  Do you remember that?

S329  RODWIN:	I can’t remember.

S330  LEVINE:	Uh-huh.
S331  But anyway, your mother kept a kosher house?
S332  So on the ship—

S333  RODWIN:	Oh, yeah.
S334  Still—

S335  LEVINE:	You still do, uh-huh.

S336  RODWIN:	It’s still ko—kosher.

S337  LEVINE:	Do you remember when the ship came into the New York harbor?

S338  RODWIN:	September.

S339  LEVINE:	Do you remember, maybe, seeing the Statue of Liberty?

S340  RODWIN:	Oh, yes.
S341  We all ran to see the Statue of Liberty.

S342  LEVINE:	Of course, you probably didn’t know what it was—

S343  RODWIN:	Yeah.

S344  LEVINE:	—because you were so young.
S345  And how about—do you remember your father meeting the family?

S346  RODWIN:	The other father?

S347  LEVINE:	Your father.
S348  Do you remember when you got to America?

S349  RODWIN:	Oh, we had lots of—lots of rel—la—

S350  LEVINE:	Relatives.

S351  RODWIN:	Relatives.

S352  LEVINE:	Uh-huh.
S353  And—and where were your relatives?
S354  Were they all in New York?

S355  RODWIN:	One was on Forty second Street.
S356  One was in the Bronx.
S357  They were all over.

S358  LEVINE:	Now, were these brothers and sisters of your mother and father, these relatives?

S359  RODWIN:	Yeah.

S360  LEVINE:	Uh-huh.
S361  So do you remember seeing your father?
S362  Because you probably didn’t even remember him.

S363  RODWIN:	Oh, I did.

S364  LEVINE:	Oh, you did remember him?
S365  Uh-huh.

S366  RODWIN:	Daddy [unclear].
S367  At that time, they used to call your father Papa.
S368  We called him Daddy because in London it was Daddy.
S369  So that’s—that’s all.

S370  LEVINE:	Uh-hmm.
S371  Do you remember where the family went when they left—when they got off the boat?

S372  RODWIN:	We went to the Lower East Side.

S373  LEVINE:	Uh-huh.
S374  And before that, do you remember Ellis Island at all?

S375  RODWIN:	No.

S376  LEVINE:	Okay.
S377  And [unclear]—

S378  RODWIN:	All—all the people.

S379  LEVINE:	Uh-hmm.
S380  And the Lower East Side.
S381  Do you remember any impressions you have from what—you know, when you were there for the first time?

S382  RODWIN:	We—we had horses—horses used to ride around.
S383  We had [unclear].

S384  LEVINE:	Like a horse and wagon, you mean?

S385  RODWIN:	Yeah.

S386  LEVINE:	Uh-huh.

S387  RODWIN:	We had the—couple wagons because we had to del—deliver.

S388  LEVINE:	You had to deliver the bakery goods.

S389  RODWIN:	Yeah.

S390  LEVINE:	Uh-huh.
S391  Now, it tur—it’s—your father must have been a baker.
S392  Was he a baker in Poland?

S393  RODWIN:	My father was not—my father was not a baker.

S394  LEVINE:	Oh.

S395  RODWIN:	He was a—a—a tailor.

S396  LEVINE:	Oh, your father was a tailor?

S397  RODWIN:	My mother was the b—the baker.

S398  LEVINE:	Okay.

S399  RODWIN:	Through my mother, they—they became—yeah, my father became a what do you call it?

S400  LEVINE:	A tailor?

S401  RODWIN:	No, a baker.

S402  LEVINE:	Oh, he became a baker from your mother?

S403  RODWIN:	Yeah.

S404  LEVINE:	I see.
S405  Now, had your mother been a baker in Poland before she ever got to—

S406  RODWIN:	Yeah.

S407  LEVINE:	—London?

S408  RODWIN:	Yeah.

S409  LEVINE:	So they opened a bakery in the Lower East Side?
S410  Uh-huh.
S411  And do you remember where you lived in the Lower East Side?

S412  RODWIN:	We lived—141 Essex Street.

S413  LEVINE:	Oh, uh-huh.
S414  You remember the building?

S415  RODWIN:	It’s a four—four-story—

S416  LEVINE:	A walkup.

S417  RODWIN:	—walkup.

S418  LEVINE:	Like a tenement?

S419  RODWIN:	Yeah.

S420  LEVINE:	Uh-huh.
S421  Did you have a—a bathroom inside?

S422  RODWIN:	Three—three—three—

S423  LEVINE:	Between apartments?

S424  RODWIN:	Yeah.

S425  LEVINE:	They were in the hall.

S426  RODWIN:	Yeah.

S427  LEVINE:	Uh-huh, yeah.
S428  And how about—do—did you have the gas meters in the apartment—

S429  RODWIN:	Yeah.

S430  LEVINE:	—that you had to put a quarter in?

S431  RODWIN:	Yeah.

S432  LEVINE:	Uh-huh.
S433  Do you remember anything else about that place?
S434  Essex Street, where you lived?

S435  RODWIN:	Well, the bakery was across the street.
S436  We could—we could—we—we [unclear] bakery there.

S437  LEVINE:	Uh-hmm.

S438  RODWIN:	We had a nice time.

S439  LEVINE:	Hmm.
S440  And so some of your—some of your brothers and sisters must have started school then right away?

S441  RODWIN:	Yeah—no.
S442  My brothers were fourteen years old.

S443  LEVINE:	Oh, so they didn’t go back to—they didn’t go to school?

S444  RODWIN:	They went—they—yeah.

S445  LEVINE:	Oh, they did?

S446  RODWIN:	They went but the—they didn’t take them because we had—my mother came with all her kids.
S447  And they says, “Let them stay home and help you.”

S448  LEVINE:	Oh, okay.
S449  So none of you had to go to school then?

S450  RODWIN:	Oh, we all went.

S451  LEVINE:	Oh, you all went.
S452  Do you remember starting school?

S453  RODWIN:	Yeah, I started in the [unclear].

S454  LEVINE:	Uh-hmm.
S455  And was—how was school for you?

S456  RODWIN:	All right.
S457  I was [unclear]—of course, in—in London, they—they started you at school at three—three o’clock—three—

S458  LEVINE:	Three years old?

S459  RODWIN:	Three years old.

S460  LEVINE:	Uh-huh.
S461  I see.
S462  So you had already been to school.

S463  RODWIN:	Yeah.

S464  LEVINE:	I see.
S465  Uh-huh.
S466  So you knew a lot of things—

S467  RODWIN:	Yeah.

S468  LEVINE:	—before you started.

S469  RODWIN:	Yeah.

S470  LEVINE:	I see, uh-huh.
S471  Okay.
S472  Can you—can you talk a little bit about the Lower East Side in those days?

S473  RODWIN:	Well—

S474  LEVINE:	What it was like?

S475  RODWIN:	I have to eat.

S476  LEVINE:	Oh, you have to eat?  (chuckles) Okay.
S477  Okay.
S478  Let me just ask you a few last questions.
S479  Okay?
S480  What did you do then?
S481  Did you do some kind of work in your life or did you—

S482  RODWIN:	I helped my mother—

S483  LEVINE:	Uh-huh.

S484  RODWIN:	—my father in the bakery.

S485  LEVINE:	In the bakery  I see.

S486  RODWIN:	Came to holidays, we used to you put almonds and cherries on the macaroons.
S487  Yeah, we—we helped out.

S488  LEVINE:	Uh-huh.
S489  And then how did you meet your husband?

S490  RODWIN:	He was a—he used to drive a—a—a—a what do you call it?
S491  He worked in a bakery too.
S492  He drove a—a—a—you know, it’s hard for me to—

S493  LEVINE:	Uh-hmm.
S494  Was it a delivery—

S495  RODWIN:	Yeah.

S496  LEVINE:	—truck?

S497  RODWIN:	Yeah.

S498  LEVINE:	Uh-huh.
S499  So then how many children did you have?

S500  RODWIN:	Me?

S501  LEVINE:	Yeah.

S502  RODWIN:	I had six.

S503  LEVINE:	You had six children and your—and what was your husband’s name?

S504  RODWIN:	Mom—Mor—Jack.

S505  LEVINE:	Jack, uh-huh.
S506  And when you look back on it now, how you and your brothers and sisters and mother and father came and settled in the Lower East Side and everything, do you think that made a big difference in your life, the kind of person you were and—

S507  RODWIN:	Well, we were al—we were always together.
S508  Always together.
S509  So, you know, it—it was a nice—

S510  LEVINE:	Did you stay in the Lower East Side or did the family move on to someplace else?

S511  RODWIN:	We moved to—oh, we—we were in Rockaway Beach.

S512  LEVINE:	Oh, uh-huh.
S513  And did you have a bakery there too?

S514  RODWIN:	Yeah, we had—we had a bakery there.

S515  LEVINE:	Wow.
S516  You don’t, by any chance, remember the name of the bakery that you had in the Lower—

S517  RODWIN:	Floun’s.
S518  Oh, Floun’s.

S519  LEVINE:	—Lower East Side.

S520  RODWIN:	Floun’s.

S521  LEVINE:	So that—that was your maiden name.
S522  Floun’s Bakery—

S523  RODWIN:	Yeah.

S524  LEVINE:	—it was called.
S525  And the bakery was also on Essex Street?

S526  RODWIN:	Yeah.

S527  LEVINE:	Across the street from where you lived?
S528  Uh-huh.
S529  Do you remember the years, roughly, that—that—that you had the bakery there?

S530  RODWIN:	Well, I must have been about four or five.

S531  LEVINE:	So, say, 1911?

S532  RODWIN:	Yeah.

S533  LEVINE:	And did you keep it for many years or—

S534  RODWIN:	No, not many years.

S535  LEVINE:	Uh-huh.

S536  RODWIN:	Oh, we were—we were on the East Side about fifteen years.

S537  LEVINE:	Fifteen?
S538  Oh, uh-huh.

S539  RODWIN:	Then we moved to Rockaway Beach.

S540  LEVINE:	Rockaway Beach, uh-huh.
S541  Uh-huh.

S542  RODWIN:	Well, that’s—

S543  LEVINE:	Okay, is there anything else you can think of that you might want to add about coming to this country or what it’s meant to you to be in this country or anything?

S544  RODWIN:	It was nice.
S545  Relatives were very nice.
S546  Oh, they used to come [unclear]—Friday, they’d come to my—my father’s bakery.
S547  And they’d—they’d take—they would have the [unclear] they were going to take.
S548  They were all right.

S549  LEVINE:	Uh-huh.
S550  So—so did you have get-togethers then with your relatives—

S551  RODWIN:	Yeah.

S552  LEVINE:	—once you got to this country?

S553  RODWIN:	Oh, they were al—always my house.

S554  LEVINE:	Uh-huh.
S555  How did your mother feel about coming to this country?

S556  RODWIN:	She didn’t mind as long—as long as my father went, she wanted to come too.

S557  LEVINE:	She wanted to be with him, uh-huh.
S558  And was he happy in this country, your fath—

S559  RODWIN:	Oh, yes.

S560  LEVINE:	Uh-huh.
S561  Okay.
S562  And then did you visit Ellis Island?

S563  RODWIN:	I think I was there when I—

S564  LEVINE:	Uh-huh.

S565  RODWIN:	Can’t remember.

S566  LEVINE:	Okay.
S567  And how are things for you now?
S568  Now that you’re ninety years old and you’re—

S569  RODWIN:	It’s all right.

S570  LEVINE:	Okay?
S571  Uh-huh.
S572  I see you have a daughter nearby.

S573  RODWIN:	Oh, I have—oh, my—I have a daughter near L.A. and a daughter in Atlanta.
S574  I have grandchildren.
S575  Here, I’ll show you.

S576  LEVINE:	Okay.
S577  Well, let me turn this off first.
S578  I want to thank you.
S579  I’m going to take your microphone off.
S580  I’ve been speaking with Minnie Rodman, who came from England in 1910 when she was three and a half years old.

S581  RODWIN:	Yeah, September.

S582  LEVINE:	And the family had originally come from the Poland, Russian border—

S583  RODWIN:	Yeah.

S584  LEVINE:	—and settled in the Lower East Side.
S585  And this is Janet Levine for the National Park Service signing off.
S586  [END OF INTERVIEW]

THE THEMES THAT ARE LIVE NOW

- id t27e6355e83 · "Belonging, identity, and return" — Identity and belonging are negotiated through name changes, discrepancies between official records and lived experience, the shifting political identity of one's birthplace, and civic acts that establish membership in a receiving country.
  gathers: Birth name superseded by everyday name, Dual birth date as official versus lived identity, Generational contrast in homeland attachment, Nationality shifting under one's birthplace, Naturalisation as civic belonging, Return visits confirming belonging in receiving country
- id t830ae2ac7b · "Family chain migration" — Family relocation is set in motion by an earlier migrant who establishes a foothold and then sends tickets, letters, or earnings to enable the rest of the household to follow.
  gathers: Absent parent's letters and tickets as migration mechanism, Prior emigration of parent as precondition for family relocation, Regional chain migration settlement, Relative as intermediary stop in migration route
- id t637dd9f8cb · "Family enterprise as portable livelihood" — A trade skill carried across borders is re-established as a family business at successive migration stops, organizing where the household lives, how children contribute labor, how marriages form, and how kinship is sustained.
  gathers: Children's unpaid labor in family enterprise, Family business as weekly relative gathering point, Family business re-established at each migration stop, Family business relocation driving residential move, Horse-drawn delivery as business transport, Living above or adjacent to family business, Marriage through shared trade workplace, Mother as bakery skill source across borders, School releasing children for family business labor, Spouse's trade skill converting partner's occupation
- id td15ccc4c5a · "Forces and constraints shaping departure" — Departure is driven by household conflict, military conscription, and caregiving concerns that determine who leaves, who stays behind, and whether a spouse will follow.
  gathers: Children left behind with grandparent due to care concerns, Conscription recall as emigration trigger, Mother-in-law conflict as migration cause, Spouse's presence as condition for migration willingness
- id t92a3e13a7c · "Language and schooling across borders" — Schooling is shaped by the age at which a child enters, prior education begun abroad, and the gap between an official or colonial language and the language spoken at home.
  gathers: Age-based school placement despite language barrier, Early school start abroad as pre-migration education, Official language versus home language
- id tbb7a7a3822 · "Material conditions of relocation and settling" — The material conditions of settling are marked by what is lost or diminished in transit, housing quality relative to neighbors, and household-borne costs of utilities, schooling, and basic amenities.
  gathers: Clothing as portable wealth lost in transit, Company housing tied to employment, Icebox as marker of relative household comfort, School fees as immigrant household cost, Tenement hall bathrooms and coin-fed gas meters
- id t8c05417a17 · "Rural subsistence and barter economies" — Rural livelihood is defined by subsistence farming, barter exchange, and household labor that includes children and women as a matter of course.
  gathers: Child participation in farm slaughter, Livestock bartering as rural livelihood, Wartime food-for-clothing barter, Women's farm labour as unremarkable
- id tfe650cc175 · "Transit conditions and practices" — Transit involves ethnic segregation on vessels, personal networks securing religious dietary needs, and parental authority over children's activities and earnings during the journey.
  gathers: Jewish section on ship as ordinary travel arrangement, Kosher food sent by acquaintance during transit, Parent refusing children's earned money in transit
- id t8f12f3c428 · "Wage labour and its physical costs" — Wage labour after migration extracts a physical cost through injury, illness, or economic downturn that interrupts or ends the capacity to work.
  gathers: Depression-era underemployment straining household, Farm-to-housework transition for immigrant women, Mining work and health decline, Packing house as decades-long livelihood, Work interruptions from medical surgery

THE CODEBOOK, AND WHERE EACH CODE WAS FOUND

- Absent parent's letters and tickets as migration mechanism — Passages where emigration is set in motion by correspondence and documents sent from an absent parent rather than by a joint family decision.
- Age-based school placement despite language barrier — Passages where an immigrant child is placed in a grade matching their age rather than their language proficiency, with practical subjects easing the transition.
- Birth name superseded by everyday name — Passages where a person's given name at birth is replaced by a different name used in daily life.
- Child participation in farm slaughter — Passages where children are described as having assigned roles in killing and processing animals for food on a farm.
- Children left behind with grandparent due to care concerns — Passages where children are left with a grandparent because a parent fears inability to care for them during migration.
- Children's unpaid labor in family enterprise — Passages where children describe helping parents with tasks in a family business without receiving wages.
- Clothing as portable wealth lost in transit — Passages where migrants' accumulated clothing, intended as a resource for the new life, is stolen or lost during the journey.
- Company housing tied to employment — Passages where a worker's residence is provided by the employer and is contingent on the job.
- Conscription recall as emigration trigger — Passages where a military recall notice is described as what causes a family to emigrate rather than comply.
- Depression-era underemployment straining household — Passages where intermittent or reduced work during the Depression is described as creating financial pressure on a family.
- Dual birth date as official versus lived identity — Passages where a person's registered birth date differs from their actual birth date.
- Early school start abroad as pre-migration education — Passages where a child's schooling began at an unusually young age in the country of origin, giving them prior education before migration.
- Family business as weekly relative gathering point — Passages where relatives regularly gather at a family business on a particular day of the week.
- Family business re-established at each migration stop — Passages where a household livelihood is restarted in the same trade at successive migration locations.
- Family business relocation driving residential move — Passages where a family's move to a new area is described as tied to relocating their business there.
- Farm-to-housework transition for immigrant women — Passages where a woman's shift from agricultural labour abroad to domestic work after migration is described as a change in the kind of work she does.
- Generational contrast in homeland attachment — Passages where a parent's longing for the homeland is explicitly contrasted with a child's indifference or attachment to the new country.
- Horse-drawn delivery as business transport — Passages where a family business delivers its goods by horse and wagon.
- Icebox as marker of relative household comfort — Passages where a household appliance is noted as something that distinguished a household from neighbors who lacked it.
- Jewish section on ship as ordinary travel arrangement — Passages where a designated Jewish section on a transport vessel is mentioned as an unremarkable feature of the journey.
- Kosher food sent by acquaintance during transit — Passages where a crew member who knows the family personally sends kosher food to them during a voyage.
- Livestock bartering as rural livelihood — Passages where trading animals or animal products is described as a way of sustaining a rural household.
- Living above or adjacent to family business — Passages where a family's residence is described as being in the same building or across the street from their business.
- Marriage through shared trade workplace — Passages where a spouse is met through working in the same trade or business.
- Mining work and health decline — Passages where mine or smelter work is described as causing physical deterioration that eventually ends the worker's ability to labour.
- Mother as bakery skill source across borders — Passages where a woman's trade skill is described as the foundation of a family business re-established in each new location.
- Mother-in-law conflict as migration cause — Passages where harassment by a husband's mother is described as what drives a woman to leave for another country.
- Nationality shifting under one's birthplace — Passages where a person's country of birth is described as having changed its political identity, so that emigration occurs from a different country than the one they were born in.
- Naturalisation as civic belonging — Passages where acquiring citizenship and voting are described as acts that establish belonging in the receiving country.
- Obligated refugee housing during wartime — Passages where households are required by authority to share their homes with displaced people during conflict.
- Official language versus home language — Passages where a colonial or state-imposed language is distinguished from the everyday language spoken at home.
- Packing house as decades-long livelihood — Passages where industrial food processing is described as long-term wage employment that sustains a household over many years.
- Parent refusing children's earned money in transit — Passages where a parent forbids children from collecting money thrown to them for performing during a journey.
- Prior emigration of parent as precondition for family relocation — Passages where a family member's earlier migration and earnings abroad are described as what later enables the rest of the family to follow.
- Regional chain migration settlement — Passages where the clustering of people from the same home region in one destination is explained as a pattern of mutual integration.
- Relative as intermediary stop in migration route — Passages where a family member living at an intermediate location serves as a temporary waypoint in the migration journey.
- Return visits confirming belonging in receiving country — Passages where trips back to the homeland are described as reinforcing the migrant's sense that the receiving country is now home.
- School fees as immigrant household cost — Passages where paying for children's schooling is described as a financial burden the household must bear from its own earnings.
- School releasing children for family business labor — Passages where school authorities advise keeping children home to help with a family enterprise.
- Spouse's presence as condition for migration willingness — Passages where a wife's willingness to migrate is described as contingent on her husband having gone first.
- Spouse's trade skill converting partner's occupation — Passages where one spouse's existing trade skill causes the other spouse to shift into that occupation.
- Tenement hall bathrooms and coin-fed gas meters — Passages where shared bathrooms in hallways and coin-operated utility meters are described as features of tenement housing.
- Wartime food-for-clothing barter — Passages where rural people trade food to urban people in exchange for clothing during wartime scarcity.
- Women's farm labour as unremarkable — Passages where a woman's heavy physical farm work is described as normal or typical rather than exceptional.
- Work interruptions from medical surgery — Passages where physical conditions requiring surgery interrupt a worker's ability to maintain continuous employment.

WHAT THE RESEARCHER IS LOOKING FOR, IN THEIR OWN WORDS

"""
how people make a living after arriving, and what it costs them
"""

WHAT THE RESEARCHER SAID ABOUT THE THEMES, IN THEIR OWN WORDS

The researcher has said nothing about the themes.
```
