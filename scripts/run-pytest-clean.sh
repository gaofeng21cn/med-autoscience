#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/.." && pwd)"
cd "${repo_root}"

if [[ -z "${CI:-}" && -z "${MAS_CLEAN_RUNNER_REUSE_ENV:-}" && -z "${MAS_CLEAN_RUNNER_TMP_ROOT:-}" ]]; then
  export MAS_CLEAN_RUNNER_REUSE_ENV=1
fi

exec "${repo_root}/scripts/run-python-clean.sh" -m pytest "$@"
