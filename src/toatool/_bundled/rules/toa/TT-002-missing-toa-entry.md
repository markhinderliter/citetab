---
id: TT-002
name: Authority missing from input TOA
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
      The table of authorities must reference the authorities cited.
      An authority cited in the body but absent from the input TOA made
      the input table non-compliant; the regenerated table corrects it.
reads:
  - registry: Authority (full resolved set), Authority.display_full,
      Authority.pages
  - pipeline: input-TOA diff baseline (parsed entries from the input
      document's TOA region)
applies_when:
  - input TOA region detected via flag or heading (spec §2.4 levels 1, 3)
  - input TOA region parsed into at least one entry
  - skip on marker bootstrap (no input TOA to compare)
status: active
---

## Summary

An authority that appears in the brief's body but has no entry in the
input document's existing TOA. toatool's regenerated TOA includes it —
the defect is corrected by construction — so this finding is an `info`
disclosure: it tells the drafter what their old table was missing, which
is both a trust signal ("the tool found what I missed") and an audit
record of the delta between input and output.

## Logic

```
baseline = parse input TOA region into entries
           (best-effort: authority text + page list per entry;
            unparseable entries recorded separately, excluded here)

resolve each baseline entry to an authority_id where possible

for each Authority in the Citation Registry:
    if Authority.authority_id not among resolved baseline entries:
        emit FINDING(TT-002, info, high,
            subject = Authority.display_full,
            message = "'{display_full}' is cited in the body
                       (pages {pages}) but had no entry in the input
                       Table of Authorities. Added.",
            detail  = pages, occurrence count)
```

One finding per missing authority.

## Confidence

`high` when the baseline entry set parsed cleanly. If the input TOA
region contained unparseable entries, every TT-002 finding in that run
drops to `medium` — an unparsed input entry might have been the
"missing" authority in a form the diff couldn't match — and the
message notes this.

## Edge cases

- **Matching is by resolved identity, not string.** "*Carmody v.
  Westfall Transit Auth.*, 512 F.3d 1042" in the input TOA matches the
  registry's Carmody authority regardless of formatting differences.
  Formatting drift alone never fires TT-002.
- **Authority excluded by TT-001.** An unresolvable short-form cluster
  is not in the registry's TOA entries and therefore cannot fire
  TT-002. The two rules are disjoint by construction.
- **Empty input TOA region** (heading present, no entries beneath).
  Treated as bootstrap-like: TT-002/003/004 skip, since every entry
  would otherwise fire and the per-authority findings would be noise.
  The regenerated TOA is itself the disclosure.

## Non-goals

- Judging *why* the entry was missing (manual drafting, a prior tool's
  failure). The finding states the fact only.

## Test fixtures

- `dirty_motion_brief.docx` → expect: exactly one TT-002 info for
  *United States v. Okafor*, 891 F.3d 655 (D1), pages 4 and 6.
- `clean_appellate_brief.docx` → expect: no TT-002 finding.
- `marker_trial_memo.docx` → expect: rule skips (bootstrap path).

## Changelog

- 1.0.0 (2026-06-05): Initial version.
