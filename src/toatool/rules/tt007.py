"""TT-007 — Pagination non-convergence (error).

The fixed-point loop hit the iteration cap (5) without two consecutive renders
agreeing on every page. The outputs are still written with the last computed
numbers, but the page references for the oscillating authorities cannot be
trusted as filed. One run-level error naming the unstable entries and the values
they alternated between, per iteration. Honest non-convergence over pretended.
"""

from __future__ import annotations

from toatool.models.finding import Evidence, Finding
from toatool.rules.base import BaseRule, RuleContext, make_finding
from toatool.rules.support import registry_by_id


class TT007(BaseRule):
    """Emit one error when the loop reached the cap without converging."""

    def applies(self, ctx: RuleContext) -> bool:
        """Always evaluates; emits only when the run did not converge."""
        return True

    def evaluate(self, ctx: RuleContext) -> list[Finding]:
        """Emit the non-convergence error, listing the oscillating authorities."""
        if ctx.converged or len(ctx.page_history) < 2:
            return []

        last = ctx.page_history[-1]
        prev = ctx.page_history[-2]
        registry = registry_by_id(ctx)
        unstable: list[dict[str, object]] = []
        for authority_id in last:
            if list(last.get(authority_id, [])) == list(prev.get(authority_id, [])):
                continue
            authority = registry.get(authority_id)
            display = authority.display_full if authority else authority_id
            unstable.append(
                {
                    "authority": display,
                    "authority_id": authority_id,
                    "per_iteration_pages": [
                        list(snapshot.get(authority_id, []))
                        for snapshot in ctx.page_history
                    ],
                }
            )

        names = (
            ", ".join(str(row["authority"]) for row in unstable) or "(none isolated)"
        )
        evidence = Evidence(
            computed_values={
                "iterations": ctx.iteration_count,
                "iteration_cap": ctx.iteration_cap,
                "unstable": unstable,
            },
        )
        return [
            make_finding(
                self.card,
                ctx,
                message=(
                    f"Page numbering did not stabilize within {ctx.iteration_cap} "
                    f"iterations. {len(unstable)} entr"
                    f"{'y' if len(unstable) == 1 else 'ies'} oscillated and their "
                    f"page references in the output may be wrong: {names}. Verify "
                    f"these entries manually before filing."
                ),
                evidence=evidence,
                remediation_hint=(
                    "Hand-verify the named entries' pages against the rendered "
                    "PDF, or resolve the instability (often a passim-boundary flip)."
                ),
            )
        ]
