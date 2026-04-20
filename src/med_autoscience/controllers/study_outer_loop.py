from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience import runtime_backend as runtime_backend_contract
from med_autoscience.controllers import study_runtime_router
from med_autoscience.controllers import study_runtime_family_orchestration as family_orchestration
from med_autoscience.controllers.study_runtime_resolution import _resolve_study
from med_autoscience.controller_confirmation_summary import (
    materialize_controller_confirmation_summary,
    read_controller_confirmation_summary,
    stable_controller_confirmation_summary_path,
)
from med_autoscience.human_gate_policy import require_controller_human_gate_allowed
from med_autoscience.native_runtime_event import NativeRuntimeEventRecord
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.publication_eval_latest import (
    read_publication_eval_latest,
    resolve_publication_eval_latest_ref,
)
from med_autoscience.runtime_event_record import RuntimeEventRecord, RuntimeEventRecordRef
from med_autoscience.runtime_escalation_record import RuntimeEscalationRecord, RuntimeEscalationRecordRef
from med_autoscience.runtime_protocol import study_runtime as study_runtime_protocol
from med_autoscience.study_charter import read_study_charter, resolve_study_charter_ref
from med_autoscience.study_decision_record import (
    StudyDecisionActionType,
    StudyDecisionCharterRef,
    StudyDecisionControllerAction,
    StudyDecisionPublicationEvalRef,
    StudyDecisionRecord,
    StudyDecisionType,
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _decision_id(*, study_id: str, quest_id: str, decision_type: str, recorded_at: str) -> str:
    return f"study-decision::{study_id}::{quest_id}::{decision_type}::{recorded_at}"


def _runtime_status_summary(
    status: dict[str, Any],
    *,
    managed_runtime_event: tuple[RuntimeEventRecordRef, RuntimeEventRecord | NativeRuntimeEventRecord, dict[str, Any] | None]
    | None = None,
) -> dict[str, str]:
    if managed_runtime_event is not None:
        runtime_event_ref, runtime_event_record, _runtime_escalation_payload = managed_runtime_event
        return _runtime_status_summary_from_runtime_event(
            status=status,
            runtime_event_ref=runtime_event_ref,
            runtime_event_record=runtime_event_record,
        )
    runtime_event_payload = status.get("runtime_event_ref")
    if isinstance(runtime_event_payload, dict):
        runtime_event_ref, runtime_event_record = _load_runtime_event_record(
            runtime_event_payload=runtime_event_payload
        )
        return _runtime_status_summary_from_runtime_event(
            status=status,
            runtime_event_ref=runtime_event_ref,
            runtime_event_record=runtime_event_record,
        )
    return {
        "decision": str(status.get("decision") or "").strip(),
        "reason": str(status.get("reason") or "").strip(),
    }


def _runtime_status_summary_from_runtime_event(
    *,
    status: dict[str, Any],
    runtime_event_ref: RuntimeEventRecordRef,
    runtime_event_record: RuntimeEventRecord | NativeRuntimeEventRecord,
) -> dict[str, str]:
    outer_loop_input = runtime_event_record.outer_loop_input
    if isinstance(runtime_event_record, RuntimeEventRecord):
        decision = str(outer_loop_input.get("decision") or "").strip()
        reason = str(outer_loop_input.get("reason") or "").strip()
        supervisor_tick_status = str(outer_loop_input.get("supervisor_tick_status") or "").strip()
    else:
        decision = str(status.get("decision") or "").strip()
        reason = str(status.get("reason") or "").strip()
        supervisor_tick_payload = status.get("supervisor_tick_audit")
        supervisor_tick_status = (
            str(supervisor_tick_payload.get("status") or "").strip()
            if isinstance(supervisor_tick_payload, dict)
            else ""
        )
    return {
        "decision": decision,
        "reason": reason,
        "quest_status": str(outer_loop_input.get("quest_status") or "").strip(),
        "active_run_id": str(outer_loop_input.get("active_run_id") or "").strip(),
        "runtime_liveness_status": str(outer_loop_input.get("runtime_liveness_status") or "").strip(),
        "supervisor_tick_status": supervisor_tick_status,
        "runtime_event_id": runtime_event_ref.event_id,
    }


def _runtime_status_active_run_id(status: dict[str, Any], runtime_status: dict[str, str]) -> str | None:
    return family_orchestration.resolve_active_run_id(
        runtime_status.get("active_run_id"),
        status.get("active_run_id"),
        ((status.get("execution_owner_guard") or {}) if isinstance(status.get("execution_owner_guard"), dict) else {}).get(
            "active_run_id"
        ),
        ((status.get("autonomous_runtime_notice") or {}) if isinstance(status.get("autonomous_runtime_notice"), dict) else {}).get(
            "active_run_id"
        ),
    )


def _build_family_human_gates_for_decision_record(
    *,
    requires_human_confirmation: bool,
    emitted_at: str,
    study_id: str,
    evidence_refs: list[dict[str, str]],
    controller_actions: tuple[StudyDecisionControllerAction, ...],
) -> list[dict[str, Any]]:
    if not requires_human_confirmation:
        return []
    return [
        family_orchestration.build_family_human_gate(
            gate_id=f"controller-human-confirmation-{study_id}",
            gate_kind="controller_human_confirmation",
            requested_at=emitted_at,
            request_surface_kind="controller_decisions",
            request_surface_id="controller_decisions/latest.json",
            evidence_refs=evidence_refs,
            decision_options=["approve", "request_changes", "reject"],
        )
    ]


def _resolve_charter_ref(
    *,
    study_root: Path,
    charter_ref: StudyDecisionCharterRef | dict[str, Any],
) -> StudyDecisionCharterRef:
    normalized_ref = (
        charter_ref
        if isinstance(charter_ref, StudyDecisionCharterRef)
        else StudyDecisionCharterRef.from_payload(charter_ref)
    )
    charter_path = resolve_study_charter_ref(study_root=study_root, ref=normalized_ref.artifact_path)
    charter_payload = read_study_charter(study_root=study_root, ref=charter_path)
    charter_id = str(charter_payload.get("charter_id") or "").strip()
    if charter_id != normalized_ref.charter_id:
        raise ValueError("study_outer_loop_tick charter_id mismatch against stable study charter artifact")
    return StudyDecisionCharterRef(charter_id=charter_id, artifact_path=str(charter_path))


def _resolve_publication_eval_ref(
    *,
    study_root: Path,
    publication_eval_ref: StudyDecisionPublicationEvalRef | dict[str, Any],
) -> StudyDecisionPublicationEvalRef:
    normalized_ref = (
        publication_eval_ref
        if isinstance(publication_eval_ref, StudyDecisionPublicationEvalRef)
        else StudyDecisionPublicationEvalRef.from_payload(publication_eval_ref)
    )
    publication_eval_path = resolve_publication_eval_latest_ref(
        study_root=study_root,
        ref=normalized_ref.artifact_path,
    )
    publication_eval_payload = read_publication_eval_latest(study_root=study_root, ref=publication_eval_path)
    eval_id = str(publication_eval_payload.get("eval_id") or "").strip()
    if eval_id != normalized_ref.eval_id:
        raise ValueError("study_outer_loop_tick eval_id mismatch against stable publication eval artifact")
    return StudyDecisionPublicationEvalRef(eval_id=eval_id, artifact_path=str(publication_eval_path))


def _load_runtime_escalation_record(
    *,
    runtime_escalation_payload: dict[str, Any],
) -> tuple[RuntimeEscalationRecordRef, RuntimeEscalationRecord]:
    runtime_escalation_ref = RuntimeEscalationRecordRef.from_payload(runtime_escalation_payload)
    artifact_path = Path(runtime_escalation_ref.artifact_path).expanduser().resolve()
    payload = json.loads(artifact_path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError("runtime escalation record artifact must contain a mapping payload")
    record = RuntimeEscalationRecord.from_payload(payload)
    written_ref = record.ref()
    if written_ref.record_id != runtime_escalation_ref.record_id:
        raise ValueError("study_outer_loop_tick runtime escalation record_id mismatch against status ref")
    if Path(written_ref.artifact_path).expanduser().resolve() != artifact_path:
        raise ValueError("study_outer_loop_tick runtime escalation artifact_path mismatch against status ref")
    if written_ref.summary_ref != runtime_escalation_ref.summary_ref:
        raise ValueError("study_outer_loop_tick runtime escalation summary_ref mismatch against status ref")
    return written_ref, record


def _load_runtime_event_record(
    *,
    runtime_event_payload: dict[str, Any],
) -> tuple[RuntimeEventRecordRef, RuntimeEventRecord | NativeRuntimeEventRecord]:
    runtime_event_ref = RuntimeEventRecordRef.from_payload(runtime_event_payload)
    artifact_path = Path(runtime_event_ref.artifact_path).expanduser().resolve()
    payload = json.loads(artifact_path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError("runtime event record artifact must contain a mapping payload")
    try:
        record = RuntimeEventRecord.from_payload(payload)
    except (TypeError, ValueError):
        record = NativeRuntimeEventRecord.from_payload(payload)
    written_ref = record.ref()
    if written_ref.event_id != runtime_event_ref.event_id:
        raise ValueError("study_outer_loop_tick runtime event event_id mismatch against status ref")
    if Path(written_ref.artifact_path).expanduser().resolve() != artifact_path:
        raise ValueError("study_outer_loop_tick runtime event artifact_path mismatch against status ref")
    if written_ref.summary_ref != runtime_event_ref.summary_ref:
        raise ValueError("study_outer_loop_tick runtime event summary_ref mismatch against status ref")
    return written_ref, record


def _managed_runtime_requires_event_ref(status: dict[str, Any]) -> bool:
    execution = status.get("execution")
    return runtime_backend_contract.is_managed_research_execution(execution if isinstance(execution, dict) else None)


def _resolve_managed_runtime_event_contract(
    *,
    status: dict[str, Any],
) -> tuple[RuntimeEventRecordRef, RuntimeEventRecord | NativeRuntimeEventRecord, dict[str, Any] | None]:
    runtime_event_payload = status.get("runtime_event_ref")
    if not isinstance(runtime_event_payload, dict):
        raise ValueError("study_outer_loop_tick requires runtime_event_ref from managed runtime status")
    runtime_event_ref, runtime_event_record = _load_runtime_event_record(
        runtime_event_payload=runtime_event_payload
    )
    status_study_id = str(status.get("study_id") or "").strip()
    status_quest_id = str(status.get("quest_id") or "").strip()
    if isinstance(runtime_event_record, RuntimeEventRecord) and status_study_id and runtime_event_record.study_id != status_study_id:
        raise ValueError("study_outer_loop_tick runtime event study_id mismatch against status")
    if status_quest_id and runtime_event_record.quest_id != status_quest_id:
        raise ValueError("study_outer_loop_tick runtime event quest_id mismatch against status")
    if isinstance(runtime_event_record, RuntimeEventRecord):
        supervisor_tick_status = str(runtime_event_record.outer_loop_input.get("supervisor_tick_status") or "").strip()
        runtime_escalation_payload = runtime_event_record.outer_loop_input.get("runtime_escalation_ref")
        if runtime_escalation_payload is not None and not isinstance(runtime_escalation_payload, dict):
            raise ValueError("study_outer_loop_tick runtime_event runtime_escalation_ref must be a mapping")
    else:
        supervisor_tick_payload = status.get("supervisor_tick_audit")
        supervisor_tick_status = (
            str(supervisor_tick_payload.get("status") or "").strip()
            if isinstance(supervisor_tick_payload, dict)
            else ""
        )
        runtime_escalation_payload = status.get("runtime_escalation_ref")
    if supervisor_tick_status != "fresh":
        raise ValueError("study_outer_loop_tick requires supervisor_tick_status=fresh in managed runtime event input")
    status_runtime_escalation_payload = status.get("runtime_escalation_ref")
    if isinstance(runtime_event_record, RuntimeEventRecord) and isinstance(status_runtime_escalation_payload, dict):
        if runtime_escalation_payload is None:
            raise ValueError("study_outer_loop_tick requires runtime_escalation_ref in managed runtime event input")
        if status_runtime_escalation_payload != runtime_escalation_payload:
            raise ValueError("study_outer_loop_tick runtime escalation ref mismatch against runtime_event")
    return runtime_event_ref, runtime_event_record, runtime_escalation_payload


def _resolve_runtime_escalation_record(
    *,
    runtime_escalation_payload: dict[str, Any] | None,
) -> tuple[RuntimeEscalationRecordRef, RuntimeEscalationRecord]:
    if isinstance(runtime_escalation_payload, dict):
        return _load_runtime_escalation_record(runtime_escalation_payload=runtime_escalation_payload)
    raise ValueError("study_outer_loop_tick requires runtime_escalation_ref from managed runtime input")


def _build_human_confirmation_request(
    *,
    study_id: str,
    summary: str,
    runtime_status: dict[str, str],
    runtime_escalation_ref: RuntimeEscalationRecordRef,
    publication_eval_payload: dict[str, Any],
    controller_actions: tuple[StudyDecisionControllerAction, ...],
) -> dict[str, Any]:
    verdict = publication_eval_payload.get("verdict")
    gaps = publication_eval_payload.get("gaps")
    publication_blockers: list[dict[str, Any]] = []
    if isinstance(verdict, dict):
        publication_blockers.append(
            {
                "overall_verdict": str(verdict.get("overall_verdict") or "").strip(),
                "primary_claim_status": str(verdict.get("primary_claim_status") or "").strip(),
                "summary": str(verdict.get("summary") or "").strip(),
                "gap_summaries": [
                    str(item.get("summary") or "").strip()
                    for item in gaps
                    if isinstance(item, dict) and str(item.get("summary") or "").strip()
                ]
                if isinstance(gaps, list)
                else [],
            }
        )
    first_action = controller_actions[0].action_type.value if controller_actions else "controller_review"
    return {
        "category": "controller_decision_confirmation",
        "summary": summary,
        "runtime_blockers": [
            {
                "decision": str(runtime_status.get("decision") or "").strip(),
                "reason": str(runtime_status.get("reason") or "").strip(),
                "record_id": runtime_escalation_ref.record_id,
                "summary_ref": runtime_escalation_ref.summary_ref,
            }
        ],
        "publication_blockers": publication_blockers,
        "current_required_action": "human_confirmation_required",
        "controller_actions": [action.to_dict() for action in controller_actions],
        "question_for_user": f"Approve controller action `{first_action}` for study `{study_id}`?",
    }


def _controller_confirmation_pending(*, study_root: Path) -> bool:
    summary_path = stable_controller_confirmation_summary_path(study_root=study_root)
    if not summary_path.exists():
        return False
    summary = read_controller_confirmation_summary(
        study_root=study_root,
        ref=summary_path,
    )
    return str(summary.get("status") or "").strip() == "pending"


def _latest_controller_decision_requires_human_confirmation(*, study_root: Path) -> bool:
    decision_path = Path(study_root).expanduser().resolve() / "artifacts" / "controller_decisions" / "latest.json"
    if not decision_path.exists():
        return False
    payload = json.loads(decision_path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError("controller decision latest artifact must contain a mapping payload")
    return StudyDecisionRecord.from_payload(payload).requires_human_confirmation


def _publication_supervisor_human_gate_requested(status_payload: dict[str, Any]) -> bool:
    publication_supervisor_state = status_payload.get("publication_supervisor_state")
    if not isinstance(publication_supervisor_state, dict):
        return False
    return str(publication_supervisor_state.get("current_required_action") or "").strip() == "human_confirmation_required"


def _recommended_publication_eval_action(publication_eval_payload: dict[str, Any]) -> dict[str, Any] | None:
    recommended_actions = publication_eval_payload.get("recommended_actions")
    if not isinstance(recommended_actions, list):
        return None
    for action in recommended_actions:
        if not isinstance(action, dict):
            continue
        if action.get("requires_controller_decision") is not True:
            continue
        return dict(action)
    return None


def _autonomous_decision_type_for_publication_eval_action(action_payload: dict[str, Any]) -> str | None:
    action_type = str(action_payload.get("action_type") or "").strip()
    if action_type == StudyDecisionType.CONTINUE_SAME_LINE.value:
        return StudyDecisionType.CONTINUE_SAME_LINE.value
    return None


def _autonomous_controller_action_type_for_runtime_status(status_payload: dict[str, Any]) -> str:
    if str(status_payload.get("reason") or "").strip() == "quest_stopped_requires_explicit_rerun":
        return StudyDecisionActionType.ENSURE_STUDY_RUNTIME_RELAUNCH_STOPPED.value
    return StudyDecisionActionType.ENSURE_STUDY_RUNTIME.value


def build_runtime_watch_outer_loop_tick_request(
    *,
    study_root: Path,
    status_payload: dict[str, Any],
) -> dict[str, Any] | None:
    resolved_study_root = Path(study_root).expanduser().resolve()
    if _publication_supervisor_human_gate_requested(status_payload):
        return None
    if _controller_confirmation_pending(study_root=resolved_study_root):
        return None
    if _latest_controller_decision_requires_human_confirmation(study_root=resolved_study_root):
        return None

    publication_eval_path = resolve_publication_eval_latest_ref(study_root=resolved_study_root)
    if not publication_eval_path.exists():
        return None
    publication_eval_payload = read_publication_eval_latest(
        study_root=resolved_study_root,
        ref=publication_eval_path,
    )
    recommended_action = _recommended_publication_eval_action(publication_eval_payload)
    if recommended_action is None:
        return None
    decision_type = _autonomous_decision_type_for_publication_eval_action(recommended_action)
    if decision_type is None:
        return None

    charter_path = resolve_study_charter_ref(study_root=resolved_study_root)
    if not charter_path.exists():
        raise ValueError("runtime watch outer-loop wakeup requires stable study charter artifact")
    charter_payload = read_study_charter(
        study_root=resolved_study_root,
        ref=charter_path,
    )
    charter_ref = StudyDecisionCharterRef(
        charter_id=str(charter_payload.get("charter_id") or "").strip(),
        artifact_path=str(charter_path),
    ).to_dict()

    runtime_escalation_payload = status_payload.get("runtime_escalation_ref")
    if not isinstance(runtime_escalation_payload, dict):
        raise ValueError("runtime watch outer-loop wakeup requires runtime_escalation_ref from managed runtime status")
    _resolve_runtime_escalation_record(runtime_escalation_payload=runtime_escalation_payload)

    publication_eval_ref = StudyDecisionPublicationEvalRef(
        eval_id=str(publication_eval_payload.get("eval_id") or "").strip(),
        artifact_path=str(publication_eval_path),
    ).to_dict()
    controller_action = StudyDecisionControllerAction(
        action_type=_autonomous_controller_action_type_for_runtime_status(status_payload),
        payload_ref=str((resolved_study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()),
    ).to_dict()
    return {
        "study_root": resolved_study_root,
        "charter_ref": charter_ref,
        "publication_eval_ref": publication_eval_ref,
        "decision_type": decision_type,
        "requires_human_confirmation": False,
        "controller_actions": [controller_action],
        "reason": str(recommended_action.get("reason") or "").strip()
        or "publication eval requests an autonomous controller decision for the current line.",
    }


def _execute_controller_action(
    *,
    action: StudyDecisionControllerAction,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    quest_id: str,
    source: str,
) -> dict[str, Any]:
    if action.action_type is StudyDecisionActionType.ENSURE_STUDY_RUNTIME:
        result = study_runtime_router.ensure_study_runtime(
            profile=profile,
            study_id=study_id,
            study_root=study_root,
            force=False,
            source=source,
        )
    elif action.action_type is StudyDecisionActionType.ENSURE_STUDY_RUNTIME_RELAUNCH_STOPPED:
        result = study_runtime_router.ensure_study_runtime(
            profile=profile,
            study_id=study_id,
            study_root=study_root,
            allow_stopped_relaunch=True,
            force=False,
            source=source,
        )
    elif action.action_type in {StudyDecisionActionType.PAUSE_RUNTIME, StudyDecisionActionType.STOP_RUNTIME}:
        execution = study_runtime_router._execution_payload(
            study_runtime_router._load_yaml_dict(study_root / "study.yaml"),
            profile=profile,
        )
        runtime_context = study_runtime_protocol.resolve_study_runtime_context(
            profile=profile,
            study_root=study_root,
            study_id=study_id,
            quest_id=quest_id,
        )
        managed_runtime_backend = (
            study_runtime_router._managed_runtime_backend_for_execution(
                execution,
                profile=profile,
                runtime_root=runtime_context.runtime_root,
            )
            or study_runtime_router._default_managed_runtime_backend()
        )
        if action.action_type is StudyDecisionActionType.PAUSE_RUNTIME:
            result = managed_runtime_backend.pause_quest(
                runtime_root=runtime_context.runtime_root,
                quest_id=quest_id,
                source=source,
            )
        else:
            result = managed_runtime_backend.stop_quest(
                runtime_root=runtime_context.runtime_root,
                quest_id=quest_id,
                source=source,
            )
    else:
        raise ValueError(f"unsupported study outer-loop controller action: {action.action_type.value}")
    return {
        "action_type": action.action_type.value,
        "payload_ref": action.payload_ref,
        "result": result,
    }


def study_outer_loop_tick(
    *,
    profile: WorkspaceProfile,
    study_id: str | None = None,
    study_root: Path | None = None,
    charter_ref: StudyDecisionCharterRef | dict[str, Any],
    publication_eval_ref: StudyDecisionPublicationEvalRef | dict[str, Any],
    decision_type: str,
    requires_human_confirmation: bool,
    controller_actions: list[dict[str, Any]] | tuple[StudyDecisionControllerAction, ...] | None = None,
    reason: str,
    source: str = "med_autoscience",
    recorded_at: str | None = None,
) -> dict[str, Any]:
    resolved_study_id, resolved_study_root, _study_payload = _resolve_study(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
    )
    status = study_runtime_router.study_runtime_status(
        profile=profile,
        study_id=resolved_study_id,
        study_root=resolved_study_root,
    )
    managed_runtime_event: tuple[RuntimeEventRecordRef, RuntimeEventRecord | NativeRuntimeEventRecord, dict[str, Any] | None] | None = None
    if _managed_runtime_requires_event_ref(status):
        managed_runtime_event = _resolve_managed_runtime_event_contract(status=status)
    runtime_status = _runtime_status_summary(status, managed_runtime_event=managed_runtime_event)
    runtime_escalation_payload = (
        managed_runtime_event[2] if managed_runtime_event is not None else status.get("runtime_escalation_ref")
    )
    quest_id = str(status.get("quest_id") or "").strip()
    if not quest_id:
        raise ValueError("study_outer_loop_tick requires quest_id from study_runtime_status")

    normalized_charter_ref = _resolve_charter_ref(
        study_root=resolved_study_root,
        charter_ref=charter_ref,
    )
    normalized_publication_eval_ref = _resolve_publication_eval_ref(
        study_root=resolved_study_root,
        publication_eval_ref=publication_eval_ref,
    )
    emitted_at = recorded_at or _utc_now()
    publication_eval_payload = read_publication_eval_latest(
        study_root=resolved_study_root,
        ref=normalized_publication_eval_ref.artifact_path,
    )
    runtime_escalation_ref, _runtime_escalation_record = _resolve_runtime_escalation_record(
        runtime_escalation_payload=runtime_escalation_payload if isinstance(runtime_escalation_payload, dict) else None,
    )
    normalized_controller_actions = tuple(
        action
        if isinstance(action, StudyDecisionControllerAction)
        else StudyDecisionControllerAction.from_payload(action)
        for action in (controller_actions or [])
    )
    human_gate_policy = None
    if requires_human_confirmation:
        human_gate_policy = require_controller_human_gate_allowed(
            decision_type=decision_type,
            controller_action_types=(action.action_type for action in normalized_controller_actions),
        )
    family_evidence_refs = [
        {
            "ref_kind": "repo_path",
            "ref": normalized_charter_ref.artifact_path,
            "label": "study_charter",
        },
        {
            "ref_kind": "repo_path",
            "ref": normalized_publication_eval_ref.artifact_path,
            "label": "publication_eval_latest",
        },
        {
            "ref_kind": "repo_path",
            "ref": runtime_escalation_ref.artifact_path,
            "label": "runtime_escalation_record",
        },
    ]
    family_human_gates = _build_family_human_gates_for_decision_record(
        requires_human_confirmation=requires_human_confirmation,
        emitted_at=emitted_at,
        study_id=resolved_study_id,
        evidence_refs=family_evidence_refs,
        controller_actions=normalized_controller_actions,
    )
    family_companion = family_orchestration.build_family_orchestration_companion(
        surface_kind="controller_decisions",
        surface_id="controller_decisions/latest.json",
        event_name=f"study_outer_loop.{decision_type}",
        source_surface="study_outer_loop_tick",
        session_id=f"study-outer-loop:{resolved_study_id}",
        program_id=family_orchestration.resolve_program_id(
            status.get("execution") if isinstance(status.get("execution"), dict) else None
        ),
        study_id=resolved_study_id,
        quest_id=quest_id,
        active_run_id=_runtime_status_active_run_id(status, runtime_status),
        runtime_decision=runtime_status.get("decision"),
        runtime_reason=runtime_status.get("reason"),
        payload={
            "decision_type": decision_type,
            "requires_human_confirmation": requires_human_confirmation,
            "human_gate_policy": human_gate_policy.to_dict() if human_gate_policy is not None else None,
            "controller_reason": reason,
        },
        event_time=emitted_at,
        checkpoint_id=f"controller-decision:{resolved_study_id}:{decision_type}",
        checkpoint_label="controller decision checkpoint",
        audit_refs=family_evidence_refs,
        state_refs=[
            {
                "role": "controller",
                "ref_kind": "repo_path",
                "ref": str(resolved_study_root / "artifacts" / "controller_decisions" / "latest.json"),
                "label": "controller_decisions_latest",
            },
            {
                "role": "publication",
                "ref_kind": "repo_path",
                "ref": normalized_publication_eval_ref.artifact_path,
                "label": "publication_eval_latest",
            },
        ],
        restoration_evidence=family_evidence_refs,
        action_graph_id="mas_runtime_orchestration",
        node_id="study_outer_loop_tick",
        gate_id=(family_human_gates[0].get("gate_id") if family_human_gates else None),
        resume_mode="reenter_human_gate" if requires_human_confirmation else "resume_from_checkpoint",
        resume_handle=f"study_outer_loop:{resolved_study_id}:{decision_type}",
        human_gate_required=requires_human_confirmation,
        human_gates=family_human_gates,
    )
    written_record = study_runtime_protocol.write_study_decision_record(
        study_root=resolved_study_root,
        record=StudyDecisionRecord(
            schema_version=1,
            decision_id=_decision_id(
                study_id=resolved_study_id,
                quest_id=quest_id,
                decision_type=decision_type,
                recorded_at=emitted_at,
            ),
            study_id=resolved_study_id,
            quest_id=quest_id,
            emitted_at=emitted_at,
            decision_type=decision_type,
            charter_ref=normalized_charter_ref,
            runtime_escalation_ref=runtime_escalation_ref,
            publication_eval_ref=normalized_publication_eval_ref,
            requires_human_confirmation=requires_human_confirmation,
            controller_actions=normalized_controller_actions,
            reason=reason,
            family_event_envelope=family_companion["family_event_envelope"],
            family_checkpoint_lineage=family_companion["family_checkpoint_lineage"],
            family_human_gates=tuple(family_companion["family_human_gates"]),
        ),
    )
    confirmation_summary_ref = materialize_controller_confirmation_summary(
        study_root=resolved_study_root,
        decision_ref=written_record.ref().to_dict(),
    )
    if requires_human_confirmation:
        return {
            "study_id": resolved_study_id,
            "quest_id": quest_id,
            "source": source,
            "runtime_status": runtime_status,
            "runtime_escalation_ref": written_record.runtime_escalation_ref.to_dict(),
            "study_decision_ref": written_record.ref().to_dict(),
            "controller_confirmation_summary_ref": confirmation_summary_ref,
            "dispatch_status": "pending_human_confirmation",
            "human_confirmation_request": _build_human_confirmation_request(
                study_id=resolved_study_id,
                summary=reason,
                runtime_status=runtime_status,
                runtime_escalation_ref=written_record.runtime_escalation_ref,
                publication_eval_payload=publication_eval_payload,
                controller_actions=written_record.controller_actions,
            ),
            "executed_controller_action": None,
        }
    executed_controller_action = _execute_controller_action(
        action=written_record.controller_actions[0],
        profile=profile,
        study_id=resolved_study_id,
        study_root=resolved_study_root,
        quest_id=quest_id,
        source=source,
    )
    return {
        "study_id": resolved_study_id,
        "quest_id": quest_id,
        "source": source,
        "runtime_status": runtime_status,
        "runtime_escalation_ref": written_record.runtime_escalation_ref.to_dict(),
        "study_decision_ref": written_record.ref().to_dict(),
        "controller_confirmation_summary_ref": confirmation_summary_ref,
        "dispatch_status": "executed",
        "executed_controller_action": executed_controller_action,
    }
