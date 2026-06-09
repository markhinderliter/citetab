"""Pydantic data models for toatool.

Two models form the canonical contract between the pipeline and every output:

- :mod:`toatool.models.registry` — the Citation Registry (``INPUT_OUTPUT_SPEC``
  §4): the single structure the pipeline produces and every output renders
  from.
- :mod:`toatool.models.finding` — the Finding (``schemas/finding.schema.json``):
  the canonical diagnostic unit emitted while generating the table.

Both cross-validate against their JSON Schemas in ``schemas/`` in both
directions; see ``tests/unit``.
"""

from __future__ import annotations
