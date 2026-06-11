# Backlog

Deferred, post-v1 items surfaced during QA, scoped to **v1.1**. Captured
here so they are not lost. BL-1 and BL-2 are enhancements, not bugs against
the v1 spec; BL-3 is a known robustness limitation whose acute symptom was
already fixed (see its note).

---

## v1.1

### BL-1 — Report clarity: mark the earliest occurrence as "(first appearance)"

**Type:** enhancement (report readability)
**Found during:** QA
**Severity:** low

When a multi-occurrence finding lists several evidence occurrences, the
report renders them in document order but gives the reader no cue that the
first line is the *earliest* appearance in the brief. Labeling the earliest
occurrence `(first appearance)` would make multi-occurrence findings easier
to act on without re-deriving paragraph order by hand.

**Scope — applies only to multi-occurrence per-authority findings:**

- In scope: findings that render more than one occurrence (e.g. TT-001
  orphan short forms with multiple hits).
- **Out of scope:** run-level findings (TT-005, TT-006, TT-007, TT-008 —
  no subject) and the aggregated TT-003 finding. These have no
  multi-occurrence evidence list, so the label is meaningless for them.
- A finding with a single occurrence gets no label (there is no other
  appearance to distinguish it from).

**Touches:**

- `docs/REPORT_SPEC.md` §5 — document the `(first appearance)` convention
  alongside the existing occurrence-evidence rendering rules (the
  `¶{paragraph_index} p.{page} "{excerpt}"` line).
- Renderer — `src/toatool/report/render.py` (occurrence-evidence rendering).
- Example reports — regenerate `examples/reports/*.toa-report.md` from real
  runs so committed examples reflect the new label.
- Tests — `tests/integration/test_report_render.py` and the report-mask /
  rendering unit tests.

**Open question:** exact placement of the label (suffix on the first
occurrence line vs. a leading marker) — settle when specced in §5.

---

### BL-2 — Output collision: `{stem}.toa-report.md` silently overwrites

**Type:** enhancement (output safety)
**Found during:** QA
**Severity:** medium

The default report name is `{input_stem}.toa-report.md`, written alongside
the input (REPORT_SPEC §5.2 / §1). When two *different* briefs share the
same filename stem in one output directory (e.g. `motion.docx` from two
folders both run into the same place), the second run silently overwrites
the first's report — and likewise the `{input_stem}.toa.docx` primary
output. No warning, no record that data was lost.

This is not a spec violation — the naming contract is deterministic and
documented — but the silent overwrite is a footgun worth closing in v1.1.

**Options (decide when specced — not yet chosen):**

1. **Warn / refuse on existing output** — detect an existing target and
   either emit a prominent warning or refuse with a non-zero exit unless an
   explicit `--force` / `--overwrite` flag is given.
2. **`--output-dir`** — let the user route outputs to a chosen directory,
   making collisions explicit and controllable.
3. **Timestamped names** — disambiguate by appending a deterministic
   discriminator. (Tension with REPORT_SPEC §6 determinism — a timestamp
   breaks "same input → same output"; would need a content hash or
   opt-in rather than a wall-clock stamp.)

**Touches (once an option is chosen):**

- `docs/INPUT_OUTPUT_SPEC.md` §5.1 / §5.2 (output naming) and
  `docs/REPORT_SPEC.md` §1.
- CLI — `src/toatool/cli.py` (output path resolution, any new flag, exit-code
  wiring).
- Tests — `tests/integration/test_cli.py`, `tests/integration/test_idempotency.py`.

**Note:** option 3 must be reconciled with the determinism guarantee before
it can be considered; options 1 and 2 do not touch determinism.

---

### BL-3 — Occurrence measurement is fragile at page boundaries

**Type:** robustness limitation
**Found during:** QA Round 2 (defect-injection harness)
**Severity:** low (acute symptom fixed; residual is a measurement-quality gap)

The page locator measures a citation's page by matching its occurrence
string against the text of each rendered page. When a layout change pushes
an occurrence onto a page boundary so the string is split across two pages,
no single page contains the whole match and the occurrence gets no measured
page (`page = None`). This is the same boundary sensitivity that underlies
TT-007, but here it affects *measurement* rather than *convergence*.

**What was already fixed (not deferred):** QA Round 2 hit this on the clean
appellate brief with its TOA deleted — removing ~14 paragraphs shifted a
Carmody pinpoint (`512 F.3d at 1047`) onto a page boundary, and the
no-placement path raised `ConvergenceError` instead of reporting TT-005.
That crash is fixed: the missing-page guard in `freeze_registry` is now
scoped to the output-emitting path, so a suppressed-output run tolerates an
unmeasured occurrence and degrades to a clean TT-005 (regression test
`test_oracle_brief_no_toa`; see [QA_ROUND2_RESULTS.md](QA_ROUND2_RESULTS.md)).

**What remains for v1.1:** the *measurement* itself is still best-effort at
boundaries. The tolerated occurrence renders as `p.?` (REPORT_SPEC §5), so
the user is not misled, but the page is simply unknown rather than correct.
Options to harden it:

1. **Boundary-aware matching** — match an occurrence against the
   concatenation of adjacent rendered pages, attributing it to the page
   where its first character falls, so a split string still resolves.
2. **Normalized cross-page search** — strip page-break artifacts before
   matching so a citation spanning a break is found.
3. **Accept and disclose** — keep `p.?` but add an explicit info-level
   disclosure when an occurrence could not be located, rather than a silent
   null (today it is silent outside the suppressed-output path's findings).

**Touches (once an option is chosen):**

- `src/toatool/pipeline/locator.py` (occurrence-to-page matching).
- Possibly `src/toatool/pipeline/convergence.py` (`freeze_registry`
  null-page handling on the emitting path).
- Tests — `tests/integration/test_rules_oracle.py` and locator unit tests.

**Note:** option 3 is the smallest change and is purely additive; options 1
and 2 improve accuracy but touch the measurement core and need their own
regression fixtures (a brief deliberately laid out to split an occurrence).
