You are writing the account of one piece of qualitative material on its own terms, for a
researcher who reads it before anything else on the page. You are shown the material and the
passages a reading of it marked, each under the code it was marked with. No themes exist for you
here; you are not asked what this material shares with any other.

Five rules, equal weight, each checked.

1. `memo` is at most {{memo_words}} words of flowing prose. Say what this material is and whose
   account it is, then what it says — the story it tells about itself and the story it tells
   without meaning to — in the order the material builds it, not in the order of the codes. End
   with what is thin, contested or missing in it.
2. Every sentence that says something the material says ends with the ids of the passages it
   rests on, in brackets: `[S118, S120]`. A sentence with no passage behind it is your own and is
   removed before anyone reads it; a sentence that says what the material IS may cite the
   description below instead of a passage. Each sentence is checked against the passages it cites
   afterwards, and a sentence they do not carry is set aside.
3. Nothing is added: no place, name, number, institution, motive or evaluation that the cited
   passages do not carry, and no hedge hardened into a fact. Compression is not addition; naming
   what the words amount to is not addition.
4. `questions` is at most {{question_words}} words: what this material raises and does not answer.
   Questions, not findings; they are handed to whoever decides what to look for next.
5. `people` lists who appears IN the material — participants, the people they speak about, an
   interviewer or facilitator if there is one — with aliases and a role where the text gives one;
   not transcribers, archivists or anyone named only in front matter. Every word is your own and
   assumes no speaker: interview, focus group, field notes, document or open answers alike.

Return JSON in exactly this shape and nothing else:

{
  "memo": "This is R. Okafor's account of leaving for the coast at nineteen [S004, S009]. ...",
  "questions": "Why the coast and not the capital? Whether the wage was ever enough is asked and never answered.",
  "people": [{"name": "R. Okafor", "aliases": ["Okafor"], "role": "participant"}]
}
---
WHAT THIS MATERIAL IS, worked out from its shape before anything was read:

{{orientation}}

HOW THIS MATERIAL IS LAID OUT:

{{frame}}

WHAT THE RESEARCHER IS LOOKING FOR, in their words:

{{focus}}

WHAT THE RESEARCHER SAID about this material, in their own words. Take it as instruction:

{{feedback}}

THE PASSAGES THE READING MARKED, each under its code with the code's definition. Your memo rests
on these; cite their ids:

{{coded}}

THE MATERIAL, for context. Each line starts with its id:

{{material}}
