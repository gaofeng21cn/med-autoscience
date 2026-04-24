#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
cd "${repo_root}"

run_sanity_checks() {
  python scripts/line_budget.py

  if git grep -n -I -E '^(<<<<<<< |=======|>>>>>>> |\|\|\|\|\|\|\| )' -- .; then
    echo "verify.sh: unresolved merge conflict markers detected" >&2
    exit 1
  fi

  local -a python_files=()
  while IFS= read -r python_file; do
    python_files+=("${python_file}")
  done < <(git ls-files '*.py')

  if [[ "${#python_files[@]}" -gt 0 ]]; then
    uv run python -m py_compile "${python_files[@]}"
  fi
}

lane="${1:-}"

run_sanity_checks

if [[ -z "${lane}" ]]; then
  make test-fast
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

if [[ "${lane}" == "family" ]]; then
  make test-family
  exit 0
fi

if [[ "${lane}" == "full" ]]; then
  make test-full
  exit 0
fi

echo "Usage: scripts/verify.sh [fast|meta|display|family|full]" >&2
exit 1
