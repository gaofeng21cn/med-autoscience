from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from med_autoscience import display_registry


def _freeze_mapping(mapping: Mapping[str, tuple[str, ...]] | None) -> Mapping[str, tuple[str, ...]]:
    frozen = {str(key): tuple(value) for key, value in (mapping or {}).items()}
    return MappingProxyType(frozen)


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
        object.__setattr__(self, "collection_required_fields", _freeze_mapping(self.collection_required_fields))
        object.__setattr__(self, "collection_optional_fields", _freeze_mapping(self.collection_optional_fields))
        object.__setattr__(
            self,
            "nested_collection_required_fields",
            _freeze_mapping(self.nested_collection_required_fields),
        )
        object.__setattr__(
            self,
            "nested_collection_optional_fields",
            _freeze_mapping(self.nested_collection_optional_fields),
        )


def _template_ids_for_evidence_class(evidence_class: str) -> tuple[str, ...]:
    return tuple(
        spec.template_id
        for spec in display_registry.list_evidence_figure_specs()
        if spec.evidence_class == evidence_class
    )


def _template_ids_for_input_schema(input_schema_id: str) -> tuple[str, ...]:
    evidence_template_ids = tuple(
        spec.template_id
        for spec in display_registry.list_evidence_figure_specs()
        if spec.input_schema_id == input_schema_id
    )
    illustration_shell_ids = tuple(
        spec.shell_id
        for spec in display_registry.list_illustration_shell_specs()
        if spec.input_schema_id == input_schema_id
    )
    table_shell_ids = tuple(
        spec.shell_id
        for spec in display_registry.list_table_shell_specs()
        if spec.input_schema_id == input_schema_id
    )
    return evidence_template_ids + illustration_shell_ids + table_shell_ids
