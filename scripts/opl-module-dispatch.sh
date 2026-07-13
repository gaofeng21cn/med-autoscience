#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
state_base="${OPL_MODULE_RUNTIME_ROOT:-${XDG_STATE_HOME:-${HOME}/.local/state}/one-person-lab/modules}"
cache_base="${OPL_MODULE_CACHE_ROOT:-${XDG_CACHE_HOME:-${HOME}/.cache}/one-person-lab/modules}"
runtime_root="${MAS_OPL_MODULE_RUNTIME_ROOT:-${state_base%/}/medautoscience}"
cache_root="${MAS_OPL_MODULE_CACHE_ROOT:-${cache_base%/}/medautoscience}"
venv_python="${runtime_root}/venv/bin/python"

if [[ ! -x "${venv_python}" ]]; then
  echo "opl-module-dispatch.sh: missing OPL-managed MAS dependency environment: ${venv_python}" >&2
  echo "Run: opl connect install --module medautoscience" >&2
  exit 1
fi

export PYTHONPATH="${repo_root}/src"
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPYCACHEPREFIX="${runtime_root}/pycache"
export MAS_OPL_MODULE_CACHE_ROOT="${cache_root}"

exec "${venv_python}" -m med_autoscience.opl_module_carrier "$@"
