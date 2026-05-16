from __future__ import annotations

import importlib
import json
import os
from pathlib import Path
import subprocess
import sys

from tests.study_runtime_test_helpers import make_profile


def _write_workspace_python(profile) -> Path:
    python_path = profile.workspace_root / ".venv" / "bin" / "python3"
    python_path.parent.mkdir(parents=True, exist_ok=True)
    python_path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    python_path.chmod(0o755)
    return python_path


def _write_successful_tick_commands(profile) -> None:
    bin_dir = profile.workspace_root / "ops" / "medautoscience" / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    for name in ("watch-runtime", "supervisor-scan", "supervisor-consume", "supervisor-execute-dispatch"):
        command = bin_dir / name
        command.write_text("#!/bin/sh\necho '{\"ok\": true}'\nexit 0\n", encoding="utf-8")
        command.chmod(0o755)


def test_default_scheduler_status_uses_opl_replacement_without_launchagent(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.supervision_scheduler")
    local = importlib.import_module("med_autoscience.controllers.supervision_scheduler_parts.local_adapter")
    profile = make_profile(tmp_path)
    launch_agents = tmp_path / "LaunchAgents"
    monkeypatch.setattr(local.platform, "system", lambda: "Darwin")
    monkeypatch.setenv("MAS_LAUNCHD_AGENTS_DIR", str(launch_agents))

    result = module.read_supervision_status(profile=profile)

    assert result["scheduler_owner"] == "opl_provider_runtime_manager"
    assert result["adapter_id"] == "opl_family_runtime_provider"
    assert result["manager"] == "opl"
    assert result["status"] == "replacement_owner_active"
    assert result["loaded"] is True
    assert result["adapter_status"]["migration_state"] == "replacement_owner_active"
    assert result["opl_replacement"]["provider_slo_tick_command"] == (
        "opl family-runtime provider-slo tick --provider temporal"
    )
    assert result["legacy_adapter"]["manager"] == "local"
    assert result["legacy_adapter"]["scheduler_owner"] == "mas_supervision_scheduler"
    assert result["authority_boundary"]["can_install_domain_daemon"] is False
    assert result["outer_supervision_slo"]["supervision_owner"] == "opl_provider_runtime_manager"
    assert not launch_agents.exists()


def test_default_scheduler_ensure_delegates_to_opl_replacement_without_launchagent(
    monkeypatch, tmp_path: Path
) -> None:
    module = importlib.import_module("med_autoscience.controllers.supervision_scheduler")
    local = importlib.import_module("med_autoscience.controllers.supervision_scheduler_parts.local_adapter")
    profile = make_profile(tmp_path)
    launch_agents = tmp_path / "LaunchAgents"
    monkeypatch.setattr(local.platform, "system", lambda: "Darwin")
    monkeypatch.setenv("MAS_LAUNCHD_AGENTS_DIR", str(launch_agents))

    result = module.ensure_supervision(profile=profile, trigger_now=True, write_install_proof=True)

    assert result["action"] == "delegated_to_opl_provider_scheduler"
    assert result["scheduler_owner"] == "opl_provider_runtime_manager"
    assert result["manager"] == "opl"
    assert result["dry_run"] is False
    assert result["write_install_proof"] is False
    assert result["after"]["status"] == "replacement_owner_active"
    assert result["legacy_local_adapter"]["manager"] == "local"
    assert result["authority_boundary"]["can_install_domain_daemon"] is False
    assert not launch_agents.exists()


def test_default_scheduler_remove_delegates_to_opl_and_keeps_local_cleanup_explicit(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.supervision_scheduler")
    profile = make_profile(tmp_path)

    result = module.remove_supervision(profile=profile)

    assert result["action"] == "delegated_to_opl_provider_scheduler"
    assert result["scheduler_owner"] == "opl_provider_runtime_manager"
    assert result["manager"] == "opl"
    assert result["removed_job_ids"] == []
    assert result["legacy_local_cleanup_command"].endswith(" --manager local")


def test_local_scheduler_dry_run_projects_launchd_without_hermes(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.supervision_scheduler")
    local = importlib.import_module("med_autoscience.controllers.supervision_scheduler_parts.local_adapter")
    profile = make_profile(tmp_path)

    monkeypatch.setattr(local.platform, "system", lambda: "Darwin")
    monkeypatch.setenv("MAS_LAUNCHD_AGENTS_DIR", str(tmp_path / "LaunchAgents"))

    result = module.ensure_supervision(
        profile=profile,
        manager="local",
        trigger_now=False,
        dry_run=True,
    )

    assert result["scheduler_owner"] == "mas_supervision_scheduler"
    assert result["adapter_id"] == "local_launchd"
    assert result["active_path_role"] == "standalone_local_diagnostic_migration_bridge"
    assert result["consumer_migration"]["replacement_owner"] == "one-person-lab"
    assert result["consumer_migration"]["replacement_owner_surface"] == "opl_provider_runtime_manager"
    assert result["consumer_migration"]["replacement_required_before_retirement"] is True
    assert result["dry_run"] is True
    assert result["install_proof"]["installed"] is False
    assert result["install_proof"]["active_path_role"] == "standalone_local_diagnostic_migration_bridge"
    assert result["install_proof"]["tick_script_path"].endswith("watch_runtime_tick.py")
    assert result["after"]["adapter_id"] == "local_launchd"
    assert not Path(result["script_path"]).exists()


def test_local_scheduler_apply_writes_tick_script_plist_and_receipt(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.supervision_scheduler")
    local = importlib.import_module("med_autoscience.controllers.supervision_scheduler_parts.local_adapter")
    profile = make_profile(tmp_path)
    workspace_python = _write_workspace_python(profile)
    launch_agents = tmp_path / "LaunchAgents"
    monkeypatch.setattr(local.platform, "system", lambda: "Darwin")
    monkeypatch.setenv("MAS_LAUNCHD_AGENTS_DIR", str(launch_agents))
    commands: list[list[str]] = []

    def fake_run_command(command: list[str]) -> dict[str, object]:
        commands.append(command)
        if command and command[0].endswith("watch_runtime_tick.py"):
            receipt = profile.workspace_root / "artifacts" / "supervision" / "scheduler" / "receipts" / "latest.json"
            receipt.parent.mkdir(parents=True, exist_ok=True)
            receipt.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "surface_kind": "mas_supervision_tick_receipt",
                        "started_at": "2026-05-09T00:00:00+00:00",
                        "finished_at": "2026-05-09T00:00:01+00:00",
                        "outcome": "succeeded",
                        "exit_code": 0,
                        "summary": "MAS supervision tick succeeded",
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
        return {"command": command, "exit_code": 0, "output": "ok"}

    monkeypatch.setattr(local, "_run_command", fake_run_command)

    result = module.ensure_supervision(
        profile=profile,
        manager="local",
        trigger_now=True,
        write_install_proof=True,
    )

    assert result["action"] == "installed_and_triggered"
    assert result["after"]["loaded"] is True
    assert result["after"]["launch_agent_probe"]["loaded"] is True
    assert result["after"]["scheduler_owner"] == "mas_supervision_scheduler"
    assert result["after"]["active_path_role"] == "standalone_local_diagnostic_migration_bridge"
    assert result["after"]["consumer_migration"]["retirement_state"] == (
        "local_legacy_retirement_pending_no_active_caller_proof"
    )
    assert result["after"]["latest_run_recorded_at"] == "2026-05-09T00:00:01+00:00"
    assert Path(result["script_path"]).is_file()
    assert Path(result["launch_agent_path"]).is_file()
    assert Path(result["install_proof_path"]).is_file()
    script = Path(result["script_path"]).read_text(encoding="utf-8")
    assert script.startswith(f"#!{workspace_python}\n")
    assert "#!/usr/bin/env python3" not in script
    assert "watch-runtime" in script
    assert "supervisor-scan" in script
    assert "supervisor-consume" in script
    assert "supervisor-execute-dispatch" in script
    assert "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin" in script
    plist = json.loads(json.dumps(local.plistlib.loads(Path(result["launch_agent_path"]).read_bytes())))
    assert plist["EnvironmentVariables"]["PATH"] == "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
    assert any(command[:2] == ["launchctl", "bootstrap"] for command in commands)
    assert any(command[:2] == ["launchctl", "print"] for command in commands)
    assert any(command and command[0].endswith("watch_runtime_tick.py") for command in commands)


def test_generated_tick_script_clears_stale_pid_lock_and_continues(tmp_path: Path) -> None:
    local = importlib.import_module("med_autoscience.controllers.supervision_scheduler_parts.local_adapter")
    profile = make_profile(tmp_path)
    _write_successful_tick_commands(profile)
    script = local._ensure_tick_script(profile=profile, interval_seconds=300)
    lock_path = local._lock_path(profile)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    stale_pid = 999999
    try:
        os.kill(stale_pid, 0)
    except ProcessLookupError:
        pass
    except PermissionError:
        stale_pid = 999998
    lock_path.write_text(str(stale_pid), encoding="utf-8")

    completed = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, check=False)

    assert completed.returncode == 0
    receipt = json.loads(local._latest_receipt_path(profile).read_text(encoding="utf-8"))
    assert receipt["outcome"] == "succeeded"
    assert receipt["lock_status"] == "cleared_stale_lock"
    assert receipt["cleared_stale_lock"] is True
    assert receipt["stale_lock_pid"] == stale_pid
    assert receipt["stale_lock_reason"] == "lock_pid_not_running"
    assert receipt["tick_sequence"]
    assert not lock_path.exists()


def test_local_scheduler_apply_blocks_when_workspace_python_missing(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.supervision_scheduler")
    local = importlib.import_module("med_autoscience.controllers.supervision_scheduler_parts.local_adapter")
    profile = make_profile(tmp_path)
    launch_agents = tmp_path / "LaunchAgents"
    monkeypatch.setattr(local.platform, "system", lambda: "Darwin")
    monkeypatch.setenv("MAS_LAUNCHD_AGENTS_DIR", str(launch_agents))

    result = module.ensure_supervision(
        profile=profile,
        manager="local",
        trigger_now=True,
        write_install_proof=True,
    )

    assert result["action"] == "blocked"
    assert result["install_proof"]["status"] == "blocked"
    assert result["install_proof"]["reason"] == "workspace_python_missing_or_not_executable"
    assert not Path(result["script_path"]).exists()
    assert not Path(result["launch_agent_path"]).exists()


def test_local_scheduler_status_requires_launchd_loaded_probe(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.supervision_scheduler")
    local = importlib.import_module("med_autoscience.controllers.supervision_scheduler_parts.local_adapter")
    profile = make_profile(tmp_path)
    _write_workspace_python(profile)
    launch_agents = tmp_path / "LaunchAgents"
    monkeypatch.setattr(local.platform, "system", lambda: "Darwin")
    monkeypatch.setenv("MAS_LAUNCHD_AGENTS_DIR", str(launch_agents))

    local._ensure_tick_script(profile=profile, interval_seconds=300)
    plist_path = local._launch_agent_path(profile)
    plist_path.parent.mkdir(parents=True, exist_ok=True)
    plist_path.write_bytes(local.plistlib.dumps(local._launch_agent_plist(profile=profile, interval_seconds=300)))
    monkeypatch.setattr(
        local,
        "_run_command",
        lambda command: {"command": command, "exit_code": 113, "output": "Could not find service"},
    )

    result = module.read_supervision_status(profile=profile, manager="local")

    assert result["status"] == "not_loaded"
    assert result["loaded"] is False
    assert result["launch_agent_probe"]["loaded"] is False


def test_explicit_hermes_adapter_is_projected_under_mas_scheduler_owner(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.supervision_scheduler")
    profile = make_profile(tmp_path)

    monkeypatch.setattr(
        module.hermes_supervision,
        "read_supervision_status",
        lambda **_: {
            "schema_version": 1,
            "surface_kind": "workspace_runtime_supervision",
            "owner": "hermes_gateway_cron",
            "status": "loaded",
            "loaded": True,
            "job_name": "medautoscience-supervision-diabetes-abc12345",
            "watch_command": ["watch-runtime", "--interval-seconds", "300"],
        },
    )

    result = module.read_supervision_status(profile=profile, manager="hermes")

    assert result["scheduler_owner"] == "mas_supervision_scheduler"
    assert result["adapter_id"] == "hermes_gateway_cron"
    assert result["active_path_role"] == "standalone_local_diagnostic_migration_bridge"
    assert result["consumer_migration"]["replacement_owner"] == "one-person-lab"
    assert result["owner"] == "hermes_gateway_cron"
    assert result["workspace_key"] == "diabetes-abc12345"
    assert result["outer_supervision_slo"]["supervision_owner"] == "mas_supervision_scheduler"
    assert result["outer_supervision_slo"]["adapter_id"] == "hermes_gateway_cron"
    assert result["outer_supervision_slo"]["handoff"]["replacement_owner"] == "one-person-lab"
    assert result["outer_supervision_slo"]["consumer_migration"]["retirement_proof_required"] == [
        "opl_replacement_contract_available",
        "replacement_proof",
        "no_active_caller_proof",
        "no_forbidden_write",
        "focused_cli_status_tests",
        "git_diff_check",
    ]
