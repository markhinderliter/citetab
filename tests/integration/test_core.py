"""Shared-core (``citetab.core.run_generation``) outcomes.

The core is the single code path behind both the CLI and the GUI. These tests
target it directly (no Click, no Tk), covering the three outcomes that map to the
0/1/2 exit codes, using the same example briefs / derived fixtures the CLI tests
use. The success and suppressed paths render, so they are gated on LibreOffice;
the failed path fails before any render.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from citetab.core import Outcome, run_generation

BRIEFS = Path(__file__).resolve().parent.parent.parent / "examples" / "briefs"

_NEEDS_RENDER = pytest.mark.skipif(
    shutil.which("libreoffice") is None and shutil.which("soffice") is None,
    reason="LibreOffice is required to render; not installed",
)


def _copy(name: str, dest_dir: Path) -> Path:
    """Copy a base brief into ``dest_dir`` and return the destination path."""
    dest = dest_dir / name
    shutil.copy(BRIEFS / name, dest)
    return dest


@_NEEDS_RENDER
def test_core_clean_is_success_with_both_files(tmp_path: Path) -> None:
    """(a) A clean brief → SUCCESS/exit 0, both files written, folder named."""
    brief = _copy("clean_appellate_brief.docx", tmp_path)
    result = run_generation(brief)

    assert result.outcome is Outcome.SUCCESS
    assert result.exit_code == 0
    assert result.output_dir == tmp_path.resolve()
    assert result.docx_path is not None and result.docx_path.is_file()
    assert result.report_path is not None and result.report_path.is_file()
    # The message names the output folder so the user can find the results.
    assert str(result.output_dir) in result.message


def test_core_non_docx_is_failed_no_files(tmp_path: Path) -> None:
    """(b) A non-.docx input → FAILED/exit 2, no files claimed, polite message."""
    bad = tmp_path / "not_really.docx"
    bad.write_text("this is plain text, not a docx archive", encoding="utf-8")
    result = run_generation(bad)

    assert result.outcome is Outcome.FAILED
    assert result.exit_code == 2
    assert result.docx_path is None
    assert result.report_path is None
    assert result.error  # the failure reason is captured
    assert result.message  # a non-empty, human-readable message
    # Nothing was written next to the input.
    assert not (tmp_path / "not_really.toa.docx").exists()
    assert not list(tmp_path.glob("*.toa-report.md"))


@_NEEDS_RENDER
def test_core_suppressed_is_issues_without_docx(memo_no_marker: Path) -> None:
    """(c) A no-placement run → ISSUES/exit 1, no .docx, report written.

    The message must not claim a regenerated brief was written on this path.
    """
    result = run_generation(memo_no_marker)

    assert result.outcome is Outcome.ISSUES
    assert result.exit_code == 1
    assert result.docx_path is None
    assert result.report_path is not None and result.report_path.is_file()
    assert not memo_no_marker.with_name("memo_no_marker.toa.docx").exists()
    # Honest message: the report is named, the (absent) .docx is NOT promised.
    assert result.report_path.name in result.message
    assert ".toa.docx" not in result.message
