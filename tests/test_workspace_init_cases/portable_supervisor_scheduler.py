from __future__ import annotations

import importlib
import os
from pathlib import Path


def test_init_workspace_creates_watch_runtime_service_scripts(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_init")
    workspace_root = tmp_path / "lung-workspace"

    module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="lung",
        dry_run=False,
        force=False,
    )

    runner = workspace_root / "ops" / "medautoscience" / "bin" / "watch-runtime-service-runner"
    install_service = workspace_root / "ops" / "medautoscience" / "bin" / "install-watch-runtime-service"
    service_status = workspace_root / "ops" / "medautoscience" / "bin" / "watch-runtime-service-status"
    uninstall_service = workspace_root / "ops" / "medautoscience" / "bin" / "uninstall-watch-runtime-service"

    for path in (runner, install_service, service_status, uninstall_service):
        assert path.is_file()
        assert os.access(path, os.X_OK)

    runner_text = runner.read_text(encoding="utf-8")
    assert 'WATCH_RUNTIME_INTERVAL_SECONDS="${WATCH_RUNTIME_INTERVAL_SECONDS:-3600}"' in runner_text
    assert 'SUPERVISOR_SCAN_INTERVAL_SECONDS="${SUPERVISOR_SCAN_INTERVAL_SECONDS:-3600}"' in runner_text
    assert 'WATCH_RUNTIME_SCRIPT="${WORKSPACE_ROOT}/ops/medautoscience/bin/watch-runtime"' in runner_text
    assert 'SUPERVISOR_SCAN_SCRIPT="${WORKSPACE_ROOT}/ops/medautoscience/bin/supervisor-scan"' in runner_text
    assert 'exec "${SUPERVISOR_SCAN_SCRIPT}" --apply-safe-actions "$@"' in runner_text

    supervisor_scan = workspace_root / "ops" / "medautoscience" / "bin" / "supervisor-scan"
    assert supervisor_scan.is_file()
    assert os.access(supervisor_scan, os.X_OK)
    supervisor_scan_text = supervisor_scan.read_text(encoding="utf-8")
    assert "run_medautosci runtime supervisor-scan" in supervisor_scan_text
    assert '--profile "${PROFILE_PATH}"' in supervisor_scan_text

    install_text = install_service.read_text(encoding="utf-8")
    assert 'run_medautosci runtime ensure-supervision --profile "${PROFILE_PATH}" "$@"' in install_text
    assert "--manager systemd" in install_text
    assert "--manager cron" in install_text
    assert "--manager docker" in install_text

    status_text = service_status.read_text(encoding="utf-8")
    assert 'run_medautosci runtime supervision-status --profile "${PROFILE_PATH}" "$@"' in status_text

    uninstall_text = uninstall_service.read_text(encoding="utf-8")
    assert 'run_medautosci runtime remove-supervision --profile "${PROFILE_PATH}" "$@"' in uninstall_text


def test_init_workspace_renders_portable_supervisor_scheduler_templates(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_init")
    workspace_root = tmp_path / "supervisor-template-workspace"

    module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="supervisor-template",
        dry_run=False,
        force=False,
    )

    templates_root = workspace_root / "ops" / "medautoscience" / "supervisor"
    systemd_service = templates_root / "systemd" / "medautoscience-supervisor-scan.service"
    systemd_timer = templates_root / "systemd" / "medautoscience-supervisor-scan.timer"
    cron_template = templates_root / "cron" / "supervisor-scan.cron"
    docker_template = templates_root / "docker" / "supervisor-scan.oneshot.sh"
    k8s_template = templates_root / "kubernetes" / "supervisor-scan-cronjob.yaml"
    launchd_instructions = templates_root / "launchd" / "README.md"

    for path in (
        systemd_service,
        systemd_timer,
        cron_template,
        docker_template,
        k8s_template,
        launchd_instructions,
    ):
        assert path.is_file()

    systemd_service_text = systemd_service.read_text(encoding="utf-8")
    systemd_timer_text = systemd_timer.read_text(encoding="utf-8")
    cron_text = cron_template.read_text(encoding="utf-8")
    docker_text = docker_template.read_text(encoding="utf-8")
    k8s_text = k8s_template.read_text(encoding="utf-8")
    launchd_text = launchd_instructions.read_text(encoding="utf-8")

    assert f"WorkingDirectory={workspace_root}" in systemd_service_text
    assert f"ExecStart={workspace_root}/ops/medautoscience/bin/supervisor-scan --apply-safe-actions" in systemd_service_text
    assert "OnCalendar=hourly" in systemd_timer_text
    assert f"{workspace_root}/ops/medautoscience/bin/supervisor-scan --apply-safe-actions" in cron_text
    assert "docker run --rm" in docker_text
    assert "supervisor-scan --apply-safe-actions" in docker_text
    assert "kind: CronJob" in k8s_text
    assert 'schedule: "0 * * * *"' in k8s_text
    assert "supervisor-scan" in k8s_text
    assert "launchd" in launchd_text
    assert "install-watch-runtime-service --manager launchd" in launchd_text
    assert "Codex App heartbeat" not in "\n".join(
        path.read_text(encoding="utf-8")
        for path in (systemd_service, systemd_timer, cron_template, docker_template, k8s_template)
    )
