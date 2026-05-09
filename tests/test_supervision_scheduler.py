from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile


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
    assert result["dry_run"] is True
    assert result["install_proof"]["installed"] is False
    assert result["install_proof"]["tick_script_path"].endswith("watch_runtime_tick.py")
    assert result["after"]["adapter_id"] == "local_launchd"
    assert not Path(result["script_path"]).exists()


def test_local_scheduler_apply_writes_tick_script_plist_and_receipt(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.supervision_scheduler")
    local = importlib.import_module("med_autoscience.controllers.supervision_scheduler_parts.local_adapter")
    profile = make_profile(tmp_path)
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
    assert result["after"]["latest_run_recorded_at"] == "2026-05-09T00:00:01+00:00"
    assert Path(result["script_path"]).is_file()
    assert Path(result["launch_agent_path"]).is_file()
    assert Path(result["install_proof_path"]).is_file()
    script = Path(result["script_path"]).read_text(encoding="utf-8")
    assert "watch-runtime" in script
    assert "supervisor-scan" in script
    assert "supervisor-consume" in script
    assert "supervisor-execute-dispatch" in script
    assert any(command[:2] == ["launchctl", "bootstrap"] for command in commands)
    assert any(command[:2] == ["launchctl", "print"] for command in commands)
    assert any(command and command[0].endswith("watch_runtime_tick.py") for command in commands)


def test_local_scheduler_status_requires_launchd_loaded_probe(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.supervision_scheduler")
    local = importlib.import_module("med_autoscience.controllers.supervision_scheduler_parts.local_adapter")
    profile = make_profile(tmp_path)
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
    assert result["owner"] == "hermes_gateway_cron"
    assert result["workspace_key"] == "diabetes-abc12345"
    assert result["outer_supervision_slo"]["supervision_owner"] == "mas_supervision_scheduler"
    assert result["outer_supervision_slo"]["adapter_id"] == "hermes_gateway_cron"
