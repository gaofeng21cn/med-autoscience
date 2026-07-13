#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
cd "${repo_root}"

verify_tmp_root="$(mktemp -d "${TMPDIR:-/tmp}/mas-verify.XXXXXX")"
cleanup_verify_tmp_root() {
  rm -rf "${verify_tmp_root}"
}
trap cleanup_verify_tmp_root EXIT

requirements_file="${verify_tmp_root}/requirements.txt"
uv export --quiet --frozen --no-emit-project --group dev --format requirements-txt > "${requirements_file}"
export PYTHONPATH=src
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPYCACHEPREFIX="${verify_tmp_root}/pycache"
export PYTEST_ADDOPTS="-p no:cacheprovider -o cache_dir=${verify_tmp_root}/pytest-cache"

run_sanity_checks() {
  if [[ "${MAS_VERIFY_REPO_HYGIENE_FIX:-0}" == "1" ]]; then
    uv run --isolated --frozen --no-project --with-requirements "${requirements_file}" python scripts/repo_hygiene_audit.py --fix
  fi
  uv run --isolated --frozen --no-project --with-requirements "${requirements_file}" python scripts/repo_hygiene_audit.py
  uv run --isolated --frozen --no-project --with-requirements "${requirements_file}" python scripts/line_budget.py

  if git grep -n -I -E '^(<<<<<<< |=======|>>>>>>> |\|\|\|\|\|\|\| )' -- .; then
    echo "verify.sh: unresolved merge conflict markers detected" >&2
    exit 1
  fi

  local -a python_files=()
  while IFS= read -r python_file; do
    if [[ ! -f "${python_file}" ]]; then
      continue
    fi
    python_files+=("${python_file}")
  done < <(git ls-files '*.py')

  if [[ "${#python_files[@]}" -gt 0 ]]; then
    uv run --isolated --frozen --no-project --with-requirements "${requirements_file}" python - "${python_files[@]}" <<'PY'
from __future__ import annotations

import pathlib
import py_compile
import tempfile
import sys


with tempfile.TemporaryDirectory(prefix="mas-py-compile-") as temp_dir:
    bytecode_dir = pathlib.Path(temp_dir)
    for index, python_file in enumerate(sys.argv[1:]):
        bytecode_path = bytecode_dir / f"{index}.pyc"
        py_compile.compile(python_file, cfile=str(bytecode_path), doraise=True)
PY
  fi
}

lane="${1:-}"

run_sanity_checks

if [[ -z "${lane}" ]]; then
  make test-fast
  exit 0
fi

if [[ "${lane}" == "smoke" ]]; then
  make test-smoke
  exit 0
fi

if [[ "${lane}" == "regression" ]]; then
  make test-regression
  exit 0
fi

if [[ "${lane}" == "ci-preflight" ]]; then
  base_ref="${2:-}"
  if [[ -z "${base_ref}" ]]; then
    echo "Usage: scripts/verify.sh ci-preflight <base-ref>" >&2
    exit 2
  fi
  BASE_REF="${base_ref}" make test-ci-preflight
  exit 0
fi

if [[ "${lane}" == "fast" ]]; then
  make test-fast
  exit 0
fi

if [[ "${lane}" == "meta" ]]; then
  make test-meta
  exit 0
fi

if [[ "${lane}" == "display" ]]; then
  make test-display
  exit 0
fi

if [[ "${lane}" == "submission" ]]; then
  make test-submission
  exit 0
fi

if [[ "${lane}" == "soak-golden" ]]; then
  make test-soak-golden
  exit 0
fi

if [[ "${lane}" == "family" ]]; then
  make test-family
  exit 0
fi

if [[ "${lane}" == "line-budget" ]]; then
  make line-budget
  exit 0
fi

if [[ "${lane}" == "line-budget:strict" ]]; then
  make line-budget-strict
  exit 0
fi

if [[ "${lane}" == "structure" ]]; then
  make test-structure
  exit 0
fi

if [[ "${lane}" == "structure:strict" ]]; then
  make test-structure-strict
  exit 0
fi

if [[ "${lane}" == "full" ]]; then
  make test-full
  exit 0
fi

if [[ "${lane}" == "control-plane" ]]; then
  make test-control-plane
  exit 0
fi

echo "Usage: scripts/verify.sh [smoke|regression|ci-preflight <base-ref>|fast|meta|display|submission|soak-golden|family|line-budget|line-budget:strict|structure|structure:strict|control-plane|full]" >&2
exit 1
