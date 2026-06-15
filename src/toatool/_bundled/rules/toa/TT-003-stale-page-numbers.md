---
id: TT-003
name: Stale page numbers in input TOA
version: 1.0.0
effective_date: 2026-06-05
domain: toa
severity_default: info
confidence_default: high
blocks_docx_output: false
citations:
  - source: FRAP
    section: "28(a)(2)"
    description: >
      The table of authorities must reference the pages of the brief
      where authorities are cited. Stale page references — the core
      defect this tool exists to eliminate — make the input table
      inaccurate; the regenerated table corrects them.
reads:
  - registry: Authority.display_full, Authority.pages, Authority.passim
  - pipeline: input-TOA diff baseline (parsed entries with page lists)
applies_when:
  - input TOA region detected via flag or heading (spec §2.4 levels 1, 3)
  - input TOA region parsed into at least one entry
  - skip on marker bootstrap and on empty input TOA region (see TT-002)
status: active
---

## Summary

Input-TOA entries whose page lists do not match the pages computed from
the converged render. This is the product thesis as a finding: the tool
measured where citations actually fall and corrected the table. Emitted
as a single aggregated `info` finding per run with a per-entry
correction table — staleness is typically global (any pagination shift
moves many entries at once), and one finding per entry would be noise.

## Logic

```
baseline = parsed input TOA entries, matched to authority_ids
           (same baseline as TT-002)

corrections = []
for each (baseline entry, matched Authority):
    input_pages  = baseline entry's page list
                   ("passim" treated as a distinct value)
    actual_pages = "passim" if Authority.passim else Authority.pages
    if input_pages != actual_pages:
        corrections.append((display_full, input_pages, actual_pages))

if corrections is non-empty:
    emit FINDING(TT-003, info, high,
        subject = "{len(corrections)} of {len(matched)} input TOA
                   entries had stale page references",
        message = "Page references were recomputed from the rendered
                   document.",
        detail  = correction table:
                  authority | listed in input | corrected to)
```

## Confidence

`high` — corrected pages come from exact text-span location in the
converged render. Drops to `medium` for any correction row whose
matched occurrences include a `medium`-confidence (approximated)
location; the row is flagged in the table.

## Edge cases

- **Passim transitions count as staleness.** Input listed pages, actual
  is passim (or vice versa): a correction row, with the passim value
  shown literally. The dirty fixture's *Carmody* (D2 + D4) exercises
  this — listed as "2, 3", corrected to "passim".
- **Order/format-only differences.** Page lists are compared as sorted
  de-duplicated integer sets; "3, 2" vs "2, 3" is not a correction.
- **Front-matter pagination.** Comparison uses the body's page-number
  domain as rendered. Roman-numeral front-matter pages never appear in
  TOA page lists, by construction of the registry.
- **Unparseable page list on an otherwise matched entry.** Treated as
  stale (corrected), with the input value shown verbatim in the row.

## Non-goals

- Per-entry findings (deliberately aggregated; see README granularity
  decision).
- Explaining *why* pages drifted (editing after TOA generation, a
  different renderer). Out of scope; TT-008 covers the one
  renderer-variance case the tool can detect.

## Test fixtures

- `dirty_motion_brief.docx` → expect: exactly one TT-003 info; the
  correction table covers every input entry with wrong pages (D2),
  including Carmody → passim (D4) and Delgado → "3, 4, 5, 6, 7"
  (D5, exactly at threshold: page list, not passim).
- `clean_appellate_brief.docx` → expect: no TT-003 finding (input pages
  are real; semantic identity in = semantic identity out).
- `marker_trial_memo.docx` → expect: rule skips (bootstrap path).

## Changelog

- 1.0.0 (2026-06-05): Initial version.
