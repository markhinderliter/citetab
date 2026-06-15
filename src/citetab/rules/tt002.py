"""TT-002 — Authority missing from input TOA (info).

An authority cited in the body but absent from the input document's TOA. The
regenerated table includes it by construction, so this is an ``info`` disclosure
of the delta. One finding per missing authority. Confidence drops to ``medium``
for the whole run when the input TOA had unparseable entries (one of them might
have been the "missing" authority in a form the diff could not match).
"""

from __future__ import annotations

from citetab.models.finding import Confidence, Evidence, Finding
from citetab.rules.base import (
    BaseRule,
    RuleContext,
    baseline_has_unparsed,
    diff_baseline_applies,
    make_finding,
    occurrence_ref,
)


class TT002(BaseRule):
    """Emit one info per registry authority absent from the input TOA."""

    def applies(self, ctx: RuleContext) -> bool:
        """Evaluates only on the heading/flag diff path with a parsed baseline."""
        return diff_baseline_applies(ctx)

    def evaluate(self, ctx: RuleContext) -> list[Finding]:
        """Emit one finding per missing authority, in document order."""
        baseline_ids = {
            entry.authority_id
            for entry in ctx.baseline.entries
            if entry.parsed and entry.authority_id is not None
        }
        confidence: Confidence = "medium" if baseline_has_unparsed(ctx) else "high"
        caveat = (
            " (note: the input TOA also contained an entry the tool could not "
            "interpret, so this match is reported at medium confidence)"
            if baseline_has_unparsed(ctx)
            else ""
        )

        findings: list[Finding] = []
        for authority in ctx.registry.authorities:
            if authority.authority_id in baseline_ids:
                continue
            pages = authority.pages
            pages_text = ", ".join(str(p) for p in pages) if pages else "—"
            evidence = Evidence(
                occurrence_references=[
                    occurrence_ref(o) for o in authority.occurrences
                ],
                computed_values={
                    "pages": list(pages),
                    "occurrence_count": len(authority.occurrences),
                },
            )
            findings.append(
                make_finding(
                    self.card,
                    ctx,
                    confidence=confidence,
                    message=(
                        f"'{authority.display_full}' is cited in the body "
                        f"(pages {pages_text}) but had no entry in the input Table "
                        f"of Authorities. Added.{caveat}"
                    ),
                    subject=authority.display_full,
                    authority_id=authority.authority_id,
                    evidence=evidence,
                )
            )
        findings.sort(
            key=lambda f: (
                min(o.paragraph_index for o in f.evidence.occurrence_references)
                if f.evidence.occurrence_references
                else 0
            )
        )
        return findings
