"""Cross-validate the registry Pydantic model against its JSON Schema.

The registry is the canonical model (PRD FR-04); both directions must agree:

- A model instance serialized to JSON validates against ``registry.schema.json``.
- A dict the schema accepts parses into the model, and a dict the schema rejects
  is also rejected by the model — for the same representative defects.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest
from jsonschema import Draft202012Validator
from pydantic import ValidationError

from toatool.models.registry import (
    Authority,
    CitationRegistry,
    Occurrence,
    RunMetadata,
)


def test_schema_is_a_valid_draft202012_schema(registry_schema: dict[str, Any]) -> None:
    """The registry schema is itself a well-formed Draft 2020-12 schema."""
    Draft202012Validator.check_schema(registry_schema)


def test_valid_dict_passes_both_model_and_schema(
    valid_registry_dict: Callable[[], dict[str, Any]],
    registry_schema: dict[str, Any],
) -> None:
    """A representative registry validates under both the model and the schema."""
    data = valid_registry_dict()
    Draft202012Validator(registry_schema).validate(data)
    registry = CitationRegistry.model_validate(data)
    assert registry.authorities[0].authority_id == "case::carmody-512-f3d-1042"


def test_model_dump_round_trips_through_schema(
    valid_registry_dict: Callable[[], dict[str, Any]],
    registry_schema: dict[str, Any],
) -> None:
    """A model serialized to JSON mode validates against the schema (model → schema)."""
    registry = CitationRegistry.model_validate(valid_registry_dict())
    dumped = registry.model_dump(mode="json")
    Draft202012Validator(registry_schema).validate(dumped)


def test_partial_registry_allows_null_occurrence_page(
    registry_schema: dict[str, Any],
) -> None:
    """An occurrence without a measured page is valid (the partial-registry case)."""
    occurrence = Occurrence(
        form="full",
        raw_text="Hartwell Industries v. NLRB, 723 F.2d 388 (2d Cir. 1984)",
        paragraph_index=8,
        char_span=(0, 55),
        confidence="medium",
    )
    assert occurrence.page is None
    authority = Authority(
        authority_id="case::hartwell",
        type="case",
        components={"reporter": "F.2d"},
        display_full="Hartwell Industries v. NLRB, 723 F.2d 388 (2d Cir. 1984)",
        sort_key="hartwell industries v nlrb",
        group="cases",
        occurrences=[occurrence],
        pages=[],
        passim=False,
    )
    registry = CitationRegistry(
        authorities=[authority],
        run_metadata=RunMetadata(
            engine_version="0.1.0",
            rule_pack_version="1.0.0",
            profile_id="frap",
            profile_version="1.0.0",
            render_engine="LibreOffice",
            render_engine_version="24.2",
            font_substitution_occurred=False,
            iteration_count=1,
            converged=True,
            input_sha256="b" * 64,
        ),
    )
    dumped = registry.model_dump(mode="json")
    assert dumped["authorities"][0]["occurrences"][0]["page"] is None
    Draft202012Validator(registry_schema).validate(dumped)


def test_empty_authorities_is_valid(
    valid_registry_dict: Callable[[], dict[str, Any]],
    registry_schema: dict[str, Any],
) -> None:
    """A brief that cites nothing yields a registry with zero authorities."""
    data = valid_registry_dict()
    data["authorities"] = []
    Draft202012Validator(registry_schema).validate(data)
    assert CitationRegistry.model_validate(data).authorities == []


@pytest.mark.parametrize(
    "mutate",
    [
        pytest.param(
            lambda d: d["authorities"][0].update({"surprise": 1}),
            id="extra-authority-key",
        ),
        pytest.param(
            lambda d: d["authorities"][0].update({"type": "brief"}), id="bad-type-enum"
        ),
        pytest.param(
            lambda d: d["authorities"][0].update({"group": "opinions"}),
            id="bad-group-enum",
        ),
        pytest.param(
            lambda d: d["authorities"][0]["occurrences"][0].update(
                {"form": "footnote"}
            ),
            id="bad-form-enum",
        ),
        pytest.param(
            lambda d: d["authorities"][0]["occurrences"][0].update(
                {"confidence": "low"}
            ),
            id="occurrence-low-confidence",
        ),
        pytest.param(
            lambda d: d["authorities"][0]["occurrences"][0].update({"char_span": [1]}),
            id="char-span-too-short",
        ),
        pytest.param(
            lambda d: d["authorities"][0].update({"pages": [0]}), id="page-below-one"
        ),
        pytest.param(
            lambda d: d["run_metadata"].update({"input_sha256": "tooshort"}),
            id="bad-sha256",
        ),
        pytest.param(
            lambda d: d["run_metadata"].update({"engine_version": "0.1"}),
            id="bad-semver",
        ),
        pytest.param(
            lambda d: d["run_metadata"].update({"profile_id": "FRAP"}),
            id="bad-profile-id",
        ),
        pytest.param(lambda d: d.pop("run_metadata"), id="missing-run-metadata"),
        pytest.param(
            lambda d: d["run_metadata"].update({"iteration_count": 0}),
            id="iteration-below-one",
        ),
    ],
)
def test_invalid_dicts_rejected_by_both(
    valid_registry_dict: Callable[[], dict[str, Any]],
    registry_schema: dict[str, Any],
    mutate: Callable[[dict[str, Any]], Any],
) -> None:
    """Each representative defect is rejected by both the schema and the model."""
    data = valid_registry_dict()
    mutate(data)

    validator = Draft202012Validator(registry_schema)
    assert not validator.is_valid(data), "schema unexpectedly accepted invalid data"

    with pytest.raises(ValidationError):
        CitationRegistry.model_validate(data)
