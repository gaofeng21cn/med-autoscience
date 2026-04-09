from __future__ import annotations

from importlib import import_module
import json
from pathlib import Path

from med_autoscience.controllers import (
    publication_gate as publication_gate_controller,
    runtime_reentry_gate as runtime_reentry_gate_controller,
    startup_data_readiness as startup_data_readiness_controller,
    startup_boundary_gate as startup_boundary_gate_controller,
)
from med_autoscience.controllers.study_runtime_types import (
    StudyRuntimeAuditRecord,
    StudyRuntimeAuditStatus,
    StudyRuntimeDecision,
    StudyRuntimeExecutionOwnerGuard,
    StudyRuntimeQuestStatus,
    StudyRuntimeReason,
    StudyRuntimeStatus,
    _LIVE_QUEST_STATUSES,
    _RESUMABLE_QUEST_STATUSES,
)
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_protocol import paper_artifacts
from med_autoscience.runtime_protocol import quest_state
from med_autoscience.runtime_protocol import study_runtime as study_runtime_protocol
from med_autoscience.study_completion import StudyCompletionStateStatus


_SUBMISSION_METADATA_ONLY_BLOCKING_ITEM_IDS = frozenset(
    {
        "author_metadata",
        "author_affiliations",
        "corresponding_author",
        "corresponding_author_contact",
        "ethics_statement",
        "human_subjects_consent_statement",
        "ai_declaration",
        "funding_statement",
        "conflict_of_interest_statement",
        "data_availability_statement",
        "acknowledgments",
    }
)

_SUPERVISOR_ONLY_ALLOWED_ACTIONS = (
    "read_runtime_status",
    "notify_user_runtime_is_live",
    "open_monitoring_entry",
    "pause_runtime",
    "resume_runtime",
    "stop_runtime",
    "record_user_decision",
)
_SUPERVISOR_ONLY_FORBIDDEN_ACTIONS = (
    "direct_study_execution",
    "direct_runtime_owned_write",
    "direct_paper_line_write",
    "direct_bundle_build",
    "direct_compiled_bundle_proofing",
)


def _router_module():
    return import_module("med_autoscience.controllers.study_runtime_router")


def _normalize_submission_blocking_item_ids(payload: dict[str, object]) -> tuple[str, ...]:
    raw_items = payload.get("blocking_items")
    if not isinstance(raw_items, list):
        return ()
    normalized: list[str] = []
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        item_id = str(item.get("id") or "").strip()
        if item_id:
            normalized.append(item_id)
    return tuple(normalized)


def _waiting_submission_metadata_only(quest_root: Path) -> bool:
    paper_bundle_manifest_path = paper_artifacts.resolve_paper_bundle_manifest(quest_root)
    if paper_bundle_manifest_path is None:
        return False
    checklist_path = paper_bundle_manifest_path.parent / "review" / "submission_checklist.json"
    if not checklist_path.exists():
        return False
    try:
        payload = json.loads(checklist_path.read_text(encoding="utf-8")) or {}
    except (OSError, json.JSONDecodeError):
        return False
    if not isinstance(payload, dict):
        return False
    blocking_item_ids = _normalize_submission_blocking_item_ids(payload)
    if not blocking_item_ids:
        return False
    return all(item_id in _SUBMISSION_METADATA_ONLY_BLOCKING_ITEM_IDS for item_id in blocking_item_ids)


def _record_quest_runtime_audits(
    *,
    status: StudyRuntimeStatus,
    quest_runtime: quest_state.QuestRuntimeSnapshot,
) -> quest_state.QuestRuntimeLivenessStatus:
    runtime_liveness_audit = StudyRuntimeAuditRecord.from_payload(dict(quest_runtime.runtime_liveness_audit or {}))
    bash_session_audit = StudyRuntimeAuditRecord.from_payload(dict(quest_runtime.bash_session_audit or {}))
    status.record_runtime_liveness_audit(runtime_liveness_audit)
    status.record_bash_session_audit(bash_session_audit)
    return quest_runtime.runtime_liveness_status


def _publication_gate_allows_direct_write(status: StudyRuntimeStatus) -> bool:
    try:
        return not status.publication_supervisor_state.bundle_tasks_downstream_only
    except KeyError:
        return True


def _runtime_owned_roots(quest_root: Path) -> tuple[str, ...]:
    return (
        str(quest_root),
        str(quest_root / ".ds"),
        str(quest_root / "paper"),
        str(quest_root / "release"),
        str(quest_root / "artifacts"),
    )


def _record_execution_owner_guard(
    *,
    status: StudyRuntimeStatus,
    quest_root: Path,
) -> None:
    execution = status.execution
    if str(execution.get("engine") or "").strip() != "med-deepscientist":
        return
    if str(execution.get("auto_entry") or "").strip() != "on_managed_research_intent":
        return
    if not status.quest_exists or status.quest_status not in _LIVE_QUEST_STATUSES:
        return
    try:
        runtime_liveness = status.runtime_liveness_audit_record
    except KeyError:
        return
    if runtime_liveness.status is StudyRuntimeAuditStatus.NONE:
        return
    try:
        active_run_id = status.autonomous_runtime_notice.active_run_id
    except KeyError:
        active_run_id = str(runtime_liveness.payload.get("active_run_id") or "").strip() or None
    publication_gate_allows_direct_write = _publication_gate_allows_direct_write(status)
    guard_reason = "live_managed_runtime"
    current_required_action = "supervise_managed_runtime"
    controller_stage_note = (
        "live managed runtime owns study-local execution; the foreground agent must stay supervisor-only "
        "until explicit takeover"
    )
    if runtime_liveness.status is not StudyRuntimeAuditStatus.LIVE:
        guard_reason = "managed_runtime_audit_unhealthy"
        current_required_action = "inspect_runtime_health_and_decide_intervention"
        controller_stage_note = (
            "managed runtime still owns study-local execution, but the liveness audit is unhealthy; "
            "stay supervisor-only until the runtime is inspected and explicitly paused or resumed"
        )
    payload = {
        "owner": "managed_runtime",
        "supervisor_only": True,
        "guard_reason": guard_reason,
        "active_run_id": active_run_id,
        "current_required_action": current_required_action,
        "allowed_actions": list(_SUPERVISOR_ONLY_ALLOWED_ACTIONS),
        "forbidden_actions": list(_SUPERVISOR_ONLY_FORBIDDEN_ACTIONS),
        "runtime_owned_roots": list(_runtime_owned_roots(quest_root)),
        "takeover_required": True,
        "takeover_action": "pause_runtime_then_explicit_human_takeover",
        "publication_gate_allows_direct_write": publication_gate_allows_direct_write,
        "controller_stage_note": controller_stage_note,
    }
    status.record_execution_owner_guard(StudyRuntimeExecutionOwnerGuard.from_payload(payload))


def _status_state(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    study_payload: dict[str, object],
    entry_mode: str | None,
) -> StudyRuntimeStatus:
    router = _router_module()
    execution = router._execution_payload(study_payload)
    selected_entry_mode = str(entry_mode or execution.get("default_entry_mode") or "full_research").strip() or "full_research"
    quest_id = str(execution.get("quest_id") or study_id).strip() or study_id
    runtime_context = study_runtime_protocol.resolve_study_runtime_context(
        profile=profile,
        study_root=study_root,
        study_id=study_id,
        quest_id=quest_id,
    )
    runtime_root = runtime_context.runtime_root
    quest_root = runtime_context.quest_root
    runtime_binding_path = runtime_context.runtime_binding_path
    launch_report_path = runtime_context.launch_report_path
    quest_runtime = quest_state.inspect_quest_runtime(quest_root)
    quest_exists = quest_runtime.quest_exists
    quest_status = StudyRuntimeStatus._normalize_quest_status_field(quest_runtime.quest_status)
    if quest_status in _LIVE_QUEST_STATUSES:
        runtime_liveness_audit = router._inspect_quest_live_execution(
            runtime_root=runtime_root,
            quest_id=quest_id,
        )
        quest_runtime = quest_runtime.with_runtime_liveness_audit(runtime_liveness_audit).with_bash_session_audit(
            dict(runtime_liveness_audit.get("bash_session_audit") or {})
        )
    contracts = router.inspect_workspace_contracts(profile)
    readiness = startup_data_readiness_controller.startup_data_readiness(workspace_root=profile.workspace_root)
    startup_boundary_gate = startup_boundary_gate_controller.evaluate_startup_boundary(
        profile=profile,
        study_root=study_root,
        study_payload=study_payload,
        execution=execution,
    )
    runtime_reentry_gate = runtime_reentry_gate_controller.evaluate_runtime_reentry(
        study_root=study_root,
        study_payload=study_payload,
        execution=execution,
        quest_root=quest_root if quest_exists else None,
        enforce_startup_hydration=quest_status in _LIVE_QUEST_STATUSES,
    )
    completion_state = router._study_completion_state(study_root=study_root)

    result = StudyRuntimeStatus(
        schema_version=1,
        study_id=study_id,
        study_root=str(study_root),
        entry_mode=selected_entry_mode,
        execution=execution,
        quest_id=quest_id,
        quest_root=str(quest_root),
        quest_exists=quest_exists,
        quest_status=quest_status,
        runtime_binding_path=str(runtime_binding_path),
        runtime_binding_exists=runtime_binding_path.exists(),
        workspace_contracts=contracts,
        startup_data_readiness=readiness,
        startup_boundary_gate=startup_boundary_gate,
        runtime_reentry_gate=runtime_reentry_gate,
        study_completion_state=completion_state,
        controller_first_policy_summary=router.render_controller_first_summary(),
        automation_ready_summary=router.render_automation_ready_summary(),
    )

    def _finalize_result() -> StudyRuntimeStatus:
        if quest_exists:
            publication_gate_report = publication_gate_controller.build_gate_report(
                publication_gate_controller.build_gate_state(quest_root)
            )
            result.record_publication_supervisor_state(
                publication_gate_controller.extract_publication_supervisor_state(publication_gate_report)
            )
        router._record_autonomous_runtime_notice_if_required(
            status=result,
            runtime_root=runtime_root,
            launch_report_path=launch_report_path,
        )
        _record_execution_owner_guard(status=result, quest_root=quest_root)
        if not result.should_refresh_startup_hydration_while_blocked():
            result.extras.pop("runtime_escalation_ref", None)
            return result
        runtime_escalation_ref = study_runtime_protocol.read_runtime_escalation_record_ref(quest_root=quest_root)
        if runtime_escalation_ref is not None:
            result.record_runtime_escalation_ref(runtime_escalation_ref)
        return result

    if str(execution.get("engine") or "").strip() != "med-deepscientist":
        result.set_decision(
            StudyRuntimeDecision.LIGHTWEIGHT,
            StudyRuntimeReason.STUDY_EXECUTION_NOT_MED_DEEPSCIENTIST,
        )
        return _finalize_result()

    auto_entry = str(execution.get("auto_entry") or "").strip()
    default_entry_mode = str(execution.get("default_entry_mode") or "full_research").strip() or "full_research"
    if auto_entry != "on_managed_research_intent":
        result.set_decision(
            StudyRuntimeDecision.LIGHTWEIGHT,
            StudyRuntimeReason.STUDY_EXECUTION_NOT_MANAGED,
        )
        return _finalize_result()
    if selected_entry_mode != default_entry_mode:
        result.set_decision(
            StudyRuntimeDecision.LIGHTWEIGHT,
            StudyRuntimeReason.ENTRY_MODE_NOT_MANAGED,
        )
        return _finalize_result()

    completion_contract_status = completion_state.status
    if completion_contract_status in {
        StudyCompletionStateStatus.INVALID,
        StudyCompletionStateStatus.INCOMPLETE,
    }:
        result.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.STUDY_COMPLETION_CONTRACT_NOT_READY,
        )
        return _finalize_result()
    if completion_state.ready:
        if not quest_exists:
            result.set_decision(
                StudyRuntimeDecision.COMPLETED,
                StudyRuntimeReason.STUDY_COMPLETION_DECLARED_WITHOUT_MANAGED_QUEST,
            )
            return _finalize_result()
        if quest_status == StudyRuntimeQuestStatus.COMPLETED:
            result.set_decision(
                StudyRuntimeDecision.COMPLETED,
                StudyRuntimeReason.QUEST_ALREADY_COMPLETED,
            )
            return _finalize_result()
        if quest_status in _LIVE_QUEST_STATUSES:
            audit_status = router._record_quest_runtime_audits(status=result, quest_runtime=quest_runtime)
            if audit_status is quest_state.QuestRuntimeLivenessStatus.UNKNOWN:
                result.set_decision(
                    StudyRuntimeDecision.BLOCKED,
                    StudyRuntimeReason.STUDY_COMPLETION_LIVE_RUNTIME_AUDIT_FAILED,
                )
            elif audit_status is quest_state.QuestRuntimeLivenessStatus.LIVE:
                result.set_decision(
                    StudyRuntimeDecision.PAUSE_AND_COMPLETE,
                    StudyRuntimeReason.STUDY_COMPLETION_READY,
                )
            else:
                result.set_decision(
                    StudyRuntimeDecision.SYNC_COMPLETION,
                    StudyRuntimeReason.STUDY_COMPLETION_READY,
                )
            return _finalize_result()
        result.set_decision(
            StudyRuntimeDecision.SYNC_COMPLETION,
            StudyRuntimeReason.STUDY_COMPLETION_READY,
        )
        return _finalize_result()

    if not result.workspace_overall_ready:
        result.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.WORKSPACE_CONTRACT_NOT_READY,
        )
        return _finalize_result()

    if result.has_unresolved_contract_for(study_id):
        result.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.STUDY_DATA_READINESS_BLOCKED,
        )
        return _finalize_result()

    startup_contract_validation = study_runtime_protocol.validate_startup_contract_resolution(
        startup_contract=router._build_startup_contract(
            profile=profile,
            study_id=study_id,
            study_root=study_root,
            study_payload=study_payload,
            execution=execution,
        )
    )
    result.record_startup_contract_validation(startup_contract_validation.to_dict())
    if startup_contract_validation.status is not study_runtime_protocol.StartupContractValidationStatus.CLEAR:
        result.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.STARTUP_CONTRACT_RESOLUTION_FAILED,
        )
        return _finalize_result()

    if not quest_exists:
        if result.startup_boundary_allows_compute_stage:
            if result.runtime_reentry_allows_runtime_entry:
                result.set_decision(
                    StudyRuntimeDecision.CREATE_AND_START,
                    StudyRuntimeReason.QUEST_MISSING,
                )
            else:
                result.set_decision(
                    StudyRuntimeDecision.BLOCKED,
                    StudyRuntimeReason.RUNTIME_REENTRY_NOT_READY_FOR_AUTO_START,
                )
        else:
            result.set_decision(
                StudyRuntimeDecision.CREATE_ONLY,
                StudyRuntimeReason.STARTUP_BOUNDARY_NOT_READY_FOR_AUTO_START,
            )
        return _finalize_result()

    if quest_status in _LIVE_QUEST_STATUSES:
        audit_status = router._record_quest_runtime_audits(status=result, quest_runtime=quest_runtime)
        if audit_status is quest_state.QuestRuntimeLivenessStatus.UNKNOWN:
            result.set_decision(
                StudyRuntimeDecision.BLOCKED,
                StudyRuntimeReason.RUNNING_QUEST_LIVE_SESSION_AUDIT_FAILED,
            )
        elif audit_status is quest_state.QuestRuntimeLivenessStatus.LIVE:
            if not result.startup_boundary_allows_compute_stage:
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
                StudyRuntimeReason.QUEST_MARKED_RUNNING_BUT_NO_LIVE_SESSION,
            )
        else:
            result.set_decision(
                StudyRuntimeDecision.BLOCKED,
                StudyRuntimeReason.QUEST_MARKED_RUNNING_BUT_AUTO_RESUME_DISABLED,
            )
        return _finalize_result()

    if quest_status in _RESUMABLE_QUEST_STATUSES:
        if not result.startup_boundary_allows_compute_stage:
            result.set_decision(
                StudyRuntimeDecision.BLOCKED,
                StudyRuntimeReason.STARTUP_BOUNDARY_NOT_READY_FOR_RESUME,
            )
            return _finalize_result()
        if not result.runtime_reentry_allows_runtime_entry:
            result.set_decision(
                StudyRuntimeDecision.BLOCKED,
                StudyRuntimeReason.RUNTIME_REENTRY_NOT_READY_FOR_RESUME,
            )
            return _finalize_result()
        if execution.get("auto_resume") is True:
            resumable_reason = {
                StudyRuntimeQuestStatus.PAUSED: StudyRuntimeReason.QUEST_PAUSED,
                StudyRuntimeQuestStatus.STOPPED: StudyRuntimeReason.QUEST_STOPPED,
            }.get(quest_status, StudyRuntimeReason.QUEST_INITIALIZED_WAITING_TO_START)
            result.set_decision(
                StudyRuntimeDecision.RESUME,
                resumable_reason,
            )
        else:
            blocked_reason = {
                StudyRuntimeQuestStatus.PAUSED: StudyRuntimeReason.QUEST_PAUSED_BUT_AUTO_RESUME_DISABLED,
                StudyRuntimeQuestStatus.STOPPED: StudyRuntimeReason.QUEST_STOPPED_BUT_AUTO_RESUME_DISABLED,
            }.get(quest_status, StudyRuntimeReason.QUEST_INITIALIZED_BUT_AUTO_RESUME_DISABLED)
            result.set_decision(
                StudyRuntimeDecision.BLOCKED,
                blocked_reason,
            )
        return _finalize_result()

    if quest_status == StudyRuntimeQuestStatus.STOPPED:
        result.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.QUEST_STOPPED_REQUIRES_EXPLICIT_RERUN,
        )
        return _finalize_result()

    if quest_status == StudyRuntimeQuestStatus.WAITING_FOR_USER:
        if _waiting_submission_metadata_only(quest_root):
            if execution.get("auto_resume") is True:
                result.set_decision(
                    StudyRuntimeDecision.RESUME,
                    StudyRuntimeReason.QUEST_WAITING_FOR_SUBMISSION_METADATA,
                )
            else:
                result.set_decision(
                    StudyRuntimeDecision.BLOCKED,
                    StudyRuntimeReason.QUEST_WAITING_FOR_SUBMISSION_METADATA_BUT_AUTO_RESUME_DISABLED,
                )
            return _finalize_result()
        result.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.QUEST_WAITING_FOR_USER,
        )
        return _finalize_result()

    result.set_decision(
        StudyRuntimeDecision.BLOCKED,
        StudyRuntimeReason.QUEST_EXISTS_WITH_NON_RESUMABLE_STATE,
    )
    return _finalize_result()


def _status_payload(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    study_payload: dict[str, object],
    entry_mode: str | None,
) -> dict[str, object]:
    router = _router_module()
    return router._status_state(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
        study_payload=study_payload,
        entry_mode=entry_mode,
    ).to_dict()
