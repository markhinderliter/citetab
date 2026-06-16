"""Ordered LibreOffice discovery: env override → standard locations → PATH.

These tests are deterministic and OS-independent: the filesystem probe
(``_is_executable``), the per-OS candidate list (``_standard_install_paths``),
and ``shutil.which`` are all monkeypatched, so they never depend on the test
machine actually having LibreOffice, a real ``Program Files``, or a real
``/Applications``.
"""

from __future__ import annotations

import pytest

from citetab.pipeline import renderer

_ENV = "CITETAB_LIBREOFFICE"


def _no_standard_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make the standard-install probe find nothing."""
    monkeypatch.setattr(renderer, "_standard_install_paths", lambda: ())


def _which_none(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make the PATH probe find nothing."""
    monkeypatch.setattr(renderer.shutil, "which", lambda _name: None)


def test_env_override_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    """An executable CITETAB_LIBREOFFICE path is returned before any other probe."""
    override = "/custom/soffice"
    monkeypatch.setenv(_ENV, override)
    monkeypatch.setattr(renderer, "_is_executable", lambda p: p == override)
    # Standard locations and PATH would also "succeed" — prove they are not consulted.
    monkeypatch.setattr(
        renderer, "_standard_install_paths", lambda: ("/should/not/use",)
    )
    monkeypatch.setattr(renderer.shutil, "which", lambda _name: "/should/not/use")

    assert renderer.find_libreoffice() == override


def test_env_override_set_but_bad_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """A set-but-non-executable override fails loudly, naming the bad path."""
    bad = "/nope/soffice"
    monkeypatch.setenv(_ENV, bad)
    monkeypatch.setattr(renderer, "_is_executable", lambda _p: False)
    # A real binary on PATH must NOT rescue a bad explicit override.
    monkeypatch.setattr(renderer.shutil, "which", lambda _name: "/usr/bin/soffice")

    with pytest.raises(renderer.RenderError, match=bad):
        renderer.find_libreoffice()


def test_standard_location_used_when_path_misses(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """With no env var and nothing on PATH, a standard install location is found."""
    monkeypatch.delenv(_ENV, raising=False)
    installed = r"C:\Program Files\LibreOffice\program\soffice.exe"
    monkeypatch.setattr(renderer, "_standard_install_paths", lambda: (installed,))
    monkeypatch.setattr(renderer, "_is_executable", lambda p: p == installed)
    _which_none(monkeypatch)

    assert renderer.find_libreoffice() == installed


def test_path_fallback_still_works(monkeypatch: pytest.MonkeyPatch) -> None:
    """With no env var and no standard location, the PATH lookup is used."""
    monkeypatch.delenv(_ENV, raising=False)
    _no_standard_paths(monkeypatch)
    monkeypatch.setattr(renderer, "_is_executable", lambda _p: False)
    monkeypatch.setattr(
        renderer.shutil,
        "which",
        lambda name: "/usr/bin/libreoffice" if name == "libreoffice" else None,
    )

    assert renderer.find_libreoffice() == "/usr/bin/libreoffice"


def test_nothing_found_raises_broadened_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When every probe misses, the error names the env var and the download URL."""
    monkeypatch.delenv(_ENV, raising=False)
    _no_standard_paths(monkeypatch)
    monkeypatch.setattr(renderer, "_is_executable", lambda _p: False)
    _which_none(monkeypatch)

    with pytest.raises(renderer.RenderError) as exc:
        renderer.find_libreoffice()
    message = str(exc.value)
    assert _ENV in message
    assert "libreoffice.org" in message
