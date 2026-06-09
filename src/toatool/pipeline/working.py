"""Mutable working structures used while the pipeline runs.

These are deliberately *not* the canonical :mod:`toatool.models.registry`
models. The convergence loop accumulates page assignments here, mutating
:class:`WorkingOccurrence.page` across iterations; only once the loop settles is
a single immutable :class:`~toatool.models.registry.CitationRegistry` frozen from
them (see :func:`toatool.pipeline.convergence.freeze_registry`). Keeping the
mutable accumulation separate from the canonical object is a hard rule of this
build: the registry is never mutated mid-loop.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from toatool.models.registry import AuthorityType, GroupKey, OccurrenceForm


@dataclass
class WorkingOccurrence:
    """A located (or not-yet-located) reference to an authority in the body."""

    form: OccurrenceForm
    raw_text: str
    paragraph_index: int
    char_span: tuple[int, int]
    pincite: str | None = None
    page: int | None = None
    confidence: str = "high"


@dataclass
class WorkingAuthority:
    """An authority and its occurrences, accumulated before the registry freeze."""

    authority_id: str
    type: AuthorityType
    components: dict[str, object]
    display_full: str
    sort_key: str
    group: GroupKey
    occurrences: list[WorkingOccurrence] = field(default_factory=list)
    display_short: str | None = None

    def pages(self) -> list[int]:
        """Return the sorted, de-duplicated pages across located occurrences."""
        seen = {occ.page for occ in self.occurrences if occ.page is not None}
        return sorted(seen)
