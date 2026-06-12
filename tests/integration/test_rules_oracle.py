"""The PRD §20 test oracle: expected findings and exit code per fixture.

Each fixture is run through the full generation pipeline and the rule pack, and
the emitted findings are asserted exactly. Per §20, CI renders under LibreOffice
font substitution, so TT-008 (warning, high) is expected on every fixture iff the
run metadata reports a substitution; these assertions verify TT-008 against that
flag, then assert the remaining findings precisely.

One reconciliation is surfaced here, not silently resolved (AI_GUARDRAILS §"spec
conflicts"): the §20 table's "dirty + marker → dirty's findings + TT-006" row is
read against the TT-006 rule card, which states that when the marker wins the
heading region is NOT used as the diff baseline, so TT-002/003/004 skip. The card
governs; the dirty+marker oracle is therefore TT-001 + TT-006 (+ TT-008), with
the diff rules skipped. See ``test_oracle_dirty_plus_marker``.
"""

from __future__ import annotations

import shutil
from collections import Counter
from pathlib import Path

import pytest

from toatool.engine.profile_loader import CourtProfile, load_profile_by_id
from toatool.engine.runner import RuleRunResult, run_rules
from toatool.models.finding import Finding
from toatool.pipeline import convergence
from toatool.pipeline.convergence import GenerationResult

BRIEFS = Path(__file__).resolve().parent.parent.parent / "examples" / "briefs"

pytestmark = pytest.mark.skipif(
    shutil.which("libreoffice") is None and shutil.which("soffice") is None,
    reason="LibreOffice is required to render; not installed",
)


@pytest.fixture(scope="module")
def frap() -> CourtProfile:
    """The FRAP court profile."""
    return load_profile_by_id("frap")


def _run(path: Path, profile: CourtProfile) -> tuple[GenerationResult, RuleRunResult]:
    """Generate and evaluate the rule pack for one brief."""
    result = convergence.generate(path, profile)
    rules = run_rules(result, input_path=path, profile=profile)
    return result, rules


def _besides_tt008(rules: RuleRunResult) -> Counter[str]:
    """Count findings per rule id, excluding the environment-dependent TT-008."""
    return Counter(f.rule_id for f in rules.findings if f.rule_id != "TT-008")


def _assert_tt008_matches_environment(
    gen: GenerationResult, rules: RuleRunResult
) -> None:
    """TT-008 is present exactly when the render reported a font substitution."""
    tt008 = [f for f in rules.findings if f.rule_id == "TT-008"]
    if gen.registry.run_metadata.font_substitution_occurred:
        assert len(tt008) == 1
        assert tt008[0].severity == "warning"
        assert tt008[0].confidence == "high"
    else:
        assert tt008 == []


def _finding(rules: RuleRunResult, rule_id: str) -> Finding:
    """Return the single finding for ``rule_id`` (asserting there is exactly one)."""
    matches = [f for f in rules.findings if f.rule_id == rule_id]
    assert len(matches) == 1, f"expected exactly one {rule_id}, got {len(matches)}"
    return matches[0]


# --------------------------------------------------------------------------- #
# Base fixtures
# --------------------------------------------------------------------------- #


def test_oracle_clean(frap: CourtProfile) -> None:
    """clean → no findings besides TT-008; exit 0; .docx written."""
    gen, rules = _run(BRIEFS / "clean_appellate_brief.docx", frap)
    _assert_tt008_matches_environment(gen, rules)
    assert _besides_tt008(rules) == Counter()
    assert rules.docx_suppressed is False
    assert rules.exit_code == 0


def test_oracle_dirty(frap: CourtProfile) -> None:
    """dirty → TT-001 ×1, TT-002 ×1, TT-003 ×1 (besides TT-008); exit 1 (error)."""
    gen, rules = _run(BRIEFS / "dirty_motion_brief.docx", frap)
    _assert_tt008_matches_environment(gen, rules)
    assert _besides_tt008(rules) == Counter({"TT-001": 1, "TT-002": 1, "TT-003": 1})

    tt001 = _finding(rules, "TT-001")
    assert tt001.severity == "error" and tt001.confidence == "high"
    # Ellison's two short forms cluster into one finding listing both occurrences.
    assert len(tt001.evidence.occurrence_references) == 2

    tt002 = _finding(rules, "TT-002")
    assert tt002.severity == "info" and tt002.confidence == "high"
    assert tt002.authority_id == "case:f3d:891:655"  # Okafor

    tt003 = _finding(rules, "TT-003")
    assert tt003.severity == "info" and tt003.confidence == "high"
    corrections = tt003.evidence.computed_values["corrections"]
    corrected = {c["authority_id"]: c["corrected"] for c in corrections}
    assert corrected["case:f3d:512:1042"] == "passim"  # Carmody D2+D4
    assert "case:us:487:213" in corrected  # Delgado D2
    assert "regulation:cfr:12:1006.14" in corrected
    assert "statute:usc:15:1692e" not in corrected  # unchanged (1 == 1)

    assert rules.docx_suppressed is False
    assert rules.exit_code == 1


def test_oracle_marker_memo(frap: CourtProfile) -> None:
    """marker memo → no findings besides TT-008 (diff rules skip); exit 0.

    Skipped is not passed: the diff rules emit nothing because there is no input
    TOA to compare, not because the table was clean.
    """
    gen, rules = _run(BRIEFS / "marker_trial_memo.docx", frap)
    _assert_tt008_matches_environment(gen, rules)
    assert _besides_tt008(rules) == Counter()
    assert gen.placement.mechanism == "marker"
    assert rules.exit_code == 0


# --------------------------------------------------------------------------- #
# Derived fixtures
# --------------------------------------------------------------------------- #


def test_oracle_dirty_plus_phantom(
    frap: CourtProfile, dirty_plus_phantom: Path
) -> None:
    """dirty + phantom → dirty's findings + TT-004 ×1 (warning, medium)."""
    gen, rules = _run(dirty_plus_phantom, frap)
    _assert_tt008_matches_environment(gen, rules)
    assert _besides_tt008(rules) == Counter(
        {"TT-001": 1, "TT-002": 1, "TT-003": 1, "TT-004": 1}
    )

    tt004 = _finding(rules, "TT-004")
    assert tt004.severity == "warning" and tt004.confidence == "medium"
    assert "Nonexistent v. Authority" in (tt004.subject or "")
    # The phantom is absent from the regenerated registry/table.
    assert not any("999" in a.authority_id for a in gen.registry.authorities)
    assert rules.exit_code == 1


def test_oracle_memo_no_marker(frap: CourtProfile, memo_no_marker: Path) -> None:
    """memo − marker → TT-005 ×1 (error, high); .docx suppressed; exit 1."""
    gen, rules = _run(memo_no_marker, frap)
    _assert_tt008_matches_environment(gen, rules)
    assert _besides_tt008(rules) == Counter({"TT-005": 1})

    tt005 = _finding(rules, "TT-005")
    assert tt005.severity == "error" and tt005.confidence == "high"
    assert tt005.blocks_docx_output is True
    assert gen.placement.mechanism == "none"
    # The .docx is suppressed but the run still produced the full TOA for the
    # report (the registry has the measured authorities).
    assert rules.docx_suppressed is True
    assert len(gen.registry.authorities) > 0
    assert rules.exit_code == 1


def test_oracle_brief_no_toa(frap: CourtProfile, brief_no_toa: Path) -> None:
    """clean − TOA (no marker) → TT-005 ×1 (error, high); .docx suppressed; exit 1.

    Regression (QA Round 2): a no-placement input whose body has an occurrence
    that becomes unmeasurable in the TOA-less render must still degrade to a
    clean TT-005, not raise ConvergenceError. The marker-memo fixture above does
    not exercise this because its citations have no boundary-prone pinpoint.
    """
    gen, rules = _run(brief_no_toa, frap)
    _assert_tt008_matches_environment(gen, rules)
    assert _besides_tt008(rules) == Counter({"TT-005": 1})

    tt005 = _finding(rules, "TT-005")
    assert tt005.severity == "error" and tt005.confidence == "high"
    assert tt005.blocks_docx_output is True
    assert gen.placement.mechanism == "none"
    assert rules.docx_suppressed is True
    assert rules.exit_code == 1


def test_oracle_brief_unmeasured_occurrence(
    frap: CourtProfile, brief_unmeasured_occurrence: Path
) -> None:
    """clean + a pincite split across a page boundary → graceful TT-009 disclosure.

    Round 3 / C2-a: on the emitting path an occurrence that cannot be measured
    must degrade honestly — the `.docx` is still written, the unmeasured pincite
    is disclosed (TT-009, warning) and rendered ``p.?``, and the rest of the
    authority's measured pages survive. Nothing is silently dropped, and nothing
    crashes.
    """
    gen, rules = _run(brief_unmeasured_occurrence, frap)
    _assert_tt008_matches_environment(gen, rules)

    # (1) Graceful: the disclosure fires, no error-severity finding, .docx written.
    tt009 = _finding(rules, "TT-009")
    assert tt009.severity == "warning" and tt009.confidence == "high"
    assert rules.error_count == 0
    assert rules.docx_suppressed is False
    assert rules.exit_code == 0

    # (2) The straddling pincite is retained as unmeasured (renders p.?), not dropped;
    # the rest of the authority's measured pages survive intact.
    carmody = next(a for a in gen.registry.authorities if "Carmody" in a.display_full)
    unmeasured = [o for o in carmody.occurrences if o.page is None]
    measured = [o.page for o in carmody.occurrences if o.page is not None]
    assert len(unmeasured) == 1 and "1047" in unmeasured[0].raw_text
    assert measured, "the authority must retain its measured occurrences"
    assert carmody.pages == sorted(set(measured)), "no measured page silently dropped"

    # (3) The TT-009 finding names the unmeasured occurrence and renders it p.?.
    refs = tt009.evidence.occurrence_references
    assert any(r.page is None and "1047" in r.excerpt for r in refs)


def test_oracle_dirty_plus_marker(frap: CourtProfile, dirty_plus_marker: Path) -> None:
    """dirty + marker → marker wins: TT-006 ×1; diff rules (TT-002/003/004) skip.

    Card-governed reconciliation of the §20 wording (see module docstring): when
    the marker wins, the heading region is left untouched and is not used as the
    diff baseline, so only TT-001 (orphan, placement-independent) and TT-006 fire
    besides TT-008.
    """
    gen, rules = _run(dirty_plus_marker, frap)
    _assert_tt008_matches_environment(gen, rules)

    assert gen.placement.mechanism == "marker"
    assert gen.placement.marker_matched is True
    assert gen.placement.heading_matched is True

    besides = _besides_tt008(rules)
    assert besides == Counter({"TT-001": 1, "TT-006": 1})
    # Diff rules skipped — not passed.
    assert besides["TT-002"] == 0
    assert besides["TT-003"] == 0
    assert besides["TT-004"] == 0

    tt006 = _finding(rules, "TT-006")
    assert tt006.severity == "warning" and tt006.confidence == "high"
    assert rules.exit_code == 1  # TT-001 is an error
