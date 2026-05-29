from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from med_autoscience.controllers.default_executor_closeout_contract import (
    default_executor_typed_closeout_contract,
)


PROTOCOL_VERSION = "mas-owner-route-attempt-protocol.v1"
PRIORITY_LATTICE = [
    "hard_methodology_or_source_blocker",
    "pending_ai_reviewer_request",
    "ai_reviewer_currentness",
    "write_route_back",
    "package_freshness",
    "delivery_or_human_handoff",
]

DEFAULT_FORBIDDEN_SURFACES = [
    "manuscript/**",
    "current_package/**",
    "paper/current_package/**",
    "manuscript/current_package/**",
    "artifacts/publication_eval/latest.json",
    "artifacts/controller_decisions/latest.json",
]
AUTHORITY_BOUNDARY = {
    "opl_owns": [
        "queue",
        "attempt",
        "retry",
        "dead_letter",
        "provider_liveness",
    ],
    "mas_owns": [
        "domain_truth",
        "ai_reviewer",
        "publication_gate",
        "artifact_authority",
        "owner_receipt",
        "typed_blocker",
    ],
}
RUNTIME_COMPLETION_GUARD = {
    "provider_completion_is_domain_completion": False,
    "provider_completion_is_stage_state": False,
    "running_worker_is_stage_state": False,
    "queue_succeeded_is_domain_completion": False,
    "retry_budget_is_domain_completion": False,
    "stage_state_owner": "one-person-lab",
    "domain_completion_owner": "med-autoscience",
    "domain_completion_requires": [
        "mas_owner_receipt_ref",
        "mas_typed_blocker_ref",
        "ai_reviewer_or_publication_gate_ref",
    ],
}


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
    return _compact_mapping(
        {
            "source_eval_id": source_refs.get("source_eval_id")
            or route.get("source_eval_id")
            or embedded_basis.get("source_eval_id"),
            "work_unit_id": source_refs.get("work_unit_id")
            or route.get("work_unit_id")
            or embedded_basis.get("work_unit_id"),
            "work_unit_fingerprint": route.get("work_unit_fingerprint")
            or source_refs.get("work_unit_fingerprint")
            or embedded_basis.get("work_unit_fingerprint"),
            "truth_epoch": route.get("truth_epoch")
            or source_refs.get("study_truth_epoch")
            or embedded_basis.get("truth_epoch"),
            "runtime_health_epoch": route.get("runtime_health_epoch")
            or source_refs.get("runtime_health_epoch")
            or embedded_basis.get("runtime_health_epoch"),
        }
    )


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
    if reason is not None and not reason_contract["registered"]:
        allowed_actions = []
        route["allowed_actions"] = []
        route["blocked_actions"] = list(_ROUTED_ACTION_TYPES)
    elif not allowed_actions and reason_contract["allowed_actions"]:
        allowed_actions = list(reason_contract["allowed_actions"])
        route["allowed_actions"] = allowed_actions
        route["blocked_actions"] = [
            action for action in _ROUTED_ACTION_TYPES if action not in set(allowed_actions)
        ]
    source_refs = dict(_mapping(route.get("source_refs")))
    basis = currentness_basis(route)
    if basis:
        source_refs["owner_route_currentness_basis"] = basis
    route["source_refs"] = source_refs
    route["owner_reason_contract"] = reason_contract
    route["priority_lattice"] = list(PRIORITY_LATTICE)
    route["currentness_contract"] = currentness_contract(route)
    route["owner_route_attempt_protocol"] = {
        "version": PROTOCOL_VERSION,
        "dispatchable": bool(reason_contract["registered"] and allowed_actions),
        "priority_class": reason_contract["priority_class"],
        "currentness_contract": route["currentness_contract"]["status"],
        "authority_boundary": _authority_boundary(),
        "runtime_completion_guard": _runtime_completion_guard(),
        "completion_boundary": default_executor_typed_closeout_contract(
            action_type=action_type or "domain_owner_action"
        )["completion_boundary"],
    }
    return route


def default_executor_attempt_envelope(
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
    completion_boundary = _completion_boundary(
        required_closeout_packet=required_closeout_packet,
        action_type=action_type,
    )
    domain_intent = _domain_intent(
        route=route,
        basis=basis,
        required_closeout_packet=required_closeout_packet,
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
        "required_closeout_packet": closeout_packet_for_transport(required_closeout_packet),
        "completion_boundary": completion_boundary,
        "authority_boundary": _authority_boundary(),
        "runtime_completion_guard": _runtime_completion_guard(),
        "domain_intent": domain_intent,
    }
    dispatchable = (
        bool(reason_contract["registered"])
        and bool(action_type)
        and bool(domain_owner)
        and bool(basis.get("work_unit_id"))
        and bool(basis.get("work_unit_fingerprint"))
        and bool(basis.get("truth_epoch"))
        and _runtime_or_eval_currentness_present(basis)
        and bool(core_fields["source_fingerprint"])
        and action_type in set(reason_contract["allowed_actions"])
        and not domain_intent["missing_required_fields"]
    )
    return {
        "version": PROTOCOL_VERSION,
        **core_fields,
        "owner_reason_contract": reason_contract,
        "priority_lattice": list(PRIORITY_LATTICE),
        "dispatchable": dispatchable,
    }


def payload_fields_for_default_executor_dispatch(
    *,
    dispatch: Mapping[str, Any],
) -> dict[str, Any]:
    envelope = default_executor_attempt_envelope(dispatch=dispatch)
    return {
        "work_unit_id": envelope.get("work_unit_id"),
        "source_eval_id": envelope.get("source_eval_id"),
        "source_fingerprint": envelope.get("source_fingerprint"),
        "domain_owner": envelope.get("domain_owner"),
        "owner_route_currentness_basis": envelope.get("owner_route_currentness_basis"),
        "allowed_write_surfaces": envelope.get("allowed_write_surfaces"),
        "forbidden_surfaces": envelope.get("forbidden_surfaces"),
        "required_closeout_packet": envelope.get("required_closeout_packet"),
        "completion_boundary": envelope.get("completion_boundary"),
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
    contract = _mapping(route.get("owner_reason_contract"))
    return action_type in set(contract.get("allowed_actions") or [])


def _entry(
    *,
    owner: str,
    allowed_actions: Iterable[str],
    required_output: str,
    priority_class: str,
    regression_refs: Iterable[str],
    forbidden_surfaces: Iterable[str] = DEFAULT_FORBIDDEN_SURFACES,
    allow_route_action: bool = False,
) -> dict[str, Any]:
    return {
        "owner": owner,
        "allowed_actions": list(allowed_actions),
        "required_output": required_output,
        "priority_class": priority_class,
        "regression_refs": list(regression_refs),
        "forbidden_surfaces": list(forbidden_surfaces),
        "allow_route_action": allow_route_action,
    }


def _ai_reviewer_entry(*regression_refs: str) -> dict[str, Any]:
    return _entry(
        owner="ai_reviewer",
        allowed_actions=["return_to_ai_reviewer_workflow"],
        required_output="artifacts/publication_eval/latest.json",
        priority_class="ai_reviewer_currentness",
        regression_refs=regression_refs or ("tests/owner_route_reconcile_cases",),
    )


def _write_entry(*regression_refs: str) -> dict[str, Any]:
    return _entry(
        owner="write",
        allowed_actions=["run_quality_repair_batch"],
        required_output=(
            "canonical manuscript story-surface delta or "
            "typed blocker:manuscript_story_surface_delta_missing"
        ),
        priority_class="write_route_back",
        regression_refs=regression_refs or ("tests/owner_route_reconcile_cases",),
    )


def _artifact_entry(*regression_refs: str) -> dict[str, Any]:
    return _entry(
        owner="artifact_os",
        allowed_actions=[
            "current_package_freshness_required",
            "artifact_display_surface_materialization_required",
        ],
        required_output="artifacts/controller/current_package_freshness/latest.json",
        priority_class="package_freshness",
        regression_refs=regression_refs or ("tests/owner_route_reconcile_cases",),
    )


def _gate_clearing_entry(*regression_refs: str) -> dict[str, Any]:
    return _entry(
        owner="gate_clearing_batch",
        allowed_actions=["run_gate_clearing_batch"],
        required_output="artifacts/controller/gate_clearing_batch/latest.json",
        priority_class="package_freshness",
        regression_refs=regression_refs or ("tests/owner_route_reconcile_cases",),
    )


_REASON_REGISTRY = {
    "ai_reviewer_request_pending": _ai_reviewer_entry("DM002:pending_ai_reviewer_request"),
    "ai_reviewer_assessment_required": _ai_reviewer_entry(),
    "ai_reviewer_assessment_stale_after_reviewer_revision": _ai_reviewer_entry(
        "DM002:stale_reviewer_record"
    ),
    "ai_reviewer_record_stale_after_current_manuscript": _ai_reviewer_entry(
        "DM002:reviewer_currentness"
    ),
    "ai_reviewer_record_stale_after_current_inputs": _ai_reviewer_entry(
        "DM003:reviewer_input_currentness"
    ),
    "ai_reviewer_record_stale_after_unit_harmonized_rerun": _ai_reviewer_entry(),
    "analysis_harmonization_completed_ai_reviewer_review_required": _ai_reviewer_entry(),
    "ai_reviewer_repair_recheck_required": _ai_reviewer_entry(),
    "analysis_repair_requires_ai_reviewer_recheck": _ai_reviewer_entry(),
    "rebuttal_closure_requires_ai_reviewer_recheck": _ai_reviewer_entry(),
    "text_repair_requires_ai_reviewer_recheck": _ai_reviewer_entry(),
    "domain_transition_ai_reviewer_re_eval": _ai_reviewer_entry("DM003:domain_transition_ai_reviewer_re_eval"),
    "return_to_ai_reviewer_workflow": _ai_reviewer_entry(),
    "publication_gate_recheck_required": _ai_reviewer_entry(),
    "ai_reviewer_request_missing": _ai_reviewer_entry(),
    "ai_reviewer_required": _ai_reviewer_entry(),
    "ai_reviewer_quality_authority_missing": _ai_reviewer_entry(),
    "ai_reviewer_record_missing": _ai_reviewer_entry(),
    "ai_reviewer_record_incomplete": _ai_reviewer_entry(),
    "dm002_publication_eval_requires_ai_reviewer_and_canonical_refresh": _ai_reviewer_entry(),
    "manuscript_story_surface_delta_missing": _write_entry("DM003:medical_prose_route_back"),
    "publication_gate_route_back_write_required": _write_entry(
        "DM003:blocked_gate_replay_route_back_write"
    ),
    "claim_evidence_alignment_required": _entry(
        owner="write",
        allowed_actions=["run_quality_repair_batch"],
        required_output=(
            "claim-evidence map and evidence ledger alignment or "
            "typed blocker:claim_evidence_alignment_required"
        ),
        priority_class="write_route_back",
        regression_refs=("DM002:claim_evidence_alignment",),
    ),
    "run_quality_repair_batch": _write_entry("tests:legacy_action_reason_write_route"),
    "publication_owner_materialization_required": _gate_clearing_entry(
        "DM002:current_ai_reviewer_materialization"
    ),
    "owner_authorized_publication_gate_replay": _gate_clearing_entry(
        "DM003:owner_authorized_publication_gate_replay"
    ),
    "domain_transition_publication_gate_blocker": _gate_clearing_entry(
        "DM003:domain_transition_publication_gate_blocker"
    ),
    "run_gate_clearing_batch": _gate_clearing_entry("tests:legacy_action_reason_gate_clearing"),
    "quest_waiting_opl_runtime_owner_route": _write_entry("DM002:runtime_redrive_route_back"),
    "controller_decision_route_back": _entry(
        owner="owner_route_next_owner",
        allowed_actions=["run_quality_repair_batch", "return_to_ai_reviewer_workflow"],
        required_output="owner-specific receipt or typed blocker",
        priority_class="write_route_back",
        regression_refs=("tests/owner_route_reconcile_cases",),
        allow_route_action=True,
    ),
    "controller_work_unit_owner_handoff_required": _entry(
        owner="owner_route_next_owner",
        allowed_actions=[
            "return_to_ai_reviewer_workflow",
            "run_quality_repair_batch",
            "publication_gate_specificity_required",
        ],
        required_output="owner-specific receipt or typed blocker",
        priority_class="delivery_or_human_handoff",
        regression_refs=("tests/owner_route_reconcile_cases",),
        allow_route_action=True,
    ),
    "publication_gate_specificity_required": _entry(
        owner="publication_gate",
        allowed_actions=["publication_gate_specificity_required"],
        required_output="artifacts/publication_eval/latest.json",
        priority_class="delivery_or_human_handoff",
        regression_refs=("DM002:publication_gate_specificity",),
    ),
    "gate_needs_specificity": _entry(
        owner="publication_gate",
        allowed_actions=["publication_gate_specificity_required"],
        required_output="specific publication gate blocker target refs",
        priority_class="delivery_or_human_handoff",
        regression_refs=("tests/owner_route_reconcile_cases",),
    ),
    "current_package_freshness_required": _artifact_entry("DM002:package_freshness"),
    "artifact_work_required": _artifact_entry("tests:artifact_owner_route"),
    "display_surface_materialization_failed": _artifact_entry(),
    "canonical_paper_inputs_rehydrate_required": _entry(
        owner="write",
        allowed_actions=["canonical_paper_inputs_rehydrate_required"],
        required_output="paper/medical_manuscript_blueprint_source.json",
        priority_class="write_route_back",
        regression_refs=("tests/domain_action_request_materializer_cases",),
    ),
    "unit_harmonized_rerun_required": _entry(
        owner="analysis_harmonization_owner",
        allowed_actions=["unit_harmonized_external_validation_rerun"],
        required_output=(
            "unit-harmonized external-validation rerun evidence or "
            "typed blocker:unit_harmonized_rerun_required"
        ),
        priority_class="hard_methodology_or_source_blocker",
        regression_refs=("DM002:unit_harmonized_rerun",),
    ),
    "unit_harmonized_external_validation_rerun": _entry(
        owner="analysis_harmonization_owner",
        allowed_actions=["unit_harmonized_external_validation_rerun"],
        required_output=(
            "unit-harmonized external-validation rerun evidence or "
            "typed blocker:unit_harmonized_rerun_required"
        ),
        priority_class="hard_methodology_or_source_blocker",
        regression_refs=("DM002:managed_runtime_unit_harmonized_rerun",),
    ),
    "transport_model_provenance_recovery_required": _entry(
        owner="source_provenance_owner",
        allowed_actions=["recover_transport_model_provenance"],
        required_output=(
            "canonical transport model provenance bundle or "
            "typed blocker:transport_model_provenance_recovery_required"
        ),
        priority_class="hard_methodology_or_source_blocker",
        regression_refs=("DM002:transport_model_provenance",),
    ),
    "recover_transport_model_provenance": _entry(
        owner="source_provenance_owner",
        allowed_actions=["recover_transport_model_provenance"],
        required_output=(
            "canonical transport model provenance bundle or "
            "typed blocker:transport_model_provenance_recovery_required"
        ),
        priority_class="hard_methodology_or_source_blocker",
        regression_refs=("DM002:transport_model_provenance",),
    ),
    "methodology_reframe_required": _entry(
        owner="decision",
        allowed_actions=["methodology_reframe_route_decision"],
        required_output="controller route decision for methodology reframe",
        priority_class="hard_methodology_or_source_blocker",
        regression_refs=("DM002:methodology_reframe",),
    ),
    "provenance_limited_harmonization_audit_required": _entry(
        owner="provenance_limited_harmonization_owner",
        allowed_actions=["provenance_limited_harmonization_audit"],
        required_output=(
            "provenance-limited harmonization audit or "
            "typed blocker:provenance_limited_harmonization_audit_required"
        ),
        priority_class="hard_methodology_or_source_blocker",
        regression_refs=("DM002:provenance_limited_harmonization",),
    ),
    "paper_authority_clean_migration_required": _entry(
        owner="ai_reviewer",
        allowed_actions=["return_to_ai_reviewer_workflow"],
        required_output="new MAS paper authority surface or typed blocker",
        priority_class="ai_reviewer_currentness",
        regression_refs=("tests/owner_route_reconcile_cases",),
    ),
    "study_completion_contract_not_ready": _entry(
        owner="controller_stop",
        allowed_actions=[],
        required_output="study completion contract blocker",
        priority_class="delivery_or_human_handoff",
        regression_refs=("tests/owner_route_reconcile_cases",),
    ),
    "runtime_controller_redrive_required": _entry(
        owner="one-person-lab",
        allowed_actions=[],
        required_output="OPL stage attempt admission or typed blocker",
        priority_class="delivery_or_human_handoff",
        regression_refs=("tests/owner_route_reconcile_cases",),
    ),
    "runtime_recovery_not_authorized": _entry(
        owner="one-person-lab",
        allowed_actions=[],
        required_output="OPL stage attempt admission or typed blocker",
        priority_class="delivery_or_human_handoff",
        regression_refs=("tests/owner_route_reconcile_cases",),
    ),
    "runtime_recovery_retry_budget_exhausted": _entry(
        owner="one-person-lab",
        allowed_actions=[],
        required_output="OPL stage attempt admission or typed blocker",
        priority_class="delivery_or_human_handoff",
        regression_refs=("tests/owner_route_reconcile_cases",),
    ),
    "abnormal_stopped_runtime_resume_required": _entry(
        owner="one-person-lab",
        allowed_actions=[],
        required_output="OPL runtime owner handoff or typed blocker",
        priority_class="delivery_or_human_handoff",
        regression_refs=("tests/owner_route_reconcile_cases/test_abnormal_stopped_runtime.py",),
    ),
    "failed_quest_runtime_relaunch_required": _entry(
        owner="one-person-lab",
        allowed_actions=[],
        required_output="OPL runtime owner handoff or typed blocker",
        priority_class="delivery_or_human_handoff",
        regression_refs=("tests/owner_route_reconcile_cases/test_failed_quest_autorepair.py",),
    ),
    "opl_runtime_owner_route_required": _entry(
        owner="one-person-lab",
        allowed_actions=[],
        required_output="OPL owner route transport receipt",
        priority_class="delivery_or_human_handoff",
        regression_refs=("tests/owner_route_reconcile_cases",),
    ),
    "typed_closeout_packet_required": _entry(
        owner="one-person-lab",
        allowed_actions=[],
        required_output="typed closeout packet with closeout refs",
        priority_class="delivery_or_human_handoff",
        regression_refs=("DM003:typed_closeout",),
    ),
    "owner_receipt_pending": _entry(
        owner="med-autoscience",
        allowed_actions=[],
        required_output="MAS owner receipt or stable typed blocker",
        priority_class="delivery_or_human_handoff",
        regression_refs=("DM003:owner_receipt",),
    ),
    "owner_chain_receipt_pending": _entry(
        owner="med-autoscience",
        allowed_actions=[],
        required_output="MAS owner receipt or stable typed blocker",
        priority_class="delivery_or_human_handoff",
        regression_refs=("DM003:owner_receipt",),
    ),
}

_ROUTED_ACTION_TYPES = (
    "publication_gate_specificity_required",
    "current_package_freshness_required",
    "artifact_display_surface_materialization_required",
    "return_to_ai_reviewer_workflow",
    "canonical_paper_inputs_rehydrate_required",
    "run_quality_repair_batch",
    "run_gate_clearing_batch",
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
    return default_executor_typed_closeout_contract(action_type=action_type or "domain_owner_action")


def _completion_boundary(
    *,
    required_closeout_packet: Mapping[str, Any],
    action_type: str | None,
) -> dict[str, Any]:
    boundary = _mapping(required_closeout_packet.get("completion_boundary"))
    if boundary:
        return dict(boundary)
    return default_executor_typed_closeout_contract(
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
            "queue_attempt_retry_liveness_owner": "one-person-lab",
            "domain_completion_owner": "med-autoscience",
        },
    }
    payload["missing_required_fields"] = _domain_intent_missing_fields(payload)
    return payload


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


def _authority_boundary() -> dict[str, list[str]]:
    return {
        "opl_owns": list(AUTHORITY_BOUNDARY["opl_owns"]),
        "mas_owns": list(AUTHORITY_BOUNDARY["mas_owns"]),
    }


def _runtime_completion_guard() -> dict[str, Any]:
    return {
        **{
            key: value
            for key, value in RUNTIME_COMPLETION_GUARD.items()
            if key != "domain_completion_requires"
        },
        "domain_completion_requires": list(RUNTIME_COMPLETION_GUARD["domain_completion_requires"]),
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


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "AUTHORITY_BOUNDARY",
    "PRIORITY_LATTICE",
    "PROTOCOL_VERSION",
    "RUNTIME_COMPLETION_GUARD",
    "closeout_packet_for_transport",
    "currentness_basis",
    "currentness_contract",
    "decorate_owner_route",
    "default_executor_attempt_envelope",
    "owner_reason_contract",
    "payload_fields_for_default_executor_dispatch",
    "route_protocol_dispatchable",
]
