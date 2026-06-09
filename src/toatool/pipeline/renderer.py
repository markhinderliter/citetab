"""Render a document to PDF via LibreOffice headless, and report font issues.

Page numbers are *measured*, not estimated (the product thesis): the working
document is laid out by a real renderer and the citations are located in the
result. LibreOffice is a required local **system** dependency; if it is absent
the tool fails with a clear, actionable message (FR-07).

Font substitution is detected deterministically via fontconfig: each font the
document declares is resolved with ``fc-match``; when the resolved family differs
from the requested one, the renderer used a substitute (e.g. Liberation Serif for
Times New Roman), which can shift marginal page boundaries and drives TT-008. No
network access is used anywhere here.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import zipfile
from dataclasses import dataclass
from pathlib import Path

_RENDER_TIMEOUT_S = 120
_FONT_ATTR_RE = re.compile(r'w:(?:ascii|hAnsi|cs)="([^"]+)"')


class RenderError(Exception):
    """Raised when LibreOffice is unavailable or rendering fails."""


@dataclass(frozen=True)
class FontSubstitution:
    """A declared font and the family the renderer used in its place."""

    original: str
    substitute: str


def find_libreoffice() -> str:
    """Return the path to the LibreOffice executable.

    Raises:
        RenderError: If neither ``libreoffice`` nor ``soffice`` is on PATH.
    """
    for name in ("libreoffice", "soffice"):
        path = shutil.which(name)
        if path is not None:
            return path
    raise RenderError(
        "LibreOffice was not found on PATH. It is a required system dependency "
        "for measuring page numbers; install it (see the README 'System "
        "requirements' section) and try again."
    )


def render_engine_info() -> tuple[str, str]:
    """Return the render engine identity and version (``("LibreOffice", "24.2…")``)."""
    executable = find_libreoffice()
    result = subprocess.run(  # noqa: S603 - fixed executable, no shell
        [executable, "--version"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    match = re.search(r"LibreOffice\s+([0-9][0-9.]*)", result.stdout)
    return "LibreOffice", match.group(1) if match else "unknown"


def render_to_pdf(docx_path: Path, out_dir: Path) -> Path:
    """Render a ``.docx`` to PDF in ``out_dir`` and return the PDF path.

    Args:
        docx_path: The document to render.
        out_dir: Directory to write the PDF (and a throwaway LO profile) into.

    Returns:
        Path to the produced PDF.

    Raises:
        RenderError: If LibreOffice is missing, errors, or produces no PDF.
    """
    executable = find_libreoffice()
    profile_dir = out_dir / "_lo_profile"
    command = [
        executable,
        "--headless",
        "--norestore",
        "--nolockcheck",
        f"-env:UserInstallation=file://{profile_dir}",
        "--convert-to",
        "pdf",
        "--outdir",
        str(out_dir),
        str(docx_path),
    ]
    try:
        result = subprocess.run(  # noqa: S603 - fixed executable, no shell
            command,
            capture_output=True,
            text=True,
            timeout=_RENDER_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired as exc:
        raise RenderError(
            f"LibreOffice timed out rendering '{docx_path}' after {_RENDER_TIMEOUT_S}s"
        ) from exc

    pdf_path = out_dir / f"{docx_path.stem}.pdf"
    if not pdf_path.is_file():
        raise RenderError(
            f"LibreOffice did not produce a PDF for '{docx_path}'. "
            f"stderr: {result.stderr.strip() or result.stdout.strip()}"
        )
    return pdf_path


def _referenced_fonts(docx_path: Path) -> set[str]:
    """Return the set of font family names the document references."""
    fonts: set[str] = set()
    with zipfile.ZipFile(docx_path) as archive:
        for part in ("word/document.xml", "word/styles.xml"):
            try:
                data = archive.read(part).decode("utf-8", "ignore")
            except KeyError:
                continue
            fonts.update(_FONT_ATTR_RE.findall(data))
    return fonts


def _fc_match(font: str) -> str | None:
    """Return the family fontconfig resolves ``font`` to, or ``None`` if unavailable."""
    executable = shutil.which("fc-match")
    if executable is None:
        return None
    result = subprocess.run(  # noqa: S603 - fixed executable, no shell
        [executable, "--format=%{family}", font],
        capture_output=True,
        text=True,
        timeout=30,
    )
    family = result.stdout.strip()
    return family.split(",")[0] if family else None


def detect_font_substitutions(docx_path: Path) -> list[FontSubstitution]:
    """Detect fonts the renderer substitutes for ones the document declares.

    Args:
        docx_path: The document whose declared fonts to check.

    Returns:
        One :class:`FontSubstitution` per declared font that resolves to a
        different family, sorted by the original name. Empty when every declared
        font is available (or fontconfig is unavailable to check).
    """
    substitutions: list[FontSubstitution] = []
    for font in sorted(_referenced_fonts(docx_path)):
        resolved = _fc_match(font)
        if resolved is not None and resolved.casefold() != font.casefold():
            substitutions.append(FontSubstitution(original=font, substitute=resolved))
    return substitutions
