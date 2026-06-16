"""TT-001 — Unresolvable short-form citation (error).

A short form (``Ellison, 740 F.3d at 1133``) that eyecite cannot anchor to any
full citation refers to an authority that cannot be identified or placed in the
TOA. One finding per unresolvable *cluster* (per authority, not per occurrence):
the orphan occurrences are grouped by their reporter/volume signature so the two
*Ellison* short forms produce a single finding listing both locations.
"""

from __future__ import annotations

import re

from citetab.models.finding import Evidence, Finding
from citetab.pipeline.working import WorkingOccurrence
from citetab.rules.base import (
    BaseRule,
    RuleContext,
    make_finding,
    occurrence_ref,
)

# Reduce an orphan short form to the authority it points at: drop the pin-cite
# tail ("at 1133"), any "supra"/"id." token, and collapse whitespace. The two
# Ellison forms ("740 F.3d at 1133" / "at 1136") both reduce to "740 f.3d".
_PIN_TAIL_RE = re.compile(r"\bat\b.*$", re.IGNORECASE)
_SUPRA_RE = re.compile(r",?\s*supra.*$", re.IGNORECASE)
_ID_RE = re.compile(r"\bid\.?\b.*$", re.IGNORECASE)
_WS_RE = re.compile(r"\s+")


def _cluster_key(raw_text: str) -> str:
    """Return a stable key grouping orphan occurrences of the same authority."""
    key = _PIN_TAIL_RE.sub("", raw_text)
    key = _SUPRA_RE.sub("", key)
    key = _ID_RE.sub("", key)
    key = _WS_RE.sub(" ", key).strip(" ,").casefold()
    return key or raw_text.casefold()


class TT001(BaseRule):
    """Emit one error per unanchored short-form cluster."""

    def applies(self, ctx: RuleContext) -> bool:
        """Always evaluates; emits only when orphans exist."""
        return True

    def evaluate(self, ctx: RuleContext) -> list[Finding]:
        """Cluster the orphans and emit one finding each, in document order."""
        clusters: dict[str, list[WorkingOccurrence]] = {}
        for occ in ctx.unresolved:
            clusters.setdefault(_cluster_key(occ.raw_text), []).append(occ)

        findings: list[Finding] = []
        for occurrences in clusters.values():
            ordered = sorted(
                occurrences, key=lambda o: (o.paragraph_index, o.char_span)
            )
            representative = ordered[0].raw_text
            evidence = Evidence(
                occurrence_references=[occurrence_ref(o) for o in ordered],
                computed_values={"occurrence_count": len(ordered)},
            )
            findings.append(
                make_finding(
                    self.card,
                    ctx,
                    message=(
                        f"Short-form citation '{representative}' has no full "
                        f"citation anywhere in the brief. It cannot be identified "
                        f"or placed in the Table of Authorities. Add a full "
                        f"citation at its first appearance and re-run."
                    ),
                    subject=representative,
                    evidence=evidence,
                    remediation_hint=(
                        "Supply the authority's full citation at first use, then "
                        "re-run; until then it is omitted from the table."
                    ),
                )
            )
        findings.sort(key=lambda f: f.evidence.occurrence_references[0].paragraph_index)
        return findings
