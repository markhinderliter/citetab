# toatool report — clean_appellate_brief.docx

- engine 0.1.0 · rule pack toa 1.0.0 · profile frap 1.0.0
- input: clean_appellate_brief.docx (sha256 7f3a9c21b4e0…)
- render: LibreOffice 24.2 headless · fonts substituted (Liberation Serif for Times New Roman)
- placement: heading "TABLE OF AUTHORITIES"
- pagination: converged in 1 iteration (cap 5)
- generated: 2026-06-08T12:00:00Z
- findings: 0 error · 1 warning · 0 info
- output: written clean_appellate_brief.toa.docx

## Table of Authorities

### Cases

	Brunner v. Caldwell, 344 P.3d 901 (Wash. 2015)	6, 7
	Carmody v. Westfall Transit Auth., 512 F.3d 1042 (9th Cir. 2018)	2, 3, 4, 5, 6
	Delgado v. Pinewood Credit Services, Inc., 487 U.S. 213 (1988)	3, 5
	Hartwell Industries v. NLRB, 723 F.2d 388 (2d Cir. 1984)	4

### Statutes

	15 U.S.C. § 1692e	1, 4

### Regulations

	12 C.F.R. § 1006.14	3, 6

### Rules

	Fed. R. App. P. 28	7

## Findings

### TT-008 · Font substitution during render — warning (high)
The document specifies Times New Roman, which is not installed in this
environment, so LibreOffice substituted Liberation Serif to render and
measure the document. Liberation Serif is metric-compatible, but page
breaks can differ from Microsoft Word's by up to one page at the margins.
Verify the page numbers against your filing copy, or install the Microsoft
fonts and re-run for exact parity.

- evidence: substituted_fonts: { "Times New Roman": "Liberation Serif" }
- authority: INPUT_OUTPUT_SPEC.md §3.1; rules/toa/TT-008
- before filing: install `ttf-mscorefonts-installer` (or render where the document's fonts are present) and re-run to confirm pagination.

---

*Note: this brief uses separately paginated front matter, so the
regeneration loop converged on the first check. The Table of Authorities
above is semantically identical to the one already in the document. In a
Times New Roman environment this run produces no findings at all.*
