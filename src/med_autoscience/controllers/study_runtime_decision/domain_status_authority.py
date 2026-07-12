from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

if __name__ != "med_autoscience.controllers.study_runtime_decision":
    from .manual_finish_dominance import *  # noqa: F403
    from .publication_and_submission import *  # noqa: F403
    from .runtime_events import *  # noqa: F403
    from .domain_transition_status import *  # noqa: F403
    from .quest_status_decisions import *  # noqa: F403
    from .status_projection_shell import *  # noqa: F403
    from .supervisor_state_overrides import *  # noqa: F403

from . import publication_and_submission as _publication_and_submission
from med_autoscience.controllers import study_truth_kernel
from med_autoscience.controllers.progress_projection.runtime_result_types import (
    StartupContractValidation,
    StartupContractValidationStatus,
)
from med_autoscience.controllers.study_runtime_types import StudyRuntimeAuditStatus, StudyRuntimeQuestStatus
from med_autoscience.workspace_contracts import build_workspace_runtime_layout_for_profile

_OPL_CURRENT_CONTROL_STATE_STALE_AFTER_SECONDS = 10 * 60
_OPL_TERMINAL_SUCCESS_STATES = {"succeeded"}


def validate_startup_contract_resolution(*, startup_contract: dict[str, Any]) -> StartupContractValidation:
    def validate_contract(
        *,
        payload: object,
        missing_blocker: str,
        invalid_blocker: str,
        unsupported_blocker: str,
        unresolved_blocker: str,
    ) -> tuple[str | None, str | None, str | None]:
        if payload is None:
            return None, missing_blocker, None
        if not isinstance(payload, dict):
            return None, invalid_blocker, None
        status = str(payload.get("status") or "").strip()
        reason_code = str(payload.get("reason_code") or "").strip() or None
        if status == "resolved":
            return status, None, reason_code
        if status == "unsupported":
            return status, unsupported_blocker, reason_code
        return status or None, unresolved_blocker, reason_code

    blockers: list[str] = []
    analysis_status, analysis_blocker, analysis_reason = validate_contract(
        payload=startup_contract.get("medical_analysis_contract_summary"),
        missing_blocker="missing_medical_analysis_contract",
        invalid_blocker="invalid_medical_analysis_contract",
        unsupported_blocker="unsupported_medical_analysis_contract",
        unresolved_blocker="unresolved_medical_analysis_contract",
    )
    reporting_status, reporting_blocker, reporting_reason = validate_contract(
        payload=startup_contract.get("medical_reporting_contract_summary"),
        missing_blocker="missing_medical_reporting_contract",
        invalid_blocker="invalid_medical_reporting_contract",
        unsupported_blocker="unsupported_medical_reporting_contract",
        unresolved_blocker="unresolved_medical_reporting_contract",
    )
    if analysis_blocker is not None:
        blockers.append(analysis_blocker)
    if reporting_blocker is not None:
        blockers.append(reporting_blocker)
    return StartupContractValidation(
        status=StartupContractValidationStatus.BLOCKED if blockers else StartupContractValidationStatus.CLEAR,
        blockers=tuple(blockers),
        medical_analysis_contract_status=analysis_status,
        medical_reporting_contract_status=reporting_status,
        medical_analysis_reason_code=analysis_reason,
        medical_reporting_reason_code=reporting_reason,
    )


def should_attach_runtime_escalation_ref(status: dict[str, Any]) -> bool:
    if not bool(status.get("quest_exists")):
        return False
    decision = str(status.get("decision") or "").strip()
    quest_status = str(status.get("quest_status") or "").strip()
    reason = str(status.get("reason") or "").strip()
    if decision == "blocked" and quest_status in {"created", "idle", "paused"} and reason in {
        "startup_boundary_not_ready_for_resume",
        "runtime_reentry_not_ready_for_resume",
        "quest_paused_but_auto_resume_disabled",
        "quest_initialized_but_auto_resume_disabled",
    }:
        return True
    if (
        decision != "handoff_required"
        or reason != "opl_stage_attempt_admission_required"
        or quest_status not in {"active", "running", "paused"}
    ):
        return False
    request = _mapping(status.get("ai_reviewer_request")) or _read_ai_reviewer_request_from_status(status)
    if not request:
        return False
    input_contract = _mapping(request.get("input_contract"))
    if input_contract.get("all_required_refs_present") is True:
        return False
    missing_or_invalid = _text_set(input_contract.get("missing_or_invalid_refs"))
    if "opl_stage_folder_state_index_refs" not in missing_or_invalid:
        return False
    stage_ref = _mapping(_mapping(input_contract.get("required_refs")).get("opl_stage_folder_state_index_refs"))
    ref = str(stage_ref.get("relative_path") or stage_ref.get("ref") or "").strip()
    if ref and ref != "opl-stage-folder://review/latest.json":
        return False
    missing_reasons = {
        *_text_set(stage_ref.get("missing_reasons")),
        *_text_set(request.get("stage_knowledge_missing_reasons")),
    }
    return "missing_ref:study_reference_context" in missing_reasons


def _read_ai_reviewer_request_from_status(status: dict[str, Any]) -> dict[str, Any]:
    study_root = str(status.get("study_root") or "").strip()
    if not study_root:
        return {}
    path = Path(study_root).expanduser() / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(payload, dict):
        return {}
    if str(payload.get("surface_kind") or "").strip() == "legacy_control_surface_tombstone":
        return {}
    return dict(payload)


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _text_set(value: object) -> set[str]:
    if not isinstance(value, list):
        return set()
    return {text for item in value if (text := str(item or "").strip())}


def _parsed_utc_datetime(value: object) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _truth_explicit_resume_releases_pause_gate(
    *,
    study_root: Path,
    study_id: str,
) -> bool:
    snapshot = study_truth_kernel.rebuild_truth_snapshot(study_root=study_root, study_id=study_id)
    if str(snapshot.get("canonical_next_action") or "").strip() not in {
        "resume_same_study_line",
        "resume_runtime",
        "relaunch_same_study_line",
    }:
        return False
    refs = snapshot.get("dominant_authority_refs")
    if not isinstance(refs, list) or not refs:
        return False
    latest_ref = refs[0]
    if not isinstance(latest_ref, dict):
        return False
    if str(latest_ref.get("event_type") or "").strip() != "explicit_resume":
        return False
    resume_at = _parsed_utc_datetime(latest_ref.get("recorded_at"))
    return resume_at is not None


def _status_state(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    study_payload: dict[str, object],
    entry_mode: str | None,
    sync_runtime_summary: bool = True,
    include_progress_projection: bool = True,
) -> ProgressProjectionStatus:
    router = _router_module()
    execution = router._execution_payload(study_payload, profile=profile)
    explicit_opl_runtime_ref = opl_runtime_contract.explicit_opl_runtime_ref(execution)
    selected_entry_mode = str(entry_mode or execution.get("default_entry_mode") or "full_research").strip() or "full_research"
    quest_id = str(execution.get("quest_id") or study_id).strip() or study_id
    runtime_layout = build_workspace_runtime_layout_for_profile(profile)
    runtime_root = runtime_layout.runtime_root
    quest_root = profile.runtime_root / quest_id
    quest_exists = (quest_root / "quest.yaml").exists()
    quest_status = StudyRuntimeQuestStatus.CREATED if quest_exists else None
    runtime_liveness_audit: dict[str, object] | None = None
    if quest_exists and opl_runtime_contract.is_opl_hosted_research_execution(execution):
        runtime_liveness_audit = _opl_current_control_state_runtime_liveness_projection(
            profile=profile,
            study_root=study_root,
            study_id=study_id,
            quest_status=quest_status,
        ) or _unknown_opl_current_control_state_runtime_liveness(quest_status=quest_status)
        snapshot = runtime_liveness_audit.get("snapshot")
        if isinstance(snapshot, dict):
            projected_status = ProgressProjectionStatus._normalize_quest_status_field(snapshot.get("status"))
            quest_status = projected_status or quest_status
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
    )
    completion_state = router._study_completion_state(study_root=study_root)
    result = ProgressProjectionStatus(
        schema_version=1,
        study_id=study_id,
        study_root=str(study_root),
        entry_mode=selected_entry_mode,
        execution=execution,
        quest_id=quest_id,
        quest_root=str(quest_root),
        quest_exists=quest_exists,
        quest_status=quest_status,
        workspace_contracts=contracts,
        startup_data_readiness=readiness,
        startup_boundary_gate=startup_boundary_gate,
        runtime_reentry_gate=runtime_reentry_gate,
        study_completion_state=completion_state,
        controller_first_policy_summary=router.render_controller_first_summary(),
        automation_ready_summary=router.render_automation_ready_summary(),
    )

    if quest_exists:
        from med_autoscience.study_task_intake import build_task_intake_progress_override

        publication_gate_report = publication_gate_controller.build_gate_report(
            publication_gate_controller.build_gate_state(quest_root)
        )
        task_intake_progress_override = build_task_intake_progress_override(
            read_latest_task_intake(study_root=study_root),
            study_root=study_root,
            publishability_gate_report=publication_gate_report,
        )
        result.record_publication_supervisor_state(
            _task_intake_publication_supervisor_state(task_intake_progress_override)
            or publication_gate_controller.extract_publication_supervisor_state(publication_gate_report)
        )
        manual_finish_state = _derive_manual_finish_dominance_state(
            quest_exists=quest_exists,
            quest_status=quest_status,
            study_root=study_root,
            quest_root=quest_root,
            publication_gate_report=publication_gate_report,
        )
        if sync_runtime_summary:
            _materialize_publication_eval_from_gate_report(
                study_root=study_root,
                study_id=study_id,
                quest_root=quest_root,
                quest_id=quest_id,
                publication_gate_report=publication_gate_report,
            )
    else:
        publication_gate_report = None
        manual_finish_state = _derive_manual_finish_dominance_state(
            quest_exists=quest_exists,
            quest_status=quest_status,
            study_root=study_root,
            quest_root=quest_root,
            publication_gate_report=publication_gate_report,
        )
    task_intake_releases_manual_finish_parking = manual_finish_state["task_intake_releases_manual_finish_parking"]
    reviewer_revision_open_blockers_release_manual_finish_parking = manual_finish_state[
        "reviewer_revision_open_blockers_release_manual_finish_parking"
    ]
    submission_metadata_only_manual_finish = manual_finish_state["submission_metadata_only_manual_finish"]
    task_intake_yields_to_submission_closeout = manual_finish_state["task_intake_yields_to_submission_closeout"]
    manual_hold_task_intake = manual_finish_state["manual_hold_task_intake"]
    bundle_only_manual_finish = manual_finish_state["bundle_only_manual_finish"]
    manual_finish_compatibility_guard = manual_finish_state["manual_finish_compatibility_guard"]
    submission_metadata_only_wait = manual_finish_state["submission_metadata_only_wait"]
    task_intake_releases_bare_paused_parking = (
        task_intake_releases_manual_finish_parking
        and not task_intake_yields_to_submission_closeout
    )
    explicit_resume_releases_pause_gate = _truth_explicit_resume_releases_pause_gate(
        study_root=study_root,
        study_id=study_id,
    )
    _record_continuation_state_if_present(
        status=result,
        quest_root=quest_root,
        active_run_id=_runtime_liveness_active_run_id(runtime_liveness_audit),
        live_opl_provider_attempt=(
            _runtime_liveness_active_run_id(runtime_liveness_audit) is not None
        ),
    )
    _record_interaction_arbitration_if_required(
        status=result,
        execution=execution,
        submission_metadata_only=submission_metadata_only_wait,
        publication_gate_report=publication_gate_report,
    )

    def _finalize_result() -> ProgressProjectionStatus:
        return finalize_status_projection_shell(
            status=result,
            study_id=study_id,
            profile=profile,
            study_root=study_root,
            quest_id=quest_id,
            quest_root=quest_root,
            runtime_liveness_audit=runtime_liveness_audit,
            router=router,
            entry_mode=entry_mode,
            sync_runtime_summary=sync_runtime_summary,
            include_progress_projection=include_progress_projection,
        )

    if explicit_opl_runtime_ref is not None and not opl_runtime_contract.is_opl_hosted_research_execution(execution):
        result.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.STUDY_EXECUTION_RUNTIME_BACKEND_UNBOUND,
        )
        return _finalize_result()

    if not opl_runtime_contract.is_opl_hosted_research_execution(execution):
        result.set_decision(
            StudyRuntimeDecision.LIGHTWEIGHT,
            StudyRuntimeReason.STUDY_EXECUTION_NOT_MANAGED_RUNTIME_BACKEND,
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
    if _publication_supervisor_requests_stop_loss(result):
        result.set_decision(
            StudyRuntimeDecision.PAUSE if quest_status in _LIVE_QUEST_STATUSES else StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.PUBLISHABILITY_STOP_LOSS_RECOMMENDED,
        )
        return _finalize_result()
    if manual_hold_task_intake or _publication_supervisor_requests_manual_hold(result):
        result.set_decision(
            StudyRuntimeDecision.PAUSE if quest_status in _LIVE_QUEST_STATUSES else StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.QUEST_WAITING_FOR_EXPLICIT_WAKEUP_AFTER_MANUAL_HOLD,
        )
        return _finalize_result()
    study_charter_gate_reason = _study_charter_gate_reason(publication_gate_report)
    if study_charter_gate_reason is not None:
        result.set_decision(
            StudyRuntimeDecision.BLOCKED,
            study_charter_gate_reason,
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
        contract = completion_state.contract
        if contract is not None and contract.requires_program_human_confirmation:
            result.set_decision(
                StudyRuntimeDecision.BLOCKED,
                StudyRuntimeReason.STUDY_COMPLETION_REQUIRES_PROGRAM_HUMAN_CONFIRMATION,
            )
            return _finalize_result()
        if quest_exists and quest_status == StudyRuntimeQuestStatus.COMPLETED:
            result.set_decision(
                StudyRuntimeDecision.COMPLETED,
                StudyRuntimeReason.QUEST_ALREADY_COMPLETED,
            )
            return _finalize_result()
        if _apply_completion_publication_gate_decision(
            result,
            study_root=study_root,
            publication_gate_report=publication_gate_report,
        ):
            return _finalize_result()
        if not quest_exists:
            result.set_decision(
                StudyRuntimeDecision.COMPLETED,
                StudyRuntimeReason.STUDY_COMPLETION_DECLARED_WITHOUT_MANAGED_QUEST,
            )
            return _finalize_result()
        if quest_status in _LIVE_QUEST_STATUSES:
            audit_status = router._record_quest_runtime_audits(
                status=result,
                runtime_liveness_audit=runtime_liveness_audit,
            )
            if audit_status is StudyRuntimeAuditStatus.UNKNOWN:
                result.set_decision(
                    StudyRuntimeDecision.BLOCKED,
                    StudyRuntimeReason.STUDY_COMPLETION_LIVE_RUNTIME_AUDIT_FAILED,
                )
            elif audit_status is StudyRuntimeAuditStatus.LIVE:
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
    if _is_delivered_human_review_milestone_without_live_worker(result, study_root=study_root):
        result.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.QUEST_PARKED_ON_UNCHANGED_FINALIZE_STATE,
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

    if sync_runtime_summary:
        startup_contract_validation = validate_startup_contract_resolution(
            startup_contract=router._build_startup_contract(
                profile=profile,
                study_id=study_id,
                study_root=study_root,
                study_payload=study_payload,
                execution=execution,
            )
        )
    else:
        startup_contract_validation = _read_only_startup_contract_validation(
            profile=profile,
            study_root=study_root,
            study_payload=study_payload,
        )
    result.record_startup_contract_validation(startup_contract_validation.to_dict())
    if startup_contract_validation.status is not StartupContractValidationStatus.CLEAR:
        result.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.STARTUP_CONTRACT_RESOLUTION_FAILED,
        )
        return _finalize_result()

    if quest_status in _RESUMABLE_QUEST_STATUSES:
        domain_redrive_reason = _current_ai_reviewer_domain_redrive_reason(
            result,
            study_root=study_root,
        )
        if _apply_ai_reviewer_domain_redrive_decision(
            result,
            reason=domain_redrive_reason,
            execution=execution,
            running_quest=False,
        ):
            return _finalize_result()

    if (
        manual_finish_compatibility_guard
        and (not task_intake_releases_manual_finish_parking or task_intake_yields_to_submission_closeout)
        and quest_status not in _LIVE_QUEST_STATUSES
        and not _has_domain_transition_runtime_redrive(result)
        and not _has_controller_work_unit_pending_redrive(result)
    ):
        result.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.QUEST_WAITING_FOR_SUBMISSION_METADATA,
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
        return _apply_live_quest_status_decision(
            result=result,
            router=router,
            runtime_liveness_audit=runtime_liveness_audit,
            execution=execution,
            study_root=study_root,
            study_id=study_id,
            quest_id=quest_id,
            publication_gate_report=publication_gate_report,
            manual_finish_compatibility_guard=manual_finish_compatibility_guard,
            submission_metadata_only_manual_finish=submission_metadata_only_manual_finish,
            task_intake_releases_manual_finish_parking=task_intake_releases_manual_finish_parking,
            task_intake_yields_to_submission_closeout=task_intake_yields_to_submission_closeout,
            reviewer_revision_open_blockers_release_manual_finish_parking=(
                reviewer_revision_open_blockers_release_manual_finish_parking
            ),
            explicit_resume_releases_pause_gate=explicit_resume_releases_pause_gate,
            finalize_result=_finalize_result,
        )

    if quest_status in _RESUMABLE_QUEST_STATUSES:
        return _apply_resumable_quest_status_decision(
            result=result,
            rebuild_status=lambda: _status_state(
                    profile=profile,
                    study_id=study_id,
                    study_root=study_root,
                    study_payload=study_payload,
                    entry_mode=entry_mode,
                    sync_runtime_summary=sync_runtime_summary,
                    include_progress_projection=include_progress_projection,
            ),
            execution=execution,
            study_root=study_root,
            quest_root=quest_root,
            quest_status=quest_status,
            task_intake_releases_bare_paused_parking=task_intake_releases_bare_paused_parking,
            task_intake_releases_manual_finish_parking=task_intake_releases_manual_finish_parking,
            submission_metadata_only_manual_finish=submission_metadata_only_manual_finish,
            bundle_only_manual_finish=bundle_only_manual_finish,
            explicit_resume_releases_pause_gate=explicit_resume_releases_pause_gate,
            finalize_result=_finalize_result,
        )

    if quest_status in {StudyRuntimeQuestStatus.STOPPED, StudyRuntimeQuestStatus.FAILED}:
        return _apply_stopped_or_failed_quest_status_decision(
            result=result,
            execution=execution,
            quest_status=quest_status,
            publication_gate_report=publication_gate_report,
            task_intake_releases_manual_finish_parking=task_intake_releases_manual_finish_parking,
            task_intake_yields_to_submission_closeout=task_intake_yields_to_submission_closeout,
            submission_metadata_only_manual_finish=submission_metadata_only_manual_finish,
            bundle_only_manual_finish=bundle_only_manual_finish,
            finalize_result=_finalize_result,
        )

    if quest_status == StudyRuntimeQuestStatus.WAITING_FOR_USER:
        return _apply_waiting_for_user_status_decision(
            result=result,
            submission_metadata_only_wait=submission_metadata_only_wait,
            submission_metadata_only_manual_finish=submission_metadata_only_manual_finish,
            finalize_result=_finalize_result,
        )

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
    sync_runtime_summary: bool = True,
    include_progress_projection: bool = True,
) -> dict[str, object]:
    router = _router_module()
    return router._status_state(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
        study_payload=study_payload,
        entry_mode=entry_mode,
        sync_runtime_summary=sync_runtime_summary,
        include_progress_projection=include_progress_projection,
    ).to_dict()


def _read_only_startup_contract_validation(
    *,
    profile: WorkspaceProfile,
    study_root: Path,
    study_payload: dict[str, object],
) -> StartupContractValidation:
    from med_autoscience.controllers import (
        medical_analysis_contract as medical_analysis_contract_controller,
        medical_reporting_contract as medical_reporting_contract_controller,
    )

    medical_analysis_contract_summary = medical_analysis_contract_controller.resolve_medical_analysis_contract_for_study(
        study_root=study_root,
        study_payload=study_payload,
        profile=profile,
    )
    medical_reporting_contract_summary = medical_reporting_contract_controller.resolve_medical_reporting_contract_for_study(
        study_root=study_root,
        study_payload=study_payload,
        profile=profile,
    )
    return validate_startup_contract_resolution(
        startup_contract={
            "medical_analysis_contract_summary": medical_analysis_contract_summary,
            "medical_reporting_contract_summary": medical_reporting_contract_summary,
        }
    )


def _unknown_opl_current_control_state_runtime_liveness(
    *,
    quest_status: StudyRuntimeQuestStatus | None,
) -> dict[str, object]:
    return {
        "status": "unknown",
        "source": "opl_current_control_state_required",
        "runtime_owner": "one-person-lab",
        "domain_owner": "med-autoscience",
        "mas_provider_live_query_retired": True,
        "provider_completion_is_domain_completion": False,
        "snapshot": {"status": quest_status.value if quest_status is not None else None},
    }


def _runtime_health_liveness_status(study_entry: dict[str, object]) -> str | None:
    runtime_health = study_entry.get("runtime_health")
    if isinstance(runtime_health, dict):
        value = str(runtime_health.get("runtime_liveness_status") or "").strip()
        if value:
            return value
    return str(study_entry.get("runtime_liveness_status") or "").strip() or None


def _non_empty_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _runtime_liveness_active_run_id(runtime_liveness_audit: dict[str, object] | None) -> str | None:
    if not isinstance(runtime_liveness_audit, dict):
        return None
    if str(runtime_liveness_audit.get("source") or "").strip() != "opl_current_control_state_provider_attempt":
        return None
    return str(runtime_liveness_audit.get("active_run_id") or "").strip() or None


def _timestamp_is_fresh(value: object, *, stale_after_seconds: int) -> bool:
    text = str(value or "").strip()
    if not text:
        return False
    try:
        recorded_at = datetime.fromisoformat(text)
    except ValueError:
        return False
    if recorded_at.tzinfo is None:
        recorded_at = recorded_at.replace(tzinfo=timezone.utc)
    age_seconds = max(
        0,
        int((_publication_and_submission._supervisor_tick_now().astimezone(timezone.utc) - recorded_at).total_seconds()),
    )
    return age_seconds <= stale_after_seconds


def _opl_current_control_state_runtime_liveness_projection(
    *,
    profile: WorkspaceProfile,
    study_root: Path,
    study_id: str,
    quest_status: StudyRuntimeQuestStatus | None,
) -> dict[str, object] | None:
    latest_report_path = _opl_current_control_state_handoff_path(study_root=study_root)
    latest_report = _read_opl_current_control_state_handoff(latest_report_path) or {}
    study_entry = _opl_current_control_state_study_entry(latest_report, study_id=study_id)
    if study_entry is not None:
        handoff_projection = _opl_current_control_state_handoff_liveness_projection(
            latest_report=latest_report,
            latest_report_path=latest_report_path,
            study_entry=study_entry,
            quest_status=quest_status,
        )
        if _runtime_liveness_projection_is_live_provider_attempt(handoff_projection):
            return handoff_projection
    else:
        handoff_projection = None
    return handoff_projection


def _runtime_liveness_projection_is_live_provider_attempt(
    projection: dict[str, object] | None,
) -> bool:
    if projection is None:
        return False
    return (
        projection.get("status") == "live"
        and projection.get("source") == "opl_current_control_state_provider_attempt"
        and projection.get("running_provider_attempt") is True
        and _non_empty_text(projection.get("active_run_id")) is not None
    )


def _opl_current_control_state_handoff_liveness_projection(
    *,
    latest_report: dict[str, object],
    latest_report_path: Path,
    study_entry: dict[str, object],
    quest_status: StudyRuntimeQuestStatus | None,
) -> dict[str, object] | None:
    handoff_generated_at = (
        str(
            study_entry.get("handoff_generated_at")
            or latest_report.get("generated_at")
            or latest_report.get("recorded_at")
            or ""
        ).strip()
        or None
    )
    if not _timestamp_is_fresh(
        handoff_generated_at,
        stale_after_seconds=_OPL_CURRENT_CONTROL_STATE_STALE_AFTER_SECONDS,
    ):
        return None
    active_run_id = str(study_entry.get("active_run_id") or "").strip() or None
    running_provider_attempt = study_entry.get("running_provider_attempt") is True
    if not running_provider_attempt:
        return _opl_terminal_success_handoff_liveness_projection(
            latest_report=latest_report,
            latest_report_path=latest_report_path,
            study_entry=study_entry,
            handoff_generated_at=handoff_generated_at,
            quest_status=quest_status,
        )
    if active_run_id is None or _runtime_health_liveness_status(study_entry) != "live":
        return None
    active_stage_attempt_id = str(study_entry.get("active_stage_attempt_id") or "").strip() or None
    active_workflow_id = str(study_entry.get("active_workflow_id") or "").strip() or None
    runtime_health = study_entry.get("runtime_health")
    return {
        "status": "live",
        "source": "opl_current_control_state_provider_attempt",
        "runtime_owner": "one-person-lab",
        "domain_owner": "med-autoscience",
        "mas_provider_live_query_retired": True,
        "provider_completion_is_domain_completion": False,
        "authority": str(latest_report.get("authority") or "observability_only").strip() or "observability_only",
        "active_run_id": active_run_id,
        "active_stage_attempt_id": active_stage_attempt_id,
        "active_workflow_id": active_workflow_id,
        "running_provider_attempt": True,
        "action_type": _non_empty_text(study_entry.get("action_type")),
        "work_unit_id": _non_empty_text(study_entry.get("work_unit_id")),
        "work_unit_fingerprint": _non_empty_text(study_entry.get("work_unit_fingerprint")),
        "action_fingerprint": _non_empty_text(study_entry.get("action_fingerprint")),
        "handoff_path": str(latest_report_path),
        "handoff_generated_at": handoff_generated_at,
        "runtime_health": dict(runtime_health) if isinstance(runtime_health, dict) else {},
        "stage_progress_log": _stage_progress_log(study_entry.get("stage_progress_log")),
        "snapshot": {"status": StudyRuntimeQuestStatus.ACTIVE.value},
    }


def _opl_terminal_success_handoff_liveness_projection(
    *,
    latest_report: dict[str, object],
    latest_report_path: Path,
    study_entry: dict[str, object],
    handoff_generated_at: str | None,
    quest_status: StudyRuntimeQuestStatus | None,
) -> dict[str, object] | None:
    current_attempt_state = _non_empty_text(study_entry.get("current_attempt_state"))
    reconciliation_status = _non_empty_text(study_entry.get("reconciliation_status"))
    terminal_state = reconciliation_status or current_attempt_state
    if terminal_state not in _OPL_TERMINAL_SUCCESS_STATES:
        return None
    if study_entry.get("running_provider_attempt") is not False:
        return None
    runtime_health = study_entry.get("runtime_health")
    next_work_unit = study_entry.get("next_work_unit")
    return {
        "status": "none",
        "source": "opl_current_control_state_terminal_transport_settled",
        "runtime_owner": "one-person-lab",
        "domain_owner": "med-autoscience",
        "mas_provider_live_query_retired": True,
        "provider_completion_is_domain_completion": False,
        "authority": str(latest_report.get("authority") or "observability_only").strip() or "observability_only",
        "active_run_id": None,
        "active_stage_attempt_id": None,
        "active_workflow_id": None,
        "running_provider_attempt": False,
        "handoff_path": str(latest_report_path),
        "handoff_generated_at": handoff_generated_at,
        "task_id": _non_empty_text(study_entry.get("task_id")),
        "task_kind": _non_empty_text(study_entry.get("task_kind")),
        "current_attempt_state": current_attempt_state,
        "reconciliation_status": reconciliation_status,
        "terminal_provider_transport_observation_superseded": (
            study_entry.get("terminal_provider_transport_observation_superseded") is True
        ),
        "superseded_terminal_observation_reason": _non_empty_text(
            study_entry.get("superseded_terminal_observation_reason")
        ),
        "superseded_by_task_status": _non_empty_text(study_entry.get("superseded_by_task_status")),
        "runtime_health": dict(runtime_health) if isinstance(runtime_health, dict) else {},
        "next_work_unit": dict(next_work_unit) if isinstance(next_work_unit, dict) else None,
        "snapshot": {"status": quest_status.value if quest_status is not None else None},
    }


def _opl_live_provider_attempt_liveness_projection(
    *,
    latest_report: dict[str, object],
    latest_report_path: Path,
    live_attempt: dict[str, object],
    quest_status: StudyRuntimeQuestStatus | None,
) -> dict[str, object] | None:
    active_run_id = str(live_attempt.get("active_run_id") or "").strip() or None
    if active_run_id is None or live_attempt.get("running_provider_attempt") is not True:
        return None
    runtime_health = live_attempt.get("runtime_health")
    return {
        "status": "live",
        "source": "opl_current_control_state_provider_attempt",
        "provider_attempt_source": str(
            live_attempt.get("source") or "opl_family_runtime_attempt_inspect"
        ).strip()
        or "opl_family_runtime_attempt_inspect",
        "runtime_owner": "one-person-lab",
        "domain_owner": "med-autoscience",
        "mas_provider_live_query_retired": True,
        "provider_completion_is_domain_completion": False,
        "authority": str(latest_report.get("authority") or "observability_only").strip() or "observability_only",
        "active_run_id": active_run_id,
        "active_stage_attempt_id": str(live_attempt.get("active_stage_attempt_id") or "").strip() or None,
        "active_workflow_id": str(live_attempt.get("active_workflow_id") or "").strip() or None,
        "running_provider_attempt": True,
        "action_type": _non_empty_text(live_attempt.get("action_type")),
        "work_unit_id": _non_empty_text(live_attempt.get("work_unit_id")),
        "work_unit_fingerprint": _non_empty_text(live_attempt.get("work_unit_fingerprint")),
        "action_fingerprint": _non_empty_text(live_attempt.get("action_fingerprint")),
        "handoff_path": str(latest_report_path),
        "handoff_generated_at": str(latest_report.get("generated_at") or latest_report.get("recorded_at") or "").strip()
        or None,
        "runtime_health": dict(runtime_health) if isinstance(runtime_health, dict) else {},
        "stage_progress_log": _stage_progress_log(live_attempt.get("stage_progress_log")),
        "snapshot": {"status": quest_status.value if quest_status is not None else None},
    }


def _stage_progress_log(value: object) -> dict[str, object] | None:
    if not isinstance(value, dict):
        return None
    keys = (
        "surface_kind",
        "projection_scope",
        "attempt_count",
        "completed_attempt_count",
        "blocked_attempt_count",
        "activity_event_count",
        "runner_progress_event_count",
        "duration_observed_attempt_count",
        "missing_usage_telemetry_attempt_count",
        "temporal_attempt_count",
        "temporal_webui_ref_count",
        "temporal_visibility_readiness_statuses",
        "activity_event_ref_count",
        "attempt_refs",
        "temporal_webui_refs",
        "authority_boundary",
    )
    projection = {key: value[key] for key in keys if key in value}
    return projection or None


__all__ = [name for name in globals() if not name.startswith("__")]
