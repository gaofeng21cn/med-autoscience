from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})

def test_bootstrap_command_refreshes_legacy_workspace_runtime_entry_scripts(
    monkeypatch, tmp_path: Path, capsys
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_init = importlib.import_module("med_autoscience.controllers.workspace_init")
    workspace_root = tmp_path / "legacy-workspace"
    hermes_agent_repo_root = tmp_path / "hermes-agent"
    med_deepscientist_repo_root = tmp_path / "med-deepscientist"
    hermes_agent_repo_root.mkdir()
    med_deepscientist_repo_root.mkdir()

    workspace_init.init_workspace(
        workspace_root=workspace_root,
        workspace_name="legacy",
        dry_run=False,
        force=False,
        hermes_agent_repo_root=hermes_agent_repo_root,
        hermes_home_root=tmp_path / ".hermes",
    )

    profile_path = workspace_root / "ops" / "medautoscience" / "profiles" / "legacy.local.toml"
    profile_text = profile_path.read_text(encoding="utf-8").replace(
        'med_deepscientist_repo_root = "/ABS/PATH/TO/med-deepscientist"',
        f'med_deepscientist_repo_root = "{med_deepscientist_repo_root}"',
    )
    profile_path.write_text(profile_text, encoding="utf-8")

    install_service = workspace_root / "ops" / "medautoscience" / "bin" / "install-watch-runtime-service"
    install_service.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"\n\n'
        'LAUNCHD_LABEL="ai.medautoscience.legacy.watch-runtime"\n'
        'SYSTEMD_SERVICE_NAME="medautoscience-watch-runtime-legacy"\n'
        'WATCH_RUNTIME_INTERVAL_SECONDS="${WATCH_RUNTIME_INTERVAL_SECONDS:-300}"\n'
        'WATCH_RUNTIME_RUNNER="${WORKSPACE_ROOT}/ops/medautoscience/bin/watch-runtime-service-runner"\n'
        'LOG_DIR="${WORKSPACE_ROOT}/ops/medautoscience/logs"\n'
        'STDOUT_LOG="${LOG_DIR}/watch-runtime.stdout.log"\n'
        'STDERR_LOG="${LOG_DIR}/watch-runtime.stderr.log"\n\n'
        'mkdir -p "${LOG_DIR}"\n\n'
        'case "$(uname -s)" in\n'
        "  Darwin)\n"
        '    launchctl bootstrap "gui/${UID}" "${HOME}/Library/LaunchAgents/${LAUNCHD_LABEL}.plist"\n'
        "    ;;\n"
        "  Linux)\n"
        '    systemctl --user enable --now "${SYSTEMD_SERVICE_NAME}.service"\n'
        "    ;;\n"
        "esac\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        cli,
        "_load_doctor_module",
        lambda: argparse.Namespace(
            build_doctor_report=lambda profile: argparse.Namespace(
                workspace_exists=True,
                runtime_exists=True,
                studies_exists=True,
                portfolio_exists=True,
                med_deepscientist_runtime_exists=True,
                medical_overlay_enabled=profile.enable_medical_overlay,
                medical_overlay_ready=True,
                profile=profile,
            ),
            overlay_request_from_profile=lambda profile: {},
        ),
    )
    monkeypatch.setattr(
        cli.analysis_bundle_controller,
        "ensure_study_runtime_analysis_bundle",
        lambda: {"action": "already_ready", "ready": True},
    )
    monkeypatch.setattr(
        cli.overlay_installer,
        "ensure_medical_overlay",
        lambda **_: {
            "mode": "ensure_ready",
            "selected_action": "noop",
            "pre_status": {"all_targets_ready": True},
            "post_status": {"all_targets_ready": True},
            "action_result": None,
        },
    )
    monkeypatch.setattr(
        cli.data_asset_updates_controller,
        "refresh_data_assets",
        lambda *, workspace_root: {"status": {"layout_ready": True}},
    )

    exit_code = cli.main(["workspace", "bootstrap", "--profile", str(profile_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert '"selected_action": "noop"' in captured.out
    install_text = install_service.read_text(encoding="utf-8")
    assert 'run_medautosci runtime ensure-supervision --profile "${PROFILE_PATH}" "$@"' in install_text
def test_ensure_study_runtime_analysis_bundle_command_prints_controller_payload(monkeypatch, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    payload = {"action": "already_ready", "ready": True}

    monkeypatch.setattr(
        cli.analysis_bundle_controller,
        "ensure_study_runtime_analysis_bundle",
        lambda: payload,
    )

    exit_code = cli.main(["runtime", "ensure-analysis-bundle"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert json.loads(captured.out) == payload
