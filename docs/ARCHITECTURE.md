# Architecture

This document describes toatool **as built**. Where the implementation diverged
from the earlier design documents (`PRD.md`, `INPUT_OUTPUT_SPEC.md`,
`REPORT_SPEC.md`, the rule cards, and `examples/briefs/README.md`), the
divergence and its reason are recorded in [§9](#9-where-reality-diverged-from-the-design-docs)
so a reader is not surprised when the code does not match the older prose. The
specs remain the normative contracts; this file is the map of the territory.

---

## 1. What the tool does

toatool ingests a `.docx` legal brief and produces two artifacts:

1. a copy of the brief with a **regenerated, court-rule-compliant Table of
   Authorities** whose page numbers are *measured* from a real LibreOffice
   render — not estimated; and
2. a **Markdown findings report** disclosing every correction the tool made and
   everything the drafter should verify before filing.

It is deterministic end to end: no LLM/ML in the generation path, no network
calls, the input is never modified, and the TOA is written as static formatted
content (never Word `TA`/`TOA` field codes). Citations are parsed with eyecite,
pages are located with pdfplumber over a LibreOffice-headless render, and every
formatting decision is read from a versioned court **profile** (data, not code).

---

## 2. Repository layout (as built)

```
src/toatool/
├── __init__.py          # __version__ (engine SemVer track)
├── cli.py               # Click CLI: generate / rules / profiles  (FR-11)
├── models/
│   ├── registry.py      # CitationRegistry, Authority, Occurrence, RunMetadata
│   └── finding.py       # Finding + Evidence + Citation (Step D schema mirror)
├── engine/
│   ├── resources.py     # resolve bundled-vs-checkout data dirs
│   ├── profile_loader.py# CourtProfile (validated YAML)
│   ├── rule_loader.py   # RuleCard frontmatter + card↔impl drift check
│   └── runner.py        # build RuleContext, run rules, exit code
├── pipeline/
│   ├── parser.py        # .docx → typed paragraphs (FR-01)
│   ├── placement.py     # TOA placement precedence walk (FR-02)
│   ├── extractor.py     # body text + char→paragraph offset map
│   ├── resolver.py      # eyecite resolution → WorkingAuthority (FR-03/04)
│   ├── supplemental.py  # toatool-owned recognizer seam (see §9.1)
│   ├── courts.py        # court-name abbreviation
│   ├── input_toa_diff.py# parse the input TOA into a diff baseline (FR-05)
│   ├── toa_builder.py   # group/sort/passim → ToaModel (FR-06)
│   ├── inserter.py      # write the generated TOA into the working copy (FR-02/09)
│   ├── renderer.py      # LibreOffice render + font-substitution detect (FR-07)
│   ├── locator.py       # pdfplumber: locate each occurrence's page (FR-07)
│   ├── convergence.py   # the fixed-point regeneration loop (FR-08)
│   └── working.py       # mutable WorkingAuthority/WorkingOccurrence
├── rules/
│   ├── base.py          # Rule protocol, RuleContext, make_finding, sort
│   ├── support.py       # shared rule helpers
│   └── tt001.py … tt008.py
└── report/
    └── render.py        # the Markdown report (REPORT_SPEC) + mask_report

rules/        profiles/        schemas/        # versioned data (bundled in the wheel)
scripts/      check.sh  reconcile_fixtures.py  regenerate_examples.py
```

Two cross-cutting loaders enforce "spec is source of truth" at startup: the
**rule loader** validates each card's frontmatter and checks that active cards
and implementations correspond exactly (`validate_implementations`), and the
**profile loader** validates the court profile YAML. Nothing about grouping,
ordering, passim, or headings is hardcoded.

---

## 3. The pipeline

Data flows in one direction; each module is one arrow of the spec §3 diagram.

```
parser ──▶ placement ──▶ extractor ──▶ resolver ──┬─▶ toa_builder ──▶ inserter
  │            │           (+ supplemental)        │
  │            └─▶ input_toa_diff (baseline)        │
  ▼                                                 ▼
ParsedDocument                            convergence loop (FR-08)
                                            renderer ──▶ locator
                                                 │  not stable ▲
                                                 ▼  stable     │
                                          freeze CitationRegistry
                                                 │
                                       runner ──▶ rules (TT-001..008)
                                                 │
                                    report/render  +  .docx writer (cli)
```

- **parser** opens the `.docx` read-only and yields typed paragraphs (text,
  style, heading level). It never mutates the input; all work is on copies.
- **placement** walks the detection precedence (spec §2.4): `--toa-heading`
  flag → `[[TOA]]` marker → default heading variant → none. It records *every*
  mechanism that matched (not just the winner) so the rules engine can later
  report conflicts (TT-006) or absence (TT-005).
- **extractor** concatenates the body (excluding the detected TOA region) into a
  single text stream with a character→paragraph offset map, so eyecite spans map
  back to `(paragraph_index, char_span)`.
- **resolver** runs eyecite `get_citations` + `resolve_citations`, turning each
  full citation and its short/supra/id cluster into one `WorkingAuthority`.
  Short forms eyecite cannot anchor become `unresolved` orphans (the TT-001
  input). The **supplemental** recognizer fills eyecite's two gaps and is merged
  here, de-duplicated by identity so eyecite always wins (see §9.1).
- **input_toa_diff** parses the input document's existing TOA region into a
  baseline of `(authority_id, pages)` entries matched by *resolved identity*,
  never string equality. This is what TT-002/003/004 compare against; on the
  marker/none paths there is no baseline and those rules skip.
- **toa_builder** groups and sorts the authorities per the profile and decides
  passim (more than `threshold_pages` distinct pages). Page text is computed on
  demand, so the same structure renders correctly as pages change each iteration.
- **inserter** writes the generated TOA into the working copy as static content,
  keeping a handle to each entry's page-number run so the loop can rewrite just
  the digits. On the marker path it emits the standard heading and consumes the
  marker — the idempotency handoff (a re-run then detects via the heading path).

---

## 4. The convergence loop (FR-08)

`convergence.generate` parses once, builds once, then runs the measure → write →
re-render → check loop, capped at 5 iterations:

```
for attempt in 1..5:
    save working.docx
    render to PDF (LibreOffice)            # renderer
    locate each occurrence's page (PDF)    # locator (pdfplumber forward cursor)
    snapshot pages
    if snapshot == previous: converged; break
    rewrite the TOA's page runs            # inserter.update_pages
```

The canonical `CitationRegistry` is **frozen exactly once, after** the loop
settles — pages, iteration count, and font substitutions accumulate in mutable
working structures during the loop and convert in a single step. A hard
invariant guards the freeze: every occurrence that feeds a TOA entry must have a
measured page, or `freeze_registry` raises `ConvergenceError` rather than emit an
entry with a missing page. If the loop hits the cap without settling, the outputs
are still written with the last numbers and TT-007 fires.

---

## 5. The rules engine

Eight independent rules (`rules/tt001.py … tt008.py`), each a small object
carrying its validated `RuleCard`. The **runner** assembles one immutable
`RuleContext` (frozen registry, placement, diff baseline, orphans, page history),
runs the loader's card↔implementation drift check, evaluates every rule whose
`applies()` is true, and sorts the combined findings for presentation:
**severity (error → warning → info) → rule id → document order** (FR-10).

| Rule | Severity | Granularity | Fires when |
|---|---|---|---|
| TT-001 unresolvable short form | error | per orphan cluster | a short form has no anchoring full citation |
| TT-002 missing TOA entry | info | per authority | a cited authority was absent from the input TOA |
| TT-003 stale page numbers | info | **one aggregated** | any input-TOA page list disagrees with the render |
| TT-004 phantom TOA entry | warning | per entry | an input-TOA entry matches no cited authority |
| TT-005 placement not found | error | run-level | no flag/marker/heading matched (**suppresses .docx**) |
| TT-006 marker+heading conflict | warning | run-level | a marker won over an existing heading region |
| TT-007 non-convergence | error | run-level | the loop hit the cap without stabilizing |
| TT-008 font substitution | warning | run-level | the render substituted any declared font |

`applies()` vs `evaluate()` makes "skipped is not passed" executable: the diff
rules on the bootstrap/marker path return `applies()=False` and emit nothing —
which the report distinguishes from a clean result. **Exit code** is derived by
the runner: `1` if any error finding fired or the `.docx` was suppressed, else
`0`. The CLI adds `2` for invocation/parse failures.

---

## 6. The report and the CLI

`report/render.py` renders the run as Markdown in three parts (REPORT_SPEC §2):
run header, the generated Table of Authorities, then findings (most actionable
first). It is always written — even when the `.docx` is suppressed (TT-005), in
which case it is the only output and still carries the full table. The only
non-deterministic values that reach the Markdown are the `generated:` timestamp
and the render-engine version; `mask_report` normalizes both for byte-stable
comparison, and `finding_id`/`evaluated_at_utc` are deliberately not rendered.

`cli.py` (Click) exposes `generate BRIEF.docx [--court] [--toa-heading]
[--output]` plus read-only `rules list|show` and `profiles list|show`. Exit
codes (FR-11): `0` success, `1` error finding or suppressed `.docx`, `2`
invocation/parse failure (missing/unreadable/non-`.docx` input, unknown profile
or rule). The iteration cap is fixed by spec at 5 and is not a flag.

---

## 7. Versioning — four independent SemVer tracks

Recorded on every run and finding so any report is reproducible against the exact
definitions in force:

- **engine** — `toatool.__version__`
- **rule pack** — `RULE_PACK_VERSION` (`rules/CHANGELOG.md`)
- **individual rule** — each card's `version`
- **court profile** — each profile's `version`

---

## 8. Data is the source of truth

`rules/toa/*.md` (cards), `profiles/*.yaml`, and `schemas/*.json` are loaded and
validated at startup; the registry and finding models cross-validate against
their JSON Schemas in both directions. The wheel force-includes `rules`,
`profiles`, and `schemas` under `toatool/_bundled/` so `pip install toatool`
works without a clone; `resources.py` prefers the bundled copy, then the repo
root.

---

## 9. Where reality diverged from the design docs

Three places where the build does not match the original prose. Each was a
deliberate, recorded decision; the older documents are being patched on next
touch, and the tests encode the as-built behavior.

### 9.1 The supplemental recognizer seam (eyecite's two gaps)

The design assumed eyecite would parse every citation in the fixtures. It does
not:

- **Subsection-letter statutes** — `15 U.S.C. § 1692e`. reporters_db's
  `law.section` regex does not allow a bare trailing letter, so eyecite yields an
  `UnknownCitation` for the `§` and drops the statute.
- **Rules of procedure** — `Fed. R. App. P. 28`. A rule of procedure is not an
  eyecite citation *type* at all, so `get_citations` returns nothing for it.

Rather than patch reporters_db (a vendored dependency we do not own) or fork
eyecite, toatool owns a single deterministic recognizer layer,
`pipeline/supplemental.py`, that recognizes exactly these two shapes and emits
the same `(identity, display_full, sort_key, type)` an eyecite authority would.
Its candidates are merged in `resolver._merge_supplemental`, **de-duplicated by
identity so anything eyecite already parsed wins**. eyecite is kept entirely
stock. Scope is full statutory/regulatory/rule citations only — no
`section 1692e` short forms in v1. (Build decision "1B".)

### 9.2 Measured pages over a continuous render, not roman front matter

`INPUT_OUTPUT_SPEC.md` and the original `examples/briefs/README.md` described the
clean brief as having separately paginated lower-roman front matter and an
arabic body, with the regeneration loop converging "on the first check by
construction." In this build's environment that layout does not hold: the
fixtures render with **continuous pagination**, and a "page" is a **physical PDF
page index** measured by rendering the working document and locating each
occurrence's text with pdfplumber. The clean brief still converges in one
iteration here — but because a TOA-length change does not shift body pagination
in these short briefs, *not* because of a roman/arabic split. The product thesis
is unchanged and in fact stronger: page numbers are always measured from a real
render, never inferred from document structure. `scripts/reconcile_fixtures.py`
treats this environment's measured pages as truth and keeps the fixtures and
`FIXTURES_README` in sync (±1 drift at the margins is accepted and is exactly the
disclosure TT-008 exists to make). The committed `examples/reports/*.md` are
regenerated outputs (`scripts/regenerate_examples.py`), not frozen oracles.

### 9.3 The substitution is Consolas → DejaVu Sans Mono, not Times → Liberation

The rule card and the hand-written example report illustrated TT-008 with `Times
New Roman → Liberation Serif`. The fixtures do not declare Times New Roman. They
declare **Consolas** (the `Source Code` paragraph style that holds the TOA
entries), which fontconfig resolves to **DejaVu Sans Mono** on a machine without
the Microsoft fonts. So TT-008 fires on all three base fixtures disclosing
`Consolas → DejaVu Sans Mono`. Detection is `renderer.detect_font_substitutions`:
it reads the fonts the `.docx` declares and resolves each with `fc-match`,
reporting any family the renderer actually substitutes — tied to the real render
path, so the finding can never disagree with the measurement. On a machine with
the document's fonts installed, no substitution is reported and TT-008 does not
fire; the test oracle asserts TT-008 *iff* the run metadata reports a
substitution.

### Smaller reconciliations on record

- **REPORT_SPEC §5 finding order** was corrected to severity → rule id → document
  order to agree with PRD §11 FR-10 and `rules/README.md`.
- **PRD §20 "dirty + marker"** row reads against the TT-006 card: when the marker
  wins, the heading region is not used as the diff baseline, so TT-002/003/004
  skip. The card governs; the oracle is TT-001 + TT-006 (+ TT-008).
- **`Occurrence.page` is nullable** to represent the pre-render partial registry;
  a converged registry is always fully populated, and the freeze asserts it.
- **`RunMetadata`** carries `rule_pack_version` and `converged` beyond the spec's
  literal list (needed for the report header and TT-007).

---

## 10. Quality gates

`scripts/check.sh` runs the four gates CI and contributors run before every PR,
in order: `ruff check` → `ruff format --check` → `mypy` (strict) → `pytest` with
the ≥85% coverage gate (configured in `pyproject.toml`). LibreOffice-dependent
integration tests skip automatically when LibreOffice is absent, but only truly
exercise where it is installed.

Testing is layered (PRD §20): unit (loaders, models↔schema, placement,
passim boundary, diff parsing, the mocked-measurer TT-007 cap, exit codes),
integration (the §20 finding oracle per fixture, the full generation pipeline,
report determinism, idempotency), and the CLI surface. The four derived fixtures
(dirty+phantom, memo−marker, dirty+marker, and the mocked oscillation) are built
from the base briefs at test time, so their derivation is inspectable and no
opaque binary is committed.

---

## 11. Deferred to post-v1

Court profiles beyond FRAP (SCOTUS, California, Washington, length-threshold
logic — the profile format is built for them; the data is not v1 work); the
machine-readable JSON sidecar (`{stem}.toa-report.json` with the ULIDs and
timestamps omitted from the Markdown — added only if the test suite demonstrates
it is needed); pincite validation; internal cross-reference checking; Bluebook
short-form/style checking; duplicate-citation detection; batch mode; PDF input;
and any LLM-assisted behavior at generation time. These are listed in the README
and PRD §12 to keep the v1 claim honest.
