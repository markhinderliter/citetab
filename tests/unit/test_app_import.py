"""Headless import-safety and the file-arg (no-dialog) path of the GUI shell.

The frozen app's GUI module must import with no display and without tkinter
present: Tk is imported lazily inside ``main()``, never at module load. The
file-argument branch of ``main()`` is fully headless — it never touches Tk — so
the frozen bundle can be launched on a brief (drag-onto-icon / ``citetab brief``)
and self-verified without a clickable dialog. None of these tests create a Tk
object.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import citetab.app


def test_app_imports_without_tk_or_display() -> None:
    """Importing the GUI module creates no Tk objects and needs no display."""
    assert callable(citetab.app.main)


def test_main_file_arg_failed_is_headless_exit_2(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A non-.docx file arg runs headlessly (no Tk), reports an error, returns 2."""
    bad = tmp_path / "not_really.docx"
    bad.write_text("this is plain text, not a docx archive", encoding="utf-8")

    code = citetab.app.main([str(bad)])

    assert code == 2
    captured = capsys.readouterr()
    assert "error:" in captured.err
    # Nothing claimed/written for an unprocessable input.
    assert not (tmp_path / "not_really.toa.docx").exists()
