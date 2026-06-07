from __future__ import annotations

from pathlib import Path


DEVELOPER_SUPERVISOR_MODE_ARGS = "--apply-safe-actions --developer-supervisor-mode developer_apply_safe"
DEVELOPER_SUPERVISOR_CONSUME_ARGS = "--mode developer_apply_safe"
DEVELOPER_SUPERVISOR_EXECUTE_DISPATCH_ARGS = "--mode developer_apply_safe"


def _render_behavior_equivalence_gate() -> str:
    return (
        "schema_version: v1\n"
        "phase_25_ready: true\n"
        "critical_overrides: []\n"
    )


def _render_medautosci_shared(profile_relpath: Path) -> str:
    return (
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n\n"
        'SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"\n'
        'MEDAUTOSCI_OPS_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"\n'
        'WORKSPACE_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"\n'
        f'DEFAULT_PROFILE="${{WORKSPACE_ROOT}}/{profile_relpath.as_posix()}"\n'
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
        'if [[ ! -f "${MED_AUTOSCIENCE_REPO_RESOLVED}/pyproject.toml" || ! -d "${MED_AUTOSCIENCE_REPO_RESOLVED}/src/med_autoscience" ]]; then\n'
        '  echo "MED_AUTOSCIENCE_REPO does not point to a valid MedAutoScience checkout: ${MED_AUTOSCIENCE_REPO_RESOLVED}" >&2\n'
        "  exit 1\n"
        "fi\n\n"
        'if [[ ! -f "${PROFILE_PATH}" ]]; then\n'
        '  echo "Profile file not found: ${PROFILE_PATH}" >&2\n'
        "  exit 1\n"
        "fi\n\n"
        'WORKSPACE_PYTHON="${WORKSPACE_ROOT}/.venv/bin/python3"\n'
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
        'MED_AUTOSCIENCE_NODE_BIN="${MED_AUTOSCIENCE_NODE_BIN:-$(command -v node || true)}"\n'
        'if [[ -n "${MED_AUTOSCIENCE_NODE_BIN}" ]]; then\n'
        '  if [[ "${MED_AUTOSCIENCE_NODE_BIN}" != /* ]]; then\n'
        '    echo "MED_AUTOSCIENCE_NODE_BIN must be an absolute path: ${MED_AUTOSCIENCE_NODE_BIN}" >&2\n'
        "    exit 1\n"
        "  fi\n"
        '  if [[ ! -x "${MED_AUTOSCIENCE_NODE_BIN}" ]]; then\n'
        '    echo "MED_AUTOSCIENCE_NODE_BIN is not executable: ${MED_AUTOSCIENCE_NODE_BIN}" >&2\n'
        "    exit 1\n"
        "  fi\n"
        "fi\n\n"
        'export MED_AUTOSCIENCE_NODE_BIN\n\n'
        "run_medautosci() {\n"
        '  if [[ ! -x "${WORKSPACE_PYTHON}" ]]; then\n'
        '    echo "Workspace Python is missing or not executable: ${WORKSPACE_PYTHON}" >&2\n'
        "    exit 1\n"
        "  fi\n"
        "  PYTHONDONTWRITEBYTECODE=1 \\\n"
        '  "${WORKSPACE_PYTHON}" -m med_autoscience.cli "$@"\n'
        "}\n"
    )


def _render_forward_script(command: str, *, with_profile: bool = False) -> str:
    extra = f' --profile "${{PROFILE_PATH}}"' if with_profile else ""
    return (
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"\n\n'
        f'run_medautosci {command}{extra} "$@"\n'
    )


def _render_bootstrap_script() -> str:
    return (
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"\n\n'
        "workspace_python_has_medautosci_cli() {\n"
        '  [[ -x "${WORKSPACE_PYTHON}" ]] || return 1\n'
        '  PYTHONDONTWRITEBYTECODE=1 "${WORKSPACE_PYTHON}" -c "import med_autoscience.cli" >/dev/null 2>&1\n'
        "}\n\n"
        "if ! workspace_python_has_medautosci_cli; then\n"
        '  MED_AUTOSCIENCE_UV_BIN="${MED_AUTOSCIENCE_UV_BIN:-$(command -v uv || true)}"\n'
        '  if [[ -z "${MED_AUTOSCIENCE_UV_BIN}" || "${MED_AUTOSCIENCE_UV_BIN}" != /* || ! -x "${MED_AUTOSCIENCE_UV_BIN}" ]]; then\n'
        '    echo "Workspace Python is missing med_autoscience.cli and MED_AUTOSCIENCE_UV_BIN is not executable: ${WORKSPACE_PYTHON}" >&2\n'
        "    exit 1\n"
        "  fi\n"
        '  PYTHONDONTWRITEBYTECODE=1 "${MED_AUTOSCIENCE_UV_BIN}" run --directory "${MED_AUTOSCIENCE_REPO_RESOLVED}" python -m med_autoscience.cli workspace bootstrap --profile "${PROFILE_PATH}" "$@"\n'
        "  exit $?\n"
        "fi\n\n"
        'run_medautosci workspace bootstrap --profile "${PROFILE_PATH}" "$@"\n'
    )


def _render_profile_optional_forward_script(command: str) -> str:
    return (
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"\n\n'
        'args=("$@")\n'
        "has_profile=0\n"
        'for arg in ${args[@]+"${args[@]}"}; do\n'
        '  if [[ "${arg}" == "--profile" ]]; then\n'
        "    has_profile=1\n"
        "    break\n"
        "  fi\n"
        "done\n\n"
        'if [[ "${has_profile}" -eq 1 ]]; then\n'
        f'  run_medautosci {command} ${{args[@]+"${{args[@]}}"}}\n'
        "else\n"
        f'  run_medautosci {command} --profile "${{PROFILE_PATH}}" ${{args[@]+"${{args[@]}}"}}\n'
        "fi\n"
    )


def _render_study_progress_script() -> str:
    return (
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"\n\n'
        'args=("$@")\n'
        'if [[ "${#args[@]}" -gt 0 && "${args[0]}" != -* ]]; then\n'
        '  study_id="${args[0]}"\n'
        '  args=("${args[@]:1}")\n'
        '  run_medautosci study-progress --profile "${PROFILE_PATH}" --study-id "${study_id}" ${args[@]+"${args[@]}"}\n'
        "else\n"
        '  run_medautosci study-progress --profile "${PROFILE_PATH}" ${args[@]+"${args[@]}"}\n'
        "fi\n"
    )


def _render_domain_health_diagnostic_script(*, workspace_root: Path, runtime_quests_root: Path) -> str:
    relative_runtime_root = runtime_quests_root.relative_to(workspace_root).as_posix()
    return (
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"\n\n'
        f'WORKSPACE_RUNTIME_ROOT="${{WORKSPACE_ROOT}}/{relative_runtime_root}"\n\n'
        'apply_args=(--request-opl-stage-attempts --request-opl-owner-route-reconcile --apply)\n'
        'for arg in "$@"; do\n'
        '  if [[ "${arg}" == "--apply" || "${arg}" == "--dry-run" || "${arg}" == "--request-opl-stage-attempts" || "${arg}" == "--request-opl-owner-route-reconcile" ]]; then\n'
        '    apply_args=()\n'
        "    break\n"
        "  fi\n"
        "done\n\n"
        'run_medautosci runtime domain-health-diagnostic \\\n'
        '  --profile "${PROFILE_PATH}" \\\n'
        '  --runtime-root "${WORKSPACE_RUNTIME_ROOT}" \\\n'
        '  ${apply_args[@]+"${apply_args[@]}"} \\\n'
        '  "$@"\n'
    )


def _render_scan_domain_routes_script() -> str:
    return (
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"\n\n'
        'run_medautosci owner-route-reconcile \\\n'
        '  --profile "${PROFILE_PATH}" \\\n'
        '  "$@"\n'
    )


def _render_materialize_domain_action_requests_script() -> str:
    return (
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"\n\n'
        'apply_mode="--apply"\n'
        'for arg in "$@"; do\n'
        '  if [[ "${arg}" == "--apply" || "${arg}" == "--dry-run" ]]; then\n'
        '    apply_mode=""\n'
        "    break\n"
        "  fi\n"
        "done\n\n"
        'run_medautosci runtime domain-action-request-materialize \\\n'
        '  --profile "${PROFILE_PATH}" \\\n'
        f"  {DEVELOPER_SUPERVISOR_CONSUME_ARGS} \\\n"
        '  ${apply_mode:+"${apply_mode}"} \\\n'
        '  "$@"\n'
    )


def _render_supervisor_execute_dispatch_script() -> str:
    return (
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"\n\n'
        'apply_mode="--apply"\n'
        'for arg in "$@"; do\n'
        '  if [[ "${arg}" == "--apply" || "${arg}" == "--dry-run" ]]; then\n'
        '    apply_mode=""\n'
        "    break\n"
        "  fi\n"
        "done\n\n"
        'run_medautosci runtime domain-owner-action-dispatch \\\n'
        '  --profile "${PROFILE_PATH}" \\\n'
        f"  {DEVELOPER_SUPERVISOR_EXECUTE_DISPATCH_ARGS} \\\n"
        '  ${apply_mode:+"${apply_mode}"} \\\n'
        '  "$@"\n'
    )


def _render_mas_runtime_bridge_shared() -> str:
    return (
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n\n"
        'SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"\n'
        'MAS_OPS_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"\n'
        'WORKSPACE_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"\n'
        'MAS_CONFIG_ENV_PATH="${MAS_OPS_ROOT}/config.env"\n'
        'MEDAUTOSCI_SHARED_SH="${WORKSPACE_ROOT}/ops/medautoscience/bin/_shared.sh"\n\n'
        'if [[ ! -f "${MEDAUTOSCI_SHARED_SH}" ]]; then\n'
        '  echo "MedAutoScience shared entry is missing: ${MEDAUTOSCI_SHARED_SH}" >&2\n'
        "  exit 1\n"
        "fi\n\n"
        "# shellcheck disable=SC1090\n"
        'source "${MEDAUTOSCI_SHARED_SH}"\n\n'
        'if [[ -f "${MAS_CONFIG_ENV_PATH}" ]]; then\n'
        "  # shellcheck disable=SC1090\n"
        '  source "${MAS_CONFIG_ENV_PATH}"\n'
        "fi\n\n"
        "load_mas_runtime_bridge_contract() {\n"
        "  local payload_json\n"
        '  payload_json="$(\n'
        '    PYTHONDONTWRITEBYTECODE=1 "${WORKSPACE_PYTHON}" - "${PROFILE_PATH}" <<'"'"'PY'"'"'\n'
        "import json\n"
        "import sys\n\n"
        "from med_autoscience.profiles import load_profile, profile_to_dict\n"
        "from med_autoscience.workspace_contracts import inspect_workspace_contracts\n\n"
        "profile = load_profile(sys.argv[1])\n"
        "print(\n"
        "    json.dumps(\n"
        "        {\n"
        '            "profile": profile_to_dict(profile),\n'
        '            "contracts": inspect_workspace_contracts(profile),\n'
        "        },\n"
        "        ensure_ascii=False,\n"
        "    )\n"
        ")\n"
        "PY\n"
        '  )"\n\n'
        '  export MEDAUTOSCI_MAS_RUNTIME_BRIDGE_CONTRACT_JSON="${payload_json}"\n\n'
        "  local contract_lines\n"
        '  contract_lines="$(\n'
        '    CONTRACT_JSON="${payload_json}" PYTHONDONTWRITEBYTECODE=1 "${WORKSPACE_PYTHON}" - <<'"'"'PY'"'"'\n'
        "import json\n"
        "import os\n\n"
        'payload = json.loads(os.environ["CONTRACT_JSON"])\n'
        'profile = payload["profile"]\n'
        'contracts = payload["contracts"]\n'
        'runtime_contract = contracts["runtime_contract"]\n'
        'behavior_gate = contracts["behavior_gate"]\n\n'
        "pairs = {\n"
        '    "workspace_root": profile["workspace_root"],\n'
        '    "runtime_root": profile["runtime_root"],\n'
        '    "managed_runtime_quests_root_matches_layout": str(\n'
        '        bool(runtime_contract.get("checks", {}).get("managed_runtime_quests_root_matches_layout"))\n'
        '    ).lower(),\n'
        '    "runtime_contract_ready": str(bool(runtime_contract.get("ready"))).lower(),\n'
        '    "phase_25_ready": str(bool(behavior_gate.get("phase_25_ready"))).lower(),\n'
        "}\n\n"
        "for key, value in pairs.items():\n"
        '    print(f"{key}\\t{value}")\n'
        "PY\n"
        '  )"\n\n'
        '  while IFS=$'"'"'\\t'"'"' read -r key value; do\n'
        '    case "${key}" in\n'
        '      workspace_root) MAS_WORKSPACE_ROOT="${value}" ;;\n'
        '      runtime_root) MAS_RUNTIME_QUESTS_ROOT="${value}" ;;\n'
        '      managed_runtime_quests_root_matches_layout) RUNTIME_ROOT_MATCHES_MANAGED_RUNTIME_LAYOUT="${value}" ;;\n'
        '      runtime_contract_ready) MAS_RUNTIME_CONTRACT_READY="${value}" ;;\n'
        '      phase_25_ready) MAS_PHASE_25_READY="${value}" ;;\n'
        "    esac\n"
        '  done <<< "${contract_lines}"\n\n'
        '  if [[ "${RUNTIME_ROOT_MATCHES_MANAGED_RUNTIME_LAYOUT:-false}" != "true" ]]; then\n'
        '    echo "runtime_root does not match managed runtime layout for profile ${PROFILE_PATH}" >&2\n'
        "    exit 1\n"
        "  fi\n\n"
        '  if [[ -z "${MAS_RUNTIME_QUESTS_ROOT:-}" ]]; then\n'
        '    echo "Failed to resolve MAS runtime_root from profile ${PROFILE_PATH}" >&2\n'
        "    exit 1\n"
        "  fi\n"
        "}\n\n"
        "render_mas_runtime_bridge_config_json() {\n"
        '  CONTRACT_JSON="${MEDAUTOSCI_MAS_RUNTIME_BRIDGE_CONTRACT_JSON}" \\\n'
        '  PYTHONDONTWRITEBYTECODE=1 "${WORKSPACE_PYTHON}" - <<'"'"'PY'"'"'\n'
        "import json\n"
        "import os\n\n"
        'payload = json.loads(os.environ["CONTRACT_JSON"])\n'
        'profile = payload["profile"]\n'
        'contracts = payload["contracts"]\n\n'
        "print(\n"
        "    json.dumps(\n"
        "        {\n"
        '            "workspace_root": profile["workspace_root"],\n'
        '            "runtime_root": profile["runtime_root"],\n'
        '            "managed_runtime_home": profile["managed_runtime_home"],\n'
        '            "opl_runtime_ref": profile["opl_runtime_ref"],\n'
        '            "external_mds_runnable_dependency": False,\n'
        '            "default_webui": "mas_progress_portal",\n'
        '            "runtime_contract_ready": contracts["runtime_contract"]["ready"],\n'
        '            "phase_25_ready": contracts["behavior_gate"]["phase_25_ready"],\n'
        '            "behavior_gate_path": contracts["behavior_gate"]["path"],\n'
        "        },\n"
        "        ensure_ascii=False,\n"
        "        indent=2,\n"
        "    )\n"
        ")\n"
        "PY\n"
        "}\n\n"
    )


def _render_mas_runtime_bridge_forward(
    command: str,
    *,
    with_profile: bool = True,
    command_suffix: str = "",
) -> str:
    profile_arg = ' --profile "${PROFILE_PATH}"' if with_profile else ""
    return (
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n\n"
        'SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"\n'
        "# shellcheck disable=SC1091\n"
        'source "${SCRIPT_DIR}/_shared.sh"\n\n'
        "load_mas_runtime_bridge_contract\n"
        f'run_medautosci {command}{profile_arg}{command_suffix} "$@"\n'
    )


def _render_mas_runtime_bridge_stop_script() -> str:
    return (
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n\n"
        'SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"\n'
        "# shellcheck disable=SC1091\n"
        'source "${SCRIPT_DIR}/_shared.sh"\n\n'
        "load_mas_runtime_bridge_contract\n"
        'if [[ "$#" -eq 0 ]]; then\n'
        '  echo "MAS controlled pause requires --study-id <study_id> or --study-root <path>." >&2\n'
        "  exit 2\n"
        "fi\n"
        'echo "MAS pause-runtime is retired; use OPL current_control_state / human gate tooling." >&2\n'
        "exit 2\n"
    )


def _render_mas_runtime_bridge_show_config() -> str:
    return (
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n\n"
        'SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"\n'
        "# shellcheck disable=SC1091\n"
        'source "${SCRIPT_DIR}/_shared.sh"\n\n'
        "load_mas_runtime_bridge_contract\n"
        "render_mas_runtime_bridge_config_json\n"
    )
