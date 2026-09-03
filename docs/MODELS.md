# Models

Both providers are first-class and chosen by `APERTURE_PROVIDER`. Every run row records the
provider, the model and its token counts, so a corpus's cost is visible after the fact.

## Reasoning

`reasoning_effort` is a per-provider default, overridable with `APERTURE_REASONING`
(`low` / `medium` / `high` / `off`).

| Provider | Model | Reasoning |
|---|---|---|
| `minimax` | MiniMax-M3 | on by default; takes no effort parameter, so nothing is sent |
| `mistral` | glm-5-2 | **off unless asked** — we send `high` |

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
