from __future__ import annotations

from typing import Any, Mapping, Sequence


SURFACE_KIND = "mas_domain_dispatch_evidence_payload_export"
PAYLOAD_REASON_CONSUMED_AI_REVIEWER_SUPERSESSION = (
    "stale_return_to_ai_reviewer_dispatch_superseded_by_consumed_ai_reviewer_routeback"
)
PAYLOAD_REASON_CONSUMED_AI_REVIEWER_PRODUCTION_HANDOFF = (
    "stale_return_to_ai_reviewer_dispatch_superseded_by_consumed_ai_reviewer_production_handoff"
)
PAYLOAD_REASON_REVIEWER_DISPATCH_SUPERSEDED_BY_AI_REVIEWER_STAGE_ADMISSION = (
    "stale_return_to_ai_reviewer_dispatch_superseded_by_current_ai_reviewer_stage_admission"
)
PAYLOAD_REASON_REVIEWER_DISPATCH_SUPERSEDED_BY_AI_REVIEWER_CURRENTNESS = (
    "stale_return_to_ai_reviewer_dispatch_superseded_by_ai_reviewer_currentness_route"
)
PAYLOAD_REASON_WRITER_DISPATCH_SUPERSEDED_BY_CONSUMED_AI_REVIEWER_ROUTEBACK = (
    "stale_run_quality_repair_dispatch_superseded_by_consumed_ai_reviewer_routeback"
)
PAYLOAD_REASON_WRITER_DISPATCH_SUPERSEDED_BY_CONSUMED_AI_REVIEWER_PRODUCTION_HANDOFF = (
    "stale_run_quality_repair_dispatch_superseded_by_consumed_ai_reviewer_production_handoff"
)
PAYLOAD_REASON_WRITER_DISPATCH_SUPERSEDED_BY_AI_REVIEWER_STAGE_ADMISSION = (
    "stale_run_quality_repair_dispatch_superseded_by_current_ai_reviewer_stage_admission"
)
PAYLOAD_REASON_AI_REVIEWER_CURRENTNESS_SUPERSESSION = (
    "stale_run_quality_repair_dispatch_superseded_by_ai_reviewer_currentness_route"
)
PAYLOAD_REASON_PUBLICATION_GATE_ROUTE_SUPERSESSION = (
    "stale_run_quality_repair_dispatch_superseded_by_publication_gate_route"
)
PAYLOAD_REASON_GATE_CLEARING_DISPATCH_SUPERSEDED_BY_PUBLICATION_GATE_ROUTE = (
    "stale_run_gate_clearing_dispatch_superseded_by_publication_gate_route"
)
PAYLOAD_REASON_REVIEWER_DISPATCH_SUPERSEDED_BY_PUBLICATION_GATE_ROUTE = (
    "stale_return_to_ai_reviewer_dispatch_superseded_by_publication_gate_route"
)
PAYLOAD_REASON_REVIEWER_DISPATCH_BLOCKED_BY_STOPPED_CURRENT_OWNER_ROUTE = (
    "stale_return_to_ai_reviewer_dispatch_blocked_by_stopped_current_owner_route"
)
PAYLOAD_REASON_WRITER_DISPATCH_BLOCKED_BY_STOPPED_CURRENT_OWNER_ROUTE = (
    "stale_run_quality_repair_dispatch_blocked_by_stopped_current_owner_route"
)
PAYLOAD_REASON_GATE_CLEARING_DISPATCH_BLOCKED_BY_STOPPED_CURRENT_OWNER_ROUTE = (
    "stale_run_gate_clearing_dispatch_blocked_by_stopped_current_owner_route"
)
PAYLOAD_REASON_OWNER_AUTHORIZED_PUBLICATION_GATE_REPLAY_STAGE_ATTEMPT_BLOCKER = (
    "owner_authorized_publication_gate_replay_stage_attempt_blocker"
)
PAYLOAD_REASON_STAGE_ATTEMPT_CLOSEOUT_TYPED_BLOCKER = (
    "stage_attempt_closeout_typed_blocker_observed_for_default_executor_dispatch"
)
PAYLOAD_REASON_STAGE_ATTEMPT_CLOSEOUT_OWNER_RECEIPT = (
    "stage_attempt_closeout_owner_receipt_observed_for_default_executor_dispatch"
)
PAYLOAD_REASON_RUNTIME_RECOVERY_RETRY_BUDGET_TERMINAL_BLOCKER = (
    "runtime_recovery_retry_budget_terminal_blocker"
)
PAYLOAD_REASON_RUNTIME_RECOVERY_NOT_AUTHORIZED_STAGE_ATTEMPT_BLOCKER = (
    "runtime_recovery_not_authorized_stage_attempt_blocker"
)
PAYLOAD_REASON_CURRENT_OWNER_ROUTE_TYPED_BLOCKER = (
    "current_owner_route_typed_blocker_observed_for_default_executor_dispatch"
)
PAYLOAD_REASON_DELIVERED_PACKAGE_HANDOFF_TYPED_BLOCKER = (
    "delivered_package_handoff_typed_blocker_observed_for_default_executor_dispatch"
)
TASK_KIND = "domain_owner/default-executor-dispatch"
SUPPORTED_SUPERSEDED_ACTION_TYPE = "return_to_ai_reviewer_workflow"
SUPPORTED_SUPERSEDED_WRITER_ACTION_TYPE = "run_quality_repair_batch"
OPL_STAGE_ATTEMPT_ADMISSION_REASON = "opl_stage_attempt_admission_required"
OPL_RUNTIME_OWNER_ROUTE_REASON = "quest_waiting_opl_runtime_owner_route"
RUNTIME_RECOVERY_NOT_AUTHORIZED_REASON = "runtime_recovery_not_authorized"
RUNTIME_RECOVERY_RETRY_BUDGET_EXHAUSTED_REASON = "runtime_recovery_retry_budget_exhausted"
OWNER_AUTHORIZED_PUBLICATION_GATE_REPLAY_REASON = "owner_authorized_publication_gate_replay"
DPCC_PUBLICATION_GATE_REPLAY_AFTER_CURRENT_AI_REVIEWER_RECORD_REASON = (
    "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
)
PUBLICATION_GATE_ROUTE_BACK_WRITE_REQUIRED_REASON = "publication_gate_route_back_write_required"
WRITE_OWNER = "write"
WRITE_ACTION_TYPE = "run_quality_repair_batch"
GATE_CLEARING_OWNER = "gate_clearing_batch"
GATE_CLEARING_ACTION_TYPE = "run_gate_clearing_batch"
READINESS_ACTION_TYPE = "complete_medical_paper_readiness_surface"


def mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def sequence(value: object) -> Sequence[object]:
    return value if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)) else ()


def text(value: object) -> str | None:
    result = str(value or "").strip()
    return result or None


def texts(values: Sequence[object]) -> list[str]:
    return [result for value in values if (result := text(value)) is not None]


def unique(values: Sequence[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        if value not in result:
            result.append(value)
    return result


def authority_boundary() -> dict[str, object]:
    return {
        "owner": "med-autoscience",
        "payload_kind": "refs_only_domain_owned_typed_blocker_payload",
        "opl_records_refs_only": True,
        "writes_mas_truth": False,
        "creates_owner_receipt": False,
        "claims_domain_ready": False,
        "claims_publication_ready": False,
        "claims_production_ready": False,
        "reads_or_writes_artifact_body": False,
        "reads_or_writes_memory_body": False,
    }
