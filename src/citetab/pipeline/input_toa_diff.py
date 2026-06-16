"""Parse the input document's existing TOA into a diff baseline (FR-05).

Before the heading-detected TOA region is replaced, its entries are parsed
best-effort into ``(authority, pages)`` pairs and matched to registry authorities
by **resolved identity**, never string equality. This baseline is what TT-002
(missing entry), TT-003 (stale pages), and TT-004 (phantom entry) compare against
in the rules phase.

On the marker-bootstrap path (and when no heading region exists) there is no
baseline: those rules skip, and skipped ≠ passed. Group-label lines (``Cases``,
``Statutes``, …) are structural and are not treated as entries. An entry line
whose authority cannot be identified, or whose page list cannot be read, is
recorded as ``parsed = False`` and handled conservatively by TT-004.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from citetab.engine.profile_loader import CourtProfile
from citetab.pipeline.parser import ParsedDocument
from citetab.pipeline.placement import PlacementResult
from citetab.pipeline.resolver import identify_entry

# Authority text, then whitespace, then a trailing page list ("2, 3, 5") or the
# passim token. The text group is non-greedy and the page token is anchored to
# end-of-line, so the split lands at the last whitespace before the page list
# even when the separator is a single space ("12 C.F.R. 1006.14 3, 6").
_ENTRY_RE = re.compile(
    r"^(?P<text>.*?\S)\s+(?P<pages>\d+(?:\s*,\s*\d+)*|passim)\s*$",
    re.IGNORECASE,
)

_COMMON_GROUP_LABELS = {
    "cases",
    "statutes",
    "regulations",
    "rules",
    "constitutional provisions",
    "other authorities",
}


@dataclass(frozen=True)
class BaselineEntry:
    """One parsed (or unparsed) entry from the input document's TOA."""

    verbatim_text: str
    input_pages: list[int] = field(default_factory=list)
    is_passim: bool = False
    parsed: bool = True
    authority_id: str | None = None


@dataclass(frozen=True)
class DiffBaseline:
    """The input-TOA baseline: its entries, or ``available=False`` when none."""

    entries: tuple[BaselineEntry, ...]
    available: bool


def _group_labels(profile: CourtProfile) -> set[str]:
    """Return the set of normalized strings that count as group labels."""
    labels = {group.label.casefold() for group in profile.groups}
    return labels | _COMMON_GROUP_LABELS


def _parse_pages(raw: str) -> tuple[list[int], bool]:
    """Parse a page token into ``(pages, is_passim)``."""
    if raw.strip().casefold() == "passim":
        return [], True
    pages = sorted({int(part) for part in raw.split(",") if part.strip()})
    return pages, False


def _parse_line(line: str, labels: set[str]) -> BaselineEntry | None:
    """Parse one TOA line into a baseline entry, or None if it is a group label."""
    stripped = line.strip()
    if not stripped:
        return None
    if stripped.casefold() in labels:
        return None

    match = _ENTRY_RE.match(stripped)
    if match is None:
        return BaselineEntry(verbatim_text=stripped, parsed=False)

    text = match.group("text").strip()
    pages, is_passim = _parse_pages(match.group("pages"))
    return BaselineEntry(
        verbatim_text=stripped,
        input_pages=pages,
        is_passim=is_passim,
        parsed=True,
        authority_id=identify_entry(text),
    )


def build_baseline(
    parsed: ParsedDocument, placement: PlacementResult, profile: CourtProfile
) -> DiffBaseline:
    """Parse the input TOA region into a diff baseline.

    Args:
        parsed: The parsed document.
        placement: The placement result (the baseline exists only on the
            heading/flag path with a matched region).
        profile: The active court profile (for group-label recognition).

    Returns:
        A :class:`DiffBaseline`. ``available`` is ``False`` on the marker or
        no-placement paths, where the diff rules skip.
    """
    if (
        placement.mechanism not in ("heading", "flag")
        or placement.heading_match is None
    ):
        return DiffBaseline(entries=(), available=False)

    match = placement.heading_match
    labels = _group_labels(profile)
    entries: list[BaselineEntry] = []
    for para in parsed.paragraphs[match.region_start : match.region_end]:
        for line in para.text.splitlines():
            entry = _parse_line(line, labels)
            if entry is not None:
                entries.append(entry)
    return DiffBaseline(entries=tuple(entries), available=True)
