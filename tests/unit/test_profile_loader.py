"""Tests for the court-profile loader.

Validates that the FRAP profile loads into typed objects exactly as written, and
that malformed profiles fail loudly with the file named.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from citetab.engine.profile_loader import (
    CourtProfile,
    ProfileLoaderError,
    load_profile,
    load_profile_by_id,
)


def test_frap_profile_loads_with_expected_fields(frap_profile_path: Path) -> None:
    """The FRAP profile loads and exposes its key formatting contract."""
    profile = load_profile(frap_profile_path)
    assert isinstance(profile, CourtProfile)
    assert profile.id == "frap"
    assert profile.name == "Federal Appellate (FRAP)"
    assert profile.version == "1.0.0"
    assert profile.effective_date == date(2026, 6, 5)
    assert profile.passim.threshold_pages == 5
    assert profile.passim.render_text == "passim"
    assert profile.empty_groups == "omit"
    assert profile.formatting.italicize_case_names is True
    assert profile.formatting.pincites_in_toa is False


def test_frap_groups_are_in_render_order(frap_profile_path: Path) -> None:
    """Groups load in their declared render order with the right type maps."""
    profile = load_profile(frap_profile_path)
    keys = [group.key for group in profile.groups]
    assert keys == [
        "cases",
        "constitutional",
        "statutes",
        "regulations",
        "rules",
        "other",
    ]
    cases_group = profile.groups[0]
    assert cases_group.label == "Cases"
    assert cases_group.types == ["case"]


def test_frap_heading_detection_variants(frap_profile_path: Path) -> None:
    """Heading config exposes the generated text and detection variants."""
    profile = load_profile(frap_profile_path)
    assert profile.heading.generated_text == "TABLE OF AUTHORITIES"
    assert "Table of Authorities" in profile.heading.detection_variants
    assert "Table of Cited Authorities" in profile.heading.detection_variants


def test_load_profile_by_id_resolves_bundled_frap() -> None:
    """``load_profile_by_id`` finds the FRAP profile via the resolved data dir."""
    profile = load_profile_by_id("frap")
    assert profile.id == "frap"


def test_load_profile_by_id_missing_raises(tmp_path: Path) -> None:
    """An unknown profile id fails loudly, naming the searched path."""
    with pytest.raises(ProfileLoaderError, match="no court profile 'nope'"):
        load_profile_by_id("nope", search_dir=tmp_path)


def test_load_profile_rejects_non_mapping(tmp_path: Path) -> None:
    """A YAML file that is not a mapping is rejected with the file named."""
    bad = tmp_path / "bad.yaml"
    bad.write_text("- just\n- a\n- list\n", encoding="utf-8")
    with pytest.raises(ProfileLoaderError, match="must be a YAML mapping"):
        load_profile(bad)


def test_load_profile_rejects_invalid_yaml(tmp_path: Path) -> None:
    """Unparseable YAML fails loudly."""
    bad = tmp_path / "bad.yaml"
    bad.write_text("id: frap\n  : broken\n::::\n", encoding="utf-8")
    with pytest.raises(ProfileLoaderError, match="not valid YAML"):
        load_profile(bad)


def test_load_profile_rejects_missing_file(tmp_path: Path) -> None:
    """A missing file raises ProfileLoaderError rather than OSError."""
    with pytest.raises(ProfileLoaderError, match="cannot read court profile"):
        load_profile(tmp_path / "absent.yaml")


def test_load_profile_rejects_unknown_field(
    tmp_path: Path, frap_profile_path: Path
) -> None:
    """An extra top-level key is rejected (extra='forbid')."""
    text = frap_profile_path.read_text(encoding="utf-8")
    polluted = tmp_path / "frap.yaml"
    polluted.write_text(text + "\nunexpected_key: 1\n", encoding="utf-8")
    with pytest.raises(ProfileLoaderError, match="failed validation"):
        load_profile(polluted)


def test_load_profile_by_id_mismatched_id_raises(
    tmp_path: Path, frap_profile_path: Path
) -> None:
    """A file whose declared id differs from its name is rejected."""
    text = frap_profile_path.read_text(encoding="utf-8")
    mis = tmp_path / "scotus.yaml"
    mis.write_text(text, encoding="utf-8")  # declares id: frap
    with pytest.raises(
        ProfileLoaderError, match="declares id 'frap', expected 'scotus'"
    ):
        load_profile_by_id("scotus", search_dir=tmp_path)
