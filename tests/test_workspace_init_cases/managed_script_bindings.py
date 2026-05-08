from __future__ import annotations

import importlib
import shutil
from pathlib import Path


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
    assert 'run_medautosci runtime ensure-supervision --profile "${PROFILE_PATH}" "$@"' in install_text


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
    assert 'run_medautosci runtime ensure-supervision --profile "${PROFILE_PATH}" "$@"' in install_text


def test_init_workspace_upgrades_medautoscience_config_with_detected_node_binding(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_init")
    entry_rendering = importlib.import_module("med_autoscience.controllers.workspace_entry_rendering")
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
    monkeypatch.setattr(entry_rendering.shutil, "which", lambda executable: str(detected_node) if executable == "node" else None)

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


def test_init_workspace_repairs_placeholder_medautoscience_config_without_clobbering_profile(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_init")
    workspace_root = tmp_path / "placeholder-config-workspace"
    active_profile = workspace_root / "ops" / "medautoscience" / "profiles" / "dm-cvd.workspace.toml"
    config_env = workspace_root / "ops" / "medautoscience" / "config.env"
    config_env.parent.mkdir(parents=True, exist_ok=True)
    config_env.write_text(
        "\n".join(
            [
                'MED_AUTOSCIENCE_REPO="/ABS/PATH/TO/med-autoscience"',
                'MED_AUTOSCIENCE_UV_BIN="/ABS/PATH/TO/uv"',
                'MED_AUTOSCIENCE_RSCRIPT_BIN="/ABS/PATH/TO/Rscript"',
                f'MED_AUTOSCIENCE_PROFILE="{active_profile}"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="dm-cvd",
        dry_run=False,
        force=False,
    )

    assert str(config_env) in result["upgraded_files"]
    config_text = config_env.read_text(encoding="utf-8")
    assert 'MED_AUTOSCIENCE_REPO="/ABS/PATH/TO/med-autoscience"' not in config_text
    assert 'MED_AUTOSCIENCE_UV_BIN="/ABS/PATH/TO/uv"' not in config_text
    assert f'MED_AUTOSCIENCE_REPO="{module._medautoscience_repo_root()}"' in config_text
    uv_path = shutil.which("uv")
    if uv_path:
        assert f'MED_AUTOSCIENCE_UV_BIN="{uv_path}"' in config_text
    assert f'MED_AUTOSCIENCE_PROFILE="{active_profile}"' in config_text


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
