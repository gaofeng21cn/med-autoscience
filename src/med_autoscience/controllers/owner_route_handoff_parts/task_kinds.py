from __future__ import annotations

FORBIDDEN_PAYLOAD_FLAGS = (
    "domain_truth_write",
    "artifact_gate_override",
    "study_truth_write",
    "publication_quality_verdict",
    "current_package_write",
    "memory_body_write",
    "publication_route_memory_writeback_accept",
    "memory_write_router_accept",
)
ALLOWED_TASK_KINDS = {
    "paper_autonomy/repair-recheck": "paper_repair_executor_dispatch",
    "paper_autonomy/ai-reviewer-recheck": "ai_reviewer_recheck_execute_dispatch",
    "paper_autonomy/guarded-apply": "paper_autonomy_guarded_apply",
    "paper_autonomy/supervisor-decision": "opl_paper_autonomy_supervisor_decision_request",
    "publication_aftercare/analysis-queue-progress": "stage_outcome_opl_handoff",
    "publication_aftercare/reviewer-refresh": "ai_reviewer_recheck_execute_dispatch",
    "paper_autonomy/gate-replay": "stage_outcome_opl_handoff",
    "paper_autonomy/route-decision": "stage_outcome_opl_handoff",
    "safe_reconcile/dry-run": "safe_reconcile_dry_run",
    "study_progress/read": "study_progress_read",
    "status/read": "status_read",
    "notification/receipt": "notification_receipt",
}
RETIRED_DIAGNOSTIC_TASK_KINDS: dict[str, str] = {
    "domain_route/reconcile-apply": "retired_owner_route_reconcile_task_kind",
    "domain_owner/owner-callable-adapter": "retired_owner_callable_adapter_task_kind",
    "domain_owner/default-executor-dispatch": "retired_default_executor_dispatch_task_kind",
}
