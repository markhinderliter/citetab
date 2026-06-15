"""TOA placement detection with strict precedence (spec §2.4, FR-02).

First match wins: (1) an explicit ``--toa-heading`` override, (2) a ``[[TOA]]``
marker alone on its paragraph, (3) a default heading variant from the court
profile, (4) nothing — in which case the tool refuses to guess (the TT-005 path).

This module only *detects*; it records every mechanism that matched (not just
the winner) so the rules engine can later emit TT-005 (nothing found) and TT-006
(marker and heading both present). Insertion happens in
:mod:`citetab.pipeline.inserter`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

from citetab.pipeline.parser import ParsedDocument

MARKER_TEXT = "[[TOA]]"

PlacementMechanism = Literal["flag", "marker", "heading", "none"]


def _normalize(text: str) -> str:
    """Normalize a heading for case-insensitive, whitespace-tolerant matching."""
    return re.sub(r"\s+", " ", text).strip().casefold()


@dataclass(frozen=True)
class HeadingMatch:
    """A heading paragraph that matched a placement heading variant."""

    heading_index: int
    """Index of the matched heading paragraph (kept; entries below are replaced)."""

    matched_text: str
    """The heading's verbatim text."""

    region_start: int
    """First paragraph index below the heading that is part of the TOA region."""

    region_end: int
    """Exclusive end of the TOA region (the next same-or-higher heading, or EOF)."""


@dataclass(frozen=True)
class PlacementResult:
    """The outcome of the placement precedence walk.

    ``mechanism`` is the winner. The other fields record every match so the
    rules engine can report conflicts (TT-006) or the absence of any placement
    (TT-005). For the marker path ``marker_index`` is the paragraph to replace;
    for the heading/flag path ``heading_match`` gives the kept heading and the
    region of entries to replace.
    """

    mechanism: PlacementMechanism
    heading_match: HeadingMatch | None = None
    marker_index: int | None = None
    extra_marker_indices: tuple[int, ...] = field(default_factory=tuple)
    marker_matched: bool = False
    heading_matched: bool = False
    flag_used: bool = False
    searched_variants: tuple[str, ...] = field(default_factory=tuple)


def _find_markers(doc: ParsedDocument) -> list[int]:
    """Return indices of paragraphs that are exactly the ``[[TOA]]`` marker."""
    return [p.index for p in doc.paragraphs if p.text.strip() == MARKER_TEXT]


def _find_heading(doc: ParsedDocument, variants: list[str]) -> HeadingMatch | None:
    """Find the first heading paragraph whose text matches one of ``variants``.

    The TOA region runs from the paragraph after the heading up to (exclusive)
    the next heading of the same or higher level, or end of document.
    """
    wanted = {_normalize(v) for v in variants}
    for para in doc.paragraphs:
        if not para.is_heading or _normalize(para.text) not in wanted:
            continue
        level = para.heading_level
        assert level is not None  # is_heading guarantees this
        region_end = len(doc.paragraphs)
        for later in doc.paragraphs[para.index + 1 :]:
            if later.heading_level is not None and later.heading_level <= level:
                region_end = later.index
                break
        return HeadingMatch(
            heading_index=para.index,
            matched_text=para.text,
            region_start=para.index + 1,
            region_end=region_end,
        )
    return None


def detect_placement(
    doc: ParsedDocument,
    detection_variants: list[str],
    toa_heading: str | None = None,
) -> PlacementResult:
    """Walk the placement precedence and return the result (spec §2.4).

    Args:
        doc: The parsed document.
        detection_variants: The court profile's default heading variants.
        toa_heading: An explicit ``--toa-heading`` override, if provided.

    Returns:
        A :class:`PlacementResult` whose ``mechanism`` is the winner, with every
        matched mechanism recorded for later conflict/absence reporting.
    """
    markers = _find_markers(doc)
    marker_index = markers[0] if markers else None
    extra_markers = tuple(markers[1:])
    marker_matched = marker_index is not None

    flag_match = _find_heading(doc, [toa_heading]) if toa_heading is not None else None
    variant_match = _find_heading(doc, detection_variants)
    heading_matched = variant_match is not None

    # Precedence: flag → marker → heading → none.
    if flag_match is not None:
        return PlacementResult(
            mechanism="flag",
            heading_match=flag_match,
            marker_index=marker_index,
            extra_marker_indices=extra_markers,
            marker_matched=marker_matched,
            heading_matched=heading_matched,
            flag_used=True,
            searched_variants=tuple(detection_variants),
        )
    if marker_matched:
        return PlacementResult(
            mechanism="marker",
            heading_match=variant_match,
            marker_index=marker_index,
            extra_marker_indices=extra_markers,
            marker_matched=True,
            heading_matched=heading_matched,
            searched_variants=tuple(detection_variants),
        )
    if variant_match is not None:
        return PlacementResult(
            mechanism="heading",
            heading_match=variant_match,
            heading_matched=True,
            searched_variants=tuple(detection_variants),
        )
    return PlacementResult(
        mechanism="none",
        searched_variants=tuple(detection_variants),
    )
