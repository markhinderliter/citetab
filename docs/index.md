---
title: "citetab — free, open-source Table of Authorities generator"
description: >-
  citetab is a free, open-source Table of Authorities generator. It builds a
  draft Table of Authorities from a Word (.docx) legal brief, runs locally on
  your own computer, and never uploads your brief. It currently targets Federal
  Appellate (FRAP-style) briefs.
permalink: /
---

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "citetab",
  "applicationCategory": "BusinessApplication",
  "operatingSystem": "Windows, macOS, Linux",
  "description": "Free, open-source Table of Authorities generator. Builds a draft Table of Authorities from a Word (.docx) legal brief, runs locally, and never uploads the brief. Currently targets Federal Appellate (FRAP-style) briefs.",
  "url": "https://github.com/markhinderliter/citetab",
  "downloadUrl": "https://github.com/markhinderliter/citetab/releases/latest/download/citetab-setup.exe",
  "softwareVersion": "0.5.0",
  "license": "https://opensource.org/licenses/MIT",
  "isAccessibleForFree": true,
  "offers": { "@type": "Offer", "price": "0", "priceCurrency": "USD" }
}
</script>
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "VideoObject",
  "name": "citetab — a free, local Table of Authorities generator",
  "description": "A short walkthrough of citetab, a free and open-source tool that generates a draft Table of Authorities from a .docx legal brief, running locally on your own computer.",
  "thumbnailUrl": "https://i.ytimg.com/vi/z78v-9oHeNM/hqdefault.jpg",
  "uploadDate": "2026-06-19",
  "contentUrl": "https://youtu.be/z78v-9oHeNM",
  "embedUrl": "https://www.youtube.com/embed/z78v-9oHeNM"
}
</script>

# A free, open-source Table of Authorities generator

<p class="lead">citetab builds a draft Table of Authorities from a Word
(<code>.docx</code>) legal brief. It runs on your own computer, never uploads
your brief, and is free and open source.</p>

<div class="btnrow">
  <a class="btn primary" href="https://github.com/markhinderliter/citetab/releases/latest/download/citetab-setup.exe">Download for Windows</a>
  <a class="btn ghost" href="{{ '/getting-started/' | relative_url }}">Getting started</a>
  <a class="btn ghost" href="https://github.com/markhinderliter/citetab">View source on GitHub</a>
</div>

<div class="video">
  <iframe src="https://www.youtube.com/embed/z78v-9oHeNM"
          title="citetab walkthrough"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowfullscreen></iframe>
</div>

## What citetab does

You give citetab a Word brief (`.docx`); it produces two files:

- **A copy of your brief** with a regenerated Table of Authorities. The page
  numbers are *measured* — citetab renders the document and locates every
  citation, including short forms, *id.*, and *supra* references — not estimated.
- **A plain-text report** listing the table it built, any corrections it made,
  and anything you should check before filing.

Citation parsing is handled by [eyecite](https://github.com/freelawproject/eyecite),
the Free Law Project's open-source citation parser.

## Why people use it

- **Free and open source.** Released under the MIT license. The full source is
  on [GitHub]({{ site.repo_url }}).
- **Runs locally — your brief never leaves your computer.** There is no upload,
  no account, no telemetry, and no network calls while it runs. Briefs are
  confidential client material, and citetab is built so they stay on your machine.
- **A real draft, not a guess.** Page numbers come from rendering the actual
  document, so the table reflects the brief as it is laid out.
- **No subscription.** It is a tool you install and run, not a hosted service.

## What it currently supports

- **Input:** Word `.docx` briefs.
- **Court format:** **Federal Appellate (FRAP-style)** Tables of Authorities.
  This is the only court profile shipped today. The profile system is designed so
  that other court profiles can be added later, but citetab does **not** currently
  claim to produce a compliant table for courts or formats other than the
  Federal Appellate / FRAP-style profile.
- **Platforms:** a double-click Windows app, plus a command-line tool for
  Windows, macOS, and Linux.

## Important: this is a drafting aid, not legal advice

citetab performs clerical document automation — locating citations and formatting
a table. It exercises no legal judgment, its output is not legal advice, and a
generated table is not a representation that the brief or its authorities are
correct. **A generated Table of Authorities is a draft for review by an attorney
or paralegal**, who remains responsible for everything filed.

---

Ready to try it? See **[Getting started]({{ '/getting-started/' | relative_url }})**,
read the **[FAQ]({{ '/faq/' | relative_url }})**, or browse the
**[source on GitHub]({{ site.repo_url }})**.
