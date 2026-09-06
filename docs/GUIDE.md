# The researcher's guide

The guide is served by the app at `/guide`. Its source — the whole of it — is
`app/templates/guide.html`, and that is the only copy: a second one in this directory would go
stale the first time a verb changed, and a researcher would cite it.

Each section has a stable id that a `?` link beside a control jumps to (`#what-happens`,
`#method`, `#focus`, `#themes`, `#reach`, `#lines`, `#absence`, `#comments`, `#rerun`, `#check`,
`#cases`, `#record`, `#sharing`, `#method-notes`). These ids must never move: reorganising the
page adds sections and ids around them, and keeps every one of these where a `?` link expects it.
`tests/test_p32_guide.py` holds the ids, checks that every `?` on the home and project pages
points at one that exists, and checks that the page does not speak the vocabulary
`context._BANNED` keeps off the page.

**The return path.** A `?` link that wants the Guide to offer an in-app way back — rather than
leaving browser Back as the only route — carries its own page as a query parameter, `from`, e.g.
`href="/guide?from=/p/{{ project.id }}#themes"` (the query comes before the fragment, in that
order). `app/pages.py`'s `_guide_origin` validates `from` the same way `accounts._local` validates
the sign-in page's `next`: it must be a path, not another site, and — because a project id is read
out of it — it must also match one of the app's own project routes. It then checks
`store.access` before naming the project or material, so the Guide never confirms a project
exists to someone it is closed to. Anything that fails either test falls back to "All projects".
A page with no `from` at all (a bookmarked or directly typed `/guide`) gets the same fallback, and
the Guide renders correctly either way.

**Developer documentation.** Where each answer is decided in the code used to end every section;
it now lives once, in `#developer-notes` at the end of the page. A researcher reading how to use
the instrument is not the same reader as one maintaining it, and should not be handed a module
name as ordinary help.
