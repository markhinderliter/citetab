"""QA Round 3 — robustness & graceful-degradation harness.

Round 3 asks what a *user* gets on hostile or hard input. Unlike Round 2, it
drives the **real `toatool generate` CLI as a subprocess** — not the in-process
API — because the failure mode we care about (an uncaught exception) would crash
an in-process harness instead of being recorded. The bar (docs/QA_ROUND3.md):
every input either rejects cleanly (exit 2, one-line stderr, nothing written) or
degrades honestly (output / clean suppression + disclosure). **A Python
traceback in stderr is always a FAIL.**

This increment implements **C2-a**, the H1 probe: a valid brief with its TOA
intact and a body pincite split across a page boundary so it cannot be measured
on the emitting path. The fixture is *constructed* (a hard page break injected
inside the citation), not frozen — deterministic and font/version-independent.
The same condition also arises naturally from pagination shifts (confirmed during
development at ~36 filler paragraphs before the body).

Usage::

    .venv-qa/bin/python scripts/qa_round3.py
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

import docx
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

REPO_ROOT = Path(__file__).resolve().parent.parent
CLEAN = REPO_ROOT / "examples" / "briefs" / "clean_appellate_brief.docx"
RESULTS = REPO_ROOT / "docs" / "QA_ROUND3_RESULTS.md"

# The pincite to split across a page boundary, and the token to break before.
_SPLIT_CITATION = "512 F.3d at 1047"
_SPLIT_MARKER = "1047"

_TRACEBACK_MARKER = "Traceback (most recent call last)"


# --------------------------------------------------------------------------- #
# Subprocess CLI runner — what the user actually sees.
# --------------------------------------------------------------------------- #
def _toatool() -> str:
    """Resolve the `toatool` console script next to the running interpreter."""
    candidate = Path(sys.executable).with_name("toatool")
    if not candidate.exists():
        raise FileNotFoundError(
            f"toatool console script not found at {candidate}; "
            "run the harness with the venv that has toatool installed"
        )
    return str(candidate)


@dataclass
class CliRun:
    """The observable result of one real `toatool generate` invocation."""

    exit_code: int
    stdout: str
    stderr: str
    files_written: list[str]

    @property
    def has_traceback(self) -> bool:
        """True if a Python traceback escaped to stderr (the cardinal sin)."""
        return _TRACEBACK_MARKER in self.stderr

    @property
    def report_written(self) -> bool:
        """True if a findings report was produced."""
        return any(name.endswith(".toa-report.md") for name in self.files_written)


def run_cli(brief: Path) -> CliRun:
    """Run `toatool generate <brief>` as a subprocess and capture what a user sees."""
    folder = brief.parent
    stem = brief.stem
    before = {p.name for p in folder.iterdir()}
    proc = subprocess.run(  # noqa: S603 — fixed argv, local tool, QA harness
        [_toatool(), "generate", str(brief)],
        capture_output=True,
        text=True,
        cwd=str(folder),
    )
    after = {p.name for p in folder.iterdir()}
    written = sorted(
        name
        for name in (after - before)
        if name.startswith(stem) and (name.endswith(".docx") or name.endswith(".md"))
    )
    return CliRun(proc.returncode, proc.stdout, proc.stderr, written)


# --------------------------------------------------------------------------- #
# C2-a fixture construction (deterministic boundary split).
# --------------------------------------------------------------------------- #
def construct_c2a(workdir: Path) -> Path:
    """Build the C2-a fixture: a pincite split across a page boundary.

    Injects a hard page break inside the Carmody pincite ``512 F.3d at 1047`` so
    its rendered text spans two physical pages and the locator cannot place it.
    Deterministic and font/version-independent (unlike padding the body), so the
    harness is reproducible across environments. The same condition also arises
    naturally from pagination shifts — confirmed during development at ~36 filler
    paragraphs before the body.
    """
    fixture = workdir / "c2a_boundary_split.docx"
    shutil.copy(CLEAN, fixture)
    document = docx.Document(str(fixture))
    target = next(p for p in document.paragraphs if _SPLIT_CITATION in p.text)
    text = target.text
    index = text.find(_SPLIT_MARKER)
    prefix, rest = text[:index], text[index:]
    for run in list(target.runs):
        run._element.getparent().remove(run._element)
    target.add_run(prefix)
    break_run = target.add_run()
    page_break = OxmlElement("w:br")
    page_break.set(qn("w:type"), "page")
    break_run._element.append(page_break)
    target.add_run(rest)
    document.save(str(fixture))
    return fixture


# --------------------------------------------------------------------------- #
# Evaluate C2-a against the Round 3 bar.
# --------------------------------------------------------------------------- #
@dataclass
class CaseResult:
    """The verdict for one Round 3 case."""

    slug: str
    title: str
    passed: bool
    detail: str


def evaluate_c2a(workdir: Path) -> CaseResult:
    """Construct C2-a, run it through the real CLI, and judge against the bar."""
    fixture = construct_c2a(workdir)
    run = run_cli(fixture)
    report = next(
        (fixture.parent / n for n in run.files_written if n.endswith(".toa-report.md")),
        None,
    )
    report_text = report.read_text(encoding="utf-8") if report else ""
    discloses = "TT-009" in report_text and "p.?" in report_text

    # The bar: no traceback; .docx + report written; the gap disclosed via TT-009.
    docx_written = any(n.endswith(".toa.docx") for n in run.files_written)
    passed = (
        (not run.has_traceback)
        and run.exit_code == 0
        and run.report_written
        and docx_written
        and discloses
    )
    verdict = "graceful + disclosed" if passed else "DEAD-END / undisclosed"
    tb = "YES" if run.has_traceback else "no"
    disc = "yes" if discloses else "NO"
    detail = (
        f"Real CLI exit={run.exit_code}; traceback={tb}; "
        f"files written={run.files_written or 'none'}; "
        f"TT-009 disclosure in report={disc}. Outcome: {verdict}."
    )
    return CaseResult(
        "C2-a",
        "Boundary-unmeasurable occurrence on the emitting path (H1)",
        passed,
        detail,
    )


def write_results(results: list[CaseResult]) -> None:
    """Write the (in-progress) Round 3 results report."""
    passed = sum(1 for r in results if r.passed)
    lines = [
        "# QA Round 3 — robustness results (in progress)",
        "",
        "Generated by `scripts/qa_round3.py`. Method and the full case list: see "
        "[QA_ROUND3.md](QA_ROUND3.md). The harness drives the real `toatool "
        "generate` CLI as a subprocess; a Python traceback in stderr is a FAIL.",
        "",
        f"**C2-a only (the H1 probe) this run: {passed}/{len(results)} passed.**",
        "",
    ]
    for r in results:
        lines.append(f"### {r.slug} — {r.title}")
        lines.append("")
        lines.append(f"- **Verdict:** {'PASS' if r.passed else 'FAIL'}")
        lines.append(f"- {r.detail}")
        lines.append("")
    RESULTS.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    """Run the implemented Round 3 cases and report."""
    with tempfile.TemporaryDirectory() as td:
        results = [evaluate_c2a(Path(td))]
    write_results(results)
    for r in results:
        print(f"[{'PASS' if r.passed else 'FAIL'}] {r.slug}: {r.detail}")
    passed = sum(1 for r in results if r.passed)
    print(f"\n{passed}/{len(results)} passed — summary: {RESULTS}")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
