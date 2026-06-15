"""The generation pipeline: parse → extract → build → render → locate → converge.

This package implements the spec §3 pipeline as one module per stage:

- :mod:`citetab.pipeline.parser` — read the ``.docx`` into typed paragraphs.
- :mod:`citetab.pipeline.placement` — detect where the TOA goes (spec §2.4).
- :mod:`citetab.pipeline.extractor` — eyecite plus the citetab recognizer seam.
- :mod:`citetab.pipeline.supplemental` — citetab's deterministic recognizer for
  citations eyecite does not model (subsection-letter statutes, court rules).
- :mod:`citetab.pipeline.resolver` — group occurrences into working authorities.
- :mod:`citetab.pipeline.input_toa_diff` — best-effort parse of the input TOA.
- :mod:`citetab.pipeline.toa_builder` — build the grouped/sorted TOA from a profile.
- :mod:`citetab.pipeline.inserter` — insert/replace the TOA in a document copy.
- :mod:`citetab.pipeline.renderer` — LibreOffice headless render + font report.
- :mod:`citetab.pipeline.locator` — pdfplumber page location of occurrences.
- :mod:`citetab.pipeline.convergence` — the fixed-point orchestrator (spec §3.2).

The canonical :class:`~citetab.models.registry.CitationRegistry` is frozen once,
after the loop settles — the pipeline accumulates pages in mutable working
structures (:mod:`citetab.pipeline.working`) and converts them in a single step.
"""

from __future__ import annotations
