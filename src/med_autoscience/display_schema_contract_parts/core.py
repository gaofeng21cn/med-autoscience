from __future__ import annotations

from dataclasses import dataclass, field
from collections.abc import Mapping

from .domain_registry import (
    input_schema_ids_for_evidence_class,
    template_ids_for_evidence_class,
    template_ids_for_input_schema,
)
from .validation import freeze_contract_mapping


@dataclass(frozen=True)
class DisplaySchemaClass:
    class_id: str
    display_name: str
    template_ids: tuple[str, ...]
    input_schema_ids: tuple[str, ...]


@dataclass(frozen=True)
class InputSchemaContract:
    input_schema_id: str
    display_kind: str
    display_name: str
    template_ids: tuple[str, ...]
    required_top_level_fields: tuple[str, ...]
    optional_top_level_fields: tuple[str, ...] = ()
    display_required_fields: tuple[str, ...] = ()
    display_optional_fields: tuple[str, ...] = ()
    collection_required_fields: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    collection_optional_fields: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    nested_collection_required_fields: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    nested_collection_optional_fields: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    additional_constraints: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "collection_required_fields", freeze_contract_mapping(self.collection_required_fields))
        object.__setattr__(self, "collection_optional_fields", freeze_contract_mapping(self.collection_optional_fields))
        object.__setattr__(
            self,
            "nested_collection_required_fields",
            freeze_contract_mapping(self.nested_collection_required_fields),
        )
        object.__setattr__(
            self,
            "nested_collection_optional_fields",
            freeze_contract_mapping(self.nested_collection_optional_fields),
        )


def _template_ids_for_evidence_class(evidence_class: str) -> tuple[str, ...]:
    return template_ids_for_evidence_class(evidence_class)


def _input_schema_ids_for_evidence_class(evidence_class: str) -> tuple[str, ...]:
    return input_schema_ids_for_evidence_class(evidence_class)


def _template_ids_for_input_schema(input_schema_id: str) -> tuple[str, ...]:
    return template_ids_for_input_schema(input_schema_id)
