"""The rule contract, evaluation context, and the finding factory (FR-10).

A rule is a small, independent object with an :attr:`Rule.id` and two methods:
:meth:`Rule.applies` (does this rule evaluate for this run?) and
:meth:`Rule.evaluate` (the findings it emits, in document order). Rules read only
the immutable :class:`RuleContext` the runner assembles once per run — they never
touch the pipeline or each other, so they can run in any order and the runner
sorts their combined output for presentation.

The split between *applies* and *evaluate* makes the rules-README "skipped vs.
failed" distinction executable: a rule that does not apply emits nothing (it is
skipped, not passed), and a rule that applies but finds nothing also emits
nothing. Neither is conflated with a clean result — that distinction is the
report layer's to draw, and it reads ``applies`` to draw it.

:func:`make_finding` centralizes the boilerplate every finding shares: the ULID,
the four version tracks, the card's citations, and the timestamp. A rule supplies
only what is rule-specific (message, severity override, evidence, subject).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol, runtime_checkable

from ulid import ULID

from citetab.engine.profile_loader import CourtProfile
from citetab.engine.rule_loader import RULE_PACK_VERSION, RuleCard
from citetab.models.finding import (
    Citation,
    Confidence,
    Evidence,
    Finding,
    OccurrenceForm,
    OccurrenceReference,
    Severity,
)
from citetab.models.registry import CitationRegistry
from citetab.pipeline.input_toa_diff import DiffBaseline
from citetab.pipeline.placement import PlacementResult
from citetab.pipeline.working import WorkingOccurrence

_SEVERITY_RANK: dict[Severity, int] = {"error": 0, "warning": 1, "info": 2}


@dataclass(frozen=True)
class RuleContext:
    """Everything the rules read, assembled once per run by the runner.

    Immutable by construction: the canonical registry is already frozen, and the
    placement, baseline, and orphan list are settled before the rules run.
    """

    input_path: Path
    profile: CourtProfile
    registry: CitationRegistry
    placement: PlacementResult
    baseline: DiffBaseline
    unresolved: tuple[WorkingOccurrence, ...]
    converged: bool
    iteration_count: int
    iteration_cap: int
    page_history: tuple[Mapping[str, Sequence[int]], ...]
    engine_version: str


@runtime_checkable
class Rule(Protocol):
    """A single Table-of-Authorities rule.

    Implementations are stateless apart from the :class:`RuleCard` they carry.
    ``evaluate`` is called only when ``applies`` returns ``True``; both receive
    the same context and must not mutate it.
    """

    card: RuleCard

    @property
    def id(self) -> str:
        """The rule id (e.g. ``TT-003``); matches the card's id."""
        ...

    def applies(self, ctx: RuleContext) -> bool:
        """Whether the rule evaluates for this run (its ``applies_when``)."""
        ...

    def evaluate(self, ctx: RuleContext) -> list[Finding]:
        """The findings the rule emits, in document order (may be empty)."""
        ...


class BaseRule:
    """Shared scaffolding: holds the card, derives ``id``, conforms to ``Rule``.

    The ``applies``/``evaluate`` defaults exist only so the base type satisfies
    the :class:`Rule` protocol; every concrete rule overrides both.
    """

    def __init__(self, card: RuleCard) -> None:
        """Bind the validated rule card this rule emits findings from."""
        self.card = card

    @property
    def id(self) -> str:
        """The rule id, taken from the card."""
        return self.card.id

    def applies(self, ctx: RuleContext) -> bool:  # pragma: no cover
        """Overridden by every concrete rule."""
        raise NotImplementedError

    def evaluate(self, ctx: RuleContext) -> list[Finding]:  # pragma: no cover
        """Overridden by every concrete rule."""
        raise NotImplementedError


def diff_baseline_applies(ctx: RuleContext) -> bool:
    """Whether the input-TOA diff rules (TT-002/003/004) evaluate.

    They compare against the input document's TOA region, which exists only on
    the heading/flag path with at least one parsed entry. On the marker-bootstrap
    path (and when the marker wins over a heading) there is no baseline, and an
    empty region is treated bootstrap-like — in all those cases the rules skip,
    and skipped is not passed (rules-README "skipped vs. failed").
    """
    return (
        ctx.placement.mechanism in ("heading", "flag")
        and ctx.baseline.available
        and len(ctx.baseline.entries) >= 1
    )


def baseline_has_unparsed(ctx: RuleContext) -> bool:
    """Whether the input TOA had any entry the baseline could not interpret."""
    return any(not entry.parsed for entry in ctx.baseline.entries)


def _now_iso() -> str:
    """Return the current UTC time as an ISO-8601 ``...Z`` timestamp."""
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


_EXCERPT_MAX = 160


class _HasOccurrence(Protocol):
    """Structural shape shared by registry and working occurrences."""

    form: OccurrenceForm
    raw_text: str
    paragraph_index: int
    char_span: tuple[int, int]
    page: int | None


def occurrence_ref(occ: _HasOccurrence) -> OccurrenceReference:
    """Convert a registry or working occurrence to a finding's evidence reference.

    The excerpt is the verbatim occurrence text, truncated with an ellipsis only
    when very long; it is never otherwise altered.
    """
    excerpt = occ.raw_text
    if len(excerpt) > _EXCERPT_MAX:
        excerpt = excerpt[: _EXCERPT_MAX - 1] + "…"
    return OccurrenceReference(
        paragraph_index=occ.paragraph_index,
        char_span=occ.char_span,
        form=occ.form,
        excerpt=excerpt,
        page=occ.page,
    )


def make_finding(
    card: RuleCard,
    ctx: RuleContext,
    *,
    message: str,
    severity: Severity | None = None,
    confidence: Confidence | None = None,
    subject: str | None = None,
    authority_id: str | None = None,
    evidence: Evidence | None = None,
    remediation_hint: str | None = None,
    blocks_docx_output: bool | None = None,
) -> Finding:
    """Build a :class:`Finding`, filling every field a rule shares from the card.

    Args:
        card: The emitting rule's validated card (version, citations, defaults).
        ctx: The run context (profile id/version, engine version).
        message: The plain-language message (rule-specific).
        severity: Overrides the card default when given.
        confidence: Overrides the card default when given.
        subject: The authority/entry/line the finding concerns; ``None`` is
            run-level.
        authority_id: Registry authority this maps to, when applicable.
        evidence: Structured evidence; an empty :class:`Evidence` when omitted.
        remediation_hint: Optional clerical "before filing" guidance.
        blocks_docx_output: Overrides the card default (TT-005 sets ``True``).

    Returns:
        A validated :class:`Finding` with a fresh ULID and timestamp.
    """
    return Finding(
        finding_id=f"f_{ULID()}",
        rule_id=card.id,
        rule_version=card.version,
        rule_pack_version=RULE_PACK_VERSION,
        profile_id=ctx.profile.id,
        profile_version=ctx.profile.version,
        severity=severity if severity is not None else card.severity_default,
        confidence=confidence if confidence is not None else card.confidence_default,
        message=message,
        evidence=evidence if evidence is not None else Evidence(),
        citations=[
            Citation(
                source=c.source,
                section=c.section,
                url=c.url,
                description=c.description,
            )
            for c in card.citations
        ],
        evaluated_at_utc=_now_iso(),
        engine_version=ctx.engine_version,
        subject=subject,
        authority_id=authority_id,
        remediation_hint=remediation_hint,
        blocks_docx_output=(
            blocks_docx_output
            if blocks_docx_output is not None
            else card.blocks_docx_output
        ),
    )


def _document_order_key(finding: Finding) -> tuple[int, int, int]:
    """Sort key placing occurrence-anchored findings first, in document order."""
    occurrences = finding.evidence.occurrence_references
    if occurrences:
        return (
            0,
            min(o.paragraph_index for o in occurrences),
            min(o.char_span[0] for o in occurrences),
        )
    if finding.evidence.toa_entry_references:
        return (1, 0, 0)
    return (2, 0, 0)


def sort_findings(findings: Sequence[Finding]) -> list[Finding]:
    """Order findings for presentation: severity → rule id → document order (FR-10).

    A stable sort, so within one (severity, rule id) the per-rule emission order
    — which each rule keeps in document order — is preserved for entry-anchored
    and run-level findings that share a document-order key.
    """
    return sorted(
        findings,
        key=lambda f: (_SEVERITY_RANK[f.severity], f.rule_id, _document_order_key(f)),
    )
