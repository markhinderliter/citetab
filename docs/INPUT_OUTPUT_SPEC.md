# citetab — Input/Output Specification (Step B)

**Status:** Draft for ratification
**Version:** 0.1.0-draft
**Project name:** citetab (placeholder; real name decided at v0.5 launch)

This document is the normative specification for what citetab accepts,
what it produces, and the internal data structure that connects them.
It is the design-phase equivalent of a schema-first contract: the
Citation Registry defined in Section 4 is the canonical structure, and
every output is a rendering of it.

---

## 1. Scope of this document

Covers:

- The input contract (what the user provides; what we promise to accept)
- The processing pipeline (parse → render → locate → generate)
- The regeneration loop (the fixed-point pagination algorithm)
- The Citation Registry (canonical internal data model)
- The output contract (regenerated .docx + Markdown report)

Does not cover:

- Rule specifications (Step C)
- Finding schema and report format details (Step D)
- Project identity files (Step E)

---

## 2. Input contract

### 2.1 Required input

A single `.docx` file (Office Open XML, ISO/IEC 29500) containing a
legal brief with citations in the body.

That is the entire required input. citetab does not require:

- A rendered PDF (we render the document ourselves; see Section 3)
- Authoring conventions, special styles, or marker comments
- Word to be installed (parsing is via python-docx; rendering via
  LibreOffice headless)

### 2.2 Acceptance posture

Accept any structurally valid `.docx` and parse defensively. Real
briefs are written by real lawyers in whatever template their office
uses; requiring compliance with conventions would break the core
promise ("works like Word's table of contents — it just updates").

Malformed or unreadable input fails loudly with a clear message naming
the file and the failure. citetab never partially processes a brief it
cannot fully parse.

### 2.3 Court profile selection

- `--court <profile>` CLI flag selects the court profile governing TOA
  format (grouping, ordering, passim threshold, heading conventions).
- Default profile: FRAP (Federal Rules of Appellate Procedure).
- An optional per-project config file may pin the court profile so
  repeat runs don't need the flag. Config file format is a Step C/D
  detail; the contract here is only that the flag exists and has a
  documented default.

### 2.4 TOA placement in the input document

Validated against court rules (June 2026): FRAP 28 mandates a table of
authorities in appellate briefs; SCOTUS and state appellate rules
(e.g., California) require the equivalent, sometimes under variant
names ("table of cited authorities"); the Ninth Circuit shell brief
uses the exact heading `TABLE OF AUTHORITIES`. Trial-court practice is
less uniform — some districts require a TOA only above a length
threshold (e.g., N.D. Cal., briefs over 10 pages), and real motion
memoranda sometimes carry no TOA section at all. Since citetab's
audience includes heavy trial-court practice, heading detection alone
is insufficient. v1 therefore supports two mechanisms.

**Detection precedence (first match wins):**

1. **`--toa-heading <text>` flag.** Explicit user override of the
   heading to match.
2. **`[[TOA]]` marker.** A single marker on its own paragraph meaning
   "the generated TOA goes here, replacing this marker." This is the
   deterministic bootstrap for documents that have no TOA section yet
   (typical of trial memoranda). The marker is consumed: it does not
   appear in the output.
3. **Default heading variants.** Case-insensitive, whitespace-tolerant
   match against a versioned variant list (initially: "Table of
   Authorities", "Table of Cited Authorities"). The variant list is
   data, not hardcoded. The replacement region is everything below the
   matched heading up to the next heading of the same or higher level.
4. **Fallback (nothing found).** citetab does NOT guess an insertion
   point. The TOA is emitted in the Markdown report only, the
   regenerated .docx is not written, and a finding explains why and how
   to fix it (add the heading, or drop a `[[TOA]]` marker). Silent
   insertion into a wrong location is never acceptable: this is a
   legal filing.

Citation-density heuristics are explicitly rejected as a detection
mechanism: citations appear throughout the argument, not only in the
TOA, so any such heuristic would be brittle.

**Marker-to-heading handoff (idempotency).** The generated TOA always
carries the standard "Table of Authorities" heading. A marker therefore
bootstraps placement exactly once; every subsequent run detects the
section via the heading path. Re-runs on citetab's own output need no
marker.

**Conflict handling.** If both a marker and a detectable heading region
are present, the marker wins and a warning-level finding identifies the
unmodified heading region. citetab never silently deletes content.

---

## 3. Processing pipeline

```
.docx
  │  parse (python-docx)
  ▼
citation extraction (eyecite: full, short, supra, id., ibid.)
  │  resolve all reference forms back to their authority
  ▼
TOA construction (group, sort, court profile applied)
  │  insert into document copy at the placement region (§2.4)
  ▼
render (LibreOffice headless → PDF)
  │  extract per-page text + positions (pdfplumber)
  ▼
locate each citation occurrence on its rendered page
  │  write page numbers into the TOA
  ▼
convergence check (§3.2) ──not stable──► re-render, repeat
  │  stable
  ▼
outputs (§5)
```

All steps run locally. No network calls. No telemetry. No LLM calls at
generation time.

### 3.1 Why we render ourselves

A `.docx` file does not store page numbers; pages exist only at render
time. LibreOffice headless (`libreoffice --headless --convert-to pdf`)
is the rendering engine. This removes the "user must supply a PDF"
burden and guarantees the page numbers in the TOA come from an actual
layout of the actual document, not an approximation.

**Font substitution disclosure.** When Microsoft fonts (Times New
Roman, etc.) are absent, LibreOffice substitutes metric-compatible
fonts (Liberation Serif, Carlito). Page breaks can differ from Word's
by ±1 page at the margins. When substitution occurs during a run,
citetab emits an info-level finding disclosing it and recommending font
installation. The risk is disclosed, never silent.

### 3.2 The regeneration loop (fixed-point pagination)

The TOA describes the document's pagination while being part of the
document, so writing it can invalidate it. The algorithm:

1. **Parse once.** Extract all citations. The set of authorities and
   occurrences is layout-independent and never changes after this step.
2. **Build once.** Construct the full TOA structure (all entries,
   grouped and sorted per court profile) and insert it. This absorbs
   the large length perturbation (e.g., a previously missing entry) in
   a single step.
3. **Measure.** Render; locate every occurrence; write actual page
   numbers (or "passim") into the TOA entries.
4. **Check.** Re-render. If no occurrence's page changed as a result of
   step 3, the document is stable — done. Otherwise update the numbers
   and repeat step 4.

Convergence is fast in practice: after step 2, iterations only change
page-number digits (and occasionally a passim flip), which rarely
changes line counts.

**Iteration cap:** 5. If pagination has not stabilized, citetab writes
the outputs with the last computed numbers plus a prominent error-level
finding identifying the unstable entries. It never loops indefinitely
and never pretends convergence.

**Front-matter exploitation.** Briefs whose TOA lives in separately
paginated front matter (roman-numeral i/ii/iii, body restarting at
arabic 1 — typical FRAP layout) converge on the first check by
construction, because TOA length cannot shift body pagination. The loop
requires no special casing; this layout simply exits early. Continuously
paginated briefs (common in trial-court filings) are where iteration
does real work.

**Passim interaction.** An authority cited on more than 5 pages lists
"passim" instead of page numbers (court profiles may tune the
threshold). If an iteration moves an authority across the threshold,
the entry text changes — a perturbation the convergence check catches
and the next pass absorbs.

### 3.3 Idempotency promise

Same input → same output, every run. Running citetab on its own output
must converge immediately with zero changes; this doubles as a built-in
self-test and is the direct answer to Best Authority's re-run
fragility, which is the core user pain (Cheryle).

---

## 4. Citation Registry (canonical internal model)

The registry is the single structure the pipeline produces and every
output renders from. It will be formalized as a JSON Schema and a
matching Pydantic model during the build phase; the shape below is
normative.

### 4.1 Authority

One entry per resolved authority.

| Field | Type | Notes |
|---|---|---|
| `authority_id` | string [req] | Stable within a run; deterministic derivation |
| `type` | enum [req] | `case`, `statute`, `regulation`, `constitutional`, `rule`, `secondary` |
| `components` | object [req] | Normalized parts (case: reporter, volume, first page, court, year; statute: code, section; etc.) |
| `display_full` | string [req] | Full citation form as rendered in the TOA |
| `display_short` | string [opt] | Short form, when derivable |
| `sort_key` | string [req] | Within-group alphabetical ordering key |
| `group` | enum [req] | TOA grouping bucket per court profile (cases / statutes / regulations / constitutional provisions / rules / other authorities) |
| `occurrences` | Occurrence[] [req] | All references, every form |
| `pages` | int[] [req] | Sorted, de-duplicated pages where any occurrence lands |
| `passim` | bool [req] | True when page count exceeds the profile threshold |

### 4.2 Occurrence

One entry per reference to an authority, in any form.

| Field | Type | Notes |
|---|---|---|
| `form` | enum [req] | `full`, `short`, `supra`, `id`, `ibid` |
| `raw_text` | string [req] | Verbatim text as it appears in the brief |
| `paragraph_index` | int [req] | Position in the .docx body (layout-independent anchor) |
| `char_span` | [int, int] [req] | Character offsets within the paragraph |
| `page` | int [req] | Page in the final converged render |
| `pincite` | string [opt] | Pinpoint reference when present |
| `confidence` | enum [req] | `high` = exact text-span match in render; `medium` = approximated location |

### 4.3 Run metadata

The registry carries run-level context: tool version, court profile and
version, render engine identity/version, font-substitution flag,
iteration count to convergence, input file hash. This is what makes a
TOA's provenance explainable after the fact.

---

## 5. Output contract

### 5.1 Regenerated .docx (primary output)

- Always a **copy**; the input file is never modified in place.
- Default name `{input_stem}.toa.docx`; `--output <path>` overrides.
- Only the TOA placement region (§2.4) is replaced. All other content,
  styles, and formatting pass through untouched.
- The TOA is written as **static formatted content, not Word TA/TOA
  field codes.** Field codes invite Word to re-paginate and reintroduce
  exactly the staleness this tool exists to eliminate. Static content
  is idempotent and renders identically in Word, LibreOffice, and
  Google Docs. "The page numbers are already correct because we
  computed them from the real render" is the product thesis expressed
  as a format decision.

### 5.2 Markdown report (secondary output)

- Default name `{input_stem}.toa-report.md`, written alongside the
  regenerated .docx.
- Leads with the generated TOA in readable form (generation first),
  followed by findings (diagnostics second). Findings include, at
  minimum in v1 scope: font-substitution disclosure (§3.1),
  non-convergence (§3.2), TOA-heading-not-found (§2.4), and the
  citation-quality findings to be specified in Step C.
- Exact report structure and the finding format are Step D.

### 5.3 Scope decisions

- **Single brief per invocation.** One .docx in, one .docx + one report
  out. No batch mode, no batch summary artifacts in v1.
- Whether a machine-readable sidecar (serialized registry) ships in v1
  is an open Step D question. The one identified argument for it is
  idempotency testing; it is not assumed.

---

## 6. Architectural commitments restated

These constrain everything above and all subsequent steps:

1. citetab **generates** a TOA. Findings are secondary to generation.
2. Deterministic before AI: no LLM calls at generation time in v1.
3. Local-first: no network calls during a run, no telemetry.
4. Specification before implementation: this document, the court
   profiles, and the Step C rule specs are the source of truth.
5. No real client documents anywhere: synthetic example briefs only.

---

## 7. Open items leaving Step B

1. **Example briefs:** synthetic fixtures — one clean FRAP-style
   appellate brief with front matter; one dirty brief with deliberate
   problems (missing TOA entry, stale page numbers, short-form-only
   authority, near-passim-threshold authority, continuous pagination to
   exercise the loop); and a third minimal trial-memorandum fixture
   with no TOA section and a `[[TOA]]` marker, exercising the bootstrap
   path. These close Step B and drive Step C's rule specifications.
2. Court profile data format (carried to Step C).
3. Finding schema and report layout (carried to Step D).
