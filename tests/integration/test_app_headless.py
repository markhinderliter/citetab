"""The frozen app's headless file-arg path on a real brief (render-gated).

Exercises ``citetab.app.main([brief])`` — the drag-onto-icon / command-line path
the onedir bundle is verified through — without opening the Tk dialog. It runs
the same generation as the CLI, writes both outputs, and discloses the applied
court profile on stdout, returning the outcome exit code.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

import citetab.app
from citetab.engine.profile_loader import load_profile_by_id

BRIEFS = Path(__file__).resolve().parent.parent.parent / "examples" / "briefs"

_NEEDS_RENDER = pytest.mark.skipif(
    shutil.which("libreoffice") is None and shutil.which("soffice") is None,
    reason="LibreOffice is required to render; not installed",
)


@_NEEDS_RENDER
def test_main_file_arg_clean_writes_files_and_discloses_profile(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A clean brief via file arg → exit 0, both files written, profile on stdout."""
    brief = tmp_path / "clean_appellate_brief.docx"
    shutil.copy(BRIEFS / "clean_appellate_brief.docx", brief)

    code = citetab.app.main([str(brief)])

    assert code == 0
    assert (tmp_path / "clean_appellate_brief.toa.docx").is_file()
    assert (tmp_path / "clean_appellate_brief.toa-report.md").is_file()
    out = capsys.readouterr().out
    version = load_profile_by_id("frap").version
    assert f"profile: frap (v{version})" in out
