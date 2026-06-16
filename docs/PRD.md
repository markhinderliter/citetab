# citetab Project Launch / Control Document

## 1. Project Name

**citetab** (working name)

The placeholder is deliberate. The real name is decided at v0.5 launch
prep; candidate names from the design phase (Cantica, Cantique) remain
on the shortlist for that decision. Nothing in this document or the
codebase should hard-couple to the placeholder in a way that makes the
rename expensive: the rename touches `pyproject.toml`, the CLI entry
point, the repo name, and user-facing strings — and nothing else.

## 2. One-Line Description

A free, local-first command-line tool that generates a court-rule-
compliant Table of Authorities for a legal brief, with page numbers
measured from a real render of the actual document — so the TOA works
the way Word's table of contents does: it just updates.

## 3. Product Thesis

Every appellate brief, and many trial-court briefs, must carry a Table
of Authorities: an indexed list of every case, statute, regulation,
constitutional provision, and rule cited, with the page numbers of the
brief where each appears. FRAP 28(a)(2) mandates it federally; state
appellate rules require the equivalent.

Building that table is miserable in exactly the way building a table of
contents used to be. Word's native TA/TOA field mechanism requires
hand-marking every citation, breaks when the document is edited, and is
so unpleasant that the dominant real-world workflow is a paralegal
manually finding every citation, typing the table by hand, and then
re-verifying every page number each time the brief changes — which it
does, repeatedly, right up to the filing deadline. The page numbers go
stale the moment anyone touches the document. This is the core user
pain, stated verbatim by the user research that drove this project: the
TOA should behave like Word's table of contents.

The commercial solutions are real but mispriced or misplaced for a
large slice of the profession:

- **Best Authority** (the incumbent desktop tool) is licensed at
  BigLaw price points and is fragile on re-runs — regenerating after an
  edit is exactly where it falls down, per direct user experience.
- **ezBriefs and TypeLaw** are cloud SaaS: the brief is uploaded to
  someone else's servers. For many practitioners that is a
  confidentiality non-starter before price is even discussed, and the
  user research captured this objection unprompted ("I don't want to
  upload my brief").
- **Word's manual workflow** is free and universally despised.

The open-source side is effectively empty. eyecite (Free Law Project)
is an excellent open-source citation parser, but nothing sits above it
as a TOA *generator* that takes a .docx, measures real page locations,
and writes the table back.

**citetab exists to be that missing layer.**

Positioning, verbatim: *"The free local alternative to ezBriefs and
TypeLaw, because your client's brief shouldn't have to live on someone
else's servers."*

It is not a citation checker, not a Bluebook style enforcer, not a
brief-formatting suite, and not legal advice. It is a generator with
disclosures: a .docx goes in, a .docx with a correct TOA comes out,
and a findings report explains every correction the tool made and every
caveat the user should know before filing.

## 4. Career / Portfolio Thesis

This is the second project built on the design pattern established by
CallLint: spec-first design, versioned rule definitions, deterministic
logic, structured findings, local-first by default, AI-assisted
implementation against human-ratified specifications.

Where CallLint demonstrated the pattern once, citetab demonstrates that
the pattern is *portable* — roughly 70% of the CallLint design package
transferred directly (finding/severity/confidence semantics, versioning
policy, rule-card format, guardrails for AI-assisted development,
liability posture), while the remaining 30% required a genuinely
different architectural decision: citetab is a generator, not a linter,
and the design package documents how the pattern bends to accommodate
that without breaking.

The portfolio statement this project makes:

> "I can identify an underserved niche in a regulated domain, design a
> defensible tool against written specifications, reuse a proven design
> system across domains, and direct AI coding tools to implement it
> under explicit guardrails — twice."

## 5. Target Users

The tier below where commercial legaltech SaaS is priced:

- **Solo practitioners** who do their own TOAs at 11pm
- **Small-firm paralegals** — Cheryle is the named persona: Best
  Authority experience, court-template and page-numbering pain, and the
  "it should act like a Word TOC" framing came from her feedback
- **Legal aid attorneys and public defenders**, whose offices will
  never buy a five-figure tool and whose briefs are exactly as
  confidential as BigLaw's
- **Law school clinics**, where the tool doubles as a teaching artifact
  (the rule cards cite FRAP and the Bluebook)

Secondary audience: legaltech-curious developers, because the tool is
open source and the eyecite ecosystem is small enough that a useful
downstream tool gets noticed.

## 6. Problem Statement

A Table of Authorities is a derived artifact: it is a function of the
document's citations and the document's pagination. Lawyers maintain it
by hand, so it drifts from the document it describes. The drift has
three concrete failure modes, all represented in the dirty fixture:

1. **Missing entries** — an authority cited in the body never made it
   into the table (fixture defect D1, *Okafor*)
2. **Stale page numbers** — the table's page references describe an
   older layout of the document (D2; the core pain)
3. **Phantom entries** — the table lists an authority the body no
   longer cites, typically a remnant of a deleted argument section
   (derived fixture for TT-004)

A fourth failure mode lives in the brief itself rather than the table:
a short-form citation with no antecedent full citation (D3, *Ellison*),
which makes the authority impossible to index correctly and is a
drafting error under Bluebook Rule 10.9.

The structural reason the problem persists: a .docx file does not
contain page numbers. Pages exist only at render time. Any tool that
promises correct page references must actually lay the document out —
and because the TOA is part of the document it describes, writing the
table can change the pagination it reports. Solving that honestly
(rather than approximately) is the technical heart of this project.

## 7. Solution Statement

citetab ingests a .docx brief and:

1. **Parses** the document (python-docx) and **extracts** every
   citation in every form — full, short, *supra*, *id.*, *ibid.* —
   using eyecite, resolving every reference form back to its authority
2. **Builds** the complete TOA per a versioned court profile (FRAP
   default): grouped, sorted, passim-thresholded, formatted
3. **Inserts** it at a deterministically detected placement (explicit
   flag → `[[TOA]]` marker → default heading variants → refuse to
   guess)
4. **Renders** the document via LibreOffice headless to PDF and
   **locates** every citation occurrence on its actual page
   (pdfplumber)
5. **Iterates to a fixed point**: re-render until no occurrence's page
   changes, capped at 5 iterations with honest failure disclosure
6. **Writes** a copy of the brief with the corrected TOA as static
   formatted content (never field codes, never in-place modification)
   plus a Markdown report that leads with the generated table and
   follows with findings

Everything runs locally. No network calls during a run, no telemetry,
no LLM calls at generation time. Running citetab on its own output
converges immediately with zero changes — idempotency is both the
product promise and a built-in self-test.

## 8. Guiding Principles

These are structural commitments, not preferences. They appear in the
custom instructions, the input/output spec (§6), AI_GUARDRAILS.md, and
here, deliberately redundantly, so no AI-assisted contribution can miss
them.

### 8.1 Generator first; findings are disclosures

This is the load-bearing difference from CallLint. CallLint was a
linter: rules *were* the product. citetab's product is the regenerated
TOA; findings exist to make the tool's corrections and caveats
unmissable. Severity therefore answers the question *"what must the
user do before filing?"* — not "how bad is the violation":

| Severity | Meaning | User action |
|---|---|---|
| `error` | Output is incomplete or unreliable; the regenerated TOA cannot be trusted as filed | Fix the brief (or placement) and re-run, or manually complete the TOA |
| `warning` | Output produced and usable, but something should be verified | Review the named item before filing |
| `info` | A correction the tool made, disclosed for trust and audit | None; informational record of the delta |

User-facing language follows: the tool "corrected," "disclosed,"
"could not place" — never "violation," "non-compliant brief," or any
phrasing implying authoritative legal judgment.

### 8.2 Deterministic before AI

No LLM, embedding model, or other ML inference in the generation path
in v1. eyecite is a deterministic parser; LibreOffice is a
deterministic renderer; the rules are pattern and structure
comparisons. A TOA generated today must be reproducible byte-for-byte
a year from now from the same input and versions.

### 8.3 Local-first, absolutely

Briefs are confidential client material. No network calls during a
run. No telemetry. No update checks. This is the positioning sentence
made architecture: the brief never leaves the user's machine.

### 8.4 Never guess, never pretend, always disclose

Three expressions of one principle:

- **Never guess a placement.** If no placement mechanism matches, the
  .docx output is suppressed (TT-005) rather than inserted somewhere
  plausible. This is a legal filing; a TOA in the wrong place is worse
  than no TOA.
- **Never pretend convergence.** If pagination doesn't stabilize within
  the iteration cap, outputs are written with the last numbers plus an
  error finding naming the unstable entries (TT-007).
- **Always disclose render caveats.** Font substitution can shift
  marginal citations ±1 page versus a Word render; when it happens, the
  user is told (TT-008).

### 8.5 Specification before implementation

The input/output spec, the rule cards, the court profiles, and the
report spec are the source of truth. The rule loader validates cards
against implementations at startup; spec drift fails loudly. Spec and
implementation change in the same PR, always.

### 8.6 No real documents, ever

All fixtures are synthetic: fictional parties, fictional case names,
invented docket numbers, citation *formats* that are valid Bluebook
patterns pointing at invented reporters' pages. Issues containing real
documents are deleted, not redacted (CONTRIBUTING.md).

## 9. Initial MVP Scope

### MVP target

**Engine v0.1.0**: the full generation pipeline for a single brief,
the **toa rule pack v1.0.0** (eight rules, TT-001 through TT-008), and
the **frap court profile v1.0.0**.

### Why these eight rules

Together they exercise every code path the engine needs:

- **TT-001 (unresolvable short form)** — exercises eyecite resolution
  output handling (anchored vs. unanchored clusters); the one v1 rule
  about the brief itself rather than the table
- **TT-002 (missing input-TOA entry)** — exercises the input-TOA diff
  baseline on the "body has it, table doesn't" axis
- **TT-003 (stale page numbers)** — the product thesis as a finding;
  exercises diff page-list comparison and per-run aggregation (one
  finding with a correction table, not N findings)
- **TT-004 (phantom entry)** — the diff's other axis ("table has it,
  body doesn't"); exercises medium-confidence semantics and
  conservative handling of unparsed input entries
- **TT-005 (placement not found)** — exercises the only
  `blocks_docx_output: true` path and the report-only output mode
- **TT-006 (marker/heading conflict)** — exercises multi-mechanism
  placement detection reporting (all matches, not just the winner)
- **TT-007 (non-convergence)** — exercises the iteration cap and
  run-metadata-driven findings
- **TT-008 (font substitution)** — exercises render-environment
  introspection and environment-dependent test assertions

### Severity reconciliation note

Spec §3.1 (Step B) described font substitution as an *info*-level
finding. The ratified TT-008 card (Step C) sets `severity_default:
warning`, with reasoning recorded in the card: it qualifies the
accuracy of the tool's core output. **The rule card governs.** When
INPUT_OUTPUT_SPEC.md is next touched, §3.1 should be patched to say
"warning"; until then this paragraph is the recorded reconciliation.

### MVP version targets

- **Engine:** 0.1.0
- **Rule pack (toa):** 1.0.0
- **All eight rules:** 1.0.0
- **frap profile:** 1.0.0

## 10. MVP User Story

As a paralegal at a four-attorney firm finalizing an appellate brief
two hours before the filing deadline, I want to run one command against
the latest .docx and get back a copy with a complete, correctly
paginated Table of Authorities plus a short report of everything the
tool changed, so that the table is no longer the thing standing between
the final edit and the courthouse — and so that I never have to upload
the brief to anyone's server to get that.

## 11. MVP Functional Requirements

Each FR cites its normative source. Where this document and a cited
spec disagree, the spec governs (Principle 8.5).

### FR-01: Input acceptance and defensive parsing
*Source: INPUT_OUTPUT_SPEC.md §2.1–2.2*

Accept any structurally valid .docx; require nothing else (no PDF, no
authoring conventions, no Word installation). Malformed input fails
loudly with a message naming the file and the failure; never partially
process.

**Acceptance:** all three example briefs parse; a truncated/corrupt
.docx produces a clear non-zero-exit error, no outputs.

### FR-02: Placement detection with strict precedence
*Source: INPUT_OUTPUT_SPEC.md §2.4*

First match wins: (1) `--toa-heading` flag → (2) `[[TOA]]` marker on
its own paragraph, consumed on use → (3) versioned default heading
variants from the court profile, case-insensitive and
whitespace-tolerant, replacement region extending to the next heading
of same-or-higher level → (4) nothing found: do **not** guess; emit
TT-005, suppress the .docx output, still write the report with the
full generated TOA. Marker + heading both present → marker wins,
heading region untouched, TT-006 emitted. Citation-density heuristics
are rejected by spec and must not be implemented.

**Acceptance:** clean and dirty fixtures detect via heading; marker
memo detects via marker and consumes it; derived no-marker memo
triggers TT-005 with no .docx written; derived marker+heading fixture
triggers TT-006 with the heading region byte-identical to input.

### FR-03: Citation extraction and resolution
*Source: INPUT_OUTPUT_SPEC.md §3, §4.2*

Extract every citation occurrence via eyecite — full, short, supra,
id., ibid. — and resolve every reference form to its authority.
Unresolvable short-form clusters produce TT-001 (one finding per
authority) and are excluded from the TOA, flagged for human review.

**Acceptance:** dirty fixture yields exactly one TT-001 (*Ellison*);
every other occurrence in all fixtures resolves; marker memo's Carmody
short form resolves to its full citation.

### FR-04: Citation Registry as the canonical model
*Source: INPUT_OUTPUT_SPEC.md §4*

The pipeline produces one Citation Registry per run — Authorities (with
type, normalized components, display forms, sort key, group, pages,
passim flag), Occurrences (form, raw text, paragraph index, char span,
page, optional pincite, confidence), and run metadata (tool version,
profile id+version, render engine identity/version, font-substitution
detail, iteration count, input file hash). Every output is a rendering
of the registry. The registry is formalized during the build as
`schemas/registry.schema.json` plus a matching Pydantic model; the
shape in spec §4 is normative.

**Acceptance:** schema and model cross-validate; a serialized registry
from any fixture run validates against the schema.

### FR-05: Input-TOA diff baseline
*Source: RULES_README.md "Derived requirement"*

Before replacing a heading-detected TOA region, parse its existing
entries best-effort into (authority, pages) pairs. Matching is by
resolved authority identity, never string equality. Unparseable
entries are recorded as unparsed: excluded from TT-002/TT-003,
treated conservatively by TT-004 per its card. On the marker bootstrap
path there is no baseline: TT-002/003/004 skip, and skipped rules emit
nothing (skipped ≠ passed).

**Acceptance:** dirty fixture yields one TT-002 (*Okafor*) and one
aggregated TT-003 covering every stale entry; marker memo yields
neither; formatting-only differences in input entries produce no
false TT-002/TT-004.

### FR-06: TOA construction per court profile
*Source: frap-profile.yaml; INPUT_OUTPUT_SPEC.md §2.3*

Grouping (cases / constitutional / statutes / regulations / rules /
other), within-group alphabetical sort by sort key, passim rendering
(MORE than `threshold_pages` distinct pages → "passim"; exactly the
threshold lists pages), dot leaders, right-aligned page numbers,
italicized case names, no pincites in the TOA, empty groups omitted —
all read from the profile YAML. Nothing about grouping, ordering,
passim, or headings is hardcoded. `--court` selects the profile;
default `frap`.

**Acceptance:** dirty fixture renders Carmody (6 pages) as "passim"
and Delgado (exactly 5 pages) as a page list; clean fixture renders
Carmody (exactly 5 pages) as a page list; groups appear in profile
order with profile labels.

### FR-07: Local render and page location
*Source: INPUT_OUTPUT_SPEC.md §3.1*

Render the working copy via LibreOffice headless to PDF; extract
per-page text and positions via pdfplumber; locate every occurrence.
Exact text-span matches are `high` confidence; approximated locations
are `medium`. Any font substitution reported by the render emits
TT-008 (warning) with the substitution pairs in run metadata.

**Acceptance:** the clean fixture's documented authority→pages table
is reproduced exactly under the LibreOffice/Liberation environment;
all fixture occurrences locate at high confidence.

### FR-08: Fixed-point regeneration loop
*Source: INPUT_OUTPUT_SPEC.md §3.2*

Parse once; build and insert the full TOA once (absorbing the large
length perturbation in one step); then measure → write numbers →
re-render → check, repeating only the check phase until no
occurrence's page changes. Iteration cap: 5. On cap without
stability: write outputs with the last numbers plus TT-007 naming the
unstable authorities. Passim flips between iterations are ordinary
perturbations the check catches. Front-matter briefs (separately
paginated TOA) converge on the first check by construction with no
special-casing.

**Acceptance:** clean fixture converges on the first check; dirty
fixture (continuous pagination, entry added) converges within the cap;
mocked oscillating measurer hits the cap and produces TT-007 naming
the oscillating authorities, with outputs still written.

### FR-09: Output writing
*Source: INPUT_OUTPUT_SPEC.md §5*

Always a copy — the input is never modified. Default
`{input_stem}.toa.docx`, `--output` overrides. Only the placement
region is replaced; all other content, styles, and formatting pass
through untouched. The TOA is static formatted content, never Word
TA/TOA field codes. The Markdown report
(`{input_stem}.toa-report.md`, written alongside) leads with the
generated TOA, then findings, per docs/REPORT_SPEC.md (Step D), which
is the authoritative layout and finding-format specification.

**Acceptance:** input file hash unchanged after every run; non-TOA
document XML semantically unchanged; report structure matches the
Step D rendered examples.

### FR-10: Findings engine
*Source: the eight TT rule cards; docs/REPORT_SPEC.md*

Rules are independent and order-insensitive. Presentation sort:
severity (error → warning → info), then rule ID, then document order.
Granularity per RULES_README: TT-001/002/004 one finding per
authority; TT-003 one aggregated finding per run; TT-005–008 one per
run. A rule that cannot evaluate due to a parse failure emits a
warning at medium confidence stating it did not run — distinct from
skipped, and the report renders the distinction. Every finding records
engine, rule, rule-pack, and profile versions.

**Acceptance:** the full test-oracle table in §20 is reproduced
exactly.

### FR-11: CLI
*Source: INPUT_OUTPUT_SPEC.md §2.3, §5.3; CallLint UX pattern*

Single brief per invocation. Click-based:

```
citetab generate BRIEF.docx [--court PROFILE] [--toa-heading TEXT] [--output PATH]
citetab rules list
citetab rules show TT-001
citetab profiles list
citetab profiles show frap
```

Exit codes: 0 = success (info/warning findings allowed); 1 = error
findings present or .docx output suppressed (TT-005, TT-007 paths);
2 = invocation/parse failure. The iteration cap is fixed at 5 by spec
and is deliberately not a flag.

**Acceptance:** `rules show` renders the card content; exit codes
verified per fixture in the end-to-end tests.

### FR-12: Idempotency
*Source: INPUT_OUTPUT_SPEC.md §3.3*

Same input → same output, every run. Running citetab on its own output
converges immediately with zero changes. The marker-to-heading handoff
preserves this: a marker bootstraps placement exactly once; the
generated TOA carries the standard heading, so re-runs detect via the
heading path.

**Acceptance:** double-run test on every fixture: second run's outputs
are identical to the first's (after masking run-scoped metadata) and
report iteration count 1 with zero changes.

## 12. Explicit Non-Goals for MVP

Deferred, per RULES_README and spec §5.3 — listed in the repo README to
keep the v1 claim honest:

- **Batch mode.** One brief per invocation; no batch summary artifacts.
  (CallLint's `_batch.md`/`_batch.json` pattern does not transfer.)
- **Court profiles beyond FRAP** (SCOTUS, California, Washington,
  N.D. Cal. length-threshold logic). The profile format is built for
  them; the data is not v1 work.
- **Pincite validation** (does the pinpoint exist in the authority)
- **Internal cross-reference checking** ("see supra Part II.B")
- **Bluebook signal/short-form style checking** (*Id.* vs *id.*,
  italicization, signal ordering)
- **Duplicate-full-citation detection** (style, not correctness)
- **Court formatting compliance** (margins, fonts, word counts)
- **Quotation accuracy against source text** — also a network /
  local-first tension that must be resolved before ever attempting
- **Word TA/TOA field-code emission** — rejected by design, not
  deferred
- **GUI, Word add-in, real-time anything, PDF input**
- **LLM-assisted anything at generation time**

## 13. Privacy / Local-First Positioning

The positioning sentence is the architecture: the brief never leaves
the machine. Concretely:

- No network calls during a run — enforceable by inspection and by a
  test that runs the pipeline with networking monitored
- No telemetry, no update checks, no crash reporting
- LibreOffice is invoked as a local subprocess; pdfplumber reads the
  local PDF; eyecite is a local library
- The findings report is a local file; nothing is "shared"
- The marketing claim ("shouldn't have to live on someone else's
  servers") is verifiable by any user reading the code — which is the
  point of it being open source

This posture is also why the tool can be recommended inside
legal-aid and public-defender offices with strict confidentiality
rules: there is no data-processing relationship to paper.

## 14. Recommended Tech Stack

| Layer | Choice | Why |
|---|---|---|
| Language | Python 3.11+ | eyecite's ecosystem; matches CallLint; mypy --strict viable |
| Citation parsing | eyecite ≥ 2.6 | The only serious open-source citation parser; Free Law Project provenance is itself a trust signal |
| .docx read/write | python-docx ≥ 1.1 | Mature, no Word dependency |
| Rendering | LibreOffice headless | **System dependency, not pip-installable.** Documented in README "System requirements"; the CLI fails with a clear message if `libreoffice` is absent |
| PDF measurement | pdfplumber ≥ 0.11 | Per-page text with positions; pure Python |
| Models | pydantic ≥ 2.7 | Registry + Finding models; schema cross-validation |
| Schemas | jsonschema ≥ 4.21 | Validate serialized registry/findings against canonical schemas |
| Rule/profile data | PyYAML ≥ 6.0 | Cards' frontmatter and court profiles |
| CLI | click ≥ 8.1 | Matches CallLint |
| IDs | python-ulid ≥ 2.2 | Sortable finding/run IDs |
| Quality | pytest, pytest-cov, ruff, mypy --strict | Gates identical to CallLint |

**Correction to apply during build:** the Step E `pyproject.toml` omits
`pdfplumber` from `[project.dependencies]` even though spec §3 requires
it. Add `pdfplumber>=0.11` as the first build-phase commit touching
pyproject. Everything else in the Step E pyproject stands, including
the bundled-data wheel configuration (rules, profiles, and schemas ship
inside the wheel so `pip install citetab` works without a clone).

## 15. Proposed Architecture

### Repository layout

```
citetab/                                ← repo root
├── README.md                           ← Step E
├── LIABILITY.md                        ← Step E
├── LICENSE                             ← Step E (MIT + additional notice)
├── CHANGELOG.md                        ← Step E (four versioning tracks)
├── CONTRIBUTING.md                     ← Step E
├── pyproject.toml                      ← Step E (+ pdfplumber fix, §14)
├── .gitignore
│
├── docs/
│   ├── PRD.md                          ← this document (Step F)
│   ├── INPUT_OUTPUT_SPEC.md            ← Step B (normative)
│   ├── REPORT_SPEC.md                  ← Step D (normative)
│   ├── AI_GUARDRAILS.md                ← Step E
│   └── ARCHITECTURE.md                 ← generated during build
│
├── rules/
│   ├── README.md                       ← Step C (RULES_README)
│   ├── CHANGELOG.md                    ← rule-pack version track
│   └── toa/
│       ├── TT-001-unresolved-short-form.md
│       ├── TT-002-missing-toa-entry.md
│       ├── TT-003-stale-page-numbers.md
│       ├── TT-004-phantom-toa-entry.md
│       ├── TT-005-toa-placement-not-found.md
│       ├── TT-006-marker-heading-conflict.md
│       ├── TT-007-non-convergence.md
│       └── TT-008-font-substitution.md
│
├── profiles/
│   └── frap.yaml                       ← Step C
│
├── schemas/
│   ├── finding.schema.json             ← Step D
│   └── registry.schema.json            ← generated during build (spec §4)
│
├── src/citetab/
│   ├── models/                         ← finding.py (Step D), registry.py (build)
│   ├── pipeline/                       ← parser, extractor, resolver, toa_builder,
│   │                                      inserter, renderer, locator, convergence,
│   │                                      input_toa_diff
│   ├── rules/                          ← base.py + one module per TT rule
│   ├── engine/                         ← rule_loader, profile_loader, runner
│   ├── report/                         ← Markdown renderer per REPORT_SPEC
│   └── cli.py
│
├── tests/
│   ├── unit/  integration/  e2e/
│   └── fixtures/
│       ├── briefs/                     ← 3 base + 3 derived .docx
│       └── expected/                   ← serialized findings + report baselines
│
└── examples/
    ├── briefs/                         ← the three Step B fixtures
    └── reports/                        ← the three Step D rendered reports
```

### Pipeline module map

The pipeline is the spec §3 diagram, one module per arrow:

```
parser ──► extractor (eyecite) ──► resolver ──► registry (partial)
   │                                               │
   └─► input_toa_diff (baseline, FR-05)            ▼
                                            toa_builder (profile)
                                                   │
                                              inserter (FR-02)
                                                   │
        ┌──── convergence orchestrator (FR-08) ────┤
        │                                          ▼
        │                                  renderer (LibreOffice)
        │                                          │
        │                                   locator (pdfplumber)
        └──────────── not stable ◄─────────────────┘
                          │ stable
                          ▼
            registry (complete) ──► rules engine ──► report + .docx writers
```

Two cross-cutting components: the **rule loader** (validates card
frontmatter against implementations at startup — Principle 8.5 made
executable) and the **profile loader** (validates profile YAML;
nothing about TOA formatting is hardcoded).

## 16. Core Data Models

Normative shapes live in INPUT_OUTPUT_SPEC.md §4 (registry) and the
Step D finding schema; this section is orientation, not redefinition.

- **Authority** — `authority_id`, `type` (case / statute / regulation /
  constitutional / rule / secondary), normalized `components`,
  `display_full`, optional `display_short`, `sort_key`, `group`,
  `occurrences[]`, `pages[]` (sorted, de-duplicated), `passim`
- **Occurrence** — `form` (full / short / supra / id / ibid),
  `raw_text`, `paragraph_index`, `char_span`, `page`, optional
  `pincite`, `confidence` (high / medium)
- **Run metadata** — tool version, profile id + version, render engine
  identity/version, font-substitution flag + pairs, iteration count,
  input file hash
- **Finding** — per the Step D schema: ULID `finding_id`, rule
  id/version, rule-pack version, severity, confidence, message,
  evidence, citations, versions of everything that produced it
- **Court profile** — per frap-profile.yaml: heading
  (generated text + detection variants), groups (key/label/types, in
  render order), sort, passim (threshold + render text), formatting
  flags, empty-group policy. Profiles are versioned data, not code.

## 17. UX / Surface Concept

One happy path, three commands of introspection:

```
$ citetab generate opposition.docx
Parsed 41 citation occurrences → 12 authorities (frap profile v1.0.0)
Placement: heading "TABLE OF AUTHORITIES" (page 1)
Converged in 2 iterations.
Wrote opposition.toa.docx
Wrote opposition.toa-report.md
2 findings: 0 error · 1 warning · 1 info   (see report)
```

The report is the conversation with the user: TOA first, findings
second, every finding stating what happened, what the tool did about
it, and what (if anything) the user must do before filing. `rules
show TT-00x` prints the card so the user can read exactly why a
finding exists and what regulation or spec section it cites — the
teaching-artifact property carried over from CallLint.

## 18. Distribution

- **PyPI** as `citetab` (rename at v0.5 will publish under the real
  name with `citetab` kept as a final redirect release)
- **GitHub** public repo from the first commit; the seed files are
  committed *before* Claude Code runs, so history shows the
  design/build boundary
- README quick start must work on a clean machine in under five
  minutes, LibreOffice install included (one apt/brew/winget line per
  platform)

## 19. Definition of Done for MVP

The MVP is complete when a user can:

1. `pip install citetab` (plus LibreOffice per README) on Linux,
   macOS, or Windows
2. Run `citetab generate examples/briefs/clean_appellate_brief.docx`
   and get a .docx whose TOA is semantically identical to the input's,
   converged on the first check
3. Run it against `dirty_motion_brief.docx` and get a corrected TOA
   (Okafor added, every page number fixed, Carmody as passim, Delgado
   as a page list) plus findings explaining each correction
4. Run it against `marker_trial_memo.docx` and watch a TOA appear
   where the `[[TOA]]` marker was — then run it again on the output
   and verify nothing changes
5. Open any report and understand every finding: what fired, why,
   with what evidence, citing which authority (FRAP, Bluebook, or
   spec section)
6. Run `citetab rules list` / `rules show` / `profiles show frap`
7. Verify by reading LIABILITY.md that the tool's posture is clear:
   drafts for attorney review, not legal advice, filing attorney
   responsible for every filing
8. Confirm by inspection that no network calls occur during a run

And when the quality gates pass: pytest green, the §20 oracle
reproduced exactly, `mypy --strict` on `src/`, `ruff check` and
`ruff format --check` clean, coverage ≥ 85%.

## 20. Testing Strategy

### Fixtures

Three authored briefs (Step B) plus four derived inputs
(RULES_README "Closing the fixture gaps"):

| Fixture | Derivation | Exercises |
|---|---|---|
| `clean_appellate_brief.docx` | authored | front-matter convergence, passim boundary (Carmody = exactly 5), no-finding path |
| `dirty_motion_brief.docx` | authored | D1–D6: TT-001/002/003, passim trigger + boundary, continuous-pagination loop |
| `marker_trial_memo.docx` | authored | marker bootstrap, diff-rule skip, idempotency handoff |
| `dirty_plus_phantom.docx` | dirty + fabricated TOA entry (*Nonexistent v. Authority*) | TT-004 |
| `memo_no_marker.docx` | marker memo − marker paragraph | TT-005, docx suppression |
| `dirty_plus_marker.docx` | dirty + `[[TOA]]` marker, heading left in place | TT-006, marker-wins precedence |
| (none) | mocked measurer alternating page assignments | TT-007 unit test |

Derived fixtures are generated by a checked-in script from the base
fixtures, not committed as opaque binaries, so the derivation is
inspectable.

### Test oracle (expected findings)

CI runs under LibreOffice with Liberation substitution, so TT-008
(warning, high) is **expected present on every fixture run** in CI.
Assertions use a helper that requires TT-008 iff the run metadata
reports substitution, then asserts the remaining findings exactly:

| Fixture | Findings besides TT-008 |
|---|---|
| clean | none |
| dirty | TT-001 ×1 (error, high — *Ellison*) · TT-002 ×1 (info, high — *Okafor*) · TT-003 ×1 (info, high — aggregated correction table covering every stale entry) |
| marker memo | none (TT-002/003/004 skipped; skipped rules emit nothing) |
| dirty + phantom | dirty's findings + TT-004 ×1 (warning, medium — *Nonexistent v. Authority*) |
| memo − marker | TT-005 ×1 (error, high); **no .docx written**; report contains the full generated TOA |
| dirty + marker | dirty's findings + TT-006 ×1 (warning, high); heading region byte-identical to input |
| mocked oscillation | TT-007 ×1 (error, high) naming the unstable authorities; outputs still written |

### Generation assertions (not findings)

Per RULES_README, D4/D5 are asserted on the TOA itself: dirty's
regenerated table renders Carmody as "passim" and Delgado as a
five-page list; clean's renders Carmody as a five-page list. Clean's
authority→pages table must match FIXTURES_README's documented values
exactly under the CI render environment.

### Idempotency tests

Every fixture that produces a .docx is run twice; the second run must
converge in one iteration with zero changes and (after masking)
byte-identical outputs. This is the spec §3.3 promise as a regression
gate, and it doubles as the marker-to-heading handoff test on the
memo.

### Masked non-deterministic fields

`finding_id`, run id, evaluation timestamps, render engine version
string, and absolute paths are masked before comparison; the masked
set is fixed and documented in `tests/conftest.py`. After masking,
JSON baselines must match byte-for-byte; Markdown reports must match
content-exactly (whitespace-tolerant).

### Test categories

- **Unit:** profile loading, card frontmatter parsing/validation,
  registry model ↔ schema cross-validation, placement precedence walk,
  passim threshold boundary, input-TOA entry parsing (including
  unparseable entries), convergence loop with mocked measurer
  (including the TT-007 cap), exit codes
- **Integration:** one per rule, asserting the oracle row(s) for the
  fixtures that exercise it
- **End-to-end:** full CLI runs per fixture comparing .docx TOA
  content and Markdown reports to baselines, plus the double-run
  idempotency pass

## 21. Repo Operating Rules for AI-Assisted Development

Full set in `docs/AI_GUARDRAILS.md` (Step E). Summary:

1. **Generator framing is structural.** Findings are disclosures
   around a generated table; no language implying authoritative legal
   judgment, and severity always answers "what must the user do before
   filing?"
2. **Deterministic before AI.** No LLM/ML inference in the generation
   path in v1.
3. **Specification before implementation.** Cards, specs, and profiles
   are the source of truth; the loader enforces it; spec and code
   change in the same PR.
4. **Local-first.** No network calls during a run, no telemetry.
5. **No real documents.** Synthetic fixtures only; real-document
   issues are deleted.
6. **Never guess, never pretend, always disclose.** TT-005's
   suppression, TT-007's honesty, TT-008's disclosure are
   load-bearing; do not "improve" them away.
7. **Versioned everything.** Engine, rule pack, individual rules, and
   profiles on independent SemVer tracks (CHANGELOG.md policy); every
   finding records all four.
8. **Honest scope.** Deferred items stay in §12 and the README, not in
   the build.

## 22. Suggested Initial Claude Code Prompt

The prompt is **phase-gated**. Without gates, an agentic coding tool
will generate the entire codebase in one pass and review happens after
the fact instead of during. Each phase ends with a hard stop: run the
checks, summarize, wait for approval. If Claude Code barrels through a
gate, stop it and remind it.

```text
Create a new Python project called citetab.

docs/PRD.md is the control document. The seed files are already in
place and committed:

- README.md, LIABILITY.md, LICENSE, CHANGELOG.md, CONTRIBUTING.md,
  pyproject.toml, .gitignore
- docs/PRD.md, docs/INPUT_OUTPUT_SPEC.md, docs/REPORT_SPEC.md,
  docs/AI_GUARDRAILS.md
- rules/README.md, rules/CHANGELOG.md, rules/toa/TT-001..TT-008 (eight
  rule cards)
- profiles/frap.yaml
- schemas/finding.schema.json
- src/citetab/models/finding.py (Pydantic model, from the design phase)
- examples/briefs/ (clean_appellate_brief.docx, dirty_motion_brief.docx,
  marker_trial_memo.docx) and examples/reports/ (three rendered
  Markdown reports)

Work in phases. At the end of every phase: run all quality gates that
exist so far, summarize what you built and any judgment calls, and
STOP for my approval before the next phase. Do not start a phase
early.

PHASE 0 — Read and play back. Read every seed file before writing any
code. Then summarize back: the product's posture, the pipeline, the
eight rules and their severities, the placement precedence, the
convergence algorithm, the test oracle in PRD §20, and the guardrails.
If anything in the seed files seems contradictory, list it here. STOP.

PHASE 1 — Models, schemas, loaders. Add pdfplumber>=0.11 to
pyproject dependencies (PRD §14 correction). Implement
schemas/registry.schema.json and src/citetab/models/registry.py per
INPUT_OUTPUT_SPEC §4, cross-validating both ways. Implement the rule
loader (parse card frontmatter, validate an implementation exists for
every active card, fail loudly on drift) and the profile loader
(validate frap.yaml, expose typed profile objects). Unit tests for
all of it. STOP.

PHASE 2 — Pipeline. Implement parser, extractor (eyecite),
resolver, input_toa_diff, toa_builder, inserter (placement precedence
per spec §2.4, including marker consumption and the refuse-to-guess
fallback), renderer (LibreOffice headless subprocess with clear
failure when absent), locator (pdfplumber), and the convergence
orchestrator (spec §3.2: parse once, build once, measure, check, cap
5). Verify against the three example briefs: clean converges on the
first check and reproduces the FIXTURES_README page table; dirty
converges within the cap with Okafor added, Carmody passim, Delgado
listed; the memo bootstraps via the marker. No rules yet. STOP.

PHASE 3 — Rules. Implement rules/base.py (a Rule protocol with
applies(registry, context) and evaluate(...) -> list[Finding]) and
all eight TT rules exactly per their cards, including granularity
(TT-003 aggregates; TT-001/002/004 are per-authority), skip vs.
could-not-evaluate semantics, and TT-005's blocks_docx_output. Wire
the runner. Integration tests asserting the PRD §20 oracle, including
the four derived fixtures (generate them by script from the base
fixtures per §20) and the mocked-measurer TT-007 unit test. STOP.

PHASE 4 — Report and CLI. Implement the Markdown report renderer
exactly per docs/REPORT_SPEC.md, validated against the three rendered
examples in examples/reports/. Implement the Click CLI per PRD §11
FR-11, including exit codes. End-to-end tests per fixture, plus the
double-run idempotency tests with the masked-field set documented in
tests/conftest.py. STOP.

PHASE 5 — Gates and docs. All gates green: pytest, ruff check, ruff
format --check, mypy --strict on src/, coverage >= 85%. Generate
docs/ARCHITECTURE.md describing what was actually built (module map,
data flow, where each spec section is implemented). Final summary:
files created, test count, coverage, gate results, judgment calls
made where specs were ambiguous (the call and why), recommended next
milestone. STOP.

Constraints (from docs/AI_GUARDRAILS.md) — non-negotiable:

- No LLM or ML inference anywhere in the generation path.
- No network calls during a run. No telemetry. No update checks.
- The input .docx is never modified; outputs are always copies.
- Never insert a TOA at a guessed location; never report convergence
  that didn't happen; never silently delete document content.
- Static TOA content only — never Word TA/TOA field codes.
- No real legal documents anywhere, including tests and issues.
- Severity language: findings are disclosures and instructions for
  the user, never legal judgments.
- If a spec and generated code disagree, the spec wins. If two specs
  disagree, PRD §9's reconciliation note governs TT-008; raise
  anything else instead of choosing silently.
```

### Seed inventory verification (do this before Phase 0)

The design files were produced across several sessions, and the
review-project copies of some Step D/E files were shadowed by
identically named CallLint reference files. Before handing off,
confirm the seed folder physically contains the **citetab** versions
of: README.md, LIABILITY.md, AI_GUARDRAILS.md, docs/REPORT_SPEC.md,
schemas/finding.schema.json, src/citetab/models/finding.py, and the
three rendered example reports. A CallLint README in a citetab repo is
the kind of error that survives to launch. The Step G handoff document
includes this checklist.

## 23. Suggested LinkedIn / Portfolio Summary

> Built citetab, a free, open-source, local-first Table of Authorities
> generator for legal briefs. A .docx goes in; a copy with a
> court-rule-compliant TOA comes out, page numbers measured from a
> real render of the actual document via a fixed-point pagination
> algorithm. Citations parsed with eyecite (Free Law Project);
> everything runs on the user's machine — no uploads, no telemetry —
> because a client's brief shouldn't have to live on someone else's
> servers. Designed spec-first (versioned rule cards, court profiles
> as data, deterministic pipeline) and implemented with AI coding
> tools under explicit written guardrails; second project built on a
> design system I've now reused across two regulated domains.

## 24. Future Expansion Ideas

Post-v1, in rough priority order — none committed:

1. **Court profiles** beyond FRAP: SCOTUS, California, Washington,
   N.D. Cal. (length-threshold logic). The highest-leverage expansion;
   pure data work against an existing format.
2. **The v2 rule candidates** from §12: pincite validation, internal
   cross-reference checking, Bluebook style checks, duplicate-citation
   detection.
3. **Registry sidecar consumers**: a diff view between two runs of the
   same brief ("what changed since the last draft").
4. **Word add-in or GUI wrapper** — only if real users ask; the CLI is
   the product until then.
5. **Quotation accuracy** — gated on resolving the local-first tension
   (it requires source corpora), not just on effort.
6. **The rename** at v0.5: real name, PyPI publication under it, repo
   rename, `citetab` redirect release.

## 25. Risks and Mitigations

**LibreOffice render fidelity.** Page boundaries can differ from
Word's by ±1 page under font substitution, and the court ultimately
sees a Word- or chambers-produced PDF. *Mitigation:* TT-008 makes the
condition unmissable and names the substituted fonts; README documents
installing Microsoft-metric fonts; the honest framing is "measured
from a real render, disclosed when the render differs from yours" —
which is still categorically better than hand-maintained numbers.

**eyecite coverage gaps.** Unusual reporters, state-specific forms,
or malformed citations may parse incompletely. *Mitigation:* the
confidence field exists for exactly this; unresolvable forms surface
as TT-001 rather than silently vanishing; eyecite is actively
maintained and contributions flow upstream.

**.docx structural diversity.** Real briefs come from decades of
firm templates. *Mitigation:* the acceptance posture is defensive
parsing with loud failure (FR-01), the placement fallback refuses to
guess, and the marker mechanism gives any user a deterministic escape
hatch.

**Convergence pathologies.** A document could in principle oscillate.
*Mitigation:* the cap-plus-TT-007 design means the worst case is an
honest error naming the unstable entries, never a hang or a silent
wrong answer.

**Adoption never materializes.** True of any free tool. *Mitigation:*
the only early signal that matters is what Cheryle (and people like
her) say when shown the working tool on a real-shaped brief. One real
conversation before any launch push — this is Step H of the handoff
and it is not skippable.

**Liability exposure.** A wrong TOA in a filed brief has professional
consequences. *Mitigation:* LIABILITY.md and the LICENSE additional
notice are unambiguous — drafts for attorney review, filing attorney
responsible for every filing; the findings system exists so the tool
never makes a silent claim; MIT's warranty disclaimer applies.

**Placeholder-name drift.** Shipping momentum could make "citetab"
permanent by default. *Mitigation:* the v0.5 gate is written into
this document and the custom instructions; §1 bounds the rename cost.

## 26. Project Identity

- **Name:** citetab (placeholder; real name at v0.5 launch prep —
  shortlist held, no further naming discussion before then)
- **License:** MIT, plus the non-license additional notice pointing at
  LIABILITY.md
- **Versioning:** four independent SemVer tracks (engine, rule pack,
  individual rules, court profiles) per CHANGELOG.md; every finding
  records all four
- **Scope statement:** generates Tables of Authorities locally;
  discloses what it changed and what it couldn't do; is not legal
  advice and never pretends to be
- **Lineage:** CallLint design system, adapted from linter to
  generator; the adaptation itself is documented (RULES_README's
  severity-semantics section) as part of the project's intellectual
  record

## 27. Final North Star

A paralegal with a brief due at 4:30 runs one command at 2:00, reads a
one-page report, spot-checks two findings, and files — without the
brief ever leaving the machine, and without anyone re-typing a page
number. Every design decision in this document either serves that
moment or doesn't belong in v1.
