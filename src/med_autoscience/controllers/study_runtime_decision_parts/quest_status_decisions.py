from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from med_autoscience.controllers.study_runtime_decision_parts.domain_transition_status import (
    _apply_domain_transition_redrive_decision,
    _domain_transition_runtime_redrive_reason,
    _has_domain_transition_runtime_redrive,
    _publication_gate_domain_redrive_reason,
)
from med_autoscience.controllers.study_runtime_decision_parts.publication_and_submission import (
    _publication_gate_requires_live_runtime_reroute,
    _record_existing_controller_work_unit_evidence_adoption,
)
from med_autoscience.controllers.study_runtime_decision_parts.runtime_events.human_gates import (
    _bare_paused_quest_requires_explicit_wakeup_without_live_worker,
    _controller_decision_requires_human_confirmation,
    _human_takeover_contract_requires_explicit_wakeup_without_live_worker,
    _is_controller_owned_finalize_parking,
    _is_human_review_milestone_parking,
    _live_worker_missing_active_run_id,
    _platform_repair_redrive_without_live_worker,
    _publication_supervisor_requires_human_confirmation,
    _set_running_quest_recovery_decision,
    _should_park_delivered_package_without_live_worker,
    _should_park_delivered_or_redriven_package_without_live_worker,
    _stale_progress_without_live_bash_sessions,
    _user_pause_contract_without_live_worker,
)
from med_autoscience.controllers.study_runtime_decision_parts.runtime_events.ownership_and_continuation import (
    _publication_gate_allows_post_clear_runtime_continuation,
    _publication_gate_allows_live_runtime_write_stage_resume,
)
from med_autoscience.controllers.study_runtime_decision_parts.runtime_events.pending_interactions import (
    _stopped_controller_owned_auto_recovery_context,
    _stopped_invalid_blocking_auto_resume_allowed,
    _task_intake_override_allows_stopped_auto_resume,
)
from med_autoscience.controllers.study_runtime_decision_parts.runtime_health_dominance import (
    _runtime_health_requires_explicit_resume,
)
from med_autoscience.controllers.study_runtime_types import (
    StudyRuntimeDecision,
    StudyRuntimeQuestStatus,
    StudyRuntimeReason,
    StudyRuntimeStatus,
    _RESUMABLE_QUEST_STATUSES,
)
from med_autoscience.runtime_protocol import quest_state


def _apply_live_quest_status_decision(
    *,
    result: StudyRuntimeStatus,
    router: Any,
    quest_runtime: Any,
    execution: dict[str, object],
    study_root: Path,
    study_id: str,
    quest_id: str,
    publication_gate_report: dict[str, object] | None,
    manual_finish_compatibility_guard: bool,
    submission_metadata_only_manual_finish: bool,
    task_intake_releases_manual_finish_parking: bool,
    task_intake_yields_to_submission_closeout: bool,
    reviewer_revision_open_blockers_release_manual_finish_parking: bool,
    finalize_result: Callable[[], StudyRuntimeStatus],
) -> StudyRuntimeStatus:
    audit_status = router._record_quest_runtime_audits(status=result, quest_runtime=quest_runtime)
    controller_owned_finalize_parking = _is_controller_owned_finalize_parking(result)
    human_review_milestone_parking = _is_human_review_milestone_parking(
        result,
        study_root=study_root,
    )
    publication_gate_redrive_reason = _publication_gate_domain_redrive_reason(result)
    domain_redrive_reason = publication_gate_redrive_reason or _domain_transition_runtime_redrive_reason(result)
    if _user_pause_contract_without_live_worker(
        result,
        audit_status=audit_status,
    ) or _human_takeover_contract_requires_explicit_wakeup_without_live_worker(
        result,
        audit_status=audit_status,
    ):
        result.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.QUEST_USER_PAUSED_REQUIRES_EXPLICIT_WAKEUP,
        )
        return finalize_result()
    if _runtime_health_requires_explicit_resume(
        status=result,
        study_root=study_root,
        study_id=study_id,
        quest_id=quest_id,
    ):
        result.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.QUEST_STOPPED_REQUIRES_EXPLICIT_RERUN,
        )
        return finalize_result()
    if (
        not _platform_repair_redrive_without_live_worker(result, audit_status=audit_status)
        and _record_existing_controller_work_unit_evidence_adoption(status=result, study_root=study_root) is not None
    ):
        result.set_decision(
            StudyRuntimeDecision.NOOP,
            StudyRuntimeReason.CONTROLLER_WORK_UNIT_EVIDENCE_ADOPTED,
        )
        return finalize_result()
    if (
        not _has_domain_transition_runtime_redrive(result)
        and _should_park_delivered_or_redriven_package_without_live_worker(
            result,
            study_root=study_root,
            audit_status=audit_status,
            manual_finish_compatibility_guard=manual_finish_compatibility_guard,
        )
        and (
            not reviewer_revision_open_blockers_release_manual_finish_parking
            or task_intake_yields_to_submission_closeout
        )
    ):
        result.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.QUEST_WAITING_FOR_SUBMISSION_METADATA,
        )
        return finalize_result()
    if human_review_milestone_parking and audit_status is not quest_state.QuestRuntimeLivenessStatus.LIVE:
        result.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.QUEST_PARKED_ON_UNCHANGED_FINALIZE_STATE,
        )
        return finalize_result()
    if audit_status is quest_state.QuestRuntimeLivenessStatus.UNKNOWN:
        if (
            domain_redrive_reason is not StudyRuntimeReason.DOMAIN_TRANSITION_AI_REVIEWER_RE_EVAL
            and manual_finish_compatibility_guard
            and (
                not task_intake_releases_manual_finish_parking
                or task_intake_yields_to_submission_closeout
            )
        ):
            result.set_decision(
                StudyRuntimeDecision.BLOCKED,
                StudyRuntimeReason.QUEST_WAITING_FOR_SUBMISSION_METADATA,
            )
        elif _stale_progress_without_live_bash_sessions(result) or _live_worker_missing_active_run_id(result):
            _set_running_quest_recovery_decision(
                status=result,
                execution=execution,
            )
        else:
            _set_running_quest_recovery_decision(
                status=result,
                execution=execution,
            )
    elif audit_status is quest_state.QuestRuntimeLivenessStatus.LIVE:
        if _apply_domain_transition_redrive_decision(
            result,
            reason=domain_redrive_reason,
            execution=execution,
            running_quest=True,
        ):
            pass
        elif manual_finish_compatibility_guard and (
            not task_intake_releases_manual_finish_parking or task_intake_yields_to_submission_closeout
        ):
            result.set_decision(
                StudyRuntimeDecision.PAUSE,
                StudyRuntimeReason.QUEST_WAITING_FOR_SUBMISSION_METADATA,
            )
        elif _publication_gate_requires_live_runtime_reroute(
            publication_gate_report,
            status=result,
        ):
            if execution.get("auto_resume") is True:
                result.set_decision(
                    StudyRuntimeDecision.RESUME,
                    StudyRuntimeReason.QUEST_DRIFTING_INTO_WRITE_WITHOUT_GATE_APPROVAL,
                )
            else:
                result.set_decision(
                    StudyRuntimeDecision.BLOCKED,
                    StudyRuntimeReason.QUEST_MARKED_RUNNING_BUT_AUTO_RESUME_DISABLED,
                )
        elif _publication_gate_allows_live_runtime_write_stage_resume(
            status=result,
            publication_gate_report=publication_gate_report,
        ):
            if execution.get("auto_resume") is True:
                result.set_decision(
                    StudyRuntimeDecision.RESUME,
                    StudyRuntimeReason.QUEST_STALE_DECISION_AFTER_WRITE_STAGE_READY,
                )
            else:
                result.set_decision(
                    StudyRuntimeDecision.BLOCKED,
                    StudyRuntimeReason.QUEST_MARKED_RUNNING_BUT_AUTO_RESUME_DISABLED,
                )
        elif not result.startup_boundary_allows_compute_stage:
            result.set_decision(
                StudyRuntimeDecision.PAUSE,
                StudyRuntimeReason.STARTUP_BOUNDARY_NOT_READY_FOR_RUNNING_QUEST,
            )
        elif not result.runtime_reentry_allows_runtime_entry:
            result.set_decision(
                StudyRuntimeDecision.PAUSE,
                StudyRuntimeReason.RUNTIME_REENTRY_NOT_READY_FOR_RUNNING_QUEST,
            )
        else:
            result.set_decision(
                StudyRuntimeDecision.NOOP,
                StudyRuntimeReason.QUEST_ALREADY_RUNNING,
            )
    elif controller_owned_finalize_parking:
        if submission_metadata_only_manual_finish:
            result.set_decision(
                StudyRuntimeDecision.BLOCKED,
                StudyRuntimeReason.QUEST_WAITING_FOR_SUBMISSION_METADATA,
            )
            return finalize_result()
        interaction_arbitration = result.extras.get("interaction_arbitration")
        if isinstance(interaction_arbitration, dict):
            classification = str(interaction_arbitration.get("classification") or "").strip()
            action = str(interaction_arbitration.get("action") or "").strip()
            if classification == "external_input_required" and action == "block":
                result.set_decision(
                    StudyRuntimeDecision.BLOCKED,
                    StudyRuntimeReason.QUEST_WAITING_FOR_EXTERNAL_INPUT,
                )
                return finalize_result()
        if _controller_decision_requires_human_confirmation(
            study_root=study_root
        ) or _publication_supervisor_requires_human_confirmation(result):
            result.set_decision(
                StudyRuntimeDecision.BLOCKED,
                StudyRuntimeReason.QUEST_PARKED_ON_UNCHANGED_FINALIZE_STATE,
            )
        elif not result.startup_boundary_allows_compute_stage:
            result.set_decision(
                StudyRuntimeDecision.BLOCKED,
                StudyRuntimeReason.STARTUP_BOUNDARY_NOT_READY_FOR_RESUME,
            )
        elif not result.runtime_reentry_allows_runtime_entry:
            result.set_decision(
                StudyRuntimeDecision.BLOCKED,
                StudyRuntimeReason.RUNTIME_REENTRY_NOT_READY_FOR_RESUME,
            )
        elif execution.get("auto_resume") is True:
            result.set_decision(
                StudyRuntimeDecision.RESUME,
                StudyRuntimeReason.QUEST_PARKED_ON_UNCHANGED_FINALIZE_STATE,
            )
        else:
            result.set_decision(
                StudyRuntimeDecision.BLOCKED,
                StudyRuntimeReason.QUEST_MARKED_RUNNING_BUT_AUTO_RESUME_DISABLED,
            )
    elif not result.startup_boundary_allows_compute_stage:
        result.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.STARTUP_BOUNDARY_NOT_READY_FOR_RESUME,
        )
    elif not result.runtime_reentry_allows_runtime_entry:
        result.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.RUNTIME_REENTRY_NOT_READY_FOR_RESUME,
        )
    elif execution.get("auto_resume") is True:
        result.set_decision(
            StudyRuntimeDecision.RESUME,
            domain_redrive_reason or StudyRuntimeReason.QUEST_MARKED_RUNNING_BUT_NO_LIVE_SESSION,
        )
    else:
        result.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.QUEST_MARKED_RUNNING_BUT_AUTO_RESUME_DISABLED,
        )
    return finalize_result()


def _apply_resumable_quest_status_decision(
    *,
    result: StudyRuntimeStatus,
    rebuild_status: Callable[[], StudyRuntimeStatus],
    execution: dict[str, object],
    study_root: Path,
    quest_root: Path,
    quest_status: StudyRuntimeQuestStatus,
    task_intake_releases_bare_paused_parking: bool,
    task_intake_releases_manual_finish_parking: bool,
    submission_metadata_only_manual_finish: bool,
    bundle_only_manual_finish: bool,
    finalize_result: Callable[[], StudyRuntimeStatus],
) -> StudyRuntimeStatus:
    if _user_pause_contract_without_live_worker(
        result,
    ) or _human_takeover_contract_requires_explicit_wakeup_without_live_worker(
        result
    ) or (
        _bare_paused_quest_requires_explicit_wakeup_without_live_worker(result)
        and not task_intake_releases_bare_paused_parking
    ):
        from med_autoscience.controllers.study_runtime_execution_parts import (
            runtime_events as runtime_execution_events,
        )

        repaired_human_takeover = runtime_execution_events.repair_legacy_human_takeover_user_pause_contract(
            quest_root=quest_root,
            source="legacy_human_takeover_escalation_repair",
        )
        if repaired_human_takeover is not None:
            result._record_dict_extra("human_takeover_contract", repaired_human_takeover)
            result = rebuild_status()
            result._record_dict_extra("human_takeover_contract", repaired_human_takeover)
            quest_status = result.quest_status
        else:
            result.set_decision(
                StudyRuntimeDecision.BLOCKED,
                StudyRuntimeReason.QUEST_USER_PAUSED_REQUIRES_EXPLICIT_WAKEUP,
            )
            return finalize_result()
    if quest_status not in _RESUMABLE_QUEST_STATUSES:
        return finalize_result()
    if _user_pause_contract_without_live_worker(
        result,
    ) or _human_takeover_contract_requires_explicit_wakeup_without_live_worker(
        result
    ) or (
        _bare_paused_quest_requires_explicit_wakeup_without_live_worker(result)
        and not task_intake_releases_bare_paused_parking
    ):
        result.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.QUEST_USER_PAUSED_REQUIRES_EXPLICIT_WAKEUP,
        )
        return finalize_result()
    if (
        _should_park_delivered_package_without_live_worker(result, study_root=study_root)
        and not task_intake_releases_manual_finish_parking
    ):
        result.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.QUEST_WAITING_FOR_SUBMISSION_METADATA,
        )
        return finalize_result()
    if (
        (submission_metadata_only_manual_finish or bundle_only_manual_finish)
        and not task_intake_releases_manual_finish_parking
    ):
        result.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.QUEST_WAITING_FOR_SUBMISSION_METADATA,
        )
        return finalize_result()
    if not result.startup_boundary_allows_compute_stage:
        result.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.STARTUP_BOUNDARY_NOT_READY_FOR_RESUME,
        )
        return finalize_result()
    if not result.runtime_reentry_allows_runtime_entry:
        result.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.RUNTIME_REENTRY_NOT_READY_FOR_RESUME,
        )
        return finalize_result()
    if execution.get("auto_resume") is True:
        resumable_reason = {
            StudyRuntimeQuestStatus.PAUSED: StudyRuntimeReason.QUEST_PAUSED,
        }.get(quest_status, StudyRuntimeReason.QUEST_INITIALIZED_WAITING_TO_START)
        result.set_decision(
            StudyRuntimeDecision.RESUME,
            resumable_reason,
        )
    else:
        blocked_reason = {
            StudyRuntimeQuestStatus.PAUSED: StudyRuntimeReason.QUEST_PAUSED_BUT_AUTO_RESUME_DISABLED,
        }.get(quest_status, StudyRuntimeReason.QUEST_INITIALIZED_BUT_AUTO_RESUME_DISABLED)
        result.set_decision(
            StudyRuntimeDecision.BLOCKED,
            blocked_reason,
        )
    return finalize_result()


def _set_stopped_resume_or_blocked_decision(
    *,
    result: StudyRuntimeStatus,
    execution: dict[str, object],
    resume_reason: StudyRuntimeReason,
    blocked_reason: StudyRuntimeReason,
) -> None:
    if not result.startup_boundary_allows_compute_stage:
        result.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.STARTUP_BOUNDARY_NOT_READY_FOR_RESUME,
        )
    elif not result.runtime_reentry_allows_runtime_entry:
        result.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.RUNTIME_REENTRY_NOT_READY_FOR_RESUME,
        )
    elif execution.get("auto_resume") is True:
        result.set_decision(
            StudyRuntimeDecision.RESUME,
            resume_reason,
        )
    else:
        result.set_decision(
            StudyRuntimeDecision.BLOCKED,
            blocked_reason,
        )


def _apply_stopped_or_failed_quest_status_decision(
    *,
    result: StudyRuntimeStatus,
    execution: dict[str, object],
    quest_root: Path,
    quest_status: StudyRuntimeQuestStatus,
    publication_gate_report: dict[str, object] | None,
    task_intake_releases_manual_finish_parking: bool,
    task_intake_yields_to_submission_closeout: bool,
    submission_metadata_only_manual_finish: bool,
    bundle_only_manual_finish: bool,
    finalize_result: Callable[[], StudyRuntimeStatus],
) -> StudyRuntimeStatus:
    if _user_pause_contract_without_live_worker(
        result,
    ) or _human_takeover_contract_requires_explicit_wakeup_without_live_worker(result):
        result.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.QUEST_USER_PAUSED_REQUIRES_EXPLICIT_WAKEUP,
        )
        return finalize_result()
    stopped_recovery_context = _stopped_controller_owned_auto_recovery_context(
        status=result,
        quest_root=quest_root,
        publication_gate_report=publication_gate_report,
    )
    interaction_arbitration = result.extras.get("interaction_arbitration")
    failed_task_intake_resume_allowed = (
        quest_status is StudyRuntimeQuestStatus.FAILED
        and task_intake_releases_manual_finish_parking
        and not task_intake_yields_to_submission_closeout
        and (
            isinstance(stopped_recovery_context, dict)
            or (
                isinstance(interaction_arbitration, dict)
                and str(interaction_arbitration.get("action") or "").strip() == "resume"
            )
        )
    )
    if (
        (submission_metadata_only_manual_finish or bundle_only_manual_finish)
        and not failed_task_intake_resume_allowed
    ):
        result.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.QUEST_WAITING_FOR_SUBMISSION_METADATA,
        )
        return finalize_result()
    if (
        isinstance(stopped_recovery_context, dict)
        and str(stopped_recovery_context.get("recovery_mode") or "").strip() == "controller_guard"
    ):
        post_clear_continuation = _publication_gate_allows_post_clear_runtime_continuation(publication_gate_report)
        _set_stopped_resume_or_blocked_decision(
            result=result,
            execution=execution,
            resume_reason=(
                StudyRuntimeReason.QUEST_STALE_DECISION_AFTER_WRITE_STAGE_READY
                if post_clear_continuation
                else StudyRuntimeReason.QUEST_STOPPED_BY_CONTROLLER_GUARD
            ),
            blocked_reason=StudyRuntimeReason.QUEST_STOPPED_BUT_AUTO_RESUME_DISABLED,
        )
        return finalize_result()
    if stopped_recovery_context is not None and isinstance(interaction_arbitration, dict):
        classification = str(interaction_arbitration.get("classification") or "").strip()
        action = str(interaction_arbitration.get("action") or "").strip()
        if action == "resume" and (
            classification != "invalid_blocking"
            or _stopped_invalid_blocking_auto_resume_allowed(stopped_recovery_context=stopped_recovery_context)
        ):
            resume_reason = {
                "submission_metadata_only": StudyRuntimeReason.QUEST_WAITING_FOR_SUBMISSION_METADATA,
                "domain_transition_runtime_redrive": _domain_transition_runtime_redrive_reason(result)
                or StudyRuntimeReason.QUEST_WAITING_PLATFORM_REPAIR_REDRIVE,
                "premature_completion_request": (
                    StudyRuntimeReason.QUEST_COMPLETION_REQUESTED_BEFORE_PUBLICATION_GATE_CLEAR
                ),
                "invalid_blocking": StudyRuntimeReason.QUEST_WAITING_ON_INVALID_BLOCKING,
            }.get(classification, StudyRuntimeReason.QUEST_WAITING_ON_INVALID_BLOCKING)
            blocked_reason = (
                StudyRuntimeReason.QUEST_WAITING_FOR_SUBMISSION_METADATA_BUT_AUTO_RESUME_DISABLED
                if classification == "submission_metadata_only"
                else StudyRuntimeReason.QUEST_STOPPED_BUT_AUTO_RESUME_DISABLED
            )
            _set_stopped_resume_or_blocked_decision(
                result=result,
                execution=execution,
                resume_reason=resume_reason,
                blocked_reason=blocked_reason,
            )
            return finalize_result()
        if classification == "external_input_required":
            result.set_decision(
                StudyRuntimeDecision.BLOCKED,
                StudyRuntimeReason.QUEST_WAITING_FOR_EXTERNAL_INPUT,
            )
            return finalize_result()
    if (
        isinstance(stopped_recovery_context, dict)
        and str(stopped_recovery_context.get("recovery_mode") or "").strip() == "managed_auto_continuation"
    ):
        _set_stopped_resume_or_blocked_decision(
            result=result,
            execution=execution,
            resume_reason=StudyRuntimeReason.QUEST_WAITING_ON_INVALID_BLOCKING,
            blocked_reason=StudyRuntimeReason.QUEST_STOPPED_BUT_AUTO_RESUME_DISABLED,
        )
        return finalize_result()
    if (
        task_intake_releases_manual_finish_parking
        and not task_intake_yields_to_submission_closeout
        and _task_intake_override_allows_stopped_auto_resume(quest_root=quest_root)
    ):
        _set_stopped_resume_or_blocked_decision(
            result=result,
            execution=execution,
            resume_reason=StudyRuntimeReason.QUEST_WAITING_ON_INVALID_BLOCKING,
            blocked_reason=StudyRuntimeReason.QUEST_STOPPED_BUT_AUTO_RESUME_DISABLED,
        )
        return finalize_result()
    result.set_decision(
        StudyRuntimeDecision.BLOCKED,
        StudyRuntimeReason.QUEST_STOPPED_REQUIRES_EXPLICIT_RERUN,
    )
    return finalize_result()


def _apply_waiting_for_user_status_decision(
    *,
    result: StudyRuntimeStatus,
    submission_metadata_only_wait: bool,
    submission_metadata_only_manual_finish: bool,
    finalize_result: Callable[[], StudyRuntimeStatus],
) -> StudyRuntimeStatus:
    interaction_arbitration = result.extras.get("interaction_arbitration")
    if isinstance(interaction_arbitration, dict):
        classification = str(interaction_arbitration.get("classification") or "").strip()
        action = str(interaction_arbitration.get("action") or "").strip()
        if action == "resume":
            resume_reason = {
                "submission_metadata_only": StudyRuntimeReason.QUEST_WAITING_FOR_SUBMISSION_METADATA,
                "domain_transition_runtime_redrive": _domain_transition_runtime_redrive_reason(result)
                or StudyRuntimeReason.QUEST_WAITING_PLATFORM_REPAIR_REDRIVE,
                "premature_completion_request": (
                    StudyRuntimeReason.QUEST_COMPLETION_REQUESTED_BEFORE_PUBLICATION_GATE_CLEAR
                ),
                "invalid_blocking": StudyRuntimeReason.QUEST_WAITING_ON_INVALID_BLOCKING,
                "pending_user_message_redrive": StudyRuntimeReason.QUEST_WAITING_USER_MESSAGE_REDRIVE,
                "platform_repair_decision_redrive": (
                    StudyRuntimeReason.QUEST_WAITING_PLATFORM_REPAIR_REDRIVE
                ),
                "controller_work_unit_pending_redrive": (
                    StudyRuntimeReason.QUEST_WAITING_PLATFORM_REPAIR_REDRIVE
                ),
                "blocked_closeout_owner_redrive": (
                    StudyRuntimeReason.QUEST_WAITING_PLATFORM_REPAIR_REDRIVE
                ),
                "domain_transition_publication_blocker": (
                    StudyRuntimeReason.STUDY_COMPLETION_PUBLISHABILITY_GATE_BLOCKED
                ),
            }.get(classification, StudyRuntimeReason.QUEST_WAITING_ON_INVALID_BLOCKING)
            result.set_decision(
                StudyRuntimeDecision.RESUME,
                resume_reason,
            )
            return finalize_result()
        if classification == "external_input_required":
            result.set_decision(
                StudyRuntimeDecision.BLOCKED,
                StudyRuntimeReason.QUEST_WAITING_FOR_EXTERNAL_INPUT,
            )
            return finalize_result()
    if submission_metadata_only_wait and submission_metadata_only_manual_finish:
        result.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.QUEST_WAITING_FOR_SUBMISSION_METADATA,
        )
        return finalize_result()
    if submission_metadata_only_wait:
        result.set_decision(
            StudyRuntimeDecision.RESUME,
            StudyRuntimeReason.QUEST_WAITING_FOR_SUBMISSION_METADATA,
        )
        return finalize_result()
    result.set_decision(
        StudyRuntimeDecision.BLOCKED,
        StudyRuntimeReason.QUEST_WAITING_FOR_USER,
    )
    return finalize_result()


__all__ = [
    "_apply_live_quest_status_decision",
    "_apply_resumable_quest_status_decision",
    "_apply_stopped_or_failed_quest_status_decision",
    "_apply_waiting_for_user_status_decision",
]
