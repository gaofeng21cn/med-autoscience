from __future__ import annotations

import importlib
import json
import subprocess
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


def test_ensure_supervision_returns_portable_scheduler_install_instructions(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.hermes_supervision")
    profile = make_profile(tmp_path)
    supervisor_scan = profile.workspace_root / "ops" / "medautoscience" / "bin" / "supervisor-scan"
    supervisor_scan.parent.mkdir(parents=True, exist_ok=True)
    supervisor_scan.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    supervisor_scan.chmod(0o755)
    supervisor_consume = profile.workspace_root / "ops" / "medautoscience" / "bin" / "supervisor-consume"
    supervisor_consume.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    supervisor_consume.chmod(0o755)
    service_template = (
        profile.workspace_root
        / "ops"
        / "medautoscience"
        / "supervisor"
        / "systemd"
        / "medautoscience-supervisor-scan.service"
    )
    timer_template = service_template.with_suffix(".timer")
    service_template.parent.mkdir(parents=True, exist_ok=True)
    service_template.write_text("[Service]\n", encoding="utf-8")
    timer_template.write_text("[Timer]\n", encoding="utf-8")

    result = module.ensure_supervision(profile=profile, manager="systemd", trigger_now=False)

    assert result["action"] == "portable_scheduler_instruction"
    assert result["manager"] == "systemd"
    assert result["installed"] is False
    assert result["codex_app_heartbeat_required"] is False
    assert result["supervisor_scan_entry"]["exists"] is True
    assert result["supervisor_scan_entry"]["executable"] is True
    assert result["supervisor_scan_entry"]["path"] == str(supervisor_scan)
    assert result["supervisor_consume_entry"]["exists"] is True
    assert result["supervisor_consume_entry"]["executable"] is True
    assert result["supervisor_consume_entry"]["path"] == str(supervisor_consume)
    assert result["templates"]["service"] == str(service_template)
    assert result["templates"]["timer"] == str(timer_template)
    assert result["install_commands"] == [
        f"mkdir -p {Path.home() / '.config' / 'systemd' / 'user'}",
        f"cp {service_template} {Path.home() / '.config' / 'systemd' / 'user' / service_template.name}",
        f"cp {timer_template} {Path.home() / '.config' / 'systemd' / 'user' / timer_template.name}",
        "systemctl --user daemon-reload",
        f"systemctl --user enable --now {timer_template.name}",
    ]


def test_ensure_supervision_returns_developer_supervisor_mode_proof_for_portable_manager(
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
    supervisor_execute_dispatch = profile.workspace_root / "ops" / "medautoscience" / "bin" / "supervisor-execute-dispatch"
    supervisor_execute_dispatch.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    supervisor_execute_dispatch.chmod(0o755)
    service_template = (
        profile.workspace_root
        / "ops"
        / "medautoscience"
        / "supervisor"
        / "systemd"
        / "medautoscience-supervisor-scan.service"
    )
    timer_template = service_template.with_suffix(".timer")
    service_template.parent.mkdir(parents=True, exist_ok=True)
    service_template.write_text("[Service]\n", encoding="utf-8")
    timer_template.write_text("[Timer]\n", encoding="utf-8")
    automation_path = tmp_path / "home" / ".codex" / "automations" / "mas" / "automation.toml"
    automation_path.parent.mkdir(parents=True, exist_ok=True)
    automation_path.write_text(
        'status = "ACTIVE"\n'
        'prompt = """developer_apply_safe\n'
        "mode=developer_apply_safe\n"
        "supervisor-scan --apply-safe-actions\n"
        "--developer-supervisor-mode developer_apply_safe\n"
        "supervisor-consume --mode developer_apply_safe --apply\n"
        "supervisor-execute-dispatch --mode developer_apply_safe --apply\n"
        "action_queue\n"
        "why_not_applied\n"
        '"""\n',
        encoding="utf-8",
    )

    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    monkeypatch.setattr(module, "_codex_app_automation_path", lambda: automation_path)

    result = module.ensure_supervision(profile=profile, manager="systemd", trigger_now=False)

    assert result["mode"] == "developer_apply_safe"
    assert result["requested_mode"] == "developer_apply_safe"
    assert result["mode_source"] == "github_user_gate"
    assert result["developer_mode_enabled"] is True
    assert result["safe_actions_enabled"] is True
    assert result["repo_level_repair_authority"] is True
    assert result["scheduler_owner"] == "systemd_scheduler"
    assert result["github_user"]["login"] == "gaofeng21cn"
    assert result["github_user"]["matches_expected"] is True
    assert result["github_user_gate"]["allowed"] is True
    assert result["codex_app_heartbeat_required"] is False
    assert result["codex_app_automation_prompt"]["active"] is True
    assert result["codex_app_automation_prompt"]["missing_prompt_tokens"] == []
    assert result["install_proof"]["status"] == "ready"
    assert result["install_proof"]["status_check_commands"] == [
        [
            str(supervisor_scan),
            "--apply-safe-actions",
            "--developer-supervisor-mode",
            "developer_apply_safe",
        ],
        [
            str(supervisor_consume),
            "--mode",
            "developer_apply_safe",
            "--apply",
        ],
        [
            str(supervisor_execute_dispatch),
            "--mode",
            "developer_apply_safe",
            "--apply",
        ],
        [str(supervisor_scan), "--status"],
    ]
    assert result["status_check_commands"] == result["install_proof"]["status_check_commands"]
    assert result["expected_artifacts"] == result["install_proof"]["expected_artifacts"]
    assert result["freshness"]["codex_app_heartbeat_required"] is False
    assert result["freshness"]["max_expected_artifact_age_seconds"] == 600


def test_ensure_supervision_writes_portable_install_proof_when_explicitly_requested(
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
    cron_template = (
        profile.workspace_root
        / "ops"
        / "medautoscience"
        / "supervisor"
        / "cron"
        / "supervisor-scan.cron"
    )
    cron_template.parent.mkdir(parents=True, exist_ok=True)
    cron_template.write_text("* * * * * supervisor-scan\n", encoding="utf-8")

    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")

    result = module.ensure_supervision(
        profile=profile,
        manager="cron",
        trigger_now=False,
        write_install_proof=True,
    )

    proof_path = profile.workspace_root / "artifacts" / "supervision" / "install_proof" / "latest.json"
    proof = json.loads(proof_path.read_text(encoding="utf-8"))
    assert result["install_proof_path"] == str(proof_path)
    assert result["install_proof"]["artifact_path"] == str(proof_path)
    assert proof["manager"] == "cron"
    assert proof["scheduler_owner"] == "cron_scheduler"
    assert proof["install_commands"] == result["install_commands"]
    assert proof["status_check_commands"] == result["status_check_commands"]
    assert proof["expected_artifacts"] == result["expected_artifacts"]
    assert proof["artifact_path"] == str(proof_path)
    assert proof["last_scan_time"] is not None
    assert proof["freshness"]["max_expected_artifact_age_seconds"] == 600
    assert proof["safe_action_mode"] == "developer_apply_safe"
    assert proof["github_gate"]["allowed"] is True
    assert proof["host_service_claim"] == "not_installed_by_mas"
    assert proof["status"] != "installed"


def test_ensure_supervision_projects_codex_app_heartbeat_as_compat_owner(
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
    automation_path = tmp_path / "home" / ".codex" / "automations" / "mas" / "automation.toml"
    automation_path.parent.mkdir(parents=True, exist_ok=True)
    automation_path.write_text(
        'status = "ACTIVE"\n'
        'prompt = "developer_apply_safe mode=developer_apply_safe supervisor-scan --apply-safe-actions '
        '--developer-supervisor-mode developer_apply_safe supervisor-consume --mode developer_apply_safe --apply '
        'supervisor-execute-dispatch --mode developer_apply_safe --apply '
        'action_queue why_not_applied"\n',
        encoding="utf-8",
    )

    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    monkeypatch.setattr(module, "_codex_app_automation_path", lambda: automation_path)

    result = module.ensure_supervision(profile=profile, manager="codex_app", trigger_now=False)

    assert result["manager"] == "codex_app"
    assert result["scheduler_owner"] == "codex_app_compat"
    assert result["install_proof"]["scheduler_owner"] == "codex_app_compat"


def test_ensure_supervision_disables_developer_mode_for_non_owner_github_user(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.hermes_supervision")
    profile = make_profile(tmp_path)
    automation_path = tmp_path / "home" / ".codex" / "automations" / "mas" / "automation.toml"
    automation_path.parent.mkdir(parents=True, exist_ok=True)
    automation_path.write_text(
        '[[automations]]\n'
        'status = "ACTIVE"\n'
        'prompt = "developer_apply_safe mode=developer_apply_safe supervisor-scan --apply-safe-actions '
        '--developer-supervisor-mode developer_apply_safe supervisor-consume --mode developer_apply_safe --apply '
        'supervisor-execute-dispatch --mode developer_apply_safe --apply '
        'action_queue why_not_applied"\n',
        encoding="utf-8",
    )

    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "someone-else")
    monkeypatch.setattr(module, "_codex_app_automation_path", lambda: automation_path)

    result = module.ensure_supervision(profile=profile, manager="cron", trigger_now=False)

    assert result["mode"] == "external_observe"
    assert result["developer_mode_enabled"] is False
    assert result["safe_actions_enabled"] is False
    assert result["repo_level_repair_authority"] is False
    assert result["github_user"]["login"] == "someone-else"
    assert result["github_user"]["matches_expected"] is False
    assert result["github_user_gate"]["allowed"] is False
    assert result["install_proof"]["status"] == "developer_mode_disabled"
    assert result["codex_app_heartbeat_required"] is False


def test_codex_app_automation_prompt_check_reports_missing_tokens(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.hermes_supervision")
    automation_path = tmp_path / "automation.toml"
    automation_path.write_text(
        'status = "ACTIVE"\n'
        'prompt = "developer_apply_safe mode=developer_apply_safe supervisor-scan --apply-safe-actions '
        '--developer-supervisor-mode developer_apply_safe"\n',
        encoding="utf-8",
    )

    result = module._codex_app_automation_prompt_check(automation_path=automation_path)

    assert result["status"] == "incomplete"
    assert result["active"] is True
    assert result["missing_prompt_tokens"] == [
        "supervisor-consume --mode developer_apply_safe --apply",
        "supervisor-execute-dispatch --mode developer_apply_safe --apply",
        "action_queue",
        "why_not_applied",
    ]


def test_ensure_supervision_returns_cron_and_launchd_scheduler_surfaces(
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
    templates_root = profile.workspace_root / "ops" / "medautoscience" / "supervisor"
    for path in (
        templates_root / "cron" / "supervisor-scan.cron",
        templates_root / "launchd" / "README.md",
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("template\n", encoding="utf-8")
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

    assert cron_result["templates"]["crontab"] == str(templates_root / "cron" / "supervisor-scan.cron")
    assert any("crontab" in command for command in cron_result["install_commands"])
    assert launchd_result["templates"]["instructions"] == str(templates_root / "launchd" / "README.md")
    assert launchd_result["install_commands"] == [
        f"{profile.workspace_root}/ops/medautoscience/bin/install-watch-runtime-service --manager launchd"
    ]
    for result in (cron_result, launchd_result):
        assert result["installed"] is False
        assert result["supervisor_scan_entry"]["exists"] is True
        assert result["supervisor_consume_entry"]["exists"] is True
        assert result["codex_app_heartbeat_required"] is False


def test_ensure_supervision_docker_manager_is_container_agnostic_fail_closed(
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
    assert result["mode"] == "external_observe"
    assert result["mode_source"] == "unsupported_container_scheduler"
    assert result["scheduler_owner"] == "external_container_scheduler"
    assert result["safe_actions_enabled"] is False
    assert result["templates"] == {}
    assert result["install_proof"]["status"] == "unsupported_container_scheduler"
    assert "docker run" not in "\n".join(result["install_commands"])
    assert "medautosci runtime supervisor-scan" in result["install_commands"][0]


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
