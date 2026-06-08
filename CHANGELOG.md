# Changelog

All notable changes to toatool are documented here. The format follows
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

### Added

- Initial design package: input/output specification (Step B), eight
  rule cards TT-001–TT-008 with the frap court profile (Step C),
  finding schema, Pydantic models, report specification, and three
  rendered example reports (Step D), project identity files (Step E).
- Three synthetic example briefs: clean appellate (FRAP-style, front
  matter), dirty motion (six deliberate defects), marker trial
  memorandum (bootstrap path).

### Notes

- v0.1.0 will be tagged when the implementation passes the full quality
  gate against the design package (see `docs/PRD.md`, Step F).
- The project name is a placeholder; the real name is decided at the
  v0.5 launch. Expect a rename release with import and CLI aliases
  noted here.
