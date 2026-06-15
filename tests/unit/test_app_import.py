"""Headless import-safety for the GUI shell.

The frozen app's GUI module must import with no display and without tkinter
present: Tk is imported lazily inside ``main()``, never at module load. This test
runs in CI (where tkinter may be absent) and must not create any Tk object.
"""

from __future__ import annotations


def test_app_imports_without_tk_or_display() -> None:
    """Importing the GUI module creates no Tk objects and needs no display."""
    import citetab.app

    assert callable(citetab.app.main)
