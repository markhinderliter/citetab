"""LibreOffice ``-env:UserInstallation`` URI construction — the Windows bug regression.

The original code built the profile-dir argument with a bare interpolation,
``f"-env:UserInstallation=file://{profile_dir}"``. On POSIX the absolute path's
leading ``/`` made that a valid ``file:///…`` URI by coincidence; on Windows it
produced ``file://C:\\…`` (``C:`` parsed as the authority, backslashes invalid),
which LibreOffice misreports as "bootstrap.ini is corrupt". These tests assert
the cross-platform ``.as_uri()`` form is well-formed for Windows AND byte-stable
for POSIX, and that the rendered command uses it.

NOTE: these run on Linux and prove the URI is well-FORMED for Windows. They do
NOT prove LibreOffice on Windows accepts it and renders — that is
verified-pending-VM (rebuild the Windows artifact, re-test in the VM).
"""

from __future__ import annotations

from pathlib import Path, PurePosixPath, PureWindowsPath
from types import SimpleNamespace
from typing import Any

import pytest

from citetab.pipeline import renderer


def test_windows_path_yields_wellformed_file_uri() -> None:
    """A Windows path → file:///C:/… (three slashes, forward slashes, drive after)."""
    assert (
        PureWindowsPath("C:/Users/me/_lo_profile").as_uri()
        == "file:///C:/Users/me/_lo_profile"
    )


def test_windows_path_with_spaces_is_percent_encoded() -> None:
    """Spaces in the path are percent-encoded — the latent bug as_uri() also fixes."""
    assert (
        PureWindowsPath("C:/Users/First Last/_lo_profile").as_uri()
        == "file:///C:/Users/First%20Last/_lo_profile"
    )


def test_posix_path_is_byte_identical_to_legacy_string() -> None:
    """On POSIX, as_uri() reproduces exactly what the old f"file://{path}" produced."""
    posix = PurePosixPath("/tmp/abc/_lo_profile")
    assert posix.as_uri() == "file:///tmp/abc/_lo_profile"
    assert posix.as_uri() == f"file://{posix}"  # the working Linux path is unchanged


def test_helper_resolves_and_returns_file_uri(tmp_path: Path) -> None:
    """The helper guards as_uri()'s absolute-path requirement with .resolve()."""
    profile_dir = tmp_path / "_lo_profile"
    uri = renderer._user_installation_uri(profile_dir)
    assert uri == profile_dir.resolve().as_uri()
    assert uri.startswith("file:///")
    assert "\\" not in uri


def test_render_command_uses_wellformed_user_installation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The soffice command carries a well-formed file:// URI, with no backslashes."""
    captured: dict[str, list[str]] = {}

    def fake_run(cmd: list[str], **_kwargs: Any) -> SimpleNamespace:
        captured["cmd"] = cmd
        return SimpleNamespace(stdout="", stderr="")  # no PDF written → RenderError

    monkeypatch.setattr(renderer, "find_libreoffice", lambda: "/usr/bin/soffice")
    monkeypatch.setattr(renderer.subprocess, "run", fake_run)

    with pytest.raises(renderer.RenderError):
        renderer.render_to_pdf(tmp_path / "working.docx", tmp_path)

    arg = next(a for a in captured["cmd"] if a.startswith("-env:UserInstallation="))
    uri = arg.split("=", 1)[1]
    assert uri.startswith("file:///")
    assert "\\" not in uri
    assert uri == (tmp_path / "_lo_profile").resolve().as_uri()
