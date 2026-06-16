---
id: TT-004
name: Phantom input-TOA entry
version: 1.0.0
effective_date: 2026-06-05
domain: toa
severity_default: warning
confidence_default: medium
blocks_docx_output: false
citations:
  - source: FRAP
    section: "28(a)(2)"
    description: >
      The table of authorities references authorities cited in the
      brief. An entry for an authority never cited in the body is a
      defect in the input table — typically a remnant of a deleted
      argument section.
reads:
  - registry: Authority (full resolved set)
  - pipeline: input-TOA diff baseline (parsed and unparsed entries)
applies_when:
  - input TOA region detected via flag or heading (spec §2.4 levels 1, 3)
  - input TOA region parsed into at least one entry
  - skip on marker bootstrap and on empty input TOA region
status: active
---

## Summary

An entry in the input document's TOA that matches no authority found in
the body. The regenerated TOA omits it by construction — it renders
only from the Citation Registry — but the omission is a `warning`, not
an `info`, because there are two explanations and the tool cannot
distinguish them:

1. The entry is a true phantom (the citing text was deleted during
   editing) — removal is correct.
2. The body citation exists but **eyecite failed to parse it** — removal
   silently drops a real authority from a legal filing.

The asymmetric cost of (2) is why this rule exists and why it warns.
citetab never silently deletes a lawyer's TOA entry.

## Logic

```
baseline = parsed input TOA entries (same baseline as TT-002/003)

for each baseline entry NOT matched to any registry authority_id:
    emit FINDING(TT-004, warning, medium,
        subject = entry's verbatim authority text,
        message = "Input TOA entry '{text}' matches no citation found
                   in the body. It was removed from the regenerated
                   Table of Authorities. If this authority IS cited in
                   the brief, the citation was not recognized — verify
                   before filing.",
        detail  = entry's verbatim text and input page list)

for each UNPARSED input TOA entry (could not be read as
                                   authority + pages):
    emit FINDING(TT-004, warning, medium,
        subject = the unparsed line, verbatim,
        message = "Input TOA line could not be interpreted and does not
                   appear in the regenerated table. Verify before
                   filing.")
```

One finding per removed or unparsed entry.

## Confidence

`medium`, always. The claim "no citation found in the body" is
deterministic over the *parse*, but the finding's real-world claim —
"this authority is not cited" — is only as good as eyecite's recall.
Encoding that gap as `medium` is the epistemological-honesty rule
applied to the tool's own parser.

## Edge cases

- **Continuation lines and subheadings.** Input TOAs contain group
  headings ("Cases", "Statutes") and wrapped entries. The baseline
  parser must not classify group headings as unparsed entries;
  recognized group labels (per the active court profile plus common
  variants) are structural, not entries.
- **Short-form-only authority in the input TOA.** If the input TOA
  lists an authority whose only body presence is an unresolvable short
  form, TT-001 fires (orphan) AND TT-004 fires (entry unmatched). Both
  are emitted; this is the one designed-in pair, and the report layer
  (Step D) may group them. Note: in this case the input TOA entry is
  itself evidence of the authority's identity — the finding messages
  cross-reference each other so the drafter sees the connection.
- **Near-miss matching.** Matching is by resolved identity (TT-002
  semantics). A typo'd input entry that still resolves (e.g., year off
  by one but reporter/volume/page match) is matched, not phantom;
  resolution tolerances live in the diff matcher, documented at build
  time.

## Non-goals

- Improving eyecite's recall. The rule discloses the consequence of a
  miss; it does not attempt secondary parsing.
- Keeping phantom entries in the output "just in case." The output TOA
  is always exactly the registry; the warning is the safety mechanism.

## Test fixtures

- **Gap.** No Step B fixture exercises this rule. Derive in tests: copy
  `dirty_motion_brief.docx`, add a fabricated entry (*Nonexistent v.
  Authority*, 999 F.9d 999) to its TOA → expect one TT-004 warning,
  entry absent from regenerated TOA.
- `clean_appellate_brief.docx` → expect: no TT-004 finding.

## Changelog

- 1.0.0 (2026-06-05): Initial version.
