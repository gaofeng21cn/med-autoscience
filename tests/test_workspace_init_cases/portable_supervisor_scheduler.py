from __future__ import annotations

import importlib
import os
from pathlib import Path


DEVELOPER_SUPERVISOR_MODE_ARGS = "--apply-safe-actions --apply-runtime-platform-repair --developer-supervisor-mode developer_apply_safe"


def test_init_workspace_omits_retired_watch_runtime_service_wrappers(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_init")
    workspace_root = tmp_path / "lung-workspace"

    module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="lung",
        dry_run=False,
        force=False,
    )

    install_service = workspace_root / "ops" / "medautoscience" / "bin" / "install-watch-runtime-service"
    service_status = workspace_root / "ops" / "medautoscience" / "bin" / "watch-runtime-service-status"
    uninstall_service = workspace_root / "ops" / "medautoscience" / "bin" / "uninstall-watch-runtime-service"
    supervisor_reconcile = workspace_root / "ops" / "medautoscience" / "bin" / "supervisor-reconcile"
    supervisor_execute_dispatch = workspace_root / "ops" / "medautoscience" / "bin" / "supervisor-execute-dispatch"

    for path in (supervisor_reconcile, supervisor_execute_dispatch):
        assert path.is_file()
        assert os.access(path, os.X_OK)
    for path in (install_service, service_status, uninstall_service):
        assert not path.exists()
    assert not (workspace_root / "ops" / "medautoscience" / "bin" / "watch-runtime-service-runner").exists()

    supervisor_reconcile_text = supervisor_reconcile.read_text(encoding="utf-8")
    assert "run_medautosci runtime supervisor-reconcile" in supervisor_reconcile_text
    assert '--profile "${PROFILE_PATH}"' in supervisor_reconcile_text
    assert "--mode developer_apply_safe" in supervisor_reconcile_text
    assert "--apply" in supervisor_reconcile_text

    supervisor_scan = workspace_root / "ops" / "medautoscience" / "bin" / "supervisor-scan"
    assert supervisor_scan.is_file()
    assert os.access(supervisor_scan, os.X_OK)
    supervisor_scan_text = supervisor_scan.read_text(encoding="utf-8")
    assert "run_medautosci runtime supervisor-scan" in supervisor_scan_text
    assert '--profile "${PROFILE_PATH}"' in supervisor_scan_text

    supervisor_consume = workspace_root / "ops" / "medautoscience" / "bin" / "supervisor-consume"
    assert supervisor_consume.is_file()
    assert os.access(supervisor_consume, os.X_OK)
    supervisor_consume_text = supervisor_consume.read_text(encoding="utf-8")
    assert "run_medautosci runtime supervisor-consume" in supervisor_consume_text
    assert '--profile "${PROFILE_PATH}"' in supervisor_consume_text
    assert "--mode developer_apply_safe" in supervisor_consume_text
    assert "--apply" in supervisor_consume_text

    supervisor_execute_dispatch_text = supervisor_execute_dispatch.read_text(encoding="utf-8")
    assert "run_medautosci runtime supervisor-execute-dispatch" in supervisor_execute_dispatch_text
    assert '--profile "${PROFILE_PATH}"' in supervisor_execute_dispatch_text
    assert "--mode developer_apply_safe" in supervisor_execute_dispatch_text
    assert "--apply" in supervisor_execute_dispatch_text


def test_init_workspace_does_not_render_workspace_local_scheduler_templates(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_init")
    workspace_root = tmp_path / "supervisor-template-workspace"

    module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="supervisor-template",
        dry_run=False,
        force=False,
    )

    templates_root = workspace_root / "ops" / "medautoscience" / "supervisor"
    assert not templates_root.exists()
    assert not (workspace_root / "ops" / "medautoscience" / "bin" / "watch-runtime-service-runner").exists()
    assert not (templates_root / "systemd").exists()
    assert not (templates_root / "cron").exists()
    assert not (templates_root / "launchd").exists()
    assert not (templates_root / "docker").exists()
    assert not (templates_root / "kubernetes").exists()


def test_init_workspace_dry_run_reports_retired_service_wrapper_without_deleting(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_init")
    workspace_root = tmp_path / "dry-run-retired-wrapper"
    install_service = workspace_root / "ops" / "medautoscience" / "bin" / "install-watch-runtime-service"
    install_service.parent.mkdir(parents=True, exist_ok=True)
    install_service.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"\n\n'
        'run_medautosci runtime ensure-supervision --profile "${PROFILE_PATH}" "$@"\n',
        encoding="utf-8",
    )

    result = module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="dry-run-retired-wrapper",
        dry_run=True,
        force=False,
    )

    assert str(install_service) in result["removed_files"]
    assert str(install_service) not in result["retained_retired_files"]
    assert install_service.exists()


def test_init_workspace_retains_same_name_custom_service_file_without_retired_markers(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_init")
    workspace_root = tmp_path / "custom-service-file"
    install_service = workspace_root / "ops" / "medautoscience" / "bin" / "install-watch-runtime-service"
    custom_content = "#!/usr/bin/env bash\necho custom-local-tool\n"
    install_service.parent.mkdir(parents=True, exist_ok=True)
    install_service.write_text(custom_content, encoding="utf-8")

    result = module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="custom-service-file",
        dry_run=False,
        force=False,
    )

    assert str(install_service) in result["retained_retired_files"]
    assert str(install_service) not in result["removed_files"]
    assert install_service.read_text(encoding="utf-8") == custom_content
