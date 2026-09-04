# Index of the record

What each source in the predecessor repository was, and whether anything still depends on it.
Long-form condensations, by area, are in `docs/research/`.

| Source | What it is | Status |
|---|---|---|
| `design/ROUND-LEDGER.md` | The three rounds' evidence, defects D0–D18, arms, scores | **keep** — the primary record; condensed in RESEARCH.md §1–2 |
| `design/BLUEPRINT.md` | Post-round synthesis: five laws, mechanisms, build order | superseded by `docs/PLAN.md`; laws carried (RESEARCH §3) |
| `design/BUILDOUT.md` | The B0–B6 build plan for the old frontend | superseded; its lessons carried (RESEARCH §1.8) |
| `design/INSIGHT-LOOP.md`, `SIM-PLAN.md` | How the simulations were run and graded | keep — needed to run a round 4 |
| `design/INTERACTION-MODEL.md`, `RESEARCHER-WALKTHROUGH.md` | What a researcher does, scene by scene | superseded by three nouns / four verbs / two pages |
| `design/UI-AUDIT.md`, `V2-PLAN.md`, `VIEW-API-MAP.md` | Why the SPA failed; the server-rendered plan | superseded; decision carried (RESEARCH §3) |
| `design/MASSHINE.md`, `data-session-spec.md`, `P10.2-CONTRACT.md` | Earlier product specs | archive |
| `engine/sim_runs/round1..3/` | Reader memos, prompts, oracle verdicts, battery | **keep** — evidence; condensed in `research/simulation-rounds.md` |
| `engine/sim_runs/round2/screen-arm4-verdict.md` | The blind comparison that found the self-brief | keep — basis of the one self-prompting slot |
| `_archive/compass_artifact_…md`, `_archive/research.md` | Literature reviews | keep — condensed in RESEARCH.md §5 |
| `_archive/MASSHINE_v0_SPEC.md`, `REWORK_PLAN.md` | The v0 spec and its audit | archive |
| `packs/migration_oral_history/` | Standpoint personas and the friction matrix | archive; the attention-not-conclusion principle carried into ideation |
| `engine/exports/**` | Generated analyses (codes, themes, friction tables) | artefacts, not findings — discard |
| `engine/masshine/anchor.py`, `absence.py`, `store.py` (turn scan), `auth.py` | Code | **carried** into `app/` |
| `engine/seed_data/` (Grande, Rodwin) | The two public transcripts | **carried** into `seed/` |

The predecessor repository and its Coolify app can be removed once this one is deployed.
- [EVAL.md](EVAL.md) — the evaluation loop: run the chain on a fixed corpus, count what it produced (bookkeeping only), judge two records blind against the seven-point rubric in `scripts/eval_rubric.md`
