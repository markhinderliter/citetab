"""TT-005 — TOA placement not found (error, suppresses .docx).

The placement walk found nothing: no ``--toa-heading`` match, no ``[[TOA]]``
marker, no default heading variant. Per spec §2.4 level 4 the regenerated
``.docx`` is **not** written (the only v1 rule with ``blocks_docx_output``); the
Markdown report is still produced and leads with the generated TOA. One run-level
finding that enumerates exactly what was searched for and how to enable insertion.
"""

from __future__ import annotations

from citetab.models.finding import Evidence, Finding
from citetab.rules.base import BaseRule, RuleContext, make_finding


class TT005(BaseRule):
    """Emit one error and suppress the .docx when no placement was found."""

    def applies(self, ctx: RuleContext) -> bool:
        """Always evaluates; emits only when placement detection found nothing."""
        return True

    def evaluate(self, ctx: RuleContext) -> list[Finding]:
        """Emit the placement-not-found error when the mechanism is ``none``."""
        if ctx.placement.mechanism != "none":
            return []

        variants = list(ctx.placement.searched_variants)
        generated = ctx.profile.heading.generated_text
        evidence = Evidence(
            computed_values={
                "mechanisms_attempted": [
                    {"mechanism": "--toa-heading override", "result": "not provided"},
                    {"mechanism": "[[TOA]] marker", "result": "none found"},
                    {"mechanism": f"heading variants {variants}", "result": "no match"},
                ],
            },
        )
        return [
            make_finding(
                self.card,
                ctx,
                message=(
                    f"No Table of Authorities location found in "
                    f"'{ctx.input_path.name}'. Searched for a '--toa-heading' "
                    f"override (not provided), a [[TOA]] marker (none), and the "
                    f"headings {variants} (no match). The generated TOA appears in "
                    f"this report; the .docx was not written. To insert it, add "
                    f"the heading '{generated}' where the table belongs, or place "
                    f"[[TOA]] on its own line there, then re-run."
                ),
                evidence=evidence,
                remediation_hint=(
                    f"Add a '{generated}' heading or a [[TOA]] marker where the "
                    f"table belongs, or pass --toa-heading, then re-run."
                ),
                blocks_docx_output=True,
            )
        ]
