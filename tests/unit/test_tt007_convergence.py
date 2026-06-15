"""TT-007 via a mocked measurer that never lets pagination settle.

Per the TT-007 card, no realistic small fixture oscillates reliably, so the loop
is tested with a mocked measure step that alternates one authority's page every
iteration. The renderer and PDF locator are replaced so no LibreOffice or PDF is
involved: the test exercises the convergence loop's cap behavior and the rule it
drives, not the renderer. Expected: the loop reaches the cap without converging,
the outputs are still written, and one TT-007 error names the oscillating entry.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from citetab.engine.profile_loader import load_profile_by_id
from citetab.engine.runner import run_rules
from citetab.pipeline import convergence, locator, renderer
from citetab.pipeline.working import WorkingOccurrence

BRIEFS = Path(__file__).resolve().parent.parent.parent / "examples" / "briefs"

# Library availability gates the render in generate(); the mocked test replaces
# the render path entirely, so it runs even without LibreOffice installed.


def _install_oscillating_measurer(monkeypatch: pytest.MonkeyPatch) -> None:
    """Replace render + locate so Carmody's page alternates 2 ⇄ 3 each iteration."""
    calls = {"n": 0}

    def fake_render(docx_path: Path, out_dir: Path) -> Path:
        return out_dir / f"{docx_path.stem}.pdf"

    def fake_locate(
        pdf_path: Path,
        occurrences: list[WorkingOccurrence],
        body_anchor: str | None,
    ) -> None:
        calls["n"] += 1
        carmody_page = 2 if calls["n"] % 2 else 3
        for occ in occurrences:
            if "512 F.3d" in occ.raw_text or "Carmody" in occ.raw_text:
                occ.page = carmody_page
            else:
                occ.page = 5
            occ.confidence = "high"

    monkeypatch.setattr(renderer, "render_to_pdf", fake_render)
    monkeypatch.setattr(locator, "locate_occurrences", fake_locate)
    monkeypatch.setattr(renderer, "detect_font_substitutions", lambda _path: [])
    monkeypatch.setattr(renderer, "render_engine_info", lambda: ("LibreOffice", "24.2"))


def test_loop_reaches_cap_without_converging(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The mocked oscillation drives the loop to the cap, never converging."""
    _install_oscillating_measurer(monkeypatch)
    frap = load_profile_by_id("frap")
    result = convergence.generate(BRIEFS / "marker_trial_memo.docx", frap)

    assert result.converged is False
    assert result.iteration_count == convergence.ITERATION_CAP
    assert result.registry.run_metadata.converged is False
    # Outputs are still produced — the working document exists for writing.
    assert result.working_document is not None
    assert result.blocks_docx_output is False


def test_tt007_fires_with_outputs_written(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """One TT-007 error names the oscillating authority; the .docx is not blocked."""
    _install_oscillating_measurer(monkeypatch)
    frap = load_profile_by_id("frap")
    path = BRIEFS / "marker_trial_memo.docx"
    result = convergence.generate(path, frap)
    rules = run_rules(result, input_path=path, profile=frap)

    tt007 = [f for f in rules.findings if f.rule_id == "TT-007"]
    assert len(tt007) == 1
    finding = tt007[0]
    assert finding.severity == "error"
    assert finding.confidence == "high"
    assert finding.blocks_docx_output is False

    unstable = finding.evidence.computed_values["unstable"]
    assert len(unstable) == 1
    assert "Carmody" in str(unstable[0]["authority"])
    per_iteration = unstable[0]["per_iteration_pages"]
    # The page alternated between two values across the capped iterations.
    assert {tuple(p) for p in per_iteration} == {(2,), (3,)}

    # TT-007 does not suppress output; the exit code is 1 because it is an error.
    assert rules.docx_suppressed is False
    assert rules.exit_code == 1
