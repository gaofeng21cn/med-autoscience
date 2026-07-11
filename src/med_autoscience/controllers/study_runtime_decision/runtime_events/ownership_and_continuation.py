from __future__ import annotations

import json
from pathlib import Path

from med_autoscience import opl_runtime_contract
from med_autoscience.controllers.study_runtime_decision.publication_and_submission import (
    _SUPERVISOR_ONLY_ALLOWED_ACTIONS,
    _SUPERVISOR_ONLY_FORBIDDEN_ACTIONS,
    _publication_gate_allows_direct_write,
    _publication_gate_requires_live_runtime_reroute,
    _publication_supervisor_current_required_action,
    _publication_supervisor_requests_automated_continuation,
)
from med_autoscience.controllers.study_runtime_types import (
    ProgressProjectionStatus,
    StudyRuntimeAuditStatus,
    StudyRuntimeContinuationState,
    StudyRuntimeExecutionOwnerGuard,
    _LIVE_QUEST_STATUSES,
)


def _publication_gate_allows_live_runtime_write_stage_resume(
    *,
    status: ProgressProjectionStatus,
    publication_gate_report: dict[str, object] | None,
) -> bool:
    if not _publication_gate_allows_post_clear_runtime_continuation(publication_gate_report):
        return False
    try:
        continuation_state = status.continuation_state
    except KeyError:
        return False
    return (
        continuation_state.active_run_id is not None
        and continuation_state.continuation_policy == "auto"
        and continuation_state.continuation_anchor == "decision"
        and continuation_state.continuation_reason is not None
        and continuation_state.continuation_reason.startswith("decision:")
    )


def _publication_gate_allows_post_clear_runtime_continuation(
    publication_gate_report: dict[str, object] | None,
) -> bool:
    if not isinstance(publication_gate_report, dict):
        return False
    if _publication_gate_requires_live_runtime_reroute(publication_gate_report):
        return False
    if bool(publication_gate_report.get("bundle_tasks_downstream_only")):
        return False
    if _publication_supervisor_current_required_action(publication_gate_report) not in {
        "continue_write_stage",
        "continue_bundle_stage",
    }:
        return False
    if str(publication_gate_report.get("status") or "").strip() not in {"", "clear"}:
        return False
    return _publication_supervisor_requests_automated_continuation(
        publication_gate_report,
        require_blocked_status=False,
    )


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
    status: ProgressProjectionStatus,
    quest_root: Path,
) -> None:
    execution = status.execution
    if not opl_runtime_contract.is_opl_hosted_research_execution(execution):
        return
    if not status.quest_exists:
        return
    try:
        runtime_liveness = status.runtime_liveness_audit_record
    except KeyError:
        return
    live_opl_provider_attempt = (
        runtime_liveness.status is StudyRuntimeAuditStatus.LIVE
        and str(runtime_liveness.payload.get("source") or "").strip()
        == "opl_current_control_state_provider_attempt"
    )
    if status.quest_status not in _LIVE_QUEST_STATUSES and not live_opl_provider_attempt:
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


def _load_json_dict(path: Path) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8")) or {}
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _load_json_dict_with_error(path: Path) -> tuple[dict[str, object], str | None]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8")) or {}
    except FileNotFoundError:
        return {}, "missing"
    except OSError:
        return {}, "read_error"
    except json.JSONDecodeError:
        return {}, "invalid_json"
    if not isinstance(payload, dict):
        return {}, "not_json_object"
    return payload, None




def _record_continuation_state_if_present(
    *,
    status: ProgressProjectionStatus,
    quest_root: Path,
    active_run_id: str | None = None,
    live_opl_provider_attempt: bool = False,
) -> None:
    _ = quest_root
    if isinstance(status.extras.get("continuation_state"), dict):
        return
    if not live_opl_provider_attempt or active_run_id is None:
        return
    status.record_continuation_state(
        StudyRuntimeContinuationState(
            quest_status=status.quest_status.value if status.quest_status is not None else None,
            active_run_id=active_run_id,
            continuation_policy=None,
            continuation_anchor=None,
            continuation_reason=None,
            stop_reason=None,
            pending_user_message_count=0,
        )
    )
