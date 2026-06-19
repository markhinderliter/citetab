"""Double-click GUI shell for citetab — a thin Tk front end over the shared core.

``main()`` has two paths over the same generation core:

- **No file argument** (a double-click): open a native "open file" dialog filtered
  to ``.docx``, run the generation, and show the result via ``tkinter.messagebox``
  — there is no console in the frozen app, so all GUI feedback is a dialog; a
  cancelled dialog exits cleanly with no error.
- **A file-path argument** (drag-a-brief-onto-the-icon, or ``citetab brief.docx``):
  run the generation headlessly and report on stdout/stderr using the same fields
  the CLI prints, returning the outcome's exit code. This path never touches Tk.

Tkinter is imported lazily inside the dialog path — never at module import and
never on the file-arg path — so this module imports safely with no display and
the frozen bundle can be self-verified headlessly. Run in development with
``python -m citetab.app`` (dialog) or ``python -m citetab.app <brief.docx>``.
"""

from __future__ import annotations

import sys
from pathlib import Path

from citetab.core import GenerationOutcome, Outcome, run_generation


def _report_stdout(result: GenerationOutcome) -> int:
    """Print the CLI-style disclosure for a headless run and return its exit code."""
    if result.outcome is Outcome.FAILED:
        print(f"error: {result.error}", file=sys.stderr)
        return result.exit_code

    assert result.report_path is not None  # set on every non-FAILED outcome
    print(f"profile: {result.profile_name}")
    if result.docx_path is None:
        print("output: .docx SUPPRESSED (no placement found); report written")
    else:
        print(f"output: {result.docx_path.name}")
    print(f"report: {result.report_path.name}")
    print(
        f"findings: {result.error_count} error · {result.warning_count} warning · "
        f"{result.info_count} info"
    )
    return result.exit_code


def _run_dialog() -> int:
    """Open the file picker, run generation on the choice, and show the result."""
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
            return 0  # cancelled — exit quietly, no dialog

        result = run_generation(Path(selected))
        show = {
            Outcome.SUCCESS: messagebox.showinfo,
            Outcome.ISSUES: messagebox.showwarning,
            Outcome.FAILED: messagebox.showerror,
        }[result.outcome]
        show("citetab", result.message)
        return result.exit_code
    finally:
        root.destroy()


def main(argv: list[str] | None = None) -> int:
    """Run the picker (no argument) or process a given brief headlessly.

    Args:
        argv: Arguments after the program name; defaults to ``sys.argv[1:]``. The
            first entry, if present, is treated as the brief path (headless run);
            no entry opens the file dialog.

    Returns:
        The process exit code (the generation outcome's, or 0 on a cancelled
        dialog).
    """
    args = sys.argv[1:] if argv is None else argv
    if args:
        return _report_stdout(run_generation(Path(args[0])))
    return _run_dialog()


if __name__ == "__main__":  # pragma: no cover - manual entry point
    raise SystemExit(main())
