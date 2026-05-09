from __future__ import annotations

import os
from pathlib import Path
import platform
import subprocess
from typing import Any

from med_autoscience.profiles import WorkspaceProfile


def legacy_service_status(*, profile: WorkspaceProfile, slug: str) -> dict[str, Any]:
    system = platform.system()
    if system == "Darwin":
        label = launchd_label(profile=profile, slug=slug)
        service_file = launchd_service_file(profile=profile, slug=slug)
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
        service_name = systemd_service_name(profile=profile, slug=slug)
        service_file = systemd_service_file(profile=profile, slug=slug)
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


def remove_legacy_service(
    *,
    profile: WorkspaceProfile,
    slug: str,
    run_command,
) -> dict[str, Any]:
    status = legacy_service_status(profile=profile, slug=slug)
    manager = str(status.get("manager") or "")
    service_label = str(status.get("service_label") or "").strip()
    service_file_text = str(status.get("service_file") or "").strip()
    service_file = Path(service_file_text) if service_file_text else None
    command_outputs: list[dict[str, Any]] = []
    unloaded = False
    removed_service_file = False

    if manager == "launchd" and service_label:
        command = ["launchctl", "bootout", f"gui/{os.getuid()}/{service_label}"]
        exit_code, output = run_command(command=command)
        command_outputs.append({"command": command, "exit_code": exit_code, "output": output})
        unloaded = exit_code == 0
    elif manager == "systemd" and service_label:
        command = ["systemctl", "--user", "disable", "--now", f"{service_label}.service"]
        exit_code, output = run_command(command=command)
        command_outputs.append({"command": command, "exit_code": exit_code, "output": output})
        unloaded = exit_code == 0

    if service_file is not None and service_file.exists():
        service_file.unlink()
        removed_service_file = True

    if manager == "systemd" and removed_service_file:
        command = ["systemctl", "--user", "daemon-reload"]
        exit_code, output = run_command(command=command)
        command_outputs.append({"command": command, "exit_code": exit_code, "output": output})

    return {
        "before": status,
        "unloaded": unloaded,
        "removed_service_file": removed_service_file,
        "command_outputs": command_outputs,
    }


def launchd_label(*, profile: WorkspaceProfile, slug: str) -> str:
    return f"ai.medautoscience.{slug}.watch-runtime"


def launchd_service_file(*, profile: WorkspaceProfile, slug: str) -> Path:
    return Path.home() / "Library" / "LaunchAgents" / f"{launchd_label(profile=profile, slug=slug)}.plist"


def systemd_service_name(*, profile: WorkspaceProfile, slug: str) -> str:
    return f"medautoscience-watch-runtime-{slug}"


def systemd_service_file(*, profile: WorkspaceProfile, slug: str) -> Path:
    return Path.home() / ".config" / "systemd" / "user" / f"{systemd_service_name(profile=profile, slug=slug)}.service"


__all__ = [
    "launchd_label",
    "launchd_service_file",
    "legacy_service_status",
    "remove_legacy_service",
    "systemd_service_file",
    "systemd_service_name",
]
