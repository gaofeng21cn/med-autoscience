#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
cd "${repo_root}"

export PYTHONDONTWRITEBYTECODE=1
export PYTEST_ADDOPTS="-p no:cacheprovider"

lane="${1:-source}"

opl_bin="${OPL_BIN:-}"
if [[ -z "${opl_bin}" ]]; then
  if [[ -n "${OPL_FRAMEWORK_ROOT:-}" && -x "${OPL_FRAMEWORK_ROOT}/bin/opl" ]]; then
    opl_bin="${OPL_FRAMEWORK_ROOT}/bin/opl"
  elif [[ -x "${repo_root}/../one-person-lab/bin/opl" ]]; then
    opl_bin="${repo_root}/../one-person-lab/bin/opl"
  else
    opl_bin="$(command -v opl || true)"
  fi
fi
if [[ -z "${OPL_FRAMEWORK_PYTHON_ROOT:-}" ]]; then
  if [[ -n "${OPL_FRAMEWORK_ROOT:-}" && -d "${OPL_FRAMEWORK_ROOT}/python" ]]; then
    export OPL_FRAMEWORK_PYTHON_ROOT="${OPL_FRAMEWORK_ROOT}/python"
  elif [[ -n "${opl_bin}" ]]; then
    framework_root="$(cd "$(dirname "${opl_bin}")/.." && pwd)"
    export OPL_FRAMEWORK_PYTHON_ROOT="${framework_root}/python"
  fi
fi
if [[ ! -f "${OPL_FRAMEWORK_PYTHON_ROOT}/opl_framework/exact_refs.py" ]]; then
  echo "verify.sh: Framework Python authority is unavailable: ${OPL_FRAMEWORK_PYTHON_ROOT}" >&2
  exit 1
fi
export PYTHONPATH="${repo_root}/src:${OPL_FRAMEWORK_PYTHON_ROOT}"
if [[ -n "${opl_bin}" && -x "${opl_bin}" ]]; then
  OPL_BIN="${opl_bin}" python3 scripts/materialize_plugin_carrier.py
  OPL_BIN="${opl_bin}" python3 scripts/materialize_plugin_carrier.py --check
elif [[ "${lane}" == "full" ]]; then
  echo "verify.sh: Framework CLI is unavailable for carrier projection check: ${opl_bin:-unset}" >&2
  exit 1
else
  echo "verify.sh: skipping CLI carrier projection check in source lane (Framework CLI unavailable)" >&2
fi
git ls-files -z | python3 scripts/repo_hygiene_audit.py

if git grep -n -I -E '^(<<<<<<< |=======|>>>>>>> |\|\|\|\|\|\|\| )' -- .; then
  echo "verify.sh: unresolved merge conflict markers detected" >&2
  exit 1
fi
if [[ "${lane}" == "source" ]]; then
  make test
  exit 0
fi
if [[ "${lane}" != "full" || "$#" -gt 1 ]]; then
  echo "Usage: scripts/verify.sh [source|full]" >&2
  exit 2
fi

if [[ -z "${opl_bin}" ]]; then
  if [[ -n "${OPL_FRAMEWORK_ROOT:-}" && -x "${OPL_FRAMEWORK_ROOT}/bin/opl" ]]; then
    opl_bin="${OPL_FRAMEWORK_ROOT}/bin/opl"
  elif [[ -x "${repo_root}/../one-person-lab/bin/opl" ]]; then
    opl_bin="${repo_root}/../one-person-lab/bin/opl"
  else
    opl_bin="$(command -v opl || true)"
  fi
fi
if [[ -z "${opl_bin}" || ! -x "${opl_bin}" ]]; then
  echo "verify.sh: Framework CLI is unavailable: ${opl_bin:-unset}" >&2
  exit 1
fi
"${opl_bin}" workspace source-hygiene --source-root "${repo_root}" --json
make test
