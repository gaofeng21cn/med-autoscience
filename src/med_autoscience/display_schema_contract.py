from __future__ import annotations

from med_autoscience import display_registry
from med_autoscience.display_schema_contract_parts import (
    DisplaySchemaClass,
    InputSchemaContract,
    _DISPLAY_SCHEMA_CLASSES,
    _INPUT_SCHEMA_CONTRACTS_DATA_GEOMETRY,
    _INPUT_SCHEMA_CONTRACTS_EFFECTS,
    _INPUT_SCHEMA_CONTRACTS_EXPLANATIONS,
    _INPUT_SCHEMA_CONTRACTS_GENERAL_PUBLICATION,
    _INPUT_SCHEMA_CONTRACTS_OMICS,
    _INPUT_SCHEMA_CONTRACTS_TIME_TO_EVENT,
)

_INPUT_SCHEMA_CONTRACTS: tuple[InputSchemaContract, ...] = (
    _INPUT_SCHEMA_CONTRACTS_TIME_TO_EVENT
    + _INPUT_SCHEMA_CONTRACTS_DATA_GEOMETRY
    + _INPUT_SCHEMA_CONTRACTS_OMICS
    + _INPUT_SCHEMA_CONTRACTS_EFFECTS
    + _INPUT_SCHEMA_CONTRACTS_EXPLANATIONS
    + _INPUT_SCHEMA_CONTRACTS_GENERAL_PUBLICATION
)

_INPUT_SCHEMA_CONTRACT_BY_ID = {item.input_schema_id: item for item in _INPUT_SCHEMA_CONTRACTS}

def _registered_template_ids() -> set[str]:
    return {
        *(item.template_id for item in display_registry.list_evidence_figure_specs()),
        *(item.shell_id for item in display_registry.list_illustration_shell_specs()),
        *(item.shell_id for item in display_registry.list_table_shell_specs()),
    }

def _validate_contract_registry_alignment() -> None:
    covered_template_ids = {
        template_id
        for schema in _INPUT_SCHEMA_CONTRACTS
        for template_id in schema.template_ids
    }
    covered_template_ids.update(
        template_id
        for display_class in _DISPLAY_SCHEMA_CLASSES
        for template_id in display_class.template_ids
    )
    missing_template_ids = _registered_template_ids() - covered_template_ids
    if missing_template_ids:
        missing = ", ".join(sorted(missing_template_ids))
        raise RuntimeError(f"display schema contract does not cover registered templates: {missing}")

def list_display_schema_classes() -> tuple[DisplaySchemaClass, ...]:
    return _DISPLAY_SCHEMA_CLASSES

def list_input_schema_contracts() -> tuple[InputSchemaContract, ...]:
    return _INPUT_SCHEMA_CONTRACTS

def get_input_schema_contract(input_schema_id: str) -> InputSchemaContract:
    normalized = str(input_schema_id or "").strip()
    try:
        return _INPUT_SCHEMA_CONTRACT_BY_ID[normalized]
    except KeyError as exc:
        raise ValueError(f"unknown input schema contract `{input_schema_id}`") from exc

_validate_contract_registry_alignment()
