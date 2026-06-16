# citetab report — dirty_motion_brief.docx

- engine 0.1.0 · rule pack toa 1.1.0 · profile frap 1.0.0
- input: dirty_motion_brief.docx (sha256 ed2fea03c9db…)
- render: LibreOffice 24.2.7.2 headless · fonts substituted (Consolas → DejaVu Sans Mono)
- placement: heading "TABLE OF AUTHORITIES"
- pagination: converged in 1 iteration (cap 5)
- generated: 2026-06-09T12:00:00Z
- findings: 1 error · 1 warning · 2 info
- output: written dirty_motion_brief.toa.docx

## Table of Authorities

### Cases

Carmody v. Westfall Transit Auth., 512 F.3d 1042 (9th Cir. 2018)	passim
Delgado v. Pinewood Credit Services, Inc., 487 U.S. 213 (1988)	2, 3, 4, 5, 6
United States v. Okafor, 891 F.3d 655 (9th Cir. 2019)	3, 4

### Statutes

15 U.S.C. § 1692e	1

### Regulations

12 C.F.R. § 1006.14	4

## Findings

### TT-001 · Unresolvable short-form citation — error (high)
Short-form citation '740 F.3d at 1133' has no full citation anywhere in the brief. It cannot be identified or placed in the Table of Authorities. Add a full citation at its first appearance and re-run.

- subject: 740 F.3d at 1133
- evidence: ¶19 p.3 "740 F.3d at 1133"; ¶26 p.4 "740 F.3d at 1136"
- authority: FRAP 28(a)(2); The Bluebook Rule 10.9 (short forms for cases); rules/toa/TT-001
- before filing: Supply the authority's full citation at first use, then re-run; until then it is omitted from the table.

### TT-008 · Font substitution during render — warning (high)
Page locations were computed under font substitution: Consolas → DejaVu Sans Mono. Citations near page boundaries may differ by ±1 page from a render with the original fonts. If exact page fidelity matters for filing, render your final PDF and spot-check boundary entries, or install the original fonts and re-run.

- evidence: substituted fonts: Consolas → DejaVu Sans Mono · render LibreOffice 24.2.7.2
- authority: INPUT_OUTPUT_SPEC.md §3.1 (font-substitution disclosure); rules/toa/TT-008
- before filing: Install the document's declared fonts (or render where they are present) and re-run for exact page parity.

### TT-002 · Authority missing from input TOA — info (high)
'United States v. Okafor, 891 F.3d 655 (9th Cir. 2019)' is cited in the body (pages 3, 4) but had no entry in the input Table of Authorities. Added.

- subject: United States v. Okafor, 891 F.3d 655 (9th Cir. 2019)
- evidence: ¶22 p.3 "891 F.3d 655"; ¶23 p.3 "891 F.3d at 661"; ¶27 p.4 "891 F.3d at 664"
- authority: FRAP 28(a)(2); rules/toa/TT-002

### TT-003 · Stale page numbers in input TOA — info (high)
3 of 4 input Table-of-Authorities entries had stale page references. Page references were recomputed from the rendered document.

- subject: 3 of 4 input TOA entries had stale page references
- evidence:

| Authority | Input TOA | Corrected |
|---|---|---|
| Carmody v. Westfall Transit Auth., 512 F.3d 1042 (9th Cir. 2018) | 2, 3 | passim |
| Delgado v. Pinewood Credit Services, Inc., 487 U.S. 213 (1988) | 4 | 2, 3, 4, 5, 6 |
| 12 C.F.R. § 1006.14 | 9 | 4 |

- authority: FRAP 28(a)(2); rules/toa/TT-003
