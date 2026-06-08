# toatool report — dirty_motion_brief.docx

- engine 0.1.0 · rule pack toa 1.0.0 · profile frap 1.0.0
- input: dirty_motion_brief.docx (sha256 b82d14f6a0c9…)
- render: LibreOffice 24.2 headless · fonts substituted (Liberation Serif for Times New Roman)
- placement: heading "TABLE OF AUTHORITIES"
- pagination: converged in 3 iterations (cap 5)
- generated: 2026-06-08T12:00:00Z
- findings: 1 error · 1 warning · 2 info
- output: written dirty_motion_brief.toa.docx

## Table of Authorities

### Cases

	Carmody v. Westfall Transit Auth., 512 F.3d 1042 (9th Cir. 2018)	passim
	Delgado v. Pinewood Credit Services, Inc., 487 U.S. 213 (1988)	3, 4, 5, 6, 7
	United States v. Okafor, 891 F.3d 655 (9th Cir. 2019)	4, 6

### Statutes

	15 U.S.C. § 1692e	1, 2

### Regulations

	12 C.F.R. § 1006.14	5

## Findings

### TT-001 · Unresolvable short-form citation — error (high)
A short-form reference to "Ellison" appears in the body, but no full
citation for Ellison appears anywhere in the brief, so eyecite cannot
anchor it to an authority and it cannot be placed in the Table of
Authorities. This is an error because an authority is being relied on
without a complete citation. Before filing, add the full citation for
Ellison at its first appearance, or remove the references.

- subject: Ellison, 740 F.3d (short form only)
- evidence: ¶34 p.2 "Ellison, 740 F.3d at 1133"; ¶61 p.7 "Ellison, 740 F.3d at 1136"
- authority: Bluebook Rule 10.9 (short forms); rules/toa/TT-001
- before filing: supply the full citation (e.g. *Ellison v. ___*, 740 F.3d ___ (___ Cir. ____)) at first use, then re-run.

### TT-008 · Font substitution during render — warning (high)
The document specifies Times New Roman, which is not installed in this
environment, so LibreOffice substituted Liberation Serif to render and
measure the document. Page breaks can differ from Microsoft Word's by up
to one page at the margins, which can shift a page number or a passim
boundary. Verify against your filing copy, or install the Microsoft fonts
and re-run for exact parity.

- evidence: substituted_fonts: { "Times New Roman": "Liberation Serif" }
- authority: INPUT_OUTPUT_SPEC.md §3.1; rules/toa/TT-008
- before filing: install `ttf-mscorefonts-installer` (or render where the document's fonts are present) and re-run.

### TT-002 · Authority missing from input TOA — info (high)
*United States v. Okafor*, 891 F.3d 655 (9th Cir. 2019) is cited in the
body but was absent from the document's existing Table of Authorities. It
has been added to the regenerated table at its measured pages. No action is
required beyond confirming the addition is correct.

- subject: United States v. Okafor, 891 F.3d 655 (9th Cir. 2019)
- evidence: ¶45 p.4 "United States v. Okafor, 891 F.3d 655 (9th Cir. 2019)"; ¶47 p.4 "Okafor, 891 F.3d at 661"; ¶58 p.6 "Okafor, 891 F.3d at 664"
- authority: Fed. R. App. P. 28(a)(2); rules/toa/TT-002

### TT-003 · Stale page numbers in input TOA — info (high)
The page references in the document's existing Table of Authorities did not
match the rendered document. They have been corrected from the actual
layout. The corrections:

| Authority | Input TOA | Corrected |
|---|---|---|
| Carmody v. Westfall Transit Auth. | 2, 3 | passim (6 pages) |
| Delgado v. Pinewood Credit Services, Inc. | 4 | 3, 4, 5, 6, 7 |
| 15 U.S.C. § 1692e | 1 | 1, 2 |
| 12 C.F.R. § 1006.14 | 9 | 5 |

- authority: Fed. R. App. P. 28(a)(2); rules/toa/TT-003
