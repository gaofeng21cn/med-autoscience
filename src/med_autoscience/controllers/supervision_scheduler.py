from __future__ import annotations

from typing import Any

from med_autoscience.controllers import hermes_supervision, outer_supervision_slo
from med_autoscience.controllers.supervision_scheduler_parts import local_adapter
from med_autoscience.profiles import WorkspaceProfile


SCHEMA_VERSION = 1
SCHEDULER_OWNER = "mas_supervision_scheduler"
HERMES_ADAPTER_ID = "hermes_gateway_cron"
DEFAULT_MANAGER = "local"
DEFAULT_INTERVAL_SECONDS = local_adapter.DEFAULT_INTERVAL_SECONDS
RETIRED_MANAGERS = {"systemd", "cron", "launchd", "docker"}


def read_supervision_status(
    *,
    profile: WorkspaceProfile,
    interval_seconds: int = DEFAULT_INTERVAL_SECONDS,
    manager: str = DEFAULT_MANAGER,
) -> dict[str, Any]:
    manager_key = _normalize_manager(manager)
    if manager_key == "local":
        payload = local_adapter.status(profile=profile, interval_seconds=interval_seconds)
    elif manager_key == "hermes":
        payload = _hermes_status(profile=profile, interval_seconds=interval_seconds)
    elif manager_key in RETIRED_MANAGERS:
        payload = _retired_manager_status(profile=profile, interval_seconds=interval_seconds, manager=manager_key)
    else:
        raise ValueError(f"unsupported supervision scheduler manager: {manager}")
    return _with_scheduler_contract(
        payload,
        profile=profile,
        interval_seconds=interval_seconds,
        adapter_id=str(payload.get("adapter_id") or _adapter_id_for_manager(manager_key)),
        manager=manager_key,
    )


def ensure_supervision(
    *,
    profile: WorkspaceProfile,
    interval_seconds: int = DEFAULT_INTERVAL_SECONDS,
    trigger_now: bool = True,
    manager: str = DEFAULT_MANAGER,
    dry_run: bool = False,
    write_install_proof: bool = False,
) -> dict[str, Any]:
    manager_key = _normalize_manager(manager)
    if manager_key == "local":
        return local_adapter.ensure(
            profile=profile,
            interval_seconds=interval_seconds,
            trigger_now=trigger_now,
            write_install_proof=write_install_proof,
            dry_run=dry_run,
        )
    if manager_key == "hermes":
        payload = hermes_supervision.ensure_supervision(
            profile=profile,
            interval_seconds=interval_seconds,
            trigger_now=trigger_now,
            manager="hermes",
            write_install_proof=write_install_proof,
        )
        return _project_hermes_result(payload)
    if manager_key in RETIRED_MANAGERS:
        payload = hermes_supervision.ensure_supervision(
            profile=profile,
            interval_seconds=interval_seconds,
            trigger_now=False,
            manager=manager_key,
            write_install_proof=False,
        )
        projected = dict(payload)
        projected.update(
            {
                "schema_version": SCHEMA_VERSION,
                "surface_kind": "workspace_runtime_supervision_install_result",
                "scheduler_owner": SCHEDULER_OWNER,
                "adapter_id": _adapter_id_for_manager(manager_key),
                "manager": manager_key,
                "installed": False,
            }
        )
        return projected
    raise ValueError(f"unsupported supervision scheduler manager: {manager}")


def remove_supervision(
    *,
    profile: WorkspaceProfile,
    interval_seconds: int = DEFAULT_INTERVAL_SECONDS,
    manager: str = DEFAULT_MANAGER,
) -> dict[str, Any]:
    manager_key = _normalize_manager(manager)
    if manager_key == "local":
        return local_adapter.remove(profile=profile, interval_seconds=interval_seconds)
    if manager_key == "hermes":
        payload = hermes_supervision.remove_supervision(profile=profile, interval_seconds=interval_seconds)
        return _project_hermes_result(payload)
    if manager_key in RETIRED_MANAGERS:
        before = read_supervision_status(profile=profile, interval_seconds=interval_seconds, manager=manager_key)
        return {
            "schema_version": SCHEMA_VERSION,
            "surface_kind": "workspace_runtime_supervision_remove_result",
            "scheduler_owner": SCHEDULER_OWNER,
            "adapter_id": _adapter_id_for_manager(manager_key),
            "manager": manager_key,
            "action": "retired_manager_fail_closed",
            "status": "retired_fail_closed",
            "before": before,
            "after": before,
            "removed": False,
            "removed_job_ids": [],
        }
    raise ValueError(f"unsupported supervision scheduler manager: {manager}")


def _with_scheduler_contract(
    payload: dict[str, Any],
    *,
    profile: WorkspaceProfile,
    interval_seconds: int,
    adapter_id: str,
    manager: str,
) -> dict[str, Any]:
    result = dict(payload)
    result.setdefault("schema_version", SCHEMA_VERSION)
    result.setdefault("surface_kind", "workspace_runtime_supervision")
    result["scheduler_owner"] = SCHEDULER_OWNER
    result["adapter_id"] = adapter_id
    result["manager"] = manager
    result.setdefault("workspace_key", local_adapter.workspace_key(profile))
    result.setdefault("interval_seconds", interval_seconds)
    result.setdefault("schedule_spec", {"kind": "interval", "interval_seconds": interval_seconds})
    result.setdefault("overlap_policy", "skip_if_running")
    result.setdefault("misfire_policy", "record_missed_and_wait_next")
    result["generated_at"] = str(result.get("generated_at") or local_adapter.utc_now())

    adapter_status = dict(result.get("adapter_status") or {})
    adapter_status.setdefault("adapter_installed", bool(result.get("adapter_installed", result.get("job_exists"))))
    adapter_status.setdefault("adapter_loaded", bool(result.get("adapter_loaded", result.get("loaded"))))
    adapter_status.setdefault("adapter_enabled", bool(result.get("adapter_enabled", result.get("job_enabled"))))
    adapter_status.setdefault("migration_state", result.get("migration_state") or "none")
    result["adapter_status"] = adapter_status
    result.setdefault("adapter_installed", adapter_status["adapter_installed"])
    result.setdefault("adapter_loaded", adapter_status["adapter_loaded"])
    result.setdefault("adapter_enabled", adapter_status["adapter_enabled"])

    result["outer_supervision_slo"] = outer_supervision_slo.build_outer_supervision_slo_projection(
        profile=profile,
        supervision_status=result,
        generated_at=result["generated_at"],
        interval_seconds=interval_seconds,
    )
    return result


def _hermes_status(*, profile: WorkspaceProfile, interval_seconds: int) -> dict[str, Any]:
    payload = dict(hermes_supervision.read_supervision_status(profile=profile, interval_seconds=interval_seconds))
    payload.update(
        {
            "adapter_id": HERMES_ADAPTER_ID,
            "manager": "hermes",
            "workspace_key": _workspace_key_from_hermes(payload) or local_adapter.workspace_key(profile),
            "adapter_installed": bool(payload.get("job_exists")),
            "adapter_loaded": bool(payload.get("loaded")),
            "adapter_enabled": bool(payload.get("job_enabled")),
            "migration_state": payload.get("migration_state") or "none",
            "last_receipt_ref": payload.get("latest_run_session_path"),
        }
    )
    payload.setdefault("owner", HERMES_ADAPTER_ID)
    return payload


def _retired_manager_status(*, profile: WorkspaceProfile, interval_seconds: int, manager: str) -> dict[str, Any]:
    payload = dict(
        hermes_supervision.ensure_supervision(
            profile=profile,
            interval_seconds=interval_seconds,
            trigger_now=False,
            manager=manager,
            write_install_proof=False,
        )
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": "workspace_runtime_supervision",
        "scheduler_owner": SCHEDULER_OWNER,
        "owner": SCHEDULER_OWNER,
        "adapter_id": _adapter_id_for_manager(manager),
        "manager": manager,
        "status": "retired_fail_closed",
        "loaded": False,
        "summary": payload.get("retired_reason") or "retired workspace-local service manager",
        "runtime_contract_ready": True,
        "runtime_contract_issues": ["retired_workspace_local_service_manager"],
        "drift_reasons": ["retired_workspace_local_service_manager"],
        "watch_command": payload.get("command") or [],
        "legacy_service_role": "retired_cleanup_evidence",
    }


def _project_hermes_result(payload: dict[str, Any]) -> dict[str, Any]:
    projected = dict(payload)
    projected.setdefault("schema_version", SCHEMA_VERSION)
    projected["scheduler_owner"] = SCHEDULER_OWNER
    projected["adapter_id"] = HERMES_ADAPTER_ID
    projected["manager"] = "hermes"
    for key in ("before", "after"):
        if isinstance(projected.get(key), dict):
            projected[key] = _project_hermes_status_dict(projected[key])
    return projected


def _project_hermes_status_dict(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        **payload,
        "scheduler_owner": SCHEDULER_OWNER,
        "adapter_id": HERMES_ADAPTER_ID,
        "manager": "hermes",
    }


def _adapter_id_for_manager(manager: str) -> str:
    if manager == "hermes":
        return HERMES_ADAPTER_ID
    if manager == "local":
        return local_adapter.local_backend_id()
    return f"retired_{manager}_scheduler"


def _workspace_key_from_hermes(payload: dict[str, Any]) -> str | None:
    job_name = str(payload.get("job_name") or "")
    prefix = "medautoscience-supervision-"
    if job_name.startswith(prefix):
        return job_name[len(prefix) :]
    return None


def _normalize_manager(manager: str | None) -> str:
    return str(manager or DEFAULT_MANAGER).strip().lower() or DEFAULT_MANAGER


__all__ = [
    "DEFAULT_INTERVAL_SECONDS",
    "SCHEMA_VERSION",
    "SCHEDULER_OWNER",
    "ensure_supervision",
    "read_supervision_status",
    "remove_supervision",
]
