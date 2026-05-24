from __future__ import annotations

from .default_executor_dispatch_tasks import TASK_KIND as DEFAULT_EXECUTOR_DISPATCH_TASK_KIND


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
    "domain_route/owner-handoff": "domain_route_owner_handoff",
    "paper_autonomy/repair-recheck": "paper_repair_executor_dispatch",
    "paper_autonomy/ai-reviewer-recheck": "ai_reviewer_recheck_execute_dispatch",
    "paper_autonomy/guarded-apply": "paper_autonomy_guarded_apply",
    DEFAULT_EXECUTOR_DISPATCH_TASK_KIND: "default_executor_dispatch_request",
    "publication_aftercare/analysis-queue-progress": "domain_route_owner_handoff",
    "publication_aftercare/reviewer-refresh": "ai_reviewer_recheck_execute_dispatch",
    "paper_autonomy/gate-replay": "domain_route_owner_handoff",
    "paper_autonomy/route-decision": "domain_route_owner_handoff",
    "safe_reconcile/dry-run": "safe_reconcile_dry_run",
    "study_progress/read": "study_progress_read",
    "status/read": "status_read",
    "notification/receipt": "notification_receipt",
}
