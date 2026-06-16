"""Integration tests: run the full generation pipeline on the three briefs.

These render with LibreOffice, so they are skipped when it is unavailable. They
verify the spec §3.2 behavior the Phase 2 gate calls for: every brief converges,
the clean brief converges on the first check with Carmody as a page list (not
passim), the dirty brief adds Okafor and surfaces the Ellison orphan, and the
marker memo bootstraps placement and hands off to the heading path on re-run.

Exact page numbers are environment-dependent (font metrics), so the assertions
check structural properties, not specific page values.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from citetab.engine.profile_loader import CourtProfile, load_profile_by_id
from citetab.pipeline import convergence, parser, placement, toa_builder
from citetab.pipeline.input_toa_diff import build_baseline

BRIEFS = Path(__file__).resolve().parent.parent.parent / "examples" / "briefs"

pytestmark = pytest.mark.skipif(
    shutil.which("libreoffice") is None and shutil.which("soffice") is None,
    reason="LibreOffice is required to render; not installed",
)


@pytest.fixture(scope="module")
def frap() -> CourtProfile:
    """The FRAP court profile."""
    return load_profile_by_id("frap")


@pytest.fixture(scope="module")
def clean(frap: CourtProfile) -> convergence.GenerationResult:
    """Generation result for the clean appellate brief."""
    return convergence.generate(BRIEFS / "clean_appellate_brief.docx", frap)


@pytest.fixture(scope="module")
def dirty(frap: CourtProfile) -> convergence.GenerationResult:
    """Generation result for the dirty motion brief."""
    return convergence.generate(BRIEFS / "dirty_motion_brief.docx", frap)


@pytest.fixture(scope="module")
def memo(frap: CourtProfile) -> convergence.GenerationResult:
    """Generation result for the marker trial memo."""
    return convergence.generate(BRIEFS / "marker_trial_memo.docx", frap)


def _authority_ids(result: convergence.GenerationResult) -> set[str]:
    return {auth.authority_id for auth in result.authorities}


def _all_occurrence_pages_set(result: convergence.GenerationResult) -> bool:
    return all(
        occ.page is not None
        for auth in result.registry.authorities
        for occ in auth.occurrences
    )


@pytest.mark.calibrated
def test_clean_converges_on_first_check(clean: convergence.GenerationResult) -> None:
    """The clean brief converges, in a single iteration."""
    assert clean.converged is True
    assert clean.iteration_count == 1


def test_clean_placement_is_heading(clean: convergence.GenerationResult) -> None:
    """The clean brief's TOA is detected via its heading."""
    assert clean.placement.mechanism == "heading"


@pytest.mark.calibrated
def test_clean_carmody_is_page_list_not_passim(
    clean: convergence.GenerationResult, frap: CourtProfile
) -> None:
    """Carmody renders as a page list (≤5 pages), never passim, in the clean brief."""
    carmody = next(
        a for a in clean.authorities if a.authority_id == "case:f3d:512:1042"
    )
    assert toa_builder.is_passim(carmody, frap) is False
    assert len(carmody.pages()) <= frap.passim.threshold_pages
    assert toa_builder.page_text(carmody, frap) != frap.passim.render_text


def test_clean_includes_jurisdiction_statutes_and_rule(
    clean: convergence.GenerationResult,
) -> None:
    """The faithful clean TOA lists the jurisdiction statutes and the rule."""
    ids = _authority_ids(clean)
    assert "statute:usc:28:1331" in ids
    assert "statute:usc:28:1291" in ids
    assert "statute:usc:15:1692e" in ids
    assert "rule:fedrappp:28" in ids


@pytest.mark.calibrated
def test_clean_registry_pages_all_present(clean: convergence.GenerationResult) -> None:
    """The frozen registry has a measured page for every occurrence."""
    assert _all_occurrence_pages_set(clean) is True


@pytest.mark.calibrated
def test_clean_input_toa_matches_registry(
    clean: convergence.GenerationResult, frap: CourtProfile
) -> None:
    """Clean's reconciled input TOA diffs clean against the measured registry.

    Diff-level finding-free: every measured authority has exactly one input-TOA
    entry, matched by resolved identity, carrying the measured page list — no
    missing entry (TT-002), stale page (TT-003), or phantom entry (TT-004). The
    rules engine re-checks this in Phase 3; this guards the reconciled fixture in
    the meantime (see scripts/reconcile_fixtures.py).
    """
    parsed = parser.parse(BRIEFS / "clean_appellate_brief.docx")
    place = placement.detect_placement(parsed, frap.heading.detection_variants)
    baseline = build_baseline(parsed, place, frap)
    assert baseline.available is True

    registry = {a.authority_id: a for a in clean.registry.authorities}
    seen: set[str] = set()
    for entry in baseline.entries:
        assert entry.parsed is True
        assert entry.authority_id in registry  # no phantom (TT-004)
        authority = registry[str(entry.authority_id)]
        if authority.passim:
            assert entry.is_passim is True
        else:
            assert entry.input_pages == list(authority.pages)  # no stale (TT-003)
        seen.add(str(entry.authority_id))
    assert seen == set(registry)  # no missing entry (TT-002)


def test_dirty_adds_okafor(dirty: convergence.GenerationResult) -> None:
    """The dirty brief resolves Okafor from the body."""
    assert "case:f3d:891:655" in _authority_ids(dirty)


def test_dirty_ellison_is_orphan(dirty: convergence.GenerationResult) -> None:
    """Ellison is an unresolved orphan (no full citation), excluded from the TOA."""
    assert "case:f3d:891:655" in _authority_ids(dirty)
    orphan_texts = " ".join(o.raw_text for o in dirty.unresolved)
    assert "740 F.3d" in orphan_texts
    assert not any("740" in a.authority_id for a in dirty.authorities)


def test_dirty_converges(dirty: convergence.GenerationResult) -> None:
    """The dirty brief converges within the cap."""
    assert dirty.converged is True
    assert 1 <= dirty.iteration_count <= convergence.ITERATION_CAP


def test_dirty_has_statute_via_recognizer(dirty: convergence.GenerationResult) -> None:
    """15 U.S.C. § 1692e (which eyecite misses) is recovered by the recognizer."""
    assert "statute:usc:15:1692e" in _authority_ids(dirty)


@pytest.mark.calibrated
def test_dirty_carmody_renders_passim(
    dirty: convergence.GenerationResult, frap: CourtProfile
) -> None:
    """Carmody spans a sixth physical page here, so it renders passim (D4).

    The end-to-end counterpart to the env-independent boundary unit test: a real
    fixture render exercises the passim path, not just is_passim() in isolation.
    """
    carmody = next(
        a for a in dirty.authorities if a.authority_id == "case:f3d:512:1042"
    )
    assert len(carmody.pages()) > frap.passim.threshold_pages
    assert toa_builder.is_passim(carmody, frap) is True
    assert toa_builder.page_text(carmody, frap) == frap.passim.render_text


@pytest.mark.calibrated
def test_dirty_delgado_is_page_list(
    dirty: convergence.GenerationResult, frap: CourtProfile
) -> None:
    """Delgado stays at the threshold and renders a page list, not passim (D5).

    The D4-vs-D5 boundary: Carmody (passim) and Delgado (page list) in the same
    rendered brief, so the threshold is proven end-to-end, not only in a unit.
    """
    delgado = next(a for a in dirty.authorities if a.authority_id == "case:us:487:213")
    assert len(delgado.pages()) <= frap.passim.threshold_pages
    assert toa_builder.is_passim(delgado, frap) is False
    assert toa_builder.page_text(delgado, frap) != frap.passim.render_text


def test_memo_bootstraps_via_marker(memo: convergence.GenerationResult) -> None:
    """The memo detects placement via the [[TOA]] marker and converges."""
    assert memo.placement.mechanism == "marker"
    assert memo.converged is True
    ids = _authority_ids(memo)
    assert {"case:f3d:512:1042", "case:us:487:213", "statute:usc:15:1692e"} <= ids


def test_memo_idempotency_handoff(
    memo: convergence.GenerationResult, frap: CourtProfile, tmp_path: Path
) -> None:
    """A re-run on the memo's output detects via the heading and converges clean."""
    output = tmp_path / "memo.toa.docx"
    memo.working_document.save(str(output))
    rerun = convergence.generate(output, frap)
    assert rerun.placement.mechanism == "heading"
    assert rerun.converged is True
    assert _authority_ids(rerun) == _authority_ids(memo)


def test_font_substitution_disclosed(clean: convergence.GenerationResult) -> None:
    """Under a substituting environment, the run metadata records it (drives TT-008)."""
    meta = clean.registry.run_metadata
    assert meta.font_substitution_occurred == bool(meta.font_substitutions)
