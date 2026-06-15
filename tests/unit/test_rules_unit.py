"""Unit tests for rule branches the rendered fixtures do not reach.

These build synthetic :class:`RuleContext` objects directly — no LibreOffice — to
exercise: TT-002's medium-confidence path (input TOA had an unparseable entry),
TT-003's input-passim correction and its non-convergence cross-reference, TT-004's
unparsed-line branch, TT-006's extra-marker branch, the runner's count helpers,
finding ordering, and the rule-pack build skip. The end-to-end behavior lives in
the §20 oracle integration tests; this file covers the edges.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from citetab.engine.profile_loader import CourtProfile, load_profile_by_id
from citetab.engine.rule_loader import RuleCard, load_rule_cards
from citetab.engine.runner import RuleRunResult
from citetab.models.registry import (
    Authority,
    CitationRegistry,
    FontSubstitution,
    Occurrence,
    RunMetadata,
)
from citetab.pipeline.input_toa_diff import BaselineEntry, DiffBaseline
from citetab.pipeline.placement import HeadingMatch, PlacementResult
from citetab.rules import RULE_CLASSES, build_rules, sort_findings
from citetab.rules.base import RuleContext, make_finding, occurrence_ref
from citetab.rules.tt002 import TT002
from citetab.rules.tt003 import TT003
from citetab.rules.tt004 import TT004
from citetab.rules.tt006 import TT006


@pytest.fixture(scope="module")
def frap() -> CourtProfile:
    """The FRAP court profile."""
    return load_profile_by_id("frap")


@pytest.fixture(scope="module")
def cards() -> dict[str, RuleCard]:
    """The loaded rule cards."""
    return load_rule_cards()


def _occurrence(page: int, *, raw: str = "Carmody, 512 F.3d at 1045") -> Occurrence:
    return Occurrence(
        form="full",
        raw_text=raw,
        paragraph_index=12,
        char_span=(0, len(raw)),
        confidence="high",
        page=page,
        pincite=None,
    )


def _authority(
    *,
    authority_id: str = "case:f3d:512:1042",
    display: str = "Carmody v. Westfall Transit Auth., 512 F.3d 1042 (9th Cir. 2018)",
    pages: list[int] | None = None,
    passim: bool = False,
    group: str = "cases",
) -> Authority:
    page_list = pages if pages is not None else [2, 3]
    return Authority(
        authority_id=authority_id,
        type="case",
        components={},
        display_full=display,
        sort_key=display.casefold(),
        group=group,  # type: ignore[arg-type]
        occurrences=[_occurrence(page_list[0], raw=display)],
        pages=page_list,
        passim=passim,
        display_short="Carmody",
    )


def _registry(
    authorities: list[Authority], *, font_sub: bool = False
) -> CitationRegistry:
    meta = RunMetadata(
        engine_version="0.1.0",
        rule_pack_version="1.0.0",
        profile_id="frap",
        profile_version="1.0.0",
        render_engine="LibreOffice",
        render_engine_version="24.2",
        font_substitution_occurred=font_sub,
        iteration_count=1,
        converged=True,
        input_sha256="a" * 64,
        font_substitutions=(
            [FontSubstitution(original="Consolas", substitute="DejaVu Sans Mono")]
            if font_sub
            else []
        ),
    )
    return CitationRegistry(authorities=authorities, run_metadata=meta)


_HEADING = PlacementResult(
    mechanism="heading",
    heading_match=HeadingMatch(
        heading_index=6,
        matched_text="TABLE OF AUTHORITIES",
        region_start=7,
        region_end=15,
    ),
    heading_matched=True,
)


def _ctx(
    frap: CourtProfile,
    *,
    registry: CitationRegistry,
    baseline: DiffBaseline,
    placement: PlacementResult = _HEADING,
    converged: bool = True,
) -> RuleContext:
    return RuleContext(
        input_path=Path("synthetic.docx"),
        profile=frap,
        registry=registry,
        placement=placement,
        baseline=baseline,
        unresolved=(),
        converged=converged,
        iteration_count=1,
        iteration_cap=5,
        page_history=(),
        engine_version="0.1.0",
    )


def test_tt002_medium_confidence_when_input_had_unparsed_entry(
    frap: CourtProfile, cards: dict[str, RuleCard]
) -> None:
    """An unparseable input entry drops every TT-002 in the run to medium."""
    registry = _registry([_authority()])
    baseline = DiffBaseline(
        entries=(BaselineEntry(verbatim_text="??? garbled line", parsed=False),),
        available=True,
    )
    findings = TT002(cards["TT-002"]).evaluate(
        _ctx(frap, registry=registry, baseline=baseline)
    )
    assert len(findings) == 1
    assert findings[0].confidence == "medium"
    assert "medium confidence" in findings[0].message


def test_tt003_input_passim_and_non_convergence_note(
    frap: CourtProfile, cards: dict[str, RuleCard]
) -> None:
    """An input-passim entry that is now a page list is a correction; the note fires."""
    registry = _registry([_authority(pages=[2, 3], passim=False)])
    baseline = DiffBaseline(
        entries=(
            BaselineEntry(
                verbatim_text="Carmody v. Westfall Transit Auth. passim",
                is_passim=True,
                parsed=True,
                authority_id="case:f3d:512:1042",
            ),
        ),
        available=True,
    )
    findings = TT003(cards["TT-003"]).evaluate(
        _ctx(frap, registry=registry, baseline=baseline, converged=False)
    )
    assert len(findings) == 1
    corrections = findings[0].evidence.computed_values["corrections"]
    assert corrections[0]["input"] == "passim"
    assert corrections[0]["corrected"] == "2, 3"
    assert "did not stabilize" in findings[0].message


def test_tt004_unparsed_line_branch(
    frap: CourtProfile, cards: dict[str, RuleCard]
) -> None:
    """An unparsed input-TOA line emits a TT-004 warning with the verbatim line."""
    registry = _registry([_authority()])
    baseline = DiffBaseline(
        entries=(BaselineEntry(verbatim_text="-- stray line --", parsed=False),),
        available=True,
    )
    findings = TT004(cards["TT-004"]).evaluate(
        _ctx(frap, registry=registry, baseline=baseline)
    )
    assert len(findings) == 1
    assert findings[0].severity == "warning"
    assert "could not be interpreted" in findings[0].message
    assert findings[0].subject == "-- stray line --"


def test_tt006_extra_marker_branch(
    frap: CourtProfile, cards: dict[str, RuleCard]
) -> None:
    """A second [[TOA]] marker (no heading) yields one extra-marker warning."""
    placement = PlacementResult(
        mechanism="marker",
        marker_index=3,
        extra_marker_indices=(9,),
        marker_matched=True,
        heading_matched=False,
    )
    registry = _registry([_authority()])
    baseline = DiffBaseline(entries=(), available=False)
    rule = TT006(cards["TT-006"])
    ctx = _ctx(frap, registry=registry, baseline=baseline, placement=placement)
    assert rule.applies(ctx) is True
    findings = rule.evaluate(ctx)
    assert len(findings) == 1
    assert "additional [[TOA]] marker" in findings[0].message


def test_runner_result_counts(frap: CourtProfile, cards: dict[str, RuleCard]) -> None:
    """RuleRunResult exposes per-severity and per-rule counts."""
    registry = _registry([_authority()])
    ctx = _ctx(
        frap, registry=registry, baseline=DiffBaseline(entries=(), available=False)
    )
    error = make_finding(cards["TT-001"], ctx, message="e", subject="x")
    info = make_finding(cards["TT-002"], ctx, message="i", subject="y")
    result = RuleRunResult(findings=(error, info), docx_suppressed=False, exit_code=1)
    assert result.error_count == 1
    assert result.info_count == 1
    assert result.warning_count == 0
    assert result.by_rule() == {"TT-001": 1, "TT-002": 1}


def test_sort_findings_orders_by_severity_then_rule(
    frap: CourtProfile, cards: dict[str, RuleCard]
) -> None:
    """Findings sort error → warning → info, then by rule id."""
    registry = _registry([_authority()])
    ctx = _ctx(
        frap, registry=registry, baseline=DiffBaseline(entries=(), available=False)
    )
    info = make_finding(cards["TT-002"], ctx, message="i", subject="i")
    warning = make_finding(cards["TT-008"], ctx, message="w")
    error = make_finding(cards["TT-001"], ctx, message="e", subject="e")
    ordered = sort_findings([info, warning, error])
    assert [f.rule_id for f in ordered] == ["TT-001", "TT-008", "TT-002"]


def test_occurrence_ref_truncates_long_excerpt() -> None:
    """A very long occurrence excerpt is truncated with an ellipsis."""

    class _Occ:
        form = "full"
        raw_text = "X" * 500
        paragraph_index = 1
        char_span = (0, 500)
        page = 2

    ref = occurrence_ref(_Occ())  # type: ignore[arg-type]
    assert ref.excerpt.endswith("…")
    assert len(ref.excerpt) <= 160


def test_build_rules_skips_inactive_card(cards: dict[str, RuleCard]) -> None:
    """A non-active card is skipped by the rule-pack builder."""
    patched = dict(cards)
    patched["TT-001"] = cards["TT-001"].model_copy(update={"status": "deprecated"})
    built_ids = {rule.id for rule in build_rules(patched)}
    assert "TT-001" not in built_ids
    assert "TT-002" in built_ids
    assert set(RULE_CLASSES) - built_ids == {"TT-001"}
