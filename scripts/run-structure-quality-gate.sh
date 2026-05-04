#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
cd "${repo_root}"

compare_ref="${OPL_QUALITY_DETAILS_COMPARE_REF:-origin/main}"
quality_limit="${OPL_QUALITY_DETAILS_LIMIT:-20}"
opl_bin="${OPL_QUALITY_DETAILS_BIN:-/Users/gaofeng/workspace/one-person-lab/bin/opl}"

run_opl_quality_details() {
  local failed_command="${1}"

  echo "structure quality gate: ${failed_command} failed; running OPL quality details against ${compare_ref}" >&2
  if ! command -v "${opl_bin}" >/dev/null 2>&1; then
    echo "structure quality gate: ${opl_bin} not found; install OPL CLI or set OPL_QUALITY_DETAILS_BIN" >&2
    return 127
  fi

  "${opl_bin}" quality details \
    --root "${repo_root}" \
    --format markdown \
    --limit "${quality_limit}" \
    --compare-ref "${compare_ref}"
}

run_sentrux_command() {
  local command_name="${1}"
  shift
  local exit_code

  set +e
  "$@"
  exit_code="$?"
  set -e

  if [[ "${exit_code}" -ne 0 ]]; then
    set +e
    run_opl_quality_details "${command_name}"
    set -e
    return "${exit_code}"
  fi

  return 0
}

run_sentrux_command "sentrux gate" sentrux gate

if [[ -f .sentrux/rules.toml ]]; then
  run_sentrux_command "sentrux check" sentrux check
fi
