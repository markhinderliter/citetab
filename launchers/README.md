# Desktop launchers (ALPHA)

Double-click launchers that let someone run TOATool **without a terminal**.
Each one pops the native "open file" dialog, asks you to pick a Word brief
(`.docx`), runs `toatool generate` on it, and prints a plain-language result.

| File | Platform |
|------|----------|
| `toatool-macos.command` | macOS |
| `toatool-windows.cmd`   | Windows |

> **Status: alpha, v0.5 usability work.** These are *not* part of the v0.1.0
> release and have had no real-machine QA yet — they're here for review. They
> are pure wrappers around the existing command-line tool: they add no Python
> dependencies, no GUI framework, and change nothing about TOATool itself.

## What you need first

1. **TOATool, installed with [pipx](https://pipx.pypa.io/).** pipx puts the
   `toatool` command on your PATH so the launcher can find it:

   ```
   pipx install toatool
   ```

   (After installing pipx for the first time, run `pipx ensurepath` once and
   reopen your terminal.) The launchers assume a pipx/global install — bare
   `toatool` on the PATH. They also add pipx's per-user bin directory
   (`~/.local/bin` on macOS, `%USERPROFILE%\.local\bin` on Windows) to the PATH
   themselves, because a double-clicked launcher starts with a trimmed-down
   PATH that can otherwise miss it.

2. **LibreOffice.** TOATool measures real page numbers by rendering the brief
   with LibreOffice, so it must be installed (free, from
   [libreoffice.org](https://www.libreoffice.org/)). It is a *system*
   dependency, not a Python package.

## Using them

### macOS — `toatool-macos.command`

1. Double-click `toatool-macos.command`.
2. The first time, macOS Gatekeeper may refuse to run a downloaded script.
   **Right-click the file → Open → Open** once to approve it; after that a
   normal double-click works.
3. If the file ever loses its "executable" flag (e.g. after copying), restore
   it from Terminal with: `chmod +x toatool-macos.command`.
4. Pick a `.docx` in the dialog. A Terminal window shows progress and the
   result, and waits for you to press **Return** before closing.

### Windows — `toatool-windows.cmd`

1. Double-click `toatool-windows.cmd`.
2. The first time, Windows SmartScreen may warn about an unrecognized script.
   Choose **More info → Run anyway** to proceed.
3. Pick a `.docx` in the dialog. A console window shows progress and the
   result, and waits for a key press before closing.

## Where your files go

The two output files are written **next to the brief you picked**, in the same
folder:

- `<name>.toa.docx` — the regenerated brief with a fresh Table of Authorities
- `<name>.toa-report.md` — the findings report

The launcher tells you the exact folder when it finishes.

## What the result means

The launcher reports one of three outcomes (mirroring TOATool's own exit codes):

| Outcome | What it means | What to do |
|---------|---------------|------------|
| **Done** | Both files were written cleanly. | Use the regenerated brief; skim the report. |
| **Finished, with issues** | The tool flagged something error-level (or couldn't place the TOA, so it didn't rewrite the `.docx`). The **report is still written.** | Open the findings report and review it **before filing**. |
| **Couldn't process that file** | The input wasn't usable (not a real `.docx`, unreadable) or a required program (LibreOffice) is missing. Nothing was written. | Read the one-line message shown; fix the input or install LibreOffice. |

The tool never shows a stack trace here — just a short human message.

## Troubleshooting

- **"TOATool isn't installed, or isn't on your PATH."** It wasn't found.
  Install it with `pipx install toatool`, run `pipx ensurepath`, then try again.
- **A message mentioning LibreOffice.** Install LibreOffice from
  [libreoffice.org](https://www.libreoffice.org/) and re-run.
- **Nothing happened / the window closed instantly.** You probably pressed
  Cancel in the file dialog — that exits quietly by design.

## For developers

The launchers deliberately do **not** probe a repo `.venv/bin` (that would be
dev-only clutter in a shipped file). If you want to point a launcher at a
development install, set the `TOATOOL_DEV_BIN` environment variable to a
directory containing a `toatool` executable; the launcher prepends it to PATH:

```bash
# macOS
TOATOOL_DEV_BIN="$PWD/.venv/bin" ./launchers/toatool-macos.command
```

```bat
REM Windows
set "TOATOOL_DEV_BIN=%CD%\.venv\Scripts"
launchers\toatool-windows.cmd
```

## Privacy

These launchers are local wrappers, consistent with `docs/AI_GUARDRAILS.md`:
no network calls, no telemetry, no LLM — they only invoke the local `toatool`
command on a file you pick. Your document never leaves your machine.
