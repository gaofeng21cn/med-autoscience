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
  elif [[ -x "${repo_root}/../.worktrees/opl-v2/bin/opl" ]]; then
    opl_bin="${repo_root}/../.worktrees/opl-v2/bin/opl"
  else
    opl_bin="$(command -v opl || true)"
  fi
fi

sdk_src=""
if [[ -n "${OPL_PYTHON_CLIENT_DIR:-}" && -d "${OPL_PYTHON_CLIENT_DIR}/src/opl_client" ]]; then
  sdk_src="${OPL_PYTHON_CLIENT_DIR}/src"
elif [[ -n "${OPL_FRAMEWORK_ROOT:-}" && -d "${OPL_FRAMEWORK_ROOT}/sdks/python-client/src/opl_client" ]]; then
  sdk_src="${OPL_FRAMEWORK_ROOT}/sdks/python-client/src"
elif [[ -d "${repo_root}/../one-person-lab/sdks/python-client/src/opl_client" ]]; then
  sdk_src="${repo_root}/../one-person-lab/sdks/python-client/src"
elif [[ -d "${repo_root}/../.worktrees/opl-v2/sdks/python-client/src/opl_client" ]]; then
  sdk_src="${repo_root}/../.worktrees/opl-v2/sdks/python-client/src"
fi
export PYTHONPATH="${repo_root}/src${sdk_src:+:${sdk_src}}${PYTHONPATH:+:${PYTHONPATH}}"

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

if [[ -z "${opl_bin}" || ! -x "${opl_bin}" ]]; then
  echo "verify.sh: OPL CLI is unavailable: ${opl_bin:-unset}" >&2
  exit 1
fi
"${opl_bin}" pack inspect "${repo_root}" --json
make test
