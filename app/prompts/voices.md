You are naming the voices in a transcript a machine made from a recording.

The recording was transcribed automatically. The transcriber separated the voices it heard and
lettered them — SPEAKER A, SPEAKER B — but it does not know who they are, and its lettering runs
only within one stretch of the recording. Below is the opening of one stretch, line by line, with
the letter the transcriber gave each voice. The researcher who made the recording has said who is
in it. Your job is to say, for each letter, whose voice it is.

Seven rules. Each carries the same weight.

1. Return one JSON object and nothing else, shaped exactly like the example at the end of this
   message, with an entry for every speaker letter listed below and for no other.
2. `role` is one of `interviewer`, `participant`, or `other`. The interviewer is the voice that
   asks and prompts; a participant is a voice that answers or tells; `other` is anyone else — a
   second interviewer's colleague, a passer-by, a child in the room, a voice that speaks once.
3. `name` is the person's name where the researcher's account gives one and the lines below
   support it, and an empty string otherwise. Never invent a name, and never take a name from the
   lines unless the speaker is being addressed or is introducing themselves.
4. Use what the researcher said as your first evidence. If they say there are two people and which
   of them leads, then two letters are those two people; a third letter is `other` unless the
   lines plainly show a third person the researcher did not mention.
5. Where the lines contradict the researcher's account, follow the lines and say so in `note` —
   the researcher is describing a recording they may not have listened to closely, and you are
   reading what was actually said.
6. `note` is at most 20 words, or empty. It is for what you could not settle: two voices you
   cannot tell apart, a letter that speaks too little to place, a name you are unsure of.
7. Every word outside the transcript is your own. Do not repeat a line back, do not summarise what
   was said, and do not comment on the content of the interview: you are identifying voices.

Return exactly this shape:

{"voices": [
  {"speaker": "SPEAKER A", "role": "interviewer", "name": "L. Byrne", "note": ""},
  {"speaker": "SPEAKER B", "role": "participant", "name": "R. Okafor", "note": ""},
  {"speaker": "SPEAKER C", "role": "other", "name": "", "note": "speaks twice, near the door"}
]}

---
WHAT THE RESEARCHER SAID ABOUT THIS RECORDING, in their own words:

{{note}}

THE VOICES TO NAME, as the transcriber lettered them in this stretch:

{{speakers}}

THE OPENING OF THIS STRETCH, each line with the voice that said it:

{{lines}}
