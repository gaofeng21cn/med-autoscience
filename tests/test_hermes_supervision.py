from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile


def _command_contains(command: list[str], *tokens: str) -> bool:
    needle = tuple(tokens)
    width = len(needle)
    return any(tuple(command[index : index + width]) == needle for index in range(0, len(command) - width + 1))


def test_read_supervision_status_reports_loaded_hermes_job(monkeypatch, tmp_path: Path) -> None:
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
                    "id": "job-001",
                    "name": module._job_name(profile),
                    "prompt": module._SILENT_PROMPT,
                    "deliver": "local",
                    "script": module._script_relpath(profile),
                    "schedule": {"kind": "interval", "minutes": 5},
                    "schedule_display": "every 5m",
                    "enabled": True,
                    "state": "scheduled",
                    "next_run_at": "2026-04-17T12:00:00+08:00",
                    "created_at": "2026-04-17T11:55:00+08:00",
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

    result = module.read_supervision_status(profile=profile)

    assert result["status"] == "loaded"
    assert result["loaded"] is True
    assert result["owner"] == "hermes_gateway_cron"
    assert result["job_id"] == "job-001"
    assert result["job_schedule_display"] == "every 5m"
    assert result["drift_reasons"] == []
    assert "Hermes-hosted runtime supervision 已在线" in result["summary"]


def test_read_supervision_status_reports_failed_latest_cron_run(monkeypatch, tmp_path: Path) -> None:
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
                    "id": "job-001",
                    "name": module._job_name(profile),
                    "prompt": module._SILENT_PROMPT,
                    "deliver": "local",
                    "script": module._script_relpath(profile),
                    "schedule": {"kind": "interval", "minutes": 5},
                    "schedule_display": "every 5m",
                    "enabled": True,
                    "state": "scheduled",
                    "next_run_at": "2026-04-17T12:00:00+08:00",
                    "created_at": "2026-04-17T11:55:00+08:00",
                }
            ],
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    session_path = profile.hermes_home_root / "sessions" / "session_cron_job-001_20260418_224328.json"
    session_path.parent.mkdir(parents=True, exist_ok=True)
    session_path.write_text(
        json.dumps(
            {
                "session_id": "cron_job-001_20260418_224328",
                "session_start": "2026-04-18T22:43:28.290627",
                "last_updated": "2026-04-18T22:43:47.848774",
                "messages": [
                    {
                        "role": "assistant",
                        "content": (
                            "MedAutoScience data-collection script failed.\n\n"
                            "Failing command:\n```bash\nwatch-runtime --interval-seconds 300 --max-ticks 1\n```"
                        ),
                    }
                ],
            },
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

    result = module.read_supervision_status(profile=profile)

    assert result["status"] == "execution_failed"
    assert result["loaded"] is False
    assert result["latest_run_status"] == "failed"
    assert result["latest_run_session_path"] == str(session_path)
    assert "最近一次 cron 执行失败" in result["summary"]


def test_read_supervision_status_accepts_object_jobs_store_payload(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.hermes_supervision")
    profile = make_profile(tmp_path)
    script_path = module._script_path(profile)
    script_path.parent.mkdir(parents=True, exist_ok=True)
    script_path.write_text("#!/usr/bin/env python3\n", encoding="utf-8")

    jobs_path = profile.hermes_home_root / "cron" / "jobs.json"
    jobs_path.parent.mkdir(parents=True, exist_ok=True)
    jobs_path.write_text(
        json.dumps(
            {
                "jobs": [
                    {
                        "id": "job-002",
                        "name": module._job_name(profile),
                        "prompt": module._SILENT_PROMPT,
                        "deliver": "local",
                        "script": module._script_relpath(profile),
                        "schedule": {"kind": "interval", "minutes": 5, "display": "every 5m"},
                        "schedule_display": "every 5m",
                        "enabled": True,
                        "state": "scheduled",
                        "next_run_at": "2026-04-18T09:16:14.132356+08:00",
                        "created_at": "2026-04-18T09:11:14.132333+08:00",
                    }
                ],
                "updated_at": "2026-04-18T09:11:14.132850+08:00",
            },
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

    result = module.read_supervision_status(profile=profile)

    assert result["status"] == "loaded"
    assert result["loaded"] is True
    assert result["job_id"] == "job-002"
    assert result["drift_reasons"] == []


def test_hermes_cli_command_prefers_managed_python_when_available(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.hermes_supervision")
    profile = make_profile(tmp_path)
    managed_python = tmp_path / "_external" / "hermes-agent" / ".venv" / "bin" / "python"

    monkeypatch.setattr(
        module,
        "inspect_hermes_runtime_contract",
        lambda **_: {
            "managed_python_path": str(managed_python),
            "managed_python_exists": True,
        },
    )

    command = module._hermes_cli_command(profile, "cron", "create")

    assert command == [
        str(managed_python),
        str((profile.hermes_agent_repo_root / "hermes").resolve()),
        "cron",
        "create",
    ]


def test_read_supervision_status_reports_legacy_only_when_workspace_local_service_still_loaded(
    monkeypatch, tmp_path: Path
) -> None:
    module = importlib.import_module("med_autoscience.controllers.hermes_supervision")
    profile = make_profile(tmp_path)

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
    monkeypatch.setattr(
        module,
        "_read_legacy_service_status",
        lambda profile: {
            "manager": "launchd",
            "service_label": "ai.medautoscience.diabetes.watch-runtime",
            "service_file": str(tmp_path / "Library" / "LaunchAgents" / "legacy.plist"),
            "service_exists": True,
            "loaded": True,
        },
    )

    result = module.read_supervision_status(profile=profile)

    assert result["status"] == "legacy_only"
    assert result["loaded"] is False
    assert "legacy_service_loaded" in result["drift_reasons"]
    assert result["legacy_service"]["loaded"] is True
    assert "legacy workspace-local runtime supervision service" in result["summary"]


def test_ensure_supervision_creates_job_and_triggers_run(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.hermes_supervision")
    profile = make_profile(tmp_path)
    commands: list[list[str]] = []
    jobs_path = profile.hermes_home_root / "cron" / "jobs.json"

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
        commands.append(command)
        if _command_contains(command, "cron", "create"):
            jobs_path.parent.mkdir(parents=True, exist_ok=True)
            jobs_path.write_text(
                json.dumps(
                    [
                        {
                            "id": "job-created",
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
            return 0, "Created job: job-created"
        if _command_contains(command, "cron", "run"):
            return 0, "Scheduled job: job-created"
        return 0, "ok"

    monkeypatch.setattr(module, "_run_command", fake_run_command)

    result = module.ensure_supervision(profile=profile)

    assert result["action"] == "created"
    assert result["after"]["job_id"] == "job-created"
    assert result["after"]["loaded"] is True
    assert module._script_path(profile).is_file()
    assert any(_command_contains(command, "cron", "create") for command in commands)
    assert any(_command_contains(command, "cron", "run") for command in commands)


def test_ensure_supervision_repairs_legacy_watch_runtime_entry_before_triggering_run(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.hermes_supervision")
    profile = make_profile(tmp_path)
    commands: list[list[str]] = []
    watch_runtime = profile.workspace_root / "ops" / "medautoscience" / "bin" / "watch-runtime"
    watch_runtime.parent.mkdir(parents=True, exist_ok=True)
    watch_runtime.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"\n\n'
        'WORKSPACE_RUNTIME_ROOT="${WORKSPACE_ROOT}/ops/med-deepscientist/runtime/quests"\n\n'
        'run_medautosci watch \\\n'
        '  --profile "${PROFILE_PATH}" \\\n'
        '  --runtime-root "${WORKSPACE_RUNTIME_ROOT}" \\\n'
        '  --ensure-study-runtimes \\\n'
        '  --apply \\\n'
        '  --loop \\\n'
        '  "$@"\n',
        encoding="utf-8",
    )
    jobs_path = profile.hermes_home_root / "cron" / "jobs.json"
    jobs_path.parent.mkdir(parents=True, exist_ok=True)
    jobs_path.write_text(
        json.dumps(
            [
                {
                    "id": "job-existing",
                    "name": module._job_name(profile),
                    "prompt": module._SILENT_PROMPT,
                    "deliver": "local",
                    "script": module._script_relpath(profile),
                    "schedule": {"kind": "interval", "minutes": 5},
                    "schedule_display": "every 5m",
                    "enabled": True,
                    "state": "scheduled",
                    "next_run_at": "2026-04-17T12:00:00+08:00",
                    "created_at": "2026-04-17T11:55:00+08:00",
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
        commands.append(command)
        return 0, "ok"

    monkeypatch.setattr(module, "_run_command", fake_run_command)

    result = module.ensure_supervision(profile=profile)

    assert result["watch_runtime_repair"]["repaired"] is True
    assert 'run_medautosci runtime watch \\' in watch_runtime.read_text(encoding="utf-8")
    assert any(_command_contains(command, "cron", "run") for command in commands)


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
