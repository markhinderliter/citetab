"""Evaluate the rule pack over a generation result (FR-10, §20 oracle).

The runner is the one place that turns a :class:`~toatool.pipeline.convergence.
GenerationResult` into findings and a process outcome. It assembles the immutable
:class:`~toatool.rules.base.RuleContext`, validates that the cards and
implementations correspond (the loader's drift check), runs every applicable
rule, sorts the combined findings for presentation, and derives the
``.docx``-suppression flag and the CLI exit code.

Exit codes (PRD §20 / FR-11): ``0`` = success (info/warning findings allowed),
``1`` = any error finding or a suppressed ``.docx`` (TT-005, TT-007 paths). The
``2`` = invocation/parse-failure code is the CLI's to return and is not produced
here — a malformed input never reaches the rules.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from toatool import __version__
from toatool.engine.profile_loader import CourtProfile
from toatool.engine.rule_loader import load_rule_cards, validate_implementations
from toatool.models.finding import Finding
from toatool.pipeline import convergence, input_toa_diff, parser
from toatool.pipeline.convergence import GenerationResult
from toatool.rules import RULE_CLASSES, build_rules, sort_findings
from toatool.rules.base import RuleContext


@dataclass(frozen=True)
class RuleRunResult:
    """The outcome of evaluating the rule pack over one generation result."""

    findings: tuple[Finding, ...]
    docx_suppressed: bool
    exit_code: int

    @property
    def error_count(self) -> int:
        """Number of error-severity findings."""
        return sum(1 for f in self.findings if f.severity == "error")

    @property
    def warning_count(self) -> int:
        """Number of warning-severity findings."""
        return sum(1 for f in self.findings if f.severity == "warning")

    @property
    def info_count(self) -> int:
        """Number of info-severity findings."""
        return sum(1 for f in self.findings if f.severity == "info")

    def by_rule(self) -> dict[str, int]:
        """Count of findings per rule id, for the oracle and the report header."""
        counts: dict[str, int] = {}
        for finding in self.findings:
            counts[finding.rule_id] = counts.get(finding.rule_id, 0) + 1
        return counts


def build_context(
    result: GenerationResult,
    *,
    input_path: Path,
    profile: CourtProfile,
) -> RuleContext:
    """Assemble the rule context from a generation result.

    The input-TOA diff baseline is built here from the same placement the
    generation used, so the diff rules see exactly the region the generator
    replaced (or, on the marker/none paths, no baseline at all).
    """
    parsed = parser.parse(input_path)
    baseline = input_toa_diff.build_baseline(parsed, result.placement, profile)
    return RuleContext(
        input_path=input_path,
        profile=profile,
        registry=result.registry,
        placement=result.placement,
        baseline=baseline,
        unresolved=tuple(result.unresolved),
        converged=result.converged,
        iteration_count=result.iteration_count,
        iteration_cap=convergence.ITERATION_CAP,
        page_history=tuple(result.page_history),
        engine_version=__version__,
    )


def run_rules(
    result: GenerationResult,
    *,
    input_path: Path,
    profile: CourtProfile,
    rules_root: Path | None = None,
) -> RuleRunResult:
    """Evaluate every applicable rule over a generation result.

    Args:
        result: The settled generation result (frozen registry, placement,
            orphans, page history).
        input_path: The input brief (for the diff baseline and TT-005's message).
        profile: The active court profile.
        rules_root: Optional override for the rules directory (tests/bundled).

    Returns:
        A :class:`RuleRunResult` with the sorted findings, the suppression flag,
        and the exit code.

    Raises:
        RuleLoaderError: If the cards and implementations have drifted apart.
    """
    cards = load_rule_cards(rules_root)
    validate_implementations(cards, RULE_CLASSES.keys())
    rules = build_rules(cards)
    ctx = build_context(result, input_path=input_path, profile=profile)

    findings: list[Finding] = []
    for rule in rules:
        if rule.applies(ctx):
            findings.extend(rule.evaluate(ctx))
    ordered = sort_findings(findings)

    docx_suppressed = result.blocks_docx_output or any(
        f.blocks_docx_output for f in ordered
    )
    has_error = any(f.severity == "error" for f in ordered)
    exit_code = 1 if (has_error or docx_suppressed) else 0
    return RuleRunResult(
        findings=tuple(ordered),
        docx_suppressed=docx_suppressed,
        exit_code=exit_code,
    )
