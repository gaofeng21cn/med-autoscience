#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd "${script_dir}/.." && pwd -P)"
cd "${repo_root}"

cleanup_tmp_root=0
reuse_env_enabled=0
if [[ "${MAS_CLEAN_RUNNER_REUSE_ENV:-0}" == "1" ]]; then
  reuse_env_enabled=1
  if [[ -n "${MAS_CLEAN_RUNNER_REUSE_ROOT:-}" ]]; then
    tmp_root="${MAS_CLEAN_RUNNER_REUSE_ROOT}"
  else
    tmp_root="${XDG_CACHE_HOME:-${HOME}/.cache}/med-autoscience/clean-runner"
  fi
elif [[ -n "${MAS_CLEAN_RUNNER_TMP_ROOT:-}" ]]; then
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

resolve_for_boundary_check() {
  local raw_path="${1}"
  local path
  local parent
  local base
  local suffix

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

  parent="${path}"
  while [[ ! -d "${parent}" && "${parent}" != "/" ]]; do
    parent="$(dirname "${parent}")"
  done
  if [[ -d "${parent}" ]]; then
    suffix="${path#"${parent}"}"
    if [[ "${parent}" == "/" ]]; then
      printf '/%s\n' "${suffix#/}"
    else
      printf '%s%s\n' "$(cd "${parent}" >/dev/null 2>&1 && pwd -P)" "${suffix}"
    fi
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

if [[ "${reuse_env_enabled}" == "1" ]]; then
  if path_is_inside_checkout "${tmp_root}"; then
    echo "run-python-clean.sh: reuse root must be outside the checkout: ${tmp_root}" >&2
    exit 2
  fi
  unset UV_PROJECT_ENVIRONMENT
  unset PYTHONPYCACHEPREFIX
  unset UV_CACHE_DIR
fi

mkdir -p "${tmp_root}"

if path_is_inside_checkout "${UV_PROJECT_ENVIRONMENT:-}"; then
  unset UV_PROJECT_ENVIRONMENT
fi

if path_is_inside_checkout "${PYTHONPYCACHEPREFIX:-}"; then
  unset PYTHONPYCACHEPREFIX
fi

if [[ "${MAS_CLEAN_RUNNER_PRESERVE_UV_CACHE:-0}" != "1" ]] || path_is_inside_checkout "${UV_CACHE_DIR:-}"; then
  unset UV_CACHE_DIR
fi

if [[ "${reuse_env_enabled}" == "1" ]]; then
  default_uv_cache_dir="${tmp_root}/uv-cache"
else
  default_uv_cache_dir="${MAS_CLEAN_RUNNER_DEFAULT_UV_CACHE_DIR:-${tmp_root}/uv-cache}"
fi
if path_is_inside_checkout "${default_uv_cache_dir}"; then
  echo "run-python-clean.sh: default uv cache must be outside the checkout: ${default_uv_cache_dir}" >&2
  exit 2
fi

export PYTHONDONTWRITEBYTECODE=1
export PYTHONPYCACHEPREFIX="${PYTHONPYCACHEPREFIX:-${tmp_root}/pycache}"
export UV_PROJECT_ENVIRONMENT="${UV_PROJECT_ENVIRONMENT:-${tmp_root}/venv}"
export UV_CACHE_DIR="${UV_CACHE_DIR:-${default_uv_cache_dir}}"
mkdir -p "${UV_CACHE_DIR}"
egg_info_base="${MAS_CLEAN_RUNNER_EGG_INFO_BASE:-${tmp_root}/egg-info}"
if path_is_inside_checkout "${egg_info_base}"; then
  echo "run-python-clean.sh: egg-info base must be outside the checkout: ${egg_info_base}" >&2
  exit 2
fi
mkdir -p "${egg_info_base}"
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
clean_runner_sync_fingerprint() {
  local analysis_state="${1}"
  {
    printf 'analysis_extra=%s\n' "${analysis_state}"
    if [[ -f "${repo_root}/pyproject.toml" ]]; then
      shasum -a 256 "${repo_root}/pyproject.toml"
    fi
    if [[ -f "${repo_root}/uv.lock" ]]; then
      shasum -a 256 "${repo_root}/uv.lock"
    fi
  } | shasum -a 256 | awk '{print $1}'
}
sync_fingerprint="$(clean_runner_sync_fingerprint "${analysis_extra_enabled}")"
venv_python="${UV_PROJECT_ENVIRONMENT}/bin/python"
sync_required=1
if [[ -f "${sync_marker}" && -x "${venv_python}" ]]; then
  if [[ "${reuse_env_enabled}" == "1" ]]; then
    if [[ "$(cat "${sync_marker}")" == "${sync_fingerprint}" ]]; then
      sync_required=0
    fi
  elif [[ "${MAS_CLEAN_RUNNER_SKIP_SYNC:-0}" == "1" ]]; then
    sync_required=0
  fi
fi
if [[ "${sync_required}" == "1" ]]; then
  uv_sync_args=(uv sync --frozen --group dev --no-install-project --inexact)
  uv_sync_args+=("-C--global-option=egg_info" "-C--global-option=--egg-base=${egg_info_base}")
  if [[ "${analysis_extra_enabled}" == "1" ]]; then
    uv_sync_args+=(--extra analysis)
  fi
  UV_NO_SYNC=0 "${uv_sync_args[@]}"
  printf '%s\n' "${sync_fingerprint}" >"${sync_marker}"
  if [[ "${analysis_extra_enabled}" == "1" ]]; then
    printf '%s\n' "$(clean_runner_sync_fingerprint 0)" >"${tmp_root}/uv-sync.done"
  fi
fi
export MAS_CLEAN_RUNNER_SKIP_SYNC=1

if [[ ! -x "${venv_python}" ]]; then
  echo "run-python-clean.sh: missing venv Python after dependency sync: ${venv_python}" >&2
  exit 1
fi

set +e
"${venv_python}" "$@"
exit_code="$?"
set -e
exit "${exit_code}"
