---
id: TT-006
name: Marker and heading both present
version: 1.0.0
effective_date: 2026-06-05
domain: toa
severity_default: warning
confidence_default: high
blocks_docx_output: false
citations:
  - source: INPUT_OUTPUT_SPEC.md
    section: "§2.4 (conflict handling)"
    description: >
      If both a [[TOA]] marker and a detectable heading region are
      present, the marker wins and a warning identifies the unmodified
      heading region. citetab never silently deletes content.
reads:
  - pipeline: placement detection result (all mechanisms that matched,
      not just the winner)
applies_when:
  - a [[TOA]] marker matched (precedence level 2)
  - AND a default heading variant also matched (precedence level 3)
status: active
---

## Summary

The document contains both a `[[TOA]]` marker and an existing TOA
section detectable by heading. Per spec §2.4, the marker wins: the
generated TOA replaces the marker, and the heading region — including
whatever stale table sits under it — is left **completely untouched**.
The output document therefore contains two TOA-like regions until the
drafter deletes the old one. This warning makes that state impossible
to miss.

## Logic

```
if placement_detection.marker_matched
   AND placement_detection.heading_matched:
    place generated TOA at the marker (marker wins)
    leave heading region unmodified
    emit FINDING(TT-006, warning, high,
        message = "Both a [[TOA]] marker and an existing
                   '{matched_heading}' section were found. The
                   generated table was placed at the marker. The
                   existing section (beginning page {N}) was NOT
                   modified or removed — the output now contains both.
                   Delete the old section before filing.",
        detail  = marker location (paragraph index, page);
                  heading region location and extent)
```

Consequence for the diff rules: when the marker wins, the heading
region is not consumed, so it is **not** used as the TT-002/003/004
baseline — those rules skip, exactly as on the pure bootstrap path. A
half-replaced, half-diffed hybrid would be incoherent.

## Confidence

`high`. Both matches are deterministic.

## Edge cases

- **`--toa-heading` plus marker.** The explicit flag is precedence
  level 1 and wins over the marker; if both match, the same
  two-regions situation arises in mirror image (flag region replaced,
  marker left in the text — and a leftover `[[TOA]]` literal in a
  filed brief is worse than a stale table). Same rule fires with the
  roles swapped in the message.
- **Multiple markers.** More than one `[[TOA]]` marker is a distinct
  failure: ambiguous placement. v1 treats it as TT-005-adjacent — first
  marker wins, additional markers each get a TT-006-style warning
  naming the unconsumed marker's location. Documented here rather than
  as a ninth rule.
- **Idempotency interaction.** A second run on TT-006 output detects
  the generated TOA via heading — and the *old* heading region too if
  it had a matching heading. Two heading matches: first in document
  order wins, warning names the second. Same never-delete posture.

## Non-goals

- Removing the old heading region automatically, ever.
- Merging the old table's content into the generated one.

## Test fixtures

- **Gap.** Derive in tests: copy `dirty_motion_brief.docx`, insert a
  `[[TOA]]` marker paragraph before the introduction → expect one
  TT-006 warning; generated TOA at the marker; original stale TOA
  untouched; TT-002/003/004 skipped.
- All three Step B fixtures → expect: no TT-006 finding.

## Changelog

- 1.0.0 (2026-06-05): Initial version.
