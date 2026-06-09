"""Tests for data-path resolution (bundled-then-repo fallback)."""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

from toatool.engine import resources


def test_resolvers_point_at_real_directories() -> None:
    """In a source checkout the resolvers find the repo-root data dirs."""
    assert (resources.rules_dir() / "toa").is_dir()
    assert (resources.profiles_dir() / "frap.yaml").is_file()
    assert (resources.schemas_dir() / "registry.schema.json").is_file()


def test_bundled_path_is_preferred(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """When a bundled copy exists it is preferred over the repo-root copy."""
    bundled_root = tmp_path / "_bundled"
    (bundled_root / "profiles").mkdir(parents=True)
    monkeypatch.setattr(resources, "_BUNDLED_ROOT", bundled_root)
    assert resources.profiles_dir() == bundled_root / "profiles"


def test_missing_everywhere_raises(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """If neither the bundled nor repo path exists, resolution fails loudly."""
    monkeypatch.setattr(resources, "_BUNDLED_ROOT", tmp_path / "nope_bundled")
    monkeypatch.setattr(resources, "_REPO_ROOT", tmp_path / "nope_repo")
    with pytest.raises(FileNotFoundError, match="not found in either"):
        resources.rules_dir()


def test_module_reimports_cleanly() -> None:
    """The module re-imports without side effects (path constants are module-level)."""
    importlib.reload(resources)
    assert resources.rules_dir().name == "rules"
