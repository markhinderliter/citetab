@echo off
setlocal EnableExtensions
REM
REM  TOATool desktop launcher (Windows) — ALPHA, v0.5 usability work.
REM
REM  A double-click wrapper around `toatool generate`. It pops the native
REM  Windows file picker (filtered to .docx) via PowerShell, runs the tool on
REM  the chosen brief, and prints a plain-language result. Pure wrapper: it
REM  changes nothing about the CLI and adds no dependencies. Local-only — no
REM  network, no telemetry.
REM
REM  Prerequisites (see launchers\README.md):
REM    * toatool installed with pipx so `toatool` is on PATH
REM    * LibreOffice installed (a system dependency of toatool)

REM Dev-only escape hatch: if TOATOOL_DEV_BIN is set, prepend it. Not used in a
REM normal install.
if defined TOATOOL_DEV_BIN set "PATH=%TOATOOL_DEV_BIN%;%PATH%"

REM pipx's per-user install dir, mirrored from the macOS ~/.local/bin fix.
set "PATH=%USERPROFILE%\.local\bin;%PATH%"

REM --- Pre-flight: is toatool reachable? -------------------------------------
where toatool >nul 2>nul
if errorlevel 1 (
  echo TOATool isn't installed, or isn't on your PATH.
  echo.
  echo Ask your IT contact to install it with:
  echo.
  echo     pipx install toatool
  echo.
  echo Then double-click this launcher again.
  echo.
  pause
  exit /b 1
)

REM --- Pick a .docx via the native dialog ------------------------------------
REM PowerShell OpenFileDialog needs -STA. On Cancel it prints nothing, so BRIEF
REM stays undefined and we exit quietly below.
set "PSCMD=Add-Type -AssemblyName System.Windows.Forms; $d = New-Object System.Windows.Forms.OpenFileDialog; $d.Filter = 'Word briefs (*.docx)|*.docx'; $d.Title = 'Choose a Word brief (.docx) to process'; if ($d.ShowDialog() -eq 'OK') { [Console]::Out.Write($d.FileName) }"
for /f "usebackq delims=" %%I in (`powershell -NoProfile -STA -Command "%PSCMD%"`) do set "BRIEF=%%I"

if not defined BRIEF (
  REM Cancelled — no nagging window.
  exit /b 0
)

echo Processing:  %BRIEF%
echo This can take a few seconds while the document is rendered...
echo.

REM --- Run the tool (stdout + stderr shown to the user) ----------------------
toatool generate "%BRIEF%"
set "STATUS=%ERRORLEVEL%"

REM Folder containing the selected brief (drive + path, trailing backslash).
for %%F in ("%BRIEF%") do set "FOLDER=%%~dpF"

echo.
if "%STATUS%"=="0" (
  echo Done. Your new files are in this folder:
  echo.
  echo     %FOLDER%
  echo.
  echo   - the regenerated brief    ^(...toa.docx^)
  echo   - the findings report      ^(...toa-report.md^)
) else if "%STATUS%"=="1" (
  echo Finished - but the tool flagged issues that need a human.
  echo.
  echo Open the findings report in this folder and review it before filing:
  echo.
  echo     %FOLDER%
) else (
  echo Couldn't process that file. See the message just above.
  echo.
  echo If it mentions LibreOffice, that program needs to be installed first
  echo ^(free, from libreoffice.org^).
)

echo.
pause
exit /b %STATUS%
