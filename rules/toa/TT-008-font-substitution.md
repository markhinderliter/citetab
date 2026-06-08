---
id: TT-008
name: Font substitution during render
version: 1.0.0
effective_date: 2026-06-05
domain: toa
severity_default: warning
confidence_default: high
blocks_docx_output: false
citations:
  - source: INPUT_OUTPUT_SPEC.md
    section: "§3.1 (font-substitution disclosure)"
    description: >
      Page locations are computed from a LibreOffice headless render.
      When the render substitutes fonts (e.g., Liberation Serif for
      Times New Roman), line breaks — and therefore page boundaries —
      can differ from what Word would produce, shifting marginal
      citations by ±1 page.
reads:
  - registry: run metadata (render engine identity/version,
      font-substitution flag and substitution pairs)
applies_when:
  - always (every run; fires only when the render reports any
    substitution)
status: active
---

## Summary

The render that determined every page number in the output used one or
more substituted fonts. Substitute metrics are close but not identical
to the originals, so a citation near a page boundary may land one page
off relative to a render with the document's true fonts (typically:
what the court sees when the PDF is produced from Word). A `warning`,
not `info`, because it qualifies the accuracy of the tool's core
output — but not an `error`, because for most briefs and most entries
the numbers are identical, and a same-machine Word-to-PDF workflow may
never observe a discrepancy.

This is the same disclosure posture the Step B fixtures apply to
themselves (FIXTURES_README, regeneration notes).

## Logic

```
if run_metadata.font_substitution_occurred:
    emit FINDING(TT-008, warning, high,
        message = "Page locations were computed under font
                   substitution: {pairs, e.g. 'Times New Roman →
                   Liberation Serif'}. Citations near page boundaries
                   may differ by ±1 page from a render with the
                   original fonts. If exact page fidelity matters for
                   filing, render your final PDF and spot-check
                   boundary entries, or install the original fonts and
                   re-run.",
        detail  = each substitution pair; render engine and version)
```

One finding per run.

## Confidence

`high`. That substitution occurred is reported by the renderer; it is
not inferred. The *magnitude* of any shift is not claimed — only the
mechanism and the bound observed in practice (±1 at margins).

## Edge cases

- **Substitution in irrelevant runs.** v1 fires on any reported
  substitution document-wide, even if the substituted font appears only
  in, say, a caption block. Scoping the disclosure to body-text fonts
  is a v2 refinement; over-disclosure is the safe default.
- **Detecting "which fonts the document wants."** Declared fonts come
  from the .docx styles/runs; available fonts from the render
  environment. The substitution report must come from the render path
  actually used, not a separate heuristic, so the finding can never
  disagree with the measurement.
- **CI/test environments.** The Step B fixtures were measured under
  Liberation substitution, so test assertions treat TT-008 as
  environment-dependent: present under default CI, absent on a machine
  with MS fonts installed. Tests assert "no findings other than
  TT-008" on the clean fixture rather than "no findings."

## Non-goals

- Shipping or installing fonts (licensing; also out of scope).
- Quantifying per-entry shift risk. Boundary-distance analysis ("this
  citation is 2 lines from a page break") is a credible v2 enhancement,
  listed as deferred.

## Test fixtures

- All three Step B fixtures under a Liberation-substituting
  environment → expect: exactly one TT-008 warning naming the
  substitution pair.
- Same fixtures with original fonts installed → expect: no TT-008.

## Changelog

- 1.0.0 (2026-06-05): Initial version.
