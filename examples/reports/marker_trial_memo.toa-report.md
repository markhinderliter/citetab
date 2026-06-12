# toatool report — marker_trial_memo.docx

- engine 0.1.0 · rule pack toa 1.1.0 · profile frap 1.0.0
- input: marker_trial_memo.docx (sha256 62f79748ca99…)
- render: LibreOffice 24.2.7.2 headless · fonts substituted (Consolas → DejaVu Sans Mono)
- placement: [[TOA]] marker, consumed
- pagination: converged in 1 iteration (cap 5)
- generated: 2026-06-09T12:00:00Z
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
Page locations were computed under font substitution: Consolas → DejaVu Sans Mono. Citations near page boundaries may differ by ±1 page from a render with the original fonts. If exact page fidelity matters for filing, render your final PDF and spot-check boundary entries, or install the original fonts and re-run.

- evidence: substituted fonts: Consolas → DejaVu Sans Mono · render LibreOffice 24.2.7.2
- authority: INPUT_OUTPUT_SPEC.md §3.1 (font-substitution disclosure); rules/toa/TT-008
- before filing: Install the document's declared fonts (or render where they are present) and re-run for exact page parity.
