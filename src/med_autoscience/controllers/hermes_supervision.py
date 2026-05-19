from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from pathlib import Path
import re
import subprocess
from typing import Any

from med_autoscience.controllers.hermes_supervision_parts.codex_app_automation import (
    canonical_codex_app_automation_prompt as _shared_canonical_codex_app_automation_prompt,
    codex_app_automation_prompt_check as _shared_codex_app_automation_prompt_check,
)
from med_autoscience.controllers.hermes_supervision_parts.legacy_services import (
    launchd_label as _shared_launchd_label,
    launchd_service_file as _shared_launchd_service_file,
    legacy_service_status as _shared_legacy_service_status,
    remove_legacy_service as _shared_remove_legacy_service,
    systemd_service_file as _shared_systemd_service_file,
    systemd_service_name as _shared_systemd_service_name,
)
from med_autoscience.controllers.hermes_supervision_parts.job_runs import (
    latest_job_run as _shared_latest_job_run,
)
from med_autoscience.hermes_runtime_contract import inspect_hermes_runtime_contract
from med_autoscience.profiles import WorkspaceProfile
from opl_harness_shared.hermes_supervision import (
    job_drift as _shared_job_drift,
    jobs_path as _shared_jobs_path,
    load_jobs as _shared_load_jobs,
    matching_jobs as _shared_matching_jobs,
    remove_empty_parent_dirs as _shared_remove_empty_parent_dirs,
    require_interval_minutes as _shared_require_interval_minutes,
    resolve_job_script_path as _shared_resolve_job_script_path,
    schedule_matches as _shared_schedule_matches,
    script_path as _shared_script_path,
    select_primary_job as _shared_select_primary_job,
    status_summary as _shared_status_summary,
)


SCHEMA_VERSION = 1
DEFAULT_INTERVAL_SECONDS = 5 * 60
_SILENT_PROMPT = (
    "A pre-run supervision script has already executed the MedAutoScience workspace supervision tick.\n"
    "If the script output shows returncode=0, respond exactly with:\n"
    "[SILENT] MAS scheduler local adapter MedAutoScience supervision tick completed.\n"
    "If the script failed, report the failure briefly and include the failing command."
)
_SILENT_SUCCESS_RESPONSE = "[SILENT] MAS scheduler local adapter MedAutoScience supervision tick completed."
def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _slugify(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-").lower()
    return normalized or "workspace"


def _workspace_key(profile: WorkspaceProfile) -> str:
    digest = hashlib.sha256(str(profile.workspace_root).encode("utf-8")).hexdigest()[:8]
    return f"{_slugify(profile.name)}-{digest}"


def _require_interval_minutes(interval_seconds: int) -> int:
    return _shared_require_interval_minutes(interval_seconds)


def _job_name(profile: WorkspaceProfile) -> str:
    return f"medautoscience-supervision-{_workspace_key(profile)}"


def _script_relpath(profile: WorkspaceProfile) -> str:
    return f"med-autoscience/{_workspace_key(profile)}/watch_runtime_tick.py"


def _script_path(profile: WorkspaceProfile) -> Path:
    return _shared_script_path(hermes_home_root=profile.hermes_home_root, script_relpath=_script_relpath(profile))


def _jobs_path(profile: WorkspaceProfile) -> Path:
    return _shared_jobs_path(hermes_home_root=profile.hermes_home_root)


def _desired_schedule(interval_seconds: int) -> str:
    return f"every {_require_interval_minutes(interval_seconds)}m"


def _watch_runtime_command(profile: WorkspaceProfile, *, interval_seconds: int) -> list[str]:
    return [
        str(profile.workspace_root / "ops" / "medautoscience" / "bin" / "watch-runtime"),
        "--interval-seconds",
        str(interval_seconds),
        "--max-ticks",
        "1",
    ]


def _codex_app_automation_path() -> Path:
    return Path.home() / ".codex" / "automations" / "mas" / "automation.toml"


def _codex_app_automation_prompt_check(*, automation_path: Path | None = None) -> dict[str, Any]:
    return _shared_codex_app_automation_prompt_check(automation_path or _codex_app_automation_path())


def _canonical_codex_app_automation_prompt() -> str:
    return _shared_canonical_codex_app_automation_prompt()


def _run_command(*, command: list[str]) -> tuple[int, str]:
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )
    output = completed.stdout.strip() or completed.stderr.strip()
    return completed.returncode, output


def _hermes_cli_command(profile: WorkspaceProfile, *args: str) -> list[str]:
    if profile.hermes_agent_repo_root is None:
        raise ValueError("profile.hermes_agent_repo_root is not configured")
    launcher = (profile.hermes_agent_repo_root / "hermes").resolve()
    runtime_contract = inspect_hermes_runtime_contract(
        hermes_agent_repo_root=profile.hermes_agent_repo_root,
        hermes_home_root=profile.hermes_home_root,
    )
    managed_python = str(runtime_contract.get("managed_python_path") or "").strip()
    if managed_python:
        return [managed_python, str(launcher), *args]
    return [str(launcher), *args]


def _load_jobs(profile: WorkspaceProfile) -> list[dict[str, Any]]:
    return _shared_load_jobs(hermes_home_root=profile.hermes_home_root)


def _resolve_job_script_path(profile: WorkspaceProfile, script_value: object) -> Path | None:
    return _shared_resolve_job_script_path(hermes_home_root=profile.hermes_home_root, script_value=script_value)


def _matching_jobs(profile: WorkspaceProfile) -> list[dict[str, Any]]:
    return _shared_matching_jobs(
        hermes_home_root=profile.hermes_home_root,
        job_name=_job_name(profile),
        script_relpath=_script_relpath(profile),
    )


def _select_primary_job(jobs: Iterable[dict[str, Any]]) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    return _shared_select_primary_job(jobs)


def _schedule_matches(job: dict[str, Any], *, interval_seconds: int) -> bool:
    return _shared_schedule_matches(job, interval_seconds=interval_seconds)


def _job_drift(
    *,
    profile: WorkspaceProfile,
    job: dict[str, Any] | None,
    interval_seconds: int,
) -> list[str]:
    return _shared_job_drift(
        hermes_home_root=profile.hermes_home_root,
        job=job,
        job_name=_job_name(profile),
        silent_prompt=_SILENT_PROMPT,
        script_relpath=_script_relpath(profile),
        interval_seconds=interval_seconds,
    )


def _status_summary(
    *,
    status: str,
    gateway_service_loaded: bool,
    job_present: bool,
    drift_reasons: list[str],
    legacy_service: dict[str, Any] | None = None,
) -> str:
    legacy_service = dict(legacy_service or {})
    legacy_loaded = bool(legacy_service.get("loaded"))
    legacy_exists = bool(legacy_service.get("service_exists"))
    if status == "retired_legacy_service_present" and (legacy_loaded or legacy_exists):
        return (
            "检测到已退役的 workspace-local runtime supervision service。当前 canonical owner 是 "
            "OPL provider/runtime manager replacement；local scheduler 只保留 tombstone/provenance refs，"
            "不再暴露 cleanup command。"
        )
    summary = _shared_status_summary(
        status=status,
        gateway_service_loaded=gateway_service_loaded,
        job_present=job_present,
        drift_reasons=drift_reasons,
    )
    return summary.replace(
        "Hermes-hosted runtime supervision",
        "MAS scheduler local adapter runtime supervision",
    )


def _remove_empty_parent_dirs(path: Path, *, stop_at: Path) -> None:
    _shared_remove_empty_parent_dirs(path, stop_at=stop_at)


def _latest_job_run(profile: WorkspaceProfile, *, job_id: str | None) -> dict[str, Any] | None:
    return _shared_latest_job_run(
        profile,
        job_id=job_id,
        silent_success_response=_SILENT_SUCCESS_RESPONSE,
    )


def _legacy_launchd_label(profile: WorkspaceProfile) -> str:
    return _shared_launchd_label(profile=profile, slug=_slugify(profile.name))


def _legacy_launchd_service_file(profile: WorkspaceProfile) -> Path:
    return _shared_launchd_service_file(profile=profile, slug=_slugify(profile.name))


def _legacy_systemd_service_name(profile: WorkspaceProfile) -> str:
    return _shared_systemd_service_name(profile=profile, slug=_slugify(profile.name))


def _legacy_systemd_service_file(profile: WorkspaceProfile) -> Path:
    return _shared_systemd_service_file(profile=profile, slug=_slugify(profile.name))


def _read_legacy_service_status(profile: WorkspaceProfile) -> dict[str, Any]:
    return _shared_legacy_service_status(profile=profile, slug=_slugify(profile.name))


def _remove_legacy_service(profile: WorkspaceProfile) -> dict[str, Any]:
    return _shared_remove_legacy_service(profile=profile, slug=_slugify(profile.name), run_command=_run_command)


def read_supervision_status(
    *,
    profile: WorkspaceProfile,
    interval_seconds: int = DEFAULT_INTERVAL_SECONDS,
) -> dict[str, Any]:
    _require_interval_minutes(interval_seconds)
    runtime_contract = inspect_hermes_runtime_contract(
        hermes_agent_repo_root=profile.hermes_agent_repo_root,
        hermes_home_root=profile.hermes_home_root,
    )
    matching_jobs = _matching_jobs(profile)
    primary_job, duplicate_jobs = _select_primary_job(matching_jobs)
    script_path = _script_path(profile)
    drift_reasons = _job_drift(profile=profile, job=primary_job, interval_seconds=interval_seconds)
    legacy_service = _read_legacy_service_status(profile)
    gateway_service_loaded = bool(runtime_contract.get("gateway_service_loaded"))
    job_present = primary_job is not None
    script_exists = script_path.is_file()
    job_enabled = bool((primary_job or {}).get("enabled", False))
    job_state = str((primary_job or {}).get("state") or "").strip() or None
    job_id = str((primary_job or {}).get("id") or "").strip() or None
    latest_run = _latest_job_run(profile, job_id=job_id)
    latest_run_failed = str((latest_run or {}).get("status") or "").strip() == "failed"
    legacy_loaded = bool(legacy_service.get("loaded"))
    legacy_exists = bool(legacy_service.get("service_exists"))
    if legacy_loaded:
        drift_reasons = [*drift_reasons, "retired_legacy_service_loaded"]
    elif legacy_exists:
        drift_reasons = [*drift_reasons, "retired_legacy_service_present"]
    if legacy_loaded or legacy_exists:
        status = "retired_legacy_service_present"
    elif job_present and gateway_service_loaded and job_enabled and job_state == "scheduled" and script_exists:
        status = "execution_failed" if latest_run_failed else "loaded"
    elif job_present:
        status = "not_loaded"
    else:
        status = "not_installed"
    summary = _status_summary(
        status=status,
        gateway_service_loaded=gateway_service_loaded,
        job_present=job_present,
        drift_reasons=drift_reasons,
        legacy_service=legacy_service,
    )
    if status == "execution_failed":
        latest_run_summary = str((latest_run or {}).get("summary") or "").strip()
        summary = (
            "MAS scheduler local adapter runtime supervision 已注册，但最近一次 cron 执行失败，workspace 级监管当前未真正在线。"
        )
        if latest_run_summary:
            summary = f"{summary} {latest_run_summary}"
    payload = {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": "workspace_runtime_supervision",
        "owner": "hermes_gateway_cron",
        "generated_at": _utc_now(),
        "manager": runtime_contract.get("gateway_service_manager"),
        "status": status,
        "loaded": status == "loaded",
        "summary": summary,
        "gateway_service_label": runtime_contract.get("gateway_service_label"),
        "gateway_service_loaded": gateway_service_loaded,
        "jobs_store_path": str(_jobs_path(profile)),
        "job_exists": job_present,
        "job_id": job_id,
        "job_name": str((primary_job or {}).get("name") or "").strip() or None,
        "job_state": job_state,
        "job_enabled": job_enabled,
        "job_next_run_at": str((primary_job or {}).get("next_run_at") or "").strip() or None,
        "job_schedule_display": str((primary_job or {}).get("schedule_display") or "").strip() or None,
        "job_script": str((primary_job or {}).get("script") or "").strip() or None,
        "script_path": str(script_path),
        "script_exists": script_exists,
        "watch_command": _watch_runtime_command(profile, interval_seconds=interval_seconds),
        "desired_schedule": _desired_schedule(interval_seconds),
        "desired_prompt": _SILENT_PROMPT,
        "drift_reasons": drift_reasons,
        "latest_run_status": str((latest_run or {}).get("status") or "").strip() or None,
        "latest_run_recorded_at": str((latest_run or {}).get("recorded_at") or "").strip() or None,
        "latest_run_summary": str((latest_run or {}).get("summary") or "").strip() or None,
        "latest_run_session_path": str((latest_run or {}).get("session_path") or "").strip() or None,
        "duplicate_job_ids": [
            str(job.get("id") or "").strip()
            for job in duplicate_jobs
            if str(job.get("id") or "").strip()
        ],
        "runtime_contract_ready": bool(runtime_contract.get("ready")),
        "runtime_contract_issues": list(runtime_contract.get("issues") or []),
        "legacy_service": legacy_service,
        "legacy_service_role": "retired_cleanup_evidence",
        "retired_legacy_cleanup_required": legacy_loaded or legacy_exists,
    }
    from med_autoscience.controllers import outer_supervision_slo

    payload["outer_supervision_slo"] = outer_supervision_slo.build_outer_supervision_slo_projection(
        profile=profile,
        supervision_status=payload,
        generated_at=payload["generated_at"],
        interval_seconds=interval_seconds,
    )
    return payload


def ensure_supervision(
    *,
    profile: WorkspaceProfile,
    interval_seconds: int = DEFAULT_INTERVAL_SECONDS,
    trigger_now: bool = True,
    manager: str = "hermes",
    write_install_proof: bool = False,
) -> dict[str, Any]:
    if manager != "hermes":
        raise ValueError(f"unsupported Hermes supervision adapter manager: {manager}")
    before = read_supervision_status(profile=profile, interval_seconds=interval_seconds)
    return {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": "workspace_runtime_supervision_legacy_tombstone",
        "status": "retired_ensure_path",
        "action": "retired_ensure_path",
        "manager": "hermes",
        "scheduler_owner": "mas_legacy_domain_slo_diagnostic",
        "adapter_id": "hermes_gateway_cron",
        "generated_at": _utc_now(),
        "workspace_key": _workspace_key(profile),
        "interval_seconds": interval_seconds,
        "before": before,
        "after": before,
        "trigger_now": bool(trigger_now),
        "write_install_proof": False,
        "requested_write_install_proof": bool(write_install_proof),
        "install_allowed": False,
        "status_allowed": True,
        "remove_allowed": True,
        "trigger_allowed": False,
        "write_tick_script_allowed": False,
        "removed_duplicate_job_ids": [],
        "legacy_removal": None,
        "command_outputs": [],
        "script_path": str(_script_path(profile)),
        "summary": (
            "Hermes gateway cron ensure/create/refresh/trigger path is retired. "
            "Use OPL scheduler replacement for active cadence; this adapter only reads or removes "
            "pre-existing legacy jobs."
        ),
    }


def remove_supervision(
    *,
    profile: WorkspaceProfile,
    interval_seconds: int = DEFAULT_INTERVAL_SECONDS,
) -> dict[str, Any]:
    before = read_supervision_status(profile=profile, interval_seconds=interval_seconds)
    removed_job_ids: list[str] = []
    command_outputs: list[dict[str, Any]] = []
    for job_id in [before["job_id"], *before["duplicate_job_ids"]]:
        if not job_id:
            continue
        remove_command = _hermes_cli_command(profile, "cron", "remove", job_id)
        exit_code, output = _run_command(command=remove_command)
        command_outputs.append({"command": remove_command, "exit_code": exit_code, "output": output})
        if exit_code == 0:
            removed_job_ids.append(job_id)

    script_path = _script_path(profile)
    script_removed = False
    if script_path.exists():
        script_path.unlink()
        script_removed = True
        _remove_empty_parent_dirs(script_path, stop_at=profile.hermes_home_root / "scripts")

    legacy_removal = None
    before_legacy_service = dict(before.get("legacy_service") or {})
    if bool(before_legacy_service.get("service_exists")) or bool(before_legacy_service.get("loaded")):
        legacy_removal = _remove_legacy_service(profile)

    after = read_supervision_status(profile=profile, interval_seconds=interval_seconds)
    return {
        "before": before,
        "after": after,
        "removed_job_ids": removed_job_ids,
        "script_removed": script_removed,
        "legacy_removal": legacy_removal,
        "command_outputs": command_outputs,
    }
