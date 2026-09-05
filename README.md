# Aperture

A reading companion for qualitative material — interviews, focus groups, field notes, documents,
open-ended survey answers.

Give it a piece of material and it works out what kind of thing it is, reads it, codes it, groups
the codes into themes, and then shows each theme as a line of claims through the text — every claim
resting on a verbatim quote, highlighted where it occurs, beside the material itself. Across a
corpus, each theme gets an account of where it holds, where it diverges, and where it is absent.
You comment in your own words on any block and that block is rewritten with your words in front of
it; you ask whether something is in the material and the answer comes back with the quotes that
make it true, or "not found in 397 passages". Nothing it claims is unquoted.

**Live:** `https://aperture.automate.business.aau.dk` — sign in with an account an administrator
made for you. Upload `.txt`, `.md`, `.docx`, `.pdf` or `.csv`.

- `docs/PLAN.md` — the design, the five laws, the layers, and what each prompt sees.
- `Astra-review.md` — the September 2026 review proposal: prioritized analysis fixes, document/project state, prompt changes, migration, evaluation, and further improvement ideas.
- `docs/RESEARCH.md` — what three rounds of trials established before this repository existed.
- `docs/MODELS.md` — the two providers and what a like-for-like comparison does and does not show.
- `docs/DEPLOY.md` — the deployment, and the two things the first rollout taught.
- `docs/prompts/` — every prompt compiled on real data, exactly as the model receives it.

```bash
python3 -m pytest tests -q          # the suite, offline, no model calls
uvicorn app.main:app --reload       # http://127.0.0.1:8000
```

Built for the MASSHINE project. MASSHINE funds the work; Aperture is the tool.
