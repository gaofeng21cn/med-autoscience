#!/usr/bin/env bash
set -euo pipefail

if [[ "${1:-}" != "full" ]]; then
  echo "Usage: $0 full" >&2
  exit 2
fi

lanes=(
  "test-regression"
  "test-meta"
  "test-display"
  "test-submission"
  "test-family"
)

full_lane_pytest_workers="${MAS_FULL_PYTEST_WORKERS:-2}"

if [[ -n "${MAS_TEST_LANE_SUMMARY_PATH:-}" ]]; then
  summary_dir="$(dirname "${MAS_TEST_LANE_SUMMARY_PATH}")"
  mkdir -p "${summary_dir}"
  summary_stem="$(basename "${MAS_TEST_LANE_SUMMARY_PATH}")"
  log_root="$(mktemp -d "${summary_dir}/${summary_stem}.logs.XXXXXX")"
else
  log_root="$(mktemp -d "${TMPDIR:-/tmp}/med-autoscience-test-full.XXXXXX")"
  trap 'rm -rf "${log_root}"' EXIT
fi

json_escape() {
  local value="${1}"
  value="${value//\\/\\\\}"
  value="${value//\"/\\\"}"
  value="${value//$'\n'/\\n}"
  printf '%s' "${value}"
}

write_summary_json() {
  local summary_path="${1}"
  local tmp_path="${summary_path}.tmp"

  {
    printf '{\n'
    printf '  "lanes": [\n'
    local index
    for index in "${!lanes[@]}"; do
      local lane="${lanes[${index}]}"
      local command="make ${lane}"
      printf '    {"lane": "%s", "command": "%s", "exit_code": %s, "duration_seconds": %s, "log_path": "%s"}' \
        "$(json_escape "${lane}")" \
        "$(json_escape "${command}")" \
        "${lane_exit_codes[${index}]}" \
        "${lane_duration_seconds[${index}]}" \
        "$(json_escape "${lane_log_paths[${index}]}")"
      if [[ "${index}" != "$((${#lanes[@]} - 1))" ]]; then
        printf ','
      fi
      printf '\n'
    done
    printf '  ]\n'
    printf '}\n'
  } >"${tmp_path}"
  mv "${tmp_path}" "${summary_path}"
}

declare -a lane_pids=()
declare -a lane_log_paths=()
declare -a lane_exit_code_paths=()
declare -a lane_duration_paths=()
declare -a lane_exit_codes=()
declare -a lane_duration_seconds=()

for lane in "${lanes[@]}"; do
  log_path="${log_root}/${lane}.log"
  exit_code_path="${log_root}/${lane}.exit_code"
  duration_path="${log_root}/${lane}.duration_seconds"
  (
    echo "[${lane}] start"
    started_at="$(date +%s)"
    set +e
    MAS_PYTEST_WORKERS="${MAS_PYTEST_WORKERS:-${full_lane_pytest_workers}}" make "${lane}"
    lane_exit_code="$?"
    set -e
    ended_at="$(date +%s)"
    duration_seconds="$((ended_at - started_at))"
    if [[ "${duration_seconds}" -lt 0 ]]; then
      duration_seconds=0
    fi
    printf '%s\n' "${lane_exit_code}" >"${exit_code_path}"
    printf '%s\n' "${duration_seconds}" >"${duration_path}"
    exit "${lane_exit_code}"
  ) >"${log_path}" 2>&1 &
  lane_pids+=("$!")
  lane_log_paths+=("${log_path}")
  lane_exit_code_paths+=("${exit_code_path}")
  lane_duration_paths+=("${duration_path}")
done

exit_code=0
for index in "${!lanes[@]}"; do
  lane="${lanes[${index}]}"
  pid="${lane_pids[${index}]}"
  wait_started_at="$(date +%s)"
  if wait "${pid}"; then
    wait_exit_code=0
  else
    wait_exit_code="$?"
    exit_code=1
  fi
  if [[ -s "${lane_exit_code_paths[${index}]}" ]]; then
    lane_exit_code="$(<"${lane_exit_code_paths[${index}]}")"
  else
    lane_exit_code="${wait_exit_code}"
  fi
  if [[ -s "${lane_duration_paths[${index}]}" ]]; then
    duration_seconds="$(<"${lane_duration_paths[${index}]}")"
  else
    wait_ended_at="$(date +%s)"
    duration_seconds="$((wait_ended_at - wait_started_at))"
  fi
  lane_exit_codes+=("${lane_exit_code}")
  lane_duration_seconds+=("${duration_seconds}")
  sed "s/^/[${lane}] /" "${lane_log_paths[${index}]}"
done

echo "[summary] test lanes:"
for index in "${!lanes[@]}"; do
  lane="${lanes[${index}]}"
  lane_exit_code="${lane_exit_codes[${index}]}"
  duration_seconds="${lane_duration_seconds[${index}]}"
  if [[ "${lane_exit_code}" == "0" ]]; then
    echo "[summary] ${lane}: passed in ${duration_seconds}s"
  else
    echo "[summary] ${lane}: failed (exit ${lane_exit_code}) in ${duration_seconds}s"
  fi
done

if [[ -n "${MAS_TEST_LANE_SUMMARY_PATH:-}" ]]; then
  write_summary_json "${MAS_TEST_LANE_SUMMARY_PATH}"
fi

exit "${exit_code}"
