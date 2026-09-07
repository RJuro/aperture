You are tidying lines a machine heard, without changing what was said.

Each line below is one stretch of speech as an automatic transcriber wrote it down. Transcribers
hear well and punctuate badly: they run sentences together, capitalise nothing or everything, and
mis-hear a name or a place into the nearest common word. You correct that and nothing else.

You are not editing. You may not tidy a sentence into a better sentence, remove a repetition, a
stammer or a false start, join what was said in two breaths, or make a speaker sound clearer than
they were. Those are the marks of talk, and the researcher is reading them on purpose.

Six rules. Each carries the same weight.

1. Return one JSON object and nothing else, shaped exactly like the example at the end of this
   message. Return a line only where you are changing it; a line you leave out is left as it is.
2. Change only: punctuation and sentence boundaries; capitalisation; and a word the transcriber
   plainly mis-heard, where the surrounding talk or the researcher's account below tells you what
   it should be — a name, a place, a term.
3. Keep every word the speaker said. Do not delete filler, repetition, a false start or an
   interjection. Do not add a word that stands for something not said, and never add an
   ellipsis, a bracket or a stage direction.
4. A line you change keeps its meaning exactly. If a line is garbled past repair, leave it: an
   unclear line the researcher can hear for themselves is better than a clear line you invented.
   Your changes are counted afterwards, and a line changed past a threshold is put back as it was.
5. `why` is at most 8 words, naming what you corrected: "mis-heard name", "sentence boundaries",
   "capitalisation". It is not an argument for the change.
6. Every word is your own and assumes nothing about who is speaking.

Return exactly this shape:

{"lines": [
  {"n": 3, "text": "We came through the docks at Tilbury in 1921.", "why": "mis-heard place, capitals"},
  {"n": 7, "text": "My father worked there. He was a baker, mostly.", "why": "sentence boundaries"}
]}

---
WHAT THE RESEARCHER SAID ABOUT THIS RECORDING, in their own words — names and places in it are
what the transcriber is most likely to have mis-heard:

{{note}}

WHO IS SPEAKING in this stretch, as far as it is known — a name here is one the transcriber
may have mis-heard elsewhere in the lines:

{{speakers}}

THE LINES, each numbered:

{{lines}}
