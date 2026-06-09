"""TT-003 — Stale page numbers in input TOA (info, aggregated).

Input-TOA entries whose page lists do not match the pages computed from the
converged render. Emitted as a single aggregated ``info`` finding with a
per-entry correction table — staleness is typically global, and one finding per
entry would be noise. ``passim`` is treated as a distinct value, so a list ⇄
passim transition is a correction. When the run did not converge (TT-007), the
corrected values are the last iteration's numbers and the message says so.
"""

from __future__ import annotations

from toatool.models.finding import Evidence, Finding
from toatool.pipeline.input_toa_diff import BaselineEntry
from toatool.rules.base import (
    BaseRule,
    RuleContext,
    diff_baseline_applies,
    make_finding,
)
from toatool.rules.support import passim_render, registry_by_id


def _input_repr(entry: BaselineEntry, render_text: str) -> str:
    """Render an input entry's page value (``passim`` or its listed pages)."""
    if entry.is_passim:
        return render_text
    return ", ".join(str(p) for p in entry.input_pages) if entry.input_pages else "—"


class TT003(BaseRule):
    """Emit a single aggregated info finding listing every stale entry."""

    def applies(self, ctx: RuleContext) -> bool:
        """Evaluates only on the heading/flag diff path with a parsed baseline."""
        return diff_baseline_applies(ctx)

    def evaluate(self, ctx: RuleContext) -> list[Finding]:
        """Build the correction table; emit one finding when any entry is stale."""
        registry = registry_by_id(ctx)
        render_text = ctx.profile.passim.render_text
        corrections: list[dict[str, object]] = []
        matched = 0
        for entry in ctx.baseline.entries:
            if not entry.parsed or entry.authority_id not in registry:
                continue
            matched += 1
            authority = registry[str(entry.authority_id)]
            actual_passim = authority.passim
            input_passim = entry.is_passim
            same = (input_passim and actual_passim) or (
                not input_passim
                and not actual_passim
                and entry.input_pages == list(authority.pages)
            )
            if same:
                continue
            corrections.append(
                {
                    "authority": authority.display_full,
                    "authority_id": authority.authority_id,
                    "input": _input_repr(entry, render_text),
                    "corrected": passim_render(authority, render_text),
                }
            )

        if not corrections:
            return []

        converged_note = (
            ""
            if ctx.converged
            else (
                " Pagination did not stabilize (see TT-007); the corrected values "
                "are the last iteration's numbers and are themselves suspect."
            )
        )
        evidence = Evidence(
            computed_values={
                "corrections": corrections,
                "matched_entries": matched,
            },
        )
        return [
            make_finding(
                self.card,
                ctx,
                message=(
                    f"{len(corrections)} of {matched} input Table-of-Authorities "
                    f"entries had stale page references. Page references were "
                    f"recomputed from the rendered document.{converged_note}"
                ),
                subject=(
                    f"{len(corrections)} of {matched} input TOA entries had stale "
                    f"page references"
                ),
                evidence=evidence,
            )
        ]
