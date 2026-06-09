"""Build the grouped, sorted TOA structure from a court profile (FR-06).

Everything about grouping, ordering, passim, and labels is read from the profile
— nothing is hardcoded. The builder produces an ordered view over the working
authorities; the page text for each entry is computed on demand from the
authority's current pages, so the same structure renders correctly on every
iteration of the convergence loop as pages change.
"""

from __future__ import annotations

from dataclasses import dataclass

from toatool.engine.profile_loader import CourtProfile
from toatool.pipeline.working import WorkingAuthority


@dataclass(frozen=True)
class ToaGroupView:
    """One rendered TOA group: its label and its authorities in sort order."""

    key: str
    label: str
    authorities: tuple[WorkingAuthority, ...]


@dataclass(frozen=True)
class ToaModel:
    """The ordered TOA structure: non-empty groups in profile render order."""

    groups: tuple[ToaGroupView, ...]


def is_passim(authority: WorkingAuthority, profile: CourtProfile) -> bool:
    """Whether an authority renders as passim (more than the profile threshold).

    Exactly ``threshold_pages`` distinct pages lists pages; the threshold is the
    boundary, not the trigger (spec §3.2, FR-06).
    """
    return len(authority.pages()) > profile.passim.threshold_pages


def page_text(authority: WorkingAuthority, profile: CourtProfile) -> str:
    """Render an authority's page column: ``passim`` or an ascending page list."""
    if is_passim(authority, profile):
        return profile.passim.render_text
    return ", ".join(str(page) for page in authority.pages())


def build_toa(authorities: list[WorkingAuthority], profile: CourtProfile) -> ToaModel:
    """Group and sort authorities into a TOA structure per the profile.

    Args:
        authorities: The resolved working authorities (pages may be unset).
        profile: The active court profile.

    Returns:
        A :class:`ToaModel` whose groups are in profile render order, each with
        its authorities sorted by ``sort_key``. Empty groups are omitted when the
        profile's ``empty_groups`` policy is ``omit``.
    """
    by_group: dict[str, list[WorkingAuthority]] = {
        group.key: [] for group in profile.groups
    }
    for authority in authorities:
        by_group[authority.group].append(authority)

    views: list[ToaGroupView] = []
    for group in profile.groups:
        members = by_group[group.key]
        if not members and profile.empty_groups == "omit":
            continue
        ordered = tuple(sorted(members, key=lambda a: a.sort_key))
        views.append(
            ToaGroupView(key=group.key, label=group.label, authorities=ordered)
        )
    return ToaModel(groups=tuple(views))
