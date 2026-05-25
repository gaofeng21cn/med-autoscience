from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from typing import Any


FAMILY_TRANSITION_SPEC_VERSION = "family-transition-runner.v1"
FAMILY_TRANSITION_TARGET_DOMAIN_ID = "medautoscience"
FAMILY_TRANSITION_OWNER = "med-autoscience"


def build_family_transition_spec(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    normalized_rows = [dict(row) for row in rows]
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in normalized_rows:
        grouped.setdefault(_transition_key(row), []).append(row)
    guards: dict[str, dict[str, Any]] = {}
    transitions: list[dict[str, Any]] = []
    for key, group in sorted(grouped.items()):
        representative = group[0]
        guard_id = _guard_id(key)
        source_refs = _unique_texts(ref for row in group for ref in row.get("source_refs") or [])
        guard_boundary = _mapping(representative.get("guard_boundary"))
        guards[guard_id] = {
            "description": f"MAS owner surfaces matched transition `{key}`.",
            "owner": _text(representative.get("owner")) or FAMILY_TRANSITION_OWNER,
            "source_ref": source_refs[0] if source_refs else None,
            "authority_boundary": {
                **dict(guard_boundary),
                "domain_transition_owner": "MedAutoScience",
                "can_write_domain_truth": False,
            },
        }
        transition = {
            "transition_id": f"mas-transition-{key}",
            "current_state": _current_state(key),
            "event": "domain_tick",
            "required_guards": [guard_id],
            "next_state": f"mas_route:{_text(representative.get('route_target')) or 'inspect'}",
            "next_work_unit": _family_work_unit(representative),
            "owner_route": _family_owner_route(representative),
            "receipt": {
                "receipt_refs": [
                    _receipt_ref(row)
                    for row in group
                    if _text(row.get("study_id"))
                ],
                "metadata": {"source_refs": source_refs},
            },
            "projection": {
                "route_node_refs": [
                    f"mas-route-node:{_text(representative.get('route_target')) or 'inspect'}",
                    f"mas-work-unit:{key}",
                ],
                "decision_type": _text(representative.get("decision_type")) or "unknown",
                "source_refs": source_refs,
                "domain_ready_verdict_owner": "med-autoscience",
            },
            "authority_boundary": {
                "domain_transition_owner": "MedAutoScience",
                "can_write_domain_truth": False,
                "can_execute_domain_action": False,
                "opl_interprets_domain_quality": False,
            },
        }
        receipt_consumption = _mapping(representative.get("completion_receipt_consumption"))
        if receipt_consumption:
            transition["receipt"]["completion_receipt_consumption"] = dict(receipt_consumption)
        typed_blocker = _family_typed_blocker(representative)
        if typed_blocker is not None:
            transition["typed_blocker"] = typed_blocker
        human_gate = _family_human_gate(representative)
        if human_gate is not None:
            transition["human_gate"] = human_gate
        transitions.append(transition)
    return {
        "surface_kind": "family_transition_spec",
        "version": FAMILY_TRANSITION_SPEC_VERSION,
        "spec_id": "mas-domain-transition-spec.v1",
        "target_domain_id": FAMILY_TRANSITION_TARGET_DOMAIN_ID,
        "owner": FAMILY_TRANSITION_OWNER,
        "authority_boundary": {
            "opl": "transition_runner_transport_projection_only",
            "domain": "truth_quality_artifact_gate_owner",
            "domain_transition_owner": "MedAutoScience",
            "domain_ready_verdict_owner": "med-autoscience",
            "artifact_authority_owner": "med-autoscience",
            "opl_interprets_domain_quality": False,
            "opl_executes_domain_action": False,
            "opl_writes_domain_truth": False,
        },
        "guards": guards,
        "transitions": transitions,
    }


def build_family_transition_matrix_cases(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for row in rows:
        row_payload = dict(row)
        study_id = _text(row_payload.get("study_id"))
        if not study_id:
            continue
        key = _transition_key(row_payload)
        source_ref = _first_source_ref(row_payload)
        context = {"receipt_ref": _receipt_ref(row_payload)}
        if source_ref:
            context = {"source_ref": source_ref, **context}
        receipt_consumption = _mapping(row_payload.get("completion_receipt_consumption"))
        if receipt_consumption:
            context["completion_receipt_consumption"] = dict(receipt_consumption)
        expected = {
            "decision_type": _text(row_payload.get("decision_type")) or "unknown",
            "route_target": _text(row_payload.get("route_target")) or "inspect",
            "next_work_unit_id": _text(_mapping(row_payload.get("next_work_unit")).get("unit_id")),
            "controller_action": _text(row_payload.get("controller_action")) or "none",
            "owner": _text(row_payload.get("owner")) or FAMILY_TRANSITION_OWNER,
        }
        cases.append(
            {
                "case_id": f"{study_id}:{key}",
                "domain_id": FAMILY_TRANSITION_TARGET_DOMAIN_ID,
                "current_state": _current_state(key),
                "event": "domain_tick",
                "guards": {_guard_id(key): True},
                "context": context,
                "expected": expected,
            }
        )
    return cases


def build_family_transition_spec_descriptor() -> dict[str, Any]:
    return {
        "surface_kind": "family_transition_spec_descriptor",
        "target_domain_id": FAMILY_TRANSITION_TARGET_DOMAIN_ID,
        "spec_surface_kind": "family_transition_spec",
        "contract_version": FAMILY_TRANSITION_SPEC_VERSION,
        "refresh_policy": "rebuild_study_state_matrix_before_opl_runner",
        "materialized_surfaces": {
            "study_state_matrix": [
                "domain_transition_table.family_transition_spec",
                "domain_transition_table.family_transition_matrix_cases",
            ],
            "domain_handler_export": ["family_transition_spec_descriptor"],
            "product_entry_manifest": ["family_transition_spec_descriptor"],
        },
        "authority_boundary": {
            "runner_owner": "OPL Framework",
            "domain_transition_owner": "MedAutoScience",
            "can_write_domain_truth": False,
            "opl_interprets_domain_quality": False,
            "opl_executes_domain_action": False,
        },
        "locator_refs": {
            "study_state_matrix_spec": "/study_state_matrix/domain_transition_table/family_transition_spec",
            "study_state_matrix_cases": "/study_state_matrix/domain_transition_table/family_transition_matrix_cases",
            "domain_handler_export_descriptor": "/mas_family_domain_handler_export/family_transition_spec_descriptor",
            "product_entry_manifest_descriptor": "/product_entry_manifest/family_transition_spec_descriptor",
        },
        "source_refs": {
            "study_state_matrix_domain_transition_table": "/study_state_matrix/domain_transition_table",
            "domain_handler_export_descriptor": "/mas_family_domain_handler_export/family_transition_spec_descriptor",
            "product_entry_manifest_descriptor": "/product_entry_manifest/family_transition_spec_descriptor",
        },
    }


def _transition_key(row: Mapping[str, Any]) -> str:
    unit = _mapping(row.get("next_work_unit"))
    return _slug(_text(unit.get("unit_id")) or _text(row.get("decision_type")) or "unclassified")


def _slug(value: str) -> str:
    text = re.sub(r"[^A-Za-z0-9]+", "_", value.strip()).strip("_").lower()
    return text or "unclassified"


def _current_state(key: str) -> str:
    return f"mas_domain_transition:{key}"


def _guard_id(key: str) -> str:
    return f"mas_guard_{key}"


def _first_source_ref(row: Mapping[str, Any]) -> str | None:
    for ref in row.get("source_refs") or []:
        text = _text(ref)
        if text:
            return text
    return None


def _receipt_ref(row: Mapping[str, Any]) -> str:
    return f"mas-domain-transition:{_text(row.get('study_id'))}:{_transition_key(row)}"


def _unique_texts(values: Iterable[object]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = _text(value)
        if text and text not in seen:
            seen.add(text)
            result.append(text)
    return result


def _family_work_unit(row: Mapping[str, Any]) -> dict[str, Any]:
    unit = _mapping(row.get("next_work_unit"))
    unit_id = _transition_key(row)
    action = _text(row.get("controller_action")) or "none"
    return {
        "work_unit_ref": f"mas-work-unit:{unit_id}",
        "action_refs": [f"mas-controller-action:{action}"],
        "metadata": {
            "unit_id": _text(unit.get("unit_id")) or unit_id,
            "lane": _text(unit.get("lane")),
            "summary": _text(unit.get("summary")),
            "controller_action": action,
            "decision_type": _text(row.get("decision_type")) or "unknown",
        },
    }


def _family_owner_route(row: Mapping[str, Any]) -> dict[str, Any]:
    owner = _text(row.get("owner")) or FAMILY_TRANSITION_OWNER
    route_target = _text(row.get("route_target")) or "inspect"
    controller_action = _text(row.get("controller_action"))
    payload: dict[str, Any] = {
        "owner": owner,
        "route_ref": f"mas-route:{route_target}",
        "metadata": {
            "route_target": route_target,
            "controller_action": controller_action,
        },
    }
    if controller_action:
        payload["action_refs"] = [f"mas-controller-action:{controller_action}"]
    return payload


def _family_typed_blocker(row: Mapping[str, Any]) -> dict[str, Any] | None:
    blocker = _mapping(row.get("typed_blocker"))
    blocker_id = _text(blocker.get("blocker_id"))
    if not blocker_id:
        return None
    refs = []
    if required_surface := _text(blocker.get("required_owner_surface")):
        refs.append(required_surface)
    return {
        "blocker_code": blocker_id,
        "owner": _text(row.get("owner")) or FAMILY_TRANSITION_OWNER,
        "refs": refs,
        "metadata": {
            "blocker_type": _text(blocker.get("blocker_type")),
            "summary": _text(blocker.get("summary")),
            "write_permitted": blocker.get("write_permitted") is True,
        },
    }


def _family_human_gate(row: Mapping[str, Any]) -> dict[str, Any] | None:
    if _text(row.get("decision_type")) != "human_gate":
        return None
    key = _transition_key(row)
    return {
        "gate_ref": f"mas-human-gate:{key}",
        "owner": "human_gate",
        "reason": _text(_mapping(row.get("typed_blocker")).get("summary")) or "mas_human_gate_required",
        "resume_refs": [_receipt_ref(row)],
    }


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = [
    "build_family_transition_matrix_cases",
    "build_family_transition_spec",
    "build_family_transition_spec_descriptor",
]
