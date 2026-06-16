"""Tests for TOA construction: grouping, sort, passim boundary (FR-06)."""

from __future__ import annotations

from citetab.engine.profile_loader import load_profile_by_id
from citetab.pipeline import toa_builder
from citetab.pipeline.working import WorkingAuthority, WorkingOccurrence


def _authority(
    authority_id: str,
    group: str,
    sort_key: str,
    pages: list[int],
    auth_type: str = "case",
) -> WorkingAuthority:
    occurrences = [
        WorkingOccurrence(
            form="full",
            raw_text=authority_id,
            paragraph_index=i,
            char_span=(0, 1),
            page=page,
        )
        for i, page in enumerate(pages)
    ]
    return WorkingAuthority(
        authority_id=authority_id,
        type=auth_type,  # type: ignore[arg-type]
        components={},
        display_full=authority_id,
        sort_key=sort_key,
        group=group,  # type: ignore[arg-type]
        occurrences=occurrences,
    )


def test_passim_boundary() -> None:
    """Exactly threshold pages lists pages; more than threshold is passim (FR-06)."""
    profile = load_profile_by_id("frap")
    at_threshold = _authority("a", "cases", "a", [1, 2, 3, 4, 5])
    over_threshold = _authority("b", "cases", "b", [1, 2, 3, 4, 5, 6])
    assert toa_builder.is_passim(at_threshold, profile) is False
    assert toa_builder.page_text(at_threshold, profile) == "1, 2, 3, 4, 5"
    assert toa_builder.is_passim(over_threshold, profile) is True
    assert toa_builder.page_text(over_threshold, profile) == "passim"


def test_pages_are_sorted_and_deduplicated() -> None:
    """An authority's pages render ascending and de-duplicated."""
    profile = load_profile_by_id("frap")
    authority = _authority("a", "cases", "a", [5, 2, 2, 3])
    assert toa_builder.page_text(authority, profile) == "2, 3, 5"


def test_grouping_order_and_empty_groups_omitted() -> None:
    """Groups appear in profile order, with empty groups omitted."""
    profile = load_profile_by_id("frap")
    authorities = [
        _authority("rule:x", "rules", "r", [3], "rule"),
        _authority("case:b", "cases", "b", [2]),
        _authority("case:a", "cases", "a", [1]),
        _authority("stat:s", "statutes", "s", [4], "statute"),
    ]
    toa = toa_builder.build_toa(authorities, profile)
    labels = [group.label for group in toa.groups]
    assert labels == ["Cases", "Statutes", "Rules"]  # constitutional/regs/other omitted


def test_within_group_sorted_by_sort_key() -> None:
    """Authorities within a group are ordered by sort key."""
    profile = load_profile_by_id("frap")
    authorities = [
        _authority("case:b", "cases", "delgado", [2]),
        _authority("case:a", "cases", "brunner", [1]),
        _authority("case:c", "cases", "carmody", [3]),
    ]
    toa = toa_builder.build_toa(authorities, profile)
    order = [a.sort_key for a in toa.groups[0].authorities]
    assert order == ["brunner", "carmody", "delgado"]
