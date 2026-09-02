# Deploying Aperture

## Environment

| Variable | Required | What it does |
|---|---|---|
| `APERTURE_DATA_DIR` | yes in production | Where the SQLite file lives. **Must be a persistent volume** or every project vanishes on redeploy. The image sets `/data`. |
| `APERTURE_PIN` | yes on a shared host | Turns on the PIN gate. Unset means no auth at all — correct for local development, wrong for anything reachable. |
| `APERTURE_PROVIDER` | no | `minimax` (default) or `mistral`. Never inferred from which key is set. |
| `MINIMAX_API_KEY` | with `minimax` | MiniMax-M3. The cheaper of the two; used for development and testing. |
| `MISTRAL_API_KEY` | with `mistral` | GLM-5.2 under the university's Mistral contract. The EU-hosted option. |
| `APERTURE_MODEL` | no | Overrides the provider's default model. |
| `APERTURE_BASE_URL` | no | Overrides the provider's base URL. |
| `PORT` | no | Defaults to 8770. Coolify sets it. |

Secrets live in Coolify's environment and in a gitignored `.env` locally. Never in the repo, never
in a commit message, never printed to a log.

## Coolify

Create a **new application** from this repository. Build with the root `Dockerfile`. Mount
persistent storage at `/data`. Set the environment above. The healthcheck hits `/health`, which is
always outside the PIN gate.

**Never rename the application after it is created.** A rename in a previous project orphaned the
data volume and the recovery still has not happened. If the name is wrong, live with it or migrate
the volume deliberately — the name in the dashboard is not worth a lost corpus.

## First run

There is no auto-seeded demo. Make a project, add a piece of material, and the upward chain runs:
work out the layout, read, find themes, write the threads, update the project summary.

## Cost

Both providers charge for thinking as output tokens. Every run row records provider, model and
token counts, and the export prints them, so a corpus's cost is visible after the fact rather than
guessed at beforehand.

## Model changes

`tests/recorded/` holds real model output, recorded once per phase and replayed by the test suite
offline. A new model is checked by re-recording against it and reading the anchor tally: quotes
that bind versus quotes that are not in the material. A silent drop in that ratio is the only thing
that would show a model has stopped being usable, and it is free to measure.
