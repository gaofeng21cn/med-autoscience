from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.domain_action_request_materializer_parts import (
    currentness_identity,
    transition_request_record_fields,
)

TARGET_RUNTIME_OWNER = "one-person-lab"
_OPL_TRANSITION_RUNTIME_POSTCONDITION = {
    "surface_kind": "opl_domain_progress_transition_runtime_postcondition",
    "required_owner_surface": "one-person-lab DomainProgressTransitionRuntime",
    "mas_surface_role": "domain_intent_and_policy_request_projection",
    "mas_can_satisfy_readback": False,
    "request_projection_only": True,
    "required_readback_shape": {
        "identity": True,
        "causality": True,
        "authority_boundary": True,
        "exactly_one_outcome": True,
        "projection_metadata": True,
        "event_id": True,
        "outbox_item_id": True,
        "stage_run_identity": True,
    },
    "mas_projection_cannot_replace": [
        "opl_command",
        "opl_event",
        "opl_transactional_outbox",
        "opl_stage_run",
        "opl_provider_admission",
        "opl_fixed_point_reconcile",
    ],
}
_MAS_TRANSITION_PROJECTION_AUTHORITY_BOUNDARY = {
    "mas_materializes_domain_intent": True,
    "mas_creates_owner_callable_carrier": False,
    "mas_creates_opl_outbox": False,
    "mas_creates_opl_event": False,
    "mas_creates_opl_stage_run": False,
    "mas_dispatch_authority": False,
    "provider_admission_pending": False,
    "can_create_success_outcome": False,
    "can_select_next_action": False,
    "target_runtime_owner": TARGET_RUNTIME_OWNER,
    "execution_requires_opl_authorization": True,
    "durable_carrier_owner": TARGET_RUNTIME_OWNER,
    "projection_only": True,
}


def domain_progress_transition_request_projection(dispatches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for dispatch in dispatches:
        record = _domain_progress_transition_request_record(dispatch)
        if record:
            records.append(record)
    for record in records:
        record["projection_source"] = "domain_action_request_materializer"
        record["legacy_owner_callable_adapter_readback"] = False
        record["domain_intent_producer"] = "med_autoscience.paper_progress_policy_adapter"
        record["durable_carrier_owner"] = TARGET_RUNTIME_OWNER
        record["opl_transition_runtime_required_for_durable_carrier"] = True
        _apply_transition_projection_boundary(record)
    return records



def _domain_progress_transition_request_record(dispatch: Mapping[str, Any]) -> dict[str, Any]:
    request = _mapping(dispatch.get("opl_domain_progress_transition_request")) or _mapping(
        _mapping(dispatch.get("prompt_contract")).get("opl_domain_progress_transition_request")
    )
    source_action = _mapping(dispatch.get("source_action"))
    owner_route = _mapping(dispatch.get("owner_route"))
    prompt_contract = _mapping(dispatch.get("prompt_contract"))
    closeout_admission = _mapping(dispatch.get("progress_first_closeout_admission"))
    record = {
        **_transition_request_identity_fields(dispatch),
        "surface": "mas_domain_progress_transition_request_projection",
        "legacy_surface": _text(dispatch.get("legacy_surface")) or _text(dispatch.get("surface")),
        "legacy_owner_callable_adapter_readback": False,
        "legacy_owner_callable_adapter_missing_opl_request": not bool(request),
        "opl_domain_progress_transition_request": request or None,
        "domain_intent_ref": _domain_intent_ref(dispatch),
        "authority_boundary": _mapping(dispatch.get("authority_boundary")) or None,
        "stage_transition_authority_boundary_ref": _stage_transition_authority_boundary_ref(dispatch)
        or None,
        **transition_request_record_fields.transition_request_record_extra_fields(
            dispatch,
            text=_text,
            mapping=_mapping,
        ),
        "refs": _mapping(dispatch.get("refs")) or None,
        "source_action_ref": _source_action_ref(source_action),
        "owner_route_ref": _owner_route_ref(owner_route),
        "prompt_contract_ref": _prompt_contract_ref(prompt_contract),
        "progress_first_closeout_admission_ref": _progress_first_closeout_admission_ref(
            closeout_admission
        ),
        "transition_request_payload_scope": "identity_refs_and_contract_metadata_only",
        "transition_request_projection_body_authority": False,
        "transition_request_projection_body_omitted": True,
        "source_action_body_omitted": bool(source_action),
        "owner_route_body_omitted": bool(owner_route),
        "prompt_contract_body_omitted": bool(prompt_contract),
        "domain_intent_body_omitted": bool(_mapping(dispatch.get("domain_intent"))),
        "stage_transition_authority_boundary_body_omitted": bool(
            _mapping(dispatch.get("stage_transition_authority_boundary"))
        ),
        "progress_first_closeout_admission_body_omitted": bool(closeout_admission),
        "operator_payload_body_omitted": bool(_mapping(dispatch.get("operator_payload"))),
        "payload_authoring_target_body_omitted": bool(
            _mapping(dispatch.get("payload_authoring_target"))
        ),
        "record_production_satisfaction_body_omitted": bool(
            _mapping(dispatch.get("record_production_satisfaction"))
        ),
        "owner_route_attempt_envelope_body_omitted": bool(
            _mapping(dispatch.get("owner_route_attempt_envelope"))
        ),
        "legacy_owner_callable_adapter_body_omitted": True,
        "omitted_body_fields": [
            "domain_intent",
            "operator_payload",
            "owner_route",
            "owner_route_attempt_envelope",
            "payload_authoring_target",
            "progress_first_closeout_admission",
            "prompt_contract",
            "record_production_satisfaction",
            "source_action",
            "stage_transition_authority_boundary",
        ],
        "provider_admission_pending": False,
        "provider_admission_requires_opl_runtime_result": True,
        "provider_completion_is_domain_completion": False,
        "projection_only": True,
        "owner_callable_adapter_diagnostic_only": True,
        "owner_callable_adapter_readiness_authority": False,
        "owner_callable_adapter_can_create_success_outcome": False,
        "owner_callable_carrier_projection_only": True,
        "mas_private_attempt_loop_forbidden": True,
        "mas_dispatch_authority": False,
        "mas_creates_owner_callable_carrier": False,
        "mas_creates_opl_outbox": False,
        "mas_creates_opl_event": False,
        "mas_creates_opl_stage_run": False,
        "target_runtime_owner": _text(dispatch.get("target_runtime_owner")) or TARGET_RUNTIME_OWNER,
        "dispatch_status": _text(dispatch.get("dispatch_status")) or "transition_request_pending",
        "blocked_reason": _text(dispatch.get("blocked_reason")),
    }
    _apply_transition_projection_boundary(record)
    if not any(
        record.get(key)
        for key in (
            "study_id",
            "action_type",
            "work_unit_id",
            "work_unit_fingerprint",
            "dispatch_path",
        )
    ):
        return {}
    return {key: value for key, value in record.items() if value is not None}


def _transition_request_identity_fields(payload: Mapping[str, Any]) -> dict[str, Any]:
    refs = _mapping(payload.get("refs"))
    source_action = _mapping(payload.get("source_action"))
    prompt_contract = _mapping(payload.get("prompt_contract"))
    request = _mapping(payload.get("opl_domain_progress_transition_request")) or _mapping(
        prompt_contract.get("opl_domain_progress_transition_request")
    )
    owner_route = _mapping(payload.get("owner_route")) or _mapping(prompt_contract.get("owner_route"))
    owner_route_source_refs = _mapping(owner_route.get("source_refs"))
    currentness_basis = _transition_request_currentness_basis(
        payload=payload,
        request=request,
        prompt_contract=prompt_contract,
        owner_route=owner_route,
        source_action=source_action,
    )
    return {
        key: value
        for key, value in {
            "study_id": _first_text(
                payload,
                request,
                prompt_contract,
                source_action,
                key="study_id",
            ),
            "quest_id": _first_text(
                payload,
                request,
                prompt_contract,
                source_action,
                key="quest_id",
            ),
            "action_type": _first_text(
                payload,
                request,
                prompt_contract,
                source_action,
                key="action_type",
            ),
            "route_identity_key": _first_text(
                payload,
                request,
                prompt_contract,
                refs,
                owner_route,
                owner_route_source_refs,
                currentness_basis,
                key="route_identity_key",
            ),
            "attempt_idempotency_key": _first_text(
                payload,
                request,
                prompt_contract,
                refs,
                owner_route,
                owner_route_source_refs,
                currentness_basis,
                key="attempt_idempotency_key",
            ),
            "work_unit_id": (
                _text(payload.get("work_unit_id"))
                or _text(payload.get("next_work_unit"))
                or _text(source_action.get("work_unit_id"))
                or _text(request.get("work_unit_id"))
                or _text(prompt_contract.get("work_unit_id"))
                or _text(owner_route_source_refs.get("work_unit_id"))
                or _text(currentness_basis.get("work_unit_id"))
            ),
            "work_unit_fingerprint": (
                _text(payload.get("work_unit_fingerprint"))
                or _text(payload.get("action_fingerprint"))
                or _text(source_action.get("work_unit_fingerprint"))
                or _text(request.get("work_unit_fingerprint"))
                or _text(prompt_contract.get("work_unit_fingerprint"))
                or _text(owner_route.get("work_unit_fingerprint"))
                or _text(owner_route_source_refs.get("work_unit_fingerprint"))
                or _text(currentness_basis.get("work_unit_fingerprint"))
            ),
            "action_fingerprint": _text(payload.get("action_fingerprint"))
            or _text(payload.get("work_unit_fingerprint")),
            "next_executable_owner": _text(payload.get("next_executable_owner"))
            or _text(request.get("next_owner"))
            or _text(prompt_contract.get("next_executable_owner")),
            "required_output_surface": _text(payload.get("required_output_surface"))
            or _text(request.get("required_output_surface"))
            or _text(prompt_contract.get("required_output_surface")),
            "dispatch_authority": _text(payload.get("dispatch_authority"))
            or _text(request.get("dispatch_authority")),
            "dispatch_path": _text(payload.get("dispatch_path")) or _text(refs.get("dispatch_path")),
            "stage_packet_ref": _text(payload.get("stage_packet_ref")) or _text(refs.get("stage_packet_ref")),
            "stage_packet_refs": payload.get("stage_packet_refs") or refs.get("stage_packet_refs"),
            "currentness_basis": currentness_basis or None,
        }.items()
        if value is not None
    }


def _transition_request_currentness_basis(
    *,
    payload: Mapping[str, Any],
    request: Mapping[str, Any],
    prompt_contract: Mapping[str, Any],
    owner_route: Mapping[str, Any],
    source_action: Mapping[str, Any],
) -> dict[str, Any]:
    return currentness_identity.normalize_currentness_sources(
        _mapping(request.get("currentness_basis")),
        currentness_identity.owner_route_basis(owner_route),
        _mapping(prompt_contract.get("owner_route_currentness_basis")),
        _mapping(source_action.get("owner_route_currentness_basis")),
        currentness_identity.action_basis(payload),
        currentness_identity.action_basis(source_action),
    )


def _source_action_ref(source_action: Mapping[str, Any]) -> dict[str, Any] | None:
    if not source_action:
        return None
    ref_field_names = (
        "surface",
        "study_id",
        "quest_id",
        "action_type",
        "action_id",
        "reason",
        "owner",
        "request_owner",
        "recommended_owner",
        "authority",
        "required_output_surface",
        "stage_index_ref",
        "current_stage_id",
        "current_work_unit_binding",
        "stage_native_next_action_admission",
        "next_work_unit",
        "controller_work_unit_id",
        "executable_work_unit",
        "work_unit_fingerprint",
        "blocked_reason",
        "route_target",
        "route_key_question",
        "route_rationale",
        "source_ref",
        "source_surface",
        "supervisor_decision_ref",
        "supervisor_authority",
        "supervisor_authority_boundary",
        "supervisor_policy_projection",
        "supervisor_policy_projection_boundary",
        "current_action_source",
        "stale_record_ref",
        "required_currentness_refs",
        "record_only_surface",
        "materialization_decision",
        "publication_eval_latest_write_allowed",
        "controller_decision_write_allowed",
        "reviewer_record_ref",
        "source_eval_id",
        "story_surface_delta_refs",
        "readiness_blocker_followup_superseded",
        "readiness_blocker_ref",
        "publication_eval_gap_ids",
        "repair_progress_precedence",
        "provider_admission_allowed",
        "provider_admission_requires_opl_runtime_result",
        "terminal_source_provenance_blocker",
        "hard_methodology_target",
        "required_delta_kind",
    )
    ref = {
        **{key: source_action[key] for key in ref_field_names if key in source_action},
        "diagnostic_ref_only": True,
        "payload_body_omitted": True,
        "work_unit_id": _text(source_action.get("work_unit_id"))
        or _text(source_action.get("next_work_unit"))
        or _text(source_action.get("controller_work_unit_id")),
        "work_unit_fingerprint": _text(source_action.get("work_unit_fingerprint"))
        or _text(source_action.get("action_fingerprint")),
        "action_fingerprint": _text(source_action.get("action_fingerprint")),
    }
    stall = _mapping(source_action.get("paper_progress_stall"))
    if stall:
        ref["paper_progress_stall_ref"] = _paper_progress_stall_ref(stall)
    return {key: value for key, value in ref.items() if value is not None}


def _owner_route_ref(owner_route: Mapping[str, Any]) -> dict[str, Any] | None:
    if not owner_route:
        return None
    source_refs = _mapping(owner_route.get("source_refs"))
    ref = {
        "diagnostic_ref_only": True,
        "payload_body_omitted": True,
        "surface": _text(owner_route.get("surface")),
        "schema_version": owner_route.get("schema_version"),
        "study_id": _text(owner_route.get("study_id")),
        "quest_id": _text(owner_route.get("quest_id")),
        "current_owner": _text(owner_route.get("current_owner")),
        "next_owner": _text(owner_route.get("next_owner")),
        "owner_reason": _text(owner_route.get("owner_reason")),
        "allowed_actions": _text_list(owner_route.get("allowed_actions")),
        "blocked_actions": _text_list(owner_route.get("blocked_actions")),
        "idempotency_key": _text(owner_route.get("idempotency_key")),
        "truth_epoch": _text(owner_route.get("truth_epoch")) or _text(owner_route.get("route_epoch")),
        "runtime_health_epoch": _text(owner_route.get("runtime_health_epoch")),
        "source_fingerprint": _text(owner_route.get("source_fingerprint")),
        "work_unit_id": _text(owner_route.get("work_unit_id"))
        or _text(source_refs.get("work_unit_id")),
        "work_unit_fingerprint": _text(owner_route.get("work_unit_fingerprint"))
        or _text(source_refs.get("work_unit_fingerprint")),
        "route_identity_key": _text(owner_route.get("route_identity_key"))
        or _text(source_refs.get("route_identity_key")),
        "attempt_idempotency_key": _text(owner_route.get("attempt_idempotency_key"))
        or _text(source_refs.get("attempt_idempotency_key")),
        "currentness_contract": _mapping(owner_route.get("currentness_contract")) or None,
        "owner_route_attempt_protocol_ref": _owner_route_attempt_protocol_ref(
            _mapping(owner_route.get("owner_route_attempt_protocol"))
        ),
        "source_refs": _owner_route_source_refs_ref(source_refs),
    }
    return {key: value for key, value in ref.items() if value is not None}


def _owner_route_source_refs_ref(source_refs: Mapping[str, Any]) -> dict[str, Any] | None:
    if not source_refs:
        return None
    allowed = {
        "bridge_authority",
        "bridged_from_idempotency_key",
        "bridged_from_owner_reason",
        "materialized_from_action_type",
        "materialized_work_unit_id",
        "owner_route_currentness_basis",
        "predecessor_action_type",
        "predecessor_work_unit_id",
        "predecessor_work_unit_fingerprint",
        "attempt_idempotency_key",
        "route_identity_key",
        "source_eval_id",
        "successor_source_surface",
        "supervisor_decision_ref",
        "study_truth_epoch",
        "runtime_health_epoch",
        "truth_epoch",
        "work_unit_id",
        "work_unit_fingerprint",
        "blocked_reason",
    }
    ref: dict[str, Any] = {}
    for key in sorted(allowed):
        value = source_refs.get(key)
        if isinstance(value, Mapping):
            mapped = _mapping(value)
            if mapped:
                ref[key] = mapped
        elif value is not None:
            ref[key] = value
    return ref or None


def _prompt_contract_ref(prompt_contract: Mapping[str, Any]) -> dict[str, Any] | None:
    if not prompt_contract:
        return None
    ref = {
        "diagnostic_ref_only": True,
        "payload_body_omitted": True,
        "study_id": _text(prompt_contract.get("study_id")),
        "quest_id": _text(prompt_contract.get("quest_id")),
        "action_type": _text(prompt_contract.get("action_type")),
        "owner_callable_command_ref": _text(prompt_contract.get("owner_callable_command")),
        "owner_callable_payload_ref": _text(prompt_contract.get("owner_callable_payload_ref")),
        "compact_evidence_packet_ref": _text(prompt_contract.get("compact_evidence_packet_ref")),
        "request_packet_ref": _text(prompt_contract.get("request_packet_ref")),
        "operator_payload_ref": _text(prompt_contract.get("operator_payload_ref")),
        "operator_payload_present": prompt_contract.get("operator_payload_present"),
        "surface_key": _text(prompt_contract.get("surface_key")),
        "dispatch_authority": _text(prompt_contract.get("dispatch_authority")),
        "required_output_surface": _text(prompt_contract.get("required_output_surface")),
        "required_output_target_surface": _mapping(
            prompt_contract.get("required_output_target_surface")
        )
        or None,
        "readiness_surface_identity": _mapping(prompt_contract.get("readiness_surface_identity"))
        or None,
        "work_unit_id": _text(prompt_contract.get("work_unit_id")),
        "work_unit_fingerprint": _text(prompt_contract.get("work_unit_fingerprint")),
        "owner_route_ref": _owner_route_ref(_mapping(prompt_contract.get("owner_route"))),
        "owner_route_currentness_basis": _mapping(
            prompt_contract.get("owner_route_currentness_basis")
        )
        or None,
        "opl_domain_progress_transition_request_ref": _transition_request_ref(
            _mapping(prompt_contract.get("opl_domain_progress_transition_request"))
        ),
        "forbidden_surfaces": _text_list(prompt_contract.get("forbidden_surfaces")),
        "allowed_write_surfaces": _text_list(prompt_contract.get("allowed_write_surfaces")),
        "search_boundaries_ref": _search_boundaries_ref(
            _mapping(prompt_contract.get("search_boundaries"))
        ),
        "medical_claim_authoring_allowed": prompt_contract.get("medical_claim_authoring_allowed"),
        "paper_package_mutation_allowed": prompt_contract.get("paper_package_mutation_allowed"),
        "quality_gate_relaxation_allowed": prompt_contract.get("quality_gate_relaxation_allowed"),
        "manual_study_patch_allowed": prompt_contract.get("manual_study_patch_allowed"),
        "provider_admission_pending": prompt_contract.get("provider_admission_pending"),
        "provider_admission_requires_opl_runtime_result": prompt_contract.get(
            "provider_admission_requires_opl_runtime_result"
        ),
        "opl_transition_runtime_postcondition": _mapping(
            prompt_contract.get("opl_transition_runtime_postcondition")
        )
        or None,
        "owner_callable_carrier_projection_only": prompt_contract.get(
            "owner_callable_carrier_projection_only"
        ),
        "mas_creates_owner_callable_carrier": prompt_contract.get("mas_creates_owner_callable_carrier"),
        "mas_local_dispatch_carrier_persistence": _text(
            prompt_contract.get("mas_local_dispatch_carrier_persistence")
        ),
        "opl_transition_runtime_required_for_durable_carrier": prompt_contract.get(
            "opl_transition_runtime_required_for_durable_carrier"
        ),
    }
    return {key: value for key, value in ref.items() if value is not None}


def _domain_intent_ref(dispatch: Mapping[str, Any]) -> dict[str, Any] | None:
    intent = _mapping(dispatch.get("domain_intent"))
    if not intent:
        return None
    ref = {
        "diagnostic_ref_only": True,
        "payload_body_omitted": True,
        "intent_kind": _text(intent.get("intent_kind")) or _text(intent.get("kind")),
        "study_id": _text(intent.get("study_id")) or _text(dispatch.get("study_id")),
        "quest_id": _text(intent.get("quest_id")) or _text(dispatch.get("quest_id")),
        "action_type": _text(intent.get("action_type")) or _text(dispatch.get("action_type")),
        "next_owner": _text(intent.get("next_owner"))
        or _text(dispatch.get("next_executable_owner")),
        "required_output_surface": _text(intent.get("required_output_surface"))
        or _text(dispatch.get("required_output_surface")),
        "work_unit_id": _text(intent.get("work_unit_id")) or _text(dispatch.get("work_unit_id")),
        "work_unit_fingerprint": _text(intent.get("work_unit_fingerprint"))
        or _text(dispatch.get("work_unit_fingerprint"))
        or _text(dispatch.get("action_fingerprint")),
    }
    return {key: value for key, value in ref.items() if value is not None}


def _stage_transition_authority_boundary_ref(dispatch: Mapping[str, Any]) -> dict[str, Any] | None:
    boundary = _mapping(dispatch.get("stage_transition_authority_boundary"))
    if not boundary:
        return None
    ref_field_names = (
        "stage_transition_authority",
        "provider_completion_counts_as_stage_transition",
        "provider_completion_counts_as_domain_completion",
        "provider_admission_requires_opl_runtime_result",
        "mas_can_create_stage_run",
        "mas_can_complete_stage_transition",
    )
    ref = {
        **{key: boundary[key] for key in ref_field_names if key in boundary},
        "diagnostic_ref_only": True,
        "payload_body_omitted": True,
        "surface_kind": _text(boundary.get("surface_kind")) or _text(boundary.get("surface")),
        "authority_owner": _text(boundary.get("authority_owner")),
        "target_runtime_owner": _text(boundary.get("target_runtime_owner")),
        "stage_run_id": _text(boundary.get("stage_run_id")),
        "stage_run_ref": _text(boundary.get("stage_run_ref")),
    }
    return {key: value for key, value in ref.items() if value is not None}


def _owner_route_attempt_protocol_ref(protocol: Mapping[str, Any]) -> dict[str, Any] | None:
    if not protocol:
        return None
    ref = {
        "diagnostic_ref_only": True,
        "payload_body_omitted": True,
        "version": _text(protocol.get("version")),
        "dispatchable": protocol.get("dispatchable"),
        "priority_class": _text(protocol.get("priority_class")),
        "currentness_contract": _text(protocol.get("currentness_contract")),
        "authority_boundary": _mapping(protocol.get("authority_boundary")) or None,
    }
    return {key: value for key, value in ref.items() if value is not None}


def _progress_first_closeout_admission_ref(admission: Mapping[str, Any]) -> dict[str, Any] | None:
    if not admission:
        return None
    ref = {
        "diagnostic_ref_only": True,
        "payload_body_omitted": True,
        "admission_status": _text(admission.get("admission_status")),
        "blocked_reason": _text(admission.get("blocked_reason")),
        "source_ref": _text(admission.get("source_ref")),
        "route_identity_key": _text(admission.get("route_identity_key")),
        "attempt_idempotency_key": _text(admission.get("attempt_idempotency_key")),
    }
    return {key: value for key, value in ref.items() if value is not None}


def _paper_progress_stall_ref(stall: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in {
            "kind": _text(stall.get("kind")),
            "route_back_evidence_ref": _text(stall.get("route_back_evidence_ref")),
            "provider_admission_allowed": stall.get("provider_admission_allowed"),
            "provider_admission_requires_opl_runtime_result": stall.get(
                "provider_admission_requires_opl_runtime_result"
            ),
        }.items()
        if value is not None
    }


def _transition_request_ref(request: Mapping[str, Any]) -> dict[str, Any] | None:
    if not request:
        return None
    ref = {
        "diagnostic_ref_only": True,
        "payload_body_omitted": True,
        "study_id": _text(request.get("study_id")),
        "quest_id": _text(request.get("quest_id")),
        "action_type": _text(request.get("action_type")),
        "work_unit_id": _text(request.get("work_unit_id")),
        "work_unit_fingerprint": _text(request.get("work_unit_fingerprint")),
        "route_identity_key": _text(request.get("route_identity_key")),
        "attempt_idempotency_key": _text(request.get("attempt_idempotency_key")),
        "dispatch_ref": _text(request.get("dispatch_ref")),
        "required_output_surface": _text(request.get("required_output_surface")),
    }
    return {key: value for key, value in ref.items() if value is not None}


def _search_boundaries_ref(search_boundaries: Mapping[str, Any]) -> dict[str, Any] | None:
    if not search_boundaries:
        return None
    ref = {
        "diagnostic_ref_only": True,
        "payload_body_omitted": True,
        "surface": _text(search_boundaries.get("surface")),
        "forbidden_command_patterns": _text_list(
            search_boundaries.get("forbidden_command_patterns")
        ),
        "forbidden_path_globs": _text_list(search_boundaries.get("forbidden_path_globs")),
    }
    return {key: value for key, value in ref.items() if value is not None}


def _text_list(value: object) -> list[str] | None:
    if not isinstance(value, (list, tuple, set)):
        return None
    items = [_text(item) for item in value]
    return [item for item in items if item is not None]


def _first_text(*payloads: Mapping[str, Any], key: str) -> str | None:
    for payload in payloads:
        value = _text(payload.get(key))
        if value is not None:
            return value
    return None



def _apply_transition_projection_boundary(payload: dict[str, Any]) -> dict[str, Any]:
    payload["provider_admission_pending"] = False
    payload["provider_admission_requires_opl_runtime_result"] = True
    payload["provider_completion_is_domain_completion"] = False
    payload["mas_dispatch_authority"] = False
    payload["mas_creates_owner_callable_carrier"] = False
    payload["mas_creates_opl_outbox"] = False
    payload["mas_creates_opl_event"] = False
    payload["mas_creates_opl_stage_run"] = False
    payload["target_runtime_owner"] = TARGET_RUNTIME_OWNER
    payload["opl_transition_runtime_required_for_durable_carrier"] = True
    payload["opl_transition_runtime_postcondition"] = _opl_transition_runtime_postcondition()
    authority_boundary = dict(_mapping(payload.get("authority_boundary")))
    authority_boundary.update(_mas_transition_projection_authority_boundary())
    payload["authority_boundary"] = authority_boundary
    return payload


def _opl_transition_runtime_postcondition() -> dict[str, Any]:
    return {
        key: dict(value) if isinstance(value, Mapping) else list(value) if isinstance(value, list) else value
        for key, value in _OPL_TRANSITION_RUNTIME_POSTCONDITION.items()
    }


def _mas_transition_projection_authority_boundary() -> dict[str, Any]:
    return dict(_MAS_TRANSITION_PROJECTION_AUTHORITY_BOUNDARY)


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


__all__ = ["domain_progress_transition_request_projection"]
