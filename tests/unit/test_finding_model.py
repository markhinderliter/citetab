"""Cross-validate the seed Finding model against ``finding.schema.json``.

The Finding model ships as a design-phase seed; these tests lock it to its
schema in both directions and exercise its one custom invariant (error/warning
findings must carry a citation).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest
from jsonschema import Draft202012Validator
from pydantic import ValidationError

from toatool.models.finding import Finding


def test_finding_schema_is_valid(finding_schema: dict[str, Any]) -> None:
    """The finding schema is a well-formed Draft 2020-12 schema."""
    Draft202012Validator.check_schema(finding_schema)


def test_valid_finding_passes_both(
    valid_finding_dict: Callable[[], dict[str, Any]],
    finding_schema: dict[str, Any],
) -> None:
    """A representative finding validates under both the schema and the model."""
    data = valid_finding_dict()
    Draft202012Validator(finding_schema).validate(data)
    assert Finding.model_validate(data).rule_id == "TT-002"


def test_finding_dump_round_trips_through_schema(
    valid_finding_dict: Callable[[], dict[str, Any]],
    finding_schema: dict[str, Any],
) -> None:
    """A model serialized to JSON mode validates against the schema (model → schema)."""
    finding = Finding.model_validate(valid_finding_dict())
    Draft202012Validator(finding_schema).validate(
        finding.model_dump(mode="json", exclude_none=True)
    )


def test_error_finding_requires_citation_in_model(
    valid_finding_dict: Callable[[], dict[str, Any]],
) -> None:
    """The model rejects an error finding with no citations (its custom invariant)."""
    data = valid_finding_dict()
    data["severity"] = "error"
    data["citations"] = []
    with pytest.raises(ValidationError, match="must carry at least one citation"):
        Finding.model_validate(data)


def test_error_finding_requires_citation_in_schema(
    valid_finding_dict: Callable[[], dict[str, Any]],
    finding_schema: dict[str, Any],
) -> None:
    """The schema's allOf rejects an error finding with no citations too."""
    data = valid_finding_dict()
    data["severity"] = "error"
    data["citations"] = []
    assert not Draft202012Validator(finding_schema).is_valid(data)


def test_info_finding_may_omit_citations(
    valid_finding_dict: Callable[[], dict[str, Any]],
    finding_schema: dict[str, Any],
) -> None:
    """An info finding (a disclosure) is allowed to carry no citations."""
    data = valid_finding_dict()
    data["severity"] = "info"
    data["citations"] = []
    Draft202012Validator(finding_schema).validate(data)
    assert Finding.model_validate(data).citations == []


@pytest.mark.parametrize(
    "mutate",
    [
        pytest.param(
            lambda d: d.update({"finding_id": "not-a-ulid"}), id="bad-finding-id"
        ),
        pytest.param(lambda d: d.update({"rule_id": "TT-3"}), id="bad-rule-id"),
        pytest.param(lambda d: d.update({"severity": "fatal"}), id="bad-severity"),
        pytest.param(lambda d: d.update({"surprise": True}), id="extra-key"),
    ],
)
def test_invalid_findings_rejected_by_both(
    valid_finding_dict: Callable[[], dict[str, Any]],
    finding_schema: dict[str, Any],
    mutate: Callable[[dict[str, Any]], Any],
) -> None:
    """Representative finding defects are rejected by both schema and model."""
    data = valid_finding_dict()
    mutate(data)
    assert not Draft202012Validator(finding_schema).is_valid(data)
    with pytest.raises(ValidationError):
        Finding.model_validate(data)
