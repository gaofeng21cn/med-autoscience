#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
cd "${repo_root}"

export PYTHONDONTWRITEBYTECODE=1
export PYTEST_ADDOPTS="-p no:cacheprovider"

lane="${1:-source}"

opl_bin="${OPL_BIN:-}"
if [[ -z "${OPL_FRAMEWORK_PYTHON_ROOT:-}" ]]; then
  opl_bin="${opl_bin:-/Users/gaofeng/workspace/one-person-lab/bin/opl}"
  framework_root="$(cd "$(dirname "${opl_bin}")/.." && pwd)"
  export OPL_FRAMEWORK_PYTHON_ROOT="${framework_root}/python"
fi
if [[ ! -f "${OPL_FRAMEWORK_PYTHON_ROOT}/opl_framework/exact_refs.py" ]]; then
  echo "verify.sh: Framework Python authority is unavailable: ${OPL_FRAMEWORK_PYTHON_ROOT}" >&2
  exit 1
fi
export PYTHONPATH="${repo_root}/src:${OPL_FRAMEWORK_PYTHON_ROOT}"
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

opl_bin="${opl_bin:-/Users/gaofeng/workspace/one-person-lab/bin/opl}"
if [[ ! -x "${opl_bin}" ]]; then
  echo "verify.sh: Framework CLI is unavailable: ${opl_bin}" >&2
  exit 1
fi
"${opl_bin}" workspace source-hygiene --source-root "${repo_root}" --json
make test
