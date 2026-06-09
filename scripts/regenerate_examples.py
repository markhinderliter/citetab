"""Regenerate the committed example reports from real runs (REPORT_SPEC §1).

Runs the full pipeline + rule pack on each base brief and writes its Markdown
report to ``examples/reports/{stem}.toa-report.md``. These are instances of the
report spec, not frozen oracles: they are reproduced by this script whenever the
pipeline, rules, or fixtures change.

The ``generated:`` timestamp is pinned to a canonical value so the committed
files are byte-stable across regenerations (the live CLI stamps the real time;
tests mask both the timestamp and the render version per REPORT_SPEC §6). The
render-engine version and input hashes are this environment's real values.

Usage::

    python scripts/regenerate_examples.py
"""

from __future__ import annotations

from pathlib import Path

from toatool.engine.profile_loader import load_profile_by_id
from toatool.engine.runner import run_rules
from toatool.pipeline import convergence
from toatool.report import render_report

REPO_ROOT = Path(__file__).resolve().parent.parent
BRIEFS = REPO_ROOT / "examples" / "briefs"
REPORTS = REPO_ROOT / "examples" / "reports"

# Canonical timestamp for the committed instances (today's date, fixed time).
PINNED_GENERATED_AT = "2026-06-09T12:00:00Z"

_FIXTURES = (
    "clean_appellate_brief.docx",
    "dirty_motion_brief.docx",
    "marker_trial_memo.docx",
)


def regenerate(name: str) -> Path:
    """Regenerate one example report; return the path written."""
    profile = load_profile_by_id("frap")
    input_path = BRIEFS / name
    gen = convergence.generate(input_path, profile)
    rules = run_rules(gen, input_path=input_path, profile=profile)

    if rules.docx_suppressed:
        output_clause = "SUPPRESSED — no placement found"
    else:
        output_clause = f"written {input_path.stem}.toa.docx"

    report = render_report(
        gen,
        rules,
        input_name=name,
        profile=profile,
        output_clause=output_clause,
        generated_at=PINNED_GENERATED_AT,
    )
    dest = REPORTS / f"{input_path.stem}.toa-report.md"
    dest.write_text(report, encoding="utf-8")
    return dest


def main() -> int:
    """Regenerate every example report and report what was written."""
    REPORTS.mkdir(parents=True, exist_ok=True)
    print("Regenerating example reports (LibreOffice render; ~20s)...")
    for name in _FIXTURES:
        dest = regenerate(name)
        print(f"  wrote {dest.relative_to(REPO_ROOT)}")
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
