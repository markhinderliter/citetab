"""TT-008 — Font substitution during render (warning).

The render that determined every page number used one or more substituted fonts.
Substitute metrics are close but not identical, so a citation near a page
boundary may land one page off relative to a render with the document's true
fonts. A ``warning`` because it qualifies the accuracy of the core output. One
run-level finding naming each substitution pair and the render engine.
"""

from __future__ import annotations

from citetab.models.finding import Evidence, Finding
from citetab.rules.base import BaseRule, RuleContext, make_finding


class TT008(BaseRule):
    """Emit one warning when the render reported any font substitution."""

    def applies(self, ctx: RuleContext) -> bool:
        """Always evaluates; emits only when a substitution occurred."""
        return True

    def evaluate(self, ctx: RuleContext) -> list[Finding]:
        """Emit the substitution disclosure when the render reported one."""
        meta = ctx.registry.run_metadata
        if not meta.font_substitution_occurred:
            return []

        pairs = [
            {"original": sub.original, "substitute": sub.substitute}
            for sub in meta.font_substitutions
        ]
        pairs_text = "; ".join(
            f"{sub.original} → {sub.substitute}" for sub in meta.font_substitutions
        )
        evidence = Evidence(
            computed_values={
                "substitutions": pairs,
                "render_engine": meta.render_engine,
                "render_engine_version": meta.render_engine_version,
            },
        )
        return [
            make_finding(
                self.card,
                ctx,
                message=(
                    f"Page locations were computed under font substitution: "
                    f"{pairs_text}. Citations near page boundaries may differ by "
                    f"±1 page from a render with the original fonts. If exact page "
                    f"fidelity matters for filing, render your final PDF and "
                    f"spot-check boundary entries, or install the original fonts "
                    f"and re-run."
                ),
                evidence=evidence,
                remediation_hint=(
                    "Install the document's declared fonts (or render where they "
                    "are present) and re-run for exact page parity."
                ),
            )
        ]
