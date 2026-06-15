"""Tests for the docx parser and the body-text/offset builder."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from citetab.pipeline import extractor, parser

BRIEFS = Path(__file__).resolve().parent.parent.parent / "examples" / "briefs"


def test_parse_fixture_paragraphs_and_headings() -> None:
    """A real fixture parses into paragraphs with heading levels detected."""
    parsed = parser.parse(BRIEFS / "clean_appellate_brief.docx")
    assert len(parsed.paragraphs) > 0
    headings = [p for p in parsed.paragraphs if p.is_heading]
    assert any(
        p.text == "TABLE OF AUTHORITIES" and p.heading_level == 1 for p in headings
    )


def test_parse_missing_file_raises() -> None:
    """A non-existent path fails loudly."""
    with pytest.raises(parser.ParserError, match="does not exist"):
        parser.parse(Path("/no/such/file.docx"))


def test_parse_non_docx_raises(tmp_path: Path) -> None:
    """A file that is not a valid .docx fails loudly."""
    bad = tmp_path / "not.docx"
    bad.write_text("this is not a zip/docx", encoding="utf-8")
    with pytest.raises(parser.ParserError, match="not a readable .docx"):
        parser.parse(bad)


def test_build_body_excludes_region(make_parsed: Callable[..., Any]) -> None:
    """Excluded paragraphs (the TOA region) do not appear in the body text."""
    doc = make_parsed(
        [
            ("Intro text", "Normal"),
            ("TABLE OF AUTHORITIES", "Heading 1"),
            ("secret toa entry", "Normal"),
            ("Body cites 15 U.S.C. § 1692e here", "Normal"),
        ]
    )
    body = extractor.build_body(doc, excluded_indices={1, 2})
    assert "secret toa entry" not in body.text
    assert "Body cites" in body.text
    assert "Intro text" in body.text


def test_to_para_span_maps_back(make_parsed: Callable[..., Any]) -> None:
    """A global span maps back to the right paragraph and local offset."""
    doc = make_parsed([("alpha", "Normal"), ("beta gamma", "Normal")])
    body = extractor.build_body(doc, excluded_indices=set())
    # "gamma" starts at global index 5 (alpha) + 1 (\n) + 5 ("beta ") = 11
    index = body.text.index("gamma")
    para_index, (start, end) = body.to_para_span(index, index + 5)
    assert para_index == 1
    assert (start, end) == (5, 10)
