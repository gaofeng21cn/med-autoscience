from __future__ import annotations


LIVE_ATTEMPT_SUPERSEDED_BLOCKERS = frozenset(
    {
        "live_worker_requires_worker_running",
        "managed_runtime_audit_unhealthy",
        "domain_owner_action_dispatch_execution_count_zero",
        "medical_paper_readiness_missing",
        "medical_paper_readiness_not_ready",
        "no_selected_dispatch_for_requested_action_types",
        "opl_execution_authorization_required",
        "opl_current_control_state.handoff_required",
        "opl_stage_attempt_admission_required",
        "provider_admission_current_control_state_required",
        "quest_waiting_opl_runtime_owner_route",
        "repair_progress_ai_reviewer_recheck_required",
        "run_quality_repair_batch_not_visible_in_current_opl_control_state",
        "runtime_recovery_not_authorized",
        "runtime_recovery_retry_budget_exhausted",
        "stage_packet_superseded_by_current_consumed_domain_transition",
    }
)
CURRENT_ACTION_SUPERSEDED_RUNTIME_BLOCKERS = frozenset(
    {
        "opl_execution_authorization_required",
        "opl_current_control_state.handoff_required",
        "opl_stage_attempt_admission_required",
        "provider_admission_current_control_state_required",
        "quest_marked_running_but_no_live_session",
        "quest_waiting_opl_runtime_owner_route",
        "repair_progress_ai_reviewer_recheck_required",
        "repair_progress_gate_replay_required",
        "runtime_recovery_not_authorized",
        "current_typed_blocker_precedes_provider_admission",
    }
)
MEDICAL_READINESS_BLOCKERS = frozenset(
    {
        "medical_paper_readiness_missing",
        "medical_paper_readiness_not_ready",
    }
)
CURRENT_ACTION_SUPERSEDED_PRIOR_ACTION_BLOCKERS = frozenset(
    {
        "domain_owner_action_dispatch_execution_count_zero",
        "domain_owner_action_dispatch_zero_selected_dispatch",
        "current_work_unit_already_typed_closeout_packet_required",
        "gate_clearing_batch_source_eval_currentness_mismatch",
        "no_selected_dispatch_for_requested_action_types",
        "owner_route_stale",
        "run_quality_repair_batch_not_visible_in_current_opl_control_state",
        "stale_stage_attempt_current_owner_route_superseded",
        "stage_packet_superseded_by_current_consumed_domain_transition",
        "stale_stage_packet_current_owner_route_changed",
    }
)
PAPER_DELTA_PRIOR_BLOCKER_SUPERSEDING_ACTION_SOURCES = frozenset(
    {
        "domain_transition",
        "repair_progress_projection.mas_owner_repair_execution_evidence",
        "study_progress.next_forced_delta.owner_action",
    }
)
OPL_CURRENT_CONTROL_ACTION_QUEUE_SOURCE = "opl_current_control_state_action_queue"
PUBLICATION_EVAL_READINESS_REPAIR_SOURCE = "publication_eval.recommended_actions.readiness_blocker_repair"
PROVIDER_ADMISSION_REPAIR_ACTIONS = frozenset(
    {
        "return_to_ai_reviewer_workflow",
        "run_gate_clearing_batch",
        "run_quality_repair_batch",
    }
)
PROVIDER_ADMISSION_AUTHORITIES = frozenset({"mas_provider_admission_identity"})
REASON_ONLY_TYPED_BLOCKERS = frozenset(
    {
        "medical_paper_readiness_missing",
        "medical_paper_readiness_not_ready",
        "medical_prose_review_request_rehydrate_required",
        "paper_progress_stall_current_missing",
        "paper_progress_stall_fingerprint_stale",
        "paper_progress_stall_terminal",
        "progress_first_owner_redrive_budget_exhausted",
        "typed_closeout_packet_required",
    }
)
RUNNING_HEALTH_VALUES = frozenset(
    {
        "attempt_running",
        "live",
        "provider_admitted",
        "running",
    }
)
TERMINAL_CLOSEOUT_STATUSES = frozenset(
    {
        "blocked",
        "closed",
        "closed_with_domain_owner_refs",
        "closed_with_owner_receipt_refs",
        "completed",
        "completed_with_domain_owner_record_only_archive",
        "completed_with_record_only_artifact_delta",
        "executed",
        "executed_progress_delta",
        "executed_record_only",
        "executed_record_only_archive_materialized",
        "owner_receipt",
        "executed_with_domain_side_effect_observed",
        "executed_with_owner_receipt",
        "failed",
        "materialized_record_only_archive",
        "record_materialized_with_domain_owner_followthrough_observed",
        "record_only_archive_materialized",
        "repeat_suppressed",
        "terminal",
        "typed_blocked",
    }
)


__all__ = [
    "CURRENT_ACTION_SUPERSEDED_PRIOR_ACTION_BLOCKERS",
    "CURRENT_ACTION_SUPERSEDED_RUNTIME_BLOCKERS",
    "LIVE_ATTEMPT_SUPERSEDED_BLOCKERS",
    "MEDICAL_READINESS_BLOCKERS",
    "OPL_CURRENT_CONTROL_ACTION_QUEUE_SOURCE",
    "PAPER_DELTA_PRIOR_BLOCKER_SUPERSEDING_ACTION_SOURCES",
    "PUBLICATION_EVAL_READINESS_REPAIR_SOURCE",
    "PROVIDER_ADMISSION_AUTHORITIES",
    "PROVIDER_ADMISSION_REPAIR_ACTIONS",
    "REASON_ONLY_TYPED_BLOCKERS",
    "RUNNING_HEALTH_VALUES",
    "TERMINAL_CLOSEOUT_STATUSES",
]
