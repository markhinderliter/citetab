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

import os
import re
import shutil
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path

_RENDER_TIMEOUT_S = 120
_FONT_ATTR_RE = re.compile(r'w:(?:ascii|hAnsi|cs)="([^"]+)"')

#: Environment variable holding an explicit path to the LibreOffice executable.
#: When set it overrides discovery; if it points at a non-executable it fails
#: loudly rather than falling through (an explicit override that's wrong is a
#: configuration error, not a reason to silently search elsewhere).
_LIBREOFFICE_ENV = "CITETAB_LIBREOFFICE"

#: LibreOffice download page, surfaced when no installation can be located.
_LIBREOFFICE_URL = "https://www.libreoffice.org/download/"


class RenderError(Exception):
    """Raised when LibreOffice is unavailable or rendering fails."""


@dataclass(frozen=True)
class FontSubstitution:
    """A declared font and the family the renderer used in its place."""

    original: str
    substitute: str


def _is_executable(path: str) -> bool:
    """Return whether ``path`` is an existing, executable file.

    On Windows ``os.access(..., X_OK)`` is satisfied by any existing file, which
    is the desired behavior for ``soffice.exe``.
    """
    return os.path.isfile(path) and os.access(path, os.X_OK)


def _standard_install_paths() -> tuple[str, ...]:
    """Return the standard install locations to probe, ordered, for this OS.

    The Windows LibreOffice installer does not add itself to ``PATH``, so the
    well-known install directory is probed directly. macOS apps live under
    ``/Applications``. Linux is intentionally empty: distro packages place
    ``libreoffice``/``soffice`` on ``PATH``, which the fallback already covers.
    """
    if sys.platform == "win32":
        return (
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        )
    if sys.platform == "darwin":
        return ("/Applications/LibreOffice.app/Contents/MacOS/soffice",)
    return ()


def find_libreoffice() -> str:
    """Return the path to the LibreOffice executable via ordered discovery.

    Discovery order, first hit wins:

    1. The ``CITETAB_LIBREOFFICE`` environment variable. If set but not
       executable, this raises — an explicit override that is wrong fails
       loudly rather than silently falling through.
    2. Standard per-OS install locations (see :func:`_standard_install_paths`).
    3. ``PATH`` (``shutil.which`` for ``libreoffice`` then ``soffice``).

    Raises:
        RenderError: If the ``CITETAB_LIBREOFFICE`` override is set but not
            executable, or if no LibreOffice can be located by any means.
    """
    override = os.environ.get(_LIBREOFFICE_ENV)
    if override:
        if _is_executable(override):
            return override
        raise RenderError(
            f"{_LIBREOFFICE_ENV} is set to '{override}', but that is not an "
            f"executable file. Point it at the full path of the LibreOffice "
            f"'soffice' executable, or unset it to use automatic discovery."
        )

    for path in _standard_install_paths():
        if _is_executable(path):
            return path

    for name in ("libreoffice", "soffice"):
        found = shutil.which(name)
        if found is not None:
            return found

    raise RenderError(
        "LibreOffice was not found. It is a required system dependency for "
        f"measuring page numbers. Install it from {_LIBREOFFICE_URL} (see the "
        "README 'System requirements' section), or set the "
        f"{_LIBREOFFICE_ENV} environment variable to the full path of the "
        "'soffice' executable, and try again."
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


def _user_installation_uri(profile_dir: Path) -> str:
    r"""Return ``profile_dir`` as a ``file://`` URI for ``-env:UserInstallation``.

    LibreOffice requires this argument to be a URL, not a native path. A bare
    ``file://`` + path interpolation only works on POSIX by accident (the leading
    ``/`` supplies the third slash); on Windows it yields ``file://C:\…`` —
    ``C:`` read as the authority, backslashes invalid — which LibreOffice
    misreports as "bootstrap.ini is corrupt". :meth:`~pathlib.Path.as_uri` emits
    the correct RFC 8089 form on both platforms (``file:///C:/…`` on Windows,
    ``file:///…`` on POSIX, byte-identical to the legacy string there) and
    percent-encodes spaces. ``resolve()`` satisfies ``as_uri()``'s requirement of
    an absolute path.
    """
    return profile_dir.resolve().as_uri()


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
        f"-env:UserInstallation={_user_installation_uri(profile_dir)}",
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
