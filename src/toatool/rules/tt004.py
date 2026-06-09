"""TT-004 — Phantom input-TOA entry (warning, medium).

An input-TOA entry that matches no authority found in the body. The regenerated
table omits it by construction, but the omission is a ``warning`` (always
``medium``): the entry may be a true remnant, or the body citation may exist and
eyecite failed to parse it — and silently dropping a real authority from a legal
filing is the costly case. One finding per removed or unparsed entry.
"""

from __future__ import annotations

from toatool.models.finding import Evidence, Finding, ToaEntryReference
from toatool.rules.base import (
    BaseRule,
    RuleContext,
    diff_baseline_applies,
    make_finding,
)
from toatool.rules.support import registry_by_id


class TT004(BaseRule):
    """Emit one warning per unmatched or unparsed input-TOA entry."""

    def applies(self, ctx: RuleContext) -> bool:
        """Evaluates only on the heading/flag diff path with a parsed baseline."""
        return diff_baseline_applies(ctx)

    def evaluate(self, ctx: RuleContext) -> list[Finding]:
        """Emit one finding per phantom (unmatched) and per unparsed entry."""
        registry = registry_by_id(ctx)
        findings: list[Finding] = []
        for entry in ctx.baseline.entries:
            if entry.parsed and entry.authority_id in registry:
                continue
            evidence = Evidence(
                toa_entry_references=[
                    ToaEntryReference(
                        verbatim_text=entry.verbatim_text,
                        input_pages=list(entry.input_pages),
                        parsed=entry.parsed,
                    )
                ],
            )
            if entry.parsed:
                message = (
                    f"Input TOA entry '{entry.verbatim_text}' matches no citation "
                    f"found in the body. It was removed from the regenerated Table "
                    f"of Authorities. If this authority IS cited in the brief, the "
                    f"citation was not recognized — verify before filing."
                )
            else:
                message = (
                    f"Input TOA line '{entry.verbatim_text}' could not be "
                    f"interpreted as an authority and page list, and does not "
                    f"appear in the regenerated table. Verify before filing."
                )
            findings.append(
                make_finding(
                    self.card,
                    ctx,
                    message=message,
                    subject=entry.verbatim_text,
                    evidence=evidence,
                    remediation_hint=(
                        "Confirm the authority is genuinely uncited; if it is "
                        "cited, the citation was not recognized by the parser."
                    ),
                )
            )
        return findings
