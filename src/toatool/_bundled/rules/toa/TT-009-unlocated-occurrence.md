---
id: TT-009
name: Unlocated occurrence
version: 1.0.0
effective_date: 2026-06-12
domain: toa
severity_default: warning
confidence_default: high
blocks_docx_output: false
citations:
  - source: INPUT_OUTPUT_SPEC.md
    section: "§3.1 (page-measurement disclosure)"
    description: >
      Page numbers are located by matching each citation's text against the
      rendered page stream. When a citation's text is split across a physical
      page boundary, no single page contains the whole string, so that one
      occurrence cannot be located and its page is left unmeasured (rendered
      "p.?"). The remaining occurrences and pages are unaffected.
reads:
  - registry: frozen authorities and their occurrences (occurrence pages,
      including any left null by the locator)
applies_when:
  - a TOA was emitted (placement found); skipped on the no-placement path,
    where TT-005 already reports that nothing usable was produced
status: active
---

## Summary

The page locator could not place one or more citation occurrences in the
rendered output, so their page is left unmeasured and rendered `p.?` in
the report. The usual cause is a citation whose text straddles a physical
page boundary: the locator concatenates the rendered pages with a newline
between them and matches each occurrence's verbatim text, so a string that
ends one page and resumes on the next matches neither.

A `warning`, not an `error`: the regenerated `.docx` is still written and
every *other* occurrence and page for the affected authority survives — the
tool degrades honestly rather than crashing or silently dropping the entry.
But a `warning`, not `info`, because a page reference in the filed Table of
Authorities is unknown until the user verifies it, and an attorney must know
that before filing.

This is the "honest degradation over pretended success" posture the
convergence loop already takes for non-convergence (TT-007) and the render
takes for font substitution (TT-008): disclose the limit, keep the usable
output, never fabricate a page.

## Logic

```
unmeasured = [occ for auth in registry.authorities
                  for occ in auth.occurrences
                  if occ.page is None]
if placement.mechanism != "none" and unmeasured:
    emit FINDING(TT-009, warning, high,
        message = "{n} citation occurrence(s) could not be placed on a
                   rendered page and are shown as 'p.?': {authority — '{text}'
                   …}. This usually means the citation's text falls across a
                   page break. The rest of each authority's pages are
                   unaffected; verify the unmeasured reference(s) against your
                   final PDF before filing.",
        detail  = each unmeasured occurrence (authority, paragraph, text))
```

One run-level finding per run, listing every unmeasured occurrence.

## Confidence

`high`. That an occurrence was not located is a fact reported by the
locator, not an inference. The finding does not claim *which* page the
occurrence is on — only that it could not be determined automatically.

## Edge cases

- **No-placement path (TT-005).** When no TOA was emitted, the `.docx` is
  suppressed and TT-005 already reports that nothing usable was produced;
  TT-009 stays silent there to avoid piling a second disclosure on a run
  that produced no Table of Authorities. `applies` is false when
  `placement.mechanism == "none"`.
- **Authority fully unmeasured.** If *every* occurrence of an authority is
  unlocated, its emitted page list is empty and TT-009 names each occurrence;
  the entry still renders with whatever the input TOA supplied, so nothing is
  silently lost.
- **Multiple unmeasured occurrences.** All are named in the single run-level
  finding, in document order.

## Non-goals

- Guessing the unmeasured page. Boundary-aware matching (attributing a split
  citation to the page where its first character falls) is a credible
  enhancement, listed as deferred — over-disclosure is the safe default.
- Re-laying-out the document to avoid the split. The tool measures; it does
  not re-typeset the brief.

## Test fixtures

- Clean brief with a hard page break injected inside the Carmody pincite
  `512 F.3d at 1047` → expect: exactly one TT-009 warning naming that
  occurrence; the `.docx` is written; Carmody's other measured pages survive
  (QA Round 3, C2-a).

## Changelog

- 1.0.0 (2026-06-12): Initial version. Introduced with rule-pack 1.1.0 to
  close the BL-3 emitting-path dead-end found in QA Round 3.
