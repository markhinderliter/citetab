# AI Guardrails for citetab Development

citetab is built primarily with AI-assisted coding tools (Claude Code,
Codex, and similar). This document codifies the constraints those tools
must follow. It exists because AI coding tools are productive but, left
unsupervised, will wander away from the project's architectural
commitments — usually by "helpfully" adding capability the design
deliberately excludes.

These guardrails apply to every AI-generated contribution, whether the AI
is the primary author or assisting a human. They are binding.

## Non-negotiable rules

### 1. Deterministic before AI

No LLM, embedding model, or other ML inference may run anywhere in the
generation path. Citation parsing (eyecite), rendering (LibreOffice
headless), and page measurement (pdfplumber) are deterministic, and they
cover v1 entirely. The same brief must produce the same table today and a
year from now.

**Rationale:** the product thesis is that the table is correct because it
was measured, not estimated. Non-determinism would undo that.

### 2. Specification before implementation

The input/output spec, every rule card, and every court profile are the
source of truth. The implementation must match them, and the loader
validates the match at startup. When changing behavior:

1. Update the spec or rule card (logic, edge cases, citations).
2. Bump the affected version per the four-track versioning policy
   (`CHANGELOG.md`).
3. Update the Python implementation.
4. Update fixtures and expected output if behavior changed.
5. Confirm the loader still accepts the rule/profile.

Skipping step 1 or 2 is a violation.

### 3. Local-first

The engine makes no network calls during a run. None — not telemetry, not
update checks, not "fetching the latest reporters." Anything that would
touch the network must be opt-in (default off), documented in the README,
and tested with network access disabled. LibreOffice is a local system
dependency; it is not a network service.

### 4. No real documents

Synthetic fixtures only. Never commit, paste, or generate a real brief,
motion, memorandum, or any client material — not in code, not in tests,
not in issues, not "anonymized." When generating examples, use plainly
fictional parties and invented citations whose **format** is valid Bluebook
so eyecite can parse them. AI tools are especially prone to inventing
realistic-looking documents that collide with real matters; do not.

### 5. Generator framing is structural

citetab *generates* a table. Findings are disclosures around that table —
what was corrected, what to verify — never legal judgments. Every finding's
severity must answer the question "what must the user do before filing?"

- Words to use: "generated," "located," "corrected," "removed," "verify
  before filing," "disclosed," "could not determine."
- Words to avoid in any user-facing string, log line, or doc: "verifies,"
  "certifies," "guarantees," "is correct," "is complete," "is compliant,"
  "approved for filing."

A finding may state what the tool did ("located 12 authorities,"
"converged in 2 iterations"). It may not state that the brief or its
authorities are correct.

### 6. Never guess, never pretend, always disclose

These behaviors are load-bearing and must not be "improved" away:

- The input `.docx` is **never modified**; every output is a copy.
- Never insert a TOA at a guessed location. If placement cannot be
  determined, emit **TT-005**, suppress the `.docx`, and still write the
  report with the full generated table (`blocks_docx_output = true`).
- Never report convergence that did not happen. If the layout will not
  stabilize within the iteration cap, emit **TT-007** (error): the page
  numbers may be unstable and the user must know.
- Never silently delete a lawyer's TOA entry. An unmatched input entry is
  removed *and* disclosed via **TT-004** (warning).
- The TOA is written as **static formatted content, never Word TA/TOA
  field codes**. Field codes reintroduce the staleness the tool exists to
  eliminate.
- Font substitution that could move a page number is disclosed via
  **TT-008**.

### 7. Versioned everything

Engine, rule pack, individual rules, and court profiles are versioned on
four independent SemVer tracks (`CHANGELOG.md`, `rules/CHANGELOG.md`, rule
card frontmatter, profile YAML). Every finding records all four so any
report is reproducible against the exact definitions in force.

### 8. Honest scope

Deferred items stay deferred (PRD §12 and the README), not quietly built.
Features outside v1 scope — however small, however easy — are out of scope
until v1 ships.

## Strong defaults

Deviating from these requires a clear justification in the PR description.

### Python style

- Type hints on all public APIs; `mypy --strict` is enforced.
- Pydantic v2 for all data models.
- `from __future__ import annotations` at the top of every module.
- Google-style docstrings on public modules, classes, and functions.
- No `print()` in library code; use `logging`.

### Testing

- Coverage stays at or above 85%.
- Each rule has an integration test exercising the relevant fixture(s);
  rules gated by data not present in the base fixtures are tested on their
  derived fixtures (generated by a checked-in script, not committed as
  opaque binaries).
- The §20 test oracle in `docs/PRD.md` is reproduced exactly. CI runs under
  LibreOffice with Liberation substitution, so **TT-008 (warning, high) is
  expected present on every fixture run in CI**.
- Idempotency is a test, not just a promise: running citetab on its own
  output must converge immediately with no changes.

### Dependencies

The footprint stays small. A new dependency needs a reason it cannot be
done with the existing stack, evidence of maintenance, compatible licensing
(MIT/Apache-2.0/BSD), and confirmation it makes no network calls and ships
no telemetry. LibreOffice remains a **system** dependency, not a Python
one.

## Discipline for AI agents specifically

- **Implementing a rule:** read the card first; implement only what it
  describes. If the card is ambiguous, ask; do not interpret ambiguity into
  a silent design decision.
- **Spec vs. implementation disagree:** the spec is the source of truth for
  intent. Fix the implementation. If the spec is wrong, fix the spec first,
  bump the version, then the code.
- **A known reconciliation:** `INPUT_OUTPUT_SPEC.md` §3.1 and the ratified
  **TT-008** card disagree on severity. **The card governs (warning).** When
  §3.1 is next touched, patch it to "warning." Raise any *other* spec-vs-spec
  conflict instead of choosing silently.
- **Tests fail:** understand why before changing anything. Fix the wrong
  side (test or code) and say which in the commit message.
- **Out-of-v1-scope features:** don't.
- **Docs and code disagree:** update both in the same PR.

## Self-check before opening a PR

- [ ] Does every behavior change update both the spec/card and the code?
- [ ] Are version bumps consistent across all four tracks?
- [ ] Do all fixtures use synthetic data only?
- [ ] Is the deterministic-before-AI commitment intact (no ML in the
      generation path)?
- [ ] Is local-first behavior intact (no network calls during a run)?
- [ ] Does any user-facing string imply legal judgment or guaranteed
      correctness? (If yes, fix it.)
- [ ] Are TT-005 suppression, TT-007 honesty, TT-004 non-deletion, and the
      static-content rule still intact?
- [ ] Are new dependencies justified per the rules above?

## Why these guardrails exist

citetab produces an artifact that goes into court filings, where mistakes
have professional consequences. Compliance-adjacent and filing-adjacent
software has well-documented failure modes when shipping is prioritized
over correctness:

- Tools that overstate authority get used as substitutes for review, then
  miss something, then become the thing the sanctions motion points at.
- Tools that drift from their specifications stop being auditable, which
  removes their reason for existing.
- Tools that estimate page numbers instead of measuring them produce tables
  that are wrong in exactly the way this tool exists to prevent.
- Tools that send documents over the network in a confidentiality-sensitive
  domain create new exposure for their users.

These guardrails are the structural commitments that keep citetab out of
those failure modes.
