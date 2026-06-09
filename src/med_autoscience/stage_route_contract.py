from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Any

import yaml

STAGE_ROUTE_CONTRACT_REF = "agent/stages/stage_route_contract.yaml"
PACKAGED_STAGE_ROUTE_CONTRACT_RESOURCE = "stage_route_contract.yaml"

REQUIRED_MODE_LIST_FIELDS = (
    "preconditions",
    "managed_entry_actions",
    "lightweight_routes",
    "managed_routes",
    "startup_boundary_gated_routes",
    "governance_routes",
    "auxiliary_routes",
    "upgrade_triggers",
)
MODE_ROUTE_LIST_FIELDS = (
    "lightweight_routes",
    "managed_routes",
    "startup_boundary_gated_routes",
    "governance_routes",
    "auxiliary_routes",
)
REQUIRED_MODE_STRING_FIELDS = (
    "mode_id",
    "display_name",
    "default_runtime_mode",
    "lightweight_scope",
)
REQUIRED_ROUTE_CONTRACT_STRING_FIELDS = (
    "route_id",
    "display_name",
    "key_question",
    "goal",
)
REQUIRED_ROUTE_CONTRACT_LIST_FIELDS = (
    "enter_conditions",
    "hard_success_gate",
    "durable_outputs_minimum",
    "human_gate_boundary",
    "next_routes",
    "route_back_triggers",
)
OPTIONAL_ROUTE_CONTRACT_LIST_FIELDS = (
    "knowledge_input_obligations",
    "memory_closeout_obligations",
)
ROUTE_OBLIGATION_FIELDS = OPTIONAL_ROUTE_CONTRACT_LIST_FIELDS
REQUIRED_EVIDENCE_REVIEW_LIST_FIELDS = (
    "minimum_proof_package",
    "reviewer_first_checks",
    "claim_evidence_consistency_requirements",
    "route_back_policy",
)
REQUIRED_SPRINT_CONTRACT_STRING_FIELDS = (
    "sprint_id",
    "objective",
)
REQUIRED_SPRINT_CONTRACT_LIST_FIELDS = (
    "covered_work_units",
    "covered_routes",
    "attempt_scope",
    "control_plane_outputs",
    "forbidden_control_plane_outputs",
    "admission_order",
    "quality_gate_policy",
    "currentness_followthrough_policy",
    "authority_boundary",
)
REQUIRED_SPRINT_CONTRACT_STRING_POLICY_FIELDS = (
    "gate_before_delta_policy",
)
REQUIRED_CANONICAL_ROUTE_IDS = (
    "scout",
    "baseline",
    "analysis-campaign",
    "write",
    "review",
    "finalize",
    "decision",
)
PROGRESS_FIRST_SPRINT_CONTRACT_FIELD = "late_stage_progress_sprint_contract"
PROGRESS_FIRST_SPRINT_ID = "publishability_repair_sprint"
PROGRESS_FIRST_SPRINT_WORK_UNIT = "current_manuscript_prose_currentness_and_gate_replay_write_closeout"
ORDINARY_PROGRESS_HANDOFF_POLICY_FIELD = "ordinary_progress_handoff_policy"


@dataclass(frozen=True)
class StageEntryMode:
    mode_id: str
    display_name: str
    default_runtime_mode: str
    compatible_agents: tuple[str, ...]
    preconditions: tuple[str, ...]
    lightweight_scope: str
    managed_entry_actions: tuple[str, ...]
    lightweight_routes: tuple[str, ...]
    managed_routes: tuple[str, ...]
    startup_boundary_gated_routes: tuple[str, ...]
    governance_routes: tuple[str, ...]
    auxiliary_routes: tuple[str, ...]
    upgrade_triggers: tuple[str, ...]


def load_stage_route_contract_payload(path: Path | None = None) -> dict[str, object]:
    resolved_path = path.expanduser().resolve() if path is not None else None
    if resolved_path is not None:
        raw_text = resolved_path.read_text(encoding="utf-8")
    else:
        raw_text = _read_canonical_stage_route_contract_text()
    payload = yaml.safe_load(raw_text)
    if not isinstance(payload, dict):
        raise ValueError("stage route contract payload must be a mapping")
    _validate_payload_contract(payload)
    return payload


def load_stage_route_contract(path: Path | None = None) -> tuple[StageEntryMode, ...]:
    return stage_entry_modes_from_payload(load_stage_route_contract_payload(path=path))


def late_stage_progress_sprint_contract_from_payload(payload: dict[str, object]) -> dict[str, Any]:
    _validate_payload_contract(payload)
    contract = payload[PROGRESS_FIRST_SPRINT_CONTRACT_FIELD]
    if not isinstance(contract, dict):
        raise ValueError(f"{PROGRESS_FIRST_SPRINT_CONTRACT_FIELD} must be a mapping")
    return dict(contract)


def route_obligations_descriptor(path: Path | None = None) -> dict[str, Any]:
    return route_obligations_descriptor_from_payload(load_stage_route_contract_payload(path=path))


def route_obligations_descriptor_from_payload(payload: dict[str, object]) -> dict[str, Any]:
    _validate_payload_contract(payload)
    route_contracts = _route_contract_payload_map(payload.get("route_contracts"))
    routes: dict[str, dict[str, Any]] = {}
    missing_route_fields: dict[str, list[str]] = {}

    for route_id, route_payload in route_contracts.items():
        route_missing_fields: list[str] = []
        route_descriptor: dict[str, Any] = {
            "route_id": route_id,
            "source_ref": f"{STAGE_ROUTE_CONTRACT_REF}#/route_contracts/{route_id}",
        }
        for field in ROUTE_OBLIGATION_FIELDS:
            obligation_descriptor = _route_obligation_field_descriptor(
                route_id=route_id,
                field=field,
                route_payload=route_payload,
            )
            route_descriptor[field] = obligation_descriptor
            if obligation_descriptor["status"] == "missing":
                route_missing_fields.append(field)
        route_descriptor["status"] = "missing" if route_missing_fields else "present"
        route_descriptor["handoff_readiness"] = {
            "status": route_descriptor["status"],
            "missing_fields": route_missing_fields,
            "blocker": None,
        }
        route_descriptor["authority_boundary"] = _route_obligation_authority_boundary()
        if route_missing_fields:
            missing_route_fields[route_id] = route_missing_fields
        routes[route_id] = route_descriptor

    return {
        "surface_kind": "stage_route_obligations_descriptor",
        "schema_version": 1,
        "contract_ref": STAGE_ROUTE_CONTRACT_REF,
        "route_count": len(routes),
        "status": "missing" if missing_route_fields else "present",
        "missing_route_fields": missing_route_fields,
        "blockers": [],
        "routes": routes,
        "authority_boundary": _route_obligation_authority_boundary(),
    }


def route_obligation_descriptors_from_payload(payload: dict[str, object]) -> dict[str, Any]:
    return route_obligations_descriptor_from_payload(payload)


def stage_entry_modes_from_payload(payload: dict[str, object]) -> tuple[StageEntryMode, ...]:
    _validate_payload_contract(payload)
    compatible_agents = _string_tuple(payload["compatible_agents"], "compatible_agents")
    modes_payload = payload["modes"]
    if not isinstance(modes_payload, list):
        raise ValueError("modes must be a list")

    modes: list[StageEntryMode] = []
    for item in modes_payload:
        if not isinstance(item, dict):
            raise ValueError("each mode must be a mapping")
        modes.append(
            StageEntryMode(
                mode_id=_string_value(item, "mode_id"),
                display_name=_string_value(item, "display_name"),
                default_runtime_mode=_string_value(item, "default_runtime_mode"),
                compatible_agents=compatible_agents,
                preconditions=_string_tuple(item["preconditions"], "preconditions"),
                lightweight_scope=_string_value(item, "lightweight_scope"),
                managed_entry_actions=_string_tuple(item["managed_entry_actions"], "managed_entry_actions"),
                lightweight_routes=_string_tuple(item["lightweight_routes"], "lightweight_routes"),
                managed_routes=_string_tuple(item["managed_routes"], "managed_routes"),
                startup_boundary_gated_routes=_string_tuple(
                    item["startup_boundary_gated_routes"],
                    "startup_boundary_gated_routes",
                ),
                governance_routes=_string_tuple(item["governance_routes"], "governance_routes"),
                auxiliary_routes=_string_tuple(item["auxiliary_routes"], "auxiliary_routes"),
                upgrade_triggers=_string_tuple(item["upgrade_triggers"], "upgrade_triggers"),
            )
        )
    return tuple(modes)


def _route_obligation_field_descriptor(
    *,
    route_id: str,
    field: str,
    route_payload: dict[str, Any],
) -> dict[str, Any]:
    source_ref = f"{STAGE_ROUTE_CONTRACT_REF}#/route_contracts/{route_id}/{field}"
    if field not in route_payload:
        return {
            "status": "missing",
            "items": [],
            "item_descriptors": [],
            "source_ref": source_ref,
            "blocker": None,
        }
    items = _string_tuple(route_payload[field], field)
    return {
        "status": "present",
        "items": list(items),
        "item_descriptors": [
            {
                "id": item,
                "status": "present",
                "source_ref": f"{source_ref}/{index}",
                "blocker": None,
            }
            for index, item in enumerate(items)
        ],
        "source_ref": source_ref,
        "blocker": None,
    }


def _route_obligation_authority_boundary() -> dict[str, bool]:
    return {
        "descriptor_only": True,
        "can_write_domain_truth": False,
        "can_authorize_publication_quality": False,
        "can_authorize_submission_readiness": False,
    }


def _read_canonical_stage_route_contract_text() -> str:
    source_path = find_stage_route_contract_path()
    if source_path is not None:
        return source_path.read_text(encoding="utf-8")
    return files("med_autoscience.resources").joinpath(PACKAGED_STAGE_ROUTE_CONTRACT_RESOURCE).read_text(
        encoding="utf-8"
    )


def find_stage_route_contract_path(*, start: Path | None = None) -> Path | None:
    """Return the repo-tracked canonical route contract path when running from source."""
    search_roots: list[Path] = []
    if start is not None:
        search_roots.append(start.expanduser().resolve())
    search_roots.append(Path(__file__).resolve())

    for root in search_roots:
        for candidate_root in (root, *root.parents):
            candidate = candidate_root / STAGE_ROUTE_CONTRACT_REF
            if candidate.is_file():
                return candidate
    return None


def _string_value(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string")
    return value


def _string_tuple(value: object, field: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list")
    if not all(isinstance(item, str) for item in value):
        raise ValueError(f"{field} must contain only strings")
    return tuple(value)


def _validate_payload_contract(payload: dict[str, Any]) -> None:
    _string_tuple(payload.get("compatible_agents"), "compatible_agents")
    _validate_ordinary_progress_handoff_policy(payload.get(ORDINARY_PROGRESS_HANDOFF_POLICY_FIELD))
    route_contracts = _route_contract_payload_map(payload.get("route_contracts"))
    _validate_late_stage_progress_sprint_contract(
        payload.get(PROGRESS_FIRST_SPRINT_CONTRACT_FIELD),
        route_contracts=route_contracts,
    )
    evidence_review_contract = payload.get("evidence_review_contract")
    if not isinstance(evidence_review_contract, dict):
        raise ValueError("evidence_review_contract must be a mapping")
    for field in REQUIRED_EVIDENCE_REVIEW_LIST_FIELDS:
        if field not in evidence_review_contract:
            raise ValueError(f"evidence_review_contract missing required field: {field}")
        _string_tuple(evidence_review_contract[field], field)

    known_route_ids = set(route_contracts)
    modes_payload = payload.get("modes")
    if not isinstance(modes_payload, list):
        raise ValueError("modes must be a list")

    for index, mode_payload in enumerate(modes_payload):
        if not isinstance(mode_payload, dict):
            raise ValueError("each mode must be a mapping")
        mode_label = _mode_label(mode_payload, index)
        if "compatible_agents" in mode_payload:
            raise ValueError(f"{mode_label} must not override compatible_agents")
        for field in REQUIRED_MODE_STRING_FIELDS:
            if field not in mode_payload:
                raise ValueError(f"{mode_label} missing required field: {field}")
            _string_value(mode_payload, field)
        for field in REQUIRED_MODE_LIST_FIELDS:
            if field not in mode_payload:
                raise ValueError(f"{mode_label} missing required field: {field}")
            values = _string_tuple(mode_payload[field], field)
            if field not in MODE_ROUTE_LIST_FIELDS:
                continue
            unknown_routes = sorted(set(values) - known_route_ids)
            if unknown_routes:
                raise ValueError(f"{mode_label} references unknown route ids in {field}: {', '.join(unknown_routes)}")


def _validate_ordinary_progress_handoff_policy(value: object) -> None:
    field = ORDINARY_PROGRESS_HANDOFF_POLICY_FIELD
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be a mapping")
    for string_field in (
        "source_ref",
        "default_progress_root",
        "stage_goal_source",
        "executor_output_requirement",
    ):
        if string_field not in value:
            raise ValueError(f"{field} missing required field: {string_field}")
        _non_empty_string_value(value, string_field, field)
    for list_field in ("accepted_closeout_shapes",):
        if list_field not in value:
            raise ValueError(f"{field} missing required field: {list_field}")
        _string_tuple(value[list_field], list_field)

    progress_delta_receipt = value.get("progress_delta_receipt")
    if not isinstance(progress_delta_receipt, dict):
        raise ValueError(f"{field}.progress_delta_receipt must be a mapping")
    for string_field in ("receipt_kind", "artifact_tier", "role"):
        if string_field not in progress_delta_receipt:
            raise ValueError(f"{field}.progress_delta_receipt missing required field: {string_field}")
        _non_empty_string_value(progress_delta_receipt, string_field, f"{field}.progress_delta_receipt")
    for list_field in ("required_fields", "cannot_authorize"):
        if list_field not in progress_delta_receipt:
            raise ValueError(f"{field}.progress_delta_receipt missing required field: {list_field}")
        _string_tuple(progress_delta_receipt[list_field], list_field)

    artifact_tier_policy = value.get("artifact_tier_policy")
    if not isinstance(artifact_tier_policy, dict):
        raise ValueError(f"{field}.artifact_tier_policy must be a mapping")
    _string_tuple(artifact_tier_policy.get("tiers"), "tiers")
    _non_empty_string_value(artifact_tier_policy, "default_tier", f"{field}.artifact_tier_policy")
    _string_tuple(
        artifact_tier_policy.get("delivery_or_publication_claim_requires_tier"),
        "delivery_or_publication_claim_requires_tier",
    )
    if not isinstance(artifact_tier_policy.get("ordinary_delta_requires_full_stage_artifact_manifest"), bool):
        raise ValueError(
            f"{field}.artifact_tier_policy ordinary_delta_requires_full_stage_artifact_manifest must be a bool"
        )

    readiness_jit_policy = value.get("readiness_jit_policy")
    if not isinstance(readiness_jit_policy, dict):
        raise ValueError(f"{field}.readiness_jit_policy must be a mapping")
    for string_field in (
        "default_mode",
        "check_scope_source",
        "full_readiness_inventory_role",
        "ordinary_progress_blocking_policy",
    ):
        _non_empty_string_value(readiness_jit_policy, string_field, f"{field}.readiness_jit_policy")
    if not isinstance(readiness_jit_policy.get("cannot_require_all_surfaces_before_writing_analysis_or_review_delta"), bool):
        raise ValueError(
            f"{field}.readiness_jit_policy cannot_require_all_surfaces_before_writing_analysis_or_review_delta must be a bool"
        )

    audit_sidecar_policy = value.get("audit_sidecar_policy")
    if not isinstance(audit_sidecar_policy, dict):
        raise ValueError(f"{field}.audit_sidecar_policy must be a mapping")
    _non_empty_string_value(audit_sidecar_policy, "role", f"{field}.audit_sidecar_policy")
    for bool_field in ("can_generate_default_next_action", "can_close_stage", "can_claim_domain_ready"):
        if not isinstance(audit_sidecar_policy.get(bool_field), bool):
            raise ValueError(f"{field}.audit_sidecar_policy {bool_field} must be a bool")


def _validate_late_stage_progress_sprint_contract(
    value: object,
    *,
    route_contracts: dict[str, dict[str, Any]],
) -> None:
    field = PROGRESS_FIRST_SPRINT_CONTRACT_FIELD
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be a mapping")
    for string_field in REQUIRED_SPRINT_CONTRACT_STRING_FIELDS:
        if string_field not in value:
            raise ValueError(f"{field} missing required field: {string_field}")
        _non_empty_string_value(value, string_field, field)
    for string_field in REQUIRED_SPRINT_CONTRACT_STRING_POLICY_FIELDS:
        if string_field not in value:
            raise ValueError(f"{field} missing required field: {string_field}")
        _non_empty_string_value(value, string_field, field)
    for list_field in REQUIRED_SPRINT_CONTRACT_LIST_FIELDS:
        if list_field not in value:
            raise ValueError(f"{field} missing required field: {list_field}")
        values = _string_tuple(value[list_field], list_field)
        if list_field == "covered_routes":
            unknown_routes = sorted(set(values) - set(route_contracts))
            if unknown_routes:
                raise ValueError(f"{field} references unknown route ids in covered_routes: {', '.join(unknown_routes)}")
    if value["sprint_id"] != PROGRESS_FIRST_SPRINT_ID:
        raise ValueError(f"{field}.sprint_id must be {PROGRESS_FIRST_SPRINT_ID}")
    covered_work_units = _string_tuple(value["covered_work_units"], "covered_work_units")
    if PROGRESS_FIRST_SPRINT_WORK_UNIT not in covered_work_units:
        raise ValueError(
            f"{field}.covered_work_units must include {PROGRESS_FIRST_SPRINT_WORK_UNIT}"
        )
    covered_routes = set(_string_tuple(value["covered_routes"], "covered_routes"))
    required_routes = {"write", "review", "finalize"}
    missing_routes = sorted(required_routes - covered_routes)
    if missing_routes:
        raise ValueError(f"{field}.covered_routes missing required route ids: {', '.join(missing_routes)}")


def _mode_label(payload: dict[str, Any], index: int) -> str:
    mode_id = payload.get("mode_id")
    if isinstance(mode_id, str) and mode_id:
        return f"mode[{mode_id}]"
    return f"mode[index={index}]"


def _route_contract_payload_map(value: object) -> dict[str, dict[str, Any]]:
    if not isinstance(value, dict):
        raise ValueError("route_contracts must be a mapping")

    route_contracts: dict[str, dict[str, Any]] = {}
    for route_id, route_payload in value.items():
        if not isinstance(route_id, str) or not route_id:
            raise ValueError("route_contracts keys must be non-empty strings")
        if not isinstance(route_payload, dict):
            raise ValueError(f"route_contracts[{route_id}] must be a mapping")
        for field in REQUIRED_ROUTE_CONTRACT_STRING_FIELDS:
            if field not in route_payload:
                raise ValueError(f"route_contracts[{route_id}] missing required field: {field}")
            if field == "key_question":
                _non_empty_string_value(route_payload, field, f"route_contracts[{route_id}]")
            else:
                _string_value(route_payload, field)
        for field in REQUIRED_ROUTE_CONTRACT_LIST_FIELDS:
            if field not in route_payload:
                raise ValueError(f"route_contracts[{route_id}] missing required field: {field}")
            _string_tuple(route_payload[field], field)
        for field in OPTIONAL_ROUTE_CONTRACT_LIST_FIELDS:
            if field in route_payload:
                _string_tuple(route_payload[field], field)
        declared_route_id = route_payload.get("route_id")
        if declared_route_id != route_id:
            raise ValueError(f"route_contracts[{route_id}] route_id must equal mapping key")
        route_contracts[route_id] = route_payload

    missing_route_ids = [route_id for route_id in REQUIRED_CANONICAL_ROUTE_IDS if route_id not in route_contracts]
    if missing_route_ids:
        raise ValueError(f"route_contracts missing required route ids: {', '.join(missing_route_ids)}")
    return route_contracts


def _non_empty_string_value(payload: dict[str, Any], key: str, label: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} {key} must be a non-empty string")
    return value
