"""Double-click GUI shell for citetab — a thin Tk front end over the shared core.

When the frozen app is launched with no file argument, ``main()`` opens a native
"open file" dialog filtered to ``.docx``, runs the same generation the CLI does
(:func:`citetab.core.run_generation`), and shows the result in a dialog. There is
no console in the frozen app, so all feedback is via ``tkinter.messagebox``; a
cancelled dialog exits cleanly with no error.

Tkinter is part of the standard library and is imported lazily inside ``main()``
— never at module import — so this module imports safely on a headless machine
(no display, or no Tk installed). Run in development with ``python -m citetab.app``.
"""

from __future__ import annotations

from pathlib import Path

from citetab.core import Outcome, run_generation


def main() -> None:
    """Open a file picker, run generation on the choice, and show the result."""
    import tkinter as tk
    from tkinter import filedialog, messagebox

    root = tk.Tk()
    root.withdraw()  # no empty main window; only dialogs are shown
    try:
        selected = filedialog.askopenfilename(
            title="Choose a Word brief (.docx) to process",
            filetypes=[("Word briefs", "*.docx")],
        )
        if not selected:
            return  # cancelled — exit quietly, no dialog

        result = run_generation(Path(selected))
        show = {
            Outcome.SUCCESS: messagebox.showinfo,
            Outcome.ISSUES: messagebox.showwarning,
            Outcome.FAILED: messagebox.showerror,
        }[result.outcome]
        show("citetab", result.message)
    finally:
        root.destroy()


if __name__ == "__main__":  # pragma: no cover - manual GUI entry point
    main()
