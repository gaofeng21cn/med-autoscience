from __future__ import annotations

from pathlib import Path


DEVELOPER_SUPERVISOR_MODE_ARGS = "--apply-safe-actions --developer-supervisor-mode developer_apply_safe"
DEVELOPER_SUPERVISOR_CONSUME_ARGS = "--mode developer_apply_safe"
DEVELOPER_SUPERVISOR_EXECUTE_DISPATCH_ARGS = "--mode developer_apply_safe"


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
        'WORKSPACE_PYTHON="${WORKSPACE_ROOT}/ops/medautoscience/.venv/bin/python3"\n'
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
        'apply_args=(--request-opl-stage-attempts --dry-run)\n'
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
