"""Domain-first module registry for active development.

New development should prefer `app.modules.<domain>` over the historical
`app.services` / `app.api.v1` scatter. Compatibility wrappers remain in place
so the app can keep running while the codebase is cleaned incrementally.
"""
