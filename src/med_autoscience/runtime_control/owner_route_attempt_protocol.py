from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from med_autoscience.controllers.owner_callable_closeout_contract import (
    owner_callable_typed_closeout_contract,
)
from med_autoscience.controllers.owner_callable_action_policy import owner_callable_search_discipline
from med_autoscience.controllers import paper_progress_transition_refs
from med_autoscience.runtime_control.owner_route_attempt_reasons import (
    DEFAULT_FORBIDDEN_SURFACES,
    _REASON_REGISTRY,
)


PROTOCOL_VERSION = "mas-owner-route-attempt-protocol.v1"
ROUTE_TO_ATTEMPT_CONTRACT = {
    "surface_kind": "mas_route_to_attempt_contract",
    "version": "mas-route-to-attempt-contract.v1",
    "when_dispatchable": "materialize_running_provider_attempt_or_executable_owner_action_or_typed_blocker",
    "allowed_current_execution_state_kinds": [
        "running_provider_attempt",
        "executable_owner_action",
        "typed_blocker",
    ],
    "forbidden_idle_states": [
        "parked_without_human_gate",
        "quest_marked_running_but_no_live_session",
        "stale_handoff_only",
        "downstream_bundle_only_idle",
    ],
    "human_gate_exception_requires_typed_blocker": True,
}
PRIORITY_LATTICE = [
    "hard_methodology_or_source_blocker",
    "pending_ai_reviewer_request",
    "ai_reviewer_currentness",
    "write_route_back",
    "package_freshness",
    "delivery_or_human_handoff",
]

AUTHORITY_BOUNDARY = {
    "runtime_transport_ref": "opl-generated:family-runtime/current-control",
    "stage_run_ref_contract": "opl-generated:family-runtime/stage-run",
    "state_index_ref_contract": "opl-generated:state-index/source-ref",
    "transport_owner": "one-person-lab",
    "mas_can_write_runtime_transport": False,
    "mas_can_authorize_provider_admission": False,
}
RUNTIME_COMPLETION_GUARD = {
    "provider_completion_is_domain_completion": False,
    "provider_completion_is_stage_state": False,
    "running_worker_is_stage_state": False,
    "stage_state_owner": "one-person-lab",
    "domain_completion_owner": "med-autoscience",
    "domain_completion_requires": [
        "mas_owner_receipt_ref",
        "mas_typed_blocker_ref",
        "ai_reviewer_or_publication_gate_ref",
    ],
}
CURRENTNESS_BASIS_FIELDS = frozenset(
    {
        "source_eval_id",
        "source",
        "source_fingerprint",
        "work_unit_id",
        "work_unit_fingerprint",
        "truth_epoch",
        "runtime_health_epoch",
        "route_epoch",
        "action_fingerprint",
        "stage_attempt_id",
        "active_stage_attempt_id",
        "stage_run_id",
        "active_run_id",
        "attempt_idempotency_key",
        "route_identity_key",
        "idempotency_key",
        "derived_from_event_id",
        "observed_generation",
        "lineage_ref",
    }
)
CLOSEOUT_PREALLOCATED_REF_TEMPLATE = (
    "studies/{study_id}/artifacts/supervision/consumer/owner_callable_adapter_receipt/"
    "<stage_attempt_id>.closeout.json"
)
STAGE_OUTCOME_OPL_HANDOFF_TASK_KIND = "stage_outcome/opl-handoff"
CLOSEOUT_FIRST_TERMINAL_OUTCOMES = [
    "typed_blocker",
    "owner_receipt",
    "human_gate",
    "progress_delta",
]


def owner_reason_contract(
    *,
    reason: str | None,
    owner: str | None = None,
    action_type: str | None = None,
) -> dict[str, Any]:
    reason_text = _text(reason)
    entry = _REASON_REGISTRY.get(reason_text or "")
    if entry is None:
        return {
            "registered": False,
            "reason": reason_text,
            "owner": owner,
            "allowed_actions": [],
            "required_output": None,
            "forbidden_surfaces": list(DEFAULT_FORBIDDEN_SURFACES),
            "priority_class": None,
            "regression_refs": [],
        }
    resolved_owner = _resolve_owner(entry.get("owner"), owner=owner)
    allowed_actions = list(entry.get("allowed_actions") or [])
    if action_type and action_type not in allowed_actions and entry.get("allow_route_action") is True:
        allowed_actions.append(action_type)
    return {
        "registered": True,
        "reason": reason_text,
        "owner": resolved_owner,
        "allowed_actions": allowed_actions,
        "required_output": entry.get("required_output"),
        "forbidden_surfaces": list(entry.get("forbidden_surfaces") or DEFAULT_FORBIDDEN_SURFACES),
        "priority_class": entry.get("priority_class"),
        "regression_refs": list(entry.get("regression_refs") or []),
    }


def currentness_basis(owner_route: Mapping[str, Any]) -> dict[str, Any]:
    route = _mapping(owner_route)
    source_refs = _mapping(route.get("source_refs"))
    embedded_basis = _mapping(source_refs.get("owner_route_currentness_basis"))
    publication_eval_ref = _mapping(source_refs.get("publication_eval_ref")) or _mapping(route.get("publication_eval_ref"))
    return _compact_mapping(
        {
            "source_eval_id": source_refs.get("source_eval_id")
            or source_refs.get("publication_eval_id")
            or publication_eval_ref.get("eval_id")
            or route.get("source_eval_id")
            or route.get("publication_eval_id")
            or embedded_basis.get("source_eval_id"),
            "source": source_refs.get("current_owner_action_source")
            or source_refs.get("source")
            or route.get("source")
            or embedded_basis.get("source"),
            "source_fingerprint": route.get("source_fingerprint")
            or source_refs.get("source_fingerprint")
            or embedded_basis.get("source_fingerprint"),
            "work_unit_id": source_refs.get("work_unit_id")
            or route.get("work_unit_id")
            or embedded_basis.get("work_unit_id"),
            "work_unit_fingerprint": route.get("work_unit_fingerprint")
            or source_refs.get("work_unit_fingerprint")
            or embedded_basis.get("work_unit_fingerprint"),
            "action_fingerprint": route.get("action_fingerprint")
            or source_refs.get("action_fingerprint")
            or embedded_basis.get("action_fingerprint"),
            "truth_epoch": route.get("truth_epoch")
            or source_refs.get("study_truth_epoch")
            or embedded_basis.get("truth_epoch"),
            "runtime_health_epoch": route.get("runtime_health_epoch")
            or source_refs.get("runtime_health_epoch")
            or embedded_basis.get("runtime_health_epoch"),
        }
    )


def normalize_currentness_sources(*candidates: object) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for candidate in candidates:
        for source in _currentness_source_mappings(candidate):
            for key, value in source.items():
                if key in CURRENTNESS_BASIS_FIELDS and _text(value) is not None:
                    payload[key] = value
    return payload


def currentness_contract(owner_route: Mapping[str, Any]) -> dict[str, Any]:
    basis = currentness_basis(owner_route)
    required = [
        "work_unit_fingerprint",
        "truth_epoch",
        "runtime_health_epoch_or_source_eval_id",
    ]
    missing = [field for field in required if _currentness_required_field_missing(field, basis)]
    return {
        "status": "currentness_basis_required",
        "basis": basis,
        "required_fields": required,
        "missing_required_fields": missing,
        "fail_closed_when_missing": True,
    }


def decorate_owner_route(owner_route: Mapping[str, Any]) -> dict[str, Any]:
    route = dict(owner_route)
    if not route:
        return {}
    reason = _text(route.get("owner_reason")) or _text(route.get("failure_signature"))
    owner = _text(route.get("next_owner"))
    allowed_actions = [_text(action) for action in route.get("allowed_actions") or []]
    allowed_actions = [action for action in allowed_actions if action is not None]
    action_type = allowed_actions[0] if len(allowed_actions) == 1 else None
    reason_contract = owner_reason_contract(reason=reason, owner=owner, action_type=action_type)
    source_refs = dict(_mapping(route.get("source_refs")))
    trace_projection = paper_progress_transition_refs.decision_trace_projection(route, source_refs)
    route.update(trace_projection)
    source_refs = {
        **source_refs,
        **{
            key: list(route.get(key) or [])
            for key in (
                "decision_trace_refs",
                "failed_path_refs",
                "consumed_failed_path_refs",
            )
            if route.get(key)
        },
    }
    basis = currentness_basis(route)
    if basis:
        source_refs["owner_route_currentness_basis"] = basis
    route["source_refs"] = source_refs
    route["owner_reason_contract"] = reason_contract
    route["priority_lattice"] = list(PRIORITY_LATTICE)
    route["currentness_contract"] = currentness_contract(route)
    route["owner_route_attempt_protocol"] = {
        "version": PROTOCOL_VERSION,
        "dispatchable": bool(allowed_actions and not route["currentness_contract"]["missing_required_fields"]),
        "priority_class": reason_contract["priority_class"],
        "currentness_contract": route["currentness_contract"]["status"],
        "route_to_attempt_contract": _route_to_attempt_contract(),
        "authority_boundary": _authority_boundary(),
        "runtime_completion_guard": _runtime_completion_guard(),
        "completion_boundary": owner_callable_typed_closeout_contract(
            action_type=action_type or "domain_owner_action"
        )["completion_boundary"],
    }
    if route.get("decision_trace") or route.get("failed_path_ledger"):
        route["owner_route_attempt_protocol"]["decision_trace"] = {
            "decision_trace_refs": list(route.get("decision_trace_refs") or []),
            "failed_path_refs": list(route.get("failed_path_refs") or []),
            "consumed_failed_path_refs": list(route.get("consumed_failed_path_refs") or []),
            "body_included": False,
            "route_authority": False,
            "repeated_failed_path_suppressed": bool(route.get("repeated_failed_path_suppressed")),
        }
    return route


def owner_callable_attempt_envelope(
    *,
    dispatch: Mapping[str, Any],
) -> dict[str, Any]:
    prompt_contract = _mapping(dispatch.get("prompt_contract"))
    owner_route = _mapping(dispatch.get("owner_route")) or _mapping(prompt_contract.get("owner_route"))
    route = decorate_owner_route(owner_route)
    action_type = _text(dispatch.get("action_type")) or _text(prompt_contract.get("action_type"))
    domain_owner = (
        _text(dispatch.get("domain_owner"))
        or _text(dispatch.get("next_executable_owner"))
        or _text(prompt_contract.get("next_executable_owner"))
        or _text(route.get("next_owner"))
    )
    reason_contract = owner_reason_contract(
        reason=_text(route.get("owner_reason")) or _text(route.get("failure_signature")),
        owner=domain_owner,
        action_type=action_type,
    )
    basis = currentness_basis(route)
    required_closeout_packet = _required_closeout_packet(dispatch=dispatch, action_type=action_type)
    closeout_first_contract = _closeout_first_contract(
        dispatch=dispatch,
        route=route,
        required_closeout_packet=required_closeout_packet,
    )
    transport_closeout_packet = {
        **dict(required_closeout_packet),
        "preallocated_closeout_ref": closeout_first_contract["preallocated_closeout_ref"],
        "closeout_first_contract": closeout_first_contract,
    }
    completion_boundary = _completion_boundary(
        required_closeout_packet=required_closeout_packet,
        action_type=action_type,
    )
    domain_intent = _domain_intent(
        route=route,
        basis=basis,
        required_closeout_packet=transport_closeout_packet,
    )
    core_fields = {
        "domain_owner": domain_owner,
        "action_type": action_type,
        "work_unit_id": basis.get("work_unit_id"),
        "source_eval_id": basis.get("source_eval_id"),
        "source_fingerprint": _text(route.get("source_fingerprint")) or _text(dispatch.get("source_fingerprint")),
        "owner_route_currentness_basis": basis,
        "allowed_write_surfaces": _list_field(dispatch, prompt_contract, "allowed_write_surfaces"),
        "forbidden_surfaces": _list_field(dispatch, prompt_contract, "forbidden_surfaces"),
        "tool_discipline": _mapping(prompt_contract.get("tool_discipline"))
        or _mapping(dispatch.get("tool_discipline"))
        or owner_callable_search_discipline(),
        "search_boundaries": _mapping(prompt_contract.get("search_boundaries"))
        or _mapping(dispatch.get("search_boundaries"))
        or owner_callable_search_discipline(),
        "required_closeout_packet": closeout_packet_for_transport(transport_closeout_packet),
        "closeout_first_contract": closeout_first_contract,
        "completion_boundary": completion_boundary,
        "authority_boundary": _authority_boundary(),
        "runtime_completion_guard": _runtime_completion_guard(),
        "domain_intent": domain_intent,
    }
    if route.get("decision_trace") or route.get("failed_path_ledger"):
        core_fields["decision_trace"] = _mapping(route.get("decision_trace"))
        core_fields["decision_trace_refs"] = list(route.get("decision_trace_refs") or [])
        core_fields["failed_path_ledger"] = _mapping(route.get("failed_path_ledger"))
        core_fields["failed_path_refs"] = list(route.get("failed_path_refs") or [])
        core_fields["consumed_failed_path_refs"] = list(route.get("consumed_failed_path_refs") or [])
    dispatchable = (
        bool(action_type)
        and bool(domain_owner)
        and bool(basis.get("work_unit_id"))
        and bool(basis.get("work_unit_fingerprint"))
        and bool(basis.get("truth_epoch"))
        and _runtime_or_eval_currentness_present(basis)
        and bool(core_fields["source_fingerprint"])
        and action_type in {_text(action) for action in route.get("allowed_actions") or []}
        and not domain_intent["missing_required_fields"]
    )
    return {
        "version": PROTOCOL_VERSION,
        **core_fields,
        "owner_reason_contract": reason_contract,
        "priority_lattice": list(PRIORITY_LATTICE),
        "dispatchable": dispatchable,
    }


def payload_fields_for_owner_callable_dispatch(
    *,
    dispatch: Mapping[str, Any],
) -> dict[str, Any]:
    envelope = owner_callable_attempt_envelope(dispatch=dispatch)
    return {
        "work_unit_id": envelope.get("work_unit_id"),
        "source_eval_id": envelope.get("source_eval_id"),
        "source_fingerprint": envelope.get("source_fingerprint"),
        "domain_owner": envelope.get("domain_owner"),
        "owner_route_currentness_basis": envelope.get("owner_route_currentness_basis"),
        "allowed_write_surfaces": envelope.get("allowed_write_surfaces"),
        "forbidden_surfaces": envelope.get("forbidden_surfaces"),
        "required_closeout_packet": envelope.get("required_closeout_packet"),
        "closeout_first_contract": envelope.get("closeout_first_contract"),
        "completion_boundary": envelope.get("completion_boundary"),
        "decision_trace": envelope.get("decision_trace"),
        "decision_trace_refs": envelope.get("decision_trace_refs"),
        "failed_path_ledger": envelope.get("failed_path_ledger"),
        "failed_path_refs": envelope.get("failed_path_refs"),
    }


def closeout_packet_for_transport(closeout_packet: Mapping[str, Any]) -> dict[str, Any]:
    packet = {
        "typed_closeout_required_for_completion": bool(
            closeout_packet.get("typed_closeout_required_for_completion")
        ),
        "free_text_closeout_accepted": bool(closeout_packet.get("free_text_closeout_accepted")),
        "accepted_surface_kinds": list(closeout_packet.get("accepted_surface_kinds") or []),
        "required_ref_field": _text(closeout_packet.get("required_ref_field")),
        "minimum_closeout_refs": int(closeout_packet.get("minimum_closeout_refs") or 0),
    }
    for key in (
        "preallocated_closeout_ref",
        "closeout_first_contract",
        "required_user_stage_log_field",
        "accepted_user_stage_log_fields",
        "required_user_stage_log_fields",
        "user_stage_log_policy",
    ):
        value = closeout_packet.get(key)
        if value:
            packet[key] = value
    return packet


def route_protocol_dispatchable(owner_route: Mapping[str, Any], *, action_type: str | None = None) -> bool:
    route = decorate_owner_route(owner_route)
    protocol = _mapping(route.get("owner_route_attempt_protocol"))
    if protocol.get("dispatchable") is not True:
        return False
    if action_type is None:
        return True
    return action_type in {_text(action) for action in route.get("allowed_actions") or []}


_ROUTED_ACTION_TYPES = (
    "publication_gate_specificity_required",
    "publication_handoff_owner_gate",
    "current_package_freshness_required",
    "artifact_display_surface_materialization_required",
    "return_to_ai_reviewer_workflow",
    "canonical_paper_inputs_rehydrate_required",
    "run_quality_repair_batch",
    "run_gate_clearing_batch",
    "complete_medical_paper_readiness_surface",
    "paper_clean_room_rebuild_required",
)


def _required_closeout_packet(
    *,
    dispatch: Mapping[str, Any],
    action_type: str | None,
) -> dict[str, Any]:
    prompt_contract = _mapping(dispatch.get("prompt_contract"))
    packet = _mapping(dispatch.get("required_closeout_packet")) or _mapping(
        prompt_contract.get("required_closeout_packet")
    )
    if packet:
        return dict(packet)
    return owner_callable_typed_closeout_contract(action_type=action_type or "domain_owner_action")


def _completion_boundary(
    *,
    required_closeout_packet: Mapping[str, Any],
    action_type: str | None,
) -> dict[str, Any]:
    boundary = _mapping(required_closeout_packet.get("completion_boundary"))
    if boundary:
        return dict(boundary)
    return owner_callable_typed_closeout_contract(
        action_type=action_type or "domain_owner_action"
    )["completion_boundary"]


def _domain_intent(
    *,
    route: Mapping[str, Any],
    basis: Mapping[str, Any],
    required_closeout_packet: Mapping[str, Any],
) -> dict[str, Any]:
    payload = {
        "surface_kind": "mas_domain_intent_v1",
        "source_fingerprint": _text(route.get("source_fingerprint")),
        "route_epoch": _text(route.get("route_epoch")),
        "truth_epoch": _text(route.get("truth_epoch")),
        "idempotency_key": _text(route.get("idempotency_key")),
        "owner_route_currentness_basis": dict(basis),
        "required_closeout_packet": closeout_packet_for_transport(required_closeout_packet),
        "lifecycle_contract": {
            "fail_closed_when_missing": True,
            "provider_completion_is_domain_completion": False,
            "runtime_transport_ref": AUTHORITY_BOUNDARY["runtime_transport_ref"],
            "stage_run_ref_contract": AUTHORITY_BOUNDARY["stage_run_ref_contract"],
            "state_index_ref_contract": AUTHORITY_BOUNDARY["state_index_ref_contract"],
            "domain_completion_owner": "med-autoscience",
        },
    }
    if route.get("decision_trace") or route.get("failed_path_ledger"):
        payload["decision_trace"] = {
            "summary": _text(_mapping(route.get("decision_trace")).get("summary")),
            "refs": list(route.get("decision_trace_refs") or []),
            "body_included": False,
            "route_authority": False,
        }
        payload["decision_trace_refs"] = list(route.get("decision_trace_refs") or [])
        payload["failed_path_ledger"] = {
            "summary": _text(_mapping(route.get("failed_path_ledger")).get("summary")),
            "refs": list(route.get("failed_path_refs") or []),
            "consumed_refs": list(route.get("consumed_failed_path_refs") or []),
            "body_included": False,
            "route_authority": False,
        }
        payload["failed_path_refs"] = list(route.get("failed_path_refs") or [])
    payload["missing_required_fields"] = _domain_intent_missing_fields(payload)
    return payload


def _closeout_first_contract(
    *,
    dispatch: Mapping[str, Any],
    route: Mapping[str, Any],
    required_closeout_packet: Mapping[str, Any],
) -> dict[str, Any]:
    study_id = _text(dispatch.get("study_id")) or _text(route.get("study_id")) or "<study_id>"
    required_ref_field = _text(required_closeout_packet.get("required_ref_field")) or "closeout_refs"
    minimum_closeout_refs = int(required_closeout_packet.get("minimum_closeout_refs") or 0)
    return {
        "surface_kind": "mas_stage_outcome_opl_handoff_closeout_first_contract",
        "version": "mas-stage-outcome-opl-handoff-closeout-first-contract.v1",
        "stage_id": STAGE_OUTCOME_OPL_HANDOFF_TASK_KIND,
        "preallocated_closeout_ref": CLOSEOUT_PREALLOCATED_REF_TEMPLATE.format(study_id=study_id),
        "required_schema": {
            "surface_kind": "stage_attempt_closeout_packet",
            "schema_version": 1,
            "stage_id": STAGE_OUTCOME_OPL_HANDOFF_TASK_KIND,
            "required_ref_field": required_ref_field,
            "minimum_closeout_refs": minimum_closeout_refs,
        },
        "required_paper_stage_log_field": _text(
            required_closeout_packet.get("required_user_stage_log_field")
        ),
        "required_paper_stage_log_fields": list(
            required_closeout_packet.get("required_user_stage_log_fields") or []
        ),
        "evidence_refs_expectation": {
            "required_ref_field": required_ref_field,
            "minimum_closeout_refs": minimum_closeout_refs,
            "missing_refs_closeout": "typed_blocker",
            "typed_blocker_reason": "typed_closeout_packet_required",
        },
        "terminal_outcomes": list(CLOSEOUT_FIRST_TERMINAL_OUTCOMES),
        "provider_completion_is_domain_completion": False,
        "provider_completion_without_closeout_refs": "typed_closeout_packet_required",
        "completed_blocked_double_state_allowed": False,
    }


def _domain_intent_missing_fields(payload: Mapping[str, Any]) -> list[str]:
    basis = _mapping(payload.get("owner_route_currentness_basis"))
    checks = {
        "source_fingerprint": payload.get("source_fingerprint"),
        "route_epoch": payload.get("route_epoch"),
        "truth_epoch": payload.get("truth_epoch"),
        "idempotency_key": payload.get("idempotency_key"),
        "owner_route_currentness_basis.work_unit_id": basis.get("work_unit_id"),
        "owner_route_currentness_basis.work_unit_fingerprint": basis.get("work_unit_fingerprint"),
        "owner_route_currentness_basis.truth_epoch": basis.get("truth_epoch"),
    }
    missing = [field for field, value in checks.items() if _text(value) is None]
    if not _runtime_or_eval_currentness_present(basis):
        missing.append("owner_route_currentness_basis.runtime_health_epoch_or_source_eval_id")
    return missing


def _currentness_required_field_missing(field: str, basis: Mapping[str, Any]) -> bool:
    if field == "runtime_health_epoch_or_source_eval_id":
        return not _runtime_or_eval_currentness_present(basis)
    return _text(basis.get(field)) is None


def _runtime_or_eval_currentness_present(basis: Mapping[str, Any]) -> bool:
    return _text(basis.get("runtime_health_epoch")) is not None or _text(basis.get("source_eval_id")) is not None


def _authority_boundary() -> dict[str, object]:
    return dict(AUTHORITY_BOUNDARY)


def _runtime_completion_guard() -> dict[str, Any]:
    return {
        **{
            key: value
            for key, value in RUNTIME_COMPLETION_GUARD.items()
            if key != "domain_completion_requires"
        },
        "domain_completion_requires": list(RUNTIME_COMPLETION_GUARD["domain_completion_requires"]),
    }


def _route_to_attempt_contract() -> dict[str, Any]:
    return {
        **ROUTE_TO_ATTEMPT_CONTRACT,
        "allowed_current_execution_state_kinds": list(
            ROUTE_TO_ATTEMPT_CONTRACT["allowed_current_execution_state_kinds"]
        ),
        "forbidden_idle_states": list(ROUTE_TO_ATTEMPT_CONTRACT["forbidden_idle_states"]),
    }


def _list_field(
    dispatch: Mapping[str, Any],
    prompt_contract: Mapping[str, Any],
    field: str,
) -> list[Any]:
    value = dispatch.get(field)
    if not isinstance(value, list):
        value = prompt_contract.get(field)
    return list(value) if isinstance(value, list) else []


def _resolve_owner(registry_owner: object, *, owner: str | None) -> str | None:
    if registry_owner == "owner_route_next_owner":
        return owner
    return _text(registry_owner) or owner


def _compact_mapping(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if _text(value) is not None}


def _currentness_source_mappings(candidate: object) -> list[dict[str, Any]]:
    payload = _mapping(candidate)
    if not payload:
        return []
    source_refs = _mapping(payload.get("source_refs"))
    currentness_contract = _mapping(payload.get("currentness_contract"))
    sources = [
        _mapping(source_refs.get("owner_route_currentness_basis")),
        _mapping(payload.get("owner_route_currentness_basis")),
        _mapping(payload.get("currentness_basis")),
        _mapping(currentness_contract.get("basis")),
        source_refs,
        payload,
    ]
    return [source for source in sources if source]


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "AUTHORITY_BOUNDARY",
    "CURRENTNESS_BASIS_FIELDS",
    "PRIORITY_LATTICE",
    "PROTOCOL_VERSION",
    "ROUTE_TO_ATTEMPT_CONTRACT",
    "RUNTIME_COMPLETION_GUARD",
    "closeout_packet_for_transport",
    "currentness_basis",
    "currentness_contract",
    "decorate_owner_route",
    "owner_callable_attempt_envelope",
    "normalize_currentness_sources",
    "owner_reason_contract",
    "payload_fields_for_owner_callable_dispatch",
    "route_protocol_dispatchable",
]
