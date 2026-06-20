---
title: "citetab compared to other ways to build a Table of Authorities"
description: >-
  How citetab — a free, open-source, local Table of Authorities generator —
  compares with marking citations by hand, Microsoft Word's built-in Table of
  Authorities feature, and cloud-based TOA services. An honest look at the
  trade-offs.
permalink: /comparison/
---

# Ways to build a Table of Authorities

There are a few common ways to produce a Table of Authorities for a brief. This
page lays out the trade-offs honestly, including where citetab is **not** the
right fit.

## At a glance

| | Mark by hand in Word | Word's built-in TOA | Cloud TOA service | **citetab** |
|---|---|---|---|---|
| Cost | Free | Free | Usually paid | **Free** |
| Open source | — | No | No | **Yes (MIT)** |
| Runs locally | Yes | Yes | No (brief uploaded) | **Yes** |
| Brief stays on your computer | Yes | Yes | No | **Yes** |
| Finds citations automatically | No | Partly (after manual marking) | Yes | **Yes** |
| Court formats | You decide | You format | Often several | **Federal Appellate (FRAP) only** |
| Output | Manual table | Word field codes | Varies | **Regenerated `.docx` + report** |

The honest takeaways are below.

## Marking citations by hand

Word lets you mark each citation and then generate a table from those marks. It is
free and entirely local, but on a brief of any length it is slow and error-prone:
you read the brief, mark every citation, categorize each one, and re-check
everything when the brief changes. citetab automates the finding and formatting so
you start from a draft instead of a blank table.

## Microsoft Word's built-in Table of Authorities

Word's feature is free and runs locally, which are real advantages. Its
limitations are well known: you still mark citations manually, the result depends
on Word field codes, and keeping page numbers correct as the brief changes is
fiddly. citetab instead parses the citations for you and writes the table as
static, formatted content with measured page numbers.

## Cloud-based Table of Authorities services

Commercial cloud tools are capable and often support several courts. The trade-off
is that they are typically **paid** and require **uploading your brief to a
vendor's servers**. For confidential client material, some practitioners would
rather not upload at all. citetab is the free, local, open-source option for that
preference. If you need broad court coverage today, a cloud tool may fit your needs
better — see the next section.

## Where citetab is *not* the right fit

To be clear about the limits:

- **citetab currently supports only the Federal Appellate (FRAP-style) profile.**
  If you are filing in a court whose Table of Authorities rules differ, citetab
  does not produce a compliant table for that court today. (More profiles can be
  added later, but the tool does not claim to support them now.)
- **citetab produces a draft.** It does no legal review. An attorney or paralegal
  must check the result before filing.
- **It needs LibreOffice installed** to measure page numbers.

## Where citetab fits well

- You want a **free, open-source** tool with no subscription.
- You want your brief to **stay on your own computer** — no upload.
- You are working with **Federal Appellate (FRAP-style)** briefs.
- You want a measured, regenerated draft you can review and refine.

If that describes you, see **[Getting started]({{ '/getting-started/' | relative_url }})**
or read the **[FAQ]({{ '/faq/' | relative_url }})**.
