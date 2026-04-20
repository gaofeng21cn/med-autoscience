from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Any

import yaml

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
REQUIRED_EVIDENCE_REVIEW_LIST_FIELDS = (
    "minimum_proof_package",
    "reviewer_first_checks",
    "claim_evidence_consistency_requirements",
    "route_back_policy",
)
REQUIRED_CANONICAL_ROUTE_IDS = (
    "scout",
    "baseline",
    "analysis-campaign",
    "write",
    "finalize",
    "decision",
)


@dataclass(frozen=True)
class EntryMode:
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


def load_entry_modes_payload(path: Path | None = None) -> dict[str, object]:
    resolved_path = path.expanduser().resolve() if path is not None else None
    if resolved_path is not None:
        raw_text = resolved_path.read_text(encoding="utf-8")
    else:
        raw_text = files("med_autoscience.agent_entry.resources").joinpath("agent_entry_modes.yaml").read_text(
            encoding="utf-8"
        )
    payload = yaml.safe_load(raw_text)
    if not isinstance(payload, dict):
        raise ValueError("entry mode payload must be a mapping")
    _validate_payload_contract(payload)
    return payload


def load_entry_modes() -> tuple[EntryMode, ...]:
    payload = load_entry_modes_payload()
    _validate_payload_contract(payload)
    compatible_agents = _string_tuple(payload["compatible_agents"], "compatible_agents")
    modes_payload = payload["modes"]
    if not isinstance(modes_payload, list):
        raise ValueError("modes must be a list")

    modes: list[EntryMode] = []
    for item in modes_payload:
        if not isinstance(item, dict):
            raise ValueError("each mode must be a mapping")
        modes.append(
            EntryMode(
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
    route_contracts = _route_contract_payload_map(payload.get("route_contracts"))
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
