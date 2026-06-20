---
title: "citetab FAQ"
description: >-
  Frequently asked questions about citetab, the free, open-source, local Table
  of Authorities generator: cost, privacy, supported courts, file types, and how
  it fits alongside attorney and paralegal review.
permalink: /faq/
---

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Is citetab free?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Yes. citetab is free and open source, released under the MIT license. There is no subscription and no account. The full source code is available on GitHub."
      }
    },
    {
      "@type": "Question",
      "name": "Does citetab upload my brief anywhere?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "No. citetab runs locally on your own computer. It makes no network calls while it runs, has no telemetry, and never uploads your brief. Your client's document stays on your machine."
      }
    },
    {
      "@type": "Question",
      "name": "Which courts and formats does citetab support?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "citetab currently ships one court profile: Federal Appellate (FRAP-style) Tables of Authorities. The profile system is designed so additional court profiles can be added later, but citetab does not currently produce a table for courts or formats other than the Federal Appellate / FRAP-style profile."
      }
    },
    {
      "@type": "Question",
      "name": "Does citetab replace an attorney or paralegal?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "No. citetab produces a draft Table of Authorities for review. It performs clerical document automation and exercises no legal judgment. Its output is not legal advice, and the filing attorney remains responsible for everything filed."
      }
    },
    {
      "@type": "Question",
      "name": "What file types does citetab accept?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "citetab reads Word .docx briefs and writes a regenerated .docx plus a plain-text report."
      }
    },
    {
      "@type": "Question",
      "name": "What do I need to run citetab?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "On Windows, install LibreOffice (free) and then the citetab installer. citetab uses LibreOffice in the background to measure real page numbers. citetab is also a Python command-line tool for Windows, macOS, and Linux."
      }
    },
    {
      "@type": "Question",
      "name": "Is citetab on PyPI?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Not yet. For now, install the command-line tool from source by cloning the GitHub repository and running pip install. A PyPI package is planned for a future release."
      }
    },
    {
      "@type": "Question",
      "name": "Is citetab really open source?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Yes. citetab is licensed under the MIT license and the complete source code is public on GitHub."
      }
    }
  ]
}
</script>

# Frequently asked questions

## Is citetab free?

Yes. citetab is **free and open source**, released under the MIT license. There is
no subscription and no account. The full source code is on
[GitHub]({{ site.repo_url }}).

## Does citetab upload my brief anywhere?

**No.** citetab runs locally on your own computer. It makes no network calls while
it runs, has no telemetry, and never uploads your brief. Your client's document
stays on your machine.

## Which courts and formats does citetab support?

citetab currently ships **one court profile: Federal Appellate (FRAP-style)**
Tables of Authorities. The profile system is designed so additional court profiles
can be added later, but citetab does **not** currently produce a table for courts
or formats other than the Federal Appellate / FRAP-style profile. If you need a
different court's format, treat the output accordingly and review it carefully.

## Does citetab replace an attorney or paralegal?

**No.** citetab produces a **draft** Table of Authorities for review. It performs
clerical document automation and exercises no legal judgment. Its output is not
legal advice, and the filing attorney remains responsible for everything filed.

## What file types does citetab accept?

citetab reads Word **`.docx`** briefs and writes a regenerated `.docx` plus a
plain-text report (`.md`).

## What do I need to run citetab?

On Windows, install **LibreOffice** (free) and then the citetab installer. citetab
uses LibreOffice in the background to measure real page numbers. citetab is also a
Python command-line tool for Windows, macOS, and Linux. See
[Getting started]({{ '/getting-started/' | relative_url }}).

## Is citetab on PyPI?

Not yet. For now, install the command-line tool from source by cloning the
[GitHub repository]({{ site.repo_url }}) and running `pip install .`. A PyPI
package is planned for a future release.

## Is citetab really open source?

Yes. citetab is licensed under the **MIT** license and the complete source code is
public on [GitHub]({{ site.repo_url }}).

## Where can I see it in action?

There is a short [walkthrough video](https://youtu.be/CJgonPrqSo0), and the
[Getting started]({{ '/getting-started/' | relative_url }}) page covers
installation and a first run.
