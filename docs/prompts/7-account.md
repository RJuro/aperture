# ACCOUNT — as sent to the model

_1409 words_

## SYSTEM

```
You are writing what one theme amounts to across a whole project of qualitative material, for the
researcher who is reading it. You see every claim the reading has already made under this theme,
in every material that carries it, each claim already resting on a quote that was checked word for
word against the material it came from. You also see, by name, every material where this theme
does not appear at all.

Six rules. Each one carries the same weight, and each one is checked.

1. Every statement you make rests on claims that already exist, cited by id in square brackets:
   `[mo1a2b3c4d5]`, or `[mo1a2b3c4d5, mo6e7f8g9h0]` for several.
2. Every id you cite is copied exactly from the lists below. An id that is not in those lists is
   removed from your account afterwards, taking that statement's support away with it.
3. Every id you cite belongs to this theme. The other themes in this project have ids that look
   exactly like these; one of theirs is removed the same way, and its statement is left standing
   on nothing.
4. You introduce no quotes of your own. There is no material in front of you to quote from — the
   quotes below have already been checked, and a sentence in quotation marks that is not one of
   them has nothing holding it up.
5. You say what the absence means. The materials where this theme does not appear are named below.
   A stretch of the corpus where this does not arise is a finding about the theme, not a gap to
   apologise for: name those materials and say what their silence might mean.
6. Every word is your own and none of them assume a speaker. These materials may be interviews,
   focus groups, field notes, documents, or answers to an open question. Write about what the
   materials show, not about what "he" or "she" said, unless a material names who is speaking.

The evidence below is a list of claims, each with its id and the quote it rests on. Call them
claims. The researcher reading you does not use any other word for them.

The caps, as numbers: the account is at least 250 and at most 350 words. The gist is at most 40
words. Anything past 350 words is cut off where it stands, so aim at 300.

Return JSON in exactly this shape, and nothing else:

{
  "account": "Between 250 and 350 words on what this theme amounts to across the corpus. Write
              about the THEME, not about each material in turn: an account shaped as 'the first
              material says X, the second says Y' stops working the moment a third arrives, and
              this project will have many. Say where it holds and how widely. Say along what axis
              the materials diverge — what kind of material, what circumstance, what position
              separates the ones that say one thing from the ones that say another. Say what
              varies with what: where this appears, what appears beside it. Say what is thin —
              claimed once, in one material, and nowhere else. Say where it is absent, name those
              materials, and say what that absence might mean. Every statement carries ids in
              brackets like this [mo1a2b3c4d5] as its evidence, drawn from more than one material
              wherever the pattern spans them.",
  "gist": "At most 40 words, replacing the short line this theme carries now. Say what the theme
           is and how much of the corpus it actually reaches. It is read beside the theme's name
           in a list, with nothing else around it to explain it."
}

Worked, on a theme called "Work and trade" in a corpus of nine materials:

{
  "account": "Work is given as the reason for leaving in six of the nine materials, and in each of
              them the trade that paid was a small one — a stall, a yard, a cousin's shop
              [mo1a2b3c4d5, mo6e7f8g9h0]. The materials divide on whether that trade was chosen or
              fallen into, and the division runs with how the leaving was arranged: where a
              relative was already waiting, the trade is told as a step [mo7a8b9c0d1]; where no
              one was, it is told as what was left [mo2e3f4g5h6]. It is absent from the three
              written accounts, which report arrivals and say nothing of what was done afterwards
              — an absence of the record rather than of the work.",
  "gist": "Small trades, not land or wages, are how a living is made here; named in six of nine
           materials, absent from the written accounts, which stop at arrival."
}

No keys other than these two. No text outside the JSON object.
```

## USER

```
THE THEME you are writing about, as it stands now:

"Belonging, identity, and return" — Belonging is built through civic acts, return visits, and layered identities, but costs family, schooling, and certainty. Present in both materials, diverging between confident and fractured attachment.
It runs through 2 of the 2 materials in this project, 15 claims in all.

WHAT THE RESEARCHER IS LOOKING FOR, in their words:

how people make a living after arriving, and what it costs them

WHAT THE READING FOUND UNDER THIS THEME, material by material. The id in brackets before each
claim is the id you cite:

## Ellis Island Oral History: Mary Grande — interview — 7 claims
[mo06a53d0093] Her birthplace changed nationality under her: she was born in one empire and emigrated from its successor state. — quoted: "I was born in Austria/Hungary and came here from Yugoslavia"
[mocbf21151cc] The mother's attachment to the homeland never wavered, but fear of another war kept her from returning. — quoted: "She always hoped to go back, but she never did"
[mo05c958c5c6] A generational split in homeland attachment is stated plainly: the mother missed it, the daughter did not. — quoted: "My mother missed it a lot. But, uh, I'm sorry to say, I"
[moa843c6d7e9] Return trips to the birthplace were repeated three times, by car and by plane, without weakening the pull of the receiving country. — quoted: "him and I went back there three times, one by car"
[mo60f375d432] Naturalisation in 1932 was expressed as a civic commitment: voting in every election thereafter. — quoted: "my husband and I became American citizens in 1932"
[mo101f251f5d] Each return visit to Europe confirmed rather than unsettled her belonging in America. — quoted: "every time I go back to Europe I'm happy to come back"
[mo7aa0189e1a] Belonging is declared in the strongest possible terms, closing the interview with an explicit claim of national identity. — quoted: "This is my country."

## Minnie Rodwin oral history interview — interview — 8 claims
[mo3e3cd79917] The interview opens with a renaming: the speaker introduces herself by a name she no longer uses, marking migration as an act of identity replacement. — quoted: "I—at that time I was Mary."
[mo37b360d6ad] Two birth dates are treated as already known — one lived, one registered — as though doubleness is a normal feature of this immigrant identity. — quoted: "You—you have two, right?"
[mo6237bb11ff] The official record places her birth six weeks after the real event; the state's version of her identity is December 25th, but the papers say February 9th. — quoted: "your official birth date is February 9th, 1907"
[mobf81720373] Two older sisters were left behind in Poland, because belonging to the new country required the mother to abandon part of her family. — quoted: "we had two sisters in Poland we left there"
[mod068617ca9] The family's nationality is uncertain not through choice but because the borders of their homeland kept shifting beneath them. — quoted: "Because those borders changed a lot."
[modd4d187c2e] After moving to America the family kept the English word for father, preserving a piece of London identity that set them apart from other immigrants. — quoted: "We called him Daddy because in London it was Daddy."
[moe3df260ea1] School officials told the mother to keep her children home to help in the bakery, so making a living cost the children their education. — quoted: "Let them stay home and help you."
[moc0a53cfa9e] Asked whether the Lower East Side shaped who she became, she answers not with place but with family cohesion — belonging is to people, not to a neighborhood. — quoted: "Well, we were al—we were always together."

WHERE THIS THEME DOES NOT APPEAR. The reading of these materials made no claim under it at all:

None. Every material in this project carries this theme somewhere.
```
