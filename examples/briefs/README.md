# toatool Example Briefs (Step B fixtures)

Three synthetic .docx briefs. All case names, parties, and citations are
fictional; citation **formats** are valid Bluebook patterns so eyecite can
parse them. No real client material appears anywhere.

These fixtures close Step B (input/output specification) and drive the
Step C rule specifications and the eventual test suite. Verified by
rendering through LibreOffice headless (Liberation Serif substituted for
Times New Roman in this environment — the same substitution toatool
discloses per spec §3.1).

---

## 1. `clean_appellate_brief.docx` — the well-formed case

FRAP-style Ninth Circuit appellant's brief. 10 physical pages.

- Separately paginated front matter (cover/caption, table of contents,
  Table of Authorities) in lower-roman numerals; body restarts at
  arabic 1. This is the layout where spec §3.2's regeneration loop
  converges on the first check by construction.
- Every authority introduced with a full citation before any short form.
- TOA heading is the standard `TABLE OF AUTHORITIES`; detection via the
  default heading path (spec §2.4 precedence level 3).
- **TOA page numbers are real.** They were produced by rendering the
  document and locating every occurrence — a hand-run of toatool's own
  measure step — then written back and re-verified by a second render
  with zero page movement.

Boundary case included: *Carmody* is cited on exactly **5** body pages —
at the passim threshold, so it lists pages, not "passim."

Authorities and their true body pages:

| Authority | Body pages |
|---|---|
| Carmody v. Westfall Transit Auth., 512 F.3d 1042 (9th Cir. 2018) | 2, 3, 4, 5, 6 |
| Delgado v. Pinewood Credit Services, Inc., 487 U.S. 213 (1988) | 3, 5 |
| Hartwell Industries v. NLRB, 723 F.2d 388 (2d Cir. 1984) | 4 |
| Brunner v. Caldwell, 344 P.3d 901 (Wash. 2015) | 6, 7 |
| 15 U.S.C. § 1692e | 1, 4 |
| 12 C.F.R. § 1006.14 | 3, 6 |
| Fed. R. App. P. 28 | 7 |

**Expected toatool behavior:** detect TOA via heading; regenerate;
converge immediately; output TOA semantically identical to the input
TOA; no error/warning findings.

---

## 2. `dirty_motion_brief.docx` — the defect battery

Continuously paginated district-court summary-judgment opposition.
8 physical pages; the (stale) TOA sits on page 1, so regenerating it can
shift body pagination — this fixture makes the §3.2 loop do real work.

Deliberate defects:

| # | Defect | Detail | Exercises |
|---|---|---|---|
| D1 | Missing TOA entry | *United States v. Okafor*, 891 F.3d 655 (9th Cir. 2019) is cited in the body (pages 4, 6) but absent from the TOA | body-not-in-TOA finding; the "add an entry, pages shift" scenario |
| D2 | Stale page numbers | Every TOA entry's page list is wrong (e.g., Carmody listed as "2, 3") | page-number regeneration |
| D3 | Orphan short form | *Ellison*, 740 F.3d at 1133 / at 1136 appears only in short form; no full citation exists anywhere | unresolvable-short-form finding (eyecite cannot anchor it) |
| D4 | Passim trigger | *Carmody* is cited on **6** body pages (2, 4, 5, 6, 7, 8) | entry must render as "passim" |
| D5 | Passim threshold | *Delgado* is cited on exactly **5** body pages (3, 4, 5, 6, 7) | entry must list pages, NOT passim — boundary against D4 |
| D6 | Continuous pagination | No front-matter section; TOA length changes shift body pages | regeneration-loop iteration |

**Expected toatool behavior:** detect TOA via heading; regenerate with
Okafor added, all page numbers corrected, Carmody as passim, Delgado as
a page list; converge within the iteration cap; emit findings for D1
(entry was missing) and D3 (orphan short form, cannot be placed in the
TOA — flagged for human review).

---

## 3. `marker_trial_memo.docx` — the bootstrap case

Two-page King County Superior Court memorandum with **no TOA section at
all** — the trial-court pattern that motivated the marker mechanism
(spec §2.4). A `[[TOA]]` marker sits on its own paragraph between the
caption and the introduction.

Citations: 15 U.S.C. § 1692e; Carmody (full + one short form);
Delgado; 12 C.F.R. § 1006.14.

**Expected toatool behavior:** detect placement via the marker (spec
precedence level 2); consume the marker; insert a generated TOA under
the standard heading. A second run on the output must detect via the
heading path and converge with zero changes — the marker-to-heading
handoff that preserves idempotency.

---

## Regeneration notes

- `generate.js` + `content.js` produce all three briefs;
  `measure.py` performs the render-and-locate pass that supplies the
  clean brief's accurate TOA page numbers (`clean_toa_pages.json`).
- Page-location numbers above were measured under LibreOffice with
  Liberation font substitution. Re-measuring under MS fonts may shift
  pages by ±1 at the margins — which is precisely the disclosure
  behavior spec §3.1 requires of the tool itself.
