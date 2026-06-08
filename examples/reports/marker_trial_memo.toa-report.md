# toatool report — marker_trial_memo.docx

- engine 0.1.0 · rule pack toa 1.0.0 · profile frap 1.0.0
- input: marker_trial_memo.docx (sha256 3e0b7ad9512f…)
- render: LibreOffice 24.2 headless · fonts substituted (Liberation Serif for Times New Roman)
- placement: [[TOA]] marker, consumed
- pagination: converged in 2 iterations (cap 5)
- generated: 2026-06-08T12:00:00Z
- findings: 0 error · 1 warning · 0 info
- output: written marker_trial_memo.toa.docx

## Table of Authorities

### Cases

	Carmody v. Westfall Transit Auth., 512 F.3d 1042 (9th Cir. 2018)	1, 2
	Delgado v. Pinewood Credit Services, Inc., 487 U.S. 213 (1988)	2

### Statutes

	15 U.S.C. § 1692e	1

### Regulations

	12 C.F.R. § 1006.14	2

## Findings

### TT-008 · Font substitution during render — warning (high)
The document specifies Times New Roman, which is not installed in this
environment, so LibreOffice substituted Liberation Serif to render and
measure the document. Page breaks can differ from Microsoft Word's by up to
one page at the margins. Verify against your filing copy, or install the
Microsoft fonts and re-run for exact parity.

- evidence: substituted_fonts: { "Times New Roman": "Liberation Serif" }
- authority: INPUT_OUTPUT_SPEC.md §3.1; rules/toa/TT-008
- before filing: install `ttf-mscorefonts-installer` (or render where the document's fonts are present) and re-run.

---

*Note: this memorandum had no Table of Authorities section. The `[[TOA]]`
marker placed one under the standard "TABLE OF AUTHORITIES" heading and was
consumed. A second run detects the table via that heading and converges
with zero changes — the marker bootstraps placement exactly once.*
