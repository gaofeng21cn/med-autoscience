#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
cd "${repo_root}"

verify_tmp_root="$(mktemp -d "${TMPDIR:-/tmp}/mas-verify.XXXXXX")"
cleanup_verify_tmp_root() {
  rm -rf "${verify_tmp_root}"
}
trap cleanup_verify_tmp_root EXIT
export MAS_CLEAN_RUNNER_TMP_ROOT="${verify_tmp_root}/python"
clean_python_runner="${MAS_CLEAN_PYTHON_RUNNER:-scripts/run-python-clean.sh}"

run_sanity_checks() {
  "${clean_python_runner}" scripts/repo_hygiene_audit.py
  "${clean_python_runner}" scripts/line_budget.py

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
    "${clean_python_runner}" - "${python_files[@]}" <<'PY'
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

json_escape() {
  local value="${1}"
  value="${value//\\/\\\\}"
  value="${value//\"/\\\"}"
  value="${value//$'\n'/\\n}"
  printf '%s' "${value}"
}

write_single_lane_summary_json() {
  local lane_name="${1}"
  local command_label="${2}"
  local command_exit_code="${3}"
  local duration_seconds="${4}"
  local summary_path="${MAS_TEST_LANE_SUMMARY_PATH}"
  local summary_dir
  local tmp_path

  summary_dir="$(dirname "${summary_path}")"
  mkdir -p "${summary_dir}"
  tmp_path="${summary_path}.tmp"
  {
    printf '{\n'
    printf '  "lanes": [\n'
    printf '    {"lane": "%s", "command": "%s", "exit_code": %s, "duration_seconds": %s, "log_path": ""}\n' \
      "$(json_escape "${lane_name}")" \
      "$(json_escape "${command_label}")" \
      "${command_exit_code}" \
      "${duration_seconds}"
    printf '  ]\n'
    printf '}\n'
  } >"${tmp_path}"
  mv "${tmp_path}" "${summary_path}"
}

run_with_optional_summary() {
  local lane_name="${1}"
  local command_label="${2}"
  shift 2
  local started_at
  local ended_at
  local duration_seconds
  local command_exit_code

  started_at="$(date +%s)"
  set +e
  "$@"
  command_exit_code="$?"
  set -e
  ended_at="$(date +%s)"
  duration_seconds="$((ended_at - started_at))"
  if [[ "${duration_seconds}" -lt 0 ]]; then
    duration_seconds=0
  fi
  if [[ -n "${MAS_TEST_LANE_SUMMARY_PATH:-}" ]]; then
    write_single_lane_summary_json "${lane_name}" "${command_label}" "${command_exit_code}" "${duration_seconds}"
  fi
  return "${command_exit_code}"
}

if [[ -z "${lane}" ]]; then
  run_with_optional_summary "smoke" "make test-smoke" make test-smoke
  exit 0
fi

if [[ "${lane}" == "smoke" ]]; then
  run_with_optional_summary "smoke" "make test-smoke" make test-smoke
  exit 0
fi

if [[ "${lane}" == "regression" ]]; then
  run_with_optional_summary "regression" "make test-regression" make test-regression
  exit 0
fi

if [[ "${lane}" == "ci-preflight" ]]; then
  base_ref="${2:-}"
  if [[ -z "${base_ref}" ]]; then
    echo "Usage: scripts/verify.sh ci-preflight <base-ref>" >&2
    exit 2
  fi
  BASE_REF="${base_ref}" run_with_optional_summary "ci-preflight" "BASE_REF=${base_ref} make test-ci-preflight" make test-ci-preflight
  exit 0
fi

if [[ "${lane}" == "fast" ]]; then
  run_with_optional_summary "fast" "make test-regression" make test-regression
  exit 0
fi

if [[ "${lane}" == "meta" ]]; then
  run_with_optional_summary "meta" "make test-meta" make test-meta
  exit 0
fi

if [[ "${lane}" == "display" ]]; then
  run_with_optional_summary "display" "make test-display" make test-display
  exit 0
fi

if [[ "${lane}" == "submission" ]]; then
  run_with_optional_summary "submission" "make test-submission" make test-submission
  exit 0
fi

if [[ "${lane}" == "family" ]]; then
  run_with_optional_summary "family" "make test-family" make test-family
  exit 0
fi

if [[ "${lane}" == "structure" ]]; then
  run_with_optional_summary "structure" "make test-structure" make test-structure
  exit 0
fi

if [[ "${lane}" == "full" ]]; then
  run_with_optional_summary "full" "make test-full" make test-full
  exit 0
fi

if [[ "${lane}" == "control-plane" ]]; then
  run_with_optional_summary "control-plane" "make test-control-plane" make test-control-plane
  exit 0
fi

echo "Usage: scripts/verify.sh [smoke|regression|ci-preflight <base-ref>|fast|meta|display|submission|family|structure|control-plane|full]" >&2
exit 1
