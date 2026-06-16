from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from med_autoscience.runtime_control.owner_callable_registry import owner_callable_registry

from .paper_progress_state import build_paper_progress_state
from .paper_progress_transition_refs import record_paper_progress_transition_ref


SCHEMA_VERSION = 1
SURFACE = "paper_progress_reconcile_receipt"


def build_paper_progress_reconcile_receipt(
    *,
    profile: Any,
    requested_study_ids: Iterable[str],
    resolved_study_ids: Iterable[str],
    before_scan: Mapping[str, Any],
    consumed: Mapping[str, Any],
    executed: Mapping[str, Any],
    after_scan: Mapping[str, Any],
    apply: bool,
    generated_at: str,
) -> dict[str, Any]:
    resolved = tuple(dict.fromkeys(item for item in (_text(value) for value in resolved_study_ids) if item))
    decisions = [
        _decision_for_study(
            profile=profile,
            study_id=study_id,
            before_study=_study(before_scan, study_id),
            after_study=_study(after_scan, study_id),
            consumed=consumed,
            executed=executed,
            apply=apply,
            generated_at=generated_at,
        )
        for study_id in resolved
    ]
    return {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "workspace_root": str(profile.workspace_root),
        "dry_run": not apply,
        "requested_studies": [item for item in (_text(value) for value in requested_study_ids) if item],
        "resolved_studies": list(resolved),
        "decision_count": len(decisions),
        "apply_eligible_count": sum(item.get("apply_eligible") is True for item in decisions),
        "action_receipt_count": sum(
            _mapping(item.get("action_receipt")).get("receipt_status")
            not in {None, "dry_run_not_recorded", "not_callable", "not_executed"}
            for item in decisions
        ),
        "decisions": decisions,
    }


def _decision_for_study(
    *,
    profile: Any,
    study_id: str,
    before_study: Mapping[str, Any],
    after_study: Mapping[str, Any],
    consumed: Mapping[str, Any],
    executed: Mapping[str, Any],
    apply: bool,
    generated_at: str,
) -> dict[str, Any]:
    current_study = dict(after_study or before_study)
    current_state = build_paper_progress_state(current_study)
    desired_state = _desired_state(current_state, current_study)
    delta = _delta(current_state=current_state, desired_state=desired_state)
    decision = _decision(current_state=current_state, desired_state=desired_state, study=current_study)
    callable_contract = _callable_contract(desired_state)
    execution = _matching_execution(executed, study_id=study_id, action_type=_text(desired_state.get("action_type")))
    execution_status = _text(_mapping(execution).get("execution_status"))
    apply_eligible = bool(
        apply
        and callable_contract is not None
        and current_state.get("requires_user_input") is not True
        and _text(desired_state.get("source_fingerprint")) is not None
        and execution_status == "executed"
    )
    action_receipt = _action_receipt(
        profile=profile,
        study=current_study,
        desired_state=desired_state,
        callable_contract=callable_contract,
        execution=execution,
        reconcile_apply_requested=apply,
        apply=apply_eligible,
        generated_at=generated_at,
    )
    return {
        "surface": "paper_progress_reconcile_decision",
        "schema_version": SCHEMA_VERSION,
        "study_id": study_id,
        "quest_id": _quest_id(current_study, study_id),
        "current_state": current_state,
        "desired_state": desired_state,
        "delta": delta,
        "decision": decision,
        "next_owner": _next_owner_for_decision(current_state=current_state, desired_state=desired_state, study=current_study),
        "why_not_progressing": _text(current_state.get("why_not_progressing")),
        "apply_eligible": apply_eligible,
        "callable_contract": callable_contract,
        "consumer_projection": _consumer_projection(consumed, study_id),
        "execution_projection": _execution_projection(execution),
        "action_receipt": action_receipt,
    }


def _desired_state(current_state: Mapping[str, Any], study: Mapping[str, Any]) -> dict[str, Any]:
    state = _text(current_state.get("state"))
    owner_route = _mapping(study.get("owner_route"))
    source_fingerprint = _source_fingerprint(study)
    if state == "opl_stage_attempt_admission_required":
        return {
            "state": "opl_stage_attempt_admission_required",
            "owner": "one-person-lab",
            "action_type": "request_opl_stage_attempt",
            "required_outputs": ("OPL stage attempt admission receipt or MAS typed blocker",),
            "artifact_delta_predicate": "opl_stage_attempt_admitted_or_typed_blocker_recorded",
            "gate_replay_target": None,
            "idempotency_key": _idempotency_key(study, owner_route, "opl_stage_attempt_admission"),
            "source_fingerprint": source_fingerprint,
        }
    if state == "awaiting_callable_owner":
        return {
            "state": "domain_owner_contract_blocked",
            "owner": "med-autoscience",
            "action_type": "owner_callable_surface_missing",
            "required_outputs": ("MAS owner receipt or typed blocker",),
            "artifact_delta_predicate": "domain_owner_contract_resolved_or_typed_blocker_recorded",
            "gate_replay_target": None,
            "idempotency_key": _idempotency_key(study, owner_route, "registry_repair"),
            "source_fingerprint": source_fingerprint,
        }
    if state == "downstream_only":
        return {
            "state": "supervisor_only_live_quality_repair",
            "owner": "supervisor_only/live_quality_repair",
            "action_type": "monitor_live_quality_repair",
            "required_outputs": (),
            "artifact_delta_predicate": "live_artifact_delta_without_delivery_package_claim",
            "gate_replay_target": "publishability_gate",
            "idempotency_key": _idempotency_key(study, owner_route, "downstream_only"),
            "source_fingerprint": source_fingerprint,
        }
    if state == "progressing":
        return {
            "state": "continue_current_write",
            "owner": _text(current_state.get("next_owner")) or "managed_runtime",
            "action_type": "observe_progress",
            "required_outputs": (),
            "artifact_delta_predicate": "meaningful_artifact_delta_remains_fresh",
            "gate_replay_target": None,
            "idempotency_key": _idempotency_key(study, owner_route, "progressing"),
            "source_fingerprint": source_fingerprint,
        }
    if state == "awaiting_human":
        return {
            "state": "human_input_required",
            "owner": "human",
            "action_type": "await_human",
            "required_outputs": (),
            "artifact_delta_predicate": "human_supplied_external_input",
            "gate_replay_target": None,
            "idempotency_key": _idempotency_key(study, owner_route, "awaiting_human"),
            "source_fingerprint": source_fingerprint,
        }
    return {
        "state": "repo_level_blocker",
        "owner": "med-autoscience",
        "action_type": "repo_route_typed_blocker_required",
        "required_outputs": ("MAS typed blocker", "MAS owner receipt"),
        "artifact_delta_predicate": "repo_route_gap_typed_blocker_or_owner_receipt_recorded",
        "gate_replay_target": None,
        "idempotency_key": _idempotency_key(study, owner_route, "repo_route_typed_blocker"),
        "source_fingerprint": source_fingerprint,
    }


def _decision(
    *,
    current_state: Mapping[str, Any],
    desired_state: Mapping[str, Any],
    study: Mapping[str, Any],
) -> str:
    state = _text(current_state.get("state"))
    if state == "opl_stage_attempt_admission_required":
        return "opl_stage_attempt_admission"
    if state == "awaiting_callable_owner":
        return "registry_repair"
    if state == "downstream_only":
        return "monitor_live_quality_repair"
    if state == "progressing":
        return "observe_progress"
    if state == "awaiting_human":
        return "await_human"
    if _text(desired_state.get("state")) == "repo_level_blocker":
        return "repo_level_blocker"
    return "inspect"


def _action_receipt(
    *,
    profile: Any,
    study: Mapping[str, Any],
    desired_state: Mapping[str, Any],
    callable_contract: Mapping[str, Any] | None,
    execution: Mapping[str, Any] | None,
    reconcile_apply_requested: bool,
    apply: bool,
    generated_at: str,
) -> dict[str, Any]:
    if callable_contract is None:
        return {"receipt_status": "not_callable", "reason": "callable_contract_missing"}
    intent = _intent(study=study, desired_state=desired_state, callable_contract=callable_contract)
    if not apply:
        if reconcile_apply_requested:
            execution_status = _text(_mapping(execution).get("execution_status"))
            return {
                "receipt_status": "not_executed",
                "reason": "owner_dispatch_not_executed",
                "execution_status": execution_status,
                "idempotency_key": intent["idempotency_key"],
                "source_fingerprint": intent["source_fingerprint"],
                "owner": intent["owner"],
                "callable_surface": intent["callable_surface"],
            }
        return {
            "receipt_status": "dry_run_not_recorded",
            "idempotency_key": intent["idempotency_key"],
            "source_fingerprint": intent["source_fingerprint"],
            "owner": intent["owner"],
            "callable_surface": intent["callable_surface"],
        }
    study_id = _text(study.get("study_id")) or "unknown-study"
    return record_paper_progress_transition_ref(
        study_root=profile.studies_root / study_id,
        quest_root=profile.runtime_root / _quest_id(study, study_id),
        idempotency_key=str(intent["idempotency_key"]),
        intent=intent,
        recorded_at=generated_at,
    )


def _intent(
    *,
    study: Mapping[str, Any],
    desired_state: Mapping[str, Any],
    callable_contract: Mapping[str, Any],
) -> dict[str, Any]:
    study_id = _text(study.get("study_id")) or "unknown-study"
    return {
        "study_id": study_id,
        "quest_id": _quest_id(study, study_id),
        "unit_id": _text(desired_state.get("state")),
        "action_type": _text(desired_state.get("action_type")),
        "lane": "paper-progress-reconcile",
        "owner": _text(desired_state.get("owner")),
        "callable_surface": _text(callable_contract.get("callable_surface")),
        "required_outputs": list(desired_state.get("required_outputs") or []),
        "artifact_delta_predicate": _text(desired_state.get("artifact_delta_predicate")),
        "gate_replay_target": _text(desired_state.get("gate_replay_target")),
        "idempotency_key": _text(desired_state.get("idempotency_key")),
        "source_fingerprint": _text(desired_state.get("source_fingerprint")),
    }


def _callable_contract(desired_state: Mapping[str, Any]) -> dict[str, Any] | None:
    owner = _text(desired_state.get("owner"))
    registry = owner_callable_registry()
    if owner in registry:
        return dict(registry[owner])
    if owner == "one-person-lab" and _text(desired_state.get("action_type")) == "request_opl_stage_attempt":
        return {
            "owner": owner,
            "action_type": "request_opl_stage_attempt",
            "callable_surface": "opl_stage_attempt.request_admission",
            "required_inputs": ("paper_progress_state", "owner_route", "source_fingerprint"),
            "required_outputs": ("OPL stage attempt admission receipt", "MAS typed blocker"),
            "artifact_delta_predicate": "opl_stage_attempt_admitted_or_typed_blocker_recorded",
            "gate_replay_target": None,
            "idempotency_scope": "study_quest_owner_route",
            "source_fingerprint_scope": "owner_route.source_fingerprint",
        }
    if owner == "med-autoscience" and _text(desired_state.get("action_type")) == "owner_callable_surface_missing":
        return {
            "owner": owner,
            "action_type": "owner_callable_surface_missing",
            "callable_surface": "mas_domain_authority.typed_blocker.owner_callable_surface_missing",
            "required_inputs": ("paper_progress_state", "owner_route", "missing_owner_ref"),
            "required_outputs": ("MAS typed blocker", "MAS owner receipt"),
            "artifact_delta_predicate": "domain_owner_contract_resolved_or_typed_blocker_recorded",
            "gate_replay_target": None,
            "idempotency_scope": "study_quest_owner_route",
            "source_fingerprint_scope": "owner_route.source_fingerprint",
        }
    if owner == "med-autoscience" and _text(desired_state.get("action_type")) == "repo_route_typed_blocker_required":
        return {
            "owner": owner,
            "action_type": "repo_route_typed_blocker_required",
            "callable_surface": "mas_domain_authority.typed_blocker.repo_route_gap",
            "required_inputs": ("paper_progress_state", "owner_route", "authority_snapshot"),
            "required_outputs": ("MAS typed blocker", "MAS owner receipt"),
            "artifact_delta_predicate": "repo_route_gap_typed_blocker_or_owner_receipt_recorded",
            "gate_replay_target": None,
            "idempotency_scope": "study_quest_owner_route",
            "source_fingerprint_scope": "owner_route.source_fingerprint",
        }
    if owner == "supervisor_only/live_quality_repair":
        return {
            "owner": owner,
            "action_type": "monitor_live_quality_repair",
            "callable_surface": "opl_stage_attempt.monitor_live_quality_repair",
            "required_inputs": ("paper_progress_state", "publication_supervisor_state"),
            "required_outputs": (),
            "artifact_delta_predicate": "live_artifact_delta_without_delivery_package_claim",
            "gate_replay_target": "publishability_gate",
            "idempotency_scope": "study_quest_owner_route",
            "source_fingerprint_scope": "owner_route.source_fingerprint",
        }
    return None


def _matching_execution(executed: Mapping[str, Any], *, study_id: str, action_type: str | None) -> dict[str, Any] | None:
    for execution in executed.get("executions") or []:
        payload = _mapping(execution)
        if _text(payload.get("study_id")) != study_id:
            continue
        if action_type is not None and _text(payload.get("action_type")) != action_type:
            continue
        return payload
    return None


def _study(scan_payload: Mapping[str, Any], study_id: str) -> dict[str, Any]:
    for study in scan_payload.get("studies") or []:
        payload = _mapping(study)
        if _text(payload.get("study_id")) == study_id:
            return payload
    return {"study_id": study_id}


def _delta(*, current_state: Mapping[str, Any], desired_state: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "current": _text(current_state.get("state")),
        "desired": _text(desired_state.get("state")),
        "needs_action": _text(current_state.get("state")) not in {"progressing", "terminal_delivered"},
        "meaningful_artifact_delta": bool(current_state.get("meaningful_artifact_delta")),
        "package_delivered": bool(current_state.get("package_delivered")),
    }


def _next_owner_for_decision(
    *,
    current_state: Mapping[str, Any],
    desired_state: Mapping[str, Any],
    study: Mapping[str, Any],
) -> str | None:
    if _text(current_state.get("state")) == "downstream_only" and _supervisor_only_live(study, current_state):
        return "supervisor_only/live_quality_repair"
    owner = _text(desired_state.get("owner"))
    return owner or _text(current_state.get("next_owner"))


def _supervisor_only_live(study: Mapping[str, Any], current_state: Mapping[str, Any]) -> bool:
    if current_state.get("actual_write_active") is not True or current_state.get("meaningful_artifact_delta") is not True:
        return False
    return _mapping(study.get("execution_owner_guard")).get("supervisor_only") is True or _text(
        _mapping(study.get("owner_route")).get("next_owner")
    ) == "external_supervisor"


def _source_fingerprint(study: Mapping[str, Any]) -> str:
    owner_route = _mapping(study.get("owner_route"))
    for value in (
        owner_route.get("source_fingerprint"),
        owner_route.get("work_unit_fingerprint"),
        _mapping(study.get("paper_progress_stall")).get("action_fingerprint"),
        _text(study.get("study_id")),
    ):
        if text := _text(value):
            return text
    return "unknown-source"


def _idempotency_key(study: Mapping[str, Any], owner_route: Mapping[str, Any], suffix: str) -> str:
    if text := _text(owner_route.get("idempotency_key")):
        return f"paper-progress::{text}::{suffix}"
    study_id = _text(study.get("study_id")) or "unknown-study"
    return f"paper-progress::{study_id}::{_source_fingerprint(study)}::{suffix}"


def _quest_id(study: Mapping[str, Any], study_id: str) -> str:
    return _text(study.get("quest_id")) or f"quest-{study_id}"


def _consumer_projection(consumed: Mapping[str, Any], study_id: str) -> dict[str, Any]:
    dispatches = [
        _mapping(item)
        for item in consumed.get("default_executor_dispatches") or []
        if _text(_mapping(item).get("study_id")) == study_id
    ]
    return {
        "dispatch_count": len(dispatches),
        "ready_count": sum(_text(item.get("dispatch_status")) == "ready" for item in dispatches),
        "blocked_count": sum(_text(item.get("dispatch_status")) == "blocked" for item in dispatches),
    }


def _execution_projection(execution: Mapping[str, Any] | None) -> dict[str, Any] | None:
    payload = _mapping(execution)
    if not payload:
        return None
    return {
        "execution_status": _text(payload.get("execution_status")),
        "blocked_reason": _text(payload.get("blocked_reason")),
        "will_start_llm": bool(payload.get("will_start_llm")),
        "action_type": _text(payload.get("action_type")),
    }


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "SCHEMA_VERSION",
    "SURFACE",
    "build_paper_progress_reconcile_receipt",
]
