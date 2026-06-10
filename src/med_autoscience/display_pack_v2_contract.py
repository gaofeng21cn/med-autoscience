from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any


CONTRACT_ID = "display-pack-contract.v2"
SCHEMA_VERSION = 2
CONTRACT_FILENAME = "display-pack-contract.v2.json"

REQUIRED_PACK_DESCRIPTOR_FIELDS = frozenset(
    (
        "pack_id",
        "version",
        "display_api_version",
        "source",
        "owner",
        "license",
        "templates",
        "style_profiles",
        "qc_profiles",
        "ai_policy",
        "goldens",
        "exemplars",
        "provenance",
        "opl_handoff",
    )
)

REQUIRED_TEMPLATE_DESCRIPTOR_FIELDS = frozenset(
    (
        "template_id",
        "full_template_id",
        "kind",
        "display_name",
        "paper_family_ids",
        "audit_family",
        "renderer_family",
        "input_schema_ref",
        "qc_profile_ref",
        "style_profile_ref",
        "required_exports",
        "execution_mode",
        "entrypoint",
        "paper_proven",
        "golden_case_paths",
        "exemplar_refs",
    )
)

REQUIRED_AUTHORITY_BOUNDARIES = {
    "mas_pack_descriptor_authority": True,
    "mas_publication_quality_authority": True,
    "mas_owns_opl_generic_pack_os": False,
    "opl_can_write_mas_publication_truth": False,
    "display_pack_lock_can_authorize_publication_readiness": False,
}

OPL_HANDOFF_TAIL_STATUS = "opl_consumer_smoke_landed"
OPL_EXTERNAL_CONSUMER_STATUS = "landed_in_opl_repo"
OPL_EXTERNAL_CONSUMER_SURFACE = "opl pack os mas-display-smoke"


def default_contract_path() -> Path:
    return Path(__file__).resolve().parents[2] / "contracts" / CONTRACT_FILENAME


def load_display_pack_v2_contract(path: Path | None = None) -> dict[str, Any]:
    contract_path = path or default_contract_path()
    payload = json.loads(contract_path.read_text(encoding="utf-8"))
    return validate_display_pack_v2_contract(payload)


def validate_display_pack_v2_contract(payload: Any) -> dict[str, Any]:
    contract = _require_object(payload, "display_pack_v2_contract")
    _require_schema_version(contract)
    _require_contract_id(contract)
    _require_required_fields(
        contract,
        "pack_descriptor",
        expected=REQUIRED_PACK_DESCRIPTOR_FIELDS,
    )
    _require_required_fields(
        contract,
        "template_descriptor",
        expected=REQUIRED_TEMPLATE_DESCRIPTOR_FIELDS,
    )
    _require_authority_boundaries(contract)
    _require_opl_handoff_tail(contract)
    return dict(contract)


def _require_object(value: Any, context: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{context} must be a JSON object")
    return dict(value)


def _require_schema_version(contract: Mapping[str, Any]) -> None:
    schema_version = contract.get("schema_version")
    if isinstance(schema_version, bool) or not isinstance(schema_version, int):
        raise ValueError("display_pack_v2_contract.schema_version must be an integer")
    if schema_version != SCHEMA_VERSION:
        raise ValueError(f"display_pack_v2_contract.schema_version must equal {SCHEMA_VERSION}")


def _require_contract_id(contract: Mapping[str, Any]) -> None:
    contract_id = contract.get("contract_id")
    if contract_id != CONTRACT_ID:
        raise ValueError(f"display_pack_v2_contract.contract_id must equal {CONTRACT_ID!r}")


def _require_string_list(item: Mapping[str, Any], field_name: str, *, context: str) -> list[str]:
    value = item.get(field_name)
    if not isinstance(value, list) or not value:
        raise ValueError(f"{context}.{field_name} must be a non-empty list of strings")
    normalized: list[str] = []
    for index, entry in enumerate(value):
        if not isinstance(entry, str) or not entry.strip():
            raise ValueError(f"{context}.{field_name}[{index}] must be a non-empty string")
        normalized.append(entry.strip())
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{context}.{field_name} must not contain duplicate values")
    return normalized


def _require_required_fields(
    contract: Mapping[str, Any],
    section_name: str,
    *,
    expected: frozenset[str],
) -> None:
    section = _require_object(contract.get(section_name), section_name)
    required_fields = set(
        _require_string_list(
            section,
            "required_fields",
            context=section_name,
        )
    )
    missing = sorted(expected - required_fields)
    unexpected = sorted(required_fields - expected)
    if missing or unexpected:
        raise ValueError(
            f"{section_name}.required_fields must match Display Pack v2 required fields; "
            f"missing={missing!r}; unexpected={unexpected!r}"
        )


def _require_authority_boundaries(contract: Mapping[str, Any]) -> None:
    authority_boundaries = _require_object(
        contract.get("authority_boundaries"),
        "authority_boundaries",
    )
    for field_name, expected_value in REQUIRED_AUTHORITY_BOUNDARIES.items():
        value = authority_boundaries.get(field_name)
        if value is not expected_value:
            raise ValueError(f"authority_boundaries.{field_name} must be {expected_value!r}")


def _require_opl_handoff_tail(contract: Mapping[str, Any]) -> None:
    handoff = _require_object(contract.get("opl_handoff"), "opl_handoff")
    status = _require_non_empty_string(handoff, "status", context="opl_handoff")
    if status != "handoff_tail":
        raise ValueError("opl_handoff.status must equal 'handoff_tail'")
    tail_status = _require_non_empty_string(handoff, "tail_status", context="opl_handoff")
    if tail_status != OPL_HANDOFF_TAIL_STATUS:
        raise ValueError(f"opl_handoff.tail_status must equal {OPL_HANDOFF_TAIL_STATUS!r}")
    target_owner = _require_non_empty_string(handoff, "target_owner", context="opl_handoff")
    if target_owner != "OPL Pack OS":
        raise ValueError("opl_handoff.target_owner must equal 'OPL Pack OS'")
    external_consumer = _require_object(
        handoff.get("external_opl_consumer"),
        "opl_handoff.external_opl_consumer",
    )
    external_status = _require_non_empty_string(
        external_consumer,
        "status",
        context="opl_handoff.external_opl_consumer",
    )
    if external_status != OPL_EXTERNAL_CONSUMER_STATUS:
        raise ValueError(
            "opl_handoff.external_opl_consumer.status must equal "
            f"{OPL_EXTERNAL_CONSUMER_STATUS!r}"
        )
    surface = _require_non_empty_string(
        external_consumer,
        "surface",
        context="opl_handoff.external_opl_consumer",
    )
    if surface != OPL_EXTERNAL_CONSUMER_SURFACE:
        raise ValueError(
            "opl_handoff.external_opl_consumer.surface must equal "
            f"{OPL_EXTERNAL_CONSUMER_SURFACE!r}"
        )
    _require_string_list(
        external_consumer,
        "verification_refs",
        context="opl_handoff.external_opl_consumer",
    )


def _require_non_empty_string(item: Mapping[str, Any], field_name: str, *, context: str) -> str:
    value = item.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{context}.{field_name} must be a non-empty string")
    return value.strip()


__all__ = [
    "CONTRACT_ID",
    "CONTRACT_FILENAME",
    "OPL_EXTERNAL_CONSUMER_STATUS",
    "OPL_EXTERNAL_CONSUMER_SURFACE",
    "OPL_HANDOFF_TAIL_STATUS",
    "REQUIRED_PACK_DESCRIPTOR_FIELDS",
    "REQUIRED_TEMPLATE_DESCRIPTOR_FIELDS",
    "SCHEMA_VERSION",
    "default_contract_path",
    "load_display_pack_v2_contract",
    "validate_display_pack_v2_contract",
]
