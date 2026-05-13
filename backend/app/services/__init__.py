"""Compatibility layer for historical service imports.

New development should prefer `app.modules.<domain>` for domain entrypoints.
The `app.services` package remains only to avoid breaking existing imports while
we converge the codebase onto the new domain-first layout.
"""
