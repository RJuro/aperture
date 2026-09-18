# Models

Both providers are first-class and chosen by `APERTURE_PROVIDER`. Every run row records the
provider, the model and its token counts, so a corpus's cost is visible after the fact.

## Reasoning

`reasoning_effort` is a per-provider default, overridable with `APERTURE_REASONING`
(`low` / `medium` / `high` / `off`).

| Provider | Model | Reasoning |
|---|---|---|
| `minimax` | MiniMax-M3 | on by default; takes no effort parameter, so nothing is sent |
| `mistral` | `zai-glm-latest` → **zai-glm-5-3** since 2026-09-18 | see below — the parameter means something different per version |
| `mistral` | glm-5-2 (until 2026-09-18) | **off unless asked** — we sent `high` |

### GLM 5.3: the same parameter, different meanings

Mistral's `zai-glm-latest` alias moves to Z.ai's newest GLM behind the scenes. Aperture asks for
the alias and records the version it resolved to (`llm.recorded_model`), so the analysis record
says `zai-glm-5-3`, never the alias.

The reasoning parameter did not carry over. Measured on a real THREAD prompt (51k characters,
DP-40 Grande × "Belonging, identity, and return"), two runs a setting:

| | seconds | output tokens | claims |
|---|---|---|---|
| 5.2 `medium` (what THREAD sent) | 45 – 56 | 5.2k – 6.2k | 11, 11 |
| 5.3 nothing sent | 181 – 193 | **32,000 — the cap** | **unparseable** |
| 5.3 `high` | 17 – 44 | 4.0k – 10.6k | 10, 13 |
| 5.3 `medium` | — | — | **400: not supported** |

Two things would have broken on a bare model switch. `medium` — asked for by THREAD, ACCOUNT,
VERIFY, VERIFY-SUMMARY and TIGHTEN — is refused, so every DOC step would have failed on its first
theme. And sending nothing, which FRAME did on 5.2 to switch reasoning off, makes 5.3 reason
without limit.

`llm.SENT_AS` translates the per-step levels (written in 5.2's words in `llm.EFFORT`) for the
version that answers: on 5.3 `medium` is sent as `high` and nothing is sent as `low`. FRAME at
`low` on a whole transcript: 2 s, 281 output tokens. A version that is not in the table is sent
as the newest one that is, and the log says it has not been measured — the next time the alias
moves, that warning is the prompt to measure again.

Not established: whether 5.3 reads better or worse than 5.2. Claim counts and depth on THREAD are
comparable; quality is a question for blind judging over a real run, not for these numbers.

GLM not reasoning is not a neutral default: left alone it answered a whole interview in 4.4k
output tokens and found roughly a third fewer claims. When it does reason it returns content as
typed blocks — a `thinking` block beside a `text` block — and only the text is the answer.

## One interview, both models, same pipeline

DP-40 Grande, 433 passages, five steps (shape, angles, read, themes, synthesis).

| | MiniMax-M3 | glm-5-2 @ high |
|---|---|---|
| Wall clock | 294s | **72s** |
| Input tokens | 33,800 | 34,400 |
| Output tokens | 61,396 | **13,230** |
| Output ÷ input | 1.82 | 0.38 |
| Quotes bound | 22 | 28 |
| Quotes not in the material | 0 | 0 |
| Cost at Mistral rates | — | **€0.090** |

## What this does and does not establish

**Robust, and repeated across two rounds:** GLM is roughly four times faster and spends four to
five times fewer output tokens for the same input. Both models ground cleanly — across three runs
the only quote that was not in the material came from M3, once.

**Not established: which reads better.** These are single runs of a stochastic process, and the
variance is larger than the gap. Two *identical* M3 runs of the same interview produced **37
claims across 5 themes** and **22 claims across 3 themes**, for the same token spend. Any
comparison of richness at one run each is measuring noise.

To settle it properly: several runs per model, and grade the output blind against the material
rather than counting it. The predecessor project's method applies — judge model output with blind
readers, never with a count.

## Practical reading

Use GLM for development: 72 seconds means a prompt change can actually be tried. Use it for the EU
deployment, where it is the option under contract. Use M3 when its longer deliberation is worth
five times the wall clock — which this comparison does not yet show it is.
