# toatool Example Briefs (Step B fixtures)

Three synthetic .docx briefs. All case names, parties, and citations are
fictional; citation **formats** are valid Bluebook patterns so eyecite can
parse them. No real client material appears anywhere.

These fixtures close Step B (input/output specification) and drive the
Step C rule specifications and the eventual test suite. Verified by
rendering through LibreOffice headless. The page numbers below are
**physical PDF page indices measured in this build's environment**
(LibreOffice 24.2). Because no Times New Roman or Consolas is installed
here, LibreOffice substitutes fonts — `Consolas → DejaVu Sans Mono` is the
substitution toatool discloses per spec §3.1; pages can drift ±1 versus a
Microsoft-font render, which is exactly the disclosure behavior the tool
exists to surface.

The measured tables below are kept in sync by `scripts/reconcile_fixtures.py`,
a checked-in, idempotent script that re-derives the clean fixture's TOA from a
real render and nudges the dirty fixture's *Carmody* into the passim range. Run
`python scripts/reconcile_fixtures.py --check` to verify the fixtures still match
this environment.

---

## 1. `clean_appellate_brief.docx` — the well-formed case

FRAP-style Ninth Circuit appellant's brief.

- Every authority introduced with a full citation before any short form.
- TOA heading is the standard `TABLE OF AUTHORITIES`; detection via the
  default heading path (spec §2.4 precedence level 3).
- The brief renders with continuous pagination in this environment, so a
  TOA-length change does not shift body pages and spec §3.2's regeneration
  loop converges on the **first check**.
- **TOA page numbers are real and reconciled.** The input TOA mirrors the
  registry toatool measures from a render: every authority the body cites is
  listed (including the two jurisdictional statutes), and every page list is
  the measured value. So the clean fixture is **finding-free** — the input TOA
  diffs clean against the generated TOA (no missing/stale/phantom entry).

Authorities and their measured body pages:

| Authority | Body pages |
|---|---|
| Brunner v. Caldwell, 344 P.3d 901 (Wash. 2015) | 6 |
| Carmody v. Westfall Transit Auth., 512 F.3d 1042 (9th Cir. 2018) | 3, 4, 5, 6 |
| Delgado v. Pinewood Credit Services, Inc., 487 U.S. 213 (1988) | 3, 5 |
| Hartwell Industries v. NLRB, 723 F.2d 388 (2d Cir. 1984) | 5 |
| 15 U.S.C. § 1692e | 2, 4 |
| 28 U.S.C. § 1291 | 2 |
| 28 U.S.C. § 1331 | 1 |
| 12 C.F.R. § 1006.14 | 3, 6 |
| Fed. R. App. P. 28 | 6 |

The passim boundary is exercised by the dirty fixture (D4/D5 below), not
here — clean's most-cited authority, *Carmody*, sits at four pages, well
under the five-page threshold.

**Expected toatool behavior:** detect TOA via heading; regenerate;
converge immediately; output TOA semantically identical to the input
TOA; no error/warning findings.

---

## 2. `dirty_motion_brief.docx` — the defect battery

Continuously paginated district-court summary-judgment opposition. The
(stale) TOA sits on page 1, so regenerating it can shift body pagination —
this fixture makes the §3.2 loop do real work.

Deliberate defects (page values are measured in this environment):

| # | Defect | Detail | Exercises |
|---|---|---|---|
| D1 | Missing TOA entry | *United States v. Okafor*, 891 F.3d 655 (9th Cir. 2019) is cited in the body (pages 3, 4) but absent from the TOA | body-not-in-TOA finding; the "add an entry, pages shift" scenario |
| D2 | Stale page numbers | Every TOA entry's page list is wrong (e.g., Carmody listed as "2, 3") | page-number regeneration |
| D3 | Orphan short form | *Ellison*, 740 F.3d at 1133 / at 1136 appears only in short form; no full citation exists anywhere | unresolvable-short-form finding (eyecite cannot anchor it) |
| D4 | Passim trigger | *Carmody* is cited across **6** physical pages (2–7); a trailing argument section keeps it over the threshold in this environment | entry must render as "passim" |
| D5 | Passim threshold | *Delgado* is cited on exactly **5** physical pages (2, 3, 4, 5, 6) | entry must list pages, NOT passim — boundary against D4 |
| D6 | Continuous pagination | No front-matter section; TOA length changes shift body pages | regeneration-loop iteration |

Measured authorities (this environment):

| Authority | Rendered |
|---|---|
| Carmody v. Westfall Transit Auth., 512 F.3d 1042 (9th Cir. 2018) | passim |
| Delgado v. Pinewood Credit Services, Inc., 487 U.S. 213 (1988) | 2, 3, 4, 5, 6 |
| United States v. Okafor, 891 F.3d 655 (9th Cir. 2019) | 3, 4 |
| 15 U.S.C. § 1692e | 1 |
| 12 C.F.R. § 1006.14 | 4 |

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

- `scripts/reconcile_fixtures.py` keeps the clean and dirty fixtures in
  sync with this environment's render: it rewrites the clean brief's input
  TOA from toatool's own measure step (so the fixture stays finding-free)
  and inserts the dirty brief's sixth-page *Carmody* section (so D4 renders
  passim). The script is idempotent; `--check` verifies without modifying.
- The page numbers above were measured under LibreOffice with font
  substitution (`Consolas → DejaVu Sans Mono`; `Times New Roman → Liberation
  Serif` when a brief declares TNR). Re-measuring under Microsoft fonts may
  shift pages by ±1 at the margins — which is precisely the disclosure
  behavior spec §3.1 requires of the tool itself. Treat the tables here as
  this environment's measured truth, not as cross-environment constants.
