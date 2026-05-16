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
LAUNCHD_TOOL_PATH = "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"


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
    if backend != "local_launchd":
        current = _non_persistent_status(profile=profile, interval_seconds=interval_seconds, adapter_id=backend)
        proof = _install_proof(
            profile=profile,
            adapter_id=backend,
            interval_seconds=interval_seconds,
            status="blocked",
            installed=False,
            dry_run=True,
            commands=[],
            command_outputs=[],
            reason="persistent_local_scheduler_not_supported_in_this_environment",
        )
        if write_install_proof:
            _write_json(_install_proof_path(profile), proof)
        return {
            "schema_version": SCHEMA_VERSION,
            "surface_kind": "workspace_runtime_supervision_install_result",
            "action": "blocked",
            "manager": "local",
            "scheduler_owner": SCHEDULER_OWNER,
            "adapter_id": backend,
            "active_path_role": consumer_migration.LOCAL_DIAGNOSTIC_PATH_ROLE,
            "before": current,
            "after": current,
            "install_proof": proof,
            "install_proof_path": str(_install_proof_path(profile)) if write_install_proof else None,
            "dry_run": dry_run,
        }

    before = _launchd_status(profile=profile, interval_seconds=interval_seconds)
    script = _tick_script_path(profile)
    plist_path = _launch_agent_path(profile)
    plist_payload = _launch_agent_plist(profile=profile, interval_seconds=interval_seconds)
    command_outputs: list[dict[str, Any]] = []
    commands = _launchd_install_commands(profile)
    action = "dry_run" if dry_run else "installed"
    if not dry_run and not _workspace_python_available(profile):
        proof = _install_proof(
            profile=profile,
            adapter_id="local_launchd",
            interval_seconds=interval_seconds,
            status="blocked",
            installed=False,
            dry_run=False,
            commands=commands,
            command_outputs=command_outputs,
            reason="workspace_python_missing_or_not_executable",
        )
        if write_install_proof:
            _write_json(_install_proof_path(profile), proof)
        after = _launchd_status(profile=profile, interval_seconds=interval_seconds)
        return {
            "schema_version": SCHEMA_VERSION,
            "surface_kind": "workspace_runtime_supervision_install_result",
            "action": "blocked",
            "manager": "local",
            "scheduler_owner": SCHEDULER_OWNER,
            "adapter_id": "local_launchd",
            "active_path_role": consumer_migration.LOCAL_DIAGNOSTIC_PATH_ROLE,
            "before": before,
            "after": after,
            "script_path": str(script),
            "launch_agent_path": str(plist_path),
            "install_proof": proof,
            "install_proof_path": str(_install_proof_path(profile)) if write_install_proof else None,
            "command_outputs": command_outputs,
            "dry_run": dry_run,
        }
    if not dry_run:
        script = _ensure_tick_script(profile=profile, interval_seconds=interval_seconds)
        plist_path.parent.mkdir(parents=True, exist_ok=True)
        plist_path.write_bytes(plistlib.dumps(plist_payload, sort_keys=True))
        command_outputs.extend(_load_launch_agent(plist_path=plist_path, label=_launchd_label(profile)))
        if trigger_now:
            command_outputs.append(_run_tick_script(script_path=script))
            action = "installed_and_triggered"
    proof = _install_proof(
        profile=profile,
        adapter_id="local_launchd",
        interval_seconds=interval_seconds,
        status="ready" if dry_run else "installed",
        installed=not dry_run,
        dry_run=dry_run,
        commands=commands,
        command_outputs=command_outputs,
        reason=None,
    )
    if write_install_proof and not dry_run:
        _write_json(_install_proof_path(profile), proof)
    after = _launchd_status(profile=profile, interval_seconds=interval_seconds)
    return {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": "workspace_runtime_supervision_install_result",
        "action": action,
        "manager": "local",
        "scheduler_owner": SCHEDULER_OWNER,
        "adapter_id": "local_launchd",
        "active_path_role": consumer_migration.LOCAL_DIAGNOSTIC_PATH_ROLE,
        "before": before,
        "after": after,
        "script_path": str(script),
        "launch_agent_path": str(plist_path),
        "install_proof": proof,
        "install_proof_path": str(_install_proof_path(profile)) if write_install_proof and not dry_run else None,
        "command_outputs": command_outputs,
        "dry_run": dry_run,
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
    if plist_path.exists():
        actual = _read_plist(plist_path)
        expected = _launch_agent_plist(profile=profile, interval_seconds=interval_seconds)
        if actual and actual != expected:
            drift_reasons.append("launch_agent_plist_drift")
    if script.exists() and _script_checksum(script) != _expected_script_checksum(
        profile=profile,
        interval_seconds=interval_seconds,
    ):
        drift_reasons.append("tick_script_checksum_drift")
    installed = plist_path.exists()
    script_exists = script.exists()
    launchd_probe = (
        _launch_agent_probe(label=_launchd_label(profile))
        if installed
        else {"loaded": False, "exit_code": None, "output": ""}
    )
    loaded = installed and script_exists and bool(launchd_probe.get("loaded")) and not drift_reasons
    status_value = "loaded" if loaded else ("not_loaded" if installed else "not_installed")
    summary = (
        "MAS local scheduler LaunchAgent 已安装并指向 MAS-owned supervision tick。"
        if loaded
        else "MAS local scheduler 尚未安装或存在漂移；运行 runtime-ensure-supervision 可刷新。"
    )
    payload = _base_status(
        profile=profile,
        adapter_id="local_launchd",
        interval_seconds=interval_seconds,
        status=status_value,
        loaded=loaded,
        summary=summary,
        script_path=script,
        latest_receipt=latest_receipt,
        drift_reasons=drift_reasons,
    )
    payload.update(
        {
            "launch_agent_label": _launchd_label(profile),
            "launch_agent_path": str(plist_path),
            "launch_agent_probe": launchd_probe,
            "adapter_status": {
                "adapter_installed": installed,
                "adapter_loaded": loaded,
                "adapter_enabled": installed,
                "migration_state": "none",
            },
            "adapter_installed": installed,
            "adapter_loaded": loaded,
            "adapter_enabled": installed,
            "job_exists": installed,
            "job_enabled": installed,
            "job_state": "scheduled" if installed else None,
            "job_schedule_display": f"every {interval_seconds}s",
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
        summary="当前环境没有可由 MAS 安装的 persistent local scheduler；可运行 one-shot reconcile。",
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
        "desired_schedule": f"every {interval_seconds}s",
        "schedule_spec": {"kind": "interval", "interval_seconds": interval_seconds, "timezone": "local"},
        "overlap_policy": "skip_if_running",
        "misfire_policy": "record_missed_and_wait_next",
        "script_path": str(script_path),
        "script_exists": script_path.is_file(),
        "tick_script_checksum": _script_checksum(script_path) if script_path.is_file() else None,
        "expected_tick_script_checksum": _expected_script_checksum(
            profile=profile,
            interval_seconds=interval_seconds,
        ),
        "watch_command": _watch_runtime_command(profile, interval_seconds=interval_seconds),
        "tick_sequence": _tick_sequence(profile, interval_seconds=interval_seconds),
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
    }
    from med_autoscience.controllers import outer_supervision_slo

    payload["outer_supervision_slo"] = outer_supervision_slo.build_outer_supervision_slo_projection(
        profile=profile,
        supervision_status=payload,
        generated_at=str(payload["generated_at"]),
        interval_seconds=interval_seconds,
    )
    return payload


def _ensure_tick_script(*, profile: WorkspaceProfile, interval_seconds: int) -> Path:
    path = _tick_script_path(profile)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_render_tick_script(profile=profile, interval_seconds=interval_seconds), encoding="utf-8")
    path.chmod(0o755)
    return path


def _render_tick_script(*, profile: WorkspaceProfile, interval_seconds: int) -> str:
    commands_json = json.dumps(_tick_sequence(profile, interval_seconds=interval_seconds))
    latest_receipt_json = json.dumps(str(_latest_receipt_path(profile)))
    history_receipt_json = json.dumps(str(_history_receipt_path(profile)))
    lock_path_json = json.dumps(str(_lock_path(profile)))
    return (
        f"#!{_workspace_python_path(profile)}\n"
        "from __future__ import annotations\n\n"
        "from datetime import datetime, timezone\n"
        "import json\n"
        "import os\n"
        "from pathlib import Path\n"
        "import subprocess\n\n"
        f"COMMANDS = json.loads({json.dumps(commands_json)})\n"
        f"LATEST_RECEIPT = Path(json.loads({json.dumps(latest_receipt_json)}))\n"
        f"HISTORY_RECEIPT = Path(json.loads({json.dumps(history_receipt_json)}))\n"
        f"LOCK_PATH = Path(json.loads({json.dumps(lock_path_json)}))\n\n"
        f"TOOL_PATH = {LAUNCHD_TOOL_PATH!r}\n"
        "existing_path = os.environ.get('PATH')\n"
        "if existing_path:\n"
        "    os.environ['PATH'] = TOOL_PATH + os.pathsep + existing_path\n"
        "else:\n"
        "    os.environ['PATH'] = TOOL_PATH\n\n"
        "def now():\n"
        "    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()\n\n"
        "def write_receipt(payload):\n"
        "    LATEST_RECEIPT.parent.mkdir(parents=True, exist_ok=True)\n"
        "    LATEST_RECEIPT.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + '\\n', encoding='utf-8')\n"
        "    HISTORY_RECEIPT.parent.mkdir(parents=True, exist_ok=True)\n"
        "    with HISTORY_RECEIPT.open('a', encoding='utf-8') as handle:\n"
        "        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + '\\n')\n\n"
        "def inspect_existing_lock():\n"
        "    if not LOCK_PATH.exists():\n"
        "        return {'active': False, 'clear': False, 'pid': None, 'reason': 'lock_missing'}\n"
        "    raw = LOCK_PATH.read_text(encoding='utf-8').strip()\n"
        "    try:\n"
        "        pid = int(raw)\n"
        "    except ValueError:\n"
        "        return {'active': False, 'clear': True, 'pid': None, 'reason': 'invalid_lock_pid', 'raw': raw[:200]}\n"
        "    if pid <= 0:\n"
        "        return {'active': False, 'clear': True, 'pid': pid, 'reason': 'invalid_lock_pid'}\n"
        "    try:\n"
        "        os.kill(pid, 0)\n"
        "    except ProcessLookupError:\n"
        "        return {'active': False, 'clear': True, 'pid': pid, 'reason': 'lock_pid_not_running'}\n"
        "    except PermissionError:\n"
        "        return {'active': True, 'clear': False, 'pid': pid, 'reason': 'lock_pid_exists_permission_denied'}\n"
        "    return {'active': True, 'clear': False, 'pid': pid, 'reason': 'lock_pid_running'}\n\n"
        "def release_owned_lock():\n"
        "    try:\n"
        "        if LOCK_PATH.read_text(encoding='utf-8').strip() == str(os.getpid()):\n"
        "            LOCK_PATH.unlink()\n"
        "    except FileNotFoundError:\n"
        "        pass\n\n"
        "started_at = now()\n"
        "lock_metadata = {}\n"
        "if LOCK_PATH.exists():\n"
        "    lock_state = inspect_existing_lock()\n"
        "    if lock_state['active']:\n"
        "        payload = {'schema_version': 1, 'surface_kind': 'mas_supervision_tick_receipt', 'started_at': started_at, 'finished_at': now(), 'outcome': 'skipped_overlap', 'exit_code': 0, 'tick_sequence': [], 'summary': 'previous MAS supervision tick still holds the lock', 'lock_status': 'active_lock_present', 'active_lock_pid': lock_state.get('pid'), 'active_lock_reason': lock_state.get('reason')}\n"
        "        write_receipt(payload)\n"
        "        raise SystemExit(0)\n"
        "    if lock_state['clear']:\n"
        "        LOCK_PATH.unlink()\n"
        "        lock_metadata = {'lock_status': 'cleared_stale_lock', 'cleared_stale_lock': True, 'stale_lock_pid': lock_state.get('pid'), 'stale_lock_reason': lock_state.get('reason')}\n"
        "        if lock_state.get('raw'):\n"
        "            lock_metadata['stale_lock_raw'] = lock_state.get('raw')\n"
        "LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)\n"
        "LOCK_PATH.write_text(str(os.getpid()), encoding='utf-8')\n"
        "results = []\n"
        "exit_code = 0\n"
        "outcome = 'succeeded'\n"
        "try:\n"
        "    for command in COMMANDS:\n"
        "        completed = subprocess.run(command, capture_output=True, text=True, check=False)\n"
        "        item = {'command': command, 'returncode': completed.returncode}\n"
        "        stdout = (completed.stdout or '').strip()\n"
        "        stderr = (completed.stderr or '').strip()\n"
        "        if stdout:\n"
        "            try:\n"
        "                item['result'] = json.loads(stdout)\n"
        "            except json.JSONDecodeError:\n"
        "                item['stdout'] = stdout[-4000:]\n"
        "        if stderr:\n"
        "            item['stderr'] = stderr[-4000:]\n"
        "        results.append(item)\n"
        "        if completed.returncode != 0:\n"
        "            exit_code = completed.returncode\n"
        "            outcome = 'failed'\n"
        "            break\n"
        "finally:\n"
        "    release_owned_lock()\n"
        "payload = {'schema_version': 1, 'surface_kind': 'mas_supervision_tick_receipt', 'started_at': started_at, 'finished_at': now(), 'outcome': outcome, 'exit_code': exit_code, 'tick_sequence': results, 'summary': f'MAS supervision tick {outcome}'}\n"
        "payload.update(lock_metadata)\n"
        "write_receipt(payload)\n"
        "print(json.dumps(payload, ensure_ascii=False))\n"
        "raise SystemExit(exit_code)\n"
    )


def _launch_agent_plist(*, profile: WorkspaceProfile, interval_seconds: int) -> dict[str, Any]:
    state_root = _state_root(profile)
    return {
        "Label": _launchd_label(profile),
        "ProgramArguments": [str(_tick_script_path(profile))],
        "RunAtLoad": False,
        "StartInterval": interval_seconds,
        "StandardErrorPath": str(state_root / "logs" / "launchd.stderr.log"),
        "StandardOutPath": str(state_root / "logs" / "launchd.stdout.log"),
        "WorkingDirectory": str(profile.workspace_root),
        "EnvironmentVariables": {"PATH": LAUNCHD_TOOL_PATH},
    }


def _install_proof(
    *,
    profile: WorkspaceProfile,
    adapter_id: str,
    interval_seconds: int,
    status: str,
    installed: bool,
    dry_run: bool,
    commands: list[list[str]],
    command_outputs: list[dict[str, Any]],
    reason: str | None,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": "mas_supervision_scheduler_install_proof",
        "generated_at": utc_now(),
        "scheduler_owner": SCHEDULER_OWNER,
        "active_path_role": consumer_migration.LOCAL_DIAGNOSTIC_PATH_ROLE,
        "consumer_migration": consumer_migration.build_consumer_migration_contract(
            adapter_id=adapter_id,
            manager="local",
        ),
        "adapter_id": adapter_id,
        "manager": "local",
        "workspace_key": workspace_key(profile),
        "job_id": _job_id(profile),
        "interval_seconds": interval_seconds,
        "status": status,
        "installed": installed,
        "dry_run": dry_run,
        "reason": reason,
        "install_commands": commands,
        "command_outputs": command_outputs,
        "artifact_path": str(_install_proof_path(profile)),
        "tick_script_path": str(_tick_script_path(profile)),
        "latest_receipt_ref": str(_latest_receipt_path(profile)),
    }


def _launchd_install_commands(profile: WorkspaceProfile) -> list[list[str]]:
    label = _launchd_label(profile)
    plist_path = _launch_agent_path(profile)
    domain = f"gui/{os.getuid()}"
    return [
        ["launchctl", "bootstrap", domain, str(plist_path)],
        ["launchctl", "enable", f"{domain}/{label}"],
    ]


def _load_launch_agent(*, plist_path: Path, label: str) -> list[dict[str, Any]]:
    domain = f"gui/{os.getuid()}"
    return [
        _run_command(["launchctl", "bootout", domain, str(plist_path)]),
        _run_command(["launchctl", "bootstrap", domain, str(plist_path)]),
        _run_command(["launchctl", "enable", f"{domain}/{label}"]),
    ]


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


def _run_tick_script(*, script_path: Path) -> dict[str, Any]:
    return _run_command([str(script_path)])


def _run_command(command: list[str]) -> dict[str, Any]:
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    return {
        "command": command,
        "exit_code": completed.returncode,
        "output": (completed.stdout or completed.stderr or "").strip(),
    }


def _tick_sequence(profile: WorkspaceProfile, *, interval_seconds: int) -> list[list[str]]:
    return [
        _watch_runtime_command(profile, interval_seconds=interval_seconds),
        [
            str(profile.workspace_root / "ops" / "medautoscience" / "bin" / "supervisor-scan"),
            "--apply-safe-actions",
            "--apply-runtime-platform-repair",
            "--developer-supervisor-mode",
            "developer_apply_safe",
        ],
        [
            str(profile.workspace_root / "ops" / "medautoscience" / "bin" / "supervisor-consume"),
            "--mode",
            "developer_apply_safe",
            "--apply",
        ],
        [
            str(profile.workspace_root / "ops" / "medautoscience" / "bin" / "supervisor-execute-dispatch"),
            "--mode",
            "developer_apply_safe",
            "--apply",
        ],
    ]


def _watch_runtime_command(profile: WorkspaceProfile, *, interval_seconds: int) -> list[str]:
    return [
        str(profile.workspace_root / "ops" / "medautoscience" / "bin" / "watch-runtime"),
        "--interval-seconds",
        str(interval_seconds),
        "--max-ticks",
        "1",
    ]


def _state_root(profile: WorkspaceProfile) -> Path:
    return profile.workspace_root / "artifacts" / "supervision" / "scheduler"


def _tick_script_path(profile: WorkspaceProfile) -> Path:
    return _state_root(profile) / "bin" / "watch_runtime_tick.py"


def _workspace_python_path(profile: WorkspaceProfile) -> Path:
    return profile.workspace_root / ".venv" / "bin" / "python3"


def _workspace_python_available(profile: WorkspaceProfile) -> bool:
    path = _workspace_python_path(profile)
    return path.is_file() and os.access(path, os.X_OK)


def _latest_receipt_path(profile: WorkspaceProfile) -> Path:
    return _state_root(profile) / "receipts" / "latest.json"


def _history_receipt_path(profile: WorkspaceProfile) -> Path:
    return _state_root(profile) / "receipts" / "history.jsonl"


def _lock_path(profile: WorkspaceProfile) -> Path:
    return _state_root(profile) / "watch_runtime_tick.lock"


def _install_proof_path(profile: WorkspaceProfile) -> Path:
    return profile.workspace_root / "artifacts" / "supervision" / "install_proof" / "latest.json"


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


def _expected_script_checksum(*, profile: WorkspaceProfile, interval_seconds: int) -> str:
    return hashlib.sha256(_render_tick_script(profile=profile, interval_seconds=interval_seconds).encode("utf-8")).hexdigest()


def _script_checksum(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return dict(payload) if isinstance(payload, dict) else {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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
