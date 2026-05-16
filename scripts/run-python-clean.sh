#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
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

export PYTHONDONTWRITEBYTECODE=1
export PYTHONPYCACHEPREFIX="${PYTHONPYCACHEPREFIX:-${tmp_root}/pycache}"
export PYTHONPATH="${repo_root}/src:${repo_root}${PYTHONPATH:+:${PYTHONPATH}}"
export PYTEST_ADDOPTS="${PYTEST_ADDOPTS:-} -p no:cacheprovider -o cache_dir=${tmp_root}/pytest-cache"

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

sync_marker="${tmp_root}/uv-sync.done"
if [[ "${MAS_CLEAN_RUNNER_SKIP_SYNC:-0}" != "1" && "${UV_NO_SYNC:-0}" != "1" && ! -f "${sync_marker}" ]]; then
  uv sync --frozen --group dev --no-install-project --inexact
  touch "${sync_marker}"
fi
export MAS_CLEAN_RUNNER_SKIP_SYNC=1

venv_python="${repo_root}/.venv/bin/python"
if [[ ! -x "${venv_python}" ]]; then
  echo "run-python-clean.sh: missing venv Python after dependency sync: ${venv_python}" >&2
  exit 1
fi

exec "${venv_python}" "$@"
