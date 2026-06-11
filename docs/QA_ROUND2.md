# QA — Round 2: defect injection

Manual QA matrix for the defect-injection round. **No code changes** are
part of this round; it exercises shipped behavior against deliberately
broken inputs.

## Where this sits

- **Round 1 — known-answer runs (passed).** The three committed fixtures
  (`clean_appellate_brief`, `dirty_motion_brief`, `marker_trial_memo`) were
  run and their reports matched the committed `examples/reports/*`. Round 1
  confirms the tool produces the *expected* findings on representative
  inputs.
- **Round 2 — defect injection (this document).** Round 1 proves the tool
  fires on known-dirty inputs; Round 2 isolates each rule by injecting
  **one defect at a time** into a copy of the clean fixture and confirming
  exactly that rule fires (and nothing else). One defect → one expected
  finding → one expected exit code.
- **Round 3 — real documents (deferred).** Different goal entirely:
  graceful degradation and `exit 2` on garbage/unparseable input, **not**
  defect-catching. Not covered here. See "Round 3 (deferred)" below.

## Method

1. Copy the clean fixture to a scratch file:
   `cp examples/briefs/clean_appellate_brief.docx /tmp/qa2_<rule>.docx`
2. Inject **exactly one** defect (see each row).
3. Run the tool on the scratch copy and record the findings section of the
   report, the exit code (`echo $?`), and whether a `.docx` was written.
4. Fill the **Result** and **Notes** columns. A row passes when the actual
   rule, severity, and exit code match the expected columns and no *other*
   defect finding appears.

### Why the clean fixture is the injection base

`examples/briefs/clean_appellate_brief.docx` is **free of defect findings** —
no TT-001/002/003/004/005/006 fires on it. So on an injected copy, any
defect finding present is necessarily the one you injected. This is what
makes single-defect isolation clean.

### Baseline: TT-008 fires on every run

**Caveat to "any finding is the injected one":** TT-008 (font substitution)
fires on **every** run in this environment because the document's declared
`Consolas` is not installed and the renderer substitutes `DejaVu Sans
Mono`. It is a `warning` and does **not** change the exit code. Treat the
lone TT-008 warning as the **baseline**; the *injected* finding is the
delta on top of it. A row is clean when the only findings are TT-008 plus
the one expected injected finding.

### Exit-code model (for reference)

The runner derives the exit code: **`1`** if any `error` finding fired
**or** the `.docx` was suppressed, else **`0`**. The CLI adds **`2`** for
invocation/parse failures (Round 3 territory). A `warning` or `info`
finding alone never raises the exit code above `0`.

## Defect matrix

| # | Defect | How to inject | Expected rule | Expected severity | Expected exit | Result | Notes |
|---|--------|---------------|---------------|-------------------|---------------|--------|-------|
| 1 | A TOA entry is missing for an authority still cited in the body | In the input TOA, **delete one entry** whose case is still cited in the brief body (leave the body citation intact) | TT-002 (missing TOA entry) | info | 0 | | |
| 2 | A TOA entry's page number disagrees with the render | In the input TOA, **change one entry's page number** to a wrong value (e.g. `4` → `41`) | TT-003 (stale page numbers, one aggregated finding) | info | 0 | | |
| 3 | The TOA lists an authority that is never cited | **Add a TOA entry** for a case that appears nowhere in the body | TT-004 (phantom TOA entry) | warning | 0 | | |
| 4 | TOA section replaced by a placement marker (bootstrap/insertion path) | **Delete the entire TOA section** and add a `[[TOA]]` marker on its own paragraph where the TOA should go | none (insertion path; marker consumed, TOA generated) | — | 0 | | Diff rules return `applies()=False` and emit nothing — verify report shows the generated TOA and **no** defect finding |
| 5 | No TOA section and no marker — placement cannot be found | **Delete the entire TOA section** and add **no** marker (and pass no `--toa-heading`) | TT-005 (placement not found) | error | 1 | | **No `.docx` written** — confirm the primary output is suppressed |
| 6 | An orphan short form with no anchoring full citation | In the body, **write a short-form citation** (e.g. `Smith, 123 F.3d at 456`) whose full citation appears **nowhere** earlier | TT-001 (unresolvable short form) | error | 1 | | |
| 7 | Both a marker and a real TOA heading are present | Keep the existing `Table of Authorities` heading **and** also add a `[[TOA]]` marker | TT-006 (marker+heading conflict) | warning | 0 | | Marker wins; on the marker path the diff rules (TT-002/003/004) **skip** — confirm only TT-006 (+ TT-008) fire |

## Rules not hand-injected

- **TT-008 (font substitution)** — not injected; it **fires on every run**
  in this environment (see Baseline above). It is the constant against
  which the injected delta is read.
- **TT-007 (non-convergence)** — not injected; reaching the loop cap by
  hand-editing a document is impractical and non-deterministic. It is
  covered by the **mocked-measurer unit test** that forces oscillation
  past the cap. No row here.

## Round 3 (deferred)

Real-document testing is intentionally **not** part of this round. Its goal
is **graceful degradation and `exit 2` on garbage** — feeding the tool
unparseable, malformed, or non-brief `.docx` input and confirming it fails
cleanly with an invocation/parse exit code rather than crashing or emitting
a misleading report. That is a robustness goal, distinct from Round 2's
defect-catching goal, and is tracked separately.
