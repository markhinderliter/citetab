"""The ``citetab`` command-line interface (FR-11).

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

from citetab import __version__
from citetab.core import Outcome, run_generation
from citetab.engine.profile_loader import ProfileLoaderError, load_profile_by_id
from citetab.engine.resources import profiles_dir, rules_dir
from citetab.engine.rule_loader import load_rule_cards

EXIT_OK = 0
EXIT_FINDINGS = 1
EXIT_INVOCATION = 2


def _fail(message: str) -> NoReturn:
    """Print an error and exit ``2`` (invocation/parse failure)."""
    click.echo(f"error: {message}", err=True)
    raise SystemExit(EXIT_INVOCATION)


@click.group()
@click.version_option(__version__, prog_name="citetab")
def main() -> None:
    """Citetab — regenerate a brief's Table of Authorities with measured pages."""


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
    result = run_generation(brief, court=court, toa_heading=toa_heading, output=output)

    if result.outcome is Outcome.FAILED:
        _fail(result.error or "could not process the input")

    # result.report_path is set on every non-FAILED outcome.
    assert result.report_path is not None
    if result.docx_path is None:
        click.echo("output: .docx SUPPRESSED (no placement found); report written")
    else:
        click.echo(f"output: {result.docx_path.name}")
    click.echo(f"report: {result.report_path.name}")
    click.echo(
        f"findings: {result.error_count} error · {result.warning_count} warning · "
        f"{result.info_count} info"
    )
    raise SystemExit(result.exit_code)


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
    prefix = f"{rule_id}-"
    matches = sorted(
        (
            entry
            for entry in (rules_dir() / "toa").iterdir()
            if entry.name.startswith(prefix) and entry.name.endswith(".md")
        ),
        key=lambda entry: entry.name,
    )
    if not matches:  # pragma: no cover - defensive
        _fail(f"rule card file for '{rule_id}' not found")
    click.echo(matches[0].read_text(encoding="utf-8"))


@main.group()
def profiles() -> None:
    """Inspect the available court profiles."""


@profiles.command("list")
def profiles_list() -> None:
    """List the available court profiles."""
    names = sorted(
        entry.name for entry in profiles_dir().iterdir() if entry.name.endswith(".yaml")
    )
    for name in names:
        try:
            profile = load_profile_by_id(name.removesuffix(".yaml"))
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
