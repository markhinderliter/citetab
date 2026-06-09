"""Tests for the registry freeze invariant (the hard null-page assertion)."""

from __future__ import annotations

from pathlib import Path

import pytest

from toatool.engine.profile_loader import load_profile_by_id
from toatool.pipeline import convergence
from toatool.pipeline.renderer import FontSubstitution
from toatool.pipeline.working import WorkingAuthority, WorkingOccurrence

CLEAN = (
    Path(__file__).resolve().parent.parent.parent
    / "examples"
    / "briefs"
    / "clean_appellate_brief.docx"
)


def _authority(page: int | None) -> WorkingAuthority:
    return WorkingAuthority(
        authority_id="case:f3d:1:1",
        type="case",
        components={},
        display_full="A v. B, 1 F.3d 1 (9th Cir. 2020)",
        sort_key="a v. b",
        group="cases",
        occurrences=[
            WorkingOccurrence(
                form="full",
                raw_text="1 F.3d 1",
                paragraph_index=3,
                char_span=(0, 8),
                page=page,
            )
        ],
    )


def _freeze(authority: WorkingAuthority):
    profile = load_profile_by_id("frap")
    return convergence.freeze_registry(
        [authority],
        profile,
        input_path=CLEAN,
        render_engine="LibreOffice",
        render_version="24.2",
        font_substitutions=[FontSubstitution("Times New Roman", "Liberation Serif")],
        iteration_count=1,
        converged=True,
    )


def test_freeze_with_pages_builds_registry() -> None:
    """An authority whose occurrences all have pages freezes into the registry."""
    registry = _freeze(_authority(page=4))
    assert registry.authorities[0].pages == [4]
    assert registry.run_metadata.font_substitution_occurred is True
    assert registry.run_metadata.input_sha256  # hashed
    assert registry.run_metadata.iteration_count == 1


def test_freeze_raises_on_null_page() -> None:
    """A converged registry with a null occurrence page fails loudly."""
    with pytest.raises(convergence.ConvergenceError, match="no .*measured page"):
        _freeze(_authority(page=None))
