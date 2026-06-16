#!/usr/bin/env bash
#
# check.sh — the single quality gate for citetab.
#
# Runs, in order, the four checks that must pass before any PR is merged:
#
#   1. ruff check            — lint (pycodestyle, pyflakes, isort, bugbear,
#                              pyupgrade, simplify, naming, pydocstyle)
#   2. ruff format --check   — formatting is canonical
#   3. mypy                  — strict static typing (config in pyproject.toml)
#   4. pytest                — tests + the >=85% coverage gate (pyproject addopts)
#
# CI runs this exact script, and so should a contributor before opening a PR.
# Every check runs even if an earlier one fails, so one invocation surfaces the
# full picture; the script exits non-zero if any check failed.
#
# One deliberate local-vs-CI difference: tests marked @pytest.mark.calibrated
# assert specific measured page numbers / pagination-derived finding sets that
# only hold on the fixture-generating machine. They RUN LOCALLY (the real
# verification) but skip automatically under CI (the conftest hook keys on the
# CI env var) because a foreign runner's LibreOffice/fonts paginate differently.
# So: locally this script is the full gate; in CI the calibrated subset is
# deselected. LibreOffice-dependent tests also skip when LibreOffice is absent
# (marked skipif) — the portable render-backed tests still exercise it in CI.
#
# Usage:  ./scripts/check.sh           (run from anywhere; cd's to repo root)
#         Activate your virtualenv first, or ensure ruff/mypy/pytest are on PATH.

set -u

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

TARGETS=(src tests scripts)
failures=()

run_step() {
  local name="$1"
  shift
  printf '\n\033[1m==> %s\033[0m\n' "$name"
  if "$@"; then
    printf '\033[32m    %s: ok\033[0m\n' "$name"
  else
    printf '\033[31m    %s: FAILED\033[0m\n' "$name"
    failures+=("$name")
  fi
}

run_step "ruff check"        ruff check "${TARGETS[@]}"
run_step "ruff format check" ruff format --check "${TARGETS[@]}"
run_step "mypy --strict"     mypy
run_step "pytest + coverage" pytest

printf '\n'
if [ "${#failures[@]}" -eq 0 ]; then
  printf '\033[32mAll quality gates passed.\033[0m\n'
  exit 0
fi
printf '\033[31mFAILED: %s\033[0m\n' "${failures[*]}"
exit 1
