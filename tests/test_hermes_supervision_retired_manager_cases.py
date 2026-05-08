from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile


def _command_contains(command: list[str], *tokens: str) -> bool:
    needle = tuple(tokens)
    width = len(needle)
    return any(tuple(command[index : index + width]) == needle for index in range(0, len(command) - width + 1))


def test_ensure_supervision_returns_retired_for_cron_and_launchd_scheduler_surfaces(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.hermes_supervision")
    profile = make_profile(tmp_path)
    supervisor_scan = profile.workspace_root / "ops" / "medautoscience" / "bin" / "supervisor-scan"
    supervisor_scan.parent.mkdir(parents=True, exist_ok=True)
    supervisor_scan.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    supervisor_scan.chmod(0o755)
    supervisor_consume = profile.workspace_root / "ops" / "medautoscience" / "bin" / "supervisor-consume"
    supervisor_consume.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    supervisor_consume.chmod(0o755)
    monkeypatch.setattr(
        module,
        "_github_user_login_check",
        lambda: {
            "status": "failed",
            "login": None,
            "expected_login": "gaofeng21cn",
            "matches_expected": False,
        },
    )

    cron_result = module.ensure_supervision(profile=profile, manager="cron", trigger_now=False)
    launchd_result = module.ensure_supervision(profile=profile, manager="launchd", trigger_now=False)

    for result in (cron_result, launchd_result):
        assert result["action"] == "retired_workspace_local_service_manager"
        assert result["status"] == "retired_fail_closed"
        assert result["canonical_owner"] == "hermes_gateway_cron"
        assert result["templates"] == {}
        assert result["install_commands"] == []
        assert result["installed"] is False
        assert result["supervisor_scan_entry"]["exists"] is True
        assert result["supervisor_consume_entry"]["exists"] is True
        assert result["codex_app_heartbeat_required"] is False


def test_ensure_supervision_docker_manager_is_retired_fail_closed(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.hermes_supervision")
    profile = make_profile(tmp_path)
    supervisor_scan = profile.workspace_root / "ops" / "medautoscience" / "bin" / "supervisor-scan"
    supervisor_scan.parent.mkdir(parents=True, exist_ok=True)
    supervisor_scan.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    supervisor_scan.chmod(0o755)
    monkeypatch.setattr(
        module,
        "_github_user_login_check",
        lambda: {
            "status": "ok",
            "login": "gaofeng21cn",
            "expected_login": "gaofeng21cn",
            "matches_expected": True,
            "gate": {"allowed": True, "login": "gaofeng21cn"},
        },
    )

    result = module.ensure_supervision(profile=profile, manager="docker", trigger_now=False)

    assert result["manager"] == "docker"
    assert result["action"] == "retired_workspace_local_service_manager"
    assert result["mode"] == "external_observe"
    assert result["mode_source"] == "retired_workspace_local_service_manager"
    assert result["scheduler_owner"] == "retired_docker_scheduler"
    assert result["safe_actions_enabled"] is False
    assert result["templates"] == {}
    assert result["install_proof"]["status"] == "retired_fail_closed"
    assert "docker run" not in "\n".join(result["install_commands"])
    assert result["install_commands"] == []


def test_remove_supervision_removes_jobs_and_script(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.hermes_supervision")
    profile = make_profile(tmp_path)
    script_path = module._script_path(profile)
    script_path.parent.mkdir(parents=True, exist_ok=True)
    script_path.write_text("#!/usr/bin/env python3\n", encoding="utf-8")
    jobs_path = profile.hermes_home_root / "cron" / "jobs.json"
    jobs_path.parent.mkdir(parents=True, exist_ok=True)
    jobs_path.write_text(
        json.dumps(
            [
                {
                    "id": "job-remove",
                    "name": module._job_name(profile),
                    "prompt": module._SILENT_PROMPT,
                    "deliver": "local",
                    "script": module._script_relpath(profile),
                    "schedule": {"kind": "interval", "minutes": 5},
                    "schedule_display": "every 5m",
                    "enabled": True,
                    "state": "scheduled",
                    "next_run_at": "2026-04-17T12:10:00+08:00",
                    "created_at": "2026-04-17T12:00:00+08:00",
                }
            ],
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        module,
        "inspect_hermes_runtime_contract",
        lambda **_: {
            "ready": True,
            "issues": [],
            "gateway_service_manager": "launchd",
            "gateway_service_label": "ai.hermes.gateway",
            "gateway_service_loaded": True,
        },
    )

    def fake_run_command(*, command: list[str]) -> tuple[int, str]:
        if _command_contains(command, "cron", "remove"):
            jobs_path.write_text("[]\n", encoding="utf-8")
            return 0, "Removed job: job-remove"
        return 0, "ok"

    monkeypatch.setattr(module, "_run_command", fake_run_command)

    result = module.remove_supervision(profile=profile)

    assert result["removed_job_ids"] == ["job-remove"]
    assert result["script_removed"] is True
    assert result["after"]["status"] == "not_installed"
    assert not script_path.exists()
