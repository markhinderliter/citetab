---
id: TT-005
name: TOA placement not found
version: 1.0.0
effective_date: 2026-06-05
domain: toa
severity_default: error
confidence_default: high
blocks_docx_output: true
citations:
  - source: INPUT_OUTPUT_SPEC.md
    section: "§2.4 (detection precedence, fallback)"
    description: >
      When no placement mechanism matches — no --toa-heading override,
      no [[TOA]] marker, no default heading variant — toatool does not
      guess an insertion point. Silent insertion into a wrong location
      is never acceptable in a legal filing.
reads:
  - pipeline: placement detection result (spec §2.4 precedence walk)
  - input: court profile heading detection_variants
applies_when:
  - always (every run)
status: active
---

## Summary

The placement walk found nothing: no `--toa-heading` match, no
`[[TOA]]` marker, no default heading variant. Per spec §2.4 level 4,
the regenerated `.docx` is **not written**. The Markdown report is
still produced and leads with the fully generated TOA so the run is not
wasted — the user gets the table, just not the in-place insertion — and
this finding explains exactly how to enable insertion on the next run.

This is the only v1 rule with `blocks_docx_output: true`.

## Logic

```
if placement_detection.result == none_found:
    suppress regenerated .docx output
    emit FINDING(TT-005, error, high,
        message = "No Table of Authorities location found in
                   '{input_filename}'. Searched for: a '--toa-heading'
                   override (not provided), a [[TOA]] marker (none), and
                   the headings {detection_variants} (no match). The
                   generated TOA appears in this report. To insert it
                   into the document, either add the heading
                   '{generated_text}' where the table belongs, or place
                   [[TOA]] on its own line there, then re-run.",
        detail  = mechanisms attempted, in precedence order, each with
                  its result)
```

## Confidence

`high`. Absence of marker and heading variants is deterministic over
the parsed document. The finding claims "not found by these
mechanisms," never "this document has no TOA section" — a heading the
variant list doesn't cover (e.g., an unusual court-specific title) is
the known miss case, which is why the message enumerates exactly what
was searched for and offers `--toa-heading` implicitly via the
remediation text.

## Edge cases

- **Heading variant misses.** "TABLE OF POINTS AND AUTHORITIES" and
  similar court-specific titles are not in the v1 variant list. The
  `--toa-heading` flag is the designed escape hatch; the variant list
  is versioned data and grows with court profiles, not code changes.
- **Marker with surrounding text.** `[[TOA]]` must be alone on its
  paragraph (spec §2.4). A paragraph containing the marker plus other
  text does not match — and is worth a remediation hint in the message
  if detected ("a [[TOA]] marker was found but shares a paragraph with
  other text; place it on its own line").
- **Exit code.** A TT-005 run is a partial success (report written,
  .docx not). CLI exit-code semantics are a Step D/E decision; the rule
  card only requires that the suppression be unmistakable in both the
  terminal output and the report.

## Non-goals

- Guessing placement by citation density or any heuristic (explicitly
  rejected, spec §2.4).
- Appending the TOA to the start/end of the document as a fallback.

## Test fixtures

- **Gap.** Derive in tests: copy `marker_trial_memo.docx`, delete the
  `[[TOA]]` marker paragraph → expect one TT-005 error, no `.docx`
  output, report contains the full generated TOA.
- All three Step B fixtures → expect: no TT-005 finding.

## Changelog

- 1.0.0 (2026-06-05): Initial version.
