from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping


SCHEMA_VERSION = 1

ATTEMPT_STATES = ("unclaimed", "claimed", "running", "retry_queued", "released")

RECOVERABLE_FAILURE_REASONS = (
    "runtime_stalled",
    "transport_failure",
    "controller_gate_blocked",
)

TERMINAL_FAILURE_REASONS = (
    "workspace_boundary_violation",
    "terminal_non_active",
    "retry_budget_exhausted",
)

_REQUIRED_FIELDS = (
    "program_id",
    "study_id",
    "quest_id",
    "work_unit_id",
    "route_id",
    "attempt_state",
    "attempt_count",
    "run_attempt_phase",
    "failure_reason",
    "workspace_root",
    "cwd",
)


def _text(value: object) -> str:
    return str(value or "").strip()


def _int(value: object, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _realpath_text(value: object) -> str | None:
    text = _text(value)
    if not text:
        return None
    return str(Path(text).expanduser().resolve(strict=False))


def _path_inside_root(*, root: str | None, candidate: str | None) -> bool:
    if root is None or candidate is None:
        return False
    try:
        Path(candidate).relative_to(Path(root))
    except ValueError:
        return False
    return True


def build_work_unit_attempt_record(payload: Mapping[str, Any]) -> dict[str, Any]:
    workspace_root = _realpath_text(payload.get("workspace_root"))
    cwd = _realpath_text(payload.get("cwd"))
    failure_reason = _text(payload.get("failure_reason"))
    attempt_state = _text(payload.get("attempt_state")) or "unclaimed"
    attempt_count = _int(payload.get("attempt_count"), default=0)
    retry_budget_remaining = _int(payload.get("retry_budget_remaining"), default=0)
    workspace_boundary_ok = _path_inside_root(root=workspace_root, candidate=cwd)
    effective_failure_reason = (
        failure_reason
        if workspace_boundary_ok
        else "workspace_boundary_violation"
    ) or "none"
    return {
        "surface": "work_unit_runtime_attempt_record",
        "schema_version": SCHEMA_VERSION,
        "program_id": _text(payload.get("program_id")),
        "study_id": _text(payload.get("study_id")),
        "quest_id": _text(payload.get("quest_id")),
        "active_run_id": _text(payload.get("active_run_id")),
        "work_unit_id": _text(payload.get("work_unit_id")),
        "route_id": _text(payload.get("route_id")),
        "attempt_state": attempt_state,
        "attempt_count": attempt_count,
        "run_attempt_phase": _text(payload.get("run_attempt_phase")),
        "failure_reason": effective_failure_reason,
        "backoff_until": _text(payload.get("backoff_until")),
        "retry_budget_remaining": retry_budget_remaining,
        "workspace_root": workspace_root,
        "cwd": cwd,
        "workspace_boundary": {
            "root": workspace_root,
            "cwd": cwd,
            "inside_root": workspace_boundary_ok,
            "fail_closed": not workspace_boundary_ok,
        },
        "retry_policy": {
            "bounded_retry": True,
            "retry_budget_remaining": retry_budget_remaining,
            "recoverable_failure_reasons": list(RECOVERABLE_FAILURE_REASONS),
            "terminal_failure_reasons": list(TERMINAL_FAILURE_REASONS),
            "research_authority": False,
        },
        "authority_boundary": {
            "orchestration_record_only": True,
            "can_create_study_truth": False,
            "can_override_publication_eval": False,
            "requires_controller_decision_for_release": attempt_state == "released",
        },
    }


def validate_work_unit_attempt_record(record: Mapping[str, Any]) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    for field in _REQUIRED_FIELDS:
        if not _text(record.get(field)):
            issues.append({"code": "missing_required_field", "field": field})
    attempt_state = _text(record.get("attempt_state"))
    if attempt_state not in ATTEMPT_STATES:
        issues.append({"code": "invalid_attempt_state", "value": attempt_state})
    if _int(record.get("attempt_count"), default=-1) < 0:
        issues.append({"code": "invalid_attempt_count"})
    workspace_boundary = record.get("workspace_boundary")
    if not isinstance(workspace_boundary, Mapping) or workspace_boundary.get("inside_root") is not True:
        issues.append({"code": "workspace_boundary_violation"})
    retry_policy = record.get("retry_policy")
    if not isinstance(retry_policy, Mapping) or retry_policy.get("research_authority") is not False:
        issues.append({"code": "retry_policy_authority_drift"})
    return {
        "surface": "work_unit_runtime_attempt_record_validation",
        "schema_version": SCHEMA_VERSION,
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
    }


def summarize_work_unit_attempts(records: list[Mapping[str, Any]]) -> dict[str, Any]:
    counts = {state: 0 for state in ATTEMPT_STATES}
    boundary_violations = 0
    retry_queue: list[dict[str, Any]] = []
    for record in records:
        state = _text(record.get("attempt_state"))
        if state in counts:
            counts[state] += 1
        workspace_boundary = record.get("workspace_boundary")
        if not isinstance(workspace_boundary, Mapping) or workspace_boundary.get("inside_root") is not True:
            boundary_violations += 1
        if state == "retry_queued":
            retry_queue.append(
                {
                    "work_unit_id": _text(record.get("work_unit_id")),
                    "attempt_count": _int(record.get("attempt_count")),
                    "failure_reason": _text(record.get("failure_reason")),
                    "backoff_until": _text(record.get("backoff_until")),
                    "retry_budget_remaining": _int(record.get("retry_budget_remaining")),
                }
            )
    return {
        "surface": "work_unit_runtime_attempt_registry_summary",
        "schema_version": SCHEMA_VERSION,
        "attempt_state_counts": counts,
        "boundary_violation_count": boundary_violations,
        "retry_queue": retry_queue,
        "observability_only": True,
        "study_truth_authority": False,
        "publication_authority": False,
    }
