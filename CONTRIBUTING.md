# Contributing to citetab

Thanks for your interest. citetab is a small, disciplined project; the
discipline is most of what makes it trustworthy. Contributions that
respect the constraints below are very welcome.

## The one absolute rule: no real documents

Never commit, attach, or paste a real brief, motion, memorandum, or any
client material — not in code, not in tests, not in issues, not
"anonymized." Real legal documents carry confidentiality and
work-product implications that this repository must never touch.

All fixtures are synthetic: fictional parties, fictional case names,
invented docket numbers, and citation **formats** that are valid
Bluebook patterns pointing at invented reporters' pages. The three
example briefs in `examples/` show the pattern; `tests/fixtures/`
derives from them. If you need a new fixture, write fiction.

Issues containing real documents will be deleted, not redacted.

## Before you change behavior: spec first

Every behavior in this tool is specified somewhere — the input/output
contract (`docs/INPUT_OUTPUT_SPEC.md`), a rule card (`rules/TT-*.md`),
a court profile (`profiles/*.yaml`), or the report spec
(`docs/REPORT_SPEC.md`). The implementation must match the spec, and
the loader validates rule cards against implementations at startup.

To change behavior:

1. Update the spec or rule card (logic, edge cases, citations)
2. Bump the relevant version per the policy in `CHANGELOG.md`
3. Update the implementation
4. Update test fixtures and expected outputs if behavior changed
5. Confirm the loader still accepts everything

Spec and implementation change in the same PR, always. Drift between
documentation and code is the failure mode this process exists to
prevent.

## Adding or changing court profiles

Court profiles are the most welcome kind of contribution — formatting
conventions vary by jurisdiction and the v1 set is small. A profile PR
needs:

- The profile YAML with a version and effective date
- Citation to the court rule or standing order it encodes (rule number
  and a link to the official text)
- A synthetic fixture exercising any convention that differs from frap
  (heading variants, grouping, passim threshold)

"Common practice in my jurisdiction" is a fine motivation but not a
citation; profiles encode written requirements, with practice notes in
comments where the written rule is silent.

## Code standards

- Python 3.11+, type hints on all public APIs, `mypy --strict` enforced
- Pydantic v2 for data models; `from __future__ import annotations`
- `ruff check` and `ruff format` clean
- Docstrings on public modules/classes/functions, Google style
- `logging`, never `print()`, in library code
- Tests for every change; coverage stays at or above 85%

## Dependency policy

The footprint stays small. A new dependency needs: a reason it can't
reasonably be done with the existing stack, evidence of maintenance,
compatible licensing (MIT/Apache-2.0/BSD), and confirmation it makes no
network calls and ships no telemetry. LibreOffice remains a system
dependency, not a Python one.

## AI-assisted contributions

Welcome, and held to exactly the same standards — plus the constraints
in `docs/AI_GUARDRAILS.md`, which are binding for AI-generated code
whether the AI is the primary author or assisting you. The short
version: no LLM calls at generation time, no network calls during a
run, no page-estimation heuristics in place of real rendering, no Word
field codes in output, synthetic fixtures only, spec before code.

## Reporting bugs

Use the issue template. Include tool/rule-pack/profile versions (top of
any report), a synthetic reproduction, and expected behavior. For wrong
TOA output, the report file itself (generated from a synthetic brief)
is the most useful attachment.

## Conduct

Be professional and assume good faith. This project serves people doing
underpaid, deadline-driven work; keep discussions respectful of
everyone's time.
