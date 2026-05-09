from __future__ import annotations

from typing import Any

from med_autoscience.controllers import hermes_supervision, outer_supervision_slo
from med_autoscience.controllers.supervision_scheduler_parts import local_adapter
from med_autoscience.profiles import WorkspaceProfile


SCHEDULER_OWNER = "mas_supervision_scheduler"
HERMES_ADAPTER_ID = "hermes_gateway_cron"
DEFAULT_MANAGER = "local"
RETIRED_MANAGERS = {"systemd", "cron", "launchd", "docker"}


def _with_scheduler_contract(
    payload: dict[str, Any],
    *,
    profile: WorkspaceProfile,
    interval_seconds: int,
    adapter_id: str,
    manager: str,
) -> dict[str, Any]:
    result = dict(payload)
    result["scheduler_owner"] = SCHEDULER_OWNER
    result["adapter_id"] = adapter_id
    result["manager"] = manager
    slo_status = dict(result)
    slo_status["owner"] = SCHEDULER_OWNER
    result.setdefault("workspace_key", local_adapter.workspace_key(profile))
    result.setdefault("interval_seconds", interval_seconds)
    adapter_status = dict(result.get("adapter_status") or {})
    adapter_status.setdefault("adapter_installed", bool(result.get("job_exists")))
    adapter_status.setdefault("adapter_loaded", bool(result.get("loaded")))
    adapter_status.setdefault("adapter_enabled", bool(result.get("job_enabled")))
    adapter_status.setdefault("migration_state", result.get("migration_state") or "none")
    result["adapter_status"] = adapter_status
    generated_at = str(result.get("generated_at") or local_adapter.utc_now())
    result["generated_at"] = generated_at
    result["outer_supervision_slo"] = outer_supervision_slo.build_outer_supervision_slo_projection(
        profile=profile,
        supervision_status=slo_status,
        generated_at=generated_at,
        interval_seconds=interval_seconds,
    )
    return result


def read_supervision_status(
    *,
    profile: WorkspaceProfile,
    interval_seconds: int = hermes_supervision.DEFAULT_INTERVAL_SECONDS,
    manager: str = DEFAULT_MANAGER,
) -> dict[str, Any]:
    if manager == "local":
        return local_adapter.status(profile=profile, interval_seconds=interval_seconds)
    if manager == "hermes":
        return _with_scheduler_contract(
            dict(hermes_supervision.read_supervision_status(profile=profile, interval_seconds=interval_seconds)),
            profile=profile,
            interval_seconds=interval_seconds,
            adapter_id=HERMES_ADAPTER_ID,
            manager="hermes",
        )
    if manager in RETIRED_MANAGERS:
        return _with_scheduler_contract(
            dict(
                hermes_supervision.ensure_supervision(
                    profile=profile,
                    interval_seconds=interval_seconds,
                    trigger_now=False,
                    manager=manager,
                )
            ),
            profile=profile,
            interval_seconds=interval_seconds,
            adapter_id=f"retired_{manager}",
            manager=manager,
        )
    raise ValueError(f"unsupported supervision scheduler manager: {manager}")


def ensure_supervision(
    *,
    profile: WorkspaceProfile,
    interval_seconds: int = hermes_supervision.DEFAULT_INTERVAL_SECONDS,
    trigger_now: bool = True,
    manager: str = DEFAULT_MANAGER,
    dry_run: bool = False,
    write_install_proof: bool = False,
) -> dict[str, Any]:
    if manager == "local":
        return local_adapter.ensure(
            profile=profile,
            interval_seconds=interval_seconds,
            trigger_now=trigger_now,
            write_install_proof=write_install_proof,
            dry_run=dry_run,
        )
    if manager == "hermes" or manager in RETIRED_MANAGERS:
        payload = hermes_supervision.ensure_supervision(
            profile=profile,
            interval_seconds=interval_seconds,
            trigger_now=trigger_now,
            manager=manager,
            write_install_proof=write_install_proof,
        )
        return _with_scheduler_contract(
            dict(payload),
            profile=profile,
            interval_seconds=interval_seconds,
            adapter_id=HERMES_ADAPTER_ID if manager == "hermes" else f"retired_{manager}",
            manager=manager,
        )
    raise ValueError(f"unsupported supervision scheduler manager: {manager}")


def remove_supervision(
    *,
    profile: WorkspaceProfile,
    interval_seconds: int = hermes_supervision.DEFAULT_INTERVAL_SECONDS,
    manager: str = DEFAULT_MANAGER,
) -> dict[str, Any]:
    if manager == "local":
        return local_adapter.remove(profile=profile, interval_seconds=interval_seconds)
    if manager == "hermes":
        return _with_scheduler_contract(
            dict(hermes_supervision.remove_supervision(profile=profile, interval_seconds=interval_seconds)),
            profile=profile,
            interval_seconds=interval_seconds,
            adapter_id=HERMES_ADAPTER_ID,
            manager=manager,
        )
    if manager in RETIRED_MANAGERS:
        before = read_supervision_status(profile=profile, interval_seconds=interval_seconds, manager=manager)
        return {
            "schema_version": 1,
            "surface_kind": "workspace_runtime_supervision_remove_result",
            "scheduler_owner": SCHEDULER_OWNER,
            "adapter_id": f"retired_{manager}",
            "manager": manager,
            "action": "retired_manager_fail_closed",
            "status": "retired",
            "before": before,
            "after": before,
            "removed_job_ids": [],
        }
    raise ValueError(f"unsupported supervision scheduler manager: {manager}")
