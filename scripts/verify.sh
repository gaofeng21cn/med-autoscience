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

  local -a python_files=()
  while IFS= read -r file; do
    [[ -f "${file}" ]] && python_files+=("${file}")
  done < <(git ls-files '*.py')
  if [[ "${#python_files[@]}" -gt 0 ]]; then
    uv run --frozen python - "${python_files[@]}" <<'PY'
from __future__ import annotations

import pathlib
import py_compile
import sys
import tempfile

with tempfile.TemporaryDirectory(prefix="mas-py-compile-") as temp_dir:
    bytecode_dir = pathlib.Path(temp_dir)
    for index, python_file in enumerate(sys.argv[1:]):
        py_compile.compile(
            python_file,
            cfile=str(bytecode_dir / f"{index}.pyc"),
            doraise=True,
        )
PY
  fi
}

run_sanity_checks
lane="${1:-full}"

case "${lane}" in
  smoke) make test-smoke ;;
  meta) make test-meta ;;
  regression) make test-regression ;;
  full) make test-full ;;
  structure) make test-structure ;;
  *)
    echo "Usage: scripts/verify.sh [smoke|meta|regression|full|structure]" >&2
    exit 2
    ;;
esac
