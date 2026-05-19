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
    assert "MAS scheduler local adapter runtime supervision 已在线" in result["summary"]
    slo = result["outer_supervision_slo"]
    assert slo["surface_kind"] == "outer_supervision_slo"
    assert slo["state"] == "missing"
    assert slo["canonical_one_shot_reconcile_domain_routes_command"] == (
        "uv run python -m med_autoscience.cli domain-route-reconcile "
        "--profile '<profile>' --mode developer_apply_safe --dry-run"
    )


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
    assert result["outer_supervision_slo"]["state"] == "blocked"
    assert "latest_scheduler_tick_execution_failed" in result["outer_supervision_slo"]["blocked_reasons"]
    assert "latest_hermes_cron_execution_failed" in result["outer_supervision_slo"]["blocked_reasons"]


def test_outer_supervision_slo_projects_fresh_due_stale_missing_and_blocked(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.outer_supervision_slo")
    profile = make_profile(tmp_path)
    base_status = {
        "owner": "hermes_gateway_cron",
        "status": "loaded",
        "watch_command": ["watch-runtime", "--interval-seconds", "300"],
    }

    fresh = module.build_outer_supervision_slo_projection(
        profile=profile,
        profile_ref="/workspace/profile.toml",
        study_id="001-risk",
        supervision_status={**base_status, "latest_run_recorded_at": "2026-05-08T01:00:00+00:00"},
        generated_at="2026-05-08T01:05:00+00:00",
    )
    due = module.build_outer_supervision_slo_projection(
        profile=profile,
        profile_ref="/workspace/profile.toml",
        study_id="001-risk",
        supervision_status={**base_status, "latest_run_recorded_at": "2026-05-08T00:49:00+00:00"},
        generated_at="2026-05-08T01:05:00+00:00",
    )
    stale = module.build_outer_supervision_slo_projection(
        profile=profile,
        profile_ref="/workspace/profile.toml",
        study_id="001-risk",
        supervision_status={**base_status, "latest_run_recorded_at": "2026-05-08T00:40:00+00:00"},
        generated_at="2026-05-08T01:05:00+00:00",
    )
    missing = module.build_outer_supervision_slo_projection(
        profile=profile,
        profile_ref="/workspace/profile.toml",
        study_id="001-risk",
        supervision_status=base_status,
        generated_at="2026-05-08T01:05:00+00:00",
    )
    blocked = module.build_outer_supervision_slo_projection(
        profile=profile,
        supervision_status={**base_status, "status": "retired_legacy_service_present"},
        generated_at="2026-05-08T01:05:00+00:00",
    )

    assert fresh["state"] == "fresh"
    assert fresh["recommended_command"] is None
    assert fresh["action_class"] == "observe_only"
    assert fresh["will_start_llm"] is False
    assert due["state"] == "due"
    assert due["action_class"] == "reconcile_dry_run"
    assert due["will_start_llm"] is False
    assert due["active_path_role"] == "legacy_scheduler_diagnostic_cleanup_only"
    assert due["consumer_migration"]["replacement_owner"] == "one-person-lab"
    assert due["consumer_migration"]["replacement_owner_surface"] == "opl_provider_runtime_manager"
    assert due["consumer_migration"]["current_surface_allowed_until_replacement"] is False
    assert due["consumer_migration"]["allowed_operations"] == ["status", "remove_legacy_jobs"]
    assert set(due["consumer_migration"]["forbidden_operations"]) == {
        "ensure",
        "create",
        "edit",
        "resume",
        "trigger_run",
        "write_tick_script",
    }
    assert due["handoff"]["current_mas_surface_role"] == "legacy_scheduler_diagnostic_cleanup_only"
    assert stale["state"] == "stale"
    assert missing["state"] == "missing"
    assert blocked["state"] == "blocked"
    assert due["recommended_command"] == (
        "uv run python -m med_autoscience.cli domain-route-reconcile "
        "--profile /workspace/profile.toml --studies 001-risk --mode developer_apply_safe --dry-run"
    )


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


def test_read_supervision_status_blocks_on_retired_workspace_local_service_when_loaded(
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

    assert result["status"] == "retired_legacy_service_present"
    assert result["loaded"] is False
    assert "retired_legacy_service_loaded" in result["drift_reasons"]
    assert result["legacy_service"]["loaded"] is True
    assert result["legacy_service_role"] == "retired_cleanup_evidence"
    assert result["retired_legacy_cleanup_required"] is True
    assert "已退役的 workspace-local runtime supervision service" in result["summary"]


def test_read_supervision_status_keeps_hermes_blocked_until_retired_legacy_service_is_cleaned(
    monkeypatch, tmp_path: Path
) -> None:
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
                    "id": "job-legacy-conflict",
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
    monkeypatch.setattr(
        module,
        "_read_legacy_service_status",
        lambda profile: {
            "manager": "launchd",
            "service_label": "ai.medautoscience.diabetes.watch-runtime",
            "service_file": str(tmp_path / "Library" / "LaunchAgents" / "legacy.plist"),
            "service_exists": True,
            "loaded": False,
        },
    )

    result = module.read_supervision_status(profile=profile)

    assert result["status"] == "retired_legacy_service_present"
    assert result["loaded"] is False
    assert result["job_id"] == "job-legacy-conflict"
    assert "retired_legacy_service_present" in result["drift_reasons"]
    assert result["retired_legacy_cleanup_required"] is True


def test_ensure_supervision_is_retired_and_does_not_remove_or_create_jobs(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.hermes_supervision")
    profile = make_profile(tmp_path)
    commands: list[list[str]] = []

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

    def fake_remove_legacy_service(profile) -> dict[str, object]:
        raise AssertionError("Hermes ensure must not clean or mutate legacy services")

    def fake_run_command(*, command: list[str]) -> tuple[int, str]:
        commands.append(command)
        raise AssertionError(f"Hermes ensure must not run commands: {command}")

    monkeypatch.setattr(module, "_remove_legacy_service", fake_remove_legacy_service)
    monkeypatch.setattr(module, "_run_command", fake_run_command)

    result = module.ensure_supervision(profile=profile, trigger_now=False)

    assert result["action"] == "retired_ensure_path"
    assert result["before"]["status"] == "retired_legacy_service_present"
    assert result["after"] == result["before"]
    assert result["install_allowed"] is False
    assert result["trigger_allowed"] is False
    assert result["write_tick_script_allowed"] is False
    assert result["legacy_removal"] is None
    assert result["command_outputs"] == []
    assert commands == []


def test_ensure_supervision_does_not_create_job_or_trigger_run(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.hermes_supervision")
    profile = make_profile(tmp_path)
    commands: list[list[str]] = []

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
        raise AssertionError(f"Hermes ensure must not run commands: {command}")

    monkeypatch.setattr(module, "_run_command", fake_run_command)

    result = module.ensure_supervision(profile=profile)

    assert result["action"] == "retired_ensure_path"
    assert result["before"]["job_exists"] is False
    assert result["after"] == result["before"]
    assert result["install_allowed"] is False
    assert result["trigger_allowed"] is False
    assert result["write_tick_script_allowed"] is False
    assert not module._script_path(profile).exists()
    assert commands == []


def test_remove_supervision_cleans_existing_hermes_job_and_script(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.hermes_supervision")
    profile = make_profile(tmp_path)
    commands: list[list[str]] = []
    jobs_path = profile.hermes_home_root / "cron" / "jobs.json"
    script_path = module._script_path(profile)
    script_path.parent.mkdir(parents=True, exist_ok=True)
    script_path.write_text("# legacy script\n", encoding="utf-8")
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
        assert _command_contains(command, "cron", "remove")
        jobs_path.write_text("[]\n", encoding="utf-8")
        return 0, "Removed job: job-existing"

    monkeypatch.setattr(module, "_run_command", fake_run_command)

    result = module.remove_supervision(profile=profile)

    assert result["removed_job_ids"] == ["job-existing"]
    assert result["script_removed"] is True
    assert not script_path.exists()
    assert any(_command_contains(command, "cron", "remove") for command in commands)


def test_ensure_supervision_does_not_repair_legacy_watch_runtime_or_trigger_run(
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
        raise AssertionError(f"Hermes ensure must not run commands: {command}")

    monkeypatch.setattr(module, "_run_command", fake_run_command)

    result = module.ensure_supervision(profile=profile)

    assert result["action"] == "retired_ensure_path"
    assert 'run_medautosci watch \\' in watch_runtime.read_text(encoding="utf-8")
    assert "run_medautosci runtime watch" not in watch_runtime.read_text(encoding="utf-8")
    assert result["command_outputs"] == []
    assert commands == []


def test_codex_app_automation_prompt_check_reports_missing_tokens(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.hermes_supervision")
    automation_path = tmp_path / "automation.toml"
    automation_path.write_text(
        'status = "ACTIVE"\n'
        'prompt = "developer_apply_safe mode=developer_apply_safe domain-route-scan --apply-safe-actions '
        '--developer-supervisor-mode developer_apply_safe"\n',
        encoding="utf-8",
    )

    result = module._codex_app_automation_prompt_check(automation_path=automation_path)

    assert result["status"] == "incomplete"
    assert result["active"] is True
    assert result["missing_prompt_tokens"] == [
        "domain-route-reconcile --mode developer_apply_safe --apply",
        "--apply-runtime-platform-repair",
        "domain-action-request-materialize --mode developer_apply_safe --apply",
        "domain-owner-action-dispatch --mode developer_apply_safe --apply",
        "workspace_dynamic_active_studies",
        "new MAS tasks",
        "active_run_id",
        "worker_running",
        "worktree",
        "action_queue",
        "why_not_applied",
        "OPL family user config",
        "study-runtime-status",
        "study-progress",
        "runtime_supervision/latest",
        "runtime_watch/latest",
        "controller_decisions/latest",
        "publication_eval/latest",
        "gate_clearing_batch/latest",
        "paper-facing artifact delta",
        "publication gate blocker",
        "controller/route/work_unit",
        "MAS repo/controller/runtime root cause",
        "不得手工改论文包或 runtime-owned surfaces",
    ]
    assert result["recommended_prompt"] == module._canonical_codex_app_automation_prompt()
    assert "workspace_dynamic_active_studies" in result["recommended_prompt"]
    assert "MAS repo/controller/runtime root cause" in result["recommended_prompt"]
    assert "不得手工改论文包或 runtime-owned surfaces" in result["recommended_prompt"]


def test_codex_app_automation_prompt_check_rejects_study_allowlist_only_prompt(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.hermes_supervision")
    automation_path = tmp_path / "automation.toml"
    automation_path.write_text(
        'status = "ACTIVE"\n'
        'prompt = "developer_apply_safe mode=developer_apply_safe domain-route-scan --apply-safe-actions '
        '--apply-runtime-platform-repair --developer-supervisor-mode developer_apply_safe '
        'domain-action-request-materialize --mode developer_apply_safe --apply '
        'domain-owner-action-dispatch --mode developer_apply_safe --apply '
        'study_ids=002-dm-china-us-mortality-attribution,003-dpcc-primary-care-phenotype-treatment-gap '
        'action_queue why_not_applied"\n',
        encoding="utf-8",
    )

    result = module._codex_app_automation_prompt_check(automation_path=automation_path)

    assert result["status"] == "incomplete"
    assert result["active"] is True
    assert result["scope_policy"] == "workspace_dynamic_active_studies"
    assert result["new_task_auto_enrollment_required"] is True
    assert result["missing_prompt_tokens"] == [
        "domain-route-reconcile --mode developer_apply_safe --apply",
        "workspace_dynamic_active_studies",
        "new MAS tasks",
        "active_run_id",
        "worker_running",
        "worktree",
        "OPL family user config",
        "study-runtime-status",
        "study-progress",
        "runtime_supervision/latest",
        "runtime_watch/latest",
        "controller_decisions/latest",
        "publication_eval/latest",
        "gate_clearing_batch/latest",
        "paper-facing artifact delta",
        "publication gate blocker",
        "controller/route/work_unit",
        "MAS repo/controller/runtime root cause",
        "不得手工改论文包或 runtime-owned surfaces",
    ]


def test_codex_app_automation_prompt_check_accepts_canonical_prompt(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.hermes_supervision")
    automation_path = tmp_path / "automation.toml"
    automation_path.write_text(
        'status = "ACTIVE"\n'
        f'prompt = """{module._canonical_codex_app_automation_prompt()}"""\n',
        encoding="utf-8",
    )

    result = module._codex_app_automation_prompt_check(automation_path=automation_path)

    assert result["status"] == "ok"
    assert result["active"] is True
    assert result["missing_prompt_tokens"] == []
    assert result["canonical_prompt"] == module._canonical_codex_app_automation_prompt()
