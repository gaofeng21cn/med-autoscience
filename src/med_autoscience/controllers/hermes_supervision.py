from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
from typing import Any

from med_autoscience.controllers.hermes_supervision_parts.codex_app_automation import (
    codex_app_automation_prompt_check as _shared_codex_app_automation_prompt_check,
)
from med_autoscience.developer_supervisor_mode import current_github_user_gate
from med_autoscience.hermes_runtime_contract import inspect_hermes_runtime_contract
from med_autoscience.profiles import WorkspaceProfile
from opl_harness_shared.hermes_supervision import (
    ensure_script_file as _shared_ensure_script_file,
    job_drift as _shared_job_drift,
    jobs_path as _shared_jobs_path,
    load_jobs as _shared_load_jobs,
    matching_jobs as _shared_matching_jobs,
    remove_empty_parent_dirs as _shared_remove_empty_parent_dirs,
    render_supervision_script as _shared_render_supervision_script,
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
    "[SILENT] Hermes-hosted MedAutoScience supervision tick completed.\n"
    "If the script failed, report the failure briefly and include the failing command."
)
_SILENT_SUCCESS_RESPONSE = "[SILENT] Hermes-hosted MedAutoScience supervision tick completed."
_LEGACY_WATCH_RUNTIME_COMMAND = "run_medautosci watch"
_CURRENT_WATCH_RUNTIME_COMMAND = "run_medautosci runtime watch"
_DEVELOPER_SUPERVISOR_GITHUB_LOGIN = "gaofeng21cn"
_DEVELOPER_SUPERVISOR_SAFE_ACTION_ARGS = (
    "--apply-safe-actions",
    "--developer-supervisor-mode",
    "developer_apply_safe",
)
_DEVELOPER_SUPERVISOR_SAFE_ACTION_TEXT = " ".join(_DEVELOPER_SUPERVISOR_SAFE_ACTION_ARGS)


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


def _workspace_watch_runtime_entry_path(profile: WorkspaceProfile) -> Path:
    return profile.workspace_root / "ops" / "medautoscience" / "bin" / "watch-runtime"


def _workspace_supervisor_scan_entry_path(profile: WorkspaceProfile) -> Path:
    return profile.workspace_root / "ops" / "medautoscience" / "bin" / "supervisor-scan"


def _workspace_supervisor_consume_entry_path(profile: WorkspaceProfile) -> Path:
    return profile.workspace_root / "ops" / "medautoscience" / "bin" / "supervisor-consume"


def _workspace_supervisor_execute_dispatch_entry_path(profile: WorkspaceProfile) -> Path:
    return profile.workspace_root / "ops" / "medautoscience" / "bin" / "supervisor-execute-dispatch"


def _codex_app_automation_path() -> Path:
    return Path.home() / ".codex" / "automations" / "mas" / "automation.toml"


def _portable_supervisor_templates(profile: WorkspaceProfile) -> dict[str, Path]:
    templates_root = profile.workspace_root / "ops" / "medautoscience" / "supervisor"
    return {
        "systemd_service": templates_root / "systemd" / "medautoscience-supervisor-scan.service",
        "systemd_timer": templates_root / "systemd" / "medautoscience-supervisor-scan.timer",
        "cron": templates_root / "cron" / "supervisor-scan.cron",
        "launchd_instructions": templates_root / "launchd" / "README.md",
    }


def _github_user_login_check() -> dict[str, Any]:
    gate = current_github_user_gate(expected_login=_DEVELOPER_SUPERVISOR_GITHUB_LOGIN)
    return {
        "command": ["gh", "api", "user", "--jq", ".login"],
        "status": "ok" if gate.get("allowed") else "failed",
        "login": gate.get("login"),
        "expected_login": gate.get("expected_login"),
        "matches_expected": gate.get("allowed") is True,
        "details": gate.get("reason"),
        "gate": gate,
    }


def _codex_app_automation_prompt_check(*, automation_path: Path | None = None) -> dict[str, Any]:
    return _shared_codex_app_automation_prompt_check(automation_path or _codex_app_automation_path())


def _developer_supervisor_mode_projection(*, profile: WorkspaceProfile, manager: str, interval_seconds: int) -> dict[str, Any]:
    github_user = _github_user_login_check()
    codex_app_prompt = _codex_app_automation_prompt_check()
    unsupported_manager = manager == "docker"
    developer_mode_enabled = bool(github_user.get("matches_expected")) and not unsupported_manager
    supervisor_scan = _workspace_supervisor_scan_entry_path(profile)
    supervisor_consume = _workspace_supervisor_consume_entry_path(profile)
    supervisor_execute_dispatch = _workspace_supervisor_execute_dispatch_entry_path(profile)
    if manager == "codex_app":
        scheduler_owner = "codex_app_compat"
    elif unsupported_manager:
        scheduler_owner = "external_container_scheduler"
    else:
        scheduler_owner = f"{manager}_scheduler"
    expected_artifacts = [
        str(profile.workspace_root / "artifacts" / "supervision" / "hourly" / "latest.json"),
        str(profile.workspace_root / "artifacts" / "supervision" / "consumer" / "latest.json"),
        str(profile.workspace_root / "artifacts" / "supervision" / "consumer" / "history.jsonl"),
        str(profile.studies_root / "<study_id>" / "artifacts" / "supervision" / "consumer" / "default_executor_execution" / "latest.json"),
    ]
    status_check_commands = [
        [str(supervisor_scan), *_DEVELOPER_SUPERVISOR_SAFE_ACTION_ARGS],
        [str(supervisor_consume), "--mode", "developer_apply_safe", "--apply"],
        [str(supervisor_execute_dispatch), "--mode", "developer_apply_safe", "--apply"],
        [str(supervisor_scan), "--status"],
    ]
    return {
        "mode": "developer_apply_safe" if developer_mode_enabled else "external_observe",
        "requested_mode": "developer_apply_safe",
        "mode_source": "unsupported_container_scheduler" if unsupported_manager else "github_user_gate",
        "developer_mode_enabled": developer_mode_enabled,
        "safe_actions_enabled": developer_mode_enabled,
        "repo_level_repair_authority": developer_mode_enabled,
        "scheduler_owner": scheduler_owner,
        "github_user": github_user,
        "github_user_gate": github_user.get("gate"),
        "codex_app_automation_prompt": codex_app_prompt,
        "codex_app_heartbeat_required": False,
        "install_proof": {
            "manager": manager,
            "status": "unsupported_container_scheduler" if unsupported_manager else (
                "ready" if developer_mode_enabled else "developer_mode_disabled"
            ),
            "status_check_commands": status_check_commands,
            "expected_artifacts": expected_artifacts,
            "freshness": {
                "projection": "portable_scheduler_tick_refreshes_supervisor_scan_artifacts",
                "interval_seconds": interval_seconds,
                "max_expected_artifact_age_seconds": interval_seconds * 2,
                "codex_app_heartbeat_required": False,
            },
        },
    }


def _install_proof_path(profile: WorkspaceProfile) -> Path:
    return profile.workspace_root / "artifacts" / "supervision" / "install_proof" / "latest.json"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _portable_install_proof(
    *,
    profile: WorkspaceProfile,
    manager: str,
    scheduler_owner: str,
    install_commands: list[str],
    status_check_commands: list[list[str]],
    expected_artifacts: list[str],
    freshness: dict[str, Any],
    safe_action_mode: str,
    github_gate: dict[str, Any] | None,
    host_service_claim: str,
    status: str,
) -> dict[str, Any]:
    proof_path = _install_proof_path(profile)
    generated_at = _utc_now()
    return {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": "portable_scheduler_install_proof",
        "generated_at": generated_at,
        "manager": manager,
        "scheduler_owner": scheduler_owner,
        "install_commands": install_commands,
        "status_check_commands": status_check_commands,
        "expected_artifacts": expected_artifacts,
        "artifact_path": str(proof_path),
        "last_scan_time": generated_at,
        "freshness": freshness,
        "safe_action_mode": safe_action_mode,
        "github_gate": dict(github_gate or {}),
        "host_service_claim": host_service_claim,
        "status": status,
        "installed": False,
    }


def _portable_supervisor_instruction(
    *,
    profile: WorkspaceProfile,
    manager: str,
    interval_seconds: int,
    write_install_proof: bool = False,
) -> dict[str, Any]:
    supervisor_scan = _workspace_supervisor_scan_entry_path(profile)
    supervisor_consume = _workspace_supervisor_consume_entry_path(profile)
    supervisor_execute_dispatch = _workspace_supervisor_execute_dispatch_entry_path(profile)
    templates = _portable_supervisor_templates(profile)
    manager_key = manager.strip().lower()
    user_systemd_root = Path.home() / ".config" / "systemd" / "user"
    result_templates: dict[str, str]
    install_commands: list[str]
    if manager_key == "systemd":
        service_template = templates["systemd_service"]
        timer_template = templates["systemd_timer"]
        result_templates = {
            "service": str(service_template),
            "timer": str(timer_template),
        }
        install_commands = [
            f"mkdir -p {user_systemd_root}",
            f"cp {service_template} {user_systemd_root / service_template.name}",
            f"cp {timer_template} {user_systemd_root / timer_template.name}",
            "systemctl --user daemon-reload",
            f"systemctl --user enable --now {timer_template.name}",
        ]
    elif manager_key == "cron":
        cron_template = templates["cron"]
        result_templates = {"crontab": str(cron_template)}
        install_commands = [
            f"(crontab -l 2>/dev/null; cat {cron_template}) | crontab -",
        ]
    elif manager_key == "docker":
        result_templates = {}
        install_commands = [
            "Run this MAS CLI entry from the container image or scheduler owned by OPL, Hermes, or the deployment platform: "
            f"<container-entry> medautosci runtime supervisor-scan --profile <profile> {_DEVELOPER_SUPERVISOR_SAFE_ACTION_TEXT}"
        ]
    elif manager_key == "launchd":
        result_templates = {"instructions": str(templates["launchd_instructions"])}
        install_commands = [
            f"{profile.workspace_root}/ops/medautoscience/bin/install-watch-runtime-service --manager launchd",
        ]
    else:
        result_templates = {}
        install_commands = []
    developer_supervisor_mode = _developer_supervisor_mode_projection(
        profile=profile,
        manager=manager_key,
        interval_seconds=interval_seconds,
    )
    host_service_claim = "not_installed_by_mas"
    install_proof = _portable_install_proof(
        profile=profile,
        manager=manager_key,
        scheduler_owner=developer_supervisor_mode["scheduler_owner"],
        install_commands=install_commands,
        status_check_commands=developer_supervisor_mode["install_proof"]["status_check_commands"],
        expected_artifacts=developer_supervisor_mode["install_proof"]["expected_artifacts"],
        freshness=developer_supervisor_mode["install_proof"]["freshness"],
        safe_action_mode=developer_supervisor_mode["mode"],
        github_gate=developer_supervisor_mode["github_user_gate"],
        host_service_claim=host_service_claim,
        status=str(developer_supervisor_mode["install_proof"]["status"]),
    )
    if write_install_proof:
        _write_json(_install_proof_path(profile), install_proof)
    return {
        "action": "portable_scheduler_instruction",
        "manager": manager_key,
        "mode": developer_supervisor_mode["mode"],
        "requested_mode": developer_supervisor_mode["requested_mode"],
        "mode_source": developer_supervisor_mode["mode_source"],
        "developer_mode_enabled": developer_supervisor_mode["developer_mode_enabled"],
        "safe_actions_enabled": developer_supervisor_mode["safe_actions_enabled"],
        "repo_level_repair_authority": developer_supervisor_mode["repo_level_repair_authority"],
        "scheduler_owner": developer_supervisor_mode["scheduler_owner"],
        "github_user": developer_supervisor_mode["github_user"],
        "github_user_gate": developer_supervisor_mode["github_user_gate"],
        "installed": False,
        "profile": str(profile.workspace_root / "ops" / "medautoscience" / "profiles"),
        "interval_seconds": interval_seconds,
        "supervisor_scan_entry": {
            "path": str(supervisor_scan),
            "exists": supervisor_scan.is_file(),
            "executable": supervisor_scan.is_file() and os.access(supervisor_scan, os.X_OK),
        },
        "supervisor_consume_entry": {
            "path": str(supervisor_consume),
            "exists": supervisor_consume.is_file(),
            "executable": supervisor_consume.is_file() and os.access(supervisor_consume, os.X_OK),
        },
        "supervisor_execute_dispatch_entry": {
            "path": str(supervisor_execute_dispatch),
            "exists": supervisor_execute_dispatch.is_file(),
            "executable": supervisor_execute_dispatch.is_file() and os.access(supervisor_execute_dispatch, os.X_OK),
        },
        "command": [
            str(supervisor_scan),
            *_DEVELOPER_SUPERVISOR_SAFE_ACTION_ARGS,
        ],
        "templates": result_templates,
        "install_commands": install_commands,
        "install_proof": install_proof,
        "install_proof_path": str(_install_proof_path(profile)) if write_install_proof else None,
        "status_check_commands": install_proof["status_check_commands"],
        "expected_artifacts": install_proof["expected_artifacts"],
        "freshness": install_proof["freshness"],
        "developer_supervisor_mode": developer_supervisor_mode,
        "codex_app_automation_prompt": developer_supervisor_mode["codex_app_automation_prompt"],
        "codex_app_heartbeat_required": False,
        "host_service_claim": host_service_claim,
        "container_policy": "MAS does not own a Docker image or Kubernetes CronJob; external OPL, Hermes, or deployment schedulers may call the MAS CLI entry.",
    }


def _repair_legacy_workspace_watch_runtime_entry(profile: WorkspaceProfile) -> dict[str, Any]:
    path = _workspace_watch_runtime_entry_path(profile)
    result: dict[str, Any] = {
        "path": str(path),
        "repaired": False,
        "reason": None,
    }
    if not path.is_file():
        result["reason"] = "missing"
        return result
    try:
        content = path.read_text(encoding="utf-8")
    except OSError:
        result["reason"] = "unreadable"
        return result
    if _CURRENT_WATCH_RUNTIME_COMMAND in content:
        result["reason"] = "current"
        return result
    if _LEGACY_WATCH_RUNTIME_COMMAND not in content:
        result["reason"] = "unknown_shape"
        return result
    updated = content.replace(_LEGACY_WATCH_RUNTIME_COMMAND, _CURRENT_WATCH_RUNTIME_COMMAND, 1)
    try:
        path.write_text(updated, encoding="utf-8")
    except OSError:
        result["reason"] = "write_failed"
        return result
    result["repaired"] = True
    result["reason"] = "legacy_flat_watch_command"
    return result


def _render_supervision_script(profile: WorkspaceProfile, *, interval_seconds: int) -> str:
    return _shared_render_supervision_script(_watch_runtime_command(profile, interval_seconds=interval_seconds))


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
    if status == "legacy_only" and (legacy_loaded or legacy_exists):
        return "检测到 legacy workspace-local runtime supervision service 仍在运行，当前 canonical Hermes supervision 尚未接管。"
    if status == "owner_drift" and (legacy_loaded or legacy_exists):
        return "canonical Hermes supervision 与 legacy workspace-local runtime supervision service 同时存在，当前需要迁移到单一 Hermes owner。"
    return _shared_status_summary(
        status=status,
        gateway_service_loaded=gateway_service_loaded,
        job_present=job_present,
        drift_reasons=drift_reasons,
    )


def _ensure_script_file(profile: WorkspaceProfile, *, interval_seconds: int) -> Path:
    return _shared_ensure_script_file(
        hermes_home_root=profile.hermes_home_root,
        script_relpath=_script_relpath(profile),
        command=_watch_runtime_command(profile, interval_seconds=interval_seconds),
    )


def _remove_empty_parent_dirs(path: Path, *, stop_at: Path) -> None:
    _shared_remove_empty_parent_dirs(path, stop_at=stop_at)


def _latest_job_session_path(profile: WorkspaceProfile, *, job_id: str | None) -> Path | None:
    resolved_job_id = str(job_id or "").strip()
    if not resolved_job_id:
        return None
    sessions_root = profile.hermes_home_root / "sessions"
    candidates = sorted(sessions_root.glob(f"session_cron_{resolved_job_id}_*.json"))
    if not candidates:
        return None
    return candidates[-1]


def _latest_job_run(profile: WorkspaceProfile, *, job_id: str | None) -> dict[str, Any] | None:
    session_path = _latest_job_session_path(profile, job_id=job_id)
    if session_path is None:
        return None
    try:
        payload = json.loads(session_path.read_text(encoding="utf-8")) or {}
    except (OSError, json.JSONDecodeError):
        return {
            "status": "invalid",
            "summary": "latest cron session payload is unreadable",
            "session_path": str(session_path),
            "recorded_at": None,
        }
    if not isinstance(payload, dict):
        return {
            "status": "invalid",
            "summary": "latest cron session payload is invalid",
            "session_path": str(session_path),
            "recorded_at": None,
        }
    messages = payload.get("messages")
    latest_content: str | None = None
    if isinstance(messages, list):
        for item in reversed(messages):
            if not isinstance(item, dict):
                continue
            if str(item.get("role") or "").strip() != "assistant":
                continue
            candidate = item.get("content")
            if isinstance(candidate, str) and candidate.strip():
                latest_content = candidate.strip()
                break
    status = "unknown"
    summary = None
    if latest_content == _SILENT_SUCCESS_RESPONSE:
        status = "success"
        summary = "latest Hermes supervision tick completed"
    elif latest_content is not None and "data-collection script failed" in latest_content.lower():
        status = "failed"
        summary = latest_content.splitlines()[0].strip()
    elif latest_content is not None:
        status = "reported"
        summary = latest_content.splitlines()[0].strip()
    return {
        "status": status,
        "summary": summary,
        "session_path": str(session_path),
        "recorded_at": str(payload.get("last_updated") or payload.get("session_start") or "").strip() or None,
    }


def _legacy_launchd_label(profile: WorkspaceProfile) -> str:
    return f"ai.medautoscience.{_slugify(profile.name)}.watch-runtime"


def _legacy_launchd_service_file(profile: WorkspaceProfile) -> Path:
    return Path.home() / "Library" / "LaunchAgents" / f"{_legacy_launchd_label(profile)}.plist"


def _legacy_systemd_service_name(profile: WorkspaceProfile) -> str:
    return f"medautoscience-watch-runtime-{_slugify(profile.name)}"


def _legacy_systemd_service_file(profile: WorkspaceProfile) -> Path:
    return Path.home() / ".config" / "systemd" / "user" / f"{_legacy_systemd_service_name(profile)}.service"


def _read_legacy_service_status(profile: WorkspaceProfile) -> dict[str, Any]:
    system = platform.system()
    if system == "Darwin":
        label = _legacy_launchd_label(profile)
        service_file = _legacy_launchd_service_file(profile)
        completed = subprocess.run(
            ["launchctl", "print", f"gui/{os.getuid()}/{label}"],
            capture_output=True,
            text=True,
            check=False,
        )
        output = completed.stdout.strip() or completed.stderr.strip()
        return {
            "manager": "launchd",
            "service_label": label,
            "service_file": str(service_file),
            "service_exists": service_file.exists(),
            "loaded": completed.returncode == 0,
            "details": output or None,
        }
    if system == "Linux":
        service_name = _legacy_systemd_service_name(profile)
        service_file = _legacy_systemd_service_file(profile)
        completed = subprocess.run(
            ["systemctl", "--user", "is-active", f"{service_name}.service"],
            capture_output=True,
            text=True,
            check=False,
        )
        output = completed.stdout.strip() or completed.stderr.strip()
        return {
            "manager": "systemd",
            "service_label": service_name,
            "service_file": str(service_file),
            "service_exists": service_file.exists(),
            "loaded": completed.returncode == 0 and output == "active",
            "details": output or None,
        }
    return {
        "manager": system.lower() or "unknown",
        "service_label": None,
        "service_file": None,
        "service_exists": False,
        "loaded": False,
        "details": None,
    }


def _remove_legacy_service(profile: WorkspaceProfile) -> dict[str, Any]:
    status = _read_legacy_service_status(profile)
    manager = str(status.get("manager") or "")
    service_label = str(status.get("service_label") or "").strip()
    service_file_text = str(status.get("service_file") or "").strip()
    service_file = Path(service_file_text) if service_file_text else None
    command_outputs: list[dict[str, Any]] = []
    unloaded = False
    removed_service_file = False

    if manager == "launchd" and service_label:
        command = ["launchctl", "bootout", f"gui/{os.getuid()}/{service_label}"]
        exit_code, output = _run_command(command=command)
        command_outputs.append({"command": command, "exit_code": exit_code, "output": output})
        unloaded = exit_code == 0
    elif manager == "systemd" and service_label:
        command = ["systemctl", "--user", "disable", "--now", f"{service_label}.service"]
        exit_code, output = _run_command(command=command)
        command_outputs.append({"command": command, "exit_code": exit_code, "output": output})
        unloaded = exit_code == 0

    if service_file is not None and service_file.exists():
        service_file.unlink()
        removed_service_file = True

    if manager == "systemd" and removed_service_file:
        command = ["systemctl", "--user", "daemon-reload"]
        exit_code, output = _run_command(command=command)
        command_outputs.append({"command": command, "exit_code": exit_code, "output": output})

    return {
        "before": status,
        "unloaded": unloaded,
        "removed_service_file": removed_service_file,
        "command_outputs": command_outputs,
    }


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
        drift_reasons = [*drift_reasons, "legacy_service_loaded"]
    elif legacy_exists:
        drift_reasons = [*drift_reasons, "legacy_service_present"]
    if job_present and gateway_service_loaded and job_enabled and job_state == "scheduled" and script_exists:
        status = "execution_failed" if latest_run_failed else "loaded"
    elif job_present:
        status = "not_loaded"
    elif legacy_loaded or legacy_exists:
        status = "legacy_only"
    else:
        status = "not_installed"
    if status in {"loaded", "execution_failed", "not_loaded"} and (legacy_loaded or legacy_exists):
        status = "owner_drift"
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
            "Hermes-hosted runtime supervision 已注册，但最近一次 cron 执行失败，workspace 级监管当前未真正在线。"
        )
        if latest_run_summary:
            summary = f"{summary} {latest_run_summary}"
    return {
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
    }


def ensure_supervision(
    *,
    profile: WorkspaceProfile,
    interval_seconds: int = DEFAULT_INTERVAL_SECONDS,
    trigger_now: bool = True,
    manager: str = "hermes",
    write_install_proof: bool = False,
) -> dict[str, Any]:
    if manager != "hermes":
        return _portable_supervisor_instruction(
            profile=profile,
            manager=manager,
            interval_seconds=interval_seconds,
            write_install_proof=write_install_proof,
        )
    _ensure_script_file(profile, interval_seconds=interval_seconds)
    watch_runtime_repair = _repair_legacy_workspace_watch_runtime_entry(profile)
    before = read_supervision_status(profile=profile, interval_seconds=interval_seconds)
    missing_prereqs = [
        issue
        for issue in before["runtime_contract_issues"]
        if issue
        not in {
            "external_runtime.gateway_service_not_loaded",
            "external_runtime.provider_not_configured",
        }
    ]
    if missing_prereqs:
        return {
            "action": "blocked",
            "blocking_issues": missing_prereqs,
            "before": before,
        }

    primary_job_id = before["job_id"]
    action = "noop"
    command_outputs: list[dict[str, Any]] = []
    if bool(watch_runtime_repair.get("repaired")) and action == "noop":
        action = "repaired_watch_runtime_entry"
    if primary_job_id is None:
        create_command = _hermes_cli_command(
            profile,
            "cron",
            "create",
            _desired_schedule(interval_seconds),
            _SILENT_PROMPT,
            "--name",
            _job_name(profile),
            "--deliver",
            "local",
            "--script",
            _script_relpath(profile),
        )
        exit_code, output = _run_command(command=create_command)
        command_outputs.append({"command": create_command, "exit_code": exit_code, "output": output})
        if exit_code != 0:
            return {
                "action": "create_failed",
                "before": before,
                "command_outputs": command_outputs,
            }
        primary_job_id = read_supervision_status(profile=profile, interval_seconds=interval_seconds).get("job_id")
        action = "created"
    else:
        if before["drift_reasons"]:
            edit_command = _hermes_cli_command(
                profile,
                "cron",
                "edit",
                primary_job_id,
                "--schedule",
                _desired_schedule(interval_seconds),
                "--prompt",
                _SILENT_PROMPT,
                "--name",
                _job_name(profile),
                "--deliver",
                "local",
                "--script",
                _script_relpath(profile),
            )
            exit_code, output = _run_command(command=edit_command)
            command_outputs.append({"command": edit_command, "exit_code": exit_code, "output": output})
            if exit_code != 0:
                return {
                    "action": "edit_failed",
                    "before": before,
                    "command_outputs": command_outputs,
                }
            action = "updated"
        if before["job_exists"] and (before["job_state"] != "scheduled" or not before["job_enabled"]):
            resume_command = _hermes_cli_command(profile, "cron", "resume", primary_job_id)
            exit_code, output = _run_command(command=resume_command)
            command_outputs.append({"command": resume_command, "exit_code": exit_code, "output": output})
            if exit_code != 0:
                return {
                    "action": "resume_failed",
                    "before": before,
                    "command_outputs": command_outputs,
                }
            action = "resumed" if action == "noop" else action

    removed_duplicate_job_ids: list[str] = []
    for duplicate_job_id in before["duplicate_job_ids"]:
        remove_command = _hermes_cli_command(profile, "cron", "remove", duplicate_job_id)
        exit_code, output = _run_command(command=remove_command)
        command_outputs.append({"command": remove_command, "exit_code": exit_code, "output": output})
        if exit_code == 0:
            removed_duplicate_job_ids.append(duplicate_job_id)

    if trigger_now and primary_job_id:
        run_command = _hermes_cli_command(profile, "cron", "run", primary_job_id)
        exit_code, output = _run_command(command=run_command)
        command_outputs.append({"command": run_command, "exit_code": exit_code, "output": output})
        if exit_code == 0 and action == "noop":
            action = "scheduled_now"

    legacy_removal = None
    if bool((before.get("legacy_service") or {}).get("service_exists")):
        legacy_removal = _remove_legacy_service(profile)
        if action == "noop" and (
            legacy_removal["unloaded"]
            or legacy_removal["removed_service_file"]
        ):
            action = "migrated_legacy_service"

    after = read_supervision_status(profile=profile, interval_seconds=interval_seconds)
    return {
        "action": action,
        "before": before,
        "after": after,
        "watch_runtime_repair": watch_runtime_repair,
        "removed_duplicate_job_ids": removed_duplicate_job_ids,
        "legacy_removal": legacy_removal,
        "command_outputs": command_outputs,
        "script_path": str(_script_path(profile)),
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
    if bool((before.get("legacy_service") or {}).get("service_exists")):
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
