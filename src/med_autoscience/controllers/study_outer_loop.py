from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.controllers import study_runtime_router
from med_autoscience.controllers import study_runtime_family_orchestration as family_orchestration
from med_autoscience.controllers import gate_clearing_batch
from med_autoscience.controllers import publication_gate as publication_gate_controller
from med_autoscience.controllers import quality_repair_batch
from med_autoscience.controllers.study_outer_loop_parts.decision_refs import (
    _build_study_decision_charter_ref,
    _latest_task_intake_yields_to_fast_lane_closeout,
    _read_evaluation_summary_payload,
    _read_latest_publication_eval_payload,
    _read_publication_eval_payload,
    _resolve_charter_ref,
    _resolve_publication_eval_ref,
    read_publication_eval_latest,
)
from med_autoscience.controllers.study_outer_loop_parts.human_confirmation import (
    _build_family_human_gates_for_decision_record,
    _build_human_confirmation_request,
    _controller_confirmation_pending,
    _latest_controller_decision_matches_spec,
    _latest_controller_decision_requires_human_confirmation,
)
from med_autoscience.controllers.study_outer_loop_parts.runtime_refs import (
    _hydrate_managed_runtime_refs,
    _managed_runtime_requires_event_ref,
    _resolve_managed_runtime_event_contract,
    _resolve_runtime_escalation_record,
    _runtime_status_active_run_id,
    _runtime_status_summary,
)
from med_autoscience.controllers.study_runtime_resolution import _resolve_study
from med_autoscience.controllers.study_outer_loop_task_intake import recommended_task_intake_action
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

def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _decision_id(*, study_id: str, quest_id: str, decision_type: str, recorded_at: str) -> str:
    return f"study-decision::{study_id}::{quest_id}::{decision_type}::{recorded_at}"


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
        if _autonomous_decision_type_for_publication_eval_action(action) is None:
            continue
        return dict(action)
    return None


def _quality_dimension_status(*, payload: dict[str, Any], dimension: str) -> str | None:
    quality_assessment = payload.get("quality_assessment")
    if not isinstance(quality_assessment, dict):
        return None
    dimension_payload = quality_assessment.get(dimension)
    if not isinstance(dimension_payload, dict):
        return None
    status = str(dimension_payload.get("status") or "").strip()
    return status or None


def _publication_eval_has_only_optional_gaps(publication_eval_payload: dict[str, Any]) -> bool:
    gaps = publication_eval_payload.get("gaps")
    if not isinstance(gaps, list):
        return False
    for gap in gaps:
        if not isinstance(gap, dict):
            return False
        if str(gap.get("severity") or "").strip() != "optional":
            return False
    return True


def _runtime_status_is_live(status_payload: dict[str, Any]) -> bool:
    runtime_liveness_status = str(status_payload.get("runtime_liveness_status") or "").strip()
    if runtime_liveness_status == "live":
        return True
    runtime_liveness_audit = status_payload.get("runtime_liveness_audit")
    if isinstance(runtime_liveness_audit, dict) and str(runtime_liveness_audit.get("status") or "").strip() == "live":
        return True
    return str(status_payload.get("quest_status") or "").strip() in {"active", "running"}


def _parked_submission_milestone_manual_finish(status_payload: dict[str, Any]) -> bool:
    reason = str(status_payload.get("reason") or "").strip()
    if reason not in {
        "quest_waiting_for_submission_metadata",
        "quest_waiting_for_submission_metadata_but_auto_resume_disabled",
    }:
        return False
    continuation_state = status_payload.get("continuation_state")
    if not isinstance(continuation_state, dict):
        return True
    if str(continuation_state.get("active_run_id") or "").strip():
        return False
    continuation_policy = str(continuation_state.get("continuation_policy") or "").strip()
    return not continuation_policy or continuation_policy == "wait_for_user_or_resume"


def _submission_milestone_route_context(
    *,
    study_root: Path,
    publication_eval_payload: dict[str, Any],
) -> dict[str, Any] | None:
    summary_payload = _read_evaluation_summary_payload(study_root=study_root)
    if summary_payload is None:
        return None
    quality_closure_truth = (
        dict(summary_payload.get("quality_closure_truth") or {})
        if isinstance(summary_payload.get("quality_closure_truth"), dict)
        else {}
    )
    if str(quality_closure_truth.get("state") or "").strip() != "bundle_only_remaining":
        return None
    verdict = publication_eval_payload.get("verdict")
    if not isinstance(verdict, dict) or str(verdict.get("overall_verdict") or "").strip() != "promising":
        return None
    if not _publication_eval_has_only_optional_gaps(publication_eval_payload):
        return None
    human_review_status = _quality_dimension_status(
        payload=summary_payload,
        dimension="human_review_readiness",
    ) or _quality_dimension_status(
        payload=publication_eval_payload,
        dimension="human_review_readiness",
    )
    if human_review_status != "ready":
        return None
    quality_execution_lane = (
        dict(summary_payload.get("quality_execution_lane") or {})
        if isinstance(summary_payload.get("quality_execution_lane"), dict)
        else {}
    )
    route_target = str(
        quality_execution_lane.get("route_target") or quality_closure_truth.get("route_target") or ""
    ).strip()
    if route_target and route_target != "finalize":
        return None
    route_key_question = str(quality_execution_lane.get("route_key_question") or "").strip()
    route_rationale = str(
        quality_execution_lane.get("summary")
        or quality_closure_truth.get("summary")
        or "Human-review milestone reached and only finalize-level bundle cleanup remains."
    ).strip()
    return {
        "summary_payload": summary_payload,
        "route_target": "finalize",
        "route_key_question": route_key_question
        or "当前论文线还差哪一个最窄的定稿或投稿包收尾动作？",
        "route_rationale": route_rationale,
    }


def _recommended_submission_milestone_autopark_action(
    *,
    study_root: Path,
    status_payload: dict[str, Any],
    publication_eval_payload: dict[str, Any],
) -> dict[str, Any] | None:
    if not _runtime_status_is_live(status_payload):
        return None
    route_context = _submission_milestone_route_context(
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    )
    if route_context is None:
        return None
    return {
        "action_id": f"quality-milestone::{study_root.name}::autopark",
        "action_type": StudyDecisionType.CONTINUE_SAME_LINE.value,
        "priority": "now",
        "reason": "Human-review milestone reached; stop the live runtime and wait for explicit resume.",
        "route_target": str(route_context.get("route_target") or "").strip() or "finalize",
        "route_key_question": str(route_context.get("route_key_question") or "").strip()
        or "当前论文线还差哪一个最窄的定稿或投稿包收尾动作？",
        "route_rationale": str(route_context.get("route_rationale") or "").strip(),
        "requires_controller_decision": True,
        "controller_action_type": StudyDecisionActionType.STOP_RUNTIME.value,
    }


def _recommended_manuscript_fast_lane_closeout_autopark_action(
    *,
    study_root: Path,
    status_payload: dict[str, Any],
) -> dict[str, Any] | None:
    if not _runtime_status_is_live(status_payload):
        return None
    return {
        "action_id": f"manuscript-fast-lane-closeout::{study_root.name}::autopark",
        "action_type": StudyDecisionType.CONTINUE_SAME_LINE.value,
        "priority": "now",
        "reason": (
            "Manuscript fast lane closeout supersedes the latest task intake; "
            "stop the live runtime and wait for explicit resume."
        ),
        "route_target": "write",
        "route_key_question": "Should MAS/MDS resume this paper line after foreground fast lane closeout?",
        "route_rationale": (
            "A controller-visible manuscript fast lane closeout is newer than the latest task intake and "
            "declares that the superseded task intake must not auto-resume."
        ),
        "requires_controller_decision": True,
        "controller_action_type": StudyDecisionActionType.STOP_RUNTIME.value,
    }


def _recommended_quality_review_loop_action(*, study_root: Path) -> dict[str, Any] | None:
    summary_payload = _read_evaluation_summary_payload(study_root=study_root)
    if summary_payload is None:
        return None
    quality_review_loop = (
        dict(summary_payload.get("quality_review_loop") or {})
        if isinstance(summary_payload.get("quality_review_loop"), dict)
        else {}
    )
    current_phase = str(quality_review_loop.get("current_phase") or "").strip()
    if current_phase != "re_review_required" and quality_review_loop.get("re_review_ready") is not True:
        return None
    next_review_focus = [
        str(item).strip()
        for item in (quality_review_loop.get("next_review_focus") or [])
        if str(item).strip()
    ]
    route_key_question = next_review_focus[0] if next_review_focus else "当前 blocking issues 是否已真正闭环？"
    summary = str(quality_review_loop.get("summary") or "").strip()
    recommended_next_action = str(quality_review_loop.get("recommended_next_action") or "").strip()
    reason = recommended_next_action or summary or "MAS 应发起下一轮质量复评，确认当前 blocking issues 是否已真正闭环。"
    route_rationale = summary or reason
    return {
        "action_id": f"quality-review-loop::{quality_review_loop.get('loop_id') or study_root.name}::re_review",
        "action_type": StudyDecisionType.CONTINUE_SAME_LINE.value,
        "priority": "now",
        "reason": reason,
        "route_target": "review",
        "route_key_question": route_key_question,
        "route_rationale": route_rationale,
        "requires_controller_decision": True,
    }


def _autonomous_decision_type_for_publication_eval_action(action_payload: dict[str, Any]) -> str | None:
    action_type = str(action_payload.get("action_type") or "").strip()
    if action_type == StudyDecisionType.CONTINUE_SAME_LINE.value:
        return StudyDecisionType.CONTINUE_SAME_LINE.value
    if action_type == StudyDecisionType.ROUTE_BACK_SAME_LINE.value:
        return StudyDecisionType.ROUTE_BACK_SAME_LINE.value
    if action_type == StudyDecisionType.BOUNDED_ANALYSIS.value:
        return StudyDecisionType.BOUNDED_ANALYSIS.value
    if action_type == StudyDecisionType.STOP_LOSS.value:
        return StudyDecisionType.STOP_LOSS.value
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
    status_payload = _hydrate_managed_runtime_refs(status_payload)
    if _parked_submission_milestone_manual_finish(status_payload):
        return None
    if _publication_supervisor_human_gate_requested(status_payload):
        return None
    if _controller_confirmation_pending(study_root=resolved_study_root):
        return None
    if _latest_controller_decision_requires_human_confirmation(study_root=resolved_study_root):
        return None

    publication_eval_entry = _read_latest_publication_eval_payload(study_root=resolved_study_root)
    if publication_eval_entry is None:
        return None
    publication_eval_path, publication_eval_payload = publication_eval_entry
    profile = gate_clearing_batch.resolve_profile_for_study_root(resolved_study_root)
    quest_id = str(status_payload.get("quest_id") or "").strip()
    gate_report: dict[str, Any] = {}
    if profile is not None and quest_id:
        quest_root = Path(profile.runtime_root).expanduser().resolve() / quest_id
        gate_report = publication_gate_controller.build_gate_report(
            publication_gate_controller.build_gate_state(quest_root)
        )
    evaluation_summary = _read_evaluation_summary_payload(study_root=resolved_study_root)
    task_intake_yields_to_fast_lane_closeout = _latest_task_intake_yields_to_fast_lane_closeout(
        study_root=resolved_study_root,
    )
    if task_intake_yields_to_fast_lane_closeout:
        recommended_action = _recommended_manuscript_fast_lane_closeout_autopark_action(
            study_root=resolved_study_root,
            status_payload=status_payload,
        )
    else:
        task_intake_action = recommended_task_intake_action(
            study_root=resolved_study_root,
            publishability_gate_report=gate_report,
            evaluation_summary=evaluation_summary,
        )
        recommended_action = task_intake_action or _recommended_submission_milestone_autopark_action(
            study_root=resolved_study_root,
            status_payload=status_payload,
            publication_eval_payload=publication_eval_payload,
        )
        if recommended_action is None:
            recommended_action = _recommended_quality_review_loop_action(study_root=resolved_study_root)
        if recommended_action is None:
            recommended_action = _recommended_publication_eval_action(publication_eval_payload)
        if profile is not None and task_intake_action is None:
            batch_action = quality_repair_batch.build_quality_repair_batch_recommended_action(
                profile=profile,
                study_root=resolved_study_root,
                quest_id=quest_id,
                publication_eval_payload=publication_eval_payload,
                gate_report=gate_report,
            )
            if batch_action is None:
                batch_action = gate_clearing_batch.build_gate_clearing_batch_recommended_action(
                    profile=profile,
                    study_root=resolved_study_root,
                    quest_id=quest_id,
                    publication_eval_payload=publication_eval_payload,
                    gate_report=gate_report,
                )
            if batch_action is not None:
                recommended_action = batch_action
    if recommended_action is None:
        return None
    decision_type = _autonomous_decision_type_for_publication_eval_action(recommended_action)
    if decision_type is None:
        return None

    charter_ref = _build_study_decision_charter_ref(
        study_root=resolved_study_root,
        missing_message="runtime watch outer-loop wakeup requires stable study charter artifact",
    ).to_dict()

    runtime_escalation_payload = status_payload.get("runtime_escalation_ref")
    if runtime_escalation_payload is not None:
        if not isinstance(runtime_escalation_payload, dict):
            raise ValueError("runtime watch outer-loop wakeup runtime_escalation_ref must be a mapping when present")
        _resolve_runtime_escalation_record(runtime_escalation_payload=runtime_escalation_payload)

    publication_eval_ref = StudyDecisionPublicationEvalRef(
        eval_id=str(publication_eval_payload.get("eval_id") or "").strip(),
        artifact_path=str(publication_eval_path),
    ).to_dict()
    controller_action_type = str(recommended_action.get("controller_action_type") or "").strip()
    if not controller_action_type:
        if decision_type == StudyDecisionType.STOP_LOSS.value:
            controller_action_type = StudyDecisionActionType.STOP_RUNTIME.value
        else:
            controller_action_type = _autonomous_controller_action_type_for_runtime_status(status_payload)
    controller_action = StudyDecisionControllerAction(
        action_type=controller_action_type,
        payload_ref=str((resolved_study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()),
    ).to_dict()
    return {
        "study_root": resolved_study_root,
        "charter_ref": charter_ref,
        "publication_eval_ref": publication_eval_ref,
        "decision_type": decision_type,
        "route_target": str(recommended_action.get("route_target") or "").strip() or None,
        "route_key_question": str(recommended_action.get("route_key_question") or "").strip() or None,
        "route_rationale": str(recommended_action.get("route_rationale") or "").strip() or None,
        "requires_human_confirmation": False,
        "controller_actions": [controller_action],
        "reason": str(recommended_action.get("reason") or "").strip()
        or "publication eval requests an autonomous controller decision for the current line.",
        "work_unit_fingerprint": str(recommended_action.get("work_unit_fingerprint") or "").strip() or None,
        "next_work_unit": dict(recommended_action.get("next_work_unit") or {}) if isinstance(recommended_action.get("next_work_unit"), dict) else None,
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
    elif action.action_type is StudyDecisionActionType.RUN_GATE_CLEARING_BATCH:
        result = gate_clearing_batch.run_gate_clearing_batch(
            profile=profile,
            study_id=study_id,
            study_root=study_root,
            quest_id=quest_id,
            source=source,
        )
    elif action.action_type is StudyDecisionActionType.RUN_QUALITY_REPAIR_BATCH:
        result = quality_repair_batch.run_quality_repair_batch(
            profile=profile,
            study_id=study_id,
            study_root=study_root,
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
