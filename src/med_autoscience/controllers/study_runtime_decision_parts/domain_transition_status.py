from __future__ import annotations

from pathlib import Path

from med_autoscience.controllers import study_runtime_interaction_arbitration as interaction_arbitration_controller
from med_autoscience.controllers.study_runtime_decision_parts.runtime_events.human_gates import (
    _is_controller_owned_finalize_parking,
)
from med_autoscience.controllers.study_runtime_decision_parts.runtime_events.pending_interactions import (
    _stopped_controller_owned_auto_recovery_context,
)
from med_autoscience.controllers.study_runtime_types import (
    StudyRuntimeDecision,
    StudyRuntimeQuestStatus,
    StudyRuntimeReason,
    StudyRuntimeStatus,
)
from med_autoscience.controllers.study_runtime_decision_parts.publication_and_submission import _load_json_dict


def _record_interaction_arbitration_if_required(
    *,
    status: StudyRuntimeStatus,
    quest_root: Path,
    execution: dict[str, object],
    submission_metadata_only: bool,
    publication_gate_report: dict[str, object] | None,
) -> None:
    stopped_recovery_context = _stopped_controller_owned_auto_recovery_context(
        status=status,
        quest_root=quest_root,
        publication_gate_report=publication_gate_report,
    )
    if (
        status.quest_status is not StudyRuntimeQuestStatus.WAITING_FOR_USER
        and not _is_controller_owned_finalize_parking(status)
        and stopped_recovery_context is None
    ):
        return
    payload = status.extras.get("pending_user_interaction")
    blocked_closeout = status.extras.get("blocked_turn_closeout")
    continuation_state = status.extras.get("continuation_state")
    controller_authorization = status.extras.get("last_controller_decision_authorization")
    domain_transition = status.extras.get("domain_transition")
    arbitration = interaction_arbitration_controller.arbitrate_waiting_for_user(
        pending_interaction=payload if isinstance(payload, dict) else None,
        decision_policy=str(execution.get("decision_policy") or "").strip() or None,
        submission_metadata_only=submission_metadata_only,
        publication_gate_report=publication_gate_report if isinstance(publication_gate_report, dict) else None,
        blocked_closeout=blocked_closeout if isinstance(blocked_closeout, dict) else None,
        continuation_state=continuation_state if isinstance(continuation_state, dict) else None,
        controller_authorization=controller_authorization if isinstance(controller_authorization, dict) else None,
        domain_transition=domain_transition if isinstance(domain_transition, dict) else None,
    )
    status.record_interaction_arbitration(arbitration)


def _domain_transition_runtime_redrive_reason(status: StudyRuntimeStatus) -> StudyRuntimeReason | None:
    domain_transition = status.extras.get("domain_transition")
    if not isinstance(domain_transition, dict):
        return None
    arbitration = interaction_arbitration_controller.arbitrate_waiting_for_user(
        pending_interaction=None,
        decision_policy=str(status.execution.get("decision_policy") or "").strip() or None,
        submission_metadata_only=False,
        domain_transition=domain_transition,
    )
    if str(arbitration.get("classification") or "").strip() != "domain_transition_runtime_redrive":
        return None
    if str(arbitration.get("action") or "").strip() != "resume":
        return None
    status.record_interaction_arbitration(arbitration)
    reason_code = str(arbitration.get("reason_code") or "").strip()
    try:
        return StudyRuntimeReason(reason_code)
    except ValueError:
        return StudyRuntimeReason.QUEST_WAITING_PLATFORM_REPAIR_REDRIVE


def _publication_gate_domain_redrive_reason(status: StudyRuntimeStatus) -> StudyRuntimeReason | None:
    domain_transition = status.extras.get("domain_transition")
    if not isinstance(domain_transition, dict):
        return None
    if str(domain_transition.get("decision_type") or "").strip() != "publication_gate_blocker":
        return None
    arbitration = interaction_arbitration_controller.arbitrate_waiting_for_user(
        pending_interaction=None,
        decision_policy=str(status.execution.get("decision_policy") or "").strip() or None,
        submission_metadata_only=False,
        domain_transition=domain_transition,
    )
    if str(arbitration.get("action") or "").strip() != "resume":
        return None
    status.record_interaction_arbitration(arbitration)
    return StudyRuntimeReason.DOMAIN_TRANSITION_PUBLICATION_GATE_BLOCKER


def _has_domain_transition_runtime_redrive(status: StudyRuntimeStatus) -> bool:
    interaction_arbitration = status.extras.get("interaction_arbitration")
    return (
        isinstance(interaction_arbitration, dict)
        and str(interaction_arbitration.get("classification") or "").strip()
        == "domain_transition_runtime_redrive"
        and str(interaction_arbitration.get("action") or "").strip() == "resume"
    )


def _current_ai_reviewer_domain_redrive_reason(
    status: StudyRuntimeStatus,
    *,
    study_root: Path,
) -> StudyRuntimeReason | None:
    reason = _domain_transition_runtime_redrive_reason(status)
    if reason is not StudyRuntimeReason.DOMAIN_TRANSITION_AI_REVIEWER_RE_EVAL:
        return None
    decision = _load_json_dict(study_root / "artifacts" / "controller_decisions" / "latest.json")
    action_types = {
        str(action.get("action_type") or "").strip()
        for action in (decision.get("controller_actions") or [])
        if isinstance(action, dict)
    }
    work_unit = decision.get("next_work_unit")
    work_unit_id = str(work_unit.get("unit_id") or "").strip() if isinstance(work_unit, dict) else ""
    fingerprint = str(decision.get("work_unit_fingerprint") or "").strip()
    if "return_to_ai_reviewer_workflow" not in action_types:
        return None
    if not fingerprint.startswith("domain-transition::ai_reviewer_re_eval::"):
        return None
    if work_unit_id and not fingerprint.startswith(f"domain-transition::ai_reviewer_re_eval::{work_unit_id}"):
        return None
    return reason


def _completion_blocked_ai_reviewer_redrive_reason(
    status: StudyRuntimeStatus,
    *,
    study_root: Path,
    publication_gate_report: dict[str, object] | None,
) -> StudyRuntimeReason | None:
    if publication_gate_report is None:
        return None
    if str(publication_gate_report.get("status") or "").strip() == "clear":
        return None
    return _current_ai_reviewer_domain_redrive_reason(status, study_root=study_root)


def _apply_completion_blocked_ai_reviewer_redrive_decision(
    status: StudyRuntimeStatus,
    *,
    study_root: Path,
    publication_gate_report: dict[str, object] | None,
) -> bool:
    reason = _completion_blocked_ai_reviewer_redrive_reason(
        status,
        study_root=study_root,
        publication_gate_report=publication_gate_report,
    )
    if reason is not StudyRuntimeReason.DOMAIN_TRANSITION_AI_REVIEWER_RE_EVAL:
        return False
    status.set_decision(StudyRuntimeDecision.RESUME, reason)
    return True


def _apply_ai_reviewer_domain_redrive_decision(
    status: StudyRuntimeStatus,
    *,
    reason: StudyRuntimeReason | None,
    execution: dict[str, object],
    running_quest: bool,
) -> bool:
    if reason is not StudyRuntimeReason.DOMAIN_TRANSITION_AI_REVIEWER_RE_EVAL:
        return False
    return _apply_domain_transition_redrive_decision(
        status,
        reason=reason,
        execution=execution,
        running_quest=running_quest,
    )


def _apply_domain_transition_redrive_decision(
    status: StudyRuntimeStatus,
    *,
    reason: StudyRuntimeReason | None,
    execution: dict[str, object],
    running_quest: bool,
) -> bool:
    if reason is None:
        return False
    if not status.startup_boundary_allows_compute_stage:
        status.set_decision(
            StudyRuntimeDecision.PAUSE if running_quest else StudyRuntimeDecision.BLOCKED,
            (
                StudyRuntimeReason.STARTUP_BOUNDARY_NOT_READY_FOR_RUNNING_QUEST
                if running_quest
                else StudyRuntimeReason.STARTUP_BOUNDARY_NOT_READY_FOR_RESUME
            ),
        )
    elif not status.runtime_reentry_allows_runtime_entry:
        status.set_decision(
            StudyRuntimeDecision.PAUSE if running_quest else StudyRuntimeDecision.BLOCKED,
            (
                StudyRuntimeReason.RUNTIME_REENTRY_NOT_READY_FOR_RUNNING_QUEST
                if running_quest
                else StudyRuntimeReason.RUNTIME_REENTRY_NOT_READY_FOR_RESUME
            ),
        )
    elif execution.get("auto_resume") is True:
        status.set_decision(
            StudyRuntimeDecision.RESUME,
            reason,
        )
    else:
        status.set_decision(
            StudyRuntimeDecision.BLOCKED,
            (
                StudyRuntimeReason.QUEST_MARKED_RUNNING_BUT_AUTO_RESUME_DISABLED
                if running_quest
                else StudyRuntimeReason.QUEST_PAUSED_BUT_AUTO_RESUME_DISABLED
            ),
        )
    return True


__all__ = [
    "_apply_completion_blocked_ai_reviewer_redrive_decision",
    "_apply_ai_reviewer_domain_redrive_decision",
    "_apply_domain_transition_redrive_decision",
    "_completion_blocked_ai_reviewer_redrive_reason",
    "_current_ai_reviewer_domain_redrive_reason",
    "_publication_gate_domain_redrive_reason",
    "_has_domain_transition_runtime_redrive",
    "_record_interaction_arbitration_if_required",
    "_domain_transition_runtime_redrive_reason",
]
