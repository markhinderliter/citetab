"""Resolve the paths to toatool's versioned data: rules, profiles, schemas.

``pyproject.toml`` force-includes the ``rules``, ``profiles``, and ``schemas``
trees into the wheel under ``toatool/_bundled/`` so ``pip install toatool``
works without a clone. In a source checkout that bundled copy does not exist and
the data lives at the repository root instead. Each resolver here looks for the
bundled copy first, then falls back to the repo-root copy, and raises a clear
error if neither is present.
"""

from __future__ import annotations

from pathlib import Path

_PKG_ROOT = Path(__file__).resolve().parent.parent
"""The installed ``toatool`` package directory (``src/toatool`` in a checkout)."""

_BUNDLED_ROOT = _PKG_ROOT / "_bundled"
"""Where the wheel places the bundled data (absent in a source checkout)."""

_REPO_ROOT = _PKG_ROOT.parent.parent
"""Repository root in a source checkout (``src/toatool`` → up two levels)."""


def _resolve(kind: str) -> Path:
    """Return the directory for a data ``kind``, bundled copy preferred.

    Args:
        kind: One of ``"rules"``, ``"profiles"``, or ``"schemas"``.

    Returns:
        The resolved directory: ``toatool/_bundled/<kind>`` if it exists,
        otherwise ``<repo-root>/<kind>``.

    Raises:
        FileNotFoundError: If neither the bundled nor the repo-root copy exists.
    """
    bundled = _BUNDLED_ROOT / kind
    if bundled.is_dir():
        return bundled
    repo = _REPO_ROOT / kind
    if repo.is_dir():
        return repo
    raise FileNotFoundError(
        f"toatool data directory '{kind}' not found in either the bundled "
        f"path ({bundled}) or the repository path ({repo}). The installation "
        f"may be incomplete."
    )


def rules_dir() -> Path:
    """Return the ``rules`` directory (containing ``README.md`` and ``toa/``)."""
    return _resolve("rules")


def profiles_dir() -> Path:
    """Return the ``profiles`` directory (containing ``frap.yaml``)."""
    return _resolve("profiles")


def schemas_dir() -> Path:
    """Return the ``schemas`` directory (finding + registry JSON Schemas)."""
    return _resolve("schemas")
