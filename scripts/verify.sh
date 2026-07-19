#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
cd "${repo_root}"

export PYTHONDONTWRITEBYTECODE=1
export PYTEST_ADDOPTS="-p no:cacheprovider"

opl_bin="${OPL_BIN:-/Users/gaofeng/workspace/one-person-lab/bin/opl}"
framework_root="$(cd "$(dirname "${opl_bin}")/.." && pwd)"
export OPL_FRAMEWORK_PYTHON_ROOT="${OPL_FRAMEWORK_PYTHON_ROOT:-${framework_root}/python}"
if [[ ! -f "${OPL_FRAMEWORK_PYTHON_ROOT}/opl_framework/exact_refs.py" ]]; then
  echo "verify.sh: Framework Python authority is unavailable: ${OPL_FRAMEWORK_PYTHON_ROOT}" >&2
  exit 1
fi
export PYTHONPATH="${repo_root}/src:${OPL_FRAMEWORK_PYTHON_ROOT}"
"${opl_bin}" workspace source-hygiene --source-root "${repo_root}" --json
git ls-files -z | python3 scripts/repo_hygiene_audit.py

if git grep -n -I -E '^(<<<<<<< |=======|>>>>>>> |\|\|\|\|\|\|\| )' -- .; then
  echo "verify.sh: unresolved merge conflict markers detected" >&2
  exit 1
fi
lane="${1:-full}"

if [[ "${lane}" != "full" || "$#" -gt 1 ]]; then
  echo "Usage: scripts/verify.sh [full]" >&2
  exit 2
fi

make test
