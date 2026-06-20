---
title: "Getting started with citetab"
description: >-
  How to install and run citetab, the free, local Table of Authorities
  generator. Install LibreOffice, download the Windows installer, and generate a
  draft Table of Authorities from a .docx brief. Command-line install from source
  is also covered.
permalink: /getting-started/
---

# Getting started

citetab is a free, local tool that builds a draft Table of Authorities from a
Word (`.docx`) brief. You install two free programs once — LibreOffice and
citetab — then pick a brief and go.

## Windows app

### 1. Install LibreOffice first

citetab measures the real page numbers in your brief by opening it the way a word
processor does. It uses **LibreOffice** — a free, open-source office suite — to do
that, quietly in the background. Your brief is opened only on your own computer
and is never uploaded.

1. Go to **[libreoffice.org](https://www.libreoffice.org/)** and download the
   Windows installer.
2. Run it and accept the standard options. You don't need to open or learn
   LibreOffice — citetab uses it for you.

If you skip this step, citetab will tell you LibreOffice is missing and point you
back here.

### 2. Download and install citetab

1. **[Download citetab-setup.exe]({{ site.download_url }})** — this downloads the
   installer directly (look in your Downloads folder).
2. Double-click it to install. citetab installs like any normal Windows program
   and adds itself to your Start menu.

**About the Windows security warning.** citetab is new and not yet
certificate-signed, so Windows may show a blue *"Windows protected your PC"*
screen. That is Windows being cautious about software it doesn't recognize yet —
citetab is open source and runs entirely on your computer. To continue, click
**More info**, then **Run anyway**.

### 3. Run it on a brief

1. Open **citetab** from the Start menu.
2. A file window opens — choose the Word brief (`.docx`) you want to process and
   click **Open**.
3. citetab works for a few seconds. **You won't see a window while it works —
   this is normal.** It is rendering your document to measure page numbers. When
   it finishes, a results box appears.
4. The results box tells you where your new files are, which court format was
   applied (**"Court profile: Federal Appellate (FRAP)"**), and whether there is
   anything to review.

citetab processes **one brief per run**. To do another, open citetab again.

### Your two new files

citetab saves two files **in the same folder as the brief you picked**:

| File | What it is |
|------|------------|
| `{yourbrief}.toa.docx` | Your brief with the regenerated Table of Authorities — the one you file. |
| `{yourbrief}.toa-report.md` | A plain-text summary of what citetab did and anything to check before filing. |

The report is a plain-text file (`.md`). You can open it with **Notepad**; for a
formatted view, open it in a Markdown viewer. citetab does not change your
original brief — it only writes these two new files.

## Command-line (Windows, macOS, Linux)

citetab is also a Python command-line tool. It isn't published to PyPI yet, so
install it from source:

```bash
# Requires Python 3.11+ and LibreOffice
git clone https://github.com/markhinderliter/citetab.git
cd citetab
pip install .
```

Then run it:

```bash
# Writes brief.toa.docx and brief.toa-report.md next to the input
citetab generate brief.docx

# The Federal Appellate (FRAP) profile is the default
citetab generate brief.docx --court frap
```

If your brief has no Table of Authorities section yet (common in trial-court
filings), put `[[TOA]]` on its own line where the table should go; citetab
inserts the table there.

## Need help?

- Read the **[FAQ]({{ '/faq/' | relative_url }})**.
- Open an issue or browse the code on **[GitHub]({{ site.repo_url }})**.
