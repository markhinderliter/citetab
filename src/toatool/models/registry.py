"""The Citation Registry — toatool's canonical internal data model.

``INPUT_OUTPUT_SPEC.md`` §4 defines the registry as "the single structure the
pipeline produces and every output renders from." This module is the Pydantic
realization of that spec, mirroring ``schemas/registry.schema.json`` field for
field; tests cross-validate the two in both directions.

The registry has two parts:

- :class:`Authority` objects (each with its :class:`Occurrence` list, resolved
  pages, and passim flag) — the content of the Table of Authorities.
- :class:`RunMetadata` — the run-level provenance (versions, render engine,
  font substitution, iteration count, input hash) that makes any generated TOA
  reproducible and auditable after the fact.

A note on one deliberate deviation from spec §4.2, which marks
``Occurrence.page`` as required: here ``page`` is nullable and defaults to
``None``. Occurrences are discovered at parse time, before any render assigns
them a page, so a partial registry needs to represent "page not yet measured."
This mirrors the analogous nullable ``page`` in ``finding.schema.json``'s
occurrence evidence. In a *converged* registry every occurrence carries an
integer page.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field

AuthorityType = Literal[
    "case", "statute", "regulation", "constitutional", "rule", "secondary"
]
"""The kind of authority, per spec §4.1. Maps to a profile group via ``types``."""

GroupKey = Literal[
    "cases", "constitutional", "statutes", "regulations", "rules", "other"
]
"""TOA grouping bucket, keyed to the active court profile's ``groups``."""

OccurrenceForm = Literal["full", "short", "supra", "id", "ibid"]
"""Citation form of a single occurrence, as classified by eyecite resolution."""

OccurrenceConfidence = Literal["high", "medium"]
"""Location confidence: ``high`` = exact span match; ``medium`` = approximated."""

_SEMVER = r"^[0-9]+\.[0-9]+\.[0-9]+$"
_PROFILE_ID = r"^[a-z0-9_]+$"
_SHA256 = r"^[0-9a-f]{64}$"


class Occurrence(BaseModel):
    """A single reference to an authority in the brief body, in any form.

    One :class:`Authority` aggregates every occurrence that resolves to it —
    the full citation, plus every short, ``supra``, ``id.``, and ``ibid.``
    reference. The ``paragraph_index`` / ``char_span`` pair is a
    layout-independent anchor that survives re-rendering; ``page`` is filled in
    once the converged render locates the occurrence.
    """

    model_config = ConfigDict(extra="forbid")

    form: OccurrenceForm
    """Citation form, as classified by eyecite resolution."""

    raw_text: str
    """Verbatim text of the occurrence as it appears in the brief."""

    paragraph_index: Annotated[int, Field(ge=0)]
    """Index of the paragraph in the ``.docx`` body where the occurrence appears."""

    char_span: tuple[Annotated[int, Field(ge=0)], Annotated[int, Field(ge=0)]]
    """Inclusive-exclusive character offsets ``[start, end)`` within the paragraph."""

    confidence: OccurrenceConfidence
    """``high`` = exact text-span match in the render; ``medium`` = approximated."""

    page: int | None = Field(default=None, ge=1)
    """Page in the converged render, or ``None`` before a render has located it."""

    pincite: str | None = None
    """Pinpoint reference (e.g. a page within the cited authority), when present."""


class Authority(BaseModel):
    """One resolved authority and every occurrence that refers to it.

    An authority is the unit a Table of Authorities lists: a case, statute,
    regulation, constitutional provision, rule, or secondary source, with the
    brief pages where it is cited. ``pages`` is the sorted, de-duplicated set of
    pages across all occurrences; ``passim`` is set when that count exceeds the
    active profile's threshold.
    """

    model_config = ConfigDict(extra="forbid")

    authority_id: str
    """Stable-within-a-run identifier, deterministically derived from the authority."""

    type: AuthorityType
    """The kind of authority; drives the TOA group via the profile's ``types`` map."""

    components: dict[str, Any]
    """Normalized parts (case: reporter/volume/page/court/year; statute: code/sec)."""

    display_full: str
    """Full citation form as rendered in the TOA."""

    sort_key: str
    """Within-group alphabetical ordering key."""

    group: GroupKey
    """TOA grouping bucket, per the active court profile."""

    occurrences: list[Occurrence]
    """Every reference to this authority, in every form."""

    pages: list[Annotated[int, Field(ge=1)]]
    """Sorted, de-duplicated brief pages where any occurrence lands."""

    passim: bool
    """True when the distinct-page count exceeds the profile's passim threshold."""

    display_short: str | None = None
    """Short citation form, when derivable."""


class FontSubstitution(BaseModel):
    """A single font pair the render engine substituted (original for substitute)."""

    model_config = ConfigDict(extra="forbid")

    original: str
    """The font the document declared."""

    substitute: str
    """The font the render engine used in its place."""


class RunMetadata(BaseModel):
    """Run-level provenance recorded on the registry, per spec §4.3.

    Carries the four version tracks (engine, rule pack, profile id + version),
    the render engine identity, the font-substitution report that drives TT-008,
    the iteration count and convergence flag that drive TT-007, and the input
    file hash. Together these make any generated TOA reproducible against the
    exact definitions and environment in force when it was produced.
    """

    model_config = ConfigDict(extra="forbid")

    engine_version: Annotated[str, Field(pattern=_SEMVER)]
    """Semantic version of the toatool engine."""

    rule_pack_version: Annotated[str, Field(pattern=_SEMVER)]
    """Semantic version of the ``toa`` rule pack."""

    profile_id: Annotated[str, Field(pattern=_PROFILE_ID)]
    """Identifier of the court profile in force (e.g. ``frap``)."""

    profile_version: Annotated[str, Field(pattern=_SEMVER)]
    """Semantic version of the court profile in force."""

    render_engine: str
    """Render engine identity (e.g. ``LibreOffice``)."""

    render_engine_version: str
    """Render engine version string (e.g. ``24.2``)."""

    font_substitution_occurred: bool
    """Whether the render substituted any font; gates TT-008."""

    iteration_count: Annotated[int, Field(ge=1)]
    """Number of convergence iterations the run took."""

    converged: bool
    """Whether pagination stabilized within the cap; ``False`` gates TT-007."""

    input_sha256: Annotated[str, Field(pattern=_SHA256)]
    """SHA-256 hex digest of the input ``.docx``, for provenance."""

    font_substitutions: list[FontSubstitution] = Field(default_factory=list)
    """The substitution pairs, when any occurred; empty otherwise."""


class CitationRegistry(BaseModel):
    """The complete Citation Registry for one run: authorities plus run metadata.

    Every output — the regenerated ``.docx`` TOA and the Markdown report — is a
    rendering of this object. The rules engine reads it (and the input-TOA diff
    baseline) to produce findings.
    """

    model_config = ConfigDict(extra="forbid")

    authorities: list[Authority]
    """Every resolved authority in the brief (may be empty for a brief with none)."""

    run_metadata: RunMetadata
    """Run-level provenance for the whole registry."""
