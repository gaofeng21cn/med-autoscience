#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
cd "${repo_root}"

verify_tmp_root="$(mktemp -d "${TMPDIR:-/tmp}/mas-verify.XXXXXX")"
trap 'rm -rf "${verify_tmp_root}"' EXIT

export PYTHONPATH=src
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPYCACHEPREFIX="${verify_tmp_root}/pycache"
export PYTEST_ADDOPTS="-p no:cacheprovider -o cache_dir=${verify_tmp_root}/pytest-cache"

run_sanity_checks() {
  uv run --frozen python scripts/repo_hygiene_audit.py

  if git grep -n -I -E '^(<<<<<<< |=======|>>>>>>> |\|\|\|\|\|\|\| )' -- .; then
    echo "verify.sh: unresolved merge conflict markers detected" >&2
    exit 1
  fi

}

run_sanity_checks
lane="${1:-full}"

if [[ "${lane}" != "full" || "$#" -gt 1 ]]; then
  echo "Usage: scripts/verify.sh [full]" >&2
  exit 2
fi

make test
