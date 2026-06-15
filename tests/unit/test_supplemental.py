"""Tests for the supplemental citation recognizer (the owned seam over eyecite)."""

from __future__ import annotations

from citetab.pipeline import supplemental


def _by_identity(text: str) -> dict[str, supplemental.SupplementalCitation]:
    return {c.identity: c for c in supplemental.recognize(text)}


def test_recognizes_subsection_letter_statute() -> None:
    """15 U.S.C. § 1692e (which eyecite misses) is recognized as a statute."""
    found = _by_identity("a claim under 15 U.S.C. § 1692e, and more")
    cite = found["statute:usc:15:1692e"]
    assert cite.type == "statute"
    assert cite.display_full == "15 U.S.C. § 1692e"
    assert cite.matched_text == "15 U.S.C. § 1692e"


def test_recognizes_plain_and_dotted_sections() -> None:
    """Plain (1331) and dotted (1006.14) sections are recognized too."""
    found = _by_identity("28 U.S.C. § 1331 and 12 C.F.R. § 1006.14")
    assert found["statute:usc:28:1331"].display_full == "28 U.S.C. § 1331"
    reg = found["regulation:cfr:12:1006.14"]
    assert reg.type == "regulation"
    assert reg.display_full == "12 C.F.R. § 1006.14"


def test_does_not_capture_trailing_period() -> None:
    """A trailing sentence period is not part of the section."""
    cite = supplemental.recognize("ends at 15 U.S.C. § 1692e.")[0]
    assert cite.display_full == "15 U.S.C. § 1692e"
    assert cite.matched_text.endswith("1692e")


def test_recognizes_court_rule() -> None:
    """Court rules, which eyecite does not model, are recognized."""
    found = _by_identity("see Fed. R. App. P. 28, which presumes")
    cite = found["rule:fedrappp:28"]
    assert cite.type == "rule"
    assert cite.display_full == "Fed. R. App. P. 28"
    assert cite.sort_key == "fedrappp 28"


def test_recognizes_civil_rule_with_subsection() -> None:
    """Civil-rule numbers with dotted/parenthesized parts are recognized."""
    cite = supplemental.recognize("under Fed. R. Civ. P. 12(b)(6) dismissal")[0]
    assert cite.type == "rule"
    assert cite.display_full == "Fed. R. Civ. P. 12(b)(6)"


def test_candidates_sorted_by_position() -> None:
    """Recognized candidates come back in order of appearance."""
    cites = supplemental.recognize("Fed. R. App. P. 28 then 15 U.S.C. § 1692e")
    assert [c.type for c in cites] == ["rule", "statute"]
    assert cites[0].span[0] < cites[1].span[0]


def test_span_matches_text() -> None:
    """The reported span indexes the matched text in the source."""
    text = "xx 28 U.S.C. § 1291 yy"
    cite = supplemental.recognize(text)[0]
    start, end = cite.span
    assert text[start:end] == cite.matched_text


def test_no_false_positive_on_prose() -> None:
    """Plain prose with no citations yields nothing."""
    assert supplemental.recognize("The court considered the statute carefully.") == []
