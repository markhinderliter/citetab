---
id: TT-007
name: Pagination non-convergence
version: 1.0.0
effective_date: 2026-06-05
domain: toa
severity_default: error
confidence_default: high
blocks_docx_output: false
citations:
  - source: INPUT_OUTPUT_SPEC.md
    section: "§3.2 (regeneration loop, iteration cap)"
    description: >
      Iteration cap is 5. If pagination has not stabilized, toatool
      writes the outputs with the last computed numbers plus a
      prominent error-level finding identifying the unstable entries.
      It never loops indefinitely and never pretends convergence.
reads:
  - registry: run metadata (iteration count), per-iteration page
      assignments for each Authority
applies_when:
  - always (every run; fires only when iterations == cap without
    stabilization)
status: active
---

## Summary

The fixed-point regeneration loop hit the iteration cap (5) without two
consecutive renders agreeing on every occurrence's page. The outputs
are still written — with the last computed numbers — but the page
references for the named authorities **cannot be trusted as filed**.
The drafter must resolve the instability (or hand-verify the named
entries) before filing. Honest non-convergence beats pretended
convergence; this finding is the spec's "never pretends" clause made
visible.

## Logic

```
run the §3.2 loop (insert placeholder → measure → check, cap 5)

if not converged at cap:
    write both outputs with last computed numbers
    unstable = authorities with any occurrence whose page differed
               between the final two iterations
    emit FINDING(TT-007, error, high,
        message = "Page numbering did not stabilize within
                   {cap} iterations. {len(unstable)} entries oscillated
                   and their page references in the output may be
                   wrong: {names}. Verify these entries manually
                   before filing.",
        detail  = per unstable authority: the page values it
                  alternated between, per iteration)
```

One finding per run.

## Confidence

`high` — non-convergence is a measured fact of the renders. The
*cause* is not claimed; only the unstable entries and their observed
oscillation are reported.

## Edge cases

- **Passim-boundary oscillation.** The known plausible oscillator: an
  authority flips across the passim threshold each iteration (page list
  ⇄ "passim" changes entry length, which shifts pagination, which flips
  it back). The detail's per-iteration values make this visible; a v2
  mitigation (hysteresis: once passim, stays passim within a run) is
  noted as deferred rather than silently built in.
- **Front-matter briefs.** Cannot fire by construction (TOA length
  cannot shift body pagination); the rule costs nothing there.
- **Interaction with TT-003.** When TT-007 fires, TT-003's "corrected
  to" values are the last iteration's numbers — themselves suspect. The
  TT-003 finding in a non-converged run carries a cross-reference note.

## Non-goals

- Raising the cap or retrying with different strategies in v1.
- Diagnosing renderer behavior. The loop treats LibreOffice as an
  oracle; this rule reports when the oracle won't settle.

## Test fixtures

- **Gap — by design.** No realistic small fixture oscillates reliably,
  and a fixture that oscillates under one LibreOffice version may
  converge under another. Test the loop, not the renderer: unit-test
  with a mocked measure step that alternates page assignments for one
  authority → expect the cap to fire, outputs written, one TT-007
  naming that authority with its per-iteration values.
- All three Step B fixtures → expect: no TT-007 finding (clean and
  marker memo converge on first check; dirty within the cap).

## Changelog

- 1.0.0 (2026-06-05): Initial version.
