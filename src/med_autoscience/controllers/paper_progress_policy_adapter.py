from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.domain_health_diagnostic_parts.opl_transition_readback import (
    required_opl_transition_readback_shape,
)
from med_autoscience.controllers.domain_action_request_materializer_parts.currentness_identity import (
    normalize_currentness_sources,
)

SURFACE_KIND = "paper_progress_policy_adapter_result"
SCHEMA_VERSION = 1
AUTHORITY = "med_autoscience.paper_progress_policy_adapter"

START_PROVIDER_ATTEMPT = "StartProviderAttempt"
MATERIALIZE_OWNER_ACTION = "MaterializeOwnerAction"
CONSUME_OWNER_RECEIPT = "ConsumeOwnerReceipt"
RECORD_TYPED_BLOCKER = "RecordTypedBlocker"
OPEN_HUMAN_GATE = "OpenHumanGate"
ADOPT_ROUTE_BACK_EVIDENCE = "AdoptRouteBackEvidence"
ADOPT_PAPER_DELTA = "AdoptPaperDelta"
STOP_LOSS = "StopLoss"
NON_ADVANCING_APPLY = "NonAdvancingApply"

FORBIDDEN_RUNTIME_FIELDS = [
    "current_control_command",
    "current_control_command_outbox_record",
    "opl_domain_progress_command",
    "opl_domain_progress_command_outbox_record",
    "opl_domain_progress_transition_event",
    "opl_domain_progress_transition_outbox_item",
    "opl_event_log_record",
    "opl_outbox_record",
    "projection_metadata",
    "read_model_generation_metadata",
    "stage_run",
    "stage_run_identity",
    "fixed_point_reconciler_state",
]

_PROVIDER_ADMISSION_NEXT_KINDS = {
    "admit_provider_attempt",
    "admit_identity_bound_stage_packet",
}
_OWNER_ACTION_NEXT_KINDS = {
    "run_mas_owner_callable",
    "materialize_mas_transition_request_or_owner_callable",
    "materialize_successor_owner_action",
    "materialize_successor_owner_gate",
    "resolve_owner_gate_decision",
    "route_back_to_owner_or_repair_materialization",
}


def build_policy_result(payload: Mapping[str, Any], *, source: str = "paper_progress") -> dict[str, Any]:
    current_work_unit = _mapping(payload.get("current_work_unit"))
    current_action = _mapping(payload.get("current_executable_owner_action"))
    recovery = _mapping(payload.get("paper_recovery_state"))
    next_action = _mapping(recovery.get("next_safe_action"))
    policy_kind = _policy_kind(
        payload=payload,
        current_work_unit=current_work_unit,
        current_action=current_action,
        recovery=recovery,
        next_action=next_action,
    )
    if policy_kind is None:
        return {}
    identity = _identity(
        payload=payload,
        current_work_unit=current_work_unit,
        current_action=current_action,
        recovery=recovery,
        next_action=next_action,
    )
    result = {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "authority": AUTHORITY,
        "authority_role": "paper_domain_policy_adapter_only",
        "source": source,
        "policy_result_id": _stable_id("paper-policy", [policy_kind, identity]),
        "recommended_opl_transition_kind": policy_kind,
        "policy_outcome_kind": _policy_outcome_kind(policy_kind),
        "study_id": identity.get("study_id"),
        "quest_id": identity.get("quest_id"),
        "owner": identity.get("owner"),
        "action_type": identity.get("action_type"),
        "work_unit_id": identity.get("work_unit_id"),
        "work_unit_fingerprint": identity.get("work_unit_fingerprint"),
        "provider_completion_is_domain_completion": False,
        "projection_metadata": _projection_metadata(identity),
        "paper_policy_verdict": _paper_policy_verdict(
            policy_kind,
            payload=payload,
            current_work_unit=current_work_unit,
            current_action=current_action,
            recovery=recovery,
            next_action=next_action,
        ),
        "opl_domain_progress_transition_request": _opl_domain_progress_transition_request(
            policy_kind=policy_kind,
            identity=identity,
        ),
        "authority_boundary": {
            "mas_can_accept_owner_receipt": True,
            "mas_can_create_domain_typed_blocker": True,
            "mas_can_authorize_paper_delta": True,
            "mas_can_authorize_provider_admission": False,
            "mas_can_run_fixed_point_reconciler": False,
            "mas_can_own_event_log_or_outbox": False,
            "mas_can_append_opl_event_log": False,
            "mas_can_emit_opl_outbox_item": False,
            "mas_can_create_opl_outbox_record": False,
            "mas_can_create_opl_event": False,
            "mas_can_create_opl_stage_run": False,
            "opl_owns_transition_runtime": True,
            "provider_completion_is_domain_completion": False,
        },
        "forbidden_runtime_fields": list(FORBIDDEN_RUNTIME_FIELDS),
        "forbidden_writes": [
            "publication_ready_claim_without_mas_gate",
            "paper_artifact_mutation_without_mas_authority",
            "owner_receipt_created_by_opl",
            "typed_blocker_created_by_opl",
            "provider_completion_as_paper_ready",
        ],
    }
    return _clean(result)


def build_non_advancing_policy_blocker(
    payload: Mapping[str, Any],
    *,
    reason: str = "fresh_readback_did_not_advance_same_aggregate",
) -> dict[str, Any]:
    result = build_policy_result(payload, source="paper_progress.non_advancing_apply")
    if not result:
        identity = _identity(
            payload=payload,
            current_work_unit=_mapping(payload.get("current_work_unit")),
            current_action=_mapping(payload.get("current_executable_owner_action")),
            recovery=_mapping(payload.get("paper_recovery_state")),
            next_action=_mapping(_mapping(payload.get("paper_recovery_state")).get("next_safe_action")),
        )
        result = {
            "surface_kind": SURFACE_KIND,
            "schema_version": SCHEMA_VERSION,
            "authority": AUTHORITY,
            "authority_role": "paper_domain_policy_adapter_only",
            "policy_result_id": _stable_id("paper-policy", [NON_ADVANCING_APPLY, identity]),
            "recommended_opl_transition_kind": NON_ADVANCING_APPLY,
            "policy_outcome_kind": _policy_outcome_kind(NON_ADVANCING_APPLY),
            "study_id": identity.get("study_id"),
            "quest_id": identity.get("quest_id"),
            "owner": identity.get("owner"),
            "action_type": identity.get("action_type"),
            "work_unit_id": identity.get("work_unit_id"),
            "work_unit_fingerprint": identity.get("work_unit_fingerprint"),
            "provider_completion_is_domain_completion": False,
            "projection_metadata": _projection_metadata(identity),
            "authority_boundary": {
                "mas_can_accept_owner_receipt": True,
                "mas_can_create_domain_typed_blocker": True,
                "mas_can_authorize_paper_delta": True,
                "mas_can_authorize_provider_admission": False,
                "mas_can_run_fixed_point_reconciler": False,
                "mas_can_own_event_log_or_outbox": False,
                "mas_can_append_opl_event_log": False,
                "mas_can_emit_opl_outbox_item": False,
                "mas_can_create_opl_outbox_record": False,
                "mas_can_create_opl_event": False,
                "mas_can_create_opl_stage_run": False,
                "opl_owns_transition_runtime": True,
                "provider_completion_is_domain_completion": False,
            },
        }
    result["paper_policy_verdict"] = {
        "verdict": "stable_typed_blocker_required",
        "typed_blocker_type": "non_advancing_apply",
        "reason": reason,
    }
    result["recommended_opl_transition_kind"] = NON_ADVANCING_APPLY
    result["policy_outcome_kind"] = _policy_outcome_kind(NON_ADVANCING_APPLY)
    result["opl_domain_progress_transition_request"] = _opl_domain_progress_transition_request(
        policy_kind=NON_ADVANCING_APPLY,
        identity=_identity(
            payload=payload,
            current_work_unit=_mapping(payload.get("current_work_unit")),
            current_action=_mapping(payload.get("current_executable_owner_action")),
            recovery=_mapping(payload.get("paper_recovery_state")),
            next_action=_mapping(_mapping(payload.get("paper_recovery_state")).get("next_safe_action")),
        ),
    )
    result["forbidden_runtime_fields"] = list(FORBIDDEN_RUNTIME_FIELDS)
    return _clean(result)


def build_transition_request(
    *,
    study_id: str,
    action_type: str,
    quest_id: str | None = None,
    work_unit_id: str | None = None,
    work_unit_fingerprint: str | None = None,
    next_owner: str | None = None,
    policy_kind: str = MATERIALIZE_OWNER_ACTION,
    source_generation: str | None = None,
    expected_version: str | None = None,
    dispatch_ref: str | None = None,
    dispatch_authority: str | None = None,
    required_output_surface: str | None = None,
    currentness_basis: Mapping[str, Any] | None = None,
    idempotency_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the MAS policy-adapter request consumed by OPL transition runtime."""
    normalized_currentness_basis = normalize_currentness_sources(currentness_basis)
    identity = _clean(
        {
            "study_id": study_id,
            "quest_id": quest_id or study_id,
            "owner": next_owner,
            "action_type": action_type,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
            "source_generation": source_generation or work_unit_fingerprint,
            "observed_generation": source_generation or work_unit_fingerprint,
        }
    )
    request = _opl_domain_progress_transition_request(
        policy_kind=policy_kind,
        identity=identity,
    )
    if expected_version is not None:
        request["expected_version"] = expected_version
    if idempotency_context:
        request["idempotency_key"] = _stable_id(
            "paper-policy-request",
            [policy_kind, identity, dict(idempotency_context)],
        )
    request.update(
        _clean(
            {
                "dispatch_ref": dispatch_ref,
                "dispatch_authority": dispatch_authority,
                "required_output_surface": required_output_surface,
                "currentness_basis": normalized_currentness_basis,
                "action_fingerprint": work_unit_fingerprint,
            }
        )
    )
    return _clean(request)


def _policy_kind(
    *,
    payload: Mapping[str, Any],
    current_work_unit: Mapping[str, Any],
    current_action: Mapping[str, Any],
    recovery: Mapping[str, Any],
    next_action: Mapping[str, Any],
) -> str | None:
    status = _text(current_work_unit.get("status"))
    phase = _text(recovery.get("phase"))
    next_kind = _text(next_action.get("kind"))
    if _has_forbidden_write(
        payload=payload,
        current_work_unit=current_work_unit,
        recovery=recovery,
        next_action=next_action,
    ):
        return RECORD_TYPED_BLOCKER
    if _has_paper_delta(payload=payload, recovery=recovery, next_action=next_action):
        return ADOPT_PAPER_DELTA
    if next_kind in {"record_human_or_owner_gate", "wait_for_owner_with_resume_token"} or phase == "human_gate":
        return OPEN_HUMAN_GATE
    if next_kind == "route_back_to_owner_or_repair_materialization":
        return ADOPT_ROUTE_BACK_EVIDENCE
    if next_kind == "publish_stable_blocker_and_stop_same_identity_redrive":
        return STOP_LOSS
    if status in {"typed_blocker", "blocked_current_work_unit"} or _mapping(payload.get("typed_blocker")):
        return RECORD_TYPED_BLOCKER
    if (
        next_kind == "await_opl_transition_readback"
        and next_action.get("provider_admission_requires_opl_runtime_result") is True
    ):
        return START_PROVIDER_ATTEMPT
    if phase == "transition_request_pending":
        return START_PROVIDER_ATTEMPT
    if (
        next_kind in _PROVIDER_ADMISSION_NEXT_KINDS
        and next_action.get("provider_admission_allowed") is True
    ):
        return START_PROVIDER_ATTEMPT
    if phase == "admission_pending":
        return START_PROVIDER_ATTEMPT
    if next_kind == "materialize_successor_owner_action":
        return MATERIALIZE_OWNER_ACTION
    if status == "owner_receipt_recorded" or phase == "owner_receipt_recorded":
        return CONSUME_OWNER_RECEIPT
    if next_kind == "consume_owner_receipt":
        return CONSUME_OWNER_RECEIPT
    if status == "executable_owner_action" or current_action:
        return MATERIALIZE_OWNER_ACTION
    if next_kind in _OWNER_ACTION_NEXT_KINDS:
        return MATERIALIZE_OWNER_ACTION
    return None


def _policy_outcome_kind(policy_kind: str) -> str:
    return {
        START_PROVIDER_ATTEMPT: "provider_admission_requested",
        MATERIALIZE_OWNER_ACTION: "owner_action_requested",
        CONSUME_OWNER_RECEIPT: "owner_receipt",
        RECORD_TYPED_BLOCKER: "typed_blocker",
        OPEN_HUMAN_GATE: "human_gate",
        ADOPT_ROUTE_BACK_EVIDENCE: "route_back_evidence",
        ADOPT_PAPER_DELTA: "paper_delta",
        STOP_LOSS: "stop_loss_typed_blocker",
        NON_ADVANCING_APPLY: "non_advancing_apply_typed_blocker",
    }.get(policy_kind, "unknown")


def _paper_policy_verdict(
    policy_kind: str,
    *,
    payload: Mapping[str, Any],
    current_work_unit: Mapping[str, Any],
    current_action: Mapping[str, Any],
    recovery: Mapping[str, Any],
    next_action: Mapping[str, Any],
) -> dict[str, Any]:
    if _has_forbidden_write(
        payload=payload,
        current_work_unit=current_work_unit,
        recovery=recovery,
        next_action=next_action,
    ):
        return {
            "verdict": "forbidden_write_typed_blocker_required",
            "typed_blocker_type": "forbidden_write",
            "forbidden_write_refs": _forbidden_write_refs(
                payload=payload,
                current_work_unit=current_work_unit,
                recovery=recovery,
                next_action=next_action,
            ),
            "paper_progress_credit_allowed": False,
            "forbidden_write_blocks_domain_progress": True,
        }
    if policy_kind == START_PROVIDER_ATTEMPT:
        return {
            "verdict": "opl_provider_attempt_allowed_by_domain_policy",
            "provider_completion_is_domain_completion": False,
            "accepted_result_families": [
                "provider_admission_request",
                "opl_runtime_readback_required",
            ],
        }
    if policy_kind == MATERIALIZE_OWNER_ACTION:
        return {
            "verdict": "mas_owner_callable_required",
            "provider_admission_allowed": False,
        }
    if policy_kind == CONSUME_OWNER_RECEIPT:
        return {
            "verdict": "mas_owner_receipt_consumption_required",
            "owner_receipt_ref": _owner_receipt_ref(recovery=recovery, next_action=next_action),
            "paper_progress_credit_allowed": True,
        }
    if policy_kind == RECORD_TYPED_BLOCKER:
        return {
            "verdict": "stable_typed_blocker_required",
            "typed_blocker_ref": _typed_blocker_ref(
                payload=payload,
                current_work_unit=current_work_unit,
                recovery=recovery,
            ),
            "paper_progress_credit_allowed": True,
        }
    if policy_kind == OPEN_HUMAN_GATE:
        return {
            "verdict": "human_gate_required",
            "human_gate_ref": _first_text(next_action.get("human_gate_ref"), recovery.get("human_gate_ref")),
            "paper_progress_credit_allowed": True,
        }
    if policy_kind == ADOPT_ROUTE_BACK_EVIDENCE:
        return {
            "verdict": "route_back_evidence_required",
            "route_back_evidence_ref": _first_text(
                next_action.get("route_back_evidence_ref"),
                recovery.get("route_back_evidence_ref"),
            ),
            "paper_progress_credit_allowed": True,
        }
    if policy_kind == ADOPT_PAPER_DELTA:
        return {
            "verdict": "paper_gate_or_artifact_delta_required",
            "paper_delta_refs": _paper_delta_refs(
                payload=payload,
                recovery=recovery,
                next_action=next_action,
            ),
            "paper_progress_credit_allowed": True,
        }
    if policy_kind == STOP_LOSS:
        return {
            "verdict": "terminal_stop_loss_typed_blocker_required",
            "typed_blocker_type": "stop_loss",
            "paper_progress_credit_allowed": True,
        }
    return {"verdict": "non_advancing_apply_requires_typed_blocker"}


def _opl_domain_progress_transition_request(
    *,
    policy_kind: str,
    identity: Mapping[str, Any],
) -> dict[str, Any]:
    study_id = _text(identity.get("study_id"))
    work_unit_id = _text(identity.get("work_unit_id"))
    fingerprint = _text(identity.get("work_unit_fingerprint"))
    source_generation = _text(identity.get("source_generation")) or fingerprint
    request = {
        "surface_kind": "mas_domain_progress_transition_request",
        "target_runtime_kind": "DomainProgressTransitionRuntime",
        "target_runtime_owner": "one-person-lab",
        "request_owner": "med-autoscience",
        "authority_role": "domain_policy_request_only",
        "mas_can_create_opl_outbox_record": False,
        "mas_can_create_opl_event": False,
        "mas_can_create_opl_stage_run": False,
        "runtime_kind": "DomainProgressTransitionRuntime",
        "recommended_transition_kind": policy_kind,
        "aggregate_identity": {
            "aggregate_kind": "study_work_unit",
            "aggregate_id": "::".join(item for item in [study_id, work_unit_id] if item),
            "study_id": study_id,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
        },
        "study_id": study_id,
        "quest_id": identity.get("quest_id"),
        "action_type": identity.get("action_type"),
        "next_owner": identity.get("owner"),
        "idempotency_key": _stable_id("paper-policy-request", [policy_kind, identity]),
        "source_generation": source_generation,
        "expected_version": source_generation,
        "required_postcondition": {
            "kind": _postcondition_kind(policy_kind),
            "outcome_owner": "one-person-lab",
            "domain_state_owner": "med-autoscience",
        },
        "provider_admission_requires_opl_readback_shape": required_opl_transition_readback_shape(),
        "domain_policy_result_ref": _stable_id("paper-policy", [policy_kind, identity]),
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "forbidden_runtime_fields": list(FORBIDDEN_RUNTIME_FIELDS),
    }
    return _clean(request)


def _projection_metadata(identity: Mapping[str, Any]) -> dict[str, Any]:
    derived_from_event_id = _text(identity.get("derived_from_event_id"))
    observed_generation = _text(identity.get("observed_generation")) or _text(
        identity.get("source_generation")
    )
    return {
        "authority": False,
        "projection_owner": "med-autoscience",
        "fixed_point_runtime_owner": "one-person-lab",
        "derived_from_event_id": derived_from_event_id,
        "observed_generation": observed_generation,
        "lag_status": "current" if derived_from_event_id and observed_generation else "empty",
    }


def _postcondition_kind(policy_kind: str) -> str:
    if policy_kind == START_PROVIDER_ATTEMPT:
        return "provider_admission_enqueued_or_blocked"
    if policy_kind == MATERIALIZE_OWNER_ACTION:
        return "owner_action_ref"
    if policy_kind == CONSUME_OWNER_RECEIPT:
        return "owner_receipt_consumed"
    if policy_kind == RECORD_TYPED_BLOCKER:
        return "typed_blocker_ref"
    if policy_kind == OPEN_HUMAN_GATE:
        return "human_gate_ref"
    if policy_kind == ADOPT_ROUTE_BACK_EVIDENCE:
        return "route_back_evidence_ref"
    if policy_kind == ADOPT_PAPER_DELTA:
        return "paper_delta_refs"
    if policy_kind == STOP_LOSS:
        return "stable_stop_loss_typed_blocker_ref"
    return "non_advancing_apply_typed_blocker_ref"


def _identity(
    *,
    payload: Mapping[str, Any],
    current_work_unit: Mapping[str, Any],
    current_action: Mapping[str, Any],
    recovery: Mapping[str, Any],
    next_action: Mapping[str, Any],
) -> dict[str, Any]:
    successor = _mapping(next_action.get("successor_owner_action"))
    source_generation = _first_text(
        _mapping(current_work_unit.get("currentness_basis")).get("truth_epoch"),
        _mapping(current_action.get("owner_route_currentness_basis")).get("truth_epoch"),
        _mapping(current_action.get("currentness_basis")).get("truth_epoch"),
        current_action.get("source_eval_id"),
    )
    basis = (
        _mapping(current_work_unit.get("currentness_basis"))
        or _mapping(current_action.get("owner_route_currentness_basis"))
        or _mapping(current_action.get("currentness_basis"))
    )
    return _clean(
        {
            "study_id": _first_text(payload.get("study_id"), recovery.get("study_id")),
            "quest_id": _first_text(payload.get("quest_id"), recovery.get("quest_id")),
            "owner": _first_text(
                successor.get("owner"),
                next_action.get("owner"),
                current_action.get("next_owner"),
                current_action.get("owner"),
                current_work_unit.get("owner"),
            ),
            "action_type": _first_text(
                successor.get("action_type"),
                next_action.get("action_type"),
                current_action.get("action_type"),
                current_work_unit.get("action_type"),
            ),
            "work_unit_id": _first_text(
                successor.get("work_unit_id"),
                next_action.get("work_unit_id"),
                current_action.get("work_unit_id"),
                current_work_unit.get("work_unit_id"),
            ),
            "work_unit_fingerprint": _first_text(
                successor.get("work_unit_fingerprint"),
                next_action.get("work_unit_fingerprint"),
                current_action.get("work_unit_fingerprint"),
                current_action.get("action_fingerprint"),
                current_work_unit.get("work_unit_fingerprint"),
                current_work_unit.get("action_fingerprint"),
            ),
            "source_generation": source_generation,
            "derived_from_event_id": _first_text(
                basis.get("derived_from_event_id"),
                current_work_unit.get("derived_from_event_id"),
                current_action.get("derived_from_event_id"),
            ),
            "observed_generation": _first_text(
                basis.get("observed_generation"),
                current_work_unit.get("observed_generation"),
                current_action.get("observed_generation"),
                source_generation,
            ),
        }
    )


def _has_paper_delta(
    *,
    payload: Mapping[str, Any],
    recovery: Mapping[str, Any],
    next_action: Mapping[str, Any],
) -> bool:
    return bool(_paper_delta_refs(payload=payload, recovery=recovery, next_action=next_action))


def _paper_delta_refs(
    *,
    payload: Mapping[str, Any],
    recovery: Mapping[str, Any],
    next_action: Mapping[str, Any],
) -> list[str]:
    refs: list[str] = []
    for key in (
        "paper_delta_ref",
        "gate_delta_ref",
        "artifact_delta_ref",
        "publication_gate_delta_ref",
        "quality_gate_receipt_ref",
        "publication_gate_receipt_ref",
    ):
        for source in (next_action, recovery, payload):
            text = _text(source.get(key))
            if text is not None and text not in refs:
                refs.append(text)
    for key in (
        "paper_delta_refs",
        "gate_delta_refs",
        "artifact_delta_refs",
        "publication_gate_delta_refs",
        "quality_gate_receipt_refs",
        "evidence_refs",
    ):
        for source in (next_action, recovery, payload):
            for text in _text_items(source.get(key)):
                if (
                    text.startswith(
                        (
                            "paper_delta:",
                            "gate_delta:",
                            "artifact_delta:",
                            "quality_gate:",
                            "publication_gate:",
                        )
                    )
                    and text not in refs
                ):
                    refs.append(text)
    return refs


def _has_forbidden_write(
    *,
    payload: Mapping[str, Any],
    current_work_unit: Mapping[str, Any],
    recovery: Mapping[str, Any],
    next_action: Mapping[str, Any],
) -> bool:
    return any(
        source.get("forbidden_write_detected") is True
        for source in (next_action, recovery, current_work_unit, payload)
    ) or bool(
        _forbidden_write_refs(
            payload=payload,
            current_work_unit=current_work_unit,
            recovery=recovery,
            next_action=next_action,
        )
    )


def _forbidden_write_refs(
    *,
    payload: Mapping[str, Any],
    current_work_unit: Mapping[str, Any],
    recovery: Mapping[str, Any],
    next_action: Mapping[str, Any],
) -> list[str]:
    refs: list[str] = []
    for source in (next_action, recovery, current_work_unit, payload):
        for key in ("forbidden_write_ref", "forbidden_write_violation_ref"):
            text = _text(source.get(key))
            if text is not None and text not in refs:
                refs.append(text)
        for key in ("forbidden_write_refs", "forbidden_write_evidence_refs", "forbidden_write_violation_refs"):
            for text in _text_items(source.get(key)):
                if text not in refs:
                    refs.append(text)
        write = _mapping(source.get("forbidden_write")) or _mapping(source.get("forbidden_write_violation"))
        for key in ("ref", "source_ref", "proof_ref", "write_ref", "forbidden_write_ref"):
            text = _text(write.get(key))
            if text is not None and text not in refs:
                refs.append(text)
        if source.get("forbidden_write_detected") is True and not refs:
            refs.append("forbidden_write:detected")
    return refs


def _owner_receipt_ref(
    *,
    recovery: Mapping[str, Any],
    next_action: Mapping[str, Any],
) -> str | None:
    return _first_text(
        next_action.get("owner_receipt_ref"),
        recovery.get("owner_receipt_ref"),
        *_matching_ref_items(recovery.get("evidence_refs"), prefix="owner_receipt:"),
    )


def _typed_blocker_ref(
    *,
    payload: Mapping[str, Any],
    current_work_unit: Mapping[str, Any],
    recovery: Mapping[str, Any],
) -> str | None:
    state = _mapping(current_work_unit.get("state"))
    typed_blocker = (
        _mapping(state.get("typed_blocker"))
        or _mapping(current_work_unit.get("typed_blocker"))
        or _mapping(payload.get("typed_blocker"))
    )
    return _first_text(
        typed_blocker.get("typed_blocker_ref"),
        typed_blocker.get("latest_owner_answer_ref"),
        typed_blocker.get("source_ref"),
        *_matching_ref_items(recovery.get("evidence_refs"), prefix="typed_blocker:"),
    )


def _matching_ref_items(value: object, *, prefix: str) -> list[str]:
    return [text for text in _text_items(value) if text.startswith(prefix)]


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _first_text(*values: object) -> str | None:
    for value in values:
        text = _text(value)
        if text is not None:
            return text
    return None


def _text_items(values: object) -> list[str]:
    if isinstance(values, str):
        text = _text(values)
        return [text] if text is not None else []
    if not isinstance(values, (list, tuple, set)):
        return []
    return [text for value in values if (text := _text(value)) is not None]


def _stable_id(prefix: str, parts: object) -> str:
    digest = hashlib.sha256(
        json.dumps(parts, ensure_ascii=True, sort_keys=True).encode("utf-8")
    ).hexdigest()[:24]
    return f"{prefix}:{digest}"


def _clean(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if value not in (None, "", [], {})}
