from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import plistlib
import re
import subprocess
from typing import Any

from med_autoscience.controllers.supervision_scheduler_parts import consumer_migration
from med_autoscience.profiles import WorkspaceProfile


SCHEMA_VERSION = 1
SCHEDULER_OWNER = "mas_supervision_scheduler"
DEFAULT_INTERVAL_SECONDS = 5 * 60
RETIRED_INSTALL_REASON = "mas_local_scheduler_install_retired_use_opl_replacement"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def workspace_key(profile: WorkspaceProfile) -> str:
    digest = hashlib.sha256(str(profile.workspace_root).encode("utf-8")).hexdigest()[:8]
    return f"{_slugify(profile.name)}-{digest}"


def local_backend_id() -> str:
    system = platform.system().lower()
    if system == "darwin":
        return "local_launchd"
    if system == "linux":
        return "local_systemd_user" if _systemd_user_available() else "local_cron"
    return "local_no_persistent_scheduler"


def status(*, profile: WorkspaceProfile, interval_seconds: int = DEFAULT_INTERVAL_SECONDS) -> dict[str, Any]:
    backend = local_backend_id()
    if backend == "local_launchd":
        return _launchd_status(profile=profile, interval_seconds=interval_seconds)
    return _non_persistent_status(profile=profile, interval_seconds=interval_seconds, adapter_id=backend)


def ensure(
    *,
    profile: WorkspaceProfile,
    interval_seconds: int = DEFAULT_INTERVAL_SECONDS,
    trigger_now: bool = True,
    write_install_proof: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    backend = local_backend_id()
    before = status(profile=profile, interval_seconds=interval_seconds)
    command_outputs: list[dict[str, Any]] = []
    after = status(profile=profile, interval_seconds=interval_seconds)
    return {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": "workspace_runtime_supervision_install_result",
        "action": "retired_cleanup_only",
        "status": "blocked",
        "manager": "local",
        "scheduler_owner": SCHEDULER_OWNER,
        "adapter_id": backend,
        "active_path_role": consumer_migration.LOCAL_DIAGNOSTIC_PATH_ROLE,
        "before": before,
        "after": after,
        "script_path": str(_tick_script_path(profile)),
        "launch_agent_path": str(_launch_agent_path(profile)),
        "install_proof_path": None,
        "command_outputs": command_outputs,
        "dry_run": True,
        "write_install_proof": False,
        "trigger_now": trigger_now,
        "requested_dry_run": dry_run,
        "requested_write_install_proof": write_install_proof,
        "reason": RETIRED_INSTALL_REASON,
        "cleanup_command": "runtime-remove-supervision --profile <profile> --manager local",
        "replacement_command": "runtime-ensure-supervision --profile <profile> --manager opl",
        "note": (
            "MAS local scheduler installation is retired. Use OPL provider replacement for scheduler "
            "lifecycle and --manager local only to inspect or remove legacy LaunchAgent artifacts."
        ),
    }


def remove(*, profile: WorkspaceProfile, interval_seconds: int = DEFAULT_INTERVAL_SECONDS) -> dict[str, Any]:
    before = status(profile=profile, interval_seconds=interval_seconds)
    command_outputs: list[dict[str, Any]] = []
    plist_path = _launch_agent_path(profile)
    label = _launchd_label(profile)
    if plist_path.exists():
        command_outputs.extend(_unload_launch_agent(plist_path=plist_path, label=label))
        try:
            plist_path.unlink()
        except OSError as exc:
            command_outputs.append({"command": ["unlink", str(plist_path)], "exit_code": 1, "output": str(exc)})
    script_path = _tick_script_path(profile)
    script_removed = False
    if script_path.exists():
        script_path.unlink()
        script_removed = True
    after = status(profile=profile, interval_seconds=interval_seconds)
    return {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": "workspace_runtime_supervision_remove_result",
        "manager": "local",
        "scheduler_owner": SCHEDULER_OWNER,
        "adapter_id": before.get("adapter_id") or local_backend_id(),
        "active_path_role": consumer_migration.LOCAL_DIAGNOSTIC_PATH_ROLE,
        "before": before,
        "after": after,
        "launch_agent_removed": not plist_path.exists(),
        "script_removed": script_removed,
        "removed_job_ids": [_job_id(profile)] if before.get("job_exists") else [],
        "command_outputs": command_outputs,
    }


def _launchd_status(*, profile: WorkspaceProfile, interval_seconds: int) -> dict[str, Any]:
    script = _tick_script_path(profile)
    plist_path = _launch_agent_path(profile)
    latest_receipt = _read_json(_latest_receipt_path(profile))
    drift_reasons: list[str] = []
    installed = plist_path.exists()
    script_exists = script.exists()
    if installed:
        drift_reasons.append("legacy_launch_agent_present")
    if script_exists:
        drift_reasons.append("legacy_tick_script_present")
    launchd_probe = (
        _launch_agent_probe(label=_launchd_label(profile))
        if installed
        else {"loaded": False, "exit_code": None, "output": ""}
    )
    legacy_artifact_present = installed or script_exists
    status_value = "retired_legacy_cleanup_required" if legacy_artifact_present else "not_installed"
    summary = (
        "检测到已退役的 MAS local scheduler 旧生成物；请运行 --manager local remove 清理。"
        if legacy_artifact_present
        else "MAS local scheduler 旧生成物不存在；local 仅保留 status/remove cleanup diagnostic。"
    )
    payload = _base_status(
        profile=profile,
        adapter_id="local_launchd",
        interval_seconds=interval_seconds,
        status=status_value,
        loaded=False,
        summary=summary,
        script_path=script,
        latest_receipt=latest_receipt,
        drift_reasons=drift_reasons,
    )
    legacy_service = {
        "launch_agent_label": _launchd_label(profile),
        "launch_agent_path": str(plist_path),
        "launch_agent_exists": installed,
        "tick_script_path": str(script),
        "tick_script_exists": script_exists,
        "launch_agent_probe": launchd_probe,
        "launch_agent_plist": _legacy_launch_agent_projection(_read_plist(plist_path)) if installed else {},
    }
    payload.update(
        {
            "launch_agent_label": _launchd_label(profile),
            "launch_agent_path": str(plist_path),
            "launch_agent_probe": launchd_probe,
            "adapter_status": {
                "adapter_installed": legacy_artifact_present,
                "adapter_loaded": False,
                "adapter_enabled": False,
                "migration_state": "legacy_cleanup_required" if legacy_artifact_present else "legacy_absent",
            },
            "adapter_installed": legacy_artifact_present,
            "adapter_loaded": False,
            "adapter_enabled": False,
            "job_exists": installed,
            "job_enabled": False,
            "job_state": "retired_cleanup_required" if legacy_artifact_present else None,
            "job_schedule_display": "retired_local_cleanup_only",
            "legacy_service": legacy_service,
            "retired_artifacts": _retired_artifacts(plist_path=plist_path, script_path=script),
            "retired_legacy_cleanup_required": legacy_artifact_present,
        }
    )
    return payload


def _non_persistent_status(
    *,
    profile: WorkspaceProfile,
    interval_seconds: int,
    adapter_id: str,
) -> dict[str, Any]:
    payload = _base_status(
        profile=profile,
        adapter_id=adapter_id,
        interval_seconds=interval_seconds,
        status="blocked",
        loaded=False,
        summary="当前环境没有可由 MAS 安装的 persistent local scheduler；local 只保留 legacy cleanup diagnostic。",
        script_path=_tick_script_path(profile),
        latest_receipt=_read_json(_latest_receipt_path(profile)),
        drift_reasons=["persistent_local_scheduler_not_available"],
    )
    payload["adapter_status"] = {
        "adapter_installed": False,
        "adapter_loaded": False,
        "adapter_enabled": False,
        "migration_state": "none",
    }
    return payload


def _base_status(
    *,
    profile: WorkspaceProfile,
    adapter_id: str,
    interval_seconds: int,
    status: str,
    loaded: bool,
    summary: str,
    script_path: Path,
    latest_receipt: dict[str, Any],
    drift_reasons: list[str],
) -> dict[str, Any]:
    latest_recorded_at = _text(latest_receipt.get("finished_at")) or _text(latest_receipt.get("started_at"))
    payload = {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": "workspace_runtime_supervision",
        "scheduler_owner": SCHEDULER_OWNER,
        "owner": SCHEDULER_OWNER,
        "active_path_role": consumer_migration.LOCAL_DIAGNOSTIC_PATH_ROLE,
        "consumer_migration": consumer_migration.build_consumer_migration_contract(
            adapter_id=adapter_id,
            manager="local",
        ),
        "adapter_id": adapter_id,
        "manager": "local",
        "generated_at": utc_now(),
        "workspace_key": workspace_key(profile),
        "job_id": _job_id(profile),
        "job_name": _job_id(profile),
        "status": status,
        "loaded": loaded,
        "summary": summary,
        "interval_seconds": interval_seconds,
        "desired_schedule": "retired_local_cleanup_only",
        "schedule_spec": {
            "kind": "retired_local_diagnostic_cleanup_only",
            "interval_seconds": interval_seconds,
        },
        "overlap_policy": "not_applicable_retired_local_adapter",
        "misfire_policy": "not_applicable_retired_local_adapter",
        "script_path": str(script_path),
        "script_exists": script_path.is_file(),
        "tick_script_checksum": None,
        "expected_tick_script_checksum": None,
        "watch_command": [],
        "tick_sequence": [],
        "latest_run_status": _text(latest_receipt.get("outcome")),
        "latest_run_recorded_at": latest_recorded_at,
        "latest_run_summary": _text(latest_receipt.get("summary")),
        "latest_run_session_path": str(_latest_receipt_path(profile)) if latest_receipt else None,
        "last_receipt_ref": str(_latest_receipt_path(profile)),
        "drift_reasons": drift_reasons,
        "duplicate_job_ids": [],
        "migration_state": "none",
        "runtime_contract_ready": True,
        "runtime_contract_issues": [],
        "legacy_service": {},
        "legacy_service_role": "retired_cleanup_evidence",
        "retired_legacy_cleanup_required": False,
        "cleanup_command": "runtime-remove-supervision --profile <profile> --manager local",
        "replacement_command": "runtime-ensure-supervision --profile <profile> --manager opl",
    }
    from med_autoscience.controllers import outer_supervision_slo

    payload["outer_supervision_slo"] = outer_supervision_slo.build_outer_supervision_slo_projection(
        profile=profile,
        supervision_status=payload,
        generated_at=str(payload["generated_at"]),
        interval_seconds=interval_seconds,
    )
    return payload


def _retired_artifacts(*, plist_path: Path, script_path: Path) -> dict[str, str]:
    artifacts: dict[str, str] = {}
    if plist_path.exists():
        artifacts["launch_agent"] = str(plist_path)
    if script_path.exists():
        artifacts["tick_script"] = str(script_path)
    return artifacts


def _legacy_launch_agent_projection(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        key: payload[key]
        for key in (
            "Label",
            "ProgramArguments",
            "RunAtLoad",
            "StartInterval",
            "StandardErrorPath",
            "StandardOutPath",
            "WorkingDirectory",
        )
        if key in payload
    }


def _launch_agent_probe(*, label: str) -> dict[str, Any]:
    domain = f"gui/{os.getuid()}"
    result = _run_command(["launchctl", "print", f"{domain}/{label}"])
    return {
        "command": result["command"],
        "exit_code": result["exit_code"],
        "loaded": result["exit_code"] == 0,
        "output": result["output"],
    }


def _unload_launch_agent(*, plist_path: Path, label: str) -> list[dict[str, Any]]:
    domain = f"gui/{os.getuid()}"
    return [
        _run_command(["launchctl", "disable", f"{domain}/{label}"]),
        _run_command(["launchctl", "bootout", domain, str(plist_path)]),
    ]


def _run_command(command: list[str]) -> dict[str, Any]:
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    return {
        "command": command,
        "exit_code": completed.returncode,
        "output": (completed.stdout or completed.stderr or "").strip(),
    }


def _state_root(profile: WorkspaceProfile) -> Path:
    return profile.workspace_root / "artifacts" / "supervision" / "scheduler"


def _tick_script_path(profile: WorkspaceProfile) -> Path:
    return _state_root(profile) / "bin" / "watch_runtime_tick.py"


def _latest_receipt_path(profile: WorkspaceProfile) -> Path:
    return _state_root(profile) / "receipts" / "latest.json"


def _launch_agents_dir() -> Path:
    override = _text(os.environ.get("MAS_LAUNCHD_AGENTS_DIR"))
    if override:
        return Path(override)
    return Path.home() / "Library" / "LaunchAgents"


def _launch_agent_path(profile: WorkspaceProfile) -> Path:
    return _launch_agents_dir() / f"{_launchd_label(profile)}.plist"


def _launchd_label(profile: WorkspaceProfile) -> str:
    return f"ai.medautoscience.{workspace_key(profile)}.supervision"


def _job_id(profile: WorkspaceProfile) -> str:
    return f"mas-supervision-{workspace_key(profile)}"


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return dict(payload) if isinstance(payload, dict) else {}


def _read_plist(path: Path) -> dict[str, Any]:
    try:
        payload = plistlib.loads(path.read_bytes())
    except (OSError, plistlib.InvalidFileException):
        return {}
    return dict(payload) if isinstance(payload, dict) else {}


def _systemd_user_available() -> bool:
    return bool(os.environ.get("XDG_RUNTIME_DIR")) and _command_exists("systemctl")


def _command_exists(binary: str) -> bool:
    return subprocess.run(["/usr/bin/env", "which", binary], capture_output=True, text=True, check=False).returncode == 0


def _slugify(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-").lower()
    return normalized or "workspace"


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "DEFAULT_INTERVAL_SECONDS",
    "SCHEMA_VERSION",
    "SCHEDULER_OWNER",
    "ensure",
    "local_backend_id",
    "remove",
    "status",
    "utc_now",
    "workspace_key",
]
