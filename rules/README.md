# toatool Rule Pack — Step C (Rule Specifications)

**Status:** Draft for ratification
**Version:** 0.1.0-draft
**Date:** 2026-06-05
**Depends on:** INPUT_OUTPUT_SPEC.md (Step B), the three Step B fixtures

Eight rules, TT-001 through TT-008, plus the FRAP court profile
(`frap-profile.yaml`). Each rule is a versioned card in the CallLint
format: YAML frontmatter (machine-readable contract) plus prose
(summary, logic, confidence, edge cases, non-goals, fixtures).

---

## How toatool rules differ from CallLint rules

CallLint was a linter: rules *were* the product. toatool is a
generator: the TOA is the product and findings are disclosures around
it. Most defects the rules describe are **corrected by the tool**, not
merely flagged. This changes what severity means.

### Severity semantics: "what must the user do before filing?"

| Severity | Meaning | User action |
|---|---|---|
| `error` | Output is incomplete or unreliable; the regenerated TOA cannot be trusted as filed | Fix the brief (or placement) and re-run, or manually complete the TOA |
| `warning` | Output produced and usable, but something should be verified | Review the named item before filing |
| `info` | A correction the tool made, disclosed for trust and audit | None; informational record of the delta |

### Confidence semantics (unchanged from CallLint)

| Confidence | Meaning |
|---|---|
| `high` | Deterministic from parse or render (structured .docx content, exact text-span location in the converged render) |
| `medium` | Approximated or best-effort (approximated occurrence location, best-effort parse of the input TOA) |

### Blocking

One rule blocks the primary output: TT-005 (placement not found)
suppresses the regenerated .docx entirely per spec §2.4 — the TOA is
emitted in the Markdown report only. Every other rule, including the
error-severity TT-001 and TT-007, still writes both outputs. This is
encoded in frontmatter as `blocks_docx_output`.

---

## Derived requirement: input-TOA diffing

TT-002, TT-003, and TT-004 require toatool to **parse the input
document's existing TOA entries** (best-effort: authority text + page
list per entry) before replacing the region. Regeneration alone cannot
produce "your TOA was missing Okafor" — that claim needs the old TOA
as a comparison baseline.

Contract:

- Diffing is best-effort. An input entry that cannot be parsed into an
  (authority, pages) pair is recorded as unparsed and excluded from
  TT-002/TT-003 comparisons; TT-004 treats it conservatively (see card).
- On the bootstrap path (marker placement, spec §2.4 level 2) there is
  no input TOA; TT-002/TT-003/TT-004 skip. Skipped ≠ passed: skipped
  rules emit nothing, consistent with CallLint's skip semantics.
- Diff matching is by resolved authority identity (the registry's
  `authority_id` resolution applied to the parsed input entry), not by
  string equality, so formatting differences alone never produce a
  false "missing entry."

---

## Rule index

| ID | Name | Severity | Confidence | Blocks .docx | Fixture coverage |
|---|---|---|---|---|---|
| TT-001 | Unresolvable short-form citation | error | high | no | dirty (D3, *Ellison*) |
| TT-002 | Authority missing from input TOA | info | high | no | dirty (D1, *Okafor*) |
| TT-003 | Stale page numbers in input TOA | info | high | no | dirty (D2) |
| TT-004 | Phantom input-TOA entry | warning | medium | no | **gap** — derive in tests |
| TT-005 | TOA placement not found | error | high | **yes** | **gap** — derive in tests |
| TT-006 | Marker and heading both present | warning | high | no | **gap** — derive in tests |
| TT-007 | Pagination non-convergence | error | high | no | **gap** — synthetic only |
| TT-008 | Font substitution during render | warning | high | no | environment-dependent (all fixtures under LibreOffice/Liberation) |

### Closing the fixture gaps

Recommendation: derive test inputs from existing fixtures rather than
authoring new ones —

- **TT-004:** copy `dirty_motion_brief.docx`, add a fabricated entry
  (*Nonexistent v. Authority*) to its TOA.
- **TT-005:** copy `marker_trial_memo.docx`, delete the `[[TOA]]`
  marker paragraph.
- **TT-006:** copy `dirty_motion_brief.docx`, add a `[[TOA]]` marker
  while leaving the heading-detectable TOA in place.
- **TT-007:** no realistic small fixture oscillates; unit-test the loop
  with a mocked measurer that alternates page assignments, asserting
  the cap fires and the finding names the unstable authorities.

### Expected findings per fixture (test oracle)

- `clean_appellate_brief.docx`: no findings except TT-008 when the
  render environment substitutes fonts. Tests assert "no findings other
  than TT-008."
- `dirty_motion_brief.docx`: exactly one TT-001 (*Ellison*), one TT-002
  (*Okafor*), one TT-003 (aggregated correction table covering every
  stale entry), TT-008 if substitution occurs. D4/D5 (passim and its
  threshold boundary) are generation behavior, asserted on the TOA
  itself, not findings.
- `marker_trial_memo.docx`: no findings except TT-008 as above
  (TT-002/003/004 skip on bootstrap). Second run on the output:
  identical — the idempotency assertion.

---

## Cross-rule concerns

**Independence and ordering.** Rules are independent and run in any
order. Findings are sorted for presentation: severity (error → warning
→ info), then rule ID, then document order of the subject.

**Granularity.** TT-001, TT-002, and TT-004 emit one finding per
authority (each names something requiring individual attention).
TT-003 emits one aggregated finding per run with a per-entry correction
table — page staleness is typically global, and N identical findings is
noise. TT-005 through TT-008 are inherently one-per-run.

**Skipped vs. failed.** A rule that doesn't apply (diff rules on the
bootstrap path) emits nothing. A rule that cannot evaluate due to a
parse failure emits a `warning` at `medium` confidence stating it did
not run. The report layer (Step D) must distinguish these.

---

## Deferred (credible v2 rules, explicitly not in v1)

- Pincite validation (does the pinpoint page exist within the cited
  authority's span)
- Internal cross-reference checking ("see supra Part II.B" targets)
- Bluebook signal and short-form style checking (*Id.* vs *id.*,
  italicization, signal ordering)
- Duplicate full citations of the same authority (style, not
  correctness)
- Court formatting compliance (margins, fonts, word counts per profile)
- Quotation accuracy against source text (requires source corpora —
  also a network/local-first tension to resolve before ever attempting)
- Additional court profiles beyond FRAP (SCOTUS, California, Washington,
  N.D. Cal. length threshold logic)

Listing these in the repo README keeps the v1 claim honest, same
posture as CallLint.

---

## Changelog

- 0.1.0-draft (2026-06-05): Initial Step C draft. Eight rules,
  FRAP profile v1.0.0, input-TOA diffing requirement made explicit.
