from __future__ import annotations

from pathlib import Path


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
        '  "${MED_AUTOSCIENCE_UV_BIN}" run --directory "${MED_AUTOSCIENCE_REPO_RESOLVED}" python -m med_autoscience.cli "$@"\n'
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


def _render_profile_optional_forward_script(command: str) -> str:
    return (
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
        f'  run_medautosci {command} "${{args[@]}}"\n'
        "else\n"
        f'  run_medautosci {command} --profile "${{PROFILE_PATH}}" "${{args[@]}}"\n'
        "fi\n"
    )


def _render_watch_runtime_script(*, runtime_quests_root: Path) -> str:
    relative_runtime_root = runtime_quests_root.relative_to(runtime_quests_root.parents[3]).as_posix()
    return (
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"\n\n'
        f'WORKSPACE_RUNTIME_ROOT="${{WORKSPACE_ROOT}}/{relative_runtime_root}"\n\n'
        'run_medautosci runtime watch \\\n'
        '  --profile "${PROFILE_PATH}" \\\n'
        '  --runtime-root "${WORKSPACE_RUNTIME_ROOT}" \\\n'
        '  --ensure-study-runtimes \\\n'
        '  --apply \\\n'
        '  --loop \\\n'
        '  "$@"\n'
    )


def _render_watch_runtime_service_runner() -> str:
    return (
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'source "$(cd "$(dirname "$0")" && pwd)/_shared.sh"\n\n'
        'WATCH_RUNTIME_INTERVAL_SECONDS="${WATCH_RUNTIME_INTERVAL_SECONDS:-300}"\n'
        'WATCH_RUNTIME_SCRIPT="${WORKSPACE_ROOT}/ops/medautoscience/bin/watch-runtime"\n\n'
        'if [[ ! -x "${WATCH_RUNTIME_SCRIPT}" ]]; then\n'
        '  echo "watch-runtime entry is missing or not executable: ${WATCH_RUNTIME_SCRIPT}" >&2\n'
        "  exit 1\n"
        "fi\n\n"
        'exec "${WATCH_RUNTIME_SCRIPT}" --interval-seconds "${WATCH_RUNTIME_INTERVAL_SECONDS}" "$@"\n'
    )


def _render_med_deepscientist_shared() -> str:
    return (
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n\n"
        'SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"\n'
        'MED_DEEPSCIENTIST_OPS_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"\n'
        'WORKSPACE_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"\n'
        'MED_DEEPSCIENTIST_CONFIG_ENV_PATH="${MED_DEEPSCIENTIST_OPS_ROOT}/config.env"\n'
        'MEDAUTOSCI_SHARED_SH="${WORKSPACE_ROOT}/ops/medautoscience/bin/_shared.sh"\n\n'
        'if [[ ! -f "${MEDAUTOSCI_SHARED_SH}" ]]; then\n'
        '  echo "MedAutoScience shared entry is missing: ${MEDAUTOSCI_SHARED_SH}" >&2\n'
        "  exit 1\n"
        "fi\n\n"
        "# shellcheck disable=SC1090\n"
        'source "${MEDAUTOSCI_SHARED_SH}"\n\n'
        'if [[ -f "${MED_DEEPSCIENTIST_CONFIG_ENV_PATH}" ]]; then\n'
        "  # shellcheck disable=SC1090\n"
        '  source "${MED_DEEPSCIENTIST_CONFIG_ENV_PATH}"\n'
        "fi\n\n"
        'if [[ -z "${MED_DEEPSCIENTIST_LAUNCHER:-}" ]]; then\n'
        '  echo "MED_DEEPSCIENTIST_LAUNCHER is not configured. Set it in ${MED_DEEPSCIENTIST_CONFIG_ENV_PATH}." >&2\n'
        "  exit 1\n"
        "fi\n\n"
        'if [[ "${MED_DEEPSCIENTIST_LAUNCHER}" != /* ]]; then\n'
        '  echo "MED_DEEPSCIENTIST_LAUNCHER must be an absolute path: ${MED_DEEPSCIENTIST_LAUNCHER}" >&2\n'
        "  exit 1\n"
        "fi\n\n"
        'if [[ ! -x "${MED_DEEPSCIENTIST_LAUNCHER}" ]]; then\n'
        '  echo "MED_DEEPSCIENTIST_LAUNCHER is not executable: ${MED_DEEPSCIENTIST_LAUNCHER}" >&2\n'
        "  exit 1\n"
        "fi\n\n"
        "load_med_deepscientist_contract() {\n"
        "  local payload_json\n"
        '  payload_json="$(\n'
        '    uv run --directory "${MED_AUTOSCIENCE_REPO_RESOLVED}" python - "${PROFILE_PATH}" <<'"'"'PY'"'"'\n'
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
        '  export MEDAUTOSCI_MED_DEEPSCIENTIST_CONTRACT_JSON="${payload_json}"\n\n'
        "  local contract_lines\n"
        '  contract_lines="$(\n'
        '    CONTRACT_JSON="${payload_json}" uv run --directory "${MED_AUTOSCIENCE_REPO_RESOLVED}" python - <<'"'"'PY'"'"'\n'
        "import json\n"
        "import os\n\n"
        'payload = json.loads(os.environ["CONTRACT_JSON"])\n'
        'profile = payload["profile"]\n'
        'contracts = payload["contracts"]\n'
        'runtime_contract = contracts["runtime_contract"]\n'
        'launcher_contract = contracts["launcher_contract"]\n'
        'behavior_gate = contracts["behavior_gate"]\n\n'
        "pairs = {\n"
        '    "workspace_root": profile["workspace_root"],\n'
        '    "runtime_root": profile["runtime_root"],\n'
        '    "med_deepscientist_runtime_root": profile["med_deepscientist_runtime_root"],\n'
        '    "med_deepscientist_repo_root": profile.get("med_deepscientist_repo_root") or "",\n'
        '    "runtime_root_matches_med_deepscientist_runtime": str(\n'
        '        bool(runtime_contract.get("checks", {}).get("runtime_root_matches_med_deepscientist_runtime"))\n'
        '    ).lower(),\n'
        '    "runtime_contract_ready": str(bool(runtime_contract.get("ready"))).lower(),\n'
        '    "launcher_contract_ready": str(bool(launcher_contract.get("ready"))).lower(),\n'
        '    "phase_25_ready": str(bool(behavior_gate.get("phase_25_ready"))).lower(),\n'
        "}\n\n"
        "for key, value in pairs.items():\n"
        '    print(f"{key}\\t{value}")\n'
        "PY\n"
        '  )"\n\n'
        '  while IFS=$'"'"'\\t'"'"' read -r key value; do\n'
        '    case "${key}" in\n'
        '      workspace_root) MED_DEEPSCIENTIST_WORKSPACE_ROOT="${value}" ;;\n'
        '      runtime_root) MED_DEEPSCIENTIST_RUNTIME_ROOT="${value}" ;;\n'
        '      med_deepscientist_runtime_root) MED_DEEPSCIENTIST_HOME="${value}" ;;\n'
        '      med_deepscientist_repo_root) MED_DEEPSCIENTIST_REPO_ROOT_AUDIT="${value}" ;;\n'
        '      runtime_root_matches_med_deepscientist_runtime) RUNTIME_ROOT_MATCHES_MED_DEEPSCIENTIST_RUNTIME="${value}" ;;\n'
        '      runtime_contract_ready) MED_DEEPSCIENTIST_RUNTIME_CONTRACT_READY="${value}" ;;\n'
        '      launcher_contract_ready) MED_DEEPSCIENTIST_LAUNCHER_CONTRACT_READY="${value}" ;;\n'
        '      phase_25_ready) MED_DEEPSCIENTIST_PHASE_25_READY="${value}" ;;\n'
        "    esac\n"
        '  done <<< "${contract_lines}"\n\n'
        '  if [[ "${RUNTIME_ROOT_MATCHES_MED_DEEPSCIENTIST_RUNTIME:-false}" != "true" ]]; then\n'
        '    echo "runtime_root does not match med_deepscientist_runtime_root/quests for profile ${PROFILE_PATH}" >&2\n'
        "    exit 1\n"
        "  fi\n\n"
        '  if [[ -z "${MED_DEEPSCIENTIST_HOME:-}" ]]; then\n'
        '    echo "Failed to resolve med_deepscientist_runtime_root from profile ${PROFILE_PATH}" >&2\n'
        "    exit 1\n"
        "  fi\n"
        "}\n\n"
        "render_med_deepscientist_config_json() {\n"
        '  CONTRACT_JSON="${MEDAUTOSCI_MED_DEEPSCIENTIST_CONTRACT_JSON}" \\\n'
        '  LAUNCHER_PATH="${MED_DEEPSCIENTIST_LAUNCHER}" \\\n'
        '  python3 - <<'"'"'PY'"'"'\n'
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
        '            "med_deepscientist_runtime_root": profile["med_deepscientist_runtime_root"],\n'
        '            "med_deepscientist_repo_root": profile.get("med_deepscientist_repo_root"),\n'
        '            "launcher": os.environ["LAUNCHER_PATH"],\n'
        '            "runtime_contract_ready": contracts["runtime_contract"]["ready"],\n'
        '            "launcher_contract_ready": contracts["launcher_contract"]["ready"],\n'
        '            "phase_25_ready": contracts["behavior_gate"]["phase_25_ready"],\n'
        '            "behavior_gate_path": contracts["behavior_gate"]["path"],\n'
        "        },\n"
        "        ensure_ascii=False,\n"
        "        indent=2,\n"
        "    )\n"
        ")\n"
        "PY\n"
        "}\n\n"
        "run_med_deepscientist_launcher() {\n"
        '  exec "${MED_DEEPSCIENTIST_LAUNCHER}" --home "${MED_DEEPSCIENTIST_HOME}" "$@"\n'
        "}\n"
    )


def _render_med_deepscientist_forward(script_command: str) -> str:
    return (
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n\n"
        'SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"\n'
        "# shellcheck disable=SC1091\n"
        'source "${SCRIPT_DIR}/_shared.sh"\n\n'
        "load_med_deepscientist_contract\n"
        f"run_med_deepscientist_launcher {script_command} \"$@\"\n"
    )


def _render_med_deepscientist_show_config() -> str:
    return (
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n\n"
        'SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"\n'
        "# shellcheck disable=SC1091\n"
        'source "${SCRIPT_DIR}/_shared.sh"\n\n'
        "load_med_deepscientist_contract\n"
        "render_med_deepscientist_config_json\n"
    )
