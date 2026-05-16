from __future__ import annotations

from typing import Any

from med_autoscience.controllers import hermes_supervision, outer_supervision_slo
from med_autoscience.controllers.supervision_scheduler_parts import consumer_migration, local_adapter
from med_autoscience.profiles import WorkspaceProfile


SCHEMA_VERSION = 1
SCHEDULER_OWNER = "opl_provider_runtime_manager"
OPL_SCHEDULER_OWNER = SCHEDULER_OWNER
LEGACY_MAS_SCHEDULER_OWNER = "mas_supervision_scheduler"
OPL_ADAPTER_ID = "opl_family_runtime_provider"
HERMES_ADAPTER_ID = "hermes_gateway_cron"
DEFAULT_MANAGER = "opl"
DEFAULT_INTERVAL_SECONDS = local_adapter.DEFAULT_INTERVAL_SECONDS


def read_supervision_status(
    *,
    profile: WorkspaceProfile,
    interval_seconds: int = DEFAULT_INTERVAL_SECONDS,
    manager: str = DEFAULT_MANAGER,
) -> dict[str, Any]:
    manager_key = _normalize_manager(manager)
    if manager_key == "opl":
        payload = _opl_replacement_status(profile=profile, interval_seconds=interval_seconds)
    elif manager_key == "local":
        payload = local_adapter.status(profile=profile, interval_seconds=interval_seconds)
    elif manager_key == "hermes":
        payload = _hermes_status(profile=profile, interval_seconds=interval_seconds)
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
    if manager_key == "opl":
        after = _opl_replacement_status(profile=profile, interval_seconds=interval_seconds)
        return _opl_replacement_action_result(
            profile=profile,
            interval_seconds=interval_seconds,
            action="delegated_to_opl_provider_scheduler",
            trigger_now=trigger_now,
            dry_run=dry_run,
            write_install_proof=write_install_proof,
            after=after,
        )
    if manager_key == "local":
        payload = local_adapter.ensure(
            profile=profile,
            interval_seconds=interval_seconds,
            trigger_now=trigger_now,
            write_install_proof=write_install_proof,
            dry_run=dry_run,
        )
        return _attach_consumer_migration(payload, adapter_id=str(payload.get("adapter_id") or "local"), manager="local")
    if manager_key == "hermes":
        payload = hermes_supervision.ensure_supervision(
            profile=profile,
            interval_seconds=interval_seconds,
            trigger_now=trigger_now,
            manager="hermes",
            write_install_proof=write_install_proof,
        )
        return _attach_consumer_migration(
            _project_hermes_result(payload),
            adapter_id=HERMES_ADAPTER_ID,
            manager="hermes",
        )
    raise ValueError(f"unsupported supervision scheduler manager: {manager}")


def remove_supervision(
    *,
    profile: WorkspaceProfile,
    interval_seconds: int = DEFAULT_INTERVAL_SECONDS,
    manager: str = DEFAULT_MANAGER,
) -> dict[str, Any]:
    manager_key = _normalize_manager(manager)
    if manager_key == "opl":
        after = _opl_replacement_status(profile=profile, interval_seconds=interval_seconds)
        return _opl_replacement_action_result(
            profile=profile,
            interval_seconds=interval_seconds,
            action="delegated_to_opl_provider_scheduler",
            trigger_now=False,
            dry_run=False,
            write_install_proof=False,
            after=after,
            removing=True,
        )
    if manager_key == "local":
        payload = local_adapter.remove(profile=profile, interval_seconds=interval_seconds)
        return _attach_consumer_migration(
            payload,
            adapter_id=str(payload.get("adapter_id") or "local"),
            manager="local",
        )
    if manager_key == "hermes":
        payload = hermes_supervision.remove_supervision(profile=profile, interval_seconds=interval_seconds)
        return _attach_consumer_migration(
            _project_hermes_result(payload),
            adapter_id=HERMES_ADAPTER_ID,
            manager="hermes",
        )
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
    result["scheduler_owner"] = SCHEDULER_OWNER if manager == "opl" else LEGACY_MAS_SCHEDULER_OWNER
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
    return _attach_consumer_migration(result, adapter_id=adapter_id, manager=manager)


def _attach_consumer_migration(payload: dict[str, Any], *, adapter_id: str, manager: str) -> dict[str, Any]:
    return consumer_migration.attach_consumer_migration_contract(
        payload,
        adapter_id=adapter_id,
        manager=manager,
    )


def _opl_replacement_status(*, profile: WorkspaceProfile, interval_seconds: int) -> dict[str, Any]:
    generated_at = local_adapter.utc_now()
    workspace_key = local_adapter.workspace_key(profile)
    legacy_status = local_adapter.status(profile=profile, interval_seconds=interval_seconds)
    legacy_adapter_status = dict(legacy_status.get("adapter_status") or {})
    legacy_adapter_status["migration_state"] = "legacy_diagnostic_only"
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": "workspace_runtime_supervision",
        "generated_at": generated_at,
        "status": "replacement_owner_active",
        "loaded": True,
        "scheduler_owner": OPL_SCHEDULER_OWNER,
        "owner": OPL_SCHEDULER_OWNER,
        "adapter_id": OPL_ADAPTER_ID,
        "manager": "opl",
        "workspace_key": workspace_key,
        "interval_seconds": interval_seconds,
        "schedule_spec": {"kind": "provider_cadence", "interval_seconds": interval_seconds},
        "desired_schedule": f"OPL provider cadence observes MAS paper-progress SLO at {interval_seconds}s",
        "overlap_policy": "provider_stage_attempt_lease",
        "misfire_policy": "provider_records_due_or_skipped_attempt",
        "summary": (
            "OPL provider/runtime manager 持有 scheduler lifecycle、cadence、provider SLO、queue intake "
            "和 attempt ledger；MAS 只投影 paper-progress SLO、owner receipt、typed blocker 与 safe action refs。"
        ),
        "migration_state": "replacement_owner_active",
        "adapter_status": {
            "adapter_installed": True,
            "adapter_loaded": True,
            "adapter_enabled": True,
            "migration_state": "replacement_owner_active",
        },
        "adapter_installed": True,
        "adapter_loaded": True,
        "adapter_enabled": True,
        "job_exists": True,
        "job_enabled": True,
        "job_state": "delegated_to_opl_provider",
        "job_id": f"opl-family-runtime-provider::{workspace_key}",
        "job_name": f"opl-family-runtime-provider::{workspace_key}",
        "watch_command": ["opl", "family-runtime", "tick", "--source", "provider-scheduler", "--hydrate"],
        "tick_sequence": [
            "opl family-runtime provider-slo tick --provider temporal",
            "opl family-runtime intake --domain medautoscience",
            "opl family-runtime tick --source provider-scheduler --hydrate",
        ],
        "latest_run_status": None,
        "latest_run_recorded_at": None,
        "latest_run_summary": None,
        "latest_run_session_path": None,
        "last_receipt_ref": "${OPL_STATE_DIR}/family-runtime/events.jsonl",
        "drift_reasons": [],
        "duplicate_job_ids": [],
        "runtime_contract_ready": True,
        "runtime_contract_issues": [],
        "opl_replacement": _opl_replacement_contract(interval_seconds=interval_seconds),
        "legacy_adapter": {
            "manager": "local",
            "scheduler_owner": LEGACY_MAS_SCHEDULER_OWNER,
            "adapter_id": legacy_status.get("adapter_id"),
            "status": legacy_status.get("status"),
            "summary": legacy_status.get("summary"),
            "adapter_status": legacy_adapter_status,
            "diagnostic_status_command": (
                "uv run python -m med_autoscience.cli runtime-supervision-status "
                "--profile <profile> --manager local"
            ),
            "cleanup_command": (
                "uv run python -m med_autoscience.cli runtime-remove-supervision "
                "--profile <profile> --manager local"
            ),
        },
        "authority_boundary": _authority_boundary(),
    }
    payload["outer_supervision_slo"] = outer_supervision_slo.build_outer_supervision_slo_projection(
        profile=profile,
        supervision_status=payload,
        generated_at=generated_at,
        interval_seconds=interval_seconds,
    )
    return payload


def _opl_replacement_action_result(
    *,
    profile: WorkspaceProfile,
    interval_seconds: int,
    action: str,
    trigger_now: bool,
    dry_run: bool,
    write_install_proof: bool,
    after: dict[str, Any],
    removing: bool = False,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": "workspace_runtime_supervision_replacement_result",
        "action": action,
        "manager": "opl",
        "scheduler_owner": OPL_SCHEDULER_OWNER,
        "adapter_id": OPL_ADAPTER_ID,
        "status": "delegated",
        "dry_run": dry_run,
        "trigger_now": trigger_now,
        "write_install_proof": False,
        "requested_write_install_proof": write_install_proof,
        "removed_job_ids": [],
        "after": after,
        "opl_replacement": after["opl_replacement"],
        "legacy_local_adapter": after["legacy_adapter"],
        "legacy_local_cleanup_command": (
            "uv run python -m med_autoscience.cli runtime-remove-supervision "
            "--profile <profile> --manager local"
        ),
        "note": (
            "MAS no longer installs or removes the default scheduler. OPL provider/runtime manager owns the "
            "scheduler replacement; explicit --manager local remains available only for legacy diagnostic cleanup."
        ),
        "remove_requested": removing,
        "authority_boundary": _authority_boundary(),
    }


def _opl_replacement_contract(*, interval_seconds: int) -> dict[str, Any]:
    return {
        "surface_kind": "mas_opl_scheduler_replacement_projection",
        "contract_ref": "contracts/opl-framework/runtime-manager-contract.json#/family_scheduler_replacement",
        "replacement_owner": OPL_SCHEDULER_OWNER,
        "cadence_owner": "provider_backed_family_runtime",
        "adapter_id": OPL_ADAPTER_ID,
        "provider_slo_tick_command": "opl family-runtime provider-slo tick --provider temporal",
        "domain_intake_command": "opl family-runtime intake --domain medautoscience",
        "family_runtime_tick_command": "opl family-runtime tick --source provider-scheduler --hydrate",
        "runtime_manager_status_command": "opl runtime manager",
        "paper_progress_slo_interval_seconds": interval_seconds,
        "mas_retained_role": [
            "paper_progress_slo_semantics",
            "owner_receipt",
            "typed_blocker",
            "safe_action_refs",
            "no_forbidden_write_evidence",
        ],
        "legacy_scheduler_owner": LEGACY_MAS_SCHEDULER_OWNER,
        "legacy_scheduler_role": "explicit_local_diagnostic_cleanup_only",
    }


def _authority_boundary() -> dict[str, bool]:
    return {
        "can_install_domain_daemon": False,
        "can_write_domain_truth": False,
        "can_write_domain_memory_body": False,
        "can_authorize_publication_quality": False,
        "can_authorize_artifact_export": False,
        "can_execute_reconcile": False,
        "can_own_generic_scheduler": False,
        "can_own_generic_daemon": False,
        "can_own_generic_queue": False,
        "can_own_generic_attempt_ledger": False,
        "can_own_generic_runner": False,
        "can_own_generic_workbench": False,
        "can_project_paper_progress_slo": True,
        "can_return_owner_receipt": True,
        "can_return_typed_blocker": True,
        "can_return_safe_action_refs": True,
    }


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


def _project_hermes_result(payload: dict[str, Any]) -> dict[str, Any]:
    projected = dict(payload)
    projected.setdefault("schema_version", SCHEMA_VERSION)
    projected["scheduler_owner"] = LEGACY_MAS_SCHEDULER_OWNER
    projected["adapter_id"] = HERMES_ADAPTER_ID
    projected["manager"] = "hermes"
    for key in ("before", "after"):
        if isinstance(projected.get(key), dict):
            projected[key] = _project_hermes_status_dict(projected[key])
    return projected


def _project_hermes_status_dict(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        **payload,
        "scheduler_owner": LEGACY_MAS_SCHEDULER_OWNER,
        "adapter_id": HERMES_ADAPTER_ID,
        "manager": "hermes",
    }


def _adapter_id_for_manager(manager: str) -> str:
    if manager == "opl":
        return OPL_ADAPTER_ID
    if manager == "hermes":
        return HERMES_ADAPTER_ID
    if manager == "local":
        return local_adapter.local_backend_id()
    raise ValueError(f"unsupported supervision scheduler manager: {manager}")


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
    "LEGACY_MAS_SCHEDULER_OWNER",
    "OPL_ADAPTER_ID",
    "OPL_SCHEDULER_OWNER",
    "SCHEMA_VERSION",
    "SCHEDULER_OWNER",
    "ensure_supervision",
    "read_supervision_status",
    "remove_supervision",
]
