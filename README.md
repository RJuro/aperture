# Aperture

A reading companion for qualitative material — interviews, focus groups, field notes, documents,
open-ended survey text.

It takes a piece of material, works out what shape it has, reads it, codes it, groups the codes,
and then shows each theme as a line through the material: short claims, each resting on a verbatim
quote highlighted where it occurs. You react to what it says; doubt sends it back to the material
rather than into a rewrite. Nothing it claims is unquoted.

`docs/PLAN.md` is the design and the build plan. `docs/DEPLOY.md` is the deployment.

```bash
python3 -m pytest tests -q          # the suite, offline, no model calls
uvicorn app.main:app --reload       # http://127.0.0.1:8000
```

Built for the MASSHINE project. MASSHINE funds the work; Aperture is the tool.
