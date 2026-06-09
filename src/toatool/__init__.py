"""toatool — a free, local-first Table of Authorities generator.

A ``.docx`` legal brief goes in; a copy with a regenerated, court-rule-
compliant Table of Authorities comes out, with page numbers measured from a
real LibreOffice render of the document. Everything runs locally: no network
calls during a run, no telemetry, and no LLM/ML inference anywhere in the
generation path.

``__version__`` is the canonical engine version recorded on every finding and
in every report header (the ``engine`` track of the four-track SemVer policy in
``CHANGELOG.md``). It is kept in sync with the ``version`` field in
``pyproject.toml``.
"""

from __future__ import annotations

__all__ = ["__version__"]

__version__ = "0.1.0"
