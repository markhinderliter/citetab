"""render_engine_info must never crash the run on a version-query failure.

Version detection is provenance/cosmetic. On Windows the GUI launcher
``soffice.exe`` hangs on ``--version`` (the console sibling ``soffice.com`` is
preferred there), but ANY query or parse failure must degrade to
``("LibreOffice", "unknown")`` rather than propagate — otherwise a 60s hang then
an uncaught ``TimeoutExpired`` kills the whole run (the confirmed Windows crash).

These simulate the failure modes by monkeypatching ``subprocess.run`` and
``find_libreoffice``, so they run anywhere with no real LibreOffice. The
``.com`` path-selection (Fix 2) is checked purely with Windows-style paths via
``PureWindowsPath`` (Linux-runnable, same technique as the URI fix). Whether
``soffice.com --version`` actually returns fast on real Windows is VM-only.
"""

from __future__ import annotations

import subprocess
from typing import Any

import pytest

from citetab.pipeline import renderer


def _fake_lo(
    monkeypatch: pytest.MonkeyPatch, path: str = "/opt/lo/program/soffice"
) -> None:
    """Pretend LibreOffice is discovered at ``path`` (no real discovery/render)."""
    monkeypatch.setattr(renderer, "find_libreoffice", lambda: path)


# --------------------------------------------------------------------------- #
# Fix 1 — the guard: a version-query failure degrades, never propagates
# --------------------------------------------------------------------------- #


def test_version_degrades_on_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    """The confirmed crash: TimeoutExpired must degrade to 'unknown', not raise."""
    _fake_lo(monkeypatch)

    def boom(*_a: Any, **_k: Any) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(cmd="soffice --version", timeout=60)

    monkeypatch.setattr(renderer.subprocess, "run", boom)
    assert renderer.render_engine_info() == ("LibreOffice", "unknown")


def test_version_degrades_on_filenotfound(monkeypatch: pytest.MonkeyPatch) -> None:
    """A missing/again-unusable executable degrades (FileNotFoundError ⊂ OSError)."""
    _fake_lo(monkeypatch)

    def boom(*_a: Any, **_k: Any) -> subprocess.CompletedProcess[str]:
        raise FileNotFoundError("soffice")

    monkeypatch.setattr(renderer.subprocess, "run", boom)
    assert renderer.render_engine_info() == ("LibreOffice", "unknown")


def test_version_degrades_on_oserror(monkeypatch: pytest.MonkeyPatch) -> None:
    """Any OSError degrades rather than crashing the run."""
    _fake_lo(monkeypatch)

    def boom(*_a: Any, **_k: Any) -> subprocess.CompletedProcess[str]:
        raise OSError("permission denied")

    monkeypatch.setattr(renderer.subprocess, "run", boom)
    assert renderer.render_engine_info() == ("LibreOffice", "unknown")


def test_version_parses_successful_output(monkeypatch: pytest.MonkeyPatch) -> None:
    """Unchanged behavior: a successful --version call still parses the number."""
    _fake_lo(monkeypatch)

    def ok(*a: Any, **_k: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=a[0], returncode=0, stdout="LibreOffice 24.2.7.2 abc\n", stderr=""
        )

    monkeypatch.setattr(renderer.subprocess, "run", ok)
    assert renderer.render_engine_info() == ("LibreOffice", "24.2.7.2")


def test_version_unknown_when_output_unparseable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A successful call with no recognizable version → 'unknown' (unchanged)."""
    _fake_lo(monkeypatch)

    def ok(*a: Any, **_k: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=a[0], returncode=0, stdout="something unexpected\n", stderr=""
        )

    monkeypatch.setattr(renderer.subprocess, "run", ok)
    assert renderer.render_engine_info() == ("LibreOffice", "unknown")


def test_missing_libreoffice_still_propagates(monkeypatch: pytest.MonkeyPatch) -> None:
    """A genuine not-found is NOT masked as 'unknown' — it still raises RenderError.

    Guards that the guard didn't over-catch: the missing-dependency path (handled
    upstream by run_generation) must survive.
    """

    def missing() -> str:
        raise renderer.RenderError("LibreOffice was not found.")

    monkeypatch.setattr(renderer, "find_libreoffice", missing)
    with pytest.raises(renderer.RenderError, match="not found"):
        renderer.render_engine_info()


# --------------------------------------------------------------------------- #
# Fix 2 — .com sibling selection (pure path logic, Windows-style, Linux-runnable)
# --------------------------------------------------------------------------- #


def test_com_sibling_for_windows_exe() -> None:
    """A Windows soffice.exe yields its soffice.com sibling in the same dir."""
    exe = r"C:\Program Files\LibreOffice\program\soffice.exe"
    assert (
        renderer._soffice_com_sibling(exe)
        == r"C:\Program Files\LibreOffice\program\soffice.com"
    )


def test_com_sibling_case_insensitive() -> None:
    """Windows names are case-insensitive: SOFFICE.EXE → soffice.com."""
    assert renderer._soffice_com_sibling(r"C:\LO\SOFFICE.EXE") == r"C:\LO\soffice.com"


def test_com_sibling_none_for_posix() -> None:
    """POSIX binaries are not soffice.exe → no .com preference (None)."""
    assert renderer._soffice_com_sibling("/usr/bin/soffice") is None
    assert renderer._soffice_com_sibling("/usr/bin/libreoffice") is None


def test_version_executable_unchanged_on_posix() -> None:
    """The version-query executable is the discovered one on POSIX (no .com)."""
    assert renderer._version_query_executable("/usr/bin/soffice") == "/usr/bin/soffice"


def test_version_executable_prefers_existing_com(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Any
) -> None:
    """When a .com sibling EXISTS, the version query targets it (Windows case).

    Uses a real existing file as the sibling and stubs the pure transform to point
    at it, so the existence-gated selection is exercised on Linux. (The pure
    name→.com mapping is covered above; that .com actually returns fast on real
    Windows is VM-pending.)
    """
    com = tmp_path / "soffice.com"
    com.write_text("", encoding="utf-8")
    monkeypatch.setattr(renderer, "_soffice_com_sibling", lambda _exe: str(com))
    assert renderer._version_query_executable(r"C:\LO\soffice.exe") == str(com)


def test_version_executable_falls_back_when_com_absent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If the computed .com sibling does not exist, fall back to the executable."""
    monkeypatch.setattr(
        renderer, "_soffice_com_sibling", lambda _exe: "/nope/soffice.com"
    )
    exe = "/real/soffice.exe"
    assert renderer._version_query_executable(exe) == exe
