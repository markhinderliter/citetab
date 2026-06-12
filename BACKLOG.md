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
**Found during:** QA Round 2 (no-placement path), QA Round 3 (emitting path)
**Severity:** low (both crash paths fixed + disclosed; residual is a
measurement-*accuracy* gap, not a safety one)

The page locator measures a citation's page by matching its occurrence
string against the text of each rendered page. When a layout change pushes
an occurrence onto a page boundary so the string is split across two pages,
no single page contains the whole match and the occurrence gets no measured
page (`page = None`). This is the same boundary sensitivity that underlies
TT-007, but here it affects *measurement* rather than *convergence*.

**What is fixed (not deferred):** both crash paths and the disclosure gap are
closed.

- *No-placement path (QA Round 2).* Deleting the TOA shifted a Carmody
  pinpoint onto a boundary; the suppressed-output run raised
  `ConvergenceError` instead of reporting TT-005. Fixed: `freeze_registry`
  tolerates the null page and the run degrades to a clean TT-005 (regression
  `test_oracle_brief_no_toa`).
- *Emitting path (QA Round 3, C2-a).* A brief **with** its TOA where a
  pincite straddles a page boundary previously raised an **uncaught**
  `ConvergenceError` — stack trace, no output. Fixed: `freeze_registry` no
  longer raises at all, and **TT-009 "unlocated occurrence"** (`warning`,
  rule-pack v1.1.0) discloses each unmeasured occurrence; it renders `p.?`,
  the `.docx` is still written, and every other measured page survives
  (regression `test_oracle_brief_unmeasured_occurrence`; see
  [QA_ROUND3_RESULTS.md](QA_ROUND3_RESULTS.md)).

**What remains for v1.1 (accuracy only):** the *measurement* itself is still
best-effort at boundaries — a split occurrence is now honestly disclosed as
`p.?`, but its page is unknown rather than correct. Options to actually
resolve the page:

1. **Boundary-aware matching** — match an occurrence against the
   concatenation of adjacent rendered pages, attributing it to the page
   where its first character falls, so a split string still resolves.
2. **Normalized cross-page search** — strip page-break artifacts before
   matching so a citation spanning a break is found.

Both reduce how often TT-009 fires; neither is a safety fix (TT-009 already
prevents a silently-wrong or missing page).

**Touches (once an option is chosen):**

- `src/toatool/pipeline/locator.py` (occurrence-to-page matching).
- Tests — `tests/integration/test_rules_oracle.py` and locator unit tests;
  the deterministic page-break fixture (`derive_brief_unmeasured_occurrence`)
  is a ready regression base.

**Note:** options 1 and 2 touch the measurement core and need their own
regression fixtures; with TT-009 in place they are an accuracy enhancement,
no longer a dead-end risk.

---

### BL-4 — Citation extraction reads body paragraphs only

**Type:** coverage limitation
**Found during:** QA Round 3 (C2-c)
**Severity:** low

`extractor.build_body` concatenates the document's body *paragraphs*
(`document.paragraphs`), which excludes text living in **tables**, **text
boxes**, and **footnotes/endnotes**. A citation that appears *only* in one of
those is silently not extracted: it never becomes an authority, never lands in
the generated TOA, and produces no finding.

QA Round 3 C2-c (a citation placed in a table cell) passed the harness only
because the surrounding brief still had body prose — the run did not crash and a
report was written. But the table-only citation itself was missed with no
disclosure. A brief whose citations are *predominantly* in footnotes (common in
some practice areas) or tables would under-generate its TOA.

**Why deferred:** this is a feature-coverage gap, not a safety one — the tool
degrades quietly rather than crashing or emitting a wrong page. Closing it is
real work: footnote/endnote text lives in separate OOXML parts
(`footnotes.xml`), and table/text-box text needs a recursive walk of the
document body, both of which also need the paragraph/char-span anchoring the
locator relies on.

**Options for v1.1:**

1. **Extend `build_body`** to walk tables and text boxes (and footnotes) in
   document order, extending the offset map so occurrences still anchor to a
   `(paragraph_index, char_span)` the locator can place.
2. **Disclose, don't extract (interim).** Detect citation-shaped text in
   tables/footnotes and emit a warning ("citations found outside the body were
   not indexed") without trying to place them — a smaller, honest stopgap.

**Touches:**

- `src/toatool/pipeline/extractor.py` (body walk + offset map).
- Possibly the parser (to surface table/footnote text) and the locator.
- Tests — a fixture with a footnote-only and a table-only citation.

**Note:** option 2 is the lighter, honest interim; option 1 is the real fix but
the largest extraction change in the pipeline.
