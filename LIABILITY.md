# Positioning and Limitations

This document exists to be unmissable. Anyone using citetab to prepare a
Table of Authorities for a document that will be filed should read it
first. It is short on purpose.

## What citetab is

citetab is a **Table of Authorities generator** for legal briefs. It
parses the citations in a `.docx`, measures where each one falls by
rendering the actual document, and writes back a court-rule-compliant
table plus a report of what it changed. It performs clerical document
automation — locating citations and formatting a table — and exercises no
legal judgment. It is open-source software, provided as-is, by independent
authors who are not lawyers and are not acting as your counsel.

## What citetab is not

### Not legal advice

A generated Table of Authorities is not a representation that the brief,
its citations, or its authorities are correct. citetab does not check
whether a case is good law, whether a quotation is accurate, whether a
pincite is right, or whether an authority supports the proposition it is
cited for. It indexes what is in the document. Do not treat its output as
a substitute for cite-checking or for the judgment of the responsible
attorney.

### Not a guarantee of a correct or complete table

citetab builds the table from the citations its parser
([eyecite](https://github.com/freelawproject/eyecite)) recognizes. If a
citation is malformed, unusually formatted, or otherwise unrecognized, it
will be absent from the table — and citetab will say so in the report
where it can detect the consequence (see TT-001, TT-002, TT-004). A clean
report does not mean every authority was captured; it means the tool
detected no problem among the things it checks. **The filing attorney is
responsible for confirming the table is complete and correct before
filing.**

### Not authoritative on court rules

v1 ships a single court profile (FRAP). State, SCOTUS, and local profiles
are deferred (see the README and `docs/PRD.md`). Even within FRAP, the
profile encodes a good-faith reading of the formatting conventions as of
the profile's version; rules change and courts vary. Confirm the table
satisfies the rules of the specific court you are filing in.

### Page numbers are measured, not certified

citetab computes page numbers by rendering your document with LibreOffice
and locating each citation in the result. LibreOffice's layout is very
close to Microsoft Word's but not pixel-identical — chiefly because of font
substitution when Microsoft fonts are absent. When a substitution occurs,
citetab discloses it (TT-008) precisely because it can move a citation
across a page boundary. For exact parity, render with the same fonts your
filing environment uses (see the README's "System requirements"). A page
number in the generated table is the page the citation occupied **in the
render citetab performed**, which you should confirm against your filing
copy.

### Honest about what it cannot do

The tool is built to never make a silent claim. It will not insert a table
where it cannot determine the location (TT-005 suppresses the `.docx`
rather than guess); it will not claim a stable layout it did not reach
(TT-007 reports non-convergence); it will not silently drop an entry it
cannot match (TT-004 warns and removes); and it never modifies your input
file — every output is a copy. These are features, not caveats: where the
tool is uncertain, it tells you instead of pretending.

## Data handling

citetab runs locally. Your document does not leave the machine the tool
runs on. There are no network calls during a run, no telemetry, and no
update checks. That said, citetab provides no encryption at rest, access
controls, or audit logging; the security of the environment it runs in is
your responsibility.

## Liability

citetab is provided under the MIT License without warranty of any kind.
The authors are not liable for any consequences of using or relying on the
tool, including but not limited to a defective Table of Authorities in a
filed document, missed deadlines, sanctions, or any other loss arising from
reliance on its output. If you rely on citetab as part of your filing
workflow, that reliance is your responsibility.

## Reporting issues

If you believe citetab produced a wrong table or a wrong finding, please
file an issue on the GitHub repository with:

- The tool, rule-pack, and profile versions (printed at the top of any
  report)
- A **synthetic** reproduction — never a real brief or client material
- The expected behavior, with the rule or citation that supports it

Well-cited, unambiguous corrections will typically land in the next
release.

## Effective date

This document is current as of citetab engine v0.5.0, rule pack v1.0.0,
and the frap profile v1.0.0. If you are reading it in a later version,
check the CHANGELOG for any material change to positioning.
