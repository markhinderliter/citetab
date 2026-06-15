"""The shared generation core behind both the CLI and the GUI.

``run_generation`` is the single code path that turns an input brief into the
regenerated ``.docx`` (unless suppressed) and the Markdown findings report. It
mirrors the CLI's original control flow exactly — same pipeline calls, same
exception set, same suppression semantics — and returns a structured
:class:`GenerationOutcome` instead of printing or exiting.

The CLI renders its own terse stdout from the structured fields (preserving its
byte-for-byte output and 0/1/2 exit codes); the GUI shows the outcome's
``message``, a plain-language summary. Both honor the suppressed path: when no
``.docx`` is written, the outcome's ``docx_path`` is ``None`` and the message
never claims a brief was written.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from pathlib import Path

from citetab.engine.profile_loader import (
    CourtProfile,
    ProfileLoaderError,
    load_profile_by_id,
)
from citetab.engine.runner import RuleRunResult, run_rules
from citetab.pipeline import convergence
from citetab.pipeline.convergence import GenerationResult
from citetab.pipeline.extractor import EmptyDocumentError
from citetab.pipeline.parser import ParserError
from citetab.pipeline.renderer import RenderError
from citetab.report import render_report


class Outcome(enum.Enum):
    """The result class of a generation run; its value is the process exit code."""

    SUCCESS = 0
    """Clean run: outputs written, no error findings (exit 0)."""

    ISSUES = 1
    """Outputs produced, but an error fired and/or the docx was suppressed (exit 1)."""

    FAILED = 2
    """Unprocessable input or invocation error; nothing written (exit 2)."""


@dataclass(frozen=True)
class GenerationOutcome:
    """The structured result of :func:`run_generation`."""

    outcome: Outcome
    exit_code: int
    output_dir: Path | None
    docx_path: Path | None
    report_path: Path | None
    error_count: int
    warning_count: int
    info_count: int
    message: str
    error: str | None = None


def _report_path(docx_path: Path) -> Path:
    """Return the report path tracking the ``.docx`` stem (REPORT_SPEC §1)."""
    name = docx_path.name
    base = name[: -len(".toa.docx")] if name.endswith(".toa.docx") else docx_path.stem
    return docx_path.with_name(f"{base}.toa-report.md")


def _output_paths(input_path: Path, output: Path | None) -> tuple[Path, Path]:
    """Resolve the ``.docx`` and report output paths for a run."""
    docx_path = (
        output
        if output is not None
        else input_path.with_name(f"{input_path.stem}.toa.docx")
    )
    return docx_path, _report_path(docx_path)


def _write_outputs(
    gen: GenerationResult,
    rules: RuleRunResult,
    *,
    input_path: Path,
    profile: CourtProfile,
    docx_path: Path,
    report_path: Path,
) -> None:
    """Write the ``.docx`` (unless suppressed) and the Markdown report."""
    if rules.docx_suppressed:
        output_clause = "SUPPRESSED — no placement found"
    else:
        gen.working_document.save(str(docx_path))
        output_clause = f"written {docx_path.name}"

    report = render_report(
        gen,
        rules,
        input_name=input_path.name,
        profile=profile,
        output_clause=output_clause,
    )
    report_path.write_text(report, encoding="utf-8")


def _failure(message: str) -> GenerationOutcome:
    """Build a FAILED outcome (exit 2) that claims no files."""
    return GenerationOutcome(
        outcome=Outcome.FAILED,
        exit_code=Outcome.FAILED.value,
        output_dir=None,
        docx_path=None,
        report_path=None,
        error_count=0,
        warning_count=0,
        info_count=0,
        message=f"Couldn't process that file:\n\n{message}",
        error=message,
    )


def _success_message(
    *,
    outcome: Outcome,
    output_dir: Path,
    docx_path: Path | None,
    report_path: Path,
    rules: RuleRunResult,
) -> str:
    """Build the GUI-facing message, naming the folder and only files written."""
    counts = (
        f"Findings: {rules.error_count} error · "
        f"{rules.warning_count} warning · {rules.info_count} info"
    )
    lines: list[str]
    if outcome is Outcome.SUCCESS:
        lines = ["Done. Your new files are in:", "", str(output_dir), ""]
    elif docx_path is None:
        lines = [
            "Finished — but issues need review.",
            "",
            "No regenerated brief was written (no place to insert the table "
            "was found).",
            "",
            "Your findings report is in:",
            "",
            str(output_dir),
            "",
        ]
    else:
        lines = [
            "Finished — but issues need review.",
            "",
            "Your new files are in:",
            "",
            str(output_dir),
            "",
        ]
    if docx_path is not None:
        lines.append(f"• regenerated brief: {docx_path.name}")
    lines.append(f"• findings report: {report_path.name}")
    lines += ["", counts]
    return "\n".join(lines)


def run_generation(
    input_path: Path,
    *,
    court: str = "frap",
    toa_heading: str | None = None,
    output: Path | None = None,
) -> GenerationOutcome:
    """Generate a brief's Table of Authorities and findings report.

    Args:
        input_path: The input ``.docx`` brief.
        court: Court profile id (default ``frap``).
        toa_heading: Explicit TOA heading to target, if any.
        output: Path for the regenerated ``.docx`` (report tracks its stem).

    Returns:
        A :class:`GenerationOutcome`. ``FAILED`` (exit 2) on an unprocessable
        input or unknown profile, with nothing written; otherwise ``SUCCESS``
        (exit 0) or ``ISSUES`` (exit 1) with the report written and the ``.docx``
        written unless suppressed.
    """
    try:
        profile = load_profile_by_id(court)
    except ProfileLoaderError as exc:
        return _failure(str(exc))

    try:
        gen = convergence.generate(input_path, profile, toa_heading=toa_heading)
    except (ParserError, RenderError, EmptyDocumentError) as exc:
        return _failure(str(exc))

    rules = run_rules(gen, input_path=input_path, profile=profile)
    docx_path, report_path = _output_paths(input_path, output)
    _write_outputs(
        gen,
        rules,
        input_path=input_path,
        profile=profile,
        docx_path=docx_path,
        report_path=report_path,
    )

    written_docx = None if rules.docx_suppressed else docx_path
    output_dir = docx_path.parent.resolve()
    outcome = Outcome.SUCCESS if rules.exit_code == 0 else Outcome.ISSUES
    message = _success_message(
        outcome=outcome,
        output_dir=output_dir,
        docx_path=written_docx,
        report_path=report_path,
        rules=rules,
    )
    return GenerationOutcome(
        outcome=outcome,
        exit_code=rules.exit_code,
        output_dir=output_dir,
        docx_path=written_docx,
        report_path=report_path,
        error_count=rules.error_count,
        warning_count=rules.warning_count,
        info_count=rules.info_count,
        message=message,
    )
