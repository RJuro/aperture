# The researcher's guide

The guide is served by the app at `/guide`. Its source — the whole of it — is
`app/templates/guide.html`, and that is the only copy: a second one in this directory would go
stale the first time a verb changed, and a researcher would cite it.

Fourteen sections, each with a stable id that a `?` link beside a control jumps to
(`#what-happens`, `#method`, `#focus`, `#themes`, `#reach`, `#lines`, `#absence`, `#comments`,
`#rerun`, `#check`, `#cases`, `#record`, `#sharing`, `#method-notes`). `tests/test_p32_guide.py`
holds the ids, checks that every `?` on the home and project pages points at one that exists, and
checks that the page does not speak the vocabulary `context._BANNED` keeps off the page.

Each section ends with the module that decides the behaviour. When a verb changes, the section
that names its module changes with it.
