"""Tests for TOA placement detection (spec §2.4 precedence)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from toatool.pipeline import placement

VARIANTS = ["Table of Authorities", "Table of Cited Authorities"]


def test_heading_detection_and_region(make_parsed: Callable[..., Any]) -> None:
    """A heading match keeps the heading and bounds the region at the next heading."""
    doc = make_parsed(
        [
            ("CAPTION", "Title"),
            ("TABLE OF AUTHORITIES", "Heading 1"),
            ("Cases", "Normal"),
            ("Carmody, 1 F.3d 1  2", "Normal"),
            ("ARGUMENT", "Heading 1"),
            ("body", "Normal"),
        ]
    )
    result = placement.detect_placement(doc, VARIANTS)
    assert result.mechanism == "heading"
    assert result.heading_match is not None
    assert result.heading_match.heading_index == 1
    assert result.heading_match.region_start == 2
    assert result.heading_match.region_end == 4  # the next Heading 1 ("ARGUMENT")


def test_region_ends_at_higher_level_heading(make_parsed: Callable[..., Any]) -> None:
    """A subheading inside the region does not end it; a same-level heading does."""
    doc = make_parsed(
        [
            ("TABLE OF AUTHORITIES", "Heading 1"),
            ("Cases", "Heading 2"),
            ("entry", "Normal"),
            ("CONCLUSION", "Heading 1"),
        ]
    )
    result = placement.detect_placement(doc, VARIANTS)
    assert result.heading_match is not None
    assert result.heading_match.region_end == 3


def test_heading_case_and_whitespace_tolerant(make_parsed: Callable[..., Any]) -> None:
    """Heading matching ignores case and collapses whitespace."""
    doc = make_parsed([("  table   of   authorities ", "Heading 1"), ("x", "Normal")])
    assert placement.detect_placement(doc, VARIANTS).mechanism == "heading"


def test_marker_detection(make_parsed: Callable[..., Any]) -> None:
    """A lone [[TOA]] marker is detected as the marker mechanism."""
    doc = make_parsed(
        [("CAPTION", "Title"), ("[[TOA]]", "Normal"), ("INTRO", "Heading 1")]
    )
    result = placement.detect_placement(doc, VARIANTS)
    assert result.mechanism == "marker"
    assert result.marker_index == 1


def test_marker_with_other_text_does_not_match(make_parsed: Callable[..., Any]) -> None:
    """A paragraph containing the marker plus other text is not a marker."""
    doc = make_parsed([("see [[TOA]] here", "Normal")])
    assert placement.detect_placement(doc, VARIANTS).mechanism == "none"


def test_marker_wins_over_heading_but_records_both(
    make_parsed: Callable[..., Any],
) -> None:
    """With both present, marker wins and the heading match is recorded (TT-006)."""
    doc = make_parsed(
        [
            ("[[TOA]]", "Normal"),
            ("TABLE OF AUTHORITIES", "Heading 1"),
            ("old entry", "Normal"),
            ("ARGUMENT", "Heading 1"),
        ]
    )
    result = placement.detect_placement(doc, VARIANTS)
    assert result.mechanism == "marker"
    assert result.marker_matched is True
    assert result.heading_matched is True
    assert result.heading_match is not None


def test_multiple_markers_recorded(make_parsed: Callable[..., Any]) -> None:
    """Extra markers beyond the first are recorded for later reporting."""
    doc = make_parsed([("[[TOA]]", "Normal"), ("[[TOA]]", "Normal")])
    result = placement.detect_placement(doc, VARIANTS)
    assert result.marker_index == 0
    assert result.extra_marker_indices == (1,)


def test_flag_wins_over_marker_and_heading(make_parsed: Callable[..., Any]) -> None:
    """An explicit --toa-heading override takes precedence over marker and heading."""
    doc = make_parsed(
        [
            ("[[TOA]]", "Normal"),
            ("TABLE OF AUTHORITIES", "Heading 1"),
            ("AUTHORITIES CITED", "Heading 1"),
            ("entry", "Normal"),
            ("ARGUMENT", "Heading 1"),
        ]
    )
    result = placement.detect_placement(doc, VARIANTS, toa_heading="Authorities Cited")
    assert result.mechanism == "flag"
    assert result.flag_used is True
    assert result.heading_match is not None
    assert result.heading_match.heading_index == 2


def test_none_when_nothing_matches(make_parsed: Callable[..., Any]) -> None:
    """No heading, no marker → the refuse-to-guess result (TT-005 path)."""
    doc = make_parsed([("CAPTION", "Title"), ("ARGUMENT", "Heading 1")])
    result = placement.detect_placement(doc, VARIANTS)
    assert result.mechanism == "none"
    assert result.searched_variants == tuple(VARIANTS)
