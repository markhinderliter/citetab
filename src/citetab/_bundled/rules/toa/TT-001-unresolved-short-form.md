---
id: TT-001
name: Unresolvable short-form citation
version: 1.0.0
effective_date: 2026-06-05
domain: toa
severity_default: error
confidence_default: high
blocks_docx_output: false
citations:
  - source: FRAP
    section: "28(a)(2)"
    description: >
      The brief must contain a table of authorities with references to
      the pages of the brief where they are cited. An authority cited in
      the body but absent from the TOA produces a non-compliant table.
  - source: The Bluebook
    section: "Rule 10.9 (short forms for cases)"
    description: >
      A short form may be used only after the authority has been cited
      in full. A short form with no antecedent full citation is a
      drafting error in the brief itself.
reads:
  - registry: Occurrence.form, Occurrence.raw_text, Occurrence.page,
      Occurrence.paragraph_index
  - pipeline: eyecite resolution output (anchored vs. unanchored
      short-form clusters)
applies_when:
  - always (every run)
status: active
---

## Summary

A short-form citation (*Ellison*, 740 F.3d at 1133) that eyecite cannot
anchor to any full citation in the document refers to an authority that
cannot be identified — reporter and page alone do not determine case
name, court, or year. The authority **cannot be placed in the TOA**.
citetab excludes it and emits an error: the regenerated TOA is
incomplete until the drafter adds a full citation and re-runs.

This is the one citation-quality rule where the underlying defect is in
the *brief*, not merely in the stale TOA, and the tool cannot fix it.

## Logic

```
for each citation cluster resolved by eyecite:
    if cluster contains only short / supra / id. / ibid. forms
       AND no full citation anchors it:
        exclude cluster from the Citation Registry's TOA entries
        emit FINDING(TT-001, error, high,
            subject = cluster.raw_text (representative short form),
            message = "Short-form citation '{raw_text}' has no full
                       citation anywhere in the brief. It cannot be
                       identified or placed in the Table of Authorities.
                       Add a full citation and re-run.",
            detail  = every occurrence: raw text, page, paragraph_index)
```

One finding per unresolvable cluster (per authority, not per
occurrence).

## Confidence

`high`. "No anchoring full citation exists in the parsed text" is a
deterministic property of eyecite's resolution over the document.
The finding does not claim the lawyer made an error of substance — only
that the document, as parsed, contains no anchor.

## Edge cases

- **Id./ibid. chains at document start.** An *id.* with no preceding
  citation of any kind is the degenerate case; same finding, message
  notes the form.
- **Full citation present but unparseable.** If the drafter wrote a
  full citation eyecite cannot parse (typo'd reporter, exotic source),
  the short forms will appear orphaned. The finding message therefore
  says "no full citation *was found*," and the detail lists occurrence
  locations so the drafter can check whether a full citation exists
  near them that the parser missed. This is also why the rule never
  silently drops the authority without a finding.
- **Supra to a named authority.** "*Carmody*, supra" anchors by name if
  a full *Carmody* citation exists; that resolves normally and does not
  fire this rule.

## Non-goals

- Guessing the authority's identity from reporter volume/page (would
  require a citation database — a network dependency, rejected for v1).
- Validating short-form *style* (Bluebook formatting of the short form
  itself) — deferred.

## Test fixtures

- `dirty_motion_brief.docx` → expect: one TT-001 error for the
  *Ellison* cluster (D3), detail listing both occurrences
  (at 1133, at 1136); *Ellison* absent from the regenerated TOA.
- `clean_appellate_brief.docx` → expect: no TT-001 finding.

## Changelog

- 1.0.0 (2026-06-05): Initial version.
