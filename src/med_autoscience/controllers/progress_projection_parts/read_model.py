from __future__ import annotations

from typing import Any


def resolved_active_run_id(*, extras: dict[str, Any]) -> str | None:
    runtime_liveness_audit = extras.get("runtime_liveness_audit")
    if isinstance(runtime_liveness_audit, dict):
        runtime_audit = runtime_liveness_audit.get("runtime_audit")
        runtime_audit = runtime_audit if isinstance(runtime_audit, dict) else {}
        liveness_status = str(
            runtime_liveness_audit.get("status")
            or runtime_audit.get("status")
            or ""
        ).strip()
        worker_running = (
            runtime_audit.get("worker_running")
            if isinstance(runtime_audit.get("worker_running"), bool)
            else runtime_liveness_audit.get("worker_running")
        )
        if liveness_status and (liveness_status != "live" or worker_running is not True):
            return None
    for payload in (
        runtime_liveness_audit,
        runtime_liveness_audit.get("runtime_audit") if isinstance(runtime_liveness_audit, dict) else None,
        extras.get("autonomous_runtime_notice"),
        extras.get("execution_owner_guard"),
    ):
        if isinstance(payload, dict):
            active_run_id = str(payload.get("active_run_id") or "").strip()
            if active_run_id:
                return active_run_id
    return None


def status_to_dict(status: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": status.schema_version,
        "study_id": status.study_id,
        "study_root": status.study_root,
        "entry_mode": status.entry_mode,
        "execution": status.execution,
        "quest_id": status.quest_id,
        "quest_root": status.quest_root,
        "quest_exists": status.quest_exists,
        "quest_status": status.quest_status.value if status.quest_status is not None else None,
        "runtime_binding_path": status.runtime_binding_path,
        "runtime_binding_exists": status.runtime_binding_exists,
        "workspace_contracts": status.workspace_contracts,
        "startup_data_readiness": status.startup_data_readiness,
        "startup_boundary_gate": status.startup_boundary_gate,
        "runtime_reentry_gate": status.runtime_reentry_gate,
        "study_completion_contract": status.study_completion_state.to_dict(),
        "controller_first_policy_summary": status.controller_first_policy_summary,
        "automation_ready_summary": status.automation_ready_summary,
    }
    if status.decision is not None:
        payload["decision"] = status.decision.value
    if status.reason is not None:
        payload["reason"] = status.reason.value
    payload.update(status.extras)
    if "active_run_id" not in payload:
        active_run_id = resolved_active_run_id(extras=status.extras)
        if active_run_id is not None:
            payload["active_run_id"] = active_run_id
    return payload
