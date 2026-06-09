"""Tests for the renderer's font detection / LO discovery, and court abbreviations."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from toatool.pipeline import courts, renderer

BRIEFS = Path(__file__).resolve().parent.parent.parent / "examples" / "briefs"

_HAS_LO = shutil.which("libreoffice") is not None or shutil.which("soffice") is not None


def test_court_abbreviation_circuit() -> None:
    """A circuit court id resolves to its Bluebook string."""
    assert courts.court_abbreviation("ca9", "F.3d") == "9th Cir."
    assert courts.court_abbreviation("ca2", "F.2d") == "2d Cir."


def test_court_abbreviation_scotus_omitted() -> None:
    """SCOTUS and the U.S. reporter omit the court parenthetical."""
    assert courts.court_abbreviation("scotus", "U.S.") is None
    assert courts.court_abbreviation("ca9", "U.S.") is None


def test_court_abbreviation_unknown() -> None:
    """An unknown or missing court id returns None."""
    assert courts.court_abbreviation(None, "F.3d") is None
    assert courts.court_abbreviation("not_a_real_court_id", "F.3d") is None


def test_referenced_fonts_on_fixture() -> None:
    """The font scanner finds declared fonts in a real fixture."""
    fonts = renderer._referenced_fonts(BRIEFS / "clean_appellate_brief.docx")
    assert isinstance(fonts, set)
    assert fonts  # at least one font is declared


def test_detect_font_substitutions_returns_list() -> None:
    """Font-substitution detection returns a (possibly empty) list of pairs."""
    subs = renderer.detect_font_substitutions(BRIEFS / "clean_appellate_brief.docx")
    assert isinstance(subs, list)
    for sub in subs:
        assert sub.original and sub.substitute


def test_find_libreoffice_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    """When LibreOffice is absent, discovery fails with an actionable message."""
    monkeypatch.setattr(renderer.shutil, "which", lambda _name: None)
    with pytest.raises(renderer.RenderError, match="LibreOffice was not found"):
        renderer.find_libreoffice()


@pytest.mark.skipif(not _HAS_LO, reason="LibreOffice required")
def test_render_engine_info() -> None:
    """The engine identity and a version string are reported."""
    name, version = renderer.render_engine_info()
    assert name == "LibreOffice"
    assert version


@pytest.mark.skipif(not _HAS_LO, reason="LibreOffice required")
def test_render_to_pdf_produces_pdf(tmp_path: Path) -> None:
    """Rendering a fixture produces a PDF file."""
    pdf = renderer.render_to_pdf(BRIEFS / "marker_trial_memo.docx", tmp_path)
    assert pdf.is_file()
    assert pdf.suffix == ".pdf"
