from __future__ import annotations

import importlib
from pathlib import Path


def test_init_workspace_upgrades_legacy_runtime_entry_scripts_without_force(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_init")
    workspace_root = tmp_path / "legacy-workspace"

    module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="legacy",
        dry_run=False,
        force=False,
    )

    shared = workspace_root / "ops" / "medautoscience" / "bin" / "_shared.sh"
    watch_runtime = workspace_root / "ops" / "medautoscience" / "bin" / "watch-runtime"
    install_service = workspace_root / "ops" / "medautoscience" / "bin" / "install-watch-runtime-service"

    shared.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n\n"
        'SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"\n'
        'MEDAUTOSCI_OPS_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"\n'
        'WORKSPACE_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"\n'
        'DEFAULT_PROFILE="${WORKSPACE_ROOT}/ops/medautoscience/profiles/legacy.local.toml"\n'
        'CONFIG_ENV_PATH="${MEDAUTOSCI_OPS_ROOT}/config.env"\n\n'
        'if [[ -f "${CONFIG_ENV_PATH}" ]]; then\n'
        "  # shellcheck disable=SC1090\n"
        '  source "${CONFIG_ENV_PATH}"\n'
        "fi\n\n"
        'PROFILE_PATH="${MED_AUTOSCIENCE_PROFILE:-${DEFAULT_PROFILE}}"\n'
        'MED_AUTOSCIENCE_REPO_RESOLVED="$(cd "${MED_AUTOSCIENCE_REPO}" && pwd)"\n\n'
        "run_medautosci() {\n"
        '  PYTHONPATH="${MED_AUTOSCIENCE_REPO_RESOLVED}/src${PYTHONPATH:+:${PYTHONPATH}}" \\\n'
        '    python3 -m med_autoscience.cli "$@"\n'
        "}\n",
        encoding="utf-8",
    )
    watch_runtime.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"\n\n'
        'run_medautosci watch \\\n'
        '  --runtime-root "/private/var/folders/example/tmp.ws/ops/med-deepscientist/runtime/quests" \\\n'
        '  "$@"\n',
        encoding="utf-8",
    )
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

    result = module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="legacy",
        dry_run=False,
        force=False,
    )

    assert str(shared) in result["upgraded_files"]
    assert str(watch_runtime) in result["upgraded_files"]
    assert str(install_service) in result["upgraded_files"]

    shared_text = shared.read_text(encoding="utf-8")
    watch_runtime_text = watch_runtime.read_text(encoding="utf-8")
    assert "MED_AUTOSCIENCE_UV_BIN" in shared_text
    assert "command -v uv" in shared_text
    assert 'python3 -m med_autoscience.cli' not in shared_text
    assert 'WORKSPACE_RUNTIME_ROOT="${WORKSPACE_ROOT}/runtime/quests"' in watch_runtime_text
    assert 'run_medautosci runtime watch \\' in watch_runtime_text
    assert '--ensure-study-runtimes' in watch_runtime_text
    assert '--apply' in watch_runtime_text
    assert '--loop' in watch_runtime_text
    install_text = install_service.read_text(encoding="utf-8")
    assert 'run_medautosci runtime ensure-supervision --profile "${PROFILE_PATH}" "$@"' in install_text


def test_init_workspace_upgrades_flat_watch_runtime_entry_even_when_current_flags_are_present(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_init")
    workspace_root = tmp_path / "legacy-watch-runtime"

    module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="legacy-watch",
        dry_run=False,
        force=False,
    )

    watch_runtime = workspace_root / "ops" / "medautoscience" / "bin" / "watch-runtime"
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

    result = module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="legacy-watch",
        dry_run=False,
        force=False,
    )

    assert str(watch_runtime) in result["upgraded_files"]
    assert 'run_medautosci runtime watch \\' in watch_runtime.read_text(encoding="utf-8")


def test_init_workspace_upgrades_legacy_public_forward_scripts_without_force(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_init")
    workspace_root = tmp_path / "legacy-public-forwarders"

    module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="legacy-public",
        dry_run=False,
        force=False,
    )

    bootstrap = workspace_root / "ops" / "medautoscience" / "bin" / "bootstrap"
    show_profile = workspace_root / "ops" / "medautoscience" / "bin" / "show-profile"
    enter_study = workspace_root / "ops" / "medautoscience" / "bin" / "enter-study"
    publication_gate = workspace_root / "ops" / "medautoscience" / "bin" / "publication-gate"
    resolve_submission_targets = workspace_root / "ops" / "medautoscience" / "bin" / "resolve-submission-targets"
    init_portfolio_memory = workspace_root / "ops" / "medautoscience" / "bin" / "init-portfolio-memory"
    prepare_external_research = workspace_root / "ops" / "medautoscience" / "bin" / "prepare-external-research"
    sync_delivery = workspace_root / "ops" / "medautoscience" / "bin" / "sync-delivery"

    bootstrap.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"\n\n'
        'run_medautosci bootstrap --profile "${PROFILE_PATH}" "$@"\n',
        encoding="utf-8",
    )
    show_profile.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"\n\n'
        'run_medautosci show-profile --profile "${PROFILE_PATH}" "$@"\n',
        encoding="utf-8",
    )
    enter_study.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"\n\n'
        'run_medautosci ensure-study-runtime --profile "${PROFILE_PATH}" "$@"\n',
        encoding="utf-8",
    )
    publication_gate.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"\n\n'
        'run_medautosci publication-gate "$@"\n',
        encoding="utf-8",
    )
    resolve_submission_targets.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"\n\n'
        'args=("$@")\n'
        "has_profile=0\n"
        'for arg in "${args[@]}"; do\n'
        '  if [[ "${arg}" == "--profile" ]]; then\n'
        "    has_profile=1\n"
        "    break\n"
        "  fi\n"
        "done\n\n"
        'if [[ "${has_profile}" -eq 1 ]]; then\n'
        '  run_medautosci resolve-submission-targets "${args[@]}"\n'
        "else\n"
        '  run_medautosci resolve-submission-targets --profile "${PROFILE_PATH}" "${args[@]}"\n'
        "fi\n",
        encoding="utf-8",
    )
    init_portfolio_memory.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"\n\n'
        'run_medautosci init-portfolio-memory "$@"\n',
        encoding="utf-8",
    )
    prepare_external_research.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"\n\n'
        'run_medautosci prepare-external-research "$@"\n',
        encoding="utf-8",
    )
    sync_delivery.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"\n\n'
        'run_medautosci sync-study-delivery "$@"\n',
        encoding="utf-8",
    )

    result = module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="legacy-public",
        dry_run=False,
        force=False,
    )

    for path in (
        bootstrap,
        show_profile,
        enter_study,
        publication_gate,
        resolve_submission_targets,
        init_portfolio_memory,
        prepare_external_research,
        sync_delivery,
    ):
        assert str(path) in result["upgraded_files"]

    assert 'run_medautosci workspace bootstrap --profile "${PROFILE_PATH}" "$@"' in bootstrap.read_text(encoding="utf-8")
    assert 'run_medautosci doctor profile --profile "${PROFILE_PATH}" "$@"' in show_profile.read_text(encoding="utf-8")
    assert 'run_medautosci study ensure-runtime --profile "${PROFILE_PATH}" "$@"' in enter_study.read_text(encoding="utf-8")
    assert 'run_medautosci publication gate "$@"' in publication_gate.read_text(encoding="utf-8")
    resolve_targets_text = resolve_submission_targets.read_text(encoding="utf-8")
    assert 'run_medautosci publication resolve-targets "${args[@]}"' in resolve_targets_text
    assert 'run_medautosci publication resolve-targets --profile "${PROFILE_PATH}" "${args[@]}"' in resolve_targets_text
    assert 'run_medautosci data init-memory "$@"' in init_portfolio_memory.read_text(encoding="utf-8")
    assert 'run_medautosci data prepare-external-research "$@"' in prepare_external_research.read_text(encoding="utf-8")
    assert 'run_medautosci study delivery-sync "$@"' in sync_delivery.read_text(encoding="utf-8")


def test_init_workspace_upgrades_shared_script_that_still_invokes_bare_uv(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_init")
    workspace_root = tmp_path / "legacy-uv-workspace"
    shared = workspace_root / "ops" / "medautoscience" / "bin" / "_shared.sh"
    shared.parent.mkdir(parents=True, exist_ok=True)
    shared.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n\n"
        'SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"\n'
        'MEDAUTOSCI_OPS_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"\n'
        'WORKSPACE_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"\n'
        'DEFAULT_PROFILE="${WORKSPACE_ROOT}/ops/medautoscience/profiles/legacy.local.toml"\n'
        'CONFIG_ENV_PATH="${MEDAUTOSCI_OPS_ROOT}/config.env"\n\n'
        'if [[ -f "${CONFIG_ENV_PATH}" ]]; then\n'
        "  # shellcheck disable=SC1090\n"
        '  source "${CONFIG_ENV_PATH}"\n'
        "fi\n\n"
        'PROFILE_PATH="${MED_AUTOSCIENCE_PROFILE:-${DEFAULT_PROFILE}}"\n'
        'MED_AUTOSCIENCE_REPO_RESOLVED="$(cd "${MED_AUTOSCIENCE_REPO}" && pwd)"\n\n'
        "run_medautosci() {\n"
        '  uv run --directory "${MED_AUTOSCIENCE_REPO_RESOLVED}" python -m med_autoscience.cli "$@"\n'
        "}\n",
        encoding="utf-8",
    )

    result = module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="legacy-uv",
        dry_run=False,
        force=False,
    )

    assert str(shared) in result["upgraded_files"]
    shared_text = shared.read_text(encoding="utf-8")
    assert "MED_AUTOSCIENCE_UV_BIN" in shared_text
    assert '"${MED_AUTOSCIENCE_UV_BIN}" run --directory "${MED_AUTOSCIENCE_REPO_RESOLVED}" python -m med_autoscience.cli "$@"' in shared_text
