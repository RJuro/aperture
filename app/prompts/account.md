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
---
THE THEME you are writing about, as it stands now:

{{theme}}

WHAT THE RESEARCHER IS LOOKING FOR, in their words:

{{focus}}

WHAT THIS CORPUS IS LIKE, written after the last piece was read:

{{brief}}

WHAT THE READING FOUND UNDER THIS THEME, material by material. The id in brackets before each
claim is the id you cite:

{{materials}}

WHERE THIS THEME DOES NOT APPEAR. The reading of these materials made no claim under it at all:

{{absent}}
