"""Load rule-card frontmatter and detect drift against implementations.

Each rule is a versioned Markdown card in ``rules/toa/`` with a YAML
frontmatter block (the machine-readable contract) followed by prose. This module
parses and validates that frontmatter into a typed :class:`RuleCard`, and checks
that every *active* card has a matching implementation and vice versa — the
executable form of Principle 8.5 ("the loader validates cards against
implementations at startup; spec drift fails loudly").

The implementation cross-check takes the set of implemented rule ids as an
argument rather than importing the rule modules itself, so the two concerns stay
decoupled: card loading is fully usable before any rule is implemented (the rule
modules arrive in a later build phase), and the drift check is exercised against
that set when the runner is wired.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import date
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from toatool.engine.resources import rules_dir
from toatool.models.finding import Confidence, Severity

_RULE_ID = r"^[A-Z]{2}-[0-9]{3}$"
_SEMVER = r"^[0-9]+\.[0-9]+\.[0-9]+$"

_FRONTMATTER_DELIMITER = "---"

#: The ``toa`` rule-pack version (the rule-pack SemVer track, ``rules/CHANGELOG.md``).
#: Recorded on every finding and in the registry's run metadata.
RULE_PACK_VERSION = "1.0.0"


class RuleLoaderError(Exception):
    """Raised when a rule card cannot be read, parsed, or validated, or drifts."""


class CardCitation(BaseModel):
    """A rule or style authority declared in a card's frontmatter."""

    model_config = ConfigDict(extra="forbid")

    source: str
    """Authority source (e.g. ``FRAP``, ``The Bluebook``, ``INPUT_OUTPUT_SPEC.md``)."""

    section: str
    """Section within the source (e.g. ``28(a)(2)``, ``Rule 10.9``, ``§2.4``)."""

    description: str | None = None
    """Optional gloss on why this authority supports the rule."""

    url: str | None = None
    """Optional URL to the cited text."""


class RuleCard(BaseModel):
    """The validated frontmatter contract of a single rule card.

    Mirrors the YAML block at the top of each ``rules/toa/TT-*.md``. The prose
    body of the card is not modeled here; it is reference material for humans and
    for ``toatool rules show``.
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=_RULE_ID)
    """Rule identifier (e.g. ``TT-003``)."""

    name: str
    """Human-readable rule name."""

    version: str = Field(pattern=_SEMVER)
    """Semantic version of this rule card (the individual-rule SemVer track)."""

    effective_date: date
    """The date this rule version took effect."""

    domain: Literal["toa"]
    """Rule pack the card belongs to. v1 has one pack, ``toa``."""

    severity_default: Severity
    """Default severity the rule emits (``error``, ``warning``, or ``info``)."""

    confidence_default: Confidence
    """Default confidence the rule emits (v1 cards use ``high`` or ``medium``)."""

    blocks_docx_output: bool
    """Whether a finding from this rule suppresses the .docx (TT-005 only)."""

    citations: list[CardCitation] = Field(min_length=1)
    """Authorities supporting the rule, copied into each finding it emits."""

    reads: list[dict[str, str]]
    """Registry/pipeline/input sources the rule reads; documentation of data flow."""

    applies_when: list[str]
    """Plain-language conditions under which the rule evaluates."""

    status: Literal["active", "deprecated"]
    """Lifecycle status. Only ``active`` cards require an implementation."""


def _split_frontmatter(text: str, source: str) -> str:
    """Extract the YAML frontmatter block from a card's Markdown text.

    Args:
        text: The full card file contents.
        source: A label (path) for error messages.

    Returns:
        The raw YAML between the opening and closing ``---`` delimiters.

    Raises:
        RuleLoaderError: If the text does not open with a frontmatter block or
            the block is not closed.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != _FRONTMATTER_DELIMITER:
        raise RuleLoaderError(
            f"rule card '{source}' does not begin with a '---' frontmatter block"
        )
    for index in range(1, len(lines)):
        if lines[index].strip() == _FRONTMATTER_DELIMITER:
            return "\n".join(lines[1:index])
    raise RuleLoaderError(f"rule card '{source}' has an unterminated frontmatter block")


def load_rule_card(path: Path) -> RuleCard:
    """Load and validate a single rule card.

    Args:
        path: Path to the ``TT-*.md`` card file.

    Returns:
        The validated :class:`RuleCard`.

    Raises:
        RuleLoaderError: If the file cannot be read, has no valid frontmatter,
            or fails schema validation. The message names the file.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RuleLoaderError(f"cannot read rule card '{path}': {exc}") from exc

    frontmatter = _split_frontmatter(text, str(path))

    try:
        data = yaml.safe_load(frontmatter)
    except yaml.YAMLError as exc:
        raise RuleLoaderError(
            f"rule card '{path}' frontmatter is not valid YAML: {exc}"
        ) from exc

    if not isinstance(data, dict):
        raise RuleLoaderError(
            f"rule card '{path}' frontmatter must be a YAML mapping, "
            f"got {type(data).__name__}"
        )

    try:
        return RuleCard.model_validate(data)
    except ValidationError as exc:
        raise RuleLoaderError(f"rule card '{path}' failed validation:\n{exc}") from exc


def load_rule_cards(
    rules_root: Path | None = None, domain: str = "toa"
) -> dict[str, RuleCard]:
    """Load every rule card in a pack, keyed by rule id.

    Args:
        rules_root: The ``rules`` directory; defaults to the resolved data dir.
        domain: The rule-pack subdirectory to read (v1: ``toa``).

    Returns:
        A mapping of rule id to :class:`RuleCard`, in sorted id order.

    Raises:
        RuleLoaderError: If the pack directory is missing, contains no cards, a
            card's declared ``id`` does not match its filename prefix, or two
            cards declare the same id.
    """
    root = rules_root if rules_root is not None else rules_dir()
    pack_dir = root / domain
    if not pack_dir.is_dir():
        raise RuleLoaderError(f"rule pack directory '{pack_dir}' does not exist")

    paths = sorted(pack_dir.glob("*.md"))
    if not paths:
        raise RuleLoaderError(f"rule pack '{pack_dir}' contains no rule cards")

    cards: dict[str, RuleCard] = {}
    for path in paths:
        card = load_rule_card(path)
        if not path.name.startswith(card.id):
            raise RuleLoaderError(
                f"rule card '{path}' declares id '{card.id}', which does not "
                f"match its filename"
            )
        if card.id in cards:
            raise RuleLoaderError(f"duplicate rule id '{card.id}' in '{pack_dir}'")
        cards[card.id] = card
    return cards


def active_rule_ids(cards: Mapping[str, RuleCard]) -> set[str]:
    """Return the ids of cards whose ``status`` is ``active``.

    Args:
        cards: A mapping of rule id to :class:`RuleCard`.

    Returns:
        The set of active rule ids.
    """
    return {rule_id for rule_id, card in cards.items() if card.status == "active"}


def validate_implementations(
    cards: Mapping[str, RuleCard], implemented_ids: Iterable[str]
) -> None:
    """Check that active cards and implementations correspond exactly.

    Every active card must have an implementation, and every implementation must
    have an active card. A mismatch is spec/implementation drift and fails
    loudly (Principle 8.5).

    Args:
        cards: A mapping of rule id to :class:`RuleCard`.
        implemented_ids: The rule ids for which an implementation exists.

    Raises:
        RuleLoaderError: If any active card lacks an implementation, or any
            implementation has no active card. The message names both gaps.
    """
    implemented = set(implemented_ids)
    active = active_rule_ids(cards)

    missing = active - implemented
    orphaned = implemented - set(cards)
    inactive_impl = (implemented & set(cards)) - active

    problems: list[str] = []
    if missing:
        problems.append(
            f"active rule card(s) without an implementation: {sorted(missing)}"
        )
    if orphaned:
        problems.append(f"implementation(s) without any rule card: {sorted(orphaned)}")
    if inactive_impl:
        problems.append(
            f"implementation(s) for non-active card(s): {sorted(inactive_impl)}"
        )

    if problems:
        raise RuleLoaderError("rule/implementation drift — " + "; ".join(problems))
