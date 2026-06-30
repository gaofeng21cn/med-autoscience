from __future__ import annotations

from typing import Any


FORBIDDEN_WRITES = (
    "/Users/gaofeng/workspace/Yang/**",
    "publication_eval/latest.json",
    "controller_decisions/latest.json",
    "owner_receipt",
    "typed_blocker",
    "human_gate",
    "current_package",
    "runtime_queue",
    "provider_attempt",
    "provider_start",
    "hydrate",
    "tick",
    "redrive",
    "apply",
)
PAPER_AUDIT_PACK_FAMILIES = (
    "analysis_rationale_log",
    "decision_trace",
    "evidence_ledger_delta",
    "review_ledger_delta",
    "revision_log_delta",
    "failed_path_ledger",
    "artifact_lineage",
    "reproducibility_refs",
)
PAPER_MISSION_RUN_BLOCKED_PATHS = (
    "publication_eval/latest.json",
    "controller_decisions/latest.json",
    "current_package",
    "runtime queue/provider attempts",
    "/Users/gaofeng/workspace/Yang/**",
)
FORBIDDEN_AUTHORITY_CLAIMS = (
    "publication_ready",
    "submission_ready",
    "current_package",
    "owner_receipt_written",
    "typed_blocker_written",
    "human_gate_written",
    "controller_decision_written",
    "publication_eval_written",
    "quality_verdict",
    "artifact_authority",
    "runtime_queue_written",
    "provider_attempt_written",
    "yang_workspace_written",
)


def authority_boundary() -> dict[str, Any]:
    return {
        "write_mode": "no_write",
        "can_write_yang_workspace": False,
        "can_write_publication_eval": False,
        "can_write_controller_decisions": False,
        "can_write_owner_receipt": False,
        "can_write_typed_blocker": False,
        "can_write_human_gate": False,
        "can_write_current_package": False,
        "can_write_runtime_queue_or_provider_attempt": False,
        "forbidden_writes": list(FORBIDDEN_WRITES),
    }
