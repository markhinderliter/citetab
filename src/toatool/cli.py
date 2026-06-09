"""The ``toatool`` command-line interface (FR-11).

One brief per ``generate`` invocation; plus read-only ``rules`` and ``profiles``
inspection commands. Exit codes (PRD §20 / FR-11):

- ``0`` — success; info/warning findings are allowed.
- ``1`` — an error finding was emitted, or the ``.docx`` was suppressed
  (TT-005, TT-007 paths). The report is still written.
- ``2`` — invocation or parse failure: a missing/unreadable/non-``.docx`` input,
  an unknown court profile, an unknown rule id, or the renderer being
  unavailable. Nothing is written.

The iteration cap is fixed by spec at 5 and is deliberately not a flag.
"""

from __future__ import annotations

from pathlib import Path
from typing import NoReturn

import click

from toatool import __version__
from toatool.engine.profile_loader import (
    CourtProfile,
    ProfileLoaderError,
    load_profile_by_id,
)
from toatool.engine.resources import profiles_dir, rules_dir
from toatool.engine.rule_loader import load_rule_cards
from toatool.engine.runner import RuleRunResult, run_rules
from toatool.pipeline import convergence
from toatool.pipeline.convergence import GenerationResult
from toatool.pipeline.parser import ParserError
from toatool.pipeline.renderer import RenderError
from toatool.report import render_report

EXIT_OK = 0
EXIT_FINDINGS = 1
EXIT_INVOCATION = 2


def _fail(message: str) -> NoReturn:
    """Print an error and exit ``2`` (invocation/parse failure)."""
    click.echo(f"error: {message}", err=True)
    raise SystemExit(EXIT_INVOCATION)


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


@click.group()
@click.version_option(__version__, prog_name="toatool")
def main() -> None:
    """Toatool — regenerate a brief's Table of Authorities with measured pages."""


@main.command()
@click.argument("brief", type=click.Path(path_type=Path))
@click.option("--court", default="frap", show_default=True, help="Court profile id.")
@click.option("--toa-heading", default=None, help="Explicit TOA heading to target.")
@click.option(
    "--output",
    default=None,
    type=click.Path(path_type=Path),
    help="Path for the regenerated .docx (report tracks its stem).",
)
def generate(
    brief: Path,
    court: str,
    toa_heading: str | None,
    output: Path | None,
) -> None:
    """Regenerate BRIEF's Table of Authorities and write a findings report."""
    try:
        profile = load_profile_by_id(court)
    except ProfileLoaderError as exc:
        _fail(str(exc))

    try:
        gen = convergence.generate(brief, profile, toa_heading=toa_heading)
    except (ParserError, RenderError) as exc:
        _fail(str(exc))

    rules = run_rules(gen, input_path=brief, profile=profile)
    docx_path, report_path = _output_paths(brief, output)
    _write_outputs(
        gen,
        rules,
        input_path=brief,
        profile=profile,
        docx_path=docx_path,
        report_path=report_path,
    )

    if rules.docx_suppressed:
        click.echo("output: .docx SUPPRESSED (no placement found); report written")
    else:
        click.echo(f"output: {docx_path.name}")
    click.echo(f"report: {report_path.name}")
    click.echo(
        f"findings: {rules.error_count} error · {rules.warning_count} warning · "
        f"{rules.info_count} info"
    )
    raise SystemExit(rules.exit_code)


@main.group()
def rules() -> None:
    """Inspect the active rule pack."""


@rules.command("list")
def rules_list() -> None:
    """List the rules in the active pack."""
    cards = load_rule_cards()
    for rule_id in sorted(cards):
        card = cards[rule_id]
        click.echo(f"{card.id}  {card.severity_default:<7}  {card.name}")


@rules.command("show")
@click.argument("rule_id")
def rules_show(rule_id: str) -> None:
    """Render a rule card's full content."""
    cards = load_rule_cards()
    if rule_id not in cards:
        _fail(f"no rule '{rule_id}' in the active pack")
    matches = sorted((rules_dir() / "toa").glob(f"{rule_id}-*.md"))
    if not matches:  # pragma: no cover - defensive
        _fail(f"rule card file for '{rule_id}' not found")
    click.echo(matches[0].read_text(encoding="utf-8"))


@main.group()
def profiles() -> None:
    """Inspect the available court profiles."""


@profiles.command("list")
def profiles_list() -> None:
    """List the available court profiles."""
    for path in sorted(profiles_dir().glob("*.yaml")):
        try:
            profile = load_profile_by_id(path.stem)
        except ProfileLoaderError:  # pragma: no cover - defensive
            continue
        click.echo(f"{profile.id}  {profile.version}  {profile.description.strip()}")


@profiles.command("show")
@click.argument("profile_id")
def profiles_show(profile_id: str) -> None:
    """Render a court profile's YAML source."""
    path = profiles_dir() / f"{profile_id}.yaml"
    if not path.is_file():
        _fail(f"no court profile '{profile_id}'")
    click.echo(path.read_text(encoding="utf-8"))


if __name__ == "__main__":  # pragma: no cover
    main()
