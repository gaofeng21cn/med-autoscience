from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers.domain_action_request_materializer import (
    evidence_gap_decision as evidence_gap_decision_part,
    execution_gate,
    materializer_core,
    owner_callable_prompt,
    transition_projection_boundary,
)
from med_autoscience.controllers.owner_callable_closeout_contract import (
    owner_callable_typed_closeout_contract,
)
from med_autoscience.controllers.opl_execution_boundary import (
    first_trusted_opl_execution_authorization,
)
from med_autoscience.controllers.runtime_ai_repair_policy import (
    two_layer_ai_repair_policy_payload,
)
from med_autoscience.profiles import WorkspaceProfile


SourceActionRef = Callable[[Mapping[str, Any]], Mapping[str, Any]]
ScanLatestPath = Callable[[WorkspaceProfile], Path]
OwnerCallableSurface = Callable[[Mapping[str, Any]], str | None]


def mas_foreground_owner_callable_dispatch_payload(
    *,
    profile: WorkspaceProfile,
    action: Mapping[str, Any],
    action_type: str,
    study_id: str,
    dispatch_path: Path,
    executor_policy: Mapping[str, Any],
    next_executable_owner: str,
    required_output_surface: str,
    owner_route: Mapping[str, Any],
    idempotency_key: str | None,
    repeat_key: str | None,
    typed_closeout_contract: Mapping[str, Any],
    owner_route_attempt_envelope: Mapping[str, Any],
    prompt_contract: Mapping[str, Any],
    readiness_dispatch: Mapping[str, Any],
    evidence_gap_projection: Mapping[str, Any],
    progress_first_closeout_admission: Mapping[str, Any],
    generated_at: str,
    schema_version: int,
    owner_callable_adapter_kind: str,
    target_runtime_owner: str,
    source_action_ref: SourceActionRef,
    owner_callable_surface: OwnerCallableSurface,
    scan_latest_path: ScanLatestPath,
) -> dict[str, Any]:
    payload = owner_callable_dispatch_payload(
        profile=profile,
        action=action,
        action_type=action_type,
        study_id=study_id,
        dispatch_path=dispatch_path,
        executor_policy=executor_policy,
        next_executable_owner=next_executable_owner,
        required_output_surface=required_output_surface,
        owner_route=owner_route,
        idempotency_key=idempotency_key,
        repeat_key=repeat_key,
        dispatch_status="dry_run",
        blocked_reason=None,
        repeat_guard={"repeat_suppressed": False, "why_not_applied": None},
        typed_closeout_contract=typed_closeout_contract,
        owner_route_attempt_envelope=owner_route_attempt_envelope,
        prompt_contract=prompt_contract,
        readiness_dispatch=readiness_dispatch,
        evidence_gap_projection=evidence_gap_projection,
        progress_first_closeout_admission=progress_first_closeout_admission,
        generated_at=generated_at,
        schema_version=schema_version,
        owner_callable_adapter_kind=owner_callable_adapter_kind,
        target_runtime_owner=target_runtime_owner,
        source_action_ref=source_action_ref,
        scan_latest_path=scan_latest_path,
    )
    prompt = dict(materializer_core.mapping(payload.get("prompt_contract")))
    prompt["owner_callable_execution_mode"] = "mas_foreground"
    prompt["provider_admission_requires_opl_runtime_result"] = False
    prompt["provider_attempt_or_lease_required"] = False
    prompt["opl_transition_runtime_required"] = False
    prompt["target_runtime_owner"] = "med-autoscience"
    payload.update(
        {
            "owner_callable_execution_mode": "mas_foreground",
            "adapter_kind": "mas_foreground_owner_callable_adapter",
            "target_runtime_owner": "med-autoscience",
            "target_runtime_owner_authority_required": True,
            "mas_dispatch_authority": False,
            "dispatch_ready_for_execution_authority": False,
            "provider_admission_pending": False,
            "provider_admission_requires_opl_runtime_result": False,
            "provider_attempt_or_lease_required": False,
            "opl_transition_runtime_required": False,
            "opl_transition_runtime_required_for_durable_carrier": False,
            "owner_callable_surface": owner_callable_surface(action),
            "dispatch_authority": "mas_foreground_owner_callable_projection",
            "consumer_mutation_scope": "mas_foreground_owner_callable_projection_only",
            "prompt_contract": prompt,
        }
    )
    return payload


def owner_callable_dispatch_payload(
    *,
    profile: WorkspaceProfile,
    action: Mapping[str, Any],
    action_type: str,
    study_id: str,
    dispatch_path: Path,
    executor_policy: Mapping[str, Any],
    next_executable_owner: str,
    required_output_surface: str,
    owner_route: Mapping[str, Any],
    idempotency_key: str | None,
    repeat_key: str | None,
    dispatch_status: str,
    blocked_reason: str | None,
    repeat_guard: Mapping[str, Any],
    typed_closeout_contract: Mapping[str, Any],
    owner_route_attempt_envelope: Mapping[str, Any],
    prompt_contract: Mapping[str, Any],
    readiness_dispatch: Mapping[str, Any],
    evidence_gap_projection: Mapping[str, Any],
    progress_first_closeout_admission: Mapping[str, Any],
    generated_at: str,
    schema_version: int,
    owner_callable_adapter_kind: str,
    target_runtime_owner: str,
    source_action_ref: SourceActionRef,
    scan_latest_path: ScanLatestPath,
) -> dict[str, Any]:
    opl_execution_authorization = first_trusted_opl_execution_authorization(
        action.get("opl_execution_authorization"),
        prompt_contract.get("opl_execution_authorization"),
        owner_route.get("opl_execution_authorization"),
        materializer_core.mapping(owner_route.get("source_refs")).get(
            "opl_execution_authorization"
        ),
    )
    authorization_required = target_runtime_owner == "one-person-lab"
    adapter_contract = _owner_callable_adapter_contract(
        action_type=action_type,
        next_executable_owner=next_executable_owner,
        required_output_surface=required_output_surface,
        schema_version=schema_version,
        owner_callable_adapter_kind=owner_callable_adapter_kind,
        target_runtime_owner=target_runtime_owner,
    )
    text = materializer_core.text
    mapping = materializer_core.mapping
    return {
        "surface": "mas_domain_progress_transition_request_projection",
        "schema_version": schema_version,
        "adapter_kind": owner_callable_adapter_kind,
        "adapter_status": "intent_materialized",
        "domain_intent_kind": "mas_owner_callable_transition_request",
        "target_runtime_owner": target_runtime_owner,
        "target_runtime_owner_authority_required": True,
        "mas_creates_opl_outbox": False,
        "mas_creates_opl_event": False,
        "mas_creates_opl_stage_run": False,
        "mas_dispatch_authority": False,
        "dispatch_ready_for_execution_authority": False,
        "owner_callable_adapter_contract": adapter_contract,
        "authority_boundary": {
            **transition_projection_boundary.authority_boundary(),
        },
        **dict(executor_policy),
        "study_id": study_id,
        "quest_id": prompt_contract["quest_id"],
        "generated_at": generated_at,
        "action_type": action_type,
        "action_id": text(action.get("action_id")),
        "dispatch_authority": _dispatch_authority_for_action(action, prompt_contract=prompt_contract),
        "next_executable_owner": next_executable_owner,
        "required_output_surface": required_output_surface,
        "work_unit_id": text(action.get("work_unit_id")) or text(action.get("next_work_unit")),
        "work_unit_fingerprint": text(action.get("work_unit_fingerprint"))
        or text(action.get("action_fingerprint")),
        **dict(readiness_dispatch),
        **(
            {"required_output_target_surface": dict(prompt_contract["required_output_target_surface"])}
            if "required_output_target_surface" in prompt_contract
            else {}
        ),
        "owner_route": owner_route or None,
        "idempotency_key": idempotency_key,
        "repeat_suppression_key": repeat_key,
        "action_fingerprint": text(action.get("action_fingerprint")),
        "paper_progress_stall": mapping(action.get("paper_progress_stall")) or None,
        "dispatch_status": dispatch_status,
        "blocked_reason": blocked_reason,
        "execution_gate": execution_gate.projection(
            dispatch_status=dispatch_status,
            blocked_reason=blocked_reason,
            opl_execution_authorization=opl_execution_authorization,
            evidence_gap_projection=evidence_gap_projection,
            authorization_required=authorization_required,
        ),
        "evidence_gap_decisions": list(evidence_gap_projection.get("evidence_gap_decisions") or []),
        "evidence_gap_decision_summary": dict(mapping(evidence_gap_projection.get("evidence_gap_decision_summary"))),
        "current_action_can_continue": (
            mapping(evidence_gap_projection.get("evidence_gap_decision_summary")).get(
                "current_action_can_continue"
            )
            is True
        ),
        "forbidden_claims": list(
            mapping(evidence_gap_projection.get("evidence_gap_decision_summary")).get("forbidden_claims")
            or []
        ),
        "assumption_ledger": list(evidence_gap_projection.get("assumption_ledger") or []),
        "soft_gap_ledger": list(evidence_gap_projection.get("soft_gap_ledger") or []),
        "observability_backlog": list(evidence_gap_projection.get("observability_backlog") or []),
        "evidence_tail_ledger": list(evidence_gap_projection.get("evidence_tail_ledger") or []),
        "evidence_gap_typed_blockers": list(evidence_gap_projection.get("evidence_gap_typed_blockers") or []),
        "evidence_gap_typed_blocker_count": int(
            evidence_gap_projection.get("evidence_gap_typed_blocker_count") or 0
        ),
        "provider_admission_effect": execution_gate.provider_admission_effect(
            dispatch_status=dispatch_status,
            opl_execution_authorization=opl_execution_authorization,
            authorization_required=authorization_required,
        ),
        "opl_execution_authorization": dict(opl_execution_authorization or {}),
        "opl_transition_runtime_postcondition": transition_projection_boundary.runtime_postcondition(),
        "repeat_suppressed": bool(repeat_guard["repeat_suppressed"]),
        "why_not_applied": repeat_guard["why_not_applied"],
        "repeat_suppression": dict(repeat_guard),
        "consumer_mutation_scope": "domain_progress_transition_request_projection_only",
        "required_closeout_packet": dict(typed_closeout_contract),
        "owner_route_attempt_envelope": dict(owner_route_attempt_envelope),
        "terminal_output_instruction": typed_closeout_contract["terminal_output_instruction"],
        "owner_callable_policy": dict(executor_policy),
        "two_layer_ai_repair_policy": two_layer_ai_repair_policy_payload(),
        "prompt_contract": dict(prompt_contract),
        "domain_intent": _domain_intent(
            action=action,
            action_type=action_type,
            study_id=study_id,
            next_executable_owner=next_executable_owner,
            required_output_surface=required_output_surface,
            owner_route=owner_route,
            adapter_contract=adapter_contract,
            schema_version=schema_version,
            target_runtime_owner=target_runtime_owner,
        ),
        "progress_first_closeout_admission": dict(progress_first_closeout_admission),
        "executor_prompt": owner_callable_prompt.executor_prompt(
            action_type=action_type,
            study_id=study_id,
            next_executable_owner=next_executable_owner,
            required_output_surface=required_output_surface,
            typed_closeout_contract=owner_callable_typed_closeout_contract,
        ),
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": False,
        "source_action": dict(source_action_ref(action)),
        "source_action_runtime_completion_fields_omitted": sorted(
            key for key in action if key in _RUNTIME_COMPLETION_SOURCE_ACTION_FIELDS
        ),
        "refs": {
            "scan_latest": str(scan_latest_path(profile)),
            "dispatch_path": str(dispatch_path),
        },
    }


def _dispatch_authority_for_action(
    action: Mapping[str, Any],
    *,
    prompt_contract: Mapping[str, Any],
) -> str | None:
    handoff = materializer_core.mapping(action.get("handoff_packet"))
    return (
        materializer_core.text(action.get("dispatch_authority"))
        or materializer_core.text(handoff.get("dispatch_authority"))
        or materializer_core.text(prompt_contract.get("dispatch_authority"))
    )


def _owner_callable_adapter_contract(
    *,
    action_type: str,
    next_executable_owner: str,
    required_output_surface: str,
    schema_version: int,
    owner_callable_adapter_kind: str,
    target_runtime_owner: str,
) -> dict[str, Any]:
    return {
        "surface": "mas_owner_callable_adapter_contract",
        "schema_version": schema_version,
        "adapter_kind": owner_callable_adapter_kind,
        "action_type": action_type,
        "next_executable_owner": next_executable_owner,
        "required_output_surface": required_output_surface,
        "target_runtime_owner": target_runtime_owner,
        "execution_authority_owner": target_runtime_owner,
        "required_opl_proof": [
            "opl_execution_authorization",
            "opl_provider_attempt",
            "attempt_lease",
            "closeout_binding",
            "accepted_owner_gate_authority",
        ],
        "mas_private_outbox_forbidden": True,
        "mas_private_dispatch_authority_forbidden": True,
        "mas_stage_run_creation_forbidden": True,
        "provider_completion_is_domain_completion": False,
    }


def _domain_intent(
    *,
    action: Mapping[str, Any],
    action_type: str,
    study_id: str,
    next_executable_owner: str,
    required_output_surface: str,
    owner_route: Mapping[str, Any],
    adapter_contract: Mapping[str, Any],
    schema_version: int,
    target_runtime_owner: str,
) -> dict[str, Any]:
    text = materializer_core.text
    mapping = materializer_core.mapping
    return {
        "surface": "mas_domain_intent",
        "schema_version": schema_version,
        "intent_kind": "owner_callable_transition_request",
        "study_id": study_id,
        "quest_id": text(action.get("quest_id")) or text(mapping(action.get("handoff_packet")).get("quest_id")),
        "action_type": action_type,
        "next_executable_owner": next_executable_owner,
        "required_output_surface": required_output_surface,
        "work_unit_id": text(action.get("work_unit_id")) or text(action.get("next_work_unit")),
        "work_unit_fingerprint": text(action.get("work_unit_fingerprint"))
        or text(action.get("action_fingerprint")),
        "target_runtime_owner": target_runtime_owner,
        "target_runtime_transition": "OPL Command/Event/Outbox/StageRun",
        "expected_domain_answer": "MAS OwnerAnswer",
        "expected_projection": "Derived Projection",
        "mas_creates_opl_outbox": False,
        "mas_creates_opl_event": False,
        "mas_creates_opl_stage_run": False,
        "opl_transition_runtime_postcondition": transition_projection_boundary.runtime_postcondition(),
        "owner_route": dict(owner_route) if owner_route else None,
        "adapter_contract": dict(adapter_contract),
    }


_RUNTIME_COMPLETION_SOURCE_ACTION_FIELDS = frozenset(
    {
        "provider_completion",
        "running_worker",
        "queue_status",
        "retry_budget_remaining",
        "domain_completion",
        "stage_state",
        "provider_completion_is_domain_completion",
        "provider_completion_is_stage_state",
        "queue_succeeded_is_domain_completion",
        "retry_budget_is_domain_completion",
        "running_worker_is_stage_state",
    }
)


__all__ = [
    "mas_foreground_owner_callable_dispatch_payload",
    "owner_callable_dispatch_payload",
]
