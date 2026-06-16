"""Idempotency: running citetab on its own output changes nothing (FR-12, §3.3).

For every .docx-producing fixture, a second run on the first run's output must
converge in a single iteration and regenerate a byte-identical Table of
Authorities. The findings legitimately differ — the first run discloses the
corrections it made; the second has nothing left to correct, which is itself the
proof the corrections stuck — so the byte-identity assertion is scoped to the
generated table, the substantive "zero changes" promise.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from citetab.engine.profile_loader import CourtProfile, load_profile_by_id
from citetab.engine.runner import run_rules
from citetab.pipeline import convergence
from citetab.pipeline.convergence import GenerationResult
from citetab.report import render_report

BRIEFS = Path(__file__).resolve().parent.parent.parent / "examples" / "briefs"

pytestmark = pytest.mark.skipif(
    __import__("shutil").which("libreoffice") is None
    and __import__("shutil").which("soffice") is None,
    reason="LibreOffice is required to render; not installed",
)


@pytest.fixture(scope="module")
def frap() -> CourtProfile:
    """The FRAP court profile."""
    return load_profile_by_id("frap")


def _toa_signature(
    gen: GenerationResult,
) -> list[tuple[str, str, tuple[int, ...], bool]]:
    """Project the generated table to (id, display, pages, passim) for comparison."""
    return sorted(
        (a.authority_id, a.display_full, tuple(a.pages), a.passim)
        for a in gen.registry.authorities
    )


def _toa_section(report: str) -> str:
    """Return the ``## Table of Authorities`` section of a rendered report."""
    start = report.index("## Table of Authorities")
    end = report.index("## Findings")
    return report[start:end]


def _render(
    gen: GenerationResult, rules: object, path: Path, frap: CourtProfile
) -> str:
    return render_report(
        gen,
        rules,  # type: ignore[arg-type]
        input_name=path.name,
        profile=frap,
        output_clause="written x",
        generated_at="2026-06-09T12:00:00Z",
    )


@pytest.mark.parametrize(
    "fixture",
    [
        "clean_appellate_brief.docx",
        "dirty_motion_brief.docx",
        "marker_trial_memo.docx",
    ],
)
def test_second_run_is_idempotent(
    fixture: str, frap: CourtProfile, tmp_path: Path
) -> None:
    """Run-on-output converges in 1 iteration with a byte-identical TOA."""
    source = BRIEFS / fixture
    first = convergence.generate(source, frap)
    rules_first = run_rules(first, input_path=source, profile=frap)
    assert not rules_first.docx_suppressed

    output = tmp_path / f"{source.stem}.toa.docx"
    first.working_document.save(str(output))

    second = convergence.generate(output, frap)
    rules_second = run_rules(second, input_path=output, profile=frap)

    # The idempotency promise: immediate convergence, zero table changes.
    assert second.iteration_count == 1
    assert second.converged is True
    assert _toa_signature(first) == _toa_signature(second)
    assert _toa_section(_render(first, rules_first, source, frap)) == _toa_section(
        _render(second, rules_second, output, frap)
    )

    # The second run has no input-TOA diff findings — the corrections stuck.
    second_rule_ids = {f.rule_id for f in rules_second.findings}
    assert {"TT-002", "TT-003", "TT-004"} & second_rule_ids == set()
