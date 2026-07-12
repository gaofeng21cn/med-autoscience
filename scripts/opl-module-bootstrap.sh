#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

state_base="${OPL_MODULE_RUNTIME_ROOT:-${XDG_STATE_HOME:-${HOME}/.local/state}/one-person-lab/modules}"
cache_base="${OPL_MODULE_CACHE_ROOT:-${XDG_CACHE_HOME:-${HOME}/.cache}/one-person-lab/modules}"
runtime_root="${MAS_OPL_MODULE_RUNTIME_ROOT:-${state_base%/}/medautoscience}"
cache_root="${MAS_OPL_MODULE_CACHE_ROOT:-${cache_base%/}/medautoscience}"

runtime_root="$(python3 -c 'import os, sys; print(os.path.realpath(os.path.expanduser(sys.argv[1])))' "${runtime_root}")"
cache_root="$(python3 -c 'import os, sys; print(os.path.realpath(os.path.expanduser(sys.argv[1])))' "${cache_root}")"

for external_root in "${runtime_root}" "${cache_root}"; do
  case "${external_root}" in
    "${repo_root}"|"${repo_root}"/*)
      echo "opl-module-bootstrap.sh: runtime and cache roots must be outside the source checkout" >&2
      exit 2
      ;;
  esac
done

mkdir -p "${runtime_root}" "${cache_root}"

command -v uv >/dev/null 2>&1 || {
  echo "opl-module-bootstrap.sh: uv is required and must be provided by OPL Base" >&2
  exit 127
}

export UV_PROJECT_ENVIRONMENT="${runtime_root}/venv"
export UV_CACHE_DIR="${cache_root}/uv"
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPYCACHEPREFIX="${runtime_root}/pycache"

uv sync --frozen --no-install-project --no-dev

venv_python="${UV_PROJECT_ENVIRONMENT}/bin/python"
if [[ ! -x "${venv_python}" ]]; then
  echo "opl-module-bootstrap.sh: dependency environment was not materialized" >&2
  exit 1
fi

"${venv_python}" - "${runtime_root}" "${cache_root}" <<'PY'
import json
import sys

print(json.dumps({
    "ok": True,
    "surface_kind": "opl_module_runtime_source_bootstrap",
    "module_id": "medautoscience",
    "environment_owner": "opl_base",
    "runtime_root": sys.argv[1],
    "cache_root": sys.argv[2],
    "source_checkout_mutation": False,
}, ensure_ascii=False))
PY
