#!/usr/bin/env bash
set -euo pipefail

if [[ "${1:-}" != "full" ]]; then
  echo "Usage: $0 full" >&2
  exit 2
fi

lanes=(
  "test-fast"
  "test-meta"
  "test-display"
  "test-family"
)

log_root="$(mktemp -d "${TMPDIR:-/tmp}/med-autoscience-test-full.XXXXXX")"
trap 'rm -rf "${log_root}"' EXIT

declare -a lane_statuses=()

for lane in "${lanes[@]}"; do
  (
    echo "[${lane}] start"
    make "${lane}"
  ) >"${log_root}/${lane}.log" 2>&1 &
  lane_statuses+=("${lane}:$!")
done

exit_code=0
for lane_status in "${lane_statuses[@]}"; do
  lane="${lane_status%%:*}"
  pid="${lane_status##*:}"
  if ! wait "${pid}"; then
    exit_code=1
  fi
  sed "s/^/[${lane}] /" "${log_root}/${lane}.log"
done

exit "${exit_code}"
