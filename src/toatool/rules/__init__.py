"""The ``toa`` rule pack: the eight TT rules and their construction.

:data:`RULE_CLASSES` maps each rule id to its implementation. :func:`build_rules`
instantiates the active rules from their loaded cards, so a rule carries its own
card (version, citations, severity default). The runner cross-checks
:data:`RULE_CLASSES` against the cards with the rule loader's drift check before
building, so a card without an implementation (or vice versa) fails loudly.
"""

from __future__ import annotations

from collections.abc import Mapping

from toatool.engine.rule_loader import RuleCard
from toatool.rules.base import (
    BaseRule,
    Rule,
    RuleContext,
    make_finding,
    sort_findings,
)
from toatool.rules.tt001 import TT001
from toatool.rules.tt002 import TT002
from toatool.rules.tt003 import TT003
from toatool.rules.tt004 import TT004
from toatool.rules.tt005 import TT005
from toatool.rules.tt006 import TT006
from toatool.rules.tt007 import TT007
from toatool.rules.tt008 import TT008

#: Every implemented rule, keyed by its rule id. The runner validates this set
#: against the loaded cards (Principle 8.5 drift check) before building rules.
RULE_CLASSES: dict[str, type[BaseRule]] = {
    "TT-001": TT001,
    "TT-002": TT002,
    "TT-003": TT003,
    "TT-004": TT004,
    "TT-005": TT005,
    "TT-006": TT006,
    "TT-007": TT007,
    "TT-008": TT008,
}


def build_rules(cards: Mapping[str, RuleCard]) -> list[Rule]:
    """Instantiate the active rules from their cards, in rule-id order.

    Args:
        cards: The loaded rule cards, keyed by id.

    Returns:
        One rule instance per active card that has an implementation, sorted by
        rule id. Inactive cards and ids without an implementation are skipped
        (the runner's drift check is what turns those into errors).
    """
    rules: list[Rule] = []
    for rule_id, card in sorted(cards.items()):
        if card.status != "active" or rule_id not in RULE_CLASSES:
            continue
        rules.append(RULE_CLASSES[rule_id](card))
    return rules


__all__ = [
    "RULE_CLASSES",
    "Rule",
    "RuleContext",
    "build_rules",
    "make_finding",
    "sort_findings",
]
