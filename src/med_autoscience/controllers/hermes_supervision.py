from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
from typing import Any, Iterable

from med_autoscience.hermes_runtime_contract import inspect_hermes_runtime_contract
from med_autoscience.profiles import WorkspaceProfile


SCHEMA_VERSION = 1
DEFAULT_INTERVAL_SECONDS = 5 * 60
_SILENT_PROMPT = (
    "A pre-run supervision script has already executed the MedAutoScience workspace supervision tick.\n"
    "If the script output shows returncode=0, respond exactly with:\n"
    "[SILENT] Hermes-hosted MedAutoScience supervision tick completed.\n"
    "If the script failed, report the failure briefly and include the failing command."
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _slugify(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-").lower()
    return normalized or "workspace"


def _workspace_key(profile: WorkspaceProfile) -> str:
    digest = hashlib.sha256(str(profile.workspace_root).encode("utf-8")).hexdigest()[:8]
    return f"{_slugify(profile.name)}-{digest}"


def _require_interval_minutes(interval_seconds: int) -> int:
    if interval_seconds < 60 or interval_seconds % 60 != 0:
        raise ValueError("interval_seconds must be a positive multiple of 60")
    return interval_seconds // 60


def _job_name(profile: WorkspaceProfile) -> str:
    return f"medautoscience-supervision-{_workspace_key(profile)}"


def _script_relpath(profile: WorkspaceProfile) -> str:
    return f"med-autoscience/{_workspace_key(profile)}/watch_runtime_tick.py"


def _script_path(profile: WorkspaceProfile) -> Path:
    return profile.hermes_home_root / "scripts" / _script_relpath(profile)


def _jobs_path(profile: WorkspaceProfile) -> Path:
    return profile.hermes_home_root / "cron" / "jobs.json"


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


def _render_supervision_script(profile: WorkspaceProfile, *, interval_seconds: int) -> str:
    command_json = json.dumps(_watch_runtime_command(profile, interval_seconds=interval_seconds))
    return (
        "#!/usr/bin/env python3\n"
        "from __future__ import annotations\n\n"
        "import json\n"
        "import subprocess\n"
        "import sys\n\n"
        f"COMMAND = json.loads({json.dumps(command_json)})\n\n"
        "completed = subprocess.run(COMMAND, capture_output=True, text=True, check=False)\n"
        "payload = {\n"
        '    "command": COMMAND,\n'
        '    "returncode": completed.returncode,\n'
        "}\n"
        "stdout = (completed.stdout or '').strip()\n"
        "stderr = (completed.stderr or '').strip()\n"
        "if stdout:\n"
        "    try:\n"
        '        payload["result"] = json.loads(stdout)\n'
        "    except json.JSONDecodeError:\n"
        '        payload["stdout"] = stdout\n'
        "if stderr:\n"
        '    payload["stderr"] = stderr\n'
        "print(json.dumps(payload, ensure_ascii=False))\n"
        "raise SystemExit(completed.returncode)\n"
    )


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
    return [str(launcher), *args]


def _load_jobs(profile: WorkspaceProfile) -> list[dict[str, Any]]:
    jobs_path = _jobs_path(profile)
    if not jobs_path.is_file():
        return []
    try:
        payload = json.loads(jobs_path.read_text(encoding="utf-8")) or []
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(payload, list):
        return []
    jobs: list[dict[str, Any]] = []
    for item in payload:
        if isinstance(item, dict):
            jobs.append(dict(item))
    return jobs


def _resolve_job_script_path(profile: WorkspaceProfile, script_value: object) -> Path | None:
    text = str(script_value or "").strip()
    if not text:
        return None
    raw = Path(text).expanduser()
    if raw.is_absolute():
        return raw.resolve()
    return (profile.hermes_home_root / "scripts" / raw).resolve()


def _matching_jobs(profile: WorkspaceProfile) -> list[dict[str, Any]]:
    desired_name = _job_name(profile)
    desired_script_path = _script_path(profile)
    matches: list[dict[str, Any]] = []
    for job in _load_jobs(profile):
        job_name = str(job.get("name") or "").strip()
        resolved_script = _resolve_job_script_path(profile, job.get("script"))
        if job_name == desired_name or resolved_script == desired_script_path:
            matches.append(job)
    return matches


def _job_sort_key(job: dict[str, Any]) -> tuple[int, int, str]:
    enabled = 1 if bool(job.get("enabled", True)) else 0
    scheduled = 1 if str(job.get("state") or "").strip() == "scheduled" else 0
    created_at = str(job.get("created_at") or "")
    return (enabled, scheduled, created_at)


def _select_primary_job(jobs: Iterable[dict[str, Any]]) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    ordered = sorted((dict(job) for job in jobs), key=_job_sort_key, reverse=True)
    if not ordered:
        return None, []
    return ordered[0], ordered[1:]


def _schedule_matches(job: dict[str, Any], *, interval_seconds: int) -> bool:
    minutes = _require_interval_minutes(interval_seconds)
    schedule = job.get("schedule")
    if not isinstance(schedule, dict):
        return False
    return schedule.get("kind") == "interval" and int(schedule.get("minutes") or -1) == minutes


def _job_drift(
    *,
    profile: WorkspaceProfile,
    job: dict[str, Any] | None,
    interval_seconds: int,
) -> list[str]:
    if job is None:
        return ["job_missing"]
    drift: list[str] = []
    if str(job.get("name") or "").strip() != _job_name(profile):
        drift.append("name_mismatch")
    if str(job.get("prompt") or "").strip() != _SILENT_PROMPT:
        drift.append("prompt_mismatch")
    if str(job.get("deliver") or "").strip() != "local":
        drift.append("deliver_mismatch")
    if not _schedule_matches(job, interval_seconds=interval_seconds):
        drift.append("schedule_mismatch")
    if _resolve_job_script_path(profile, job.get("script")) != _script_path(profile):
        drift.append("script_mismatch")
    return drift


def _status_summary(
    *,
    status: str,
    gateway_service_loaded: bool,
    job_present: bool,
    drift_reasons: list[str],
) -> str:
    if status == "loaded":
        if drift_reasons:
            return "Hermes-hosted runtime supervision 已在线，但当前注册项与期望 contract 存在漂移。"
        return "Hermes-hosted runtime supervision 已在线，workspace 级监管会持续刷新。"
    if status == "not_loaded":
        if not gateway_service_loaded and job_present:
            return "Hermes-hosted runtime supervision 已注册，但 Hermes gateway 当前未在线。"
        if job_present:
            return "Hermes-hosted runtime supervision 已注册，但当前未处于调度中。"
        return "Hermes-hosted runtime supervision 还没有进入可调度状态。"
    return "Hermes-hosted runtime supervision 尚未注册。"


def _ensure_script_file(profile: WorkspaceProfile, *, interval_seconds: int) -> Path:
    script_path = _script_path(profile)
    script_path.parent.mkdir(parents=True, exist_ok=True)
    script_path.write_text(_render_supervision_script(profile, interval_seconds=interval_seconds), encoding="utf-8")
    script_path.chmod(0o755)
    return script_path


def _remove_empty_parent_dirs(path: Path, *, stop_at: Path) -> None:
    current = path.parent
    stop = stop_at.resolve()
    while current.exists() and current.resolve() != stop:
        try:
            current.rmdir()
        except OSError:
            break
        current = current.parent


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
    gateway_service_loaded = bool(runtime_contract.get("gateway_service_loaded"))
    job_present = primary_job is not None
    script_exists = script_path.is_file()
    job_enabled = bool((primary_job or {}).get("enabled", False))
    job_state = str((primary_job or {}).get("state") or "").strip() or None
    if job_present and gateway_service_loaded and job_enabled and job_state == "scheduled" and script_exists:
        status = "loaded"
    elif job_present:
        status = "not_loaded"
    else:
        status = "not_installed"
    return {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": "workspace_runtime_supervision",
        "owner": "hermes_gateway_cron",
        "generated_at": _utc_now(),
        "manager": runtime_contract.get("gateway_service_manager"),
        "status": status,
        "loaded": status == "loaded",
        "summary": _status_summary(
            status=status,
            gateway_service_loaded=gateway_service_loaded,
            job_present=job_present,
            drift_reasons=drift_reasons,
        ),
        "gateway_service_label": runtime_contract.get("gateway_service_label"),
        "gateway_service_loaded": gateway_service_loaded,
        "jobs_store_path": str(_jobs_path(profile)),
        "job_exists": job_present,
        "job_id": str((primary_job or {}).get("id") or "").strip() or None,
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
        "duplicate_job_ids": [
            str(job.get("id") or "").strip()
            for job in duplicate_jobs
            if str(job.get("id") or "").strip()
        ],
        "runtime_contract_ready": bool(runtime_contract.get("ready")),
        "runtime_contract_issues": list(runtime_contract.get("issues") or []),
    }


def ensure_supervision(
    *,
    profile: WorkspaceProfile,
    interval_seconds: int = DEFAULT_INTERVAL_SECONDS,
    trigger_now: bool = True,
) -> dict[str, Any]:
    _ensure_script_file(profile, interval_seconds=interval_seconds)
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

    after = read_supervision_status(profile=profile, interval_seconds=interval_seconds)
    return {
        "action": action,
        "before": before,
        "after": after,
        "removed_duplicate_job_ids": removed_duplicate_job_ids,
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

    after = read_supervision_status(profile=profile, interval_seconds=interval_seconds)
    return {
        "before": before,
        "after": after,
        "removed_job_ids": removed_job_ids,
        "script_removed": script_removed,
        "command_outputs": command_outputs,
    }
