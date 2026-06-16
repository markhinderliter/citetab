"""Build the searchable body text and map spans back to paragraphs.

Citation extraction runs over the body text — every paragraph *except* the TOA
region (or the marker paragraph), so the input table's own entries are not
mistaken for body occurrences. The paragraphs are concatenated in document order
(eyecite resolves short forms against the full citations that precede them, which
requires continuous text), and an offset map converts any global character span
back to a ``(paragraph_index, char_span)`` pair for the registry and evidence.
"""

from __future__ import annotations

from dataclasses import dataclass

from citetab.pipeline.parser import ParsedDocument

_SEPARATOR = "\n"


class EmptyDocumentError(Exception):
    """Raised when the document has no readable body text to scan for citations.

    A valid but text-empty ``.docx`` (a scanned/image-only brief, or a document
    whose body is genuinely empty) has nothing for the resolver to read. This is
    an unprocessable input — surfaced as a clean ``exit 2`` with OCR guidance,
    not a TOA-placement finding (QA Round 3, C1-i).
    """


@dataclass(frozen=True)
class BodyText:
    """The concatenated body text plus a paragraph offset map."""

    text: str
    _starts: tuple[int, ...]
    _indices: tuple[int, ...]

    def to_para_span(self, start: int, end: int) -> tuple[int, tuple[int, int]]:
        """Map a global character span to ``(paragraph_index, local_span)``.

        Args:
            start: Global start offset within :attr:`text`.
            end: Global end offset within :attr:`text`.

        Returns:
            The original paragraph index and the span relative to that
            paragraph's start.
        """
        position = 0
        for position in range(len(self._starts) - 1, -1, -1):
            if self._starts[position] <= start:
                break
        para_start = self._starts[position]
        return self._indices[position], (start - para_start, end - para_start)


def build_body(doc: ParsedDocument, excluded_indices: set[int]) -> BodyText:
    """Concatenate the body paragraphs (excluding the TOA region) with offsets.

    Args:
        doc: The parsed document.
        excluded_indices: Paragraph indices to exclude (the TOA region or marker).

    Returns:
        A :class:`BodyText` with the concatenated text and its offset map.
    """
    chunks: list[str] = []
    starts: list[int] = []
    indices: list[int] = []
    cursor = 0
    for para in doc.paragraphs:
        if para.index in excluded_indices:
            continue
        starts.append(cursor)
        indices.append(para.index)
        chunks.append(para.text)
        cursor += len(para.text) + len(_SEPARATOR)
    return BodyText(
        text=_SEPARATOR.join(chunks),
        _starts=tuple(starts),
        _indices=tuple(indices),
    )
