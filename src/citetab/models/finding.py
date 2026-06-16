"""Pydantic models mirroring ``schemas/finding.schema.json``.

A :class:`Finding` is the canonical diagnostic unit produced while
generating a Table of Authorities. The Markdown report is a rendering of
the generated TOA followed by zero or more findings. A finding is emitted
only when there is something to disclose: a correction the tool made, a
problem the user must act on, or a render caveat. It is never a legal
judgment.

Fields follow ``docs/PRD.md`` section 16: there is no ``status`` or
``evaluation_path`` field (those were CallLint concepts that do not map to
a generator). Severity carries the meaning instead -- ``error`` and
``warning`` flag things the user must act on or verify, while ``info``
discloses normal behavior or a correction the tool made.

This module is the seed model committed during the design phase. The
engine and report renderer import it; tests cross-validate it against the
JSON Schema in both directions.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Severity = Literal["error", "warning", "info"]
Confidence = Literal["high", "medium", "low"]
OccurrenceForm = Literal["full", "short", "supra", "id", "ibid"]

_FINDING_ID = r"^f_[0-9A-HJKMNP-TV-Z]{26}$"
_RULE_ID = r"^[A-Z]{2}-[0-9]{3}$"
_SEMVER = r"^[0-9]+\.[0-9]+\.[0-9]+$"
_PROFILE_ID = r"^[a-z0-9_]+$"


class OccurrenceReference(BaseModel):
    """A citation occurrence in the document body cited as evidence."""

    model_config = ConfigDict(extra="forbid")

    paragraph_index: Annotated[int, Field(ge=0)]
    """Index of the paragraph in the body where the occurrence appears."""

    char_span: tuple[Annotated[int, Field(ge=0)], Annotated[int, Field(ge=0)]]
    """Inclusive-exclusive character offsets ``[start, end)`` within the paragraph."""

    form: OccurrenceForm
    """Citation form, as classified by eyecite resolution."""

    excerpt: str
    """Verbatim occurrence text. Never altered; truncation marked with an ellipsis."""

    page: int | None = Field(default=None, ge=1)
    """Page in the converged render, or ``None`` if the finding fired before one."""


class ToaEntryReference(BaseModel):
    """An entry from the input document's existing TOA cited as evidence."""

    model_config = ConfigDict(extra="forbid")

    verbatim_text: str
    """The input TOA entry exactly as it appeared, including page references."""

    input_pages: list[Annotated[int, Field(ge=1)]] = Field(default_factory=list)
    """Page references listed for this entry in the input TOA, when parseable."""

    parsed: bool = True
    """Whether the entry was interpretable as an authority plus page list."""


class Evidence(BaseModel):
    """Structured evidence supporting a finding, for auditing within the report."""

    model_config = ConfigDict(extra="forbid")

    occurrence_references: list[OccurrenceReference] = Field(default_factory=list)
    """Body occurrences the finding cites. Empty for input-TOA or run-level findings."""

    toa_entry_references: list[ToaEntryReference] = Field(default_factory=list)
    """Input-TOA entries the finding cites. Empty for body-only or run-level."""

    computed_values: dict[str, Any] = Field(default_factory=dict)
    """Rule-specific intermediate values (e.g. corrected_pages, passim_threshold)."""


class Citation(BaseModel):
    """A rule or style authority supporting a finding, copied from the rule card."""

    model_config = ConfigDict(extra="forbid")

    source: str
    """Authority source (e.g. 'FRAP', 'Bluebook', 'INPUT_OUTPUT_SPEC.md')."""

    section: str
    """Section within the source (e.g. '28(a)(2)', 'Rule 10.9', '§3.1')."""

    url: str | None = None
    """Optional URL to the cited text."""

    description: str | None = None
    """Optional gloss on why the authority supports the finding."""


class Finding(BaseModel):
    """A single rule outcome emitted while generating a Table of Authorities."""

    model_config = ConfigDict(extra="forbid")

    finding_id: Annotated[str, Field(pattern=_FINDING_ID)]
    """ULID identifying this finding instance; sortable by creation time."""

    rule_id: Annotated[str, Field(pattern=_RULE_ID)]
    """Identifier of the rule that produced this finding (e.g. 'TT-003')."""

    rule_version: Annotated[str, Field(pattern=_SEMVER)]
    """Semantic version of the rule card at generation time."""

    rule_pack_version: Annotated[str, Field(pattern=_SEMVER)]
    """Semantic version of the ``toa`` rule pack at generation time."""

    profile_id: Annotated[str, Field(pattern=_PROFILE_ID)]
    """Identifier of the court profile in force during the run (e.g. 'frap')."""

    profile_version: Annotated[str, Field(pattern=_SEMVER)]
    """Semantic version of the court profile in force during the run."""

    severity: Severity
    """What the finding demands of the user: error, warning, or info."""

    confidence: Confidence
    """Confidence in the finding's claim: high, medium, or low (v1 uses high/medium)."""

    message: str
    """Plain-language summary: what happened, what the tool did, what to verify."""

    evidence: Evidence
    """Structured evidence supporting the finding."""

    citations: list[Citation]
    """Supporting authorities, copied from the rule card."""

    evaluated_at_utc: str
    """ISO-8601 timestamp of when the rule was evaluated (not when the doc was)."""

    engine_version: Annotated[str, Field(pattern=_SEMVER)]
    """Semantic version of the citetab engine at generation time."""

    subject: str | None = None
    """Verbatim authority/entry/line the finding concerns; omitted for run-level."""

    authority_id: str | None = None
    """Registry Authority this finding maps to, when applicable."""

    remediation_hint: str | None = None
    """Optional clerical guidance on what to check before filing. Not legal advice."""

    blocks_docx_output: bool = False
    """Whether this finding suppressed the regenerated .docx (true only for TT-005)."""

    @model_validator(mode="after")
    def _error_and_warning_findings_cite_authority(self) -> Finding:
        """Require at least one citation for error and warning findings.

        Error and warning findings assert a problem against a rule or style
        authority, so they must carry the citation that grounds it. Info
        findings (disclosures and corrections the tool made) may omit it.
        """
        if self.severity in ("error", "warning") and not self.citations:
            raise ValueError(
                f"{self.severity} findings must carry at least one citation"
            )
        return self
