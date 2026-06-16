"""TT-006 — Marker and heading both present (warning).

When a ``[[TOA]]`` marker and a detectable heading region both exist, the marker
wins: the generated TOA replaces the marker and the heading region — including any
stale table under it — is left untouched, so the output carries two TOA-like
regions until the drafter deletes the old one. This warning makes that state
impossible to miss. Additional ``[[TOA]]`` markers beyond the first are each
named in their own warning (ambiguous placement; the first marker wins).
"""

from __future__ import annotations

from citetab.models.finding import Evidence, Finding
from citetab.rules.base import BaseRule, RuleContext, make_finding


class TT006(BaseRule):
    """Emit a warning when marker and heading both matched (and per extra marker)."""

    def applies(self, ctx: RuleContext) -> bool:
        """Evaluates when a marker matched, or extra markers are present."""
        place = ctx.placement
        return place.marker_matched and (
            place.heading_matched or bool(place.extra_marker_indices)
        )

    def evaluate(self, ctx: RuleContext) -> list[Finding]:
        """Emit the conflict warning, plus one per additional marker."""
        place = ctx.placement
        findings: list[Finding] = []

        if place.heading_matched and place.heading_match is not None:
            match = place.heading_match
            evidence = Evidence(
                computed_values={
                    "marker_paragraph_index": place.marker_index,
                    "heading_text": match.matched_text,
                    "heading_paragraph_index": match.heading_index,
                    "heading_region": [match.region_start, match.region_end],
                },
            )
            findings.append(
                make_finding(
                    self.card,
                    ctx,
                    message=(
                        f"Both a [[TOA]] marker and an existing "
                        f"'{match.matched_text}' section were found. The generated "
                        f"table was placed at the marker. The existing section "
                        f"(paragraph {match.heading_index}) was NOT modified or "
                        f"removed — the output now contains both. Delete the old "
                        f"section before filing."
                    ),
                    evidence=evidence,
                    remediation_hint=(
                        "Delete the pre-existing Table of Authorities section "
                        "before filing; the generated one is at the marker."
                    ),
                )
            )

        for extra in place.extra_marker_indices:
            findings.append(
                make_finding(
                    self.card,
                    ctx,
                    message=(
                        f"An additional [[TOA]] marker was found at paragraph "
                        f"{extra} and was left in place — placement is ambiguous "
                        f"when more than one marker is present, so only the first "
                        f"marker received the generated table. Remove the extra "
                        f"marker before filing."
                    ),
                    evidence=Evidence(
                        computed_values={"extra_marker_paragraph_index": extra}
                    ),
                    remediation_hint=(
                        "Remove the extra [[TOA]] marker; only the first is used."
                    ),
                )
            )
        return findings
