# citetab

> Working name. The real name is decided at the v0.5 launch.

**A free, local Table of Authorities tool — because pressing
Alt+Shift+I two hundred times isn't a solution.**

If you've ever Googled "free Table of Authorities tool," the answer was
"use Microsoft Word's built-in feature." This is technically true and
practically useless for any brief over twenty pages: read the brief
yourself, mark every citation by hand, categorize each one in a dialog
box, and only then insert the table. The other "free" options are demo
modes of cloud tools that require uploading confidential client
documents to a vendor's servers.

citetab is the option that doesn't make you choose between hundreds of
keyboard shortcuts and someone else's cloud. It runs on your machine.
It finds the citations automatically. It generates the Table of
Authorities with page numbers measured from a real render of your
document. When you edit the brief, you run the tool again and the table
is regenerated correctly — the way Word's table-of-*contents* button
works, finally applied to authorities.

---

## What it does

A Word brief (`.docx`) goes in; two files come out:

- **`{brief}.toa.docx`** — your brief with a regenerated, court-rule-
  compliant Table of Authorities. Page numbers are computed by actually
  rendering the document and locating every citation, including short
  forms, *id.*, and *supra* references, resolved back to their
  authorities by [eyecite](https://github.com/freelawproject/eyecite)
  (the Free Law Project's citation parser, tested against tens of
  millions of citations).
- **`{brief}.toa-report.md`** — a plain-text report: the generated
  table, anything you should check before filing, and a disclosure of
  every correction the tool made (entries that were missing, page
  numbers that were stale, entries it couldn't resolve).

Everything runs locally. No upload, no account, no telemetry, no
network calls during a run. **Your client's brief never leaves your
machine.**

## Who it's for

Solo practitioners, small-firm paralegals, legal aid attorneys, public
defenders, and law school clinics — the tier below where commercial
legaltech is priced. ezBriefs and TypeLaw are good tools that cost
hundreds of dollars per year and require uploading your brief to their
servers. If neither of those constraints works for you, this tool is
for you.

---

## Getting started (Windows)

You'll do this once. There are two free programs to install — LibreOffice
(which citetab uses behind the scenes) and citetab itself — and then you
pick a brief and go.

### Step 1 — Install LibreOffice first

citetab measures the real page numbers in your brief by opening it the
way a word processor does. **LibreOffice** is the free, open-source
program it uses to do that. Your brief is opened only on your own
computer — it is never uploaded anywhere.

1. Go to **<https://www.libreoffice.org/>** and download the installer
   for Windows.
2. Run it and accept the standard options.

That's it — you don't need to open LibreOffice or learn it. citetab uses
it quietly in the background. (If you skip this step, citetab will tell
you LibreOffice is missing and point you back here.)

### Step 2 — Download and install citetab

1. Download **`citetab-setup.exe`** (from the project's releases page).
2. Double-click it to install. citetab installs like any normal Windows
   program and adds itself to your Start menu. During setup it will
   remind you about the LibreOffice requirement from Step 1.

**A note about the Windows security warning.** Because citetab is new
and not yet certificate-signed, Windows may show a blue
"Windows protected your PC" screen when you run the installer. This is
Windows being cautious about software it doesn't recognize yet — not a
sign that anything is wrong. citetab is open source and runs entirely on
your computer. To continue:

- Click **More info**
- Then click **Run anyway**

<!-- TODO: remove this SmartScreen subsection once the installer is
     code-signed (OV/IV certificate). See the signing decision in the
     project notes. -->

### Step 3 — Run citetab on a brief

1. Open **citetab** from the Start menu.
2. A file window opens — **choose the Word brief (`.docx`) you want to
   process** and click Open.
3. citetab works for a few seconds. **You won't see a window while it
   works — this is normal.** It's rendering your document to measure the
   page numbers. When it finishes, a results box appears.
4. The results box tells you where your new files are, which court
   format was applied (**"Court profile: Federal Appellate (FRAP)"**),
   and whether there's anything to review. Click **OK**.

citetab processes **one brief per run**. To do another brief, just open
citetab again from the Start menu.

### Your two new files

citetab saves two files **in the same folder as the brief you picked**:

| File | What it is |
|------|------------|
| `{yourbrief}.toa.docx` | Your brief with the regenerated Table of Authorities. This is the one you file. |
| `{yourbrief}.toa-report.md` | A plain-text summary of what citetab did — the table it built, any corrections it made, and anything to check before filing. |

The report is a plain-text file (`.md`). You can **open it with Notepad**
to read it. For a nicer, formatted view, open it with a Markdown viewer
(or paste it into one) — but Notepad is perfectly readable. citetab does
not change your original brief; it only writes these two new files.

---

## How it works

A `.docx` file does not contain page numbers — pages exist only when the
document is laid out. And because the Table of Authorities is *part of*
the document it describes, writing the table can change the pagination
it reports. citetab solves that honestly rather than approximately:

1. **Parse** the document and **extract** every citation in every form —
   full, short, *supra*, *id.*, *ibid.* — with eyecite, resolving each
   reference back to its authority.
2. **Build** the complete Table of Authorities from a versioned court
   profile (Federal Appellate / FRAP by default): grouped, sorted,
   *passim*-thresholded, formatted.
3. **Place** it deterministically — explicit setting, then a `[[TOA]]`
   marker, then the profile's heading variants — and refuse to guess if
   none of those match.
4. **Render** the document to PDF via LibreOffice and **locate** every
   citation on its actual page.
5. **Iterate to a fixed point** — re-render until no citation's page
   changes, capped with honest failure disclosure if it won't settle.
6. **Write** a copy of the brief with the corrected table as static,
   formatted content — never Word field codes, never modifying the
   original — plus the plain-text report.

Running citetab on its own output converges immediately with zero
changes. That idempotency is both the product promise and a built-in
self-test.

## What it checks and discloses

The report leads with the generated table; findings come second. Each
finding states what happened, what the tool did about it, and what (if
anything) you must do before filing. Findings carry three severities
(`error`, `warning`, `info`) and two confidence levels (`high` when
derived from the document's structure, `medium` when it depends on the
citation parser's recall).

| ID     | Name                              | Severity | What it discloses                                              |
|--------|-----------------------------------|----------|----------------------------------------------------------------|
| TT-001 | Unresolvable short-form citation  | error    | A short form with no antecedent full citation; can't be indexed |
| TT-002 | Authority missing from input TOA  | info     | An authority cited in the body but absent from the input table; added |
| TT-003 | Stale page numbers in input TOA   | info     | The input table's page references describe an older layout; corrected |
| TT-004 | Phantom input-TOA entry           | warning  | An input-table entry that matches nothing cited in the body    |
| TT-005 | TOA placement not found           | error    | No place to put the table; output `.docx` is suppressed        |
| TT-006 | Marker and heading both present   | warning  | Both a `[[TOA]]` marker and a heading exist; marker wins        |
| TT-007 | Pagination non-convergence        | error    | Pagination didn't settle within the iteration cap              |
| TT-008 | Font substitution during render   | warning  | A render font was substituted; page numbers may shift          |

---

## For developers and command-line use

Everything above describes the simple Windows app. citetab is also a
Python command-line tool, which is how developers, Linux/macOS users,
and anyone who wants to script it can run it.

### Install

citetab isn't published to PyPI yet, so install it from source:

```bash
# Requires Python 3.11+ and LibreOffice (see System requirements below)
git clone https://github.com/markhinderliter/citetab.git
cd citetab
pip install .
```

This installs the `citetab` command. (A PyPI package — `pip install citetab` —
is planned for a future release.)

### Use

```bash
# Generate: writes brief.toa.docx and brief.toa-report.md
citetab generate brief.docx

# Pick the court profile governing TOA format (default: frap)
citetab generate brief.docx --court frap

# See what the tool checks and discloses
citetab rules list
citetab rules show TT-003
```

A run looks like this:

```
$ citetab generate opposition.docx
Parsed 41 citation occurrences -> 12 authorities (Federal Appellate (FRAP))
Placement: heading "TABLE OF AUTHORITIES" (page 1)
Converged in 2 iterations.
Wrote opposition.toa.docx
Wrote opposition.toa-report.md
2 findings: 0 error - 1 warning - 1 info   (see report)
```

If your brief has no Table of Authorities section yet (common in trial-
court filings), put `[[TOA]]` on its own line where the table should go.
citetab inserts the table there and consumes the marker.

### System requirements

- **Python 3.11+**
- **LibreOffice** (headless) — a required *system* dependency, not a
  Python package. citetab measures page numbers by rendering your
  document with LibreOffice, so it must be installed and on your PATH.
  The tool fails with a clear message if it can't find it.

```bash
# Debian / Ubuntu
sudo apt install libreoffice

# macOS (Homebrew)
brew install --cask libreoffice

# Windows
winget install TheDocumentFoundation.LibreOffice
```

**For accurate page numbers, install the Microsoft fonts.** Briefs are
typically set in Times New Roman, which isn't present on most Linux
systems. LibreOffice substitutes a metric-compatible font (Liberation
Serif), which is close but can occasionally shift a citation across a
page boundary. When a substitution happens, citetab discloses it (rule
`TT-008`) so you know to double-check. Installing the real fonts removes
the ambiguity:

```bash
# Debian / Ubuntu
sudo apt install ttf-mscorefonts-installer
```

macOS and Windows generally already have these fonts.

### Project structure

```
citetab/
├── README.md                 ← you are here
├── LIABILITY.md              ← explicit positioning and disclaimers
├── LICENSE                   ← MIT + additional notice
├── CHANGELOG.md
├── CONTRIBUTING.md
├── pyproject.toml
├── docs/                     ← PRD, input/output spec, report spec, AI guardrails
├── rules/toa/                ← rule cards (Markdown), versioned
├── profiles/                 ← court profiles (YAML data, e.g. frap)
├── schemas/                  ← canonical JSON Schemas (registry, finding)
├── src/citetab/              ← engine, CLI, report renderer
├── tests/                    ← unit + integration tests, fixtures, expected output
└── examples/briefs/          ← synthetic example briefs
```

---

## Design principles

These are structural commitments, not preferences.

**Generation first.** citetab's product is the regenerated table.
Findings are disclosures around it — what was corrected, what to check —
not the point of the tool.

**Deterministic before AI.** Citation parsing, rendering, and page
measurement are deterministic. No LLM calls at generation time. The same
brief produces the same table today and a year from now.

**Local-first.** Briefs are confidential client material. No network
calls during a run, no telemetry, ever.

**Specification before code.** The input/output contract, every rule,
and every court profile is a versioned document. The implementation must
match the spec; drift fails loudly.

**Measured, not estimated.** Page numbers come from rendering the actual
document and locating each citation in the converged result — not from
heuristics, not from field codes.

## Compatibility

- Python 3.11+ · Linux, macOS, Windows
- LibreOffice 7.x / 24.x / 25.x (headless)
- No GPU, no cloud, no account
- Single brief per invocation (no batch mode in v1)

## Contributing

Contributions are welcome and held to the project's standards: type
hints with `mypy --strict`, `ruff` clean, tests for every change,
coverage at or above 85%, and the constraints in `docs/AI_GUARDRAILS.md`
(no LLM at generation time, no network calls during a run, no
page-estimation heuristics, no Word field codes in output, synthetic
fixtures only, spec before code). AI-assisted contributions are welcome
and held to exactly the same bar. See [CONTRIBUTING.md](./CONTRIBUTING.md).

## License

MIT. See [LICENSE](./LICENSE). Permissive on purpose: defensibility comes
from documentation quality and spec transparency, not license
enforcement. If a commercial vendor adopts pieces of this, that is a
positive outcome.

## Disclaimer

citetab prepares a draft Table of Authorities for attorney review. It
performs clerical document automation — locating citations and
formatting a table — and exercises no legal judgment. Its output is not
legal advice, and a generated table is not a representation that the
brief or its authorities are correct. The filing attorney is responsible
for everything filed.

See [LIABILITY.md](./LIABILITY.md) for the full positioning. It is short,
and you should actually read it.
