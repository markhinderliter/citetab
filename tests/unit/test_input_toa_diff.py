"""Tests for input-TOA diff baseline parsing (FR-05)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from citetab.engine.profile_loader import load_profile_by_id
from citetab.pipeline import input_toa_diff, placement

VARIANTS = ["Table of Authorities", "Table of Cited Authorities"]
_CARMODY = "Carmody v. Westfall Transit Auth., 512 F.3d 1042 (9th Cir. 2018)"


def _baseline(make_parsed: Callable[..., Any], region_lines: list[tuple[str, str]]):
    profile = load_profile_by_id("frap")
    doc = make_parsed(
        [
            ("TABLE OF AUTHORITIES", "Heading 1"),
            *region_lines,
            ("ARGUMENT", "Heading 1"),
        ]
    )
    place = placement.detect_placement(doc, VARIANTS)
    return input_toa_diff.build_baseline(doc, place, profile)


def test_parses_entries_and_identities(make_parsed: Callable[..., Any]) -> None:
    """Entries parse into pages and resolve to authority identities."""
    baseline = _baseline(
        make_parsed,
        [
            ("Cases", "Normal"),
            (f"{_CARMODY}  2, 3", "Normal"),
            ("Statutes", "Normal"),
            ("15 U.S.C. § 1692e   1, 4", "Normal"),
        ],
    )
    assert baseline.available is True
    by_id = {e.authority_id: e for e in baseline.entries}
    assert by_id["case:f3d:512:1042"].input_pages == [2, 3]
    assert by_id["statute:usc:15:1692e"].input_pages == [1, 4]


def test_single_space_separator(make_parsed: Callable[..., Any]) -> None:
    """A single-space separator before the page list still parses."""
    baseline = _baseline(make_parsed, [("12 C.F.R. § 1006.14 3, 6", "Normal")])
    entry = baseline.entries[0]
    assert entry.parsed is True
    assert entry.input_pages == [3, 6]
    assert entry.authority_id == "regulation:cfr:12:1006.14"


def test_passim_entry(make_parsed: Callable[..., Any]) -> None:
    """A passim entry is recorded as passim with no page list."""
    baseline = _baseline(
        make_parsed,
        [(f"{_CARMODY}  passim", "Normal")],
    )
    entry = baseline.entries[0]
    assert entry.is_passim is True
    assert entry.input_pages == []


def test_group_labels_skipped(make_parsed: Callable[..., Any]) -> None:
    """Group-label lines are structural, not entries."""
    baseline = _baseline(
        make_parsed,
        [
            ("Cases", "Normal"),
            ("Statutes", "Normal"),
            ("15 U.S.C. § 1692e  1", "Normal"),
        ],
    )
    assert len(baseline.entries) == 1


def test_unparseable_line_recorded(make_parsed: Callable[..., Any]) -> None:
    """A line with no trailing page list is recorded as unparsed."""
    baseline = _baseline(make_parsed, [("Some stray prose with no pages", "Normal")])
    entry = baseline.entries[0]
    assert entry.parsed is False
    assert entry.authority_id is None


def test_marker_path_has_no_baseline(make_parsed: Callable[..., Any]) -> None:
    """On the marker bootstrap path the baseline is unavailable (diff rules skip)."""
    profile = load_profile_by_id("frap")
    doc = make_parsed([("[[TOA]]", "Normal"), ("INTRO", "Heading 1")])
    place = placement.detect_placement(doc, VARIANTS)
    baseline = input_toa_diff.build_baseline(doc, place, profile)
    assert baseline.available is False
    assert baseline.entries == ()
