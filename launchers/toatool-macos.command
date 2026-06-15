#!/bin/bash
#
# TOATool desktop launcher (macOS) — ALPHA, v0.5 usability work.
#
# A double-click wrapper around `toatool generate`. It pops the native macOS
# file picker (filtered to .docx), runs the tool on the chosen brief, and prints
# a plain-language result. It is a pure wrapper: it changes nothing about the
# CLI and adds no dependencies. Local-only — no network, no telemetry.
#
# Prerequisites (see launchers/README.md):
#   • toatool installed with pipx so `toatool` is on PATH
#   • LibreOffice installed (a system dependency of toatool)

# Double-clicked .command files start with a minimal PATH that often omits
# pipx's install dir, so add it explicitly. (Requested fallback.)
export PATH="$HOME/.local/bin:$PATH"

# Dev-only escape hatch: if TOATOOL_DEV_BIN is set, prepend it (e.g. a repo
# .venv/bin during development). Not used in a normal install.
if [ -n "$TOATOOL_DEV_BIN" ]; then
  export PATH="$TOATOOL_DEV_BIN:$PATH"
fi

# Print a message, wait for Return, then close. Keeps the window readable when
# launched by double-click (which closes the terminal as soon as we exit).
finish() {
  echo
  echo "$1"
  echo
  echo "Press Return to close this window."
  read -r _
  exit "${2:-0}"
}

# --- Pre-flight: is toatool reachable? -------------------------------------
if ! command -v toatool >/dev/null 2>&1; then
  finish "TOATool isn't installed, or isn't on your PATH.

Ask your IT contact to install it with:

    pipx install toatool

Then double-click this launcher again." 1
fi

# --- Pick a .docx via the native dialog ------------------------------------
# `POSIX path of (choose file ...)` returns a normal /Users/... path. If the
# user cancels, osascript errors; we swallow it and exit quietly.
BRIEF="$(osascript -e 'POSIX path of (choose file with prompt "Choose a Word brief (.docx) to process:" of type {"docx"})' 2>/dev/null)"

if [ -z "$BRIEF" ]; then
  # Cancelled — no nagging window.
  exit 0
fi

echo "Processing:  $BRIEF"
echo "This can take a few seconds while the document is rendered…"
echo

# --- Run the tool (stdout + stderr shown to the user) ----------------------
toatool generate "$BRIEF"
STATUS=$?
FOLDER="$(dirname "$BRIEF")"

case "$STATUS" in
  0)
    finish "Done. Your new files are in this folder:

    $FOLDER

  • the regenerated brief        (…toa.docx)
  • the findings report          (…toa-report.md)" 0
    ;;
  1)
    # Error-severity finding, or the .docx was suppressed. The report is still
    # written. The tool's own summary above says exactly what was produced.
    # We propagate exit 1 (parity with the Windows launcher) so the outcome is
    # scriptable; the message makes clear this is "review needed", not a crash.
    finish "Finished — but the tool flagged issues that need a human.

Open the findings report in this folder and review it before filing:

    $FOLDER" "$STATUS"
    ;;
  *)
    # Exit 2 (or anything unexpected): toatool already printed a one-line
    # 'error: …' reason above — no stack trace.
    finish "Couldn't process that file. See the message just above.

If it mentions LibreOffice, that program needs to be installed first
(free, from libreoffice.org)." "$STATUS"
    ;;
esac
