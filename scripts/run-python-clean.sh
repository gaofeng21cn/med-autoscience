#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd "${script_dir}/.." && pwd -P)"
cd "${repo_root}"

cleanup_tmp_root=0
if [[ -n "${MAS_CLEAN_RUNNER_TMP_ROOT:-}" ]]; then
  tmp_root="${MAS_CLEAN_RUNNER_TMP_ROOT}"
else
  tmp_root="$(mktemp -d "${TMPDIR:-/tmp}/mas-python-run.XXXXXX")"
  cleanup_tmp_root=1
fi

cleanup() {
  if [[ "${cleanup_tmp_root}" == "1" ]]; then
    rm -rf "${tmp_root}"
  fi
}
trap cleanup EXIT

mkdir -p "${tmp_root}"

resolve_for_boundary_check() {
  local raw_path="${1}"
  local path
  local parent
  local base

  if [[ -z "${raw_path}" ]]; then
    return 1
  fi

  case "${raw_path}" in
    "~")
      path="${HOME}"
      ;;
    "~/"*)
      path="${HOME}/${raw_path#~/}"
      ;;
    /*)
      path="${raw_path}"
      ;;
    *)
      path="${repo_root}/${raw_path}"
      ;;
  esac

  if [[ -d "${path}" ]]; then
    (cd "${path}" >/dev/null 2>&1 && pwd -P)
    return
  fi

  parent="$(dirname "${path}")"
  base="$(basename "${path}")"
  if [[ -d "${parent}" ]]; then
    printf '%s/%s\n' "$(cd "${parent}" >/dev/null 2>&1 && pwd -P)" "${base}"
    return
  fi

  return 1
}

path_is_inside_checkout() {
  local raw_path="${1}"
  local resolved

  resolved="$(resolve_for_boundary_check "${raw_path}")" || return 1
  [[ "${resolved}" == "${repo_root}" || "${resolved}" == "${repo_root}/"* ]]
}

if path_is_inside_checkout "${UV_PROJECT_ENVIRONMENT:-}"; then
  unset UV_PROJECT_ENVIRONMENT
fi

if path_is_inside_checkout "${PYTHONPYCACHEPREFIX:-}"; then
  unset PYTHONPYCACHEPREFIX
fi

export PYTHONDONTWRITEBYTECODE=1
export PYTHONPYCACHEPREFIX="${PYTHONPYCACHEPREFIX:-${tmp_root}/pycache}"
export UV_PROJECT_ENVIRONMENT="${UV_PROJECT_ENVIRONMENT:-${tmp_root}/venv}"
pythonpath_root="${MAS_CLEAN_RUNNER_SOURCE_ROOT:-${repo_root}}"
export PYTHONPATH="${pythonpath_root}/src:${pythonpath_root}${PYTHONPATH:+:${PYTHONPATH}}"
export PYTEST_ADDOPTS="${PYTEST_ADDOPTS:-} -p no:cacheprovider -o cache_dir=${tmp_root}/pytest-cache"

cli_apply_requires_analysis_extra() {
  if [[ "$#" -lt 3 ]]; then
    return 1
  fi
  if [[ "${1}" != "-m" || "${2}" != "med_autoscience.cli" ]]; then
    return 1
  fi

  local command="${3}"
  local subcommand="${4:-}"
  local start_index=4
  if [[ "${command}" == "runtime" ]]; then
    command="${subcommand}"
    start_index=5
  elif [[ "${command}" == "sidecar" ]]; then
    if [[ "${subcommand}" == "dispatch" ]]; then
      return 0
    fi
    return 1
  fi

  case "${command}" in
    domain-route-reconcile|owner-route-reconcile|domain-owner-action-dispatch)
      local arg
      for arg in "${@:start_index}"; do
        if [[ "${arg}" == "--apply" ]]; then
          return 0
        fi
      done
      ;;
  esac
  return 1
}

analysis_extra_enabled=0
if [[ "${MAS_CLEAN_RUNNER_ANALYSIS_EXTRA:-0}" == "1" ]] || cli_apply_requires_analysis_extra "$@"; then
  analysis_extra_enabled=1
  export MAS_CLEAN_RUNNER_ANALYSIS_EXTRA=1
fi

entrypoint_bin="${tmp_root}/bin"
mkdir -p "${entrypoint_bin}"

write_launcher() {
  local name="${1}"
  local module="${2}"
  local path="${entrypoint_bin}/${name}"

  {
    printf '#!/usr/bin/env bash\n'
    printf 'set -euo pipefail\n'
    printf 'exec "%s/scripts/run-python-clean.sh" -m "%s" "$@"\n' "${repo_root}" "${module}"
  } >"${path}"
  chmod +x "${path}"
}

write_launcher medautosci med_autoscience.cli
write_launcher medautosci-mcp med_autoscience.mcp_server
export PATH="${entrypoint_bin}:${PATH}"

if [[ "${analysis_extra_enabled}" == "1" ]]; then
  sync_marker="${tmp_root}/uv-sync.analysis.done"
else
  sync_marker="${tmp_root}/uv-sync.done"
fi
if [[ "${MAS_CLEAN_RUNNER_SKIP_SYNC:-0}" != "1" && ! -f "${sync_marker}" ]]; then
  uv_sync_args=(uv sync --frozen --group dev --no-install-project --inexact)
  if [[ "${analysis_extra_enabled}" == "1" ]]; then
    uv_sync_args+=(--extra analysis)
  fi
  UV_NO_SYNC=0 "${uv_sync_args[@]}"
  touch "${sync_marker}"
  if [[ "${analysis_extra_enabled}" == "1" ]]; then
    touch "${tmp_root}/uv-sync.done"
  fi
fi
export MAS_CLEAN_RUNNER_SKIP_SYNC=1

venv_python="${UV_PROJECT_ENVIRONMENT}/bin/python"
if [[ ! -x "${venv_python}" ]]; then
  echo "run-python-clean.sh: missing venv Python after dependency sync: ${venv_python}" >&2
  exit 1
fi

exec "${venv_python}" "$@"
