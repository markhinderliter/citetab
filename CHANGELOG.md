# Changelog

All notable changes to citetab are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/), and the project adheres
to [Semantic Versioning](https://semver.org/).

## Versioning policy

Four independently versioned tracks:

| Track | Lives in | Bumps when |
|---|---|---|
| **Engine** | `pyproject.toml` | Pipeline, CLI, report renderer, or models change |
| **Rule pack** | `rules/CHANGELOG.md` | Any rule card added/changed/retired |
| **Individual rules** | each `rules/TT-*.md` frontmatter | That rule's logic, severity, or edge cases change |
| **Court profiles** | each `profiles/*.yaml` | That profile's formatting conventions change |

Every finding records the engine, rule, rule-pack, and profile versions
that produced it, so any report is reproducible against the exact
definitions in force when it was generated.

Versioning semantics for rules and profiles: **major** = findings or
output change meaning (a severity change, a passim-threshold change);
**minor** = new behavior that doesn't reinterpret old output (a new
heading variant); **patch** = documentation and clarity only.

## [Unreleased]

### Changed

- **Renamed the product `toatool` → `citetab`** (2026-06-15). The rename covers
  the Python package (`src/toatool/` → `src/citetab/`), the distribution name,
  the CLI command and `prog_name` (`toatool` → `citetab`), the LibreOffice
  override environment variable (`TOATOOL_LIBREOFFICE` → `CITETAB_LIBREOFFICE`),
  the engine-name stamped in the generated report header, and user-facing
  documentation. The domain abbreviation "toa" is unchanged: the `.toa.docx` and
  `.toa-report.md` output suffixes, the `rules/toa/` path, the TT-001–TT-009 rule
  IDs, and "Table of Authorities" all stay. Historical v0.1.0/v0.1.1 entries
  below are left as the factual record of what shipped under the old name.

### Added

- Initial design package: input/output specification (Step B), eight
  rule cards TT-001–TT-008 with the frap court profile (Step C),
  finding schema, Pydantic models, report specification, and three
  rendered example reports (Step D), project identity files (Step E).
- Three synthetic example briefs: clean appellate (FRAP-style, front
  matter), dirty motion (six deliberate defects), marker trial
  memorandum (bootstrap path).

### Fixed

- No-placement path (TT-005) no longer raises `ConvergenceError` when a
  body occurrence cannot be measured in the TOA-less render. The
  missing-page guard in `freeze_registry` is now scoped to the
  output-emitting path; when output is suppressed (no TOA is written) an
  unmeasured occurrence is tolerated (`page = None`) so the run degrades
  to a clean TT-005 instead of crashing. Found by QA Round 2's
  defect-injection harness on the clean brief minus its TOA; regression
  test `tests/integration/test_rules_oracle.py::test_oracle_brief_no_toa`.

### Notes

- v0.1.0 will be tagged when the implementation passes the full quality
  gate against the design package (see `docs/PRD.md`, Step F).
- The project name is a placeholder; the real name is decided at the
  v0.5 launch. Expect a rename release with import and CLI aliases
  noted here.

## [0.5.0] — 2026-06-19

First public release. citetab is now a double-click **Windows app**, not only a
command-line tool — aimed at the paralegal/solo-practitioner user who shouldn't
need a terminal.

### Added

- **Windows installer.** An (unsigned) `citetab-setup.exe`, built by the
  `build-windows` workflow, installs citetab like a normal Windows program with a
  Start-menu shortcut and an uninstaller. Setup shows the LibreOffice prerequisite
  — it informs only; it never downloads or installs anything for you. (Unsigned
  for now, so Windows SmartScreen warns on first run; code signing is deferred.)
- **In-app file picker (GUI).** Launching citetab with no file opens a
  "choose a `.docx`" dialog and reports the result in a message box: where the new
  files are, the court format applied, and anything to review. No terminal needed.
- **Human-readable court profile.** The CLI and GUI now disclose the applied
  format as "Court profile: Federal Appellate (FRAP)" rather than "frap (v1.0.0)".

### Changed

- **Graceful missing-LibreOffice handling.** If LibreOffice isn't installed,
  citetab now fails with a clear, instructive message (install it from
  libreoffice.org) and a clean exit instead of a crash or stack trace — and a
  bad/empty input still reports its own problem first, even when LibreOffice is
  also absent.

### Fixed

- **Windows render crash.** On Windows the LibreOffice version probe
  (`soffice.exe --version`) could hang ~60 seconds and crash the entire run before
  rendering. The probe now degrades gracefully on any failure and uses the console
  `soffice.com` so it returns the real version quickly; generation completes and
  the report shows the actual LibreOffice version instead of "unknown".
