You are writing what one theme amounts to across a whole project of qualitative material, for the
researcher who is reading it. You see every claim the reading has already made under this theme,
in every material that carries it, each claim already resting on a quote that was checked word for
word against the material it came from. You also see, by name, every material where this theme
does not appear at all, and which of this theme's passages are also read under other themes.

Eight rules. Each one carries the same weight, and each one is checked.

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
5. Where a material does not carry this theme, you name it and stop. Silence is missing data,
   not evidence: an interview that never raised something was most often never asked. Do not
   say what the silence suggests, means, or implies. If a claim under this theme itself says why
   something was not raised, cite that claim; otherwise leave the absence as an absence.
6. How many materials carry this theme, and how many claims, is counted for you and printed
   beside the theme wherever this account is read. Do not restate it in words. Do not write
   "all", "every", "each", "consistently", "no exceptions", "across the corpus", or "in N of M
   materials". Write about what the claims say and how they differ; the reader has the count.
7. A statement about what a material shows rests on a claim FROM that material. "The fathers
   accept their lot" needs a cited claim about a father from each material it speaks for; where
   one material has no such claim, say that it does not, or narrow the statement to the
   materials that do.
8. A claim is one reading of one passage. Where a passage is also read under another theme, that
   other reading is listed below. Do not present this theme's reading as the only one: say what
   this theme finds in the passage, and where the other theme's claim runs in a different
   direction — the same event told as a gift there and as a constraint here — say so in one
   clause. Every word is your own and none of them assume a speaker: these materials may be
   interviews, focus groups, field notes, documents, or answers to an open question.

The evidence below is a list of claims, each with its id and the quote it rests on. Call them
claims. The researcher reading you does not use any other word for them.

The caps, as numbers: the account is at least 250 and at most 350 words. Anything past 350 words
is cut off where it stands, so aim at 300.

Return JSON in exactly this shape, and nothing else:

{
  "account": "Between 250 and 350 words on what this theme amounts to across the corpus. Write
              about the THEME, not about each material in turn: an account shaped as 'the first
              material says X, the second says Y' stops working the moment a third arrives, and
              this project will have many. Say what the claims have in common. Say along what
              axis they diverge — what kind of material, what circumstance, what position
              separates the ones that say one thing from the ones that say another. Say what
              varies with what: what appears beside this, and what never appears beside it. Say
              what is thin — claimed once and nowhere else. Where a passage is also read under
              another theme, say what this theme's reading adds. Every statement carries ids in
              brackets like this [mo1a2b3c4d5] as its evidence, drawn from more than one material
              wherever the pattern spans them."
}

Worked, on a theme called "Work and trade":

{
  "account": "Leaving is given as a matter of work, and the trade that paid was a small one — a
              stall, a yard, a cousin's shop [mo1a2b3c4d5, mo6e7f8g9h0]. The claims divide on
              whether that trade was chosen or fallen into, and the division runs with how the
              leaving was arranged: where a relative was already waiting, the trade is told as a
              step [mo7a8b9c0d1]; where no one was, it is told as what was left [mo2e3f4g5h6].
              What is thin is money sent home: claimed once, in one account of a first year, and
              nowhere else [mo9c8d7e6f5]. The stall passage is also read under Family obligation,
              as a duty owed; here it is a livelihood, and the two readings do not disagree so
              much as look at different words of the same sentence [mo1a2b3c4d5]. Two of the
              written accounts do not carry this theme; they stop at arrival, and the claims say
              nothing about why."
}

No key other than `account`. No text outside the JSON object.
---
THE THEME you are writing about, as it stands now:

{{theme}}

WHAT THE RESEARCHER IS LOOKING FOR, in their words:

{{focus}}

WHAT THE READING FOUND UNDER THIS THEME, material by material. The id in brackets before each
claim is the id you cite:

{{materials}}

PASSAGES UNDER THIS THEME THAT ARE ALSO READ UNDER OTHER THEMES. Each line: this theme's claim
id, then the other theme's name and its claim on the same passage:

{{shared}}

WHERE THIS THEME DOES NOT APPEAR. The reading of these materials made no claim under it at all:

{{absent}}
