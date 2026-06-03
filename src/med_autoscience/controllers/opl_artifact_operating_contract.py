from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

CONTRACT_REF = "contracts/opl-framework/artifact-operating-contract.json"
CONTRACT_ID = "opl-artifact-operating-contract.v1"


def load_opl_artifact_operating_contract() -> dict[str, Any]:
    path = find_opl_artifact_operating_contract_path()
    if path is None:
        raise FileNotFoundError(f"missing OPL artifact operating contract: {CONTRACT_REF}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"{CONTRACT_REF} must contain a JSON object")
    contract = dict(payload)
    _validate_contract(contract)
    return contract


def operating_contract_projection(contract: Mapping[str, Any]) -> dict[str, Any]:
    manifest_boundary = _mapping(_mapping(contract["manifest_contract"])["validity_boundary"])
    return {
        "contract_ref": str(contract["contract_ref"]),
        "contract_id": str(contract["contract_id"]),
        "version": int(contract["version"]),
        "progress_basis": _string_list(_mapping(contract["progress_model"])["precedence"]),
        "manifest_validity_is_semantic_receipt_validity": bool(
            manifest_boundary["manifest_validity_is_semantic_receipt_validity"]
        ),
        "controller_read_model_currentness_role": str(
            _mapping(contract["controller_read_model_currentness"])["role"]
        ),
    }


def promotion_protocol_steps(contract: Mapping[str, Any]) -> list[str]:
    return _string_list(_mapping(contract["promotion_protocol"])["ordered_steps"])


def consumability_gate_projection(contract: Mapping[str, Any]) -> dict[str, Any]:
    gate = _mapping(contract["consumability_gate"])
    return {
        "contract_ref": f"{CONTRACT_REF}#/consumability_gate",
        "required_checks": _string_list(gate["required_checks"]),
        "checks": _checks(gate["checks"]),
        "body_included": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_readiness": False,
        "can_write_mas_truth": False,
    }


def current_pointer_contract_projection(contract: Mapping[str, Any]) -> dict[str, Any]:
    current_pointer = _mapping(contract["current_pointer"])
    return {
        "contract_ref": f"{CONTRACT_REF}#/current_pointer",
        "promotion_requires": _string_list(current_pointer["promotion_requires"]),
        "promotion_state_values": _string_list(current_pointer["promotion_state_values"]),
        "projection_rebuild_required_after_promotion": bool(
            current_pointer["projection_rebuild_required_after_promotion"]
        ),
    }


def find_opl_artifact_operating_contract_path(*, start: Path | None = None) -> Path | None:
    search_roots: list[Path] = []
    if start is not None:
        search_roots.append(start.expanduser().resolve())
    search_roots.append(Path(__file__).resolve())
    for root in search_roots:
        for candidate_root in (root, *root.parents):
            candidate = candidate_root / CONTRACT_REF
            if candidate.is_file():
                return candidate
    return None


def _validate_contract(contract: Mapping[str, Any]) -> None:
    if contract.get("surface_kind") != "opl_artifact_operating_contract":
        raise ValueError(f"{CONTRACT_REF} surface_kind must be opl_artifact_operating_contract")
    if contract.get("contract_id") != CONTRACT_ID:
        raise ValueError(f"{CONTRACT_REF} contract_id must be {CONTRACT_ID}")
    if contract.get("contract_ref") != CONTRACT_REF:
        raise ValueError(f"{CONTRACT_REF} contract_ref must match repo path")
    operating = operating_contract_projection(contract)
    if operating["progress_basis"] != [
        "current_pointer",
        "accepted_receipt",
        "valid_manifest",
        "existing_artifacts",
    ]:
        raise ValueError(f"{CONTRACT_REF} progress precedence changed unexpectedly")
    if operating["manifest_validity_is_semantic_receipt_validity"] is not False:
        raise ValueError(f"{CONTRACT_REF} must keep manifest validity separate from receipt validity")
    if operating["controller_read_model_currentness_role"] != "repair_projection_diagnostic_only":
        raise ValueError(f"{CONTRACT_REF} must keep controller/read-model/currentness diagnostic-only")
    if promotion_protocol_steps(contract) != [
        "attempt_output",
        "manifest_valid",
        "receipt_accepted",
        "current_pointer_promoted",
        "projection_rebuilt",
    ]:
        raise ValueError(f"{CONTRACT_REF} promotion protocol changed unexpectedly")
    expected_checks = [
        "role",
        "hash",
        "source",
        "current_truth",
        "receipt_authority",
        "lineage",
        "retention_restore",
        "domain_validation",
    ]
    if consumability_gate_projection(contract)["required_checks"] != expected_checks:
        raise ValueError(f"{CONTRACT_REF} consumability gate changed unexpectedly")


def _mapping(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{CONTRACT_REF} expected a JSON object")
    return dict(value)


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise ValueError(f"{CONTRACT_REF} expected a list of non-empty strings")
    return list(value)


def _checks(value: Any) -> dict[str, dict[str, Any]]:
    checks = _mapping(value)
    return {str(key): _mapping(item) for key, item in checks.items()}


__all__ = [
    "CONTRACT_ID",
    "CONTRACT_REF",
    "consumability_gate_projection",
    "current_pointer_contract_projection",
    "find_opl_artifact_operating_contract_path",
    "load_opl_artifact_operating_contract",
    "operating_contract_projection",
    "promotion_protocol_steps",
]
