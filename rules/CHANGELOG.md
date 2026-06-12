# Rule Pack Changelog — `toa`

The rule-pack version track. It bumps whenever a rule card in this pack is
added, changed, or retired. It is one of toatool's four independent SemVer
tracks (see the top-level `CHANGELOG.md` for the full policy).

Individual rules carry their own versions in their card frontmatter; this
file records the version of the pack as a whole. Every finding records both
the rule version and the rule-pack version that produced it.

Versioning semantics for the pack: **major** = a change that reinterprets
existing output (a rule's severity or core meaning changes); **minor** = a
rule is added, or behavior is extended without reinterpreting old output;
**patch** = documentation and clarity only.

## [Unreleased]

### Added — pack **v1.1.0**

- **TT-009 — Unlocated occurrence** (`warning`, `high`, does not suppress
  the `.docx`), card v1.0.0. Discloses a citation occurrence the page
  locator could not place (typically a citation whose text straddles a
  physical page boundary): the occurrence is rendered `p.?`, the `.docx` is
  still written, and every other occurrence and page survives. **Minor**
  bump — a rule is added without reinterpreting any existing output.

  This closes the BL-3 emitting-path dead-end found in QA Round 3: an
  unmeasurable occurrence on the emitting path previously raised an uncaught
  `ConvergenceError` (stack trace, no output). `freeze_registry` now tolerates
  a null page and TT-009 discloses it. See `docs/QA_ROUND3.md`.

  | ID     | Name                 | Severity | Confidence | Suppresses .docx |
  |--------|----------------------|----------|------------|------------------|
  | TT-009 | Unlocated occurrence | warning  | high       | no               |

### Added — pack **v1.0.0**

- Initial `toa` rule pack, **v1.0.0**, with eight rules (each v1.0.0).
  Severities and confidences below are taken directly from the ratified
  rule-card frontmatter:

  | ID     | Name                              | Severity | Confidence | Suppresses .docx |
  |--------|-----------------------------------|----------|------------|------------------|
  | TT-001 | Unresolvable short-form citation  | error    | high       | no               |
  | TT-002 | Authority missing from input TOA  | info     | high       | no               |
  | TT-003 | Stale page numbers in input TOA   | info     | high       | no               |
  | TT-004 | Phantom input-TOA entry           | warning  | medium     | no               |
  | TT-005 | TOA placement not found           | error    | high       | **yes**          |
  | TT-006 | Marker and heading both present   | warning  | high       | no               |
  | TT-007 | Pagination non-convergence        | error    | high       | no               |
  | TT-008 | Font substitution during render   | warning  | high       | no               |

- The `frap` court profile (v1.0.0) the pack is specified against.

### Notes

- The split is deliberate: **TT-002 and TT-003 are `info`** because they
  describe corrections the tool made *for* the user (a missing entry added,
  stale page numbers fixed) — disclosures, not problems. **TT-001, TT-005,
  and TT-007 are `error`** because the user must act: an unindexable short
  form, no place to put the table, or a layout that would not stabilize.
- **TT-005 is the only rule that suppresses the regenerated `.docx`**
  (`blocks_docx_output: true`). It refuses to guess a placement rather than
  emit a table in the wrong spot; the report is still written, with the full
  generated TOA.
- **TT-004 is the only `medium`-confidence rule**: "this authority is not
  cited in the body" is deterministic over the parse, but only as reliable
  as eyecite's recall, so removal is disclosed rather than silent.
- **TT-008's severity is `warning`** per its card; `INPUT_OUTPUT_SPEC.md`
  §3.1 still reads otherwise and is to be patched on next touch — the card
  governs. CI runs under LibreOffice with Liberation substitution, so this
  finding is expected present on every fixture run in CI.
- Pack version 1.0.0 is tagged together with engine v0.1.0 when the
  implementation passes the full quality gate against the design package.
