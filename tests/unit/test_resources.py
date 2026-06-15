"""Tests for single-source data-path resolution via importlib.resources.

The versioned data is package data under ``toatool/_bundled/``; resolvers return
a Traversable that works in a source checkout, a wheel, and a frozen app. These
tests cover the live (source-checkout) resolution and a *simulated frozen
layout* where the package resources are rooted at a temporary directory and no
repo-root copy exists — proving the single-mode resolver and the real loaders
work without the old repo-root fallback.
"""

from __future__ import annotations

import importlib
import shutil
from pathlib import Path

import pytest

from toatool.engine import resources
from toatool.engine.profile_loader import load_profile
from toatool.engine.rule_loader import load_rule_cards

_EXPECTED_RULE_CARDS = 9


def test_resolvers_resolve_and_load_in_source_checkout() -> None:
    """Resolvers return real data dirs that the actual loaders can consume."""
    assert (resources.rules_dir() / "toa").is_dir()
    assert (resources.profiles_dir() / "frap.yaml").is_file()
    assert (resources.schemas_dir() / "registry.schema.json").is_file()

    cards = load_rule_cards(resources.rules_dir())
    assert len(cards) == _EXPECTED_RULE_CARDS
    profile = load_profile(resources.profiles_dir() / "frap.yaml")
    assert profile.id == "frap"


def test_frozen_layout_resolves_and_loads(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Simulated frozen app: package data under a temp root, no repo-root copy.

    ``importlib.resources.files`` is redirected to a temporary package root that
    contains only ``_bundled/``. The resolvers and the real loaders must work
    purely off that — exercising the single-mode path with no fallback — and
    iterdir-based discovery must still find all rule cards and the profile.
    """
    real_bundled = Path(str(resources.files("toatool"))) / "_bundled"
    pkg_root = tmp_path / "frozen_pkg"
    shutil.copytree(real_bundled, pkg_root / "_bundled")

    # Redirect package-resource resolution at the temp root (a Path is a
    # Traversable), simulating where a frozen app extracts/lays out its data.
    monkeypatch.setattr(resources, "files", lambda _package: pkg_root)

    assert resources.rules_dir().is_dir()
    toa_cards = [
        entry.name
        for entry in resources.rules_dir().joinpath("toa").iterdir()
        if entry.name.endswith(".md")
    ]
    assert len(toa_cards) == _EXPECTED_RULE_CARDS

    cards = load_rule_cards(resources.rules_dir())
    assert len(cards) == _EXPECTED_RULE_CARDS

    assert resources.profiles_dir().joinpath("frap.yaml").is_file()
    profile = load_profile(resources.profiles_dir() / "frap.yaml")
    assert profile.id == "frap"


def test_missing_data_raises(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """When the package data is absent, resolution fails loudly (single-mode)."""
    monkeypatch.setattr(resources, "files", lambda _package: tmp_path / "empty")
    with pytest.raises(FileNotFoundError, match="was not found"):
        resources.rules_dir()


def test_module_reimports_cleanly() -> None:
    """The module re-imports without side effects."""
    importlib.reload(resources)
    assert resources.rules_dir().name == "rules"
