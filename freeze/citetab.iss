; freeze/citetab.iss — Inno Setup script for the citetab Windows installer (v0.5 / 3c).
;
; Packages the PyInstaller onedir bundle (dist\citetab\, INCLUDING _internal\)
; into an UNSIGNED setup.exe that:
;   - installs citetab under Program Files,
;   - adds a Start-menu shortcut that launches the GUI picker (citetab.exe with
;     NO arguments — the no-arg → Tk file-dialog path),
;   - shows an informational page stating the LibreOffice prerequisite (it only
;     INFORMS; it does not download or install anything — Option A),
;   - registers a standard uninstaller.
;
; Out of scope by decision: code signing (deferred — this is UNSIGNED) and
; auto-fetching LibreOffice (Option A — the user installs it themselves).
;
; NOT verifiable on Linux. Inno Setup is Windows-only; compile with iscc on
; Windows (CI does this on windows-latest). Build locally from the repo root:
;   iscc /DMyAppVersion=0.1.0 freeze\citetab.iss
; CI injects the real version from the installed package; the default below only
; lets the script compile standalone.

#ifndef MyAppVersion
  #define MyAppVersion "0.0.0"
#endif

#define MyAppName "Citetab"
#define MyAppPublisher "Citetab"
#define MyAppExeName "citetab.exe"

[Setup]
; AppId uniquely identifies the application to Windows for upgrades and uninstall.
; It MUST stay constant across all future versions — changing it would make a new
; version install alongside the old instead of upgrading it. (Fixed GUID, not the
; double-brace is an escaped literal "{".)
AppId={{B7E9F3A1-4C2D-4E8B-9A1F-2D3C4B5A6E7F}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
; {autopf} = the real "Program Files" for the install's bitness (see 64-bit mode
; below); admin elevation is required to write there.
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
; The app is fully self-contained, so there is nothing to configure beyond the
; install dir; suppress the redundant "choose Start-menu folder" page.
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\{#MyAppExeName}
; Anchor source/output to the script's own location (freeze\..) = repo root, so
; the compile works regardless of the caller's working directory.
SourceDir={#SourcePath}..
OutputDir=dist\installer
OutputBaseFilename=citetab-setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
; The PyInstaller bundle from windows-latest is 64-bit, so install into the
; 64-bit Program Files (not Program Files (x86)). x64compatible requires Inno
; Setup 6.3+; the CI runner installs a current 6.x, which satisfies this.
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
; Writing to Program Files and a machine-wide Start-menu group needs admin.
PrivilegesRequired=admin

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
; The whole onedir tree — citetab.exe plus _internal\ — copied verbatim. Order is
; irrelevant; recursesubdirs/createallsubdirs preserve the _internal\ layout that
; importlib.resources and the bundled Tcl/Tk rely on at runtime.
Source: "dist\citetab\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
; Start-menu shortcut → the GUI picker. No Parameters: line, so citetab.exe is run
; with NO arguments → app.main opens the Tk "choose a .docx" dialog. This is the
; double-click/paralegal path, NOT a console/CLI shortcut.
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"

[Code]
{ A self-contained informational page (no external readme file to ship or get
  wrong in CI) inserted right after the Welcome page, before any install action.
  CreateOutputMsgPage is Inno's standard read-only message page — chosen over
  InfoBeforeFile precisely because it needs no separate bundled file, keeping the
  prerequisite notice in this one script. It INFORMS ONLY: nothing is downloaded
  or installed (Option A — the user keeps full control of LibreOffice). }
procedure InitializeWizard();
begin
  CreateOutputMsgPage(
    wpWelcome,
    'LibreOffice required',
    'Citetab uses LibreOffice to measure document pages.',
    'Citetab requires LibreOffice to process documents.' + #13#10 + #13#10 +
    'If you do not already have it, install it free from' + #13#10 +
    'https://www.libreoffice.org/' + #13#10 + #13#10 +
    'then run Citetab. This installer does not download or install LibreOffice ' +
    '— you stay in control of what is installed on your computer.');
end;
