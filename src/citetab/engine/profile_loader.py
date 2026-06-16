"""Load and validate court profiles into typed objects.

A court profile (e.g. ``profiles/frap.yaml``) is *data, not code*: it defines
the TOA heading text and detection variants, the grouping buckets and their
render order, the within-group sort, the passim threshold, and the formatting
flags. The pipeline reads these; nothing about grouping, ordering, passim, or
headings is hardcoded (PRD §15, FR-06).

This module validates a profile YAML against :class:`CourtProfile` and fails
loudly — naming the file — when the data does not match the contract.
"""

from __future__ import annotations

from datetime import date
from importlib.resources.abc import Traversable
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from citetab.engine.resources import profiles_dir
from citetab.models.registry import AuthorityType

_SEMVER = r"^[0-9]+\.[0-9]+\.[0-9]+$"
_PROFILE_ID = r"^[a-z0-9_]+$"


class ProfileLoaderError(Exception):
    """Raised when a court profile cannot be read or fails validation."""


class HeadingConfig(BaseModel):
    """Heading text the tool writes and the variants it detects (spec §2.4)."""

    model_config = ConfigDict(extra="forbid")

    generated_text: str
    """Heading written above a generated TOA (also used on the marker bootstrap)."""

    detection_variants: list[str] = Field(min_length=1)
    """Headings matched case-insensitively and whitespace-tolerantly for placement."""


class GroupConfig(BaseModel):
    """One TOA grouping bucket: a key, a display label, and the types it holds."""

    model_config = ConfigDict(extra="forbid")

    key: str
    """Stable group key, matching :data:`citetab.models.registry.GroupKey`."""

    label: str
    """Human-readable group heading rendered in the TOA (e.g. ``Cases``)."""

    types: list[AuthorityType] = Field(min_length=1)
    """Authority types that fall into this group."""


class SortConfig(BaseModel):
    """Within-group ordering policy."""

    model_config = ConfigDict(extra="forbid")

    within_group: Literal["sort_key"]
    """Field to sort by within each group. v1 supports ``sort_key`` only."""


class PassimConfig(BaseModel):
    """Passim threshold and the text rendered when it is exceeded."""

    model_config = ConfigDict(extra="forbid")

    threshold_pages: int = Field(ge=1)
    """An authority on MORE than this many distinct pages renders as passim."""

    render_text: str
    """Text rendered in place of a page list (e.g. ``passim``)."""


class FormattingConfig(BaseModel):
    """Profile formatting flags for TOA rendering."""

    model_config = ConfigDict(extra="forbid")

    dot_leader: bool
    """Whether to render dot leaders between the entry and its page list."""

    page_numbers_right_aligned: bool
    """Whether page numbers are right-aligned."""

    italicize_case_names: bool
    """Whether case names are italicized."""

    pincites_in_toa: bool
    """Whether pincites appear in the TOA (false: the TOA lists brief pages)."""


class CourtProfile(BaseModel):
    """A validated court profile: the complete TOA-format contract as data."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=_PROFILE_ID)
    """Profile identifier (e.g. ``frap``); selected by ``--court``."""

    version: str = Field(pattern=_SEMVER)
    """Semantic version of this profile (the court-profile SemVer track)."""

    effective_date: date
    """The date this profile version took effect."""

    description: str
    """Human-readable description of the profile and its provenance."""

    heading: HeadingConfig
    """Heading text and detection variants."""

    groups: list[GroupConfig] = Field(min_length=1)
    """Grouping buckets, in render order. Empty groups are omitted from output."""

    sort: SortConfig
    """Within-group ordering policy."""

    passim: PassimConfig
    """Passim threshold and render text."""

    formatting: FormattingConfig
    """Formatting flags."""

    empty_groups: Literal["omit"]
    """Empty-group policy. v1 supports ``omit`` only."""

    def group_for_type(self, authority_type: AuthorityType) -> str:
        """Return the group key an authority type belongs to.

        Args:
            authority_type: The authority's type (e.g. ``case``, ``statute``).

        Returns:
            The matching group's ``key`` (e.g. ``cases``).

        Raises:
            ProfileLoaderError: If no group in the profile claims the type.
        """
        for group in self.groups:
            if authority_type in group.types:
                return group.key
        raise ProfileLoaderError(
            f"court profile '{self.id}' has no group for authority type "
            f"'{authority_type}'"
        )


def load_profile(path: Traversable) -> CourtProfile:
    """Load and validate a single court profile YAML file.

    Args:
        path: The profile ``.yaml`` file (a Traversable or ``pathlib.Path``).

    Returns:
        The validated :class:`CourtProfile`.

    Raises:
        ProfileLoaderError: If the file is missing, is not valid YAML, is not a
            mapping, or fails schema validation. The message names the file.
    """
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ProfileLoaderError(f"cannot read court profile '{path}': {exc}") from exc

    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise ProfileLoaderError(
            f"court profile '{path}' is not valid YAML: {exc}"
        ) from exc

    if not isinstance(data, dict):
        raise ProfileLoaderError(
            f"court profile '{path}' must be a YAML mapping, got {type(data).__name__}"
        )

    try:
        return CourtProfile.model_validate(data)
    except ValidationError as exc:
        raise ProfileLoaderError(
            f"court profile '{path}' failed validation:\n{exc}"
        ) from exc


def load_profile_by_id(
    profile_id: str, search_dir: Traversable | None = None
) -> CourtProfile:
    """Load a court profile by id from the profiles directory.

    Args:
        profile_id: The profile id (e.g. ``frap``), matching its ``<id>.yaml`` file.
        search_dir: Directory to search; defaults to the resolved profiles dir.

    Returns:
        The validated :class:`CourtProfile`.

    Raises:
        ProfileLoaderError: If no file exists for the id, or it fails to load,
            or its declared ``id`` does not match ``profile_id``.
    """
    directory = search_dir if search_dir is not None else profiles_dir()
    path = directory / f"{profile_id}.yaml"
    if not path.is_file():
        raise ProfileLoaderError(f"no court profile '{profile_id}' found at '{path}'")
    profile = load_profile(path)
    if profile.id != profile_id:
        raise ProfileLoaderError(
            f"court profile file '{path}' declares id '{profile.id}', "
            f"expected '{profile_id}'"
        )
    return profile
