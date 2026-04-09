from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.controllers import study_runtime_router
from med_autoscience.controllers.study_runtime_resolution import _resolve_study
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.publication_eval_latest import (
    read_publication_eval_latest,
    resolve_publication_eval_latest_ref,
)
from med_autoscience.runtime_escalation_record import RuntimeEscalationRecord, RuntimeEscalationRecordRef
from med_autoscience.runtime_protocol import study_runtime as study_runtime_protocol
from med_autoscience.study_charter import read_study_charter, resolve_study_charter_ref
from med_autoscience.study_decision_record import (
    StudyDecisionActionType,
    StudyDecisionCharterRef,
    StudyDecisionControllerAction,
    StudyDecisionPublicationEvalRef,
    StudyDecisionRecord,
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _decision_id(*, study_id: str, quest_id: str, decision_type: str, recorded_at: str) -> str:
    return f"study-decision::{study_id}::{quest_id}::{decision_type}::{recorded_at}"


def _runtime_status_summary(status: dict[str, Any]) -> dict[str, str]:
    return {
        "decision": str(status.get("decision") or "").strip(),
        "reason": str(status.get("reason") or "").strip(),
    }


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


def _runtime_escalation_recommended_actions(reason: str) -> tuple[str, ...]:
    if reason == "quest_stopped_requires_explicit_rerun":
        return ("explicit_stopped_quest_relaunch", "controller_review_required")
    return ("refresh_startup_hydration", "controller_review_required")


def _resolve_runtime_escalation_record(
    *,
    runtime_escalation_payload: dict[str, Any] | None,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    quest_id: str,
    runtime_status: dict[str, str],
    emitted_at: str,
) -> tuple[RuntimeEscalationRecordRef, RuntimeEscalationRecord]:
    if isinstance(runtime_escalation_payload, dict):
        return _load_runtime_escalation_record(runtime_escalation_payload=runtime_escalation_payload)
    runtime_context = study_runtime_protocol.resolve_study_runtime_context(
        profile=profile,
        study_root=study_root,
        study_id=study_id,
        quest_id=quest_id,
    )
    reason = str(runtime_status.get("reason") or "").strip()
    if not reason:
        raise ValueError("study_outer_loop_tick requires runtime reason to synthesize runtime escalation record")
    record = RuntimeEscalationRecord(
        schema_version=1,
        record_id=f"runtime-escalation::{study_id}::{quest_id}::{reason}::{emitted_at}",
        study_id=study_id,
        quest_id=quest_id,
        emitted_at=emitted_at,
        trigger=study_runtime_protocol.RuntimeEscalationTrigger(
            trigger_id=reason,
            source="study_outer_loop_status",
        ),
        scope="quest",
        severity="quest",
        reason=reason,
        recommended_actions=_runtime_escalation_recommended_actions(reason),
        evidence_refs=(str(runtime_context.launch_report_path),),
        runtime_context_refs={"launch_report_path": str(runtime_context.launch_report_path)},
        summary_ref=str(runtime_context.launch_report_path),
    )
    written_record = study_runtime_protocol.write_runtime_escalation_record(
        quest_root=runtime_context.quest_root,
        record=record,
    )
    return written_record.ref(), written_record


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
        runtime_context = study_runtime_protocol.resolve_study_runtime_context(
            profile=profile,
            study_root=study_root,
            study_id=study_id,
            quest_id=quest_id,
        )
        if action.action_type is StudyDecisionActionType.PAUSE_RUNTIME:
            result = study_runtime_router.med_deepscientist_transport.pause_quest(
                runtime_root=runtime_context.runtime_root,
                quest_id=quest_id,
                source=source,
            )
        else:
            result = study_runtime_router.med_deepscientist_transport.stop_quest(
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
    runtime_status = _runtime_status_summary(status)
    runtime_escalation_payload = status.get("runtime_escalation_ref")
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
        profile=profile,
        study_id=resolved_study_id,
        study_root=resolved_study_root,
        quest_id=quest_id,
        runtime_status=runtime_status,
        emitted_at=emitted_at,
    )
    normalized_controller_actions = tuple(
        action
        if isinstance(action, StudyDecisionControllerAction)
        else StudyDecisionControllerAction.from_payload(action)
        for action in (controller_actions or [])
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
        ),
    )
    if requires_human_confirmation:
        return {
            "study_id": resolved_study_id,
            "quest_id": quest_id,
            "source": source,
            "runtime_status": runtime_status,
            "runtime_escalation_ref": written_record.runtime_escalation_ref.to_dict(),
            "study_decision_ref": written_record.ref().to_dict(),
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
        "dispatch_status": "executed",
        "executed_controller_action": executed_controller_action,
    }
