"""Small shared helpers used by more than one rule module."""

from __future__ import annotations

from citetab.models.registry import Authority
from citetab.rules.base import RuleContext


def registry_by_id(ctx: RuleContext) -> dict[str, Authority]:
    """Map authority id → frozen registry authority for the run."""
    return {auth.authority_id: auth for auth in ctx.registry.authorities}


def passim_render(authority: Authority, render_text: str) -> str:
    """Render an authority's page value: ``passim`` or its ascending page list."""
    if authority.passim:
        return render_text
    return ", ".join(str(p) for p in authority.pages) if authority.pages else "—"
