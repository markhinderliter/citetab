"""Tests for the rule-card loader and the drift check.

Validates that all nine TT cards load with the frontmatter the design package
specifies, that malformed cards fail loudly, and that the
card-vs-implementation drift check catches every kind of mismatch.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from citetab.engine.rule_loader import (
    RuleCard,
    RuleLoaderError,
    active_rule_ids,
    load_rule_card,
    load_rule_cards,
    validate_implementations,
)

ALL_RULE_IDS = {f"TT-00{n}" for n in range(1, 10)}

# Severity/confidence/blocking taken directly from the ratified rule cards and
# rules/CHANGELOG.md, so this also guards against a card's frontmatter drifting.
EXPECTED = {
    "TT-001": ("error", "high", False),
    "TT-002": ("info", "high", False),
    "TT-003": ("info", "high", False),
    "TT-004": ("warning", "medium", False),
    "TT-005": ("error", "high", True),
    "TT-006": ("warning", "high", False),
    "TT-007": ("error", "high", False),
    "TT-008": ("warning", "high", False),
    "TT-009": ("warning", "high", False),
}


def test_all_nine_cards_load(rules_dir: Path) -> None:
    """The toa pack loads exactly the nine TT cards."""
    cards = load_rule_cards(rules_dir)
    assert set(cards) == ALL_RULE_IDS


@pytest.mark.parametrize("rule_id", sorted(ALL_RULE_IDS))
def test_card_frontmatter_matches_ratified_contract(
    rules_dir: Path, rule_id: str
) -> None:
    """Each card's severity, confidence, and blocking flag match the design package."""
    cards = load_rule_cards(rules_dir)
    card = cards[rule_id]
    severity, confidence, blocks = EXPECTED[rule_id]
    assert card.severity_default == severity
    assert card.confidence_default == confidence
    assert card.blocks_docx_output == blocks
    assert card.domain == "toa"
    assert card.status == "active"
    assert card.version == "1.0.0"
    assert card.citations, "every card must carry at least one citation"


def test_tt005_is_the_only_blocking_rule(rules_dir: Path) -> None:
    """Exactly one rule suppresses the .docx, and it is TT-005."""
    cards = load_rule_cards(rules_dir)
    blocking = {rid for rid, card in cards.items() if card.blocks_docx_output}
    assert blocking == {"TT-005"}


def test_all_cards_are_active(rules_dir: Path) -> None:
    """All nine cards are active in v1."""
    cards = load_rule_cards(rules_dir)
    assert active_rule_ids(cards) == ALL_RULE_IDS


def test_load_single_card(rules_dir: Path) -> None:
    """A single card parses into a typed RuleCard."""
    card = load_rule_card(rules_dir / "toa" / "TT-001-unresolved-short-form.md")
    assert isinstance(card, RuleCard)
    assert card.id == "TT-001"
    assert card.name == "Unresolvable short-form citation"
    sources = {c.source for c in card.citations}
    assert {"FRAP", "The Bluebook"} <= sources


def test_validate_implementations_passes_when_complete(rules_dir: Path) -> None:
    """No drift when every active card has an implementation and vice versa."""
    cards = load_rule_cards(rules_dir)
    validate_implementations(cards, ALL_RULE_IDS)  # should not raise


def test_validate_implementations_detects_missing(rules_dir: Path) -> None:
    """A missing implementation for an active card is drift."""
    cards = load_rule_cards(rules_dir)
    with pytest.raises(RuleLoaderError, match="without an implementation"):
        validate_implementations(cards, ALL_RULE_IDS - {"TT-007"})


def test_validate_implementations_detects_orphan(rules_dir: Path) -> None:
    """An implementation with no card at all is drift."""
    cards = load_rule_cards(rules_dir)
    with pytest.raises(RuleLoaderError, match="without any rule card"):
        validate_implementations(cards, ALL_RULE_IDS | {"TT-099"})


def test_validate_implementations_detects_inactive_impl() -> None:
    """An implementation for a card that exists but is not active is drift."""
    deprecated = _card_with(status="deprecated")
    with pytest.raises(RuleLoaderError, match="for non-active card"):
        validate_implementations({deprecated.id: deprecated}, {deprecated.id})


def test_missing_frontmatter_raises(tmp_path: Path) -> None:
    """A card without a frontmatter block fails loudly."""
    bad = tmp_path / "TT-001.md"
    bad.write_text("# no frontmatter here\n", encoding="utf-8")
    with pytest.raises(RuleLoaderError, match="does not begin with a '---'"):
        load_rule_card(bad)


def test_unterminated_frontmatter_raises(tmp_path: Path) -> None:
    """A card whose frontmatter is never closed fails loudly."""
    bad = tmp_path / "TT-001.md"
    bad.write_text("---\nid: TT-001\nname: x\n", encoding="utf-8")
    with pytest.raises(RuleLoaderError, match="unterminated frontmatter"):
        load_rule_card(bad)


def test_card_validation_error_raises(tmp_path: Path) -> None:
    """A card with an invalid severity is rejected with the file named."""
    bad = tmp_path / "TT-001.md"
    bad.write_text(
        "---\n"
        "id: TT-001\n"
        "name: x\n"
        "version: 1.0.0\n"
        "effective_date: 2026-06-05\n"
        "domain: toa\n"
        "severity_default: fatal\n"
        "confidence_default: high\n"
        "blocks_docx_output: false\n"
        "citations:\n"
        "  - source: FRAP\n"
        "    section: '28(a)(2)'\n"
        "reads: []\n"
        "applies_when: []\n"
        "status: active\n"
        "---\nbody\n",
        encoding="utf-8",
    )
    with pytest.raises(RuleLoaderError, match="failed validation"):
        load_rule_card(bad)


def test_filename_id_mismatch_raises(tmp_path: Path, rules_dir: Path) -> None:
    """A card whose id does not match its filename prefix is rejected."""
    pack = tmp_path / "toa"
    pack.mkdir()
    original = (rules_dir / "toa" / "TT-001-unresolved-short-form.md").read_text(
        encoding="utf-8"
    )
    (pack / "TT-999-misnamed.md").write_text(original, encoding="utf-8")
    with pytest.raises(RuleLoaderError, match="does not match its filename"):
        load_rule_cards(tmp_path)


def test_empty_pack_raises(tmp_path: Path) -> None:
    """A pack directory with no cards fails loudly."""
    (tmp_path / "toa").mkdir()
    with pytest.raises(RuleLoaderError, match="contains no rule cards"):
        load_rule_cards(tmp_path)


def test_missing_pack_dir_raises(tmp_path: Path) -> None:
    """A missing pack directory fails loudly."""
    with pytest.raises(RuleLoaderError, match="does not exist"):
        load_rule_cards(tmp_path)


def test_unreadable_card_raises(tmp_path: Path) -> None:
    """A path that cannot be read as a file fails loudly (OSError → RuleLoaderError)."""
    directory = tmp_path / "TT-001.md"
    directory.mkdir()  # a directory cannot be read_text'd
    with pytest.raises(RuleLoaderError, match="cannot read rule card"):
        load_rule_card(directory)


def test_non_mapping_frontmatter_raises(tmp_path: Path) -> None:
    """Frontmatter that parses to a non-mapping is rejected."""
    bad = tmp_path / "TT-001.md"
    bad.write_text("---\n- a\n- b\n---\nbody\n", encoding="utf-8")
    with pytest.raises(RuleLoaderError, match="must be a YAML mapping"):
        load_rule_card(bad)


def test_invalid_yaml_frontmatter_raises(tmp_path: Path) -> None:
    """Frontmatter that is not valid YAML fails loudly."""
    bad = tmp_path / "TT-001.md"
    bad.write_text("---\nid: TT-001\n: : :\n  bad\n---\nbody\n", encoding="utf-8")
    with pytest.raises(RuleLoaderError, match="not valid YAML"):
        load_rule_card(bad)


def test_duplicate_rule_id_raises(tmp_path: Path, rules_dir: Path) -> None:
    """Two cards declaring the same id is drift and fails loudly."""
    pack = tmp_path / "toa"
    pack.mkdir()
    original = (rules_dir / "toa" / "TT-001-unresolved-short-form.md").read_text(
        encoding="utf-8"
    )
    (pack / "TT-001-a.md").write_text(original, encoding="utf-8")
    (pack / "TT-001-b.md").write_text(original, encoding="utf-8")
    with pytest.raises(RuleLoaderError, match="duplicate rule id 'TT-001'"):
        load_rule_cards(tmp_path)


def _card_with(**overrides: object) -> RuleCard:
    """Build a minimal valid RuleCard for drift-check tests."""
    base: dict[str, object] = {
        "id": "TT-042",
        "name": "Synthetic",
        "version": "1.0.0",
        "effective_date": "2026-06-05",
        "domain": "toa",
        "severity_default": "info",
        "confidence_default": "high",
        "blocks_docx_output": False,
        "citations": [{"source": "FRAP", "section": "28(a)(2)"}],
        "reads": [],
        "applies_when": [],
        "status": "active",
    }
    base.update(overrides)
    return RuleCard.model_validate(base)
