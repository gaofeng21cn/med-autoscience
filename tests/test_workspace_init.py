from __future__ import annotations

import importlib
import json
import os
from pathlib import Path


def test_init_workspace_dry_run_reports_plan_without_writing_files(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_init")
    workspace_root = tmp_path / "diabetes-workspace"

    result = module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="diabetes",
        dry_run=True,
        force=False,
    )

    assert result["dry_run"] is True
    assert result["workspace_root"] == str(workspace_root)
    assert result["workspace_name"] == "diabetes"
    assert result["created_directories"]
    assert result["created_files"]
    assert not workspace_root.exists()


def test_init_workspace_creates_minimal_workspace_and_entry_files(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_init")
    workspace_root = tmp_path / "glioma-workspace"

    result = module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="glioma",
        dry_run=False,
        force=False,
    )

    assert result["dry_run"] is False
    assert workspace_root.exists()
    assert (workspace_root / "datasets").is_dir()
    assert (workspace_root / "contracts").is_dir()
    assert (workspace_root / "studies").is_dir()
    assert (workspace_root / "portfolio" / "data_assets").is_dir()
    assert (workspace_root / "portfolio" / "research_memory").is_dir()
    assert (workspace_root / "portfolio" / "research_memory" / "literature").is_dir()
    assert (workspace_root / "portfolio" / "research_memory" / "literature" / "coverage").is_dir()
    assert (workspace_root / "portfolio" / "research_memory" / "prompts").is_dir()
    assert (workspace_root / "portfolio" / "research_memory" / "external_reports").is_dir()
    assert (workspace_root / "ops" / "medautoscience" / "bin").is_dir()
    assert (workspace_root / "ops" / "med-deepscientist" / "bin").is_dir()

    profile_path = workspace_root / "ops" / "medautoscience" / "profiles" / "glioma.local.toml"
    assert profile_path.is_file()
    profile_text = profile_path.read_text(encoding="utf-8")
    assert 'name = "glioma"' in profile_text
    assert f'workspace_root = "{workspace_root}"' in profile_text
    assert 'default_startup_anchor_policy = "scout_first_for_continue_existing_state"' in profile_text
    assert 'legacy_code_execution_policy = "forbid_without_user_approval"' in profile_text
    assert 'public_data_discovery_policy = "required_for_scout_route_selection"' in profile_text
    assert 'startup_boundary_requirements = ["paper_framing", "journal_shortlist", "evidence_package"]' in profile_text
    assert '"analysis-campaign", "figure-polish", "write"' in profile_text
    assert "enable_autofigure_edit" not in profile_text
    assert "autofigure_edit_bootstrap_mode" not in profile_text
    assert "autofigure_edit_service_url" not in profile_text

    med_config = workspace_root / "ops" / "medautoscience" / "config.env"
    deep_config = workspace_root / "ops" / "med-deepscientist" / "config.env"
    med_shared = workspace_root / "ops" / "medautoscience" / "bin" / "_shared.sh"
    ds_shared = workspace_root / "ops" / "med-deepscientist" / "bin" / "_shared.sh"
    assert med_config.is_file()
    assert deep_config.is_file()
    assert med_shared.is_file()
    assert ds_shared.is_file()
    med_shared_text = med_shared.read_text(encoding="utf-8")
    ds_shared_text = ds_shared.read_text(encoding="utf-8")
    assert 'MED_AUTOSCIENCE_UV_BIN="${MED_AUTOSCIENCE_UV_BIN:-$(command -v uv || true)}"' in med_shared_text
    assert 'MED_AUTOSCIENCE_RSCRIPT_BIN="${MED_AUTOSCIENCE_RSCRIPT_BIN:-$(command -v Rscript || true)}"' in med_shared_text
    assert 'MED_AUTOSCIENCE_NODE_BIN="${MED_AUTOSCIENCE_NODE_BIN:-$(command -v node || true)}"' in med_shared_text
    assert '"${MED_AUTOSCIENCE_UV_BIN}" run --directory "${MED_AUTOSCIENCE_REPO_RESOLVED}" python -m med_autoscience.cli "$@"' in med_shared_text
    assert 'uv run --directory "${MED_AUTOSCIENCE_REPO_RESOLVED}" python - "${PROFILE_PATH}"' in ds_shared_text
    assert 'CONTRACT_JSON="${payload_json}" uv run --directory "${MED_AUTOSCIENCE_REPO_RESOLVED}" python - <<' in ds_shared_text

    show_profile = workspace_root / "ops" / "medautoscience" / "bin" / "show-profile"
    enter_study = workspace_root / "ops" / "medautoscience" / "bin" / "enter-study"
    watch_runtime = workspace_root / "ops" / "medautoscience" / "bin" / "watch-runtime"
    resolve_journal_shortlist = workspace_root / "ops" / "medautoscience" / "bin" / "resolve-journal-shortlist"
    init_portfolio_memory = workspace_root / "ops" / "medautoscience" / "bin" / "init-portfolio-memory"
    portfolio_memory_status = workspace_root / "ops" / "medautoscience" / "bin" / "portfolio-memory-status"
    init_workspace_literature = workspace_root / "ops" / "medautoscience" / "bin" / "init-workspace-literature"
    workspace_literature_status = workspace_root / "ops" / "medautoscience" / "bin" / "workspace-literature-status"
    prepare_external_research = workspace_root / "ops" / "medautoscience" / "bin" / "prepare-external-research"
    external_research_status = workspace_root / "ops" / "medautoscience" / "bin" / "external-research-status"
    ds_doctor = workspace_root / "ops" / "med-deepscientist" / "bin" / "doctor"
    assert show_profile.is_file()
    assert enter_study.is_file()
    assert watch_runtime.is_file()
    assert resolve_journal_shortlist.is_file()
    assert init_portfolio_memory.is_file()
    assert portfolio_memory_status.is_file()
    assert init_workspace_literature.is_file()
    assert workspace_literature_status.is_file()
    assert prepare_external_research.is_file()
    assert external_research_status.is_file()
    assert ds_doctor.is_file()
    assert os.access(show_profile, os.X_OK)
    assert os.access(enter_study, os.X_OK)
    assert os.access(watch_runtime, os.X_OK)
    assert os.access(resolve_journal_shortlist, os.X_OK)
    assert os.access(init_portfolio_memory, os.X_OK)
    assert os.access(portfolio_memory_status, os.X_OK)
    assert os.access(init_workspace_literature, os.X_OK)
    assert os.access(workspace_literature_status, os.X_OK)
    assert os.access(prepare_external_research, os.X_OK)
    assert os.access(external_research_status, os.X_OK)
    assert os.access(ds_doctor, os.X_OK)
    watch_runtime_text = watch_runtime.read_text(encoding="utf-8")
    assert '--profile "${PROFILE_PATH}"' in watch_runtime_text
    assert "--ensure-study-runtimes" in watch_runtime_text
    assert "--apply" in watch_runtime_text
    assert "--loop" in watch_runtime_text

    portfolio_memory_readme = workspace_root / "portfolio" / "research_memory" / "README.md"
    portfolio_memory_registry = workspace_root / "portfolio" / "research_memory" / "registry.yaml"
    workspace_literature_registry = workspace_root / "portfolio" / "research_memory" / "literature" / "registry.jsonl"
    assert portfolio_memory_readme.is_file()
    assert portfolio_memory_registry.is_file()
    assert workspace_literature_registry.is_file()
    assert "Portfolio Research Memory" in portfolio_memory_readme.read_text(encoding="utf-8")

    root_readme = workspace_root / "README.md"
    assert root_readme.is_file()
    root_readme_text = root_readme.read_text(encoding="utf-8")
    assert "workspace" in root_readme_text.lower()
    assert "ops/medautoscience/bin/show-profile" in root_readme_text
    assert "不要直接通过 `med-deepscientist` UI、CLI 或 daemon HTTP API 发起研究 quest" in root_readme_text
    assert "portfolio/research_memory/" in root_readme_text

    deepscientist_readme = workspace_root / "ops" / "med-deepscientist" / "README.md"
    assert deepscientist_readme.is_file()
    deepscientist_readme_text = deepscientist_readme.read_text(encoding="utf-8")
    assert "runtime 运维面" in deepscientist_readme_text
    assert "不是研究入口" in deepscientist_readme_text
    assert "ops/medautoscience/bin/enter-study" in deepscientist_readme_text

    workspace_pyproject = workspace_root / "pyproject.toml"
    assert workspace_pyproject.is_file()
    workspace_pyproject_text = workspace_pyproject.read_text(encoding="utf-8")
    expected_repo_relpath = Path(os.path.relpath(Path(module.__file__).resolve().parents[3], workspace_root)).as_posix()
    assert 'name = "glioma-workspace"' in workspace_pyproject_text
    assert 'description = "Managed Python environment for the glioma workspace."' in workspace_pyproject_text
    assert '"med-autoscience"' in workspace_pyproject_text
    assert "[tool.uv.sources]" in workspace_pyproject_text
    assert f'med-autoscience = {{ path = "{expected_repo_relpath}", editable = true }}' in workspace_pyproject_text

    workspace_rules = workspace_root / "WORKSPACE_AUTOSCIENCE_RULES.md"
    assert workspace_rules.is_file()
    workspace_rules_text = workspace_rules.read_text(encoding="utf-8")
    assert "优先复用 MedAutoScience 已覆盖的成熟 controller / CLI / overlay skill" in workspace_rules_text
    assert "边界明确且 startup-ready 后，默认切入 `Hermes-backed` managed runtime 的自动持续推进" in workspace_rules_text
    assert "必须显式通知用户自动驾驶已启动或已被检测到，并提供监督入口" in workspace_rules_text
    assert "前台必须立即进入 supervisor-only 监管态" in workspace_rules_text
    assert "不得直接写入 runtime-owned 的 study / quest / paper surface" in workspace_rules_text
    assert "portfolio-memory-status" in workspace_rules_text
    assert "prepare-external-research" in workspace_rules_text

    watch_runtime_text = watch_runtime.read_text(encoding="utf-8")
    assert 'source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"' in watch_runtime_text
    assert 'WORKSPACE_RUNTIME_ROOT="${WORKSPACE_ROOT}/ops/med-deepscientist/runtime/quests"' in watch_runtime_text
    assert 'run_medautosci watch \\' in watch_runtime_text
    assert str(workspace_root / "ops" / "med-deepscientist" / "runtime" / "quests") not in watch_runtime_text


def test_init_workspace_is_idempotent_and_force_overwrites_files(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_init")
    workspace_root = tmp_path / "pituitary-workspace"

    first = module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="pituitary",
        dry_run=False,
        force=False,
    )
    assert first["created_files"]

    profile_path = workspace_root / "ops" / "medautoscience" / "profiles" / "pituitary.local.toml"
    profile_path.write_text("# local edit\n", encoding="utf-8")

    second = module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="pituitary",
        dry_run=False,
        force=False,
    )
    assert str(profile_path) in second["skipped_files"]
    assert profile_path.read_text(encoding="utf-8") == "# local edit\n"

    third = module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="pituitary",
        dry_run=False,
        force=True,
    )
    assert str(profile_path) in third["overwritten_files"]
    assert 'name = "pituitary"' in profile_path.read_text(encoding="utf-8")


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
    assert 'WATCH_RUNTIME_INTERVAL_SECONDS="${WATCH_RUNTIME_INTERVAL_SECONDS:-300}"' in runner_text
    assert 'WATCH_RUNTIME_SCRIPT="${WORKSPACE_ROOT}/ops/medautoscience/bin/watch-runtime"' in runner_text
    assert 'exec "${WATCH_RUNTIME_SCRIPT}" --interval-seconds "${WATCH_RUNTIME_INTERVAL_SECONDS}" "$@"' in runner_text

    install_text = install_service.read_text(encoding="utf-8")
    assert "ai.medautoscience.lung.watch-runtime" in install_text
    assert "medautoscience-watch-runtime-lung" in install_text
    assert 'watch-runtime-service-runner' in install_text
    assert "MED_AUTOSCIENCE_UV_BIN" in install_text
    assert "MED_AUTOSCIENCE_RSCRIPT_BIN" in install_text
    assert "MED_AUTOSCIENCE_NODE_BIN" in install_text
    assert "command -v uv" in install_text
    assert "command -v Rscript" in install_text
    assert "command -v node" in install_text
    assert "launchctl bootstrap" in install_text
    assert "systemctl --user enable --now" in install_text
    assert 'ops/medautoscience/logs' in install_text

    status_text = service_status.read_text(encoding="utf-8")
    assert "launchctl print" in status_text
    assert "systemctl --user status" in status_text

    uninstall_text = uninstall_service.read_text(encoding="utf-8")
    assert "launchctl bootout" in uninstall_text
    assert "systemctl --user disable --now" in uninstall_text


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
    assert 'WORKSPACE_RUNTIME_ROOT="${WORKSPACE_ROOT}/ops/med-deepscientist/runtime/quests"' in watch_runtime_text
    assert '--ensure-study-runtimes' in watch_runtime_text
    assert '--apply' in watch_runtime_text
    assert '--loop' in watch_runtime_text
    install_text = install_service.read_text(encoding="utf-8")
    assert "MED_AUTOSCIENCE_UV_BIN" in install_text
    assert "command -v uv" in install_text


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


def test_init_workspace_upgrades_current_managed_scripts_when_rscript_binding_is_missing(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_init")
    workspace_root = tmp_path / "legacy-rscript-workspace"
    shared = workspace_root / "ops" / "medautoscience" / "bin" / "_shared.sh"
    install_service = workspace_root / "ops" / "medautoscience" / "bin" / "install-watch-runtime-service"
    shared.parent.mkdir(parents=True, exist_ok=True)
    install_service.parent.mkdir(parents=True, exist_ok=True)

    shared.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n\n"
        'SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"\n'
        'MEDAUTOSCI_OPS_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"\n'
        'WORKSPACE_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"\n'
        'DEFAULT_PROFILE="${WORKSPACE_ROOT}/ops/medautoscience/profiles/legacy-rscript.local.toml"\n'
        'CONFIG_ENV_PATH="${MEDAUTOSCI_OPS_ROOT}/config.env"\n\n'
        'if [[ -f "${CONFIG_ENV_PATH}" ]]; then\n'
        "  # shellcheck disable=SC1090\n"
        '  source "${CONFIG_ENV_PATH}"\n'
        "fi\n\n"
        'if [[ -n "${MED_AUTOSCIENCE_PROFILE:-}" ]]; then\n'
        '  PROFILE_PATH="${MED_AUTOSCIENCE_PROFILE}"\n'
        "else\n"
        '  PROFILE_PATH="${DEFAULT_PROFILE}"\n'
        "fi\n\n"
        'if [[ -z "${MED_AUTOSCIENCE_REPO:-}" ]]; then\n'
        '  echo "MED_AUTOSCIENCE_REPO is not configured. Set it in ${CONFIG_ENV_PATH} or export it explicitly." >&2\n'
        "  exit 1\n"
        "fi\n\n"
        'MED_AUTOSCIENCE_REPO_RESOLVED="$(cd "${MED_AUTOSCIENCE_REPO}" && pwd)"\n\n'
        'if [[ ! -f "${PROFILE_PATH}" ]]; then\n'
        '  echo "Profile file not found: ${PROFILE_PATH}" >&2\n'
        "  exit 1\n"
        "fi\n\n"
        'MED_AUTOSCIENCE_UV_BIN="${MED_AUTOSCIENCE_UV_BIN:-$(command -v uv || true)}"\n'
        'if [[ -z "${MED_AUTOSCIENCE_UV_BIN}" ]]; then\n'
        '  echo "uv is not available. Set MED_AUTOSCIENCE_UV_BIN in ${CONFIG_ENV_PATH} or install uv on PATH." >&2\n'
        "  exit 1\n"
        "fi\n\n"
        'if [[ "${MED_AUTOSCIENCE_UV_BIN}" != /* ]]; then\n'
        '  echo "MED_AUTOSCIENCE_UV_BIN must be an absolute path: ${MED_AUTOSCIENCE_UV_BIN}" >&2\n'
        "  exit 1\n"
        "fi\n\n"
        'if [[ ! -x "${MED_AUTOSCIENCE_UV_BIN}" ]]; then\n'
        '  echo "MED_AUTOSCIENCE_UV_BIN is not executable: ${MED_AUTOSCIENCE_UV_BIN}" >&2\n'
        "  exit 1\n"
        "fi\n\n"
        "run_medautosci() {\n"
        '  "${MED_AUTOSCIENCE_UV_BIN}" run --directory "${MED_AUTOSCIENCE_REPO_RESOLVED}" python -m med_autoscience.cli "$@"\n'
        "}\n",
        encoding="utf-8",
    )
    install_service.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"\n\n'
        'LAUNCHD_LABEL="ai.medautoscience.legacy-rscript.watch-runtime"\n'
        'SYSTEMD_SERVICE_NAME="medautoscience-watch-runtime-legacy-rscript"\n'
        'WATCH_RUNTIME_INTERVAL_SECONDS="${WATCH_RUNTIME_INTERVAL_SECONDS:-300}"\n'
        'WATCH_RUNTIME_RUNNER="${WORKSPACE_ROOT}/ops/medautoscience/bin/watch-runtime-service-runner"\n'
        'LOG_DIR="${WORKSPACE_ROOT}/ops/medautoscience/logs"\n'
        'STDOUT_LOG="${LOG_DIR}/watch-runtime.stdout.log"\n'
        'STDERR_LOG="${LOG_DIR}/watch-runtime.stderr.log"\n\n'
        'MED_AUTOSCIENCE_UV_BIN="${MED_AUTOSCIENCE_UV_BIN:-$(command -v uv || true)}"\n'
        'if [[ -z "${MED_AUTOSCIENCE_UV_BIN}" ]]; then\n'
        '  echo "uv is not available. Set MED_AUTOSCIENCE_UV_BIN in ops/medautoscience/config.env or install uv on PATH before installing the service." >&2\n'
        "  exit 1\n"
        "fi\n\n"
        'if [[ "${MED_AUTOSCIENCE_UV_BIN}" != /* ]]; then\n'
        '  echo "MED_AUTOSCIENCE_UV_BIN must be an absolute path: ${MED_AUTOSCIENCE_UV_BIN}" >&2\n'
        "  exit 1\n"
        "fi\n\n"
        'if [[ ! -x "${MED_AUTOSCIENCE_UV_BIN}" ]]; then\n'
        '  echo "MED_AUTOSCIENCE_UV_BIN is not executable: ${MED_AUTOSCIENCE_UV_BIN}" >&2\n'
        "  exit 1\n"
        "fi\n\n"
        'mkdir -p "${LOG_DIR}"\n\n'
        'case "$(uname -s)" in\n'
        "  Darwin)\n"
        '    LAUNCHD_LABEL="${LAUNCHD_LABEL}" \\\n'
        '    WATCH_RUNTIME_INTERVAL_SECONDS="${WATCH_RUNTIME_INTERVAL_SECONDS}" \\\n'
        '    MED_AUTOSCIENCE_UV_BIN="${MED_AUTOSCIENCE_UV_BIN}" \\\n'
        "    python3 - <<'PY'\n"
        "import os\n"
        "payload = {\n"
        '    "EnvironmentVariables": {\n'
        '        "WATCH_RUNTIME_INTERVAL_SECONDS": os.environ["WATCH_RUNTIME_INTERVAL_SECONDS"],\n'
        '        "MED_AUTOSCIENCE_UV_BIN": os.environ["MED_AUTOSCIENCE_UV_BIN"],\n'
        "    },\n"
        "}\n"
            "print(payload)\n"
            "PY\n"
            '    launchctl bootstrap "gui/${UID}" "${HOME}/Library/LaunchAgents/${LAUNCHD_LABEL}.plist"\n'
            "    ;;\n"
            "  Linux)\n"
            '    cat > /tmp/watch-runtime.service <<EOF\n'
            'Environment=WATCH_RUNTIME_INTERVAL_SECONDS=${WATCH_RUNTIME_INTERVAL_SECONDS}\n'
            'Environment=MED_AUTOSCIENCE_UV_BIN=${MED_AUTOSCIENCE_UV_BIN}\n'
            "EOF\n"
            '    systemctl --user enable --now "${SYSTEMD_SERVICE_NAME}.service"\n'
            "    ;;\n"
            "esac\n",
            encoding="utf-8",
        )

    result = module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="legacy-rscript",
        dry_run=False,
        force=False,
    )

    assert str(shared) in result["upgraded_files"]
    assert str(install_service) in result["upgraded_files"]
    assert "MED_AUTOSCIENCE_RSCRIPT_BIN" in shared.read_text(encoding="utf-8")
    install_text = install_service.read_text(encoding="utf-8")
    assert "MED_AUTOSCIENCE_RSCRIPT_BIN" in install_text
    assert "command -v Rscript" in install_text


def test_init_workspace_upgrades_current_managed_scripts_when_node_binding_is_missing(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_init")
    workspace_root = tmp_path / "legacy-node-workspace"
    shared = workspace_root / "ops" / "medautoscience" / "bin" / "_shared.sh"
    install_service = workspace_root / "ops" / "medautoscience" / "bin" / "install-watch-runtime-service"
    shared.parent.mkdir(parents=True, exist_ok=True)
    install_service.parent.mkdir(parents=True, exist_ok=True)

    shared.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n\n"
        'SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"\n'
        'MEDAUTOSCI_OPS_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"\n'
        'WORKSPACE_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"\n'
        'DEFAULT_PROFILE="${WORKSPACE_ROOT}/ops/medautoscience/profiles/legacy-node.local.toml"\n'
        'CONFIG_ENV_PATH="${MEDAUTOSCI_OPS_ROOT}/config.env"\n\n'
        'if [[ -f "${CONFIG_ENV_PATH}" ]]; then\n'
        "  # shellcheck disable=SC1090\n"
        '  source "${CONFIG_ENV_PATH}"\n'
        "fi\n\n"
        'if [[ -n "${MED_AUTOSCIENCE_PROFILE:-}" ]]; then\n'
        '  PROFILE_PATH="${MED_AUTOSCIENCE_PROFILE}"\n'
        "else\n"
        '  PROFILE_PATH="${DEFAULT_PROFILE}"\n'
        "fi\n\n"
        'if [[ -z "${MED_AUTOSCIENCE_REPO:-}" ]]; then\n'
        '  echo "MED_AUTOSCIENCE_REPO is not configured. Set it in ${CONFIG_ENV_PATH} or export it explicitly." >&2\n'
        "  exit 1\n"
        "fi\n\n"
        'MED_AUTOSCIENCE_REPO_RESOLVED="$(cd "${MED_AUTOSCIENCE_REPO}" && pwd)"\n\n'
        'if [[ ! -f "${PROFILE_PATH}" ]]; then\n'
        '  echo "Profile file not found: ${PROFILE_PATH}" >&2\n'
        "  exit 1\n"
        "fi\n\n"
        'MED_AUTOSCIENCE_UV_BIN="${MED_AUTOSCIENCE_UV_BIN:-$(command -v uv || true)}"\n'
        'if [[ -z "${MED_AUTOSCIENCE_UV_BIN}" ]]; then\n'
        '  echo "uv is not available. Set MED_AUTOSCIENCE_UV_BIN in ${CONFIG_ENV_PATH} or install uv on PATH." >&2\n'
        "  exit 1\n"
        "fi\n\n"
        'if [[ "${MED_AUTOSCIENCE_UV_BIN}" != /* ]]; then\n'
        '  echo "MED_AUTOSCIENCE_UV_BIN must be an absolute path: ${MED_AUTOSCIENCE_UV_BIN}" >&2\n'
        "  exit 1\n"
        "fi\n\n"
        'if [[ ! -x "${MED_AUTOSCIENCE_UV_BIN}" ]]; then\n'
        '  echo "MED_AUTOSCIENCE_UV_BIN is not executable: ${MED_AUTOSCIENCE_UV_BIN}" >&2\n'
        "  exit 1\n"
        "fi\n\n"
        'MED_AUTOSCIENCE_RSCRIPT_BIN="${MED_AUTOSCIENCE_RSCRIPT_BIN:-$(command -v Rscript || true)}"\n'
        'if [[ -n "${MED_AUTOSCIENCE_RSCRIPT_BIN}" ]]; then\n'
        '  if [[ "${MED_AUTOSCIENCE_RSCRIPT_BIN}" != /* ]]; then\n'
        '    echo "MED_AUTOSCIENCE_RSCRIPT_BIN must be an absolute path: ${MED_AUTOSCIENCE_RSCRIPT_BIN}" >&2\n'
        "    exit 1\n"
        "  fi\n"
        '  if [[ ! -x "${MED_AUTOSCIENCE_RSCRIPT_BIN}" ]]; then\n'
        '    echo "MED_AUTOSCIENCE_RSCRIPT_BIN is not executable: ${MED_AUTOSCIENCE_RSCRIPT_BIN}" >&2\n'
        "    exit 1\n"
        "  fi\n"
        "fi\n\n"
        'export MED_AUTOSCIENCE_RSCRIPT_BIN\n\n'
        "run_medautosci() {\n"
        '  "${MED_AUTOSCIENCE_UV_BIN}" run --directory "${MED_AUTOSCIENCE_REPO_RESOLVED}" python -m med_autoscience.cli "$@"\n'
        "}\n",
        encoding="utf-8",
    )
    install_service.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"\n\n'
        'LAUNCHD_LABEL="ai.medautoscience.legacy-node.watch-runtime"\n'
        'SYSTEMD_SERVICE_NAME="medautoscience-watch-runtime-legacy-node"\n'
        'WATCH_RUNTIME_INTERVAL_SECONDS="${WATCH_RUNTIME_INTERVAL_SECONDS:-300}"\n'
        'WATCH_RUNTIME_RUNNER="${WORKSPACE_ROOT}/ops/medautoscience/bin/watch-runtime-service-runner"\n'
        'LOG_DIR="${WORKSPACE_ROOT}/ops/medautoscience/logs"\n'
        'STDOUT_LOG="${LOG_DIR}/watch-runtime.stdout.log"\n'
        'STDERR_LOG="${LOG_DIR}/watch-runtime.stderr.log"\n\n'
        'MED_AUTOSCIENCE_UV_BIN="${MED_AUTOSCIENCE_UV_BIN:-$(command -v uv || true)}"\n'
        'if [[ -z "${MED_AUTOSCIENCE_UV_BIN}" ]]; then\n'
        '  echo "uv is not available. Set MED_AUTOSCIENCE_UV_BIN in ops/medautoscience/config.env or install uv on PATH before installing the service." >&2\n'
        "  exit 1\n"
        "fi\n\n"
        'if [[ "${MED_AUTOSCIENCE_UV_BIN}" != /* ]]; then\n'
        '  echo "MED_AUTOSCIENCE_UV_BIN must be an absolute path: ${MED_AUTOSCIENCE_UV_BIN}" >&2\n'
        "  exit 1\n"
        "fi\n\n"
        'if [[ ! -x "${MED_AUTOSCIENCE_UV_BIN}" ]]; then\n'
        '  echo "MED_AUTOSCIENCE_UV_BIN is not executable: ${MED_AUTOSCIENCE_UV_BIN}" >&2\n'
        "  exit 1\n"
        "fi\n\n"
        'MED_AUTOSCIENCE_RSCRIPT_BIN="${MED_AUTOSCIENCE_RSCRIPT_BIN:-$(command -v Rscript || true)}"\n'
        'if [[ -n "${MED_AUTOSCIENCE_RSCRIPT_BIN}" ]]; then\n'
        '  if [[ "${MED_AUTOSCIENCE_RSCRIPT_BIN}" != /* ]]; then\n'
        '    echo "MED_AUTOSCIENCE_RSCRIPT_BIN must be an absolute path: ${MED_AUTOSCIENCE_RSCRIPT_BIN}" >&2\n'
        "    exit 1\n"
        "  fi\n"
        '  if [[ ! -x "${MED_AUTOSCIENCE_RSCRIPT_BIN}" ]]; then\n'
        '    echo "MED_AUTOSCIENCE_RSCRIPT_BIN is not executable: ${MED_AUTOSCIENCE_RSCRIPT_BIN}" >&2\n'
        "    exit 1\n"
        "  fi\n"
        "fi\n\n"
        'mkdir -p "${LOG_DIR}"\n\n'
        'case "$(uname -s)" in\n'
        "  Darwin)\n"
        '    LAUNCHD_LABEL="${LAUNCHD_LABEL}" \\\n'
        '    WATCH_RUNTIME_INTERVAL_SECONDS="${WATCH_RUNTIME_INTERVAL_SECONDS}" \\\n'
        '    MED_AUTOSCIENCE_UV_BIN="${MED_AUTOSCIENCE_UV_BIN}" \\\n'
        '    MED_AUTOSCIENCE_RSCRIPT_BIN="${MED_AUTOSCIENCE_RSCRIPT_BIN}" \\\n'
        "    python3 - <<'PY'\n"
        "import os\n"
        "payload = {\n"
        '    "EnvironmentVariables": {\n'
        '        "WATCH_RUNTIME_INTERVAL_SECONDS": os.environ["WATCH_RUNTIME_INTERVAL_SECONDS"],\n'
        '        "MED_AUTOSCIENCE_UV_BIN": os.environ["MED_AUTOSCIENCE_UV_BIN"],\n'
        "    },\n"
        "}\n"
        "if os.environ.get(\"MED_AUTOSCIENCE_RSCRIPT_BIN\"):\n"
        '    payload["EnvironmentVariables"]["MED_AUTOSCIENCE_RSCRIPT_BIN"] = os.environ["MED_AUTOSCIENCE_RSCRIPT_BIN"]\n'
        "print(payload)\n"
        "PY\n"
        '    launchctl bootstrap "gui/${UID}" "${HOME}/Library/LaunchAgents/${LAUNCHD_LABEL}.plist"\n'
        "    ;;\n"
        "  Linux)\n"
        '    cat > /tmp/watch-runtime.service <<EOF\n'
        'Environment=WATCH_RUNTIME_INTERVAL_SECONDS=${WATCH_RUNTIME_INTERVAL_SECONDS}\n'
        'Environment=MED_AUTOSCIENCE_UV_BIN=${MED_AUTOSCIENCE_UV_BIN}\n'
        'Environment=MED_AUTOSCIENCE_RSCRIPT_BIN=${MED_AUTOSCIENCE_RSCRIPT_BIN}\n'
        "EOF\n"
        '    systemctl --user enable --now "${SYSTEMD_SERVICE_NAME}.service"\n'
        "    ;;\n"
        "esac\n",
        encoding="utf-8",
    )

    result = module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="legacy-node",
        dry_run=False,
        force=False,
    )

    assert str(shared) in result["upgraded_files"]
    assert str(install_service) in result["upgraded_files"]
    assert "MED_AUTOSCIENCE_NODE_BIN" in shared.read_text(encoding="utf-8")
    install_text = install_service.read_text(encoding="utf-8")
    assert "MED_AUTOSCIENCE_NODE_BIN" in install_text
    assert "command -v node" in install_text


def test_init_workspace_upgrades_medautoscience_config_with_detected_node_binding(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_init")
    workspace_root = tmp_path / "config-upgrade-workspace"
    config_env = workspace_root / "ops" / "medautoscience" / "config.env"
    detected_node = tmp_path / "bin" / "node"
    detected_node.parent.mkdir(parents=True, exist_ok=True)
    detected_node.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    detected_node.chmod(0o755)
    config_env.parent.mkdir(parents=True, exist_ok=True)
    config_env.write_text(
        "\n".join(
            [
                'MED_AUTOSCIENCE_REPO="/Users/gaofeng/workspace/med-autoscience"',
                f'MED_AUTOSCIENCE_PROFILE="{workspace_root / "ops" / "medautoscience" / "profiles" / "config-upgrade.local.toml"}"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(module.shutil, "which", lambda executable: str(detected_node) if executable == "node" else None)

    result = module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="config-upgrade",
        dry_run=False,
        force=False,
    )

    assert str(config_env) in result["upgraded_files"]
    config_text = config_env.read_text(encoding="utf-8")
    assert f'MED_AUTOSCIENCE_NODE_BIN="{detected_node}"' in config_text
    assert 'MED_AUTOSCIENCE_REPO="/Users/gaofeng/workspace/med-autoscience"' in config_text


def test_init_workspace_upgrades_configured_active_profile_with_explicit_hermes_binding(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_init")
    workspace_root = tmp_path / "nfpitnet-workspace"
    profiles_root = workspace_root / "ops" / "medautoscience" / "profiles"
    profiles_root.mkdir(parents=True, exist_ok=True)
    active_profile = profiles_root / "nfpitnet.workspace.toml"
    active_profile.write_text(
        "\n".join(
            [
                'name = "nfpitnet"',
                f'workspace_root = "{workspace_root}"',
                f'runtime_root = "{workspace_root / "ops" / "med-deepscientist" / "runtime" / "quests"}"',
                f'studies_root = "{workspace_root / "studies"}"',
                f'portfolio_root = "{workspace_root / "portfolio"}"',
                f'med_deepscientist_runtime_root = "{workspace_root / "ops" / "med-deepscientist" / "runtime"}"',
                'med_deepscientist_repo_root = "/Users/gaofeng/workspace/med-deepscientist"',
                'default_publication_profile = "general_medical_journal"',
                'default_citation_style = "AMA"',
                "enable_medical_overlay = true",
                'medical_overlay_scope = "workspace"',
                'medical_overlay_skills = ["intake-audit", "scout", "baseline", "idea", "decision", "experiment", "analysis-campaign", "write", "review", "rebuttal", "finalize"]',
                'medical_overlay_bootstrap_mode = "ensure_ready"',
                'research_route_bias_policy = "high_plasticity_medical"',
                'preferred_study_archetypes = ["clinical_classifier", "llm_agent_clinical_task"]',
                'default_startup_anchor_policy = "scout_first_for_continue_existing_state"',
                'legacy_code_execution_policy = "forbid_without_user_approval"',
                'public_data_discovery_policy = "required_for_scout_route_selection"',
                'startup_boundary_requirements = ["paper_framing", "journal_shortlist", "evidence_package"]',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    config_env = workspace_root / "ops" / "medautoscience" / "config.env"
    config_env.parent.mkdir(parents=True, exist_ok=True)
    config_env.write_text(
        "\n".join(
            [
                'MED_AUTOSCIENCE_REPO="/Users/gaofeng/workspace/med-autoscience"',
                f'MED_AUTOSCIENCE_PROFILE="{active_profile}"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    hermes_repo_root = tmp_path / "_external" / "hermes-agent"
    hermes_home_root = tmp_path / ".hermes"
    result = module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="nfpitnet",
        dry_run=False,
        force=False,
        hermes_agent_repo_root=hermes_repo_root,
        hermes_home_root=hermes_home_root,
    )

    assert result["profile_path"] == str(active_profile)
    assert str(active_profile) in result["upgraded_files"]
    assert not (profiles_root / "nfpitnet.local.toml").exists()

    active_profile_text = active_profile.read_text(encoding="utf-8")
    assert f'hermes_agent_repo_root = "{hermes_repo_root}"' in active_profile_text
    assert f'hermes_home_root = "{hermes_home_root}"' in active_profile_text
    assert 'preferred_study_archetypes = ["clinical_classifier", "llm_agent_clinical_task"]' in active_profile_text
