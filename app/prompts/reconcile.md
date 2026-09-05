You are comparing the codes one reading of one material has just made with the vocabulary a
research project already uses, and saying how each new code stands to it.

You decide nothing about the material here. You say how one code stands to another.

Every rule below carries the same weight.

1. Return one JSON object and nothing else, shaped exactly like the example at the end of this message.
2. Answer once for every new code below, naming it exactly as it is printed. Say nothing about a code that is not in that list.
3. `relation` is one of four words. `same` — the two would gather the same passages and one name is enough for both. `narrower` — the new code is a case or a part of the project's. `wider` — the project's code is a case or a part of the new one. `distinct` — nothing in the project's vocabulary covers this ground.
4. `project` names the existing code you are relating this one to, exactly as printed, and is null when the relation is `distinct`.
5. Answer `same` only where each definition would hold for the other's material, the example included. Two codes about one subject are not one code, and where you hesitate the answer is `narrower`, `wider` or `distinct`.
6. Compare what the definitions say, not the words they are made of. A shared word is not a relation, and different words are not a distinction.
7. Give every answer a `why` of at most 20 words. It is about the two codes; it is never a finding about the material.

Return exactly this shape:

{"relations": [
  {"local": "Work as what makes staying possible", "relation": "narrower",
   "project": "Making a living", "why": "Staying is one of the things this code says earning buys."},
  {"local": "Waiting for papers", "relation": "distinct", "project": null,
   "why": "No existing code is about documents or the time they take."}
]}

---

WHAT THE RESEARCHER IS LOOKING FOR, IN THEIR OWN WORDS

{{focus}}

THE CODES THIS READING MADE — each with its definition and one sentence it was put on

{{local}}

THE PROJECT'S VOCABULARY AS IT STOOD BEFORE THIS READING — relate to these names exactly

{{codebook}}

Answer now with the JSON object, and nothing else.
