"""Unit tests for the report mask (REPORT_SPEC §6), no render required."""

from __future__ import annotations

from citetab.report import mask_report

_SAMPLE = (
    "# citetab report — brief.docx\n"
    "\n"
    "- engine 0.5.0 · rule pack toa 1.1.0 · profile frap 1.0.0\n"
    "- input: brief.docx (sha256 0123456789ab…)\n"
    "- render: LibreOffice 24.2.7.2 headless · fonts substituted (Consolas → DejaVu)\n"
    '- placement: heading "TABLE OF AUTHORITIES"\n'
    "- pagination: converged in 1 iteration (cap 5)\n"
    "- generated: 2026-06-09T19:00:47Z\n"
    "- findings: 0 error · 1 warning · 0 info\n"
    "- output: written brief.toa.docx\n"
)


def test_mask_normalizes_timestamp_and_render_version() -> None:
    """The generated timestamp and render version are masked; the rest is intact."""
    masked = mask_report(_SAMPLE)
    assert "- generated: <MASKED>" in masked
    assert "- render: LibreOffice <VERSION> headless · fonts substituted" in masked
    # The font pair, placement, and findings lines are preserved.
    assert "Consolas → DejaVu" in masked
    assert '- placement: heading "TABLE OF AUTHORITIES"' in masked
    assert "24.2.7.2" not in masked
    assert "19:00:47" not in masked


def test_mask_is_idempotent() -> None:
    """Masking an already-masked report is a no-op."""
    once = mask_report(_SAMPLE)
    assert mask_report(once) == once


def test_two_timestamps_mask_equal() -> None:
    """Reports differing only in the masked fields are equal after masking."""
    other = _SAMPLE.replace("2026-06-09T19:00:47Z", "2099-01-01T00:00:00Z").replace(
        "24.2.7.2", "7.6.0.1"
    )
    assert other != _SAMPLE
    assert mask_report(other) == mask_report(_SAMPLE)
