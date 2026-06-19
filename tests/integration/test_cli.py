"""CLI behavior and exit codes (FR-11, PRD §20).

Exit-code coverage is the focus: 0 on a clean run, 1 when an error finding fires
or the .docx is suppressed, and 2 on an invocation/parse failure. The exit-2
cases (malformed input, unknown profile/rule) fail before any render, so they run
without LibreOffice; the success paths are gated on it.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import docx
import pytest
from click.testing import CliRunner

from citetab.cli import main
from citetab.engine.profile_loader import load_profile_by_id

BRIEFS = Path(__file__).resolve().parent.parent.parent / "examples" / "briefs"

_NEEDS_RENDER = pytest.mark.skipif(
    shutil.which("libreoffice") is None and shutil.which("soffice") is None,
    reason="LibreOffice is required to render; not installed",
)


@pytest.fixture()
def runner() -> CliRunner:
    """A Click CLI runner."""
    return CliRunner()


def _copy(name: str, dest_dir: Path) -> Path:
    """Copy a base brief into ``dest_dir`` and return the destination path."""
    dest = dest_dir / name
    shutil.copy(BRIEFS / name, dest)
    return dest


# --------------------------------------------------------------------------- #
# Exit code 2 — invocation / parse failure (no render needed)
# --------------------------------------------------------------------------- #


def test_generate_malformed_input_exits_2(runner: CliRunner, tmp_path: Path) -> None:
    """A non-.docx (unreadable) input fails to parse and exits 2."""
    bad = tmp_path / "not_really.docx"
    bad.write_text("this is plain text, not a docx archive", encoding="utf-8")
    result = runner.invoke(main, ["generate", str(bad)])
    assert result.exit_code == 2
    assert "error:" in result.output


def test_generate_textless_docx_rejected_with_ocr_hint(
    runner: CliRunner, tmp_path: Path
) -> None:
    """A valid .docx with no readable text is rejected (exit 2) with OCR guidance.

    Round 3 / C1-i: an empty or image-only document must not crash the resolver
    (eyecite rejects empty text), and must surface honest advice — OCR — not
    TT-005's "add a heading/marker", which is the wrong fix for a textless input.
    Fails before any render, so no LibreOffice is needed.
    """
    textless = tmp_path / "scanned.docx"
    docx.Document().save(str(textless))
    result = runner.invoke(main, ["generate", str(textless)])
    assert result.exit_code == 2, result.output
    lower = result.output.lower()
    assert "no readable text" in lower
    assert "ocr" in lower
    # Not TT-005's placement advice, which would be wrong for a textless file.
    assert "heading" not in lower and "marker" not in lower


def test_generate_missing_input_exits_2(runner: CliRunner, tmp_path: Path) -> None:
    """A path that does not exist exits 2."""
    result = runner.invoke(main, ["generate", str(tmp_path / "absent.docx")])
    assert result.exit_code == 2


def test_generate_unknown_profile_exits_2(runner: CliRunner, tmp_path: Path) -> None:
    """An unknown court profile exits 2 before any rendering."""
    brief = _copy("clean_appellate_brief.docx", tmp_path)
    result = runner.invoke(main, ["generate", str(brief), "--court", "nonesuch"])
    assert result.exit_code == 2


def test_rules_show_unknown_exits_2(runner: CliRunner) -> None:
    """An unknown rule id exits 2."""
    result = runner.invoke(main, ["rules", "show", "TT-999"])
    assert result.exit_code == 2


def test_profiles_show_unknown_exits_2(runner: CliRunner) -> None:
    """An unknown profile id exits 2."""
    result = runner.invoke(main, ["profiles", "show", "nonesuch"])
    assert result.exit_code == 2


# --------------------------------------------------------------------------- #
# Inspection commands (no render)
# --------------------------------------------------------------------------- #


def test_rules_list(runner: CliRunner) -> None:
    """`rules list` names all nine rules."""
    result = runner.invoke(main, ["rules", "list"])
    assert result.exit_code == 0
    for rule_id in (f"TT-00{n}" for n in range(1, 10)):
        assert rule_id in result.output


def test_rules_show(runner: CliRunner) -> None:
    """`rules show` renders the card content."""
    result = runner.invoke(main, ["rules", "show", "TT-001"])
    assert result.exit_code == 0
    assert "Unresolvable short-form citation" in result.output


def test_profiles_list(runner: CliRunner) -> None:
    """`profiles list` includes frap."""
    result = runner.invoke(main, ["profiles", "list"])
    assert result.exit_code == 0
    assert "frap" in result.output


def test_profiles_show(runner: CliRunner) -> None:
    """`profiles show frap` renders the YAML."""
    result = runner.invoke(main, ["profiles", "show", "frap"])
    assert result.exit_code == 0
    assert "passim" in result.output


# --------------------------------------------------------------------------- #
# Exit codes 0 / 1 — full runs (render required)
# --------------------------------------------------------------------------- #


@_NEEDS_RENDER
def test_generate_clean_exits_0(runner: CliRunner, tmp_path: Path) -> None:
    """The finding-free clean brief exits 0 and writes both outputs."""
    brief = _copy("clean_appellate_brief.docx", tmp_path)
    result = runner.invoke(main, ["generate", str(brief)])
    assert result.exit_code == 0
    assert (tmp_path / "clean_appellate_brief.toa.docx").is_file()
    assert (tmp_path / "clean_appellate_brief.toa-report.md").is_file()
    # The applied court profile is disclosed on stdout (not just the report file),
    # now as the human-readable name sourced from the live profile.
    name = load_profile_by_id("frap").name
    assert f"profile: {name}" in result.output


@_NEEDS_RENDER
def test_generate_dirty_exits_1(runner: CliRunner, tmp_path: Path) -> None:
    """The dirty brief's TT-001 error makes it exit 1; outputs still written."""
    brief = _copy("dirty_motion_brief.docx", tmp_path)
    result = runner.invoke(main, ["generate", str(brief)])
    assert result.exit_code == 1
    assert (tmp_path / "dirty_motion_brief.toa.docx").is_file()
    assert (tmp_path / "dirty_motion_brief.toa-report.md").is_file()


@_NEEDS_RENDER
def test_generate_memo_exits_0(runner: CliRunner, tmp_path: Path) -> None:
    """The marker memo bootstraps and exits 0."""
    brief = _copy("marker_trial_memo.docx", tmp_path)
    result = runner.invoke(main, ["generate", str(brief)])
    assert result.exit_code == 0


@_NEEDS_RENDER
def test_generate_no_placement_suppresses_docx_exits_1(
    runner: CliRunner, memo_no_marker: Path
) -> None:
    """A no-placement run suppresses the .docx, still writes the report, exits 1."""
    result = runner.invoke(main, ["generate", str(memo_no_marker)])
    assert result.exit_code == 1
    assert "SUPPRESSED" in result.output
    # The applied profile is disclosed even on the suppressed/issues path.
    name = load_profile_by_id("frap").name
    assert f"profile: {name}" in result.output
    report = memo_no_marker.with_name("memo_no_marker.toa-report.md")
    assert report.is_file()
    assert not memo_no_marker.with_name("memo_no_marker.toa.docx").exists()


@_NEEDS_RENDER
def test_generate_output_option(runner: CliRunner, tmp_path: Path) -> None:
    """`--output` controls the .docx path; the report tracks its stem."""
    brief = _copy("clean_appellate_brief.docx", tmp_path)
    out = tmp_path / "custom.toa.docx"
    result = runner.invoke(main, ["generate", str(brief), "--output", str(out)])
    assert result.exit_code == 0
    assert out.is_file()
    assert (tmp_path / "custom.toa-report.md").is_file()
