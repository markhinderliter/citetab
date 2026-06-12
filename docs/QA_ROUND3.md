# QA — Round 3: robustness & graceful degradation

Plan for the third QA round. Rounds 1–2 proved the tool produces the *right*
findings on *well-formed* inputs. Round 3 asks a different question: **what
happens when the input is hostile or hard?** It is the gate before any real
person drives a real document through the tool (or the desktop launcher).

## Where this sits

- **Round 1 — known-answer runs (passed).** The three committed fixtures
  reproduce their committed reports. The tool does the right thing on
  representative input.
- **Round 2 — defect injection (passed, 7/7).** One defect at a time into the
  clean fixture; each actionable rule fires exactly as specified. Caught and
  fixed a real crash on the no-placement path (TT-005 / `freeze_registry`).
- **Round 3 — robustness (this document).** Not defect-catching. The goal is
  **graceful degradation and clean rejection**: every input either fails
  cleanly or degrades honestly — and *never* dumps a stack trace.

## The bar

For **every** input in this round, exactly one of these must be true. A third
outcome — an uncaught exception / Python traceback — is always a failure.

1. **Clean rejection (Category 1).** The input is not processable. The tool
   exits **2**, prints a single `error: …` line to stderr, and writes
   **nothing**. No traceback.
2. **Graceful degradation (Category 2).** The input is valid but hard. The
   tool writes its outputs (or cleanly suppresses the `.docx` with a reason),
   and the report **honestly discloses** any limitation — `p.?` for an
   occurrence it could not place, TT-007 for non-convergence, TT-008 for font
   substitution — rather than emitting a confidently wrong page number. Exit
   code may be 0 or 1; the report is always written.

> **Why a traceback is the cardinal sin here.** Behind the desktop launcher,
> a clean exit 2 becomes a polite "couldn't process that file"; a graceful
> degradation becomes "done — review the report." A traceback becomes a wall
> of red text, or — worse — the launcher's "finished, review the report"
> message pointing at a report that was never written. The launcher can make a
> failure *polite*; it cannot make a *crash* invisible.

---

## Category 1 — malformed / non-`.docx` / non-brief → clean exit 2

Confirm unreadable inputs are rejected cleanly. The parser already validates
`is_file()` and wraps `docx.Document()` in `except Exception → ParserError`
([parser.py](../src/toatool/pipeline/parser.py)), which the CLI turns into
exit 2 — so most of these are expected green; the round is verifying that and
checking the **message quality** (a paralegal must understand it).

| Case | How to construct | Expected | Pass criteria | Result | Notes |
|------|------------------|----------|---------------|--------|-------|
| C1-a | A path that does not exist | exit 2, `error: input file '…' does not exist` | exit 2; nothing written; no traceback | | |
| C1-b | A PDF or PNG renamed `*.docx` | exit 2, `error: …not a readable .docx…` | as above | | |
| C1-c | A `.docx` truncated mid-file (valid zip header, broken body) | exit 2, ParserError | as above | | |
| C1-d | A 0-byte file named `*.docx` | exit 2, ParserError | as above | | |
| C1-e | A legacy `.doc` (OLE2) served as `*.docx` | exit 2, ParserError | as above | | |
| C1-f | A plain-text file renamed `*.docx` | exit 2, ParserError | as above | | |
| C1-g | A password-protected / encrypted `.docx` | exit 2 — **verify the message is human** (python-docx's error may be cryptic) | exit 2; message names the file and a plain reason | | |
| C1-h | A directory path instead of a file | exit 2 (`is_file()` is false) | as above | | |
| C1-i | A valid `.docx` with only images / zero text paragraphs | **characterize** — likely parses, finds no placement → TT-005 (exit 1), *not* exit 2 | no traceback; outcome documented | | |

### Scoping note — "non-brief" splits in two

The brief said "non-brief input → clean exit 2." That holds only for inputs
the tool **cannot read**. A *readable* `.docx` that simply isn't a legal brief
(a letter; a memo with no citations and no Table of Authorities) parses fine,
finds no TOA placement, and degrades to **TT-005 (error, exit 1, report
written)** — it is a Category 2 graceful-degradation outcome, not a Category 1
rejection. Round 3 records this distinction rather than forcing exit 2:

| Case | How to construct | Expected | Pass criteria | Result | Notes |
|------|------------------|----------|---------------|--------|-------|
| C1-j | A valid `.docx` of ordinary prose — no citations, no TOA, no `[[TOA]]` marker | TT-005 (no placement), exit 1, report written, `.docx` suppressed | no traceback; report explains "couldn't find where to put a TOA" | | |

---

## Category 2 — structurally hard valid briefs → graceful degradation

Feed valid briefs that stress the **measure → write → re-render → check** loop
and the page locator, and confirm the tool degrades honestly instead of
crashing or lying. This is the BL-3 genre: occurrences near page boundaries,
oscillation, and citations the locator cannot place.

### Headline risk (high confidence, from code)

> **H1 — the emitting-path `ConvergenceError` is uncaught.** The Round-2 fix
> relaxed `freeze_registry`'s missing-page guard **only on the suppressed
> (no-placement) path**. On the **emitting** path — a real brief *with* a
> placed TOA — an occurrence that becomes unmeasurable (e.g. its citation
> string splits across a page boundary) still raises `ConvergenceError`. The
> CLI catches only `ParserError`/`RenderError`, so this propagates **uncaught**
> → traceback, exit 1, **no output**. This is the exact BL-3 dead-end, and the
> most likely real-world failure: a paralegal's brief whose pagination happens
> to land a pincite on a page break. C2-a is built to trigger it; the round's
> central question is whether it does, and which fix to take.

| Case | How to construct | Expected (the bar) | Pass criteria | Result | Notes |
|------|------------------|--------------------|---------------|--------|-------|
| **C2-a** | Clean brief **with its TOA intact**, body padded with filler until a known pincite lands on a page boundary (unmeasurable) | Output written with `p.?` for that occurrence **and** a disclosure finding; exit 0/1; **no traceback** | no uncaught exception; report discloses the gap | | **Tests H1.** Likely currently FAILs (traceback) → drives the BL-3 fix |
| C2-b | A brief whose citations live in **footnotes/endnotes** | Footnote occurrences measured, or cleanly excluded with disclosure; no crash | no traceback; no silently-wrong page | | |
| C2-c | Citations inside **tables or text boxes** | Located or cleanly skipped; no crash | as above | | |
| C2-d | A **large** brief: 40+ authorities, TOA spanning multiple pages | Converges, or TT-007 if it can't; correct page lists; no crash; finishes in reasonable time | as above | | stresses convergence under bigger layout shifts |
| C2-e | One authority cited **15+ times** (passim-heavy) | Passim rendering at the profile threshold; all occurrences handled; no crash | as above | | |
| C2-f | **Page-number restart** — roman front matter then arabic body | Pages attributed correctly across the restart; no mis-mapping; no crash | as above | | stresses the locator's page map |
| C2-g | Unusual but valid placement: front-matter TOA; `[[TOA]]` marker in a memo body; heading-variant casing/spacing | Correct detection via the right path; no crash | as above | | |
| C2-h | eyecite-hard citation forms: `id.`/`supra` chains, string citations, parallel cites, nested parentheticals | Resolve or skip cleanly; genuine orphans → TT-001; no crash or silent misparse | as above | | |
| C2-i | A **real, public-domain appellate brief** (e.g. a CourtListener filing) | End-to-end graceful: output + honest disclosures | no traceback; reviewer judges report sanity | | optional/manual; do not commit large/3rd-party binaries |
| C2-j | True non-convergence (oscillation) | TT-007 (error), last-computed pages written, exit 1, no crash | as above | | real construction is impractical/non-deterministic; loop logic already covered by the mocked unit test — include only if a natural oscillator is found |

### Likely fix direction (decide from findings, not now)

If H1 reproduces, the preferred fix mirrors the project's "honest degradation
over pretended success" stance (and TT-007's design): extend `freeze_registry`
to tolerate an unmeasured occurrence on the **emitting** path too — render it
as `p.?` and attach an **info/warning disclosure finding** naming the
unplaced occurrence — rather than (a) crashing or (b) catching the error in
the CLI and rejecting the whole brief with exit 2. The brief is ~95% usable;
refusing it outright is the wrong trade. This is the substance of BL-3.

---

## How Round 3 will be run

- **Drive the real CLI as a subprocess**, not the in-process API. Round 2's
  harness called `convergence.generate()` directly, which is right for
  inspecting findings — but an uncaught `ConvergenceError` would crash the
  *harness*, not be recorded. To observe what a *user* gets, Round 3 invokes
  `toatool generate <file>` and captures `(exit_code, stdout, stderr,
  files-written)`. **A traceback in stderr is an automatic FAIL.**
- **A `scripts/qa_round3.py` harness** in two parts: (1) a rejection suite that
  generates the Category-1 inputs and asserts exit 2 + one-line stderr +
  nothing written; (2) a degradation suite that generates/loads the Category-2
  briefs and asserts the bar (output or clean suppression, honest disclosure,
  no traceback). Reuse the Round-2 scaffolding.
- **Construct fixtures, don't freeze them.** The boundary cases (C2-a, C2-f)
  are sensitive to the LibreOffice version and installed fonts, so build them
  with a generator that pads incrementally until it *detects* the target
  condition (a `None` page), as Round 2 did — not as committed binaries.
- **Summary report** `docs/QA_ROUND3_RESULTS.md`, same shape as Round 2:
  per-case verdicts, a conclusions section, and any discrepancy surfaced with
  its evidence (a traceback excerpt, not just "failed").

## Done definition

Round 3 is complete when every Category-1 case rejects cleanly (exit 2, no
traceback) and every Category-2 case degrades within the bar (output or clean
suppression, honest disclosure, no traceback) — with any failure either fixed
(like Round 2's TT-005) or explicitly accepted and documented in BACKLOG.

## Relationship to the desktop launcher

Round 3 is the real prerequisite for putting the tool in front of a paralegal.
The launcher makes a failure *polite*, but a Category-2 dead-end — "I dragged
my own brief in and it said it can't process it" — is still a dead-end the
wrapper cannot save. The sequence is: **tag v0.1.0 (done) → build the launcher
→ Round 3 (and any BL-3 fix it forces) → only then a real brief driven by a
real user.** Putting the launcher in front of someone before Round 3 risks
their first experience being a clean failure on their own document.

## Out of scope

- Performance/load testing beyond "finishes in reasonable time" on C2-d.
- Concurrency / multi-file batch runs (one brief per invocation by design).
- Adversarial/malicious documents as a security exercise (macro payloads,
  zip bombs) — a separate hardening concern, not graceful-degradation QA.
