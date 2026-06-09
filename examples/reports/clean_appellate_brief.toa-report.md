# toatool report — clean_appellate_brief.docx

- engine 0.1.0 · rule pack toa 1.0.0 · profile frap 1.0.0
- input: clean_appellate_brief.docx (sha256 96346125243f…)
- render: LibreOffice 24.2.7.2 headless · fonts substituted (Consolas → DejaVu Sans Mono)
- placement: heading "TABLE OF AUTHORITIES"
- pagination: converged in 1 iteration (cap 5)
- generated: 2026-06-09T12:00:00Z
- findings: 0 error · 1 warning · 0 info
- output: written clean_appellate_brief.toa.docx

## Table of Authorities

### Cases

Brunner v. Caldwell, 344 P.3d 901 (Wash. 2015)	6
Carmody v. Westfall Transit Auth., 512 F.3d 1042 (9th Cir. 2018)	3, 4, 5, 6
Delgado v. Pinewood Credit Services, Inc., 487 U.S. 213 (1988)	3, 5
Hartwell Industries v. National Labor Relations Board, 723 F.2d 388 (2d Cir. 1984)	5

### Statutes

15 U.S.C. § 1692e	2, 4
28 U.S.C. § 1291	2
28 U.S.C. § 1331	1

### Regulations

12 C.F.R. § 1006.14	3, 6

### Rules

Fed. R. App. P. 28	6

## Findings

### TT-008 · Font substitution during render — warning (high)
Page locations were computed under font substitution: Consolas → DejaVu Sans Mono. Citations near page boundaries may differ by ±1 page from a render with the original fonts. If exact page fidelity matters for filing, render your final PDF and spot-check boundary entries, or install the original fonts and re-run.

- evidence: substituted fonts: Consolas → DejaVu Sans Mono · render LibreOffice 24.2.7.2
- authority: INPUT_OUTPUT_SPEC.md §3.1 (font-substitution disclosure); rules/toa/TT-008
- before filing: Install the document's declared fonts (or render where they are present) and re-run for exact page parity.
