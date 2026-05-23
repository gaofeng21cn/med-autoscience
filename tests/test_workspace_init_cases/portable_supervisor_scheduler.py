from __future__ import annotations

import importlib
import os
from pathlib import Path


DEVELOPER_SUPERVISOR_MODE_ARGS = "--apply-safe-actions --developer-supervisor-mode developer_apply_safe"


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
    supervisor_execute_dispatch = workspace_root / "ops" / "medautoscience" / "bin" / "domain-owner-action-dispatch"

    for path in (supervisor_execute_dispatch,):
        assert path.is_file()
        assert os.access(path, os.X_OK)
    for path in (install_service, service_status, uninstall_service):
        assert not path.exists()
    assert not (workspace_root / "ops" / "medautoscience" / "bin" / "watch-runtime-service-runner").exists()
    scan_domain_routes = workspace_root / "ops" / "medautoscience" / "bin" / "owner-route-reconcile"
    assert scan_domain_routes.is_file()
    assert os.access(scan_domain_routes, os.X_OK)
    scan_domain_routes_text = scan_domain_routes.read_text(encoding="utf-8")
    assert "run_medautosci owner-route-reconcile" in scan_domain_routes_text
    assert '--profile "${PROFILE_PATH}"' in scan_domain_routes_text

    materialize_domain_action_requests = workspace_root / "ops" / "medautoscience" / "bin" / "domain-action-request-materialize"
    assert materialize_domain_action_requests.is_file()
    assert os.access(materialize_domain_action_requests, os.X_OK)
    materialize_domain_action_requests_text = materialize_domain_action_requests.read_text(encoding="utf-8")
    assert "run_medautosci runtime domain-action-request-materialize" in materialize_domain_action_requests_text
    assert '--profile "${PROFILE_PATH}"' in materialize_domain_action_requests_text
    assert "--mode developer_apply_safe" in materialize_domain_action_requests_text
    assert "--apply" in materialize_domain_action_requests_text

    supervisor_execute_dispatch_text = supervisor_execute_dispatch.read_text(encoding="utf-8")
    assert "run_medautosci runtime domain-owner-action-dispatch" in supervisor_execute_dispatch_text
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
    service_status = workspace_root / "ops" / "medautoscience" / "bin" / "watch-runtime-service-status"
    uninstall_service = workspace_root / "ops" / "medautoscience" / "bin" / "uninstall-watch-runtime-service"
    runner = workspace_root / "ops" / "medautoscience" / "bin" / "watch-runtime-service-runner"
    retired_payloads = {
        install_service: (
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            'source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"\n\n'
            'run_medautosci runtime ensure-supervision --profile "${PROFILE_PATH}" "$@"\n'
        ),
        service_status: (
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            'source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"\n\n'
            'run_medautosci runtime supervision-status --profile "${PROFILE_PATH}" "$@"\n'
        ),
        uninstall_service: (
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            'source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"\n\n'
            'run_medautosci runtime remove-supervision --profile "${PROFILE_PATH}" "$@"\n'
        ),
        runner: (
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            'source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"\n\n'
            'WATCH_RUNTIME_RUNNER="${WORKSPACE_ROOT}/ops/medautoscience/bin/watch-runtime-service-runner"\n'
        ),
    }
    for path, content in retired_payloads.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    result = module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="dry-run-retired-wrapper",
        dry_run=True,
        force=False,
    )

    for path in retired_payloads:
        assert str(path) in result["removed_files"]
        assert str(path) not in result["retained_retired_files"]
        assert path.exists()


def test_init_workspace_removes_retired_service_wrapper_family(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_init")
    workspace_root = tmp_path / "remove-retired-wrapper-family"
    install_service = workspace_root / "ops" / "medautoscience" / "bin" / "install-watch-runtime-service"
    service_status = workspace_root / "ops" / "medautoscience" / "bin" / "watch-runtime-service-status"
    uninstall_service = workspace_root / "ops" / "medautoscience" / "bin" / "uninstall-watch-runtime-service"
    runner = workspace_root / "ops" / "medautoscience" / "bin" / "watch-runtime-service-runner"
    retired_payloads = {
        install_service: 'run_medautosci runtime ensure-supervision --profile "${PROFILE_PATH}" "$@"\n',
        service_status: 'run_medautosci runtime supervision-status --profile "${PROFILE_PATH}" "$@"\n',
        uninstall_service: 'run_medautosci runtime remove-supervision --profile "${PROFILE_PATH}" "$@"\n',
        runner: 'WATCH_RUNTIME_RUNNER="${WORKSPACE_ROOT}/ops/medautoscience/bin/watch-runtime-service-runner"\n',
    }
    for path, marker in retired_payloads.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("#!/usr/bin/env bash\n" + marker, encoding="utf-8")

    result = module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="remove-retired-wrapper-family",
        dry_run=False,
        force=False,
    )

    for path in retired_payloads:
        assert str(path) in result["removed_files"]
        assert str(path) not in result["retained_retired_files"]
        assert not path.exists()


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
