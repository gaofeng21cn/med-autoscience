from __future__ import annotations

from typing import Any, Mapping


SCHEMA_VERSION = 1

REQUIRED_DURABILITY_GUARANTEES = (
    "pause_resume_from_restore_point",
    "event_sourced_replay",
    "idempotent_controller_tick",
    "human_gate_as_durable_decision",
    "retry_budget_before_escalation",
)

RUNTIME_TRUTH_SURFACES = (
    "progress_projection",
    "domain_health_diagnostic",
    "artifacts/runtime/health/latest.json",
    "runtime_escalation_record.json",
)

STUDY_TRUTH_SURFACES = (
    "study_charter",
    "paper/evidence_ledger.json",
    "paper/review_ledger.json",
    "artifacts/publication_eval/latest.json",
    "artifacts/controller_decisions/latest.json",
)

STATE_MACHINE: tuple[dict[str, str], ...] = (
    {"state_id": "queued", "resume_action": "claim_next_work_unit"},
    {"state_id": "running", "resume_action": "continue_active_work_unit"},
    {"state_id": "awaiting_artifact_delta", "resume_action": "wait_or_replay_gate"},
    {"state_id": "route_back", "resume_action": "dispatch_same_line_repair"},
    {"state_id": "awaiting_human_gate", "resume_action": "wait_for_durable_decision"},
    {"state_id": "recovering", "resume_action": "recover_runtime"},
    {"state_id": "completed", "resume_action": "materialize_completion"},
    {"state_id": "escalated", "resume_action": "surface_platform_repair"},
)

EVENT_REPLAY_CONTRACT: dict[str, Any] = {
    "event_log_required": True,
    "event_order_key": "recorded_at",
    "dedupe_key": "event_id",
    "replay_starts_from": "restore_point_id",
    "replay_must_reconstruct": [
        "active_state",
        "active_run_id",
        "work_unit_id",
        "retry_budget_remaining",
        "pending_human_gate_decision_id",
    ],
    "event_classes": [
        "runtime_state_observed",
        "worker_heartbeat",
        "artifact_delta_observed",
        "route_back_decision",
        "human_gate_decision",
        "recovery_attempt",
        "retry_budget_decremented",
    ],
}

IDEMPOTENT_TICK_CONTRACT: dict[str, Any] = {
    "idempotency_key_fields": [
        "program_id",
        "study_id",
        "quest_id",
        "active_run_id",
        "work_unit_id",
        "restore_point_id",
        "tick_sequence",
    ],
    "duplicate_tick_policy": "return_existing_decision_ref",
    "allowed_write_surfaces": [
        "progress_projection",
        "domain_health_diagnostic",
        "runtime_escalation_record.json",
        "artifacts/controller_decisions/latest.json",
    ],
    "forbidden_tick_effects": [
        "create_study_truth",
        "override_study_truth",
        "override_quality_truth",
        "declare_publication_ready",
    ],
}

HUMAN_GATE_CONTRACT: dict[str, Any] = {
    "decision_is_required": True,
    "decision_surface": "artifacts/controller_decisions/latest.json",
    "decision_fields": [
        "decision_id",
        "decided_by",
        "decided_at",
        "decision",
        "scope",
        "evidence_refs",
        "resume_action",
    ],
    "pending_state": "awaiting_human_gate",
    "resume_requires_decision_id": True,
}

RETRY_BUDGET_CONTRACT: dict[str, Any] = {
    "budget_scope": "controller_route_work_unit",
    "attempt_count_field": "attempt_count",
    "retry_budget_field": "retry_budget_remaining",
    "budget_decrement_event": "retry_budget_decremented",
    "exhaustion_state": "escalated",
    "exhaustion_requires_surface": "runtime_escalation_record.json",
    "exhaustion_allowed_next_actions": [
        "surface_platform_repair",
        "request_human_gate_decision",
        "request_route_redesign",
    ],
}


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _text(value: object) -> str:
    return str(value or "").strip()


def build_durable_workflow_contract() -> dict[str, Any]:
    return {
        "surface": "durable_workflow_contract",
        "schema_version": SCHEMA_VERSION,
        "workflow_owner": "MedAutoScience Runtime OS",
        "runtime_health_can_override_quality_truth": False,
        "runtime_health_can_override_study_truth": False,
        "study_truth_can_be_mutated_by_read_model": False,
        "runtime_health_role": "observability_and_recovery_only",
        "quality_truth_owner": "Quality OS",
        "study_truth_owner": "StudyTruthKernel",
        "durability_guarantees": list(REQUIRED_DURABILITY_GUARANTEES),
        "state_machine": [dict(state) for state in STATE_MACHINE],
        "runtime_truth_surfaces": list(RUNTIME_TRUTH_SURFACES),
        "study_truth_surfaces": list(STUDY_TRUTH_SURFACES),
        "event_replay": dict(EVENT_REPLAY_CONTRACT),
        "idempotent_tick": dict(IDEMPOTENT_TICK_CONTRACT),
        "human_gate": dict(HUMAN_GATE_CONTRACT),
        "retry_budget": dict(RETRY_BUDGET_CONTRACT),
        "forbidden_shortcuts": [
            "status_read_mutates_truth",
            "runtime_health_overrides_study_truth",
            "runtime_health_overrides_publication_quality",
            "retry_without_budget",
            "human_gate_without_durable_decision",
            "event_replay_without_dedupe_key",
        ],
    }


def validate_durable_workflow_contract(contract: Mapping[str, Any]) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    if contract.get("runtime_health_can_override_quality_truth") is not False:
        issues.append({"code": "runtime_health_overrides_quality_truth"})
    if contract.get("runtime_health_can_override_study_truth") is not False:
        issues.append({"code": "runtime_health_overrides_study_truth"})
    if contract.get("study_truth_can_be_mutated_by_read_model") is not False:
        issues.append({"code": "read_model_mutates_study_truth"})
    guarantees = {str(item) for item in _list(contract.get("durability_guarantees"))}
    for guarantee in REQUIRED_DURABILITY_GUARANTEES:
        if guarantee not in guarantees:
            issues.append({"code": "missing_durability_guarantee", "guarantee": guarantee})
    for state in _list(contract.get("state_machine")):
        if not isinstance(state, Mapping):
            issues.append({"code": "invalid_state"})
            continue
        if not _text(state.get("state_id")):
            issues.append({"code": "state_missing_id"})
        if not _text(state.get("resume_action")):
            issues.append({"code": "state_missing_resume_action", "state_id": _text(state.get("state_id"))})
    event_replay = contract.get("event_replay")
    if not isinstance(event_replay, Mapping):
        issues.append({"code": "missing_event_replay_contract"})
    else:
        if event_replay.get("event_log_required") is not True:
            issues.append({"code": "event_replay_requires_event_log"})
        if not _text(event_replay.get("dedupe_key")):
            issues.append({"code": "event_replay_missing_dedupe_key"})
        if not _text(event_replay.get("replay_starts_from")):
            issues.append({"code": "event_replay_missing_restore_point"})
    idempotent_tick = contract.get("idempotent_tick")
    if not isinstance(idempotent_tick, Mapping):
        issues.append({"code": "missing_idempotent_tick_contract"})
    else:
        key_fields = {str(item) for item in _list(idempotent_tick.get("idempotency_key_fields"))}
        for field in ("program_id", "study_id", "quest_id", "active_run_id", "tick_sequence"):
            if field not in key_fields:
                issues.append({"code": "idempotent_tick_missing_key_field", "field": field})
    human_gate = contract.get("human_gate")
    if not isinstance(human_gate, Mapping):
        issues.append({"code": "missing_human_gate_contract"})
    else:
        if human_gate.get("decision_is_required") is not True:
            issues.append({"code": "human_gate_missing_durable_decision"})
        if _text(human_gate.get("decision_surface")) != "artifacts/controller_decisions/latest.json":
            issues.append({"code": "human_gate_wrong_decision_surface"})
    retry_budget = contract.get("retry_budget")
    if not isinstance(retry_budget, Mapping):
        issues.append({"code": "missing_retry_budget_contract"})
    else:
        if not _text(retry_budget.get("retry_budget_field")):
            issues.append({"code": "retry_budget_missing_budget_field"})
        if not _text(retry_budget.get("exhaustion_requires_surface")):
            issues.append({"code": "retry_budget_missing_exhaustion_surface"})
    return {
        "surface": "durable_workflow_contract_validation",
        "schema_version": SCHEMA_VERSION,
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
    }
