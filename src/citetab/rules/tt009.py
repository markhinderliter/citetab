"""TT-009 — Unlocated occurrence (warning).

The page locator could not place one or more citation occurrences in the rendered
output — typically a citation whose text straddles a physical page boundary, so
no single rendered page contains the whole string. Those occurrences are left
unmeasured (``page = None``, rendered ``p.?``). The ``.docx`` is still written and
every other occurrence and page survives: honest degradation over a crash or a
silently dropped page. One run-level warning names each unmeasured occurrence, in
document order. Skipped on the no-placement path (TT-005's domain), where no TOA
was emitted at all.
"""

from __future__ import annotations

from citetab.models.finding import Evidence, Finding
from citetab.rules.base import BaseRule, RuleContext, make_finding, occurrence_ref


class TT009(BaseRule):
    """Emit one warning when an emitted TOA has any unmeasured occurrence."""

    def applies(self, ctx: RuleContext) -> bool:
        """Evaluate only when a TOA was emitted; no-placement runs are TT-005's."""
        return ctx.placement.mechanism != "none"

    def evaluate(self, ctx: RuleContext) -> list[Finding]:
        """Disclose every occurrence the locator could not place (in document order)."""
        unmeasured = [
            (auth, occ)
            for auth in ctx.registry.authorities
            for occ in auth.occurrences
            if occ.page is None
        ]
        if not unmeasured:
            return []

        unmeasured.sort(key=lambda pair: (pair[1].paragraph_index, pair[1].char_span))
        references = [occurrence_ref(occ) for _, occ in unmeasured]
        computed = [
            {
                "authority": auth.display_full,
                "authority_id": auth.authority_id,
                "paragraph_index": occ.paragraph_index,
                "occurrence": occ.raw_text,
            }
            for auth, occ in unmeasured
        ]
        named = "; ".join(
            f"{auth.display_full} — '{occ.raw_text}'" for auth, occ in unmeasured
        )
        count = len(unmeasured)
        plural = count != 1
        evidence = Evidence(
            occurrence_references=references,
            computed_values={"unmeasured": computed},
        )
        return [
            make_finding(
                self.card,
                ctx,
                message=(
                    f"{count} citation occurrence{'s' if plural else ''} could not be "
                    f"placed on a rendered page and {'are' if plural else 'is'} shown "
                    f"as 'p.?': {named}. This usually means the citation's text falls "
                    f"across a page break. The rest of each authority's pages are "
                    f"unaffected; verify the unmeasured reference"
                    f"{'s' if plural else ''} against your final PDF before filing."
                ),
                evidence=evidence,
                remediation_hint=(
                    "Confirm the unmeasured citation's page in your rendered PDF, or "
                    "adjust the layout so the citation is not split across a page "
                    "break, and re-run."
                ),
            )
        ]
