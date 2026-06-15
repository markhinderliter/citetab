"""Resolve the paths to toatool's versioned data: rules, profiles, schemas.

The versioned data (``rules/``, ``profiles/``, ``schemas/``) is the single
source of truth under ``src/toatool/_bundled/`` and ships as ordinary package
data. Each resolver returns it via :func:`importlib.resources.files`, which
resolves correctly in a source/editable checkout, an installed wheel, and a
frozen app (PyInstaller / Briefcase, including zipimport).

The functions return :class:`~importlib.resources.abc.Traversable`, not
``pathlib.Path``: a zipped resource has no real filesystem path. Consumers must
therefore use Traversable operations (``/``, ``is_dir``, ``is_file``,
``iterdir``, ``read_text``) and avoid ``Path``-only APIs such as ``glob`` and
``stem``.
"""

from __future__ import annotations

from importlib.resources import files
from importlib.resources.abc import Traversable

_PACKAGE = "toatool"
"""The import package whose data tree we resolve against."""

_BUNDLED = "_bundled"
"""The package subdirectory holding the versioned data."""


def _resolve(kind: str) -> Traversable:
    """Return the bundled data directory for a data ``kind``.

    Args:
        kind: One of ``"rules"``, ``"profiles"``, or ``"schemas"``.

    Returns:
        The ``toatool/_bundled/<kind>`` directory as a Traversable.

    Raises:
        FileNotFoundError: If the directory is not present in the package data.
    """
    bundled = files(_PACKAGE) / _BUNDLED / kind
    if not bundled.is_dir():
        raise FileNotFoundError(
            f"toatool data directory '{kind}' was not found at '{bundled}'. "
            f"The installation may be incomplete."
        )
    return bundled


def rules_dir() -> Traversable:
    """Return the ``rules`` directory (containing ``README.md`` and ``toa/``)."""
    return _resolve("rules")


def profiles_dir() -> Traversable:
    """Return the ``profiles`` directory (containing ``frap.yaml``)."""
    return _resolve("profiles")


def schemas_dir() -> Traversable:
    """Return the ``schemas`` directory (finding + registry JSON Schemas)."""
    return _resolve("schemas")
