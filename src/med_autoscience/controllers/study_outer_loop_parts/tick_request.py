from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from med_autoscience.controllers import gate_clearing_batch
from med_autoscience.controllers import publication_gate as publication_gate_controller
from med_autoscience.controllers import publication_work_unit_lifecycle
from med_autoscience.controllers import publication_work_units
from med_autoscience.controllers import quality_repair_batch
from med_autoscience.controllers.quality_repair_batch_parts import story_surface_delta
from med_autoscience.controllers.study_domain_transition_table_parts import publication_gate_lifecycle_transitions
from med_autoscience.controllers import domain_transition_currentness
from med_autoscience.controllers.study_outer_loop_parts.decision_refs import (
    _build_study_decision_charter_ref,
    _latest_task_intake_yields_to_verified_fast_lane_closeout,
    _read_evaluation_summary_payload,
    _read_latest_publication_eval_payload,
)
from med_autoscience.controllers.study_outer_loop_parts.domain_transition_actions import (
    domain_transition_recommended_action,
)
from med_autoscience.controllers.study_outer_loop_parts.human_confirmation import (
    _controller_confirmation_pending,
    _latest_controller_decision_requires_human_confirmation,
)
from med_autoscience.controllers.study_outer_loop_parts.methodology_analysis_routes import (
    merge_publication_eval_methodology_work_unit as _merge_publication_eval_methodology_work_unit,
    methodology_analysis_route_preempts_ai_reviewer_recheck as _methodology_analysis_route_preempts_ai_reviewer_recheck,
)
from med_autoscience.controllers.study_outer_loop_parts.owner_priority import (
    bundle_stage_publication_eval_preempts_task_intake,
    gate_clearing_preempts_task_intake,
    startup_freshness_requires_gate_clearing,
)
from med_autoscience.controllers.study_outer_loop_parts.recommendation_actions import (
    _GATE_NEEDS_SPECIFICITY_QUESTION,
    _autonomous_controller_action_type_for_runtime_status,
    _autonomous_decision_type_for_publication_eval_action,
    _current_ai_reviewer_route_back_preempts_ai_reviewer_recheck,
    _promote_gate_needs_specificity_action,
    _publication_supervisor_human_gate_requested,
    _quality_repair_batch_preempts_task_intake,
    _recommended_manuscript_fast_lane_closeout_autopark_action,
    _recommended_publication_eval_action,
    _recommended_quality_review_loop_action,
    _recommended_submission_milestone_autopark_action,
)
from med_autoscience.controllers.study_outer_loop_parts.runtime_refs import (
    _hydrate_managed_runtime_refs,
    _resolve_runtime_escalation_record,
)
from med_autoscience.controllers.study_outer_loop_parts.runtime_state import (
    _parked_submission_milestone_manual_finish,
    _runtime_status_is_live,
)
from med_autoscience.controllers.study_outer_loop_task_intake import recommended_task_intake_action
from med_autoscience.publication_eval_specificity_targets import specificity_target_status
from med_autoscience.study_decision_record import (
    StudyDecisionActionType,
    StudyDecisionControllerAction,
    StudyDecisionPublicationEvalRef,
    StudyDecisionType,
)


_WORK_UNIT_TARGET_CONTEXT_KEYS = (
    "specificity_targets",
    "work_unit_targets",
    "blocking_artifact_refs",
    "blocker_details",
    "gate_blocker_details",
    "gaps",
    "source_path",
)
_BUNDLE_STAGE_CURRENT_REQUIRED_ACTIONS = frozenset({"continue_bundle_stage", "complete_bundle_stage"})
_FINALIZE_WORK_UNIT_IDS = frozenset(
    {
        "submission_authority_sync_closure",
        "submission_minimal_refresh",
        "submission_delivery_sync_closure",
        "publication_gate_replay",
    }
)


def _read_closed_publication_gate_recheck_lifecycle(study_root: Path) -> dict[str, Any] | None:
    resolved_study_root = Path(study_root).expanduser().resolve()
    lifecycle_path = publication_work_unit_lifecycle.stable_publication_work_unit_lifecycle_path(
        study_root=resolved_study_root
    )
    try:
        payload = json.loads(lifecycle_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    if not publication_work_unit_lifecycle.lifecycle_payload_is_closed(payload):
        return None
    if str(payload.get("recommended_next_route") or "").strip() != "return_to_publication_gate_recheck":
        return None
    if str(payload.get("next_owner") or "").strip() != "publication_gate":
        return None
    work_unit = payload.get("work_unit")
    if isinstance(work_unit, dict) and str(work_unit.get("unit_id") or "").strip() == "publication_gate_recheck":
        return None
    publication_eval_entry = _read_latest_publication_eval_payload(study_root=resolved_study_root)
    publication_eval_payload = publication_eval_entry[1] if publication_eval_entry is not None else {}
    if publication_gate_lifecycle_transitions.lifecycle_is_stale_for_publication_eval(
        lifecycle=payload,
        publication_eval=publication_eval_payload,
    ):
        return None
    if story_surface_delta.ai_reviewer_recheck_supersedes_lifecycle(
        study_root=resolved_study_root,
        lifecycle=payload,
        publication_eval=publication_eval_payload,
        repair_evidence_path=resolved_study_root / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json",
    ):
        return None
    return payload


def _publication_gate_recheck_action_from_closed_lifecycle(
    *,
    lifecycle: dict[str, Any],
) -> dict[str, Any]:
    work_unit = dict(lifecycle.get("work_unit") or {}) if isinstance(lifecycle.get("work_unit"), dict) else {}
    return {
        "action_id": "publication-work-unit-lifecycle::publication_gate_recheck",
        "action_type": StudyDecisionType.ROUTE_BACK_SAME_LINE.value,
        "priority": "now",
        "reason": "publication_gate_recheck_required",
        "route_target": "review",
        "route_key_question": "已完成的 publication work unit 是否通过 publication gate replay？",
        "route_rationale": (
            "A controller-owned work unit has been consumed and handed off to the publication gate; "
            "replay the gate before any stale same-line repair can be dispatched again."
        ),
        "requires_controller_decision": True,
        "controller_action_type": StudyDecisionActionType.RUN_GATE_CLEARING_BATCH.value,
        "work_unit_fingerprint": "publication-gate-recheck::closed-work-unit",
        "next_work_unit": {
            "unit_id": "publication_gate_recheck",
            "lane": "review",
            "summary": "Replay the publication gate for the closed controller work unit.",
            "source_work_unit": work_unit or None,
        },
        "blocking_work_units": [
            {
                "unit_id": "publication_gate_recheck",
                "lane": "review",
                "summary": "Replay the publication gate for the closed controller work unit.",
            }
        ],
    }


def _action_next_work_unit(action_payload: dict[str, Any]) -> dict[str, Any]:
    next_work_unit = action_payload.get("next_work_unit")
    return dict(next_work_unit) if isinstance(next_work_unit, dict) else {}


def _action_work_unit_id(action_payload: dict[str, Any]) -> str | None:
    text = str(_action_next_work_unit(action_payload).get("unit_id") or "").strip()
    return text or None


def _action_work_unit_fingerprint(action_payload: dict[str, Any]) -> str | None:
    text = str(action_payload.get("work_unit_fingerprint") or "").strip()
    if text:
        return text
    next_work_unit = _action_next_work_unit(action_payload)
    text = str(next_work_unit.get("fingerprint") or "").strip()
    return text or None


def _specificity_target_context_from_publication_eval(
    *,
    publication_eval_payload: dict[str, Any],
    recommended_action: dict[str, Any],
) -> dict[str, Any]:
    recommended_fingerprint = _action_work_unit_fingerprint(recommended_action)
    recommended_unit_id = _action_work_unit_id(recommended_action)
    actions = publication_eval_payload.get("recommended_actions")
    if not isinstance(actions, list):
        return {}
    for action in actions:
        if not isinstance(action, dict):
            continue
        action_fingerprint = _action_work_unit_fingerprint(action)
        action_unit_id = _action_work_unit_id(action)
        fingerprint_matches = (
            recommended_fingerprint is not None
            and action_fingerprint is not None
            and action_fingerprint == recommended_fingerprint
        )
        unit_matches = recommended_fingerprint is None and recommended_unit_id is not None and action_unit_id == recommended_unit_id
        if not fingerprint_matches and not unit_matches:
            continue
        if specificity_target_status(action.get("specificity_targets")).get("complete") is not True:
            continue
        return {
            key: action[key]
            for key in _WORK_UNIT_TARGET_CONTEXT_KEYS
            if key in action
        }
    return {}


def _gate_report_is_bundle_stage(gate_report: dict[str, Any]) -> bool:
    status = str(gate_report.get("status") or "").strip()
    if status not in {"blocked", "clear"}:
        return False
    if gate_report.get("allow_write") is False:
        supervisor_phase = str(gate_report.get("supervisor_phase") or "").strip()
        if supervisor_phase != "bundle_stage_blocked":
            return False
    if status == "clear":
        blockers = [
            str(item or "").strip()
            for item in (gate_report.get("blockers") or [])
            if str(item or "").strip()
        ]
        if blockers:
            return False
    current_required_action = str(gate_report.get("current_required_action") or "").strip()
    if current_required_action not in _BUNDLE_STAGE_CURRENT_REQUIRED_ACTIONS:
        return False
    return True


def _status_payload_reports_bundle_stage(status_payload: dict[str, Any]) -> bool:
    publication_supervisor_state = status_payload.get("publication_supervisor_state")
    if not isinstance(publication_supervisor_state, dict):
        return False
    supervisor_phase = str(publication_supervisor_state.get("supervisor_phase") or "").strip()
    if supervisor_phase not in {"bundle_stage_ready", "bundle_stage_blocked"}:
        return False
    current_required_action = str(publication_supervisor_state.get("current_required_action") or "").strip()
    return current_required_action in _BUNDLE_STAGE_CURRENT_REQUIRED_ACTIONS


def _bundle_stage_finalize_action_from_publication_eval(
    *,
    publication_eval_payload: dict[str, Any],
    gate_report: dict[str, Any],
) -> dict[str, Any] | None:
    if not _gate_report_is_bundle_stage(gate_report):
        return None
    action = _recommended_publication_eval_action(publication_eval_payload)
    if action is None:
        return None
    work_unit_payload = publication_work_units.derive_publication_work_units(
        gate_report,
        specificity_targets=publication_work_units.specificity_targets_from_publication_eval(
            publication_eval_payload
        ),
    )
    next_work_unit = work_unit_payload.get("next_work_unit")
    if not isinstance(next_work_unit, dict):
        return action
    unit_id = str(next_work_unit.get("unit_id") or "").strip()
    if unit_id not in _FINALIZE_WORK_UNIT_IDS:
        return action
    return {
        **action,
        "action_type": StudyDecisionType.CONTINUE_SAME_LINE.value,
        "route_target": "finalize",
        "route_key_question": str(action.get("route_key_question") or "").strip()
        or "当前论文线还差哪一个最窄的定稿或投稿包收尾动作？",
        "route_rationale": str(action.get("route_rationale") or action.get("reason") or "").strip()
        or "The publication gate is clear and bundle-stage work is now on the critical path.",
        "work_unit_fingerprint": work_unit_payload.get("fingerprint"),
        "blocking_work_units": work_unit_payload.get("blocking_work_units") or [],
        "next_work_unit": dict(next_work_unit),
        "blocking_artifact_refs": work_unit_payload.get("blocking_artifact_refs") or [],
    }


def _target_ready_next_work_unit(next_work_unit: dict[str, Any] | None, target_context: dict[str, Any]) -> dict[str, Any] | None:
    if not isinstance(next_work_unit, dict):
        return None
    if specificity_target_status(target_context.get("specificity_targets")).get("complete") is not True:
        return dict(next_work_unit)
    sanitized = dict(next_work_unit)
    sanitized.pop("non_executable_reason", None)
    sanitized.pop("required_target_kinds", None)
    if sanitized.get("controller_work_unit_executable") is False:
        sanitized.pop("controller_work_unit_executable", None)
    return sanitized


def build_domain_health_diagnostic_outer_loop_tick_request(
    *,
    study_root: Path,
    status_payload: dict[str, Any],
    publication_gate_controller_override: Any | None = None,
    recommended_task_intake_action_fn: Any | None = None,
    quality_repair_batch_override: Any | None = None,
) -> dict[str, Any] | None:
    gate_controller = publication_gate_controller_override or publication_gate_controller
    task_intake_action_fn = recommended_task_intake_action_fn or recommended_task_intake_action
    quality_repair_batch_module = quality_repair_batch_override or quality_repair_batch
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

    try:
        publication_eval_entry = _read_latest_publication_eval_payload(study_root=resolved_study_root)
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        if domain_transition_currentness.status_domain_transition_route_back_tick_request(
            study_root=resolved_study_root,
            status_payload=status_payload,
        ) is not None:
            return None
        raise
    if publication_eval_entry is None:
        return None
    publication_eval_path, publication_eval_payload = publication_eval_entry
    profile = gate_clearing_batch.resolve_profile_for_study_root(resolved_study_root)
    quest_id = str(status_payload.get("quest_id") or "").strip()
    gate_report: dict[str, Any] = {}
    if profile is not None and quest_id:
        quest_root = Path(profile.runtime_root).expanduser().resolve() / quest_id
        gate_report = gate_controller.build_gate_report(
            gate_controller.build_gate_state(quest_root)
        )
    closed_publication_gate_recheck_lifecycle = _read_closed_publication_gate_recheck_lifecycle(
        resolved_study_root
    )
    evaluation_summary = _read_evaluation_summary_payload(study_root=resolved_study_root)
    task_intake_yields_to_fast_lane_closeout = _latest_task_intake_yields_to_verified_fast_lane_closeout(
        study_root=resolved_study_root,
        publishability_gate_report=gate_report,
        evaluation_summary=evaluation_summary,
    )
    if task_intake_yields_to_fast_lane_closeout:
        recommended_action = _recommended_manuscript_fast_lane_closeout_autopark_action(
            study_root=resolved_study_root,
            status_payload=status_payload,
        )
    else:
        runtime_is_live = _runtime_status_is_live(status_payload)
        submission_milestone_autopark_action = (
            _recommended_submission_milestone_autopark_action(
                study_root=resolved_study_root,
                status_payload=status_payload,
                publication_eval_payload=publication_eval_payload,
                require_live_runtime=False,
            )
            if not runtime_is_live
            else None
        )
        task_intake_action = task_intake_action_fn(
            study_root=resolved_study_root,
            publishability_gate_report=gate_report,
            evaluation_summary=evaluation_summary,
        )
        domain_transition_action = domain_transition_recommended_action(
            study_id=str(status_payload.get("study_id") or resolved_study_root.name),
            study_root=resolved_study_root,
            status_payload={**status_payload, "publication_gate_report": dict(gate_report)},
            active_run_id=str(status_payload.get("active_run_id") or "").strip() or None,
        )
        live_submission_milestone_autopark_action = _recommended_submission_milestone_autopark_action(
            study_root=resolved_study_root,
            status_payload=status_payload,
            publication_eval_payload=publication_eval_payload,
        )
        domain_transition_decision_type = str(
            (
                (domain_transition_action or {}).get("domain_transition")
                if isinstance((domain_transition_action or {}).get("domain_transition"), dict)
                else {}
            ).get("decision_type")
            or ""
        ).strip()
        if _methodology_analysis_route_preempts_ai_reviewer_recheck(
            domain_transition_decision_type=domain_transition_decision_type,
            task_intake_action=task_intake_action,
            publication_eval_payload=publication_eval_payload,
        ) or _current_ai_reviewer_route_back_preempts_ai_reviewer_recheck(
            domain_transition_decision_type=domain_transition_decision_type,
            publication_eval_payload=publication_eval_payload,
        ):
            domain_transition_action = None
            domain_transition_decision_type = ""
        if (
            domain_transition_decision_type == "bundle_stage_finalize"
            and task_intake_action is not None
            and not _status_payload_reports_bundle_stage(status_payload)
        ):
            domain_transition_action = None
            domain_transition_decision_type = ""
        if (
            domain_transition_decision_type == "publication_gate_blocker"
            and task_intake_action is not None
            and str(gate_report.get("status") or "").strip() == "clear"
        ):
            domain_transition_action = None
            domain_transition_decision_type = ""
        if domain_transition_decision_type == "delivered_package_handoff" and task_intake_action is not None:
            domain_transition_action = None
            domain_transition_decision_type = ""
        submission_milestone_preempts_bundle_finalize = (
            live_submission_milestone_autopark_action is not None
            and domain_transition_decision_type == "bundle_stage_finalize"
        )
        if submission_milestone_preempts_bundle_finalize:
            domain_transition_action = None
        bundle_stage_finalize_preempts_task_intake = bundle_stage_publication_eval_preempts_task_intake(
            status_payload=status_payload,
            gate_report=gate_report,
            publication_eval_payload=publication_eval_payload,
            task_intake_action=task_intake_action,
        )
        if domain_transition_action is not None or bundle_stage_finalize_preempts_task_intake:
            task_intake_action = None
        batch_action = None
        startup_freshness_gate = startup_freshness_requires_gate_clearing(status_payload)
        gate_is_blocked = str(gate_report.get("status") or "").strip() == "blocked"
        if (
            profile is not None
            and not bundle_stage_finalize_preempts_task_intake
            and domain_transition_decision_type != "delivered_package_handoff"
            and (task_intake_action is None or startup_freshness_gate or gate_is_blocked)
        ):
            if startup_freshness_gate:
                batch_action = gate_clearing_batch.build_gate_clearing_batch_recommended_action(
                    profile=profile,
                    study_root=resolved_study_root,
                    quest_id=quest_id,
                    publication_eval_payload=publication_eval_payload,
                    gate_report=gate_report,
                    prefer_startup_freshness_work_unit=startup_freshness_gate,
                )
            if batch_action is None:
                batch_action = quality_repair_batch_module.build_quality_repair_batch_recommended_action(
                    profile=profile,
                    study_root=resolved_study_root,
                    quest_id=quest_id,
                    publication_eval_payload=publication_eval_payload,
                    gate_report=gate_report,
                )
            if batch_action is None and task_intake_action is None:
                batch_action = gate_clearing_batch.build_gate_clearing_batch_recommended_action(
                    profile=profile,
                    study_root=resolved_study_root,
                    quest_id=quest_id,
                    publication_eval_payload=publication_eval_payload,
                    gate_report=gate_report,
                )
        if gate_clearing_preempts_task_intake(
            status_payload=status_payload,
            batch_action=batch_action,
        ) or _quality_repair_batch_preempts_task_intake(batch_action):
            task_intake_action = None
        bundle_stage_finalize_action = (
            _bundle_stage_finalize_action_from_publication_eval(
                publication_eval_payload=publication_eval_payload,
                gate_report=gate_report,
            )
            if (
                bundle_stage_finalize_preempts_task_intake
                and _status_payload_reports_bundle_stage(status_payload)
                and not submission_milestone_preempts_bundle_finalize
            )
            else None
        )
        quality_repair_batch_preempts_task_intake = _quality_repair_batch_preempts_task_intake(batch_action)
        domain_transition_preempts_quality_batch = domain_transition_decision_type != "publication_gate_blocker"
        gate_clearing_batch_preempts_publication_gate_replay = (
            domain_transition_decision_type == "publication_gate_blocker"
            and isinstance(batch_action, dict)
            and str(batch_action.get("controller_action_type") or "").strip()
            == StudyDecisionActionType.RUN_GATE_CLEARING_BATCH.value
        )
        if domain_transition_action is not None and domain_transition_preempts_quality_batch:
            recommended_action = domain_transition_action
        elif startup_freshness_gate and batch_action is not None:
            recommended_action = batch_action
        elif quality_repair_batch_preempts_task_intake:
            recommended_action = batch_action
        elif gate_clearing_batch_preempts_publication_gate_replay:
            recommended_action = batch_action
        elif domain_transition_action is not None:
            recommended_action = domain_transition_action
        elif submission_milestone_preempts_bundle_finalize:
            recommended_action = live_submission_milestone_autopark_action
        elif bundle_stage_finalize_action is not None:
            recommended_action = bundle_stage_finalize_action
        else:
            recommended_action = (
                submission_milestone_autopark_action
                if submission_milestone_autopark_action is not None
                else task_intake_action
            )
        if recommended_action is None:
            recommended_action = _recommended_submission_milestone_autopark_action(
                study_root=resolved_study_root,
                status_payload=status_payload,
                publication_eval_payload=publication_eval_payload,
            )
        if recommended_action is None:
            recommended_action = _recommended_quality_review_loop_action(study_root=resolved_study_root)
        if recommended_action is None:
            recommended_action = _recommended_publication_eval_action(publication_eval_payload)
        if (
            profile is not None
            and domain_transition_action is None
            and task_intake_action is None
            and domain_transition_decision_type != "delivered_package_handoff"
        ):
            if batch_action is not None:
                recommended_action = batch_action
        if closed_publication_gate_recheck_lifecycle is not None:
            recommended_action = _publication_gate_recheck_action_from_closed_lifecycle(
                lifecycle=closed_publication_gate_recheck_lifecycle
            )
    if recommended_action is None:
        return None
    recommended_action = _merge_publication_eval_methodology_work_unit(
        recommended_action,
        publication_eval_payload=publication_eval_payload,
    )
    work_unit_target_context = {
        key: recommended_action[key]
        for key in _WORK_UNIT_TARGET_CONTEXT_KEYS
        if key in recommended_action
    }
    if specificity_target_status(work_unit_target_context.get("specificity_targets")).get("complete") is not True:
        matched_target_context = _specificity_target_context_from_publication_eval(
            publication_eval_payload=publication_eval_payload,
            recommended_action=recommended_action,
        )
        if matched_target_context:
            work_unit_target_context = matched_target_context
    if work_unit_target_context:
        recommended_action = {**recommended_action, **work_unit_target_context}
    recommended_action = _promote_gate_needs_specificity_action(recommended_action)
    work_unit_target_context = {
        key: recommended_action[key]
        for key in _WORK_UNIT_TARGET_CONTEXT_KEYS
        if key in recommended_action
    }
    decision_type = _autonomous_decision_type_for_publication_eval_action(recommended_action)
    if decision_type is None:
        return None

    charter_ref = _build_study_decision_charter_ref(
        study_root=resolved_study_root,
        missing_message="domain health diagnostic outer-loop wakeup requires stable study charter artifact",
    ).to_dict()

    runtime_escalation_payload = status_payload.get("runtime_escalation_ref")
    if runtime_escalation_payload is not None:
        if not isinstance(runtime_escalation_payload, dict):
            raise ValueError("domain health diagnostic outer-loop wakeup runtime_escalation_ref must be a mapping when present")
        _resolve_runtime_escalation_record(runtime_escalation_payload=runtime_escalation_payload)

    publication_eval_ref = StudyDecisionPublicationEvalRef(
        eval_id=str(publication_eval_payload.get("eval_id") or "").strip(),
        artifact_path=str(publication_eval_path),
    ).to_dict()
    controller_action_type = str(recommended_action.get("controller_action_type") or "").strip()
    if not controller_action_type:
        if decision_type == StudyDecisionType.RETURN_TO_CONTROLLER.value:
            controller_action_type = StudyDecisionActionType.REQUEST_GATE_SPECIFICITY.value
        elif decision_type == StudyDecisionType.STOP_LOSS.value:
            controller_action_type = StudyDecisionActionType.STOP_RUNTIME.value
        else:
            controller_action_type = _autonomous_controller_action_type_for_runtime_status(status_payload)
    controller_action = StudyDecisionControllerAction(
        action_type=controller_action_type,
        payload_ref=str((resolved_study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()),
    ).to_dict()
    next_work_unit = (
        dict(recommended_action.get("next_work_unit") or {})
        if isinstance(recommended_action.get("next_work_unit"), dict)
        else None
    )
    next_work_unit = _target_ready_next_work_unit(next_work_unit, work_unit_target_context)
    return {
        "study_root": resolved_study_root,
        "charter_ref": charter_ref,
        "publication_eval_ref": publication_eval_ref,
        "decision_type": decision_type,
        "route_target": (
            str(recommended_action.get("route_target") or "").strip()
            or ("controller" if decision_type == StudyDecisionType.RETURN_TO_CONTROLLER.value else None)
        ),
        "route_key_question": (
            str(recommended_action.get("route_key_question") or "").strip()
            or (
                _GATE_NEEDS_SPECIFICITY_QUESTION
                if decision_type == StudyDecisionType.RETURN_TO_CONTROLLER.value
                else None
            )
        ),
        "source_route_key_question": str(recommended_action.get("source_route_key_question") or "").strip() or None,
        "route_rationale": (
            str(recommended_action.get("route_rationale") or "").strip()
            or (
                str(recommended_action.get("reason") or "").strip()
                if decision_type == StudyDecisionType.RETURN_TO_CONTROLLER.value
                else None
            )
        ),
        "requires_human_confirmation": False,
        "controller_actions": [controller_action],
        "reason": str(recommended_action.get("reason") or "").strip()
        or "publication eval requests an autonomous controller decision for the current line.",
        "work_unit_fingerprint": str(recommended_action.get("work_unit_fingerprint") or "").strip() or None,
        "next_work_unit": next_work_unit,
        "blocking_work_units": list(recommended_action.get("blocking_work_units") or []),
        **work_unit_target_context,
    }
