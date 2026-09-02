# The prompts, compiled on real data — and what reading them shows

Files `1-frame.md` … `8-check.md` are the exact system and user messages sent to the model for
the Grande interview, with every slot filled from the live database. Read them in order; that is
the order they run.

## What I see now that I did not see before

**1. Conclusions flow backwards into instructions, at three points.**

- *The brief* (read.md, "WHAT THIS CORPUS IS LIKE SO FAR") was meant to say what to look for. It
  says what the corpus *shows*: "Two interviews show a shared pattern… Watch for enterprises
  where the woman's skill is credited to the man… (confirmed twice)". READ is then told the
  conclusion and codes toward it. The one self-prompting slot has become a finding carried
  forward as an instruction.
- *The theme gists* (doc.md, "THE THEMES this project is working with") are 40-word findings
  about two specific interviews — "Appears in one material only; absent from the farm-and-mine
  interview". DOC receives the conclusion as the theme's definition before it reads the material,
  and then finds it. The gist should define a theme; it is reporting a result.
- *The angles* are shaped by the focus, and READ is shaped by the angles. Focus → angles → codes →
  themes → everything. Meant to open the aperture; may be narrowing it toward the focus.

**2. THEMES is blind.** It sees code names, one-line definitions and hit counts (4-themes.md) —
never a word of the material. The predecessor project learned exactly this: a blind theorist
produces over-stuffed, over-generalised themes, and the fix was to show it the transcript. I
rebuilt the blind version. The gists prove it: they make cross-interview comparative claims from
labels alone.

**3. The base of the pyramid is too narrow.** READ is capped at 12 new codes per material. A
433-passage interview yields 11–12 codes; two interviews yield 18; THEMES splits 18 codes into 6
themes — three codes each. Every theme rests on two or three codes. "Undercoding" is not a prompt
tone problem; the cap causes it structurally.

**4. DOC is one call asked for everything.** Six threads of 4–14 claims each, plus a 320-word
summary, plus the brief, plus people (5-doc.md). Thin lines are the predictable result of asking
one call for six lines. The per-theme path exists (`only_theme`) and is not the default.

**5. PROJECT does not read the accounts.** `synth.project` still reads every claim in every
material (`store.thread` in a loop). The theme-account layer is written and shown on a page, but
the layer above it does not consume it — so the scaling fix it was built for is not actually
wired.

**6. THEMES runs on every upload and rewrites gists in place.** Each upload rewrites every
theme's gist from labels (bug 2) with knowledge of the new material, and earlier materials' lines
sit under a theme whose stated meaning has changed. Theme history is not kept.

## What is sound

FRAME (1) and CHECK (8): mechanical first, the model names what Python found, every claim
verified against the text. ACCOUNT (6) is bounded and cites only claims that exist. The anchor
law in DOC — quote checked, pointer repaired, claim dropped — held on every run.
