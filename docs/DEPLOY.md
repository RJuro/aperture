# Deploying Aperture

## Environment

| Variable | Required | What it does |
|---|---|---|
| `APERTURE_DATA_DIR` | yes in production | Where the SQLite file lives. **Must be a persistent volume** or every project vanishes on redeploy. The image sets `/data`. |
| `APERTURE_ADMIN` | yes on a shared host | `name:password`. Creates the first admin on first boot when no user exists; the admin then makes users on `/admin`. With no users the instance is open — correct for a laptop, wrong for anything reachable. |
| `APERTURE_PROVIDER` | no | `minimax` (default) or `mistral`. Never inferred from which key is set. |
| `MINIMAX_API_KEY` | with `minimax` | MiniMax-M3. The cheaper of the two; used for development and testing. |
| `MISTRAL_API_KEY` | with `mistral` | GLM-5.2 under the university's Mistral contract. The EU-hosted option. |
| `APERTURE_MODEL` | no | Overrides the provider's default model. |
| `APERTURE_BASE_URL` | no | Overrides the provider's base URL. |
| `PORT` | no | Defaults to 8770. Coolify sets it. |

Secrets live in Coolify's environment and in a gitignored `.env` locally. Never in the repo, never
in a commit message, never printed to a log.

## Coolify

Two things learned deploying this the first time, both of which cost a rollout:

- **The image must contain `curl`.** Coolify's rollout healthcheck shells out to `curl` (or
  `wget`) inside the new container. `python:3.12-slim` has neither, so a perfectly healthy start
  was judged unhealthy and rolled back. The Dockerfile installs it.
- **Every push to `main` redeploys, and without the volume below every redeploy wipes the database.**
  This is not hypothetical: on the first day, two pushes of a small change replaced the container
  in the middle of a live walkthrough and erased its project, its user and its running analysis.
  Until the volume is attached, either do not push, or turn off automatic deployment on the
  application in the Coolify UI (the API does not expose the setting).
- **Persistent storage could not be attached through the API** (every `type` value was rejected
  with a 422). Attach it in the Coolify UI: the application → *Persistent Storage* → add a volume
  mounted at `/data`. **Do this before anyone uploads real material.** Without it a redeploy starts
  with an empty database, and that is the loss the predecessor project already suffered once.

The application `aperture` exists (created 2026-09-03 from `https://github.com/RJuro/aperture`, project `automate`, environment `production`, domain `aperture.automate.business.aau.dk`). Build with the root `Dockerfile`. Mount
persistent storage at `/data`. Set the environment above. The healthcheck hits `/health`, which is
always outside the sign-in.

**Never rename the application after it is created.** A rename in a previous project orphaned the
data volume and the recovery still has not happened. If the name is wrong, live with it or migrate
the volume deliberately — the name in the dashboard is not worth a lost corpus.

## First run

There is no auto-seeded demo. Make a project, add a piece of material, and the upward chain runs:
work out the layout, read, find themes, write the threads, update the project summary.

## Monitoring

The app logs to stdout under the name `aperture`; Coolify collects it at the application →
**Logs**, beside uvicorn's access lines. One line per model call, per job and per step, `key=value`
and grep-able:

```
llm  label=thread provider=minimax model=MiniMax-M3 in=7692 out=1681 s=63.2
llm  label=thread busy=429 wait=30s try=2/5            · the provider is loaded; it is waiting
llm  label=project json=retry | json=repaired          · the answer would not parse
job  id=j… project=p… started steps=17 | finished s=… | stopped | failed
step kind=doc project=p… material=m… started | finished s=… in=… out=… | failed: …
```

Grep `busy=429` for a rate-limited afternoon, `ERROR` or `failed` for a chain that stopped, and
`started` with no `finished` after it for the hang this exists to catch. **Ids only**: no prompt,
no material, no title, no quote — a log leaves the researcher's machine and a title is usually
somebody's name. The reason in full is on the run row, where its owner reads it.

`/admin/runs` is the same thing after the fact, for an administrator: the last fourteen days by
day (runs, failures, tokens, minutes of model time) and the last 200 runs across every project.

## Cost

Both providers charge for thinking as output tokens. Every run row records provider, model and
token counts, and the export prints them, so a corpus's cost is visible after the fact rather than
guessed at beforehand.

## Model changes

`tests/recorded/` holds real model output, recorded once per phase and replayed by the test suite
offline. A new model is checked by re-recording against it and reading the anchor tally: quotes
that bind versus quotes that are not in the material. A silent drop in that ratio is the only thing
that would show a model has stopped being usable, and it is free to measure.
