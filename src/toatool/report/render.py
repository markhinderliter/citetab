"""Render a run as the Markdown findings report (REPORT_SPEC.md, normative).

Three parts in order (§2): the run header (§3), the generated Table of
Authorities (§4), then the findings, most actionable first (§5). The report is
always produced — even when the ``.docx`` is suppressed (TT-005), in which case
it is the only output and still carries the full table.

Determinism (§6): for a given input and environment the report is byte-stable
except the ``generated:`` timestamp and the render-engine version string;
:func:`mask_report` normalizes both so two runs compare equal. The ``finding_id``
ULID and ``evaluated_at_utc`` are deliberately not rendered (they live in the
optional sidecar, §7), so no other run-scoped value reaches the Markdown.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime

from toatool import __version__
from toatool.engine.profile_loader import CourtProfile
from toatool.engine.rule_loader import RULE_PACK_VERSION, RuleCard, load_rule_cards
from toatool.engine.runner import RuleRunResult
from toatool.models.finding import Finding
from toatool.pipeline import toa_builder
from toatool.pipeline.convergence import GenerationResult

_GENERATED_PREFIX = "- generated: "
_RENDER_PREFIX = "- render: "


def _now_iso() -> str:
    """Return the current UTC time as an ISO-8601 ``...Z`` timestamp."""
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _font_clause(gen: GenerationResult) -> str:
    """Render the header's font status: ``ok`` or ``substituted (pairs)``."""
    subs = gen.registry.run_metadata.font_substitutions
    if not subs:
        return "ok"
    pairs = "; ".join(f"{s.original} → {s.substitute}" for s in subs)
    return f"substituted ({pairs})"


def _placement_clause(gen: GenerationResult) -> str:
    """Render the header's placement line from the detected mechanism."""
    place = gen.placement
    if place.mechanism == "marker":
        return "[[TOA]] marker, consumed"
    if place.mechanism == "flag" and place.heading_match is not None:
        return f'--toa-heading "{place.heading_match.matched_text}"'
    if place.mechanism == "heading" and place.heading_match is not None:
        return f'heading "{place.heading_match.matched_text}"'
    return "none found — no placement mechanism matched"


def _pagination_clause(gen: GenerationResult) -> str:
    """Render the header's pagination line (converged or hit the cap)."""
    if gen.converged:
        n = max(gen.iteration_count, 1)
        plural = "iteration" if n == 1 else "iterations"
        return f"converged in {n} {plural} (cap 5)"
    return "DID NOT CONVERGE (cap 5 reached)"


def _header(
    gen: GenerationResult,
    rules: RuleRunResult,
    *,
    input_name: str,
    profile: CourtProfile,
    output_clause: str,
    generated_at: str,
) -> list[str]:
    """Build the run-header lines (§3)."""
    meta = gen.registry.run_metadata
    return [
        f"# toatool report — {input_name}",
        "",
        f"- engine {__version__} · rule pack toa {RULE_PACK_VERSION} · "
        f"profile {profile.id} {profile.version}",
        f"- input: {input_name} (sha256 {meta.input_sha256[:12]}…)",
        f"- render: {meta.render_engine} {meta.render_engine_version} headless · "
        f"fonts {_font_clause(gen)}",
        f"- placement: {_placement_clause(gen)}",
        f"- pagination: {_pagination_clause(gen)}",
        f"{_GENERATED_PREFIX}{generated_at}",
        f"- findings: {rules.error_count} error · {rules.warning_count} warning · "
        f"{rules.info_count} info",
        f"- output: {output_clause}",
    ]


def _toa_section(gen: GenerationResult, profile: CourtProfile) -> list[str]:
    """Build the generated Table of Authorities section (§4)."""
    lines = ["## Table of Authorities", ""]
    for group in gen.toa.groups:
        lines.append(f"### {group.label}")
        lines.append("")
        for authority in group.authorities:
            pages = toa_builder.page_text(authority, profile)
            lines.append(f"{authority.display_full}\t{pages}")
        lines.append("")
    return lines


def _render_occurrences(finding: Finding) -> str:
    """Render occurrence evidence as ``¶N p.M "excerpt"`` joined by semicolons."""
    parts = []
    for occ in finding.evidence.occurrence_references:
        page = f"p.{occ.page}" if occ.page is not None else "p.?"
        parts.append(f'¶{occ.paragraph_index} {page} "{occ.excerpt}"')
    return "; ".join(parts)


def _correction_table(finding: Finding) -> list[str]:
    """Render TT-003's per-entry corrections as a Markdown table."""
    rows = finding.evidence.computed_values["corrections"]
    lines = [
        "- evidence:",
        "",
        "| Authority | Input TOA | Corrected |",
        "|---|---|---|",
    ]
    for row in rows:
        lines.append(f"| {row['authority']} | {row['input']} | {row['corrected']} |")
    lines.append("")
    return lines


def _compact_values(finding: Finding) -> str:
    """Render remaining computed values as a compact ``key: value`` list."""
    values = finding.evidence.computed_values
    if "substitutions" in values:
        pairs = "; ".join(
            f"{s['original']} → {s['substitute']}" for s in values["substitutions"]
        )
        return (
            f"substituted fonts: {pairs} · render "
            f"{values['render_engine']} {values['render_engine_version']}"
        )
    if "unstable" in values:
        names = []
        for row in values["unstable"]:
            seq = " ⇄ ".join(",".join(map(str, p)) for p in row["per_iteration_pages"])
            names.append(f"{row['authority']} ({seq})")
        return "unstable: " + "; ".join(names)
    if "mechanisms_attempted" in values:
        return "; ".join(
            f"{m['mechanism']}: {m['result']}" for m in values["mechanisms_attempted"]
        )
    rendered = [f"{key}: {value}" for key, value in values.items()]
    return " · ".join(rendered)


def _evidence_lines(finding: Finding) -> list[str]:
    """Render the ``- evidence:`` line(s) for one finding."""
    if "corrections" in finding.evidence.computed_values:
        return _correction_table(finding)
    if finding.evidence.occurrence_references:
        return [f"- evidence: {_render_occurrences(finding)}"]
    if finding.evidence.toa_entry_references:
        entry = finding.evidence.toa_entry_references[0]
        pages = (
            f" (listed pages {', '.join(map(str, entry.input_pages))})"
            if entry.input_pages
            else ""
        )
        return [f'- evidence: "{entry.verbatim_text}"{pages}']
    if finding.evidence.computed_values:
        return [f"- evidence: {_compact_values(finding)}"]
    return []


def _authority_line(finding: Finding) -> str:
    """Render the ``- authority:`` line: every card citation, then the card path."""
    cites = "; ".join(f"{c.source} {c.section}" for c in finding.citations)
    return f"- authority: {cites}; rules/toa/{finding.rule_id}"


def _finding_block(finding: Finding, cards: Mapping[str, RuleCard]) -> list[str]:
    """Render one finding as a Markdown subsection (§5)."""
    name = cards[finding.rule_id].name if finding.rule_id in cards else finding.rule_id
    lines = [
        f"### {finding.rule_id} · {name} — {finding.severity} ({finding.confidence})",
        finding.message,
        "",
    ]
    if finding.subject is not None:
        lines.append(f"- subject: {finding.subject}")
    lines.extend(_evidence_lines(finding))
    lines.append(_authority_line(finding))
    if finding.remediation_hint is not None:
        lines.append(f"- before filing: {finding.remediation_hint}")
    lines.append("")
    return lines


def _findings_section(rules: RuleRunResult, cards: Mapping[str, RuleCard]) -> list[str]:
    """Build the findings section (§5), or the ``No findings.`` line."""
    lines = ["## Findings", ""]
    if not rules.findings:
        lines.append("No findings.")
        lines.append("")
        return lines
    for finding in rules.findings:
        lines.extend(_finding_block(finding, cards))
    return lines


def render_report(
    gen: GenerationResult,
    rules: RuleRunResult,
    *,
    input_name: str,
    profile: CourtProfile,
    output_clause: str,
    generated_at: str | None = None,
    cards: Mapping[str, RuleCard] | None = None,
) -> str:
    """Render the full Markdown report for a run (REPORT_SPEC §2–5).

    Args:
        gen: The settled generation result.
        rules: The evaluated rule-run result (findings, counts).
        input_name: The input file's display name (basename, never an abs path).
        profile: The active court profile.
        output_clause: The ``- output:`` line value (written path or SUPPRESSED).
        generated_at: The ``generated:`` timestamp; current UTC when omitted.
        cards: Loaded rule cards for rule names; loaded on demand when omitted.

    Returns:
        The report as a UTF-8 string with LF line endings and a terminal newline.
    """
    resolved_cards = cards if cards is not None else load_rule_cards()
    stamp = generated_at if generated_at is not None else _now_iso()
    lines: list[str] = []
    lines.extend(
        _header(
            gen,
            rules,
            input_name=input_name,
            profile=profile,
            output_clause=output_clause,
            generated_at=stamp,
        )
    )
    lines.append("")
    lines.extend(_toa_section(gen, profile))
    lines.extend(_findings_section(rules, resolved_cards))
    return "\n".join(lines).rstrip("\n") + "\n"


def mask_report(text: str) -> str:
    """Normalize the run-scoped header fields for byte-stable comparison (§6).

    Masks the ``generated:`` timestamp and the render-engine version string — the
    only non-deterministic values in the Markdown for a fixed input. ``finding_id``
    and ``evaluated_at_utc`` are never rendered, so nothing else needs masking.
    """
    masked: list[str] = []
    for line in text.splitlines():
        if line.startswith(_GENERATED_PREFIX):
            masked.append(f"{_GENERATED_PREFIX}<MASKED>")
        elif line.startswith(_RENDER_PREFIX):
            engine = line[len(_RENDER_PREFIX) :].split(" ", 1)[0]
            rest = line.split(" headless", 1)
            tail = f" headless{rest[1]}" if len(rest) == 2 else ""
            masked.append(f"{_RENDER_PREFIX}{engine} <VERSION>{tail}")
        else:
            masked.append(line)
    return "\n".join(masked) + "\n"
