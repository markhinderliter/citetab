"""Report rendering: determinism, citation completeness, and per-rule sections.

Covers the four things the report must get right that earlier hand-written
examples got wrong or could not show: byte-stability after masking the
documented non-deterministic fields, TT-001 emitting *all* card citations, TT-008
disclosing the real substituted pair, and the run-level rule sections (TT-005
suppression, TT-006 conflict, TT-007 non-convergence).
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from citetab.engine.profile_loader import CourtProfile, load_profile_by_id
from citetab.engine.runner import run_rules
from citetab.pipeline import convergence, locator, renderer
from citetab.pipeline.working import WorkingOccurrence
from citetab.report import mask_report, render_report

BRIEFS = Path(__file__).resolve().parent.parent.parent / "examples" / "briefs"

_NEEDS_RENDER = pytest.mark.skipif(
    shutil.which("libreoffice") is None and shutil.which("soffice") is None,
    reason="LibreOffice is required to render; not installed",
)


@pytest.fixture(scope="module")
def frap() -> CourtProfile:
    """The FRAP court profile."""
    return load_profile_by_id("frap")


def _render(path: Path, profile: CourtProfile, *, generated_at: str) -> str:
    """Generate, evaluate, and render a brief's report."""
    gen = convergence.generate(path, profile)
    rules = run_rules(gen, input_path=path, profile=profile)
    clause = (
        "SUPPRESSED — no placement found"
        if rules.docx_suppressed
        else f"written {path.stem}.toa.docx"
    )
    return render_report(
        gen,
        rules,
        input_name=path.name,
        profile=profile,
        output_clause=clause,
        generated_at=generated_at,
    )


@_NEEDS_RENDER
def test_report_byte_stable_after_masking(frap: CourtProfile) -> None:
    """Two reports differing only in the masked fields are equal after masking."""
    path = BRIEFS / "dirty_motion_brief.docx"
    gen = convergence.generate(path, frap)
    rules = run_rules(gen, input_path=path, profile=frap)
    kwargs = {"input_name": path.name, "profile": frap, "output_clause": "written x"}
    first = render_report(gen, rules, generated_at="2026-01-01T00:00:00Z", **kwargs)
    second = render_report(gen, rules, generated_at="2099-12-31T23:59:59Z", **kwargs)
    assert first != second  # the generated: line differs
    assert mask_report(first) == mask_report(second)


@_NEEDS_RENDER
def test_tt001_authority_line_lists_all_card_citations(frap: CourtProfile) -> None:
    """TT-001's authority line emits both card citations (FRAP and Bluebook)."""
    report = _render(
        BRIEFS / "dirty_motion_brief.docx", frap, generated_at="2026-06-09T12:00:00Z"
    )
    line = next(
        ln
        for ln in report.splitlines()
        if ln.startswith("- authority:") and "Rule 10.9" in ln
    )
    assert "FRAP 28(a)(2)" in line
    assert "The Bluebook Rule 10.9" in line
    assert "rules/toa/TT-001" in line


@_NEEDS_RENDER
@pytest.mark.calibrated
def test_tt008_discloses_real_substitution_pair(frap: CourtProfile) -> None:
    """TT-008 names the real Consolas→DejaVu pair, not the old Times→Liberation."""
    report = _render(
        BRIEFS / "clean_appellate_brief.docx", frap, generated_at="2026-06-09T12:00:00Z"
    )
    assert "Consolas → DejaVu Sans Mono" in report
    assert "Times New Roman" not in report
    assert "Liberation Serif" not in report


@_NEEDS_RENDER
@pytest.mark.calibrated
def test_no_findings_and_fonts_ok_without_substitution(
    frap: CourtProfile, monkeypatch: pytest.MonkeyPatch
) -> None:
    """With substitution off, the finding-free clean brief renders no findings."""
    monkeypatch.setattr(renderer, "detect_font_substitutions", lambda _path: [])
    report = _render(
        BRIEFS / "clean_appellate_brief.docx", frap, generated_at="2026-06-09T12:00:00Z"
    )
    assert "fonts ok" in report
    assert "No findings." in report


@_NEEDS_RENDER
def test_tt005_report_suppressed_and_placement_none(
    frap: CourtProfile, memo_no_marker: Path
) -> None:
    """The no-placement report leads with the TOA, shows SUPPRESSED, renders TT-005."""
    report = _render(memo_no_marker, frap, generated_at="2026-06-09T12:00:00Z")
    assert "- output: SUPPRESSED" in report
    assert "none found" in report
    assert "## Table of Authorities" in report  # the table is still present
    assert "### TT-005 · TOA placement not found — error (high)" in report


@_NEEDS_RENDER
def test_tt006_report_renders_conflict(
    frap: CourtProfile, dirty_plus_marker: Path
) -> None:
    """The marker-wins report renders a TT-006 warning section."""
    report = _render(dirty_plus_marker, frap, generated_at="2026-06-09T12:00:00Z")
    assert "### TT-006 · Marker and heading both present — warning (high)" in report
    assert "[[TOA]] marker, consumed" in report  # placement line


@_NEEDS_RENDER
def test_tt004_report_renders_entry_evidence(
    frap: CourtProfile, dirty_plus_phantom: Path
) -> None:
    """TT-004 renders the phantom input-TOA entry verbatim with its listed pages."""
    report = _render(dirty_plus_phantom, frap, generated_at="2026-06-09T12:00:00Z")
    assert "### TT-004 · Phantom input-TOA entry — warning (medium)" in report
    assert '- evidence: "Nonexistent v. Authority, 999 F.9d 999   5"' in report
    assert "(listed pages 5)" in report


def test_tt007_report_renders_non_convergence(
    frap: CourtProfile, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A mocked oscillation renders DID NOT CONVERGE and a TT-007 section."""
    calls = {"n": 0}

    def fake_render(docx_path: Path, out_dir: Path) -> Path:
        return out_dir / f"{docx_path.stem}.pdf"

    def fake_locate(
        pdf_path: Path, occurrences: list[WorkingOccurrence], anchor: str | None
    ) -> None:
        calls["n"] += 1
        page = 2 if calls["n"] % 2 else 3
        for occ in occurrences:
            occ.page = page if "512 F.3d" in occ.raw_text else 5
            occ.confidence = "high"

    monkeypatch.setattr(renderer, "render_to_pdf", fake_render)
    monkeypatch.setattr(locator, "locate_occurrences", fake_locate)
    monkeypatch.setattr(renderer, "detect_font_substitutions", lambda _p: [])
    monkeypatch.setattr(renderer, "render_engine_info", lambda: ("LibreOffice", "24.2"))

    report = _render(
        BRIEFS / "marker_trial_memo.docx", frap, generated_at="2026-06-09T12:00:00Z"
    )
    assert "DID NOT CONVERGE (cap 5 reached)" in report
    assert "### TT-007 · Pagination non-convergence — error (high)" in report
    assert "unstable:" in report
