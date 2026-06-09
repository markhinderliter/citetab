"""Locate each citation occurrence on its rendered page (FR-07).

pdfplumber extracts the rendered text per physical page; this module concatenates
those pages into one normalized stream with a character→page map, then finds each
occurrence's verbatim text in document order with a forward-only cursor.

The forward cursor does two jobs at once: it disambiguates repeated citation text
(each occurrence matches the *next* appearance, in document order), and — started
just after the TOA region — it skips the generated table's own citation text, so
a full citation that appears both in the TOA and the body is located in the body.

A page found by exact forward match is ``high`` confidence; a fallback match
(searched from the start because the forward search missed) is ``medium``.
"""

from __future__ import annotations

import re
from pathlib import Path

import pdfplumber

from toatool.pipeline.working import WorkingOccurrence

_SECTION_RE = re.compile(r"\s*§\s*")
_WS_RE = re.compile(r"\s+")


def _normalize(text: str) -> str:
    """Normalize whitespace and section-sign spacing for robust matching."""
    return _WS_RE.sub(" ", _SECTION_RE.sub(" § ", text)).strip()


class _Stream:
    """A normalized page-text stream with a character→page map."""

    def __init__(self, page_texts: list[str]) -> None:
        parts: list[str] = []
        page_of: list[int] = []
        for page_number, text in enumerate(page_texts, start=1):
            normalized = _normalize(text)
            if parts:
                parts.append("\n")
                page_of.append(page_number)
            parts.append(normalized)
            page_of.extend([page_number] * len(normalized))
        self.text = "".join(parts)
        self.page_of = page_of

    def page_at(self, index: int) -> int:
        """Return the page number for a character index into the stream."""
        return self.page_of[index]


def _page_texts(pdf_path: Path) -> list[str]:
    """Extract per-page text from a PDF in reading order."""
    with pdfplumber.open(str(pdf_path)) as document:
        return [page.extract_text() or "" for page in document.pages]


def locate_occurrences(
    pdf_path: Path,
    occurrences: list[WorkingOccurrence],
    body_anchor: str | None,
) -> None:
    """Assign a page to each occurrence by locating it in the rendered PDF.

    Occurrences are mutated in place: ``page`` and ``confidence`` are set. They
    are processed in document order so the forward cursor stays aligned with the
    rendered reading order.

    Args:
        pdf_path: The rendered PDF.
        occurrences: All body occurrences to locate (any order; sorted here).
        body_anchor: Text of the first body paragraph after the TOA, used to move
            the cursor past the generated table. ``None`` searches from the start.
    """
    stream = _Stream(_page_texts(pdf_path))
    ordered = sorted(occurrences, key=lambda o: (o.paragraph_index, o.char_span))

    cursor = 0
    if body_anchor:
        anchor_pos = stream.text.find(_normalize(body_anchor))
        if anchor_pos >= 0:
            cursor = anchor_pos

    for occurrence in ordered:
        needle = _normalize(occurrence.raw_text)
        if not needle:
            continue
        index = stream.text.find(needle, cursor)
        if index >= 0:
            occurrence.page = stream.page_at(index)
            occurrence.confidence = "high"
            cursor = index + len(needle)
            continue
        fallback = stream.text.find(needle)
        if fallback >= 0:
            occurrence.page = stream.page_at(fallback)
            occurrence.confidence = "medium"
