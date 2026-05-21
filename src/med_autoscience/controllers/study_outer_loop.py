from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.controllers import study_runtime_router
from med_autoscience.controllers import study_runtime_family_orchestration as family_orchestration
from med_autoscience.controllers import gate_clearing_batch
from med_autoscience.controllers import quality_repair_batch
from med_autoscience.controllers.study_outer_loop_parts.decision_refs import (
    _build_study_decision_charter_ref,
    _read_latest_publication_eval_payload,
    _read_publication_eval_payload,
    _resolve_charter_ref,
    _resolve_publication_eval_ref,
)
from med_autoscience.controllers.study_outer_loop_parts.action_execution import (
    execute_controller_action as _execute_controller_action_impl,
)
from med_autoscience.controllers.study_outer_loop_parts.human_confirmation import (
    _build_family_human_gates_for_decision_record,
    _build_human_confirmation_request,
    _controller_confirmation_pending,
    _latest_controller_decision_matches_spec,
    _latest_controller_decision_requires_human_confirmation,
)
from med_autoscience.controllers.study_outer_loop_parts.recommendation_actions import (
    _publication_supervisor_human_gate_requested,
    _submission_milestone_route_context,
)
from med_autoscience.controllers.study_outer_loop_parts.runtime_refs import (
    _hydrate_managed_runtime_refs,
    _managed_runtime_requires_event_ref,
    _resolve_managed_runtime_event_contract,
    _resolve_runtime_escalation_record,
    _runtime_status_active_run_id,
    _runtime_status_summary,
)
from med_autoscience.controllers.study_outer_loop_parts.runtime_state import (
    _runtime_status_is_live,
)
from med_autoscience.controllers.study_runtime_resolution import _resolve_study
from med_autoscience.controller_confirmation_summary import (
    materialize_controller_confirmation_summary,
)
from med_autoscience.human_gate_policy import require_controller_human_gate_allowed
from med_autoscience.native_runtime_event import NativeRuntimeEventRecord
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_event_record import RuntimeEventRecord, RuntimeEventRecordRef
from med_autoscience.runtime.autonomy_governance import build_autonomy_governance_contract
from med_autoscience.runtime_protocol import study_runtime as study_runtime_protocol
from med_autoscience.study_decision_record import (
    StudyDecisionActionType,
    StudyDecisionCharterRef,
    StudyDecisionControllerAction,
    StudyDecisionPublicationEvalRef,
    StudyDecisionRecord,
    StudyDecisionType,
)

from med_autoscience.controllers.study_outer_loop_parts.tick_request import (
    build_runtime_watch_outer_loop_tick_request,
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _decision_id(*, study_id: str, quest_id: str, decision_type: str, recorded_at: str) -> str:
    return f"study-decision::{study_id}::{quest_id}::{decision_type}::{recorded_at}"


def _execute_controller_action(
    *,
    action: StudyDecisionControllerAction,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    quest_id: str,
    source: str,
) -> dict[str, Any]:
    return _execute_controller_action_impl(
        action=action,
        profile=profile,
        study_id=study_id,
        study_root=study_root,
        quest_id=quest_id,
        source=source,
        ensure_study_runtime_fn=study_runtime_router.ensure_study_runtime,
        execution_payload_fn=study_runtime_router._execution_payload,
        load_yaml_dict_fn=study_runtime_router._load_yaml_dict,
        managed_runtime_backend_for_execution_fn=study_runtime_router._managed_runtime_backend_for_execution,
        default_managed_runtime_backend_fn=study_runtime_router._default_managed_runtime_backend,
        run_gate_clearing_batch_fn=gate_clearing_batch.run_gate_clearing_batch,
        run_quality_repair_batch_fn=quality_repair_batch.run_quality_repair_batch,
    )


def _materialize_study_decision_record(
    *,
    status: dict[str, Any],
    runtime_status: dict[str, str],
    profile: WorkspaceProfile,
    resolved_study_id: str,
    resolved_study_root: Path,
    quest_id: str,
    charter_ref: StudyDecisionCharterRef | dict[str, Any],
    publication_eval_ref: StudyDecisionPublicationEvalRef | dict[str, Any],
    decision_type: str,
    route_target: str | None,
    route_key_question: str | None,
    route_rationale: str | None,
    source_route_key_question: str | None = None,
    work_unit_fingerprint: str | None = None,
    next_work_unit: dict[str, Any] | None = None,
    blocking_work_units: list[dict[str, Any]] | tuple[dict[str, Any], ...] | None = None,
    requires_human_confirmation: bool,
    controller_actions: list[dict[str, Any]] | tuple[StudyDecisionControllerAction, ...] | None,
    reason: str,
    source: str,
    recorded_at: str | None,
    runtime_escalation_payload: dict[str, Any] | None = None,
) -> tuple[StudyDecisionRecord, str | None, dict[str, Any], dict[str, str]]:
    normalized_charter_ref = _resolve_charter_ref(
        study_root=resolved_study_root,
        charter_ref=charter_ref,
    )
    normalized_publication_eval_ref = _resolve_publication_eval_ref(
        study_root=resolved_study_root,
        publication_eval_ref=publication_eval_ref,
    )
    emitted_at = recorded_at or _utc_now()
    publication_eval_payload = _read_publication_eval_payload(
        study_root=resolved_study_root,
        ref=normalized_publication_eval_ref.artifact_path,
    )
    runtime_escalation_ref, _runtime_escalation_record = _resolve_runtime_escalation_record(
        runtime_escalation_payload=runtime_escalation_payload if isinstance(runtime_escalation_payload, dict) else None,
        status=status,
        study_root=resolved_study_root,
        study_id=resolved_study_id,
        quest_id=quest_id,
        emitted_at=emitted_at,
        source=source,
        runtime_status=runtime_status,
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
    autonomy_governance_contract = build_autonomy_governance_contract(
        decision_type=decision_type,
        controller_action_types=(action.action_type for action in normalized_controller_actions),
        route_target=route_target,
        requires_human_confirmation=requires_human_confirmation,
        direction_locked=True,
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
            "work_unit_fingerprint": work_unit_fingerprint,
            "next_work_unit": dict(next_work_unit) if isinstance(next_work_unit, dict) else None,
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
            route_target=route_target,
            route_key_question=route_key_question,
            route_rationale=route_rationale,
            source_route_key_question=source_route_key_question,
            work_unit_fingerprint=work_unit_fingerprint,
            next_work_unit=dict(next_work_unit) if isinstance(next_work_unit, dict) else None,
            blocking_work_units=tuple(blocking_work_units or ()),
            autonomy_governance_contract=autonomy_governance_contract,
            family_event_envelope=family_companion["family_event_envelope"],
            family_checkpoint_lineage=family_companion["family_checkpoint_lineage"],
            family_human_gates=tuple(family_companion["family_human_gates"]),
        ),
    )
    confirmation_summary_ref = materialize_controller_confirmation_summary(
        study_root=resolved_study_root,
        decision_ref=written_record.ref().to_dict(),
    )
    return written_record, confirmation_summary_ref, publication_eval_payload, runtime_status


def study_outer_loop_tick(
    *,
    profile: WorkspaceProfile,
    study_id: str | None = None,
    study_root: Path | None = None,
    charter_ref: StudyDecisionCharterRef | dict[str, Any],
    publication_eval_ref: StudyDecisionPublicationEvalRef | dict[str, Any],
    decision_type: str,
    route_target: str | None = None,
    route_key_question: str | None = None,
    route_rationale: str | None = None,
    source_route_key_question: str | None = None,
    work_unit_fingerprint: str | None = None,
    next_work_unit: dict[str, Any] | None = None,
    blocking_work_units: list[dict[str, Any]] | tuple[dict[str, Any], ...] | None = None,
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
    status = _hydrate_managed_runtime_refs(status)
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
    written_record, confirmation_summary_ref, publication_eval_payload, runtime_status = _materialize_study_decision_record(
        status=status,
        runtime_status=runtime_status,
        profile=profile,
        resolved_study_id=resolved_study_id,
        resolved_study_root=resolved_study_root,
        quest_id=quest_id,
        charter_ref=charter_ref,
        publication_eval_ref=publication_eval_ref,
        decision_type=decision_type,
        route_target=route_target,
        route_key_question=route_key_question,
        route_rationale=route_rationale,
        source_route_key_question=source_route_key_question,
        work_unit_fingerprint=work_unit_fingerprint,
        next_work_unit=next_work_unit,
        blocking_work_units=blocking_work_units,
        requires_human_confirmation=requires_human_confirmation,
        controller_actions=controller_actions,
        reason=reason,
        source=source,
        recorded_at=recorded_at,
        runtime_escalation_payload=runtime_escalation_payload if isinstance(runtime_escalation_payload, dict) else None,
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
    dispatch_status = "executed"
    action_result = executed_controller_action.get("result")
    if isinstance(action_result, dict) and action_result.get("ok") is False:
        dispatch_status = "blocked"
    return {
        "study_id": resolved_study_id,
        "quest_id": quest_id,
        "source": source,
        "runtime_status": runtime_status,
        "runtime_escalation_ref": written_record.runtime_escalation_ref.to_dict(),
        "study_decision_ref": written_record.ref().to_dict(),
        "controller_confirmation_summary_ref": confirmation_summary_ref,
        "dispatch_status": dispatch_status,
        "executed_controller_action": executed_controller_action,
    }


def materialize_non_dispatching_outer_loop_decision(
    *,
    profile: WorkspaceProfile,
    study_id: str | None = None,
    study_root: Path | None = None,
    status_payload: dict[str, Any] | None = None,
    charter_ref: StudyDecisionCharterRef | dict[str, Any],
    publication_eval_ref: StudyDecisionPublicationEvalRef | dict[str, Any],
    decision_type: str,
    route_target: str | None = None,
    route_key_question: str | None = None,
    route_rationale: str | None = None,
    source_route_key_question: str | None = None,
    work_unit_fingerprint: str | None = None,
    next_work_unit: dict[str, Any] | None = None,
    blocking_work_units: list[dict[str, Any]] | tuple[dict[str, Any], ...] | None = None,
    requires_human_confirmation: bool = False,
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
    status = (
        dict(status_payload)
        if isinstance(status_payload, dict)
        else study_runtime_router.study_runtime_status(
            profile=profile,
            study_id=resolved_study_id,
            study_root=resolved_study_root,
        )
    )
    status = _hydrate_managed_runtime_refs(status)
    runtime_status = _runtime_status_summary(status)
    quest_id = str(status.get("quest_id") or "").strip()
    if not quest_id:
        raise ValueError("non-dispatching outer-loop decision requires quest_id")
    written_record, confirmation_summary_ref, _publication_eval_payload, runtime_status = _materialize_study_decision_record(
        status=status,
        runtime_status=runtime_status,
        profile=profile,
        resolved_study_id=resolved_study_id,
        resolved_study_root=resolved_study_root,
        quest_id=quest_id,
        charter_ref=charter_ref,
        publication_eval_ref=publication_eval_ref,
        decision_type=decision_type,
        route_target=route_target,
        route_key_question=route_key_question,
        route_rationale=route_rationale,
        source_route_key_question=source_route_key_question,
        work_unit_fingerprint=work_unit_fingerprint,
        next_work_unit=next_work_unit,
        blocking_work_units=blocking_work_units,
        requires_human_confirmation=requires_human_confirmation,
        controller_actions=controller_actions,
        reason=reason,
        source=source,
        recorded_at=recorded_at,
        runtime_escalation_payload=status.get("runtime_escalation_ref") if isinstance(status.get("runtime_escalation_ref"), dict) else None,
    )
    return {
        "study_id": resolved_study_id,
        "quest_id": quest_id,
        "source": source,
        "runtime_status": runtime_status,
        "runtime_escalation_ref": written_record.runtime_escalation_ref.to_dict(),
        "study_decision_ref": written_record.ref().to_dict(),
        "controller_confirmation_summary_ref": confirmation_summary_ref,
        "dispatch_status": "recorded_non_dispatching",
        "executed_controller_action": None,
    }


def refresh_parked_submission_milestone_controller_decision(
    *,
    profile: WorkspaceProfile,
    study_id: str | None = None,
    study_root: Path | None = None,
    status_payload: dict[str, Any] | None = None,
    source: str = "submission-minimal-post-materialization",
    recorded_at: str | None = None,
) -> dict[str, Any] | None:
    resolved_study_id, resolved_study_root, _study_payload = _resolve_study(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
    )
    status = (
        dict(status_payload)
        if isinstance(status_payload, dict)
        else study_runtime_router.study_runtime_status(
            profile=profile,
            study_id=resolved_study_id,
            study_root=resolved_study_root,
        )
    )
    status = _hydrate_managed_runtime_refs(status)
    if _publication_supervisor_human_gate_requested(status):
        return None
    if _controller_confirmation_pending(study_root=resolved_study_root):
        return None
    if _latest_controller_decision_requires_human_confirmation(study_root=resolved_study_root):
        return None
    if _runtime_status_is_live(status):
        return None

    publication_eval_entry = _read_latest_publication_eval_payload(study_root=resolved_study_root)
    if publication_eval_entry is None:
        return None
    publication_eval_path, publication_eval_payload = publication_eval_entry
    route_context = _submission_milestone_route_context(
        study_root=resolved_study_root,
        publication_eval_payload=publication_eval_payload,
    )
    if route_context is None:
        return None

    charter_ref = _build_study_decision_charter_ref(
        study_root=resolved_study_root,
        missing_message="parked submission milestone refresh requires stable study charter artifact",
    )
    quest_id = (
        str(status.get("quest_id") or "").strip()
        or str(publication_eval_payload.get("quest_id") or "").strip()
    )
    if not quest_id:
        raise ValueError("parked submission milestone refresh requires quest_id")
    runtime_status = _runtime_status_summary(status)
    reason = "Submission-package milestone remains parked; keep the runtime stopped until explicit resume."
    controller_actions = (
        StudyDecisionControllerAction(
            action_type=StudyDecisionActionType.STOP_RUNTIME,
            payload_ref=str((resolved_study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()),
        ),
    )
    publication_eval_ref = StudyDecisionPublicationEvalRef(
        eval_id=str(publication_eval_payload.get("eval_id") or "").strip(),
        artifact_path=str(publication_eval_path),
    )
    runtime_escalation_payload = status.get("runtime_escalation_ref")
    runtime_escalation_ref, _runtime_escalation_record = _resolve_runtime_escalation_record(
        runtime_escalation_payload=runtime_escalation_payload if isinstance(runtime_escalation_payload, dict) else None,
        status=status,
        study_root=resolved_study_root,
        study_id=resolved_study_id,
        quest_id=quest_id,
        emitted_at=recorded_at or _utc_now(),
        source=source,
        runtime_status=runtime_status,
    )
    if _latest_controller_decision_matches_spec(
        study_root=resolved_study_root,
        decision_type=StudyDecisionType.CONTINUE_SAME_LINE.value,
        requires_human_confirmation=False,
        reason=reason,
        charter_ref=charter_ref,
        publication_eval_ref=publication_eval_ref,
        controller_actions=controller_actions,
        runtime_escalation_ref=runtime_escalation_ref,
        route_target=str(route_context.get("route_target") or "").strip() or None,
        route_key_question=str(route_context.get("route_key_question") or "").strip() or None,
        route_rationale=str(route_context.get("route_rationale") or "").strip() or None,
    ):
        return {
            "status": "already_current",
            "study_decision_ref": StudyDecisionRecord.from_payload(
                json.loads(
                    (
                        resolved_study_root / "artifacts" / "controller_decisions" / "latest.json"
                    ).read_text(encoding="utf-8")
                )
            ).ref().to_dict(),
            "decision_type": StudyDecisionType.CONTINUE_SAME_LINE.value,
            "route_target": str(route_context.get("route_target") or "").strip() or None,
        }

    written_record, confirmation_summary_ref, _publication_eval_payload, _runtime_status = _materialize_study_decision_record(
        status=status,
        runtime_status=runtime_status,
        profile=profile,
        resolved_study_id=resolved_study_id,
        resolved_study_root=resolved_study_root,
        quest_id=quest_id,
        charter_ref=charter_ref.to_dict(),
        publication_eval_ref=publication_eval_ref.to_dict(),
        decision_type=StudyDecisionType.CONTINUE_SAME_LINE.value,
        route_target=str(route_context.get("route_target") or "").strip() or None,
        route_key_question=str(route_context.get("route_key_question") or "").strip() or None,
        route_rationale=str(route_context.get("route_rationale") or "").strip() or None,
        requires_human_confirmation=False,
        controller_actions=controller_actions,
        reason=reason,
        source=source,
        recorded_at=recorded_at,
        runtime_escalation_payload=runtime_escalation_ref.to_dict(),
    )
    return {
        "status": "refreshed",
        "study_id": resolved_study_id,
        "quest_id": quest_id,
        "study_decision_ref": written_record.ref().to_dict(),
        "controller_confirmation_summary_ref": confirmation_summary_ref,
        "decision_type": written_record.decision_type.value,
        "route_target": written_record.route_target,
        "route_key_question": written_record.route_key_question,
        "route_rationale": written_record.route_rationale,
        "reason": written_record.reason,
    }
