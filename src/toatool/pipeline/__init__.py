"""The generation pipeline: parse → extract → build → render → locate → converge.

This package implements the spec §3 pipeline as one module per stage:

- :mod:`toatool.pipeline.parser` — read the ``.docx`` into typed paragraphs.
- :mod:`toatool.pipeline.placement` — detect where the TOA goes (spec §2.4).
- :mod:`toatool.pipeline.extractor` — eyecite plus the toatool recognizer seam.
- :mod:`toatool.pipeline.supplemental` — toatool's deterministic recognizer for
  citations eyecite does not model (subsection-letter statutes, court rules).
- :mod:`toatool.pipeline.resolver` — group occurrences into working authorities.
- :mod:`toatool.pipeline.input_toa_diff` — best-effort parse of the input TOA.
- :mod:`toatool.pipeline.toa_builder` — build the grouped/sorted TOA from a profile.
- :mod:`toatool.pipeline.inserter` — insert/replace the TOA in a document copy.
- :mod:`toatool.pipeline.renderer` — LibreOffice headless render + font report.
- :mod:`toatool.pipeline.locator` — pdfplumber page location of occurrences.
- :mod:`toatool.pipeline.convergence` — the fixed-point orchestrator (spec §3.2).

The canonical :class:`~toatool.models.registry.CitationRegistry` is frozen once,
after the loop settles — the pipeline accumulates pages in mutable working
structures (:mod:`toatool.pipeline.working`) and converts them in a single step.
"""

from __future__ import annotations
