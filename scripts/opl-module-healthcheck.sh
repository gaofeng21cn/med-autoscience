#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "${repo_root}"

case "${1:-}" in
  "")
    mode="--healthcheck"
    ;;
  --probe)
    mode="--probe"
    ;;
  --help|-h)
    cat <<'EOF'
Usage: scripts/opl-module-healthcheck.sh [--probe|--help]

Without arguments, validate the OPL-managed MAS runtime source carrier.
--probe validates the read-only MedAutoScienceDomainEntry.dispatch target only.
EOF
    exit 0
    ;;
  *)
    echo "Usage: scripts/opl-module-healthcheck.sh [--probe|--help]" >&2
    exit 2
    ;;
esac

state_base="${OPL_MODULE_RUNTIME_ROOT:-${XDG_STATE_HOME:-${HOME}/.local/state}/one-person-lab/modules}"
cache_base="${OPL_MODULE_CACHE_ROOT:-${XDG_CACHE_HOME:-${HOME}/.cache}/one-person-lab/modules}"
runtime_root="${MAS_OPL_MODULE_RUNTIME_ROOT:-${state_base%/}/medautoscience}"
cache_root="${MAS_OPL_MODULE_CACHE_ROOT:-${cache_base%/}/medautoscience}"
venv_python="${runtime_root}/venv/bin/python"

if [[ ! -x "${venv_python}" ]]; then
  echo "opl-module-healthcheck.sh: missing OPL-managed MAS dependency environment; run scripts/opl-module-bootstrap.sh" >&2
  exit 1
fi

export PYTHONPATH="${repo_root}/src"
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPYCACHEPREFIX="${runtime_root}/pycache"
export MAS_OPL_MODULE_CACHE_ROOT="${cache_root}"

exec "${venv_python}" -m med_autoscience.opl_module_carrier "${mode}" --repo-root "${repo_root}"
