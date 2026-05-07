from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Callable
from urllib.parse import quote

from med_autoscience.controllers import auto_runtime_parking
from med_autoscience.runtime_protocol import quest_state

from ..study_runtime_status import (
    StudyRuntimeAutonomousRuntimeNotice,
    StudyRuntimeAuditStatus,
    StudyRuntimeBindingAction,
    StudyRuntimeQuestStatus,
    StudyRuntimeStatus,
    _LIVE_QUEST_STATUSES,
)
from .runtime_event_relay import (
    materialize_runtime_supervision,
    maybe_emit_runtime_escalation_record,
    post_transition_quest_status,
    record_transition_runtime_event,
    runtime_escalation_evidence_refs,
    runtime_escalation_recommended_actions,
    runtime_escalation_trigger_source,
    runtime_event_outer_loop_input,
    runtime_event_status_snapshot,
)


def clear_stale_platform_repair_redrive_after_pause(
    *,
    quest_root: Path,
    source: str,
) -> dict[str, Any] | None:
    runtime_state_path = Path(quest_root) / ".ds" / "runtime_state.json"
    try:
        runtime_state = json.loads(runtime_state_path.read_text(encoding="utf-8")) or {}
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(runtime_state, dict):
        return None
    if str(runtime_state.get("status") or "").strip().lower() != StudyRuntimeQuestStatus.PAUSED.value:
        return None
    if str(runtime_state.get("active_run_id") or "").strip():
        return None
    if bool(runtime_state.get("worker_running")):
        return None
    if str(runtime_state.get("continuation_reason") or "").strip() != "runtime_platform_repair_redrive":
        return None
    cleared = [
        key
        for key in ("continuation_policy", "continuation_anchor", "continuation_reason", "continuation_updated_at")
        if key in runtime_state
    ]
    for key in cleared:
        runtime_state.pop(key, None)
    runtime_state["last_platform_repair_redrive_clearance"] = {
        "source": source,
        "cleared_keys": cleared,
        "cleared_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }
    runtime_state_path.write_text(
        json.dumps(runtime_state, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {
        "status": "cleared",
        "runtime_state_path": str(runtime_state_path),
        "cleared_keys": cleared,
    }


def record_user_pause_contract_after_pause(
    *,
    quest_root: Path,
    source: str,
) -> dict[str, Any] | None:
    runtime_state_path = Path(quest_root) / ".ds" / "runtime_state.json"
    try:
        runtime_state = json.loads(runtime_state_path.read_text(encoding="utf-8")) or {}
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(runtime_state, dict):
        return None
    status = str(runtime_state.get("status") or "").strip().lower()
    if status not in {
        StudyRuntimeQuestStatus.PAUSED.value,
        StudyRuntimeQuestStatus.STOPPED.value,
    }:
        return None
    if str(runtime_state.get("active_run_id") or "").strip():
        return None
    if bool(runtime_state.get("worker_running")):
        return None
    recorded_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    runtime_state["stop_reason"] = "user_pause"
    runtime_state["continuation_policy"] = "wait_for_user_or_resume"
    runtime_state["continuation_anchor"] = "user_pause"
    runtime_state["continuation_reason"] = "user_pause"
    runtime_state["user_pause_contract"] = {
        "source": source,
        "recorded_at": recorded_at,
        "resume_requires_explicit_wakeup": True,
    }
    runtime_state_path.write_text(
        json.dumps(runtime_state, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {
        "status": "recorded",
        "runtime_state_path": str(runtime_state_path),
        "source": source,
        "recorded_at": recorded_at,
    }


def pause_runtime_state_postcondition(
    *,
    quest_root: Path,
    error: str,
) -> dict[str, Any]:
    runtime_state = quest_state.load_runtime_state(quest_root)
    runtime_status = str(runtime_state.get("status") or "").strip().lower() or None
    active_run_id = str(runtime_state.get("active_run_id") or "").strip() or None
    worker_running = bool(runtime_state.get("worker_running"))
    effective = (
        runtime_status
        in {
            StudyRuntimeQuestStatus.PAUSED.value,
            StudyRuntimeQuestStatus.STOPPED.value,
        }
        and active_run_id is None
        and not worker_running
    )
    return {
        "effective": effective,
        "source": "runtime_state",
        "runtime_state_path": str(Path(quest_root) / ".ds" / "runtime_state.json"),
        "runtime_state_status": runtime_status,
        "active_run_id": active_run_id,
        "worker_running": worker_running,
        "control_transport_error": error,
    }


def pause_failure_result_from_postcondition(postcondition: dict[str, Any]) -> dict[str, Any]:
    effective_status = str(postcondition.get("runtime_state_status") or "").strip() or "paused"
    payload: dict[str, Any] = {
        "ok": False,
        "status": effective_status if postcondition["effective"] else "unavailable",
        "error": postcondition["control_transport_error"],
        "pause_postcondition": dict(postcondition),
    }
    if postcondition["effective"]:
        payload["snapshot"] = {
            "status": effective_status,
            "active_run_id": None,
            "worker_running": False,
        }
    return payload


def has_delivered_human_package_surface(study_root: Path) -> bool:
    manuscript_root = Path(study_root) / "manuscript"
    current_package_root = manuscript_root / "current_package"
    return (
        (manuscript_root / "delivery_manifest.json").exists()
        and (manuscript_root / "current_package.zip").exists()
        and current_package_root.is_dir()
        and (current_package_root / "manuscript.docx").exists()
        and (current_package_root / "paper.pdf").exists()
    )


def record_auto_runtime_parked_projection(status: StudyRuntimeStatus) -> None:
    projection = auto_runtime_parking.build_auto_runtime_parked_projection(status.to_dict())
    status["auto_runtime_parked"] = projection
    for field_name in (
        "parked_state",
        "parked_owner",
        "resource_release_expected",
        "awaiting_explicit_wakeup",
        "auto_execution_complete",
        "reopen_policy",
        "legacy_current_stage",
    ):
        status[field_name] = projection.get(field_name)


def managed_runtime_notice_reason(
    *,
    binding_last_action: StudyRuntimeBindingAction | None,
    strict_live: bool,
) -> str:
    if not strict_live:
        if binding_last_action in {
            StudyRuntimeBindingAction.CREATE_AND_START,
            StudyRuntimeBindingAction.RESUME,
            StudyRuntimeBindingAction.RELAUNCH_STOPPED,
        }:
            return "managed_runtime_recovery_requested"
        return "managed_runtime_degraded"
    if binding_last_action is StudyRuntimeBindingAction.CREATE_AND_START:
        return "managed_runtime_started"
    if binding_last_action is StudyRuntimeBindingAction.RESUME:
        return "managed_runtime_resumed"
    if binding_last_action is StudyRuntimeBindingAction.RELAUNCH_STOPPED:
        return "managed_runtime_relaunched"
    return "detected_existing_live_managed_runtime"


def should_record_autonomous_runtime_notice(
    *,
    status: StudyRuntimeStatus,
    router_module: Callable[[], Any],
) -> bool:
    return (
        router_module()._managed_runtime_backend_for_execution(status.execution) is not None
        and str(status.execution.get("auto_entry") or "").strip() == "on_managed_research_intent"
        and status.quest_exists
        and status.quest_status in _LIVE_QUEST_STATUSES
    )


def runtime_audit_worker_running(payload: dict[str, Any]) -> bool:
    runtime_audit = payload.get("runtime_audit")
    if isinstance(runtime_audit, dict):
        return runtime_audit.get("worker_running") is True
    return payload.get("worker_running") is True


def is_strictly_live_runtime_notice(
    *,
    status: StudyRuntimeStatus,
    active_run_id: str | None,
) -> bool:
    if active_run_id is None:
        return False
    payload = status.extras.get("runtime_liveness_audit")
    if not isinstance(payload, dict):
        return False
    audit_status = str(payload.get("status") or "").strip().lower()
    return audit_status == StudyRuntimeAuditStatus.LIVE.value and runtime_audit_worker_running(payload)


def record_autonomous_runtime_notice_if_required(
    *,
    status: StudyRuntimeStatus,
    runtime_root: Path,
    launch_report_path: Path,
    router_module: Callable[[], Any],
    binding_last_action: StudyRuntimeBindingAction | None = None,
    active_run_id: str | None = None,
) -> None:
    if not should_record_autonomous_runtime_notice(status=status, router_module=router_module):
        return
    router = router_module()
    managed_runtime_backend = router._managed_runtime_backend_for_execution(status.execution)
    if managed_runtime_backend is None:
        return
    browser_url: str | None = None
    monitoring_error: str | None = None
    try:
        browser_url = managed_runtime_backend.resolve_daemon_url(runtime_root=runtime_root)
    except (RuntimeError, OSError, ValueError) as exc:
        monitoring_error = str(exc)
    resolved_active_run_id = str(active_run_id or "").strip() or None
    if resolved_active_run_id is None:
        payload = status.extras.get("runtime_liveness_audit")
        if isinstance(payload, dict):
            resolved_active_run_id = str(payload.get("active_run_id") or "").strip() or None
            if resolved_active_run_id is None:
                runtime_audit = payload.get("runtime_audit")
                if isinstance(runtime_audit, dict):
                    resolved_active_run_id = str(runtime_audit.get("active_run_id") or "").strip() or None
    strict_live = is_strictly_live_runtime_notice(
        status=status,
        active_run_id=resolved_active_run_id,
    )
    if resolved_active_run_id is None and not strict_live:
        return
    quest_status = status.quest_status.value if status.quest_status is not None else "unknown"
    encoded_quest_id = quote(status.quest_id, safe="")
    status.record_autonomous_runtime_notice(
        StudyRuntimeAutonomousRuntimeNotice(
            required=True,
            notice_key=f"quest:{status.quest_id}:{resolved_active_run_id or quest_status}",
            notification_reason=managed_runtime_notice_reason(
                binding_last_action=binding_last_action,
                strict_live=strict_live,
            ),
            quest_id=status.quest_id,
            quest_status=quest_status,
            active_run_id=resolved_active_run_id,
            browser_url=browser_url,
            quest_api_url=f"{browser_url}/api/quests/{encoded_quest_id}" if browser_url is not None else None,
            quest_session_api_url=(
                f"{browser_url}/api/quests/{encoded_quest_id}/session" if browser_url is not None else None
            ),
            monitoring_available=browser_url is not None,
            monitoring_error=monitoring_error,
            launch_report_path=str(launch_report_path),
        )
    )
